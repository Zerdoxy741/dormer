#!/usr/bin/env python3
"""Merge a GitHub release object from stdin with the archived notes."""
import json
import re
import sys
from pathlib import Path

out = []
for r in [json.load(sys.stdin)]:
    if r.get("draft") or r.get("prerelease"):
        continue
    body = r.get("body") or ""
    notes, _, verify = body.partition("<!-- verify -->")
    sha = re.search(r"\b[0-9a-f]{64}\b", verify)
    vt = re.search(r"https://www\.virustotal\.com/gui/file/[0-9a-f]{64}", verify)
    out.append({
        "version": (r.get("name") or "").replace("Dormer", "").strip() or r["tag_name"],
        "build": r["tag_name"],
        "date": (r.get("published_at") or "")[:10],
        "notes": notes.strip(),
        "sha256": sha.group(0) if sha else None,
        "virustotal": vt.group(0) if vt else None,
        "url": r.get("html_url"),
    })
if not out:
    sys.exit("Release stable attendue")
archive = Path(__file__).resolve().parents[1] / "data/releases.json"
for previous in json.loads(archive.read_text()):
    if previous["build"] != out[0]["build"]:
        previous.pop("url", None)
        previous.pop("virustotal", None)
        out.append(previous)
print(json.dumps(out, ensure_ascii=False, indent=1))
