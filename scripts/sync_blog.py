#!/usr/bin/env python3
"""Copy the BabyLoveGrowth articles into the blog, so they stay on dormernotch.com
after the subscription ends.

    python3 scripts/sync_blog.py            # add the articles that are not in the blog yet
    python3 scripts/sync_blog.py --force mac-volume-mixer   # redo one (overwrites hand edits)

The API key is read from the macOS keychain (service "babylovegrowth"), or from the
BLG_API_KEY environment variable. For each new article it writes:
  - data/blog-source/<slug>.json   the article exactly as the API returned it (archive)
  - scripts/blog/<slug>.html       the body, cleaned (no BabyLoveGrowth banners or credit)
  - docs/blog/<slug>/*.jpg         the images, downloaded and resized
  - an entry in data/blog.json
Articles already in data/blog.json are left alone, so hand edits are kept.
Then run `python3 scripts/build.py`.
"""
import datetime
import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
API = "https://api.babylovegrowth.ai/api/integrations/v1"
INDEX = REPO / "data" / "blog.json"
MAX_WIDTH = 1600


def api_key() -> str:
    if os.environ.get("BLG_API_KEY"):
        return os.environ["BLG_API_KEY"]
    out = subprocess.run(["security", "find-generic-password", "-s", "babylovegrowth", "-w"],
                         capture_output=True, text=True)
    if out.returncode:
        sys.exit("No API key: add it to the keychain (service babylovegrowth) or set BLG_API_KEY.")
    return out.stdout.strip()


def get(path: str, key: str):
    req = urllib.request.Request(API + path, headers={"X-API-Key": key, "Content-Type": "application/json",
                                                     "User-Agent": "dormer-blog-sync"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(2 ** attempt * 2)
                continue
            raise


def all_articles(key: str) -> list:
    out, offset = [], 0
    while True:
        page = get(f"/articles?limit=50&offset={offset}", key)
        out += page
        if len(page) < 50:
            return out
        offset += 50


# --- cleaning the article HTML ---------------------------------------------------------

VOID = {"img", "br", "hr", "meta", "link", "input", "source"}
DROP_ATTRS = {"tabindex", "target", "rel", "style", "class"}


class Node:
    def __init__(self, tag, attrs, parent=None):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs), parent, []

    def text(self) -> str:
        return "".join(c if isinstance(c, str) else c.text() for c in self.children)

    def find_all(self, tag):
        for c in self.children:
            if isinstance(c, Node):
                if c.tag == tag:
                    yield c
                yield from c.find_all(tag)


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.root = self.cur = Node("root", {})

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur)
        self.cur.children.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.children.append(data)

    def handle_entityref(self, name):
        self.cur.children.append(f"&{name};")

    def handle_charref(self, name):
        self.cur.children.append(f"&#{name};")


def render(n) -> str:
    if isinstance(n, str):
        return n
    inner = "".join(render(c) for c in n.children)
    if n.tag == "root":
        return inner
    attrs = "".join(f' {k}="{html.escape(v or "")}"' for k, v in n.attrs.items())
    return f"<{n.tag}{attrs}>" if n.tag in VOID else f"<{n.tag}{attrs}>{inner}</{n.tag}>"


def only_image(n: Node):
    """The <img> if this <p> holds nothing but one image."""
    kids = [c for c in n.children if not (isinstance(c, str) and not c.strip())]
    return kids[0] if len(kids) == 1 and isinstance(kids[0], Node) and kids[0].tag == "img" else None


def clean(body: str, images: dict) -> str:
    """images: remote src -> (local src, width, height). The first image is the cover, so it is dropped."""
    t = Tree()
    t.feed(body)
    cover_seen = False

    def walk(n: Node) -> list:
        out = []
        for c in n.children:
            if isinstance(c, str):
                out.append(c)
                continue
            if c.tag == "h1" or "data-blg-cta" in c.attrs or c.tag in ("script", "style"):
                continue
            if c.tag == "p" and "babylovegrowth" in render(c).lower():
                continue
            nonlocal cover_seen
            img = only_image(c) if c.tag == "p" else None
            if img is not None:
                if not cover_seen:
                    cover_seen = True
                    continue
                src, w, h = images[img.attrs["src"]]
                alt = html.escape(img.attrs.get("alt", ""))
                out.append(f'<figure><img src="{src}" alt="{alt}" width="{w}" height="{h}" '
                           f'loading="lazy" decoding="async"></figure>')
                continue
            for k in DROP_ATTRS:
                c.attrs.pop(k, None)
            c.children = walk(c)
            if c.tag == "table":
                out.append(f'<div class="tbl">{render(c)}</div>')
            else:
                out.append(c)
        return out

    t.root.children = walk(t.root)
    s = render(t.root)
    s = re.sub(r"\n{3,}", "\n\n", s).strip()
    return s.replace("’", "'") + "\n"


# --- images ------------------------------------------------------------------------------

def image_name(alt: str, used: set) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", alt.lower()).strip("-")[:48].strip("-") or "image"
    name, i = base, 2
    while name in used:
        name, i = f"{base}-{i}", i + 1
    used.add(name)
    return name + ".jpg"


def download(url: str, dest: Path) -> tuple:
    req = urllib.request.Request(url, headers={"User-Agent": "dormer-blog-sync"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = dest.with_suffix(".download")
        raw.write_bytes(r.read())
    # convert to JPEG with the macOS image tool, and shrink (never enlarge) wide images
    w, h = size(raw)
    resize = ["--resampleWidth", str(MAX_WIDTH)] if w > MAX_WIDTH else []
    subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "80", *resize, str(raw), "--out", str(dest)],
                   capture_output=True, check=True)
    raw.unlink()
    return size(dest)


def size(path: Path) -> tuple:
    info = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
                          capture_output=True, text=True, check=True).stdout
    return int(re.search(r"pixelWidth: (\d+)", info).group(1)), int(re.search(r"pixelHeight: (\d+)", info).group(1))


def add(article: dict, key: str) -> dict:
    full = get(f"/articles/{article['id']}", key)
    slug = full["slug"]
    (REPO / "data" / "blog-source").mkdir(exist_ok=True)
    (REPO / "data" / "blog-source" / f"{slug}.json").write_text(json.dumps(full, indent=2, ensure_ascii=False) + "\n")

    body = full["content_html"]
    imgs = re.findall(r'<img[^>]*?src="([^"]+)"[^>]*?alt="([^"]*)"', body)
    folder = REPO / "docs" / "blog" / slug
    folder.mkdir(parents=True, exist_ok=True)
    images, used = {}, {"cover"}
    cover = None
    for i, (src, alt) in enumerate(imgs):
        name = "cover.jpg" if i == 0 else image_name(html.unescape(alt), used)
        w, h = download(src, folder / name)
        images[src] = (f"/blog/{slug}/{name}", w, h)
        if i == 0:
            cover = (name, html.unescape(alt), [w, h])
    if cover is None:
        sys.exit(f"{slug}: no cover image")

    (REPO / "scripts" / "blog" / f"{slug}.html").write_text(clean(body, images))
    date = (full.get("published_at") or full["created_at"])[:10]
    date = min(date, datetime.date.today().isoformat())
    return {"slug": slug, "title": full["title"].replace("’", "'"),
            "desc": full["meta_description"].replace("’", "'"), "date": date,
            "cover": cover[0], "cover_alt": cover[1], "cover_size": cover[2], "source": "babylovegrowth"}


def main():
    force = set(sys.argv[sys.argv.index("--force") + 1:]) if "--force" in sys.argv else set()
    key = api_key()
    posts = json.loads(INDEX.read_text())
    have = {p["slug"] for p in posts} - force
    added = []
    for a in all_articles(key):
        if a["slug"] in have:
            continue
        entry = add(a, key)
        posts = [p for p in posts if p["slug"] != entry["slug"]] + [entry]
        added.append(entry["slug"])
        print("added", entry["slug"])
    posts.sort(key=lambda p: p["date"], reverse=True)
    INDEX.write_text(json.dumps(posts, indent=2, ensure_ascii=False) + "\n")
    print(f"{len(added)} new article(s). Now run: python3 scripts/build.py" if added else "Nothing new.")


if __name__ == "__main__":
    main()
