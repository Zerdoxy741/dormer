#!/usr/bin/env python3
"""Turn the GitHub releases API response (stdin) into data/releases.json (stdout).

Used by release.sh in the app repo:
    gh api "repos/Zerdoxy741/dormer/releases?per_page=100" | python3 scripts/releases.py > data/releases.json

Keeps only published releases, with the notes shown to users (before the <!-- verify --> marker)
and the SHA-256 / VirusTotal lines that release.sh writes after it.
"""
import json
import re
import sys

out = []
for r in json.load(sys.stdin):
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
print(json.dumps(out, ensure_ascii=False, indent=1))
