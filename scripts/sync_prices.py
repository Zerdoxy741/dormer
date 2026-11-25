#!/usr/bin/env python3
"""Refresh data/prices.json from the source of each price.

- Dormer: the Polar API (needs the POLAR_TOKEN env var: an organization access token with products:read).
- NotchNook: its pricing page (regular prices, sales ignored).
- DynamicLake: its Gumroad page.
Apps with "sync": null are checked by hand.

A price that can't be read, or looks wrong, is never written: the old value stays and a warning is printed.
Exit code is 0 either way, so a broken competitor page never blocks the site; warnings show in the Action log.
"""
import datetime
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

FILE = Path(__file__).resolve().parent.parent / "data" / "prices.json"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"


def get(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def sane(v):
    return isinstance(v, (int, float)) and 1 <= v <= 300


def polar(app):
    token = os.environ.get("POLAR_TOKEN")
    if not token:
        return None, "POLAR_TOKEN not set, Dormer price left as is"
    d = json.loads(get(f"https://api.polar.sh/v1/products/{app['product_id']}",
                       {"Authorization": f"Bearer {token}", "Accept": "application/json"}))
    eur = [p for p in d.get("prices", []) if p.get("amount_type") == "fixed"
           and p.get("price_currency") == "eur" and not p.get("is_archived")]
    if not eur:
        return None, "no fixed EUR price on the Polar product"
    return {"lifetime": eur[0]["price_amount"] / 100, "currency": "EUR"}, None


def notchnook(app):
    page = get("https://lo.cafe/notchnook/")
    amounts = [(float(m.group(1)), m.group(2) or "") for m in re.finditer(r"€(\d+\.\d{2})(/month)?", page)]
    monthly = [a for a, per in amounts if per]
    once = [a for a, per in amounts if not per]
    if not monthly or not once:
        return None, "no prices found on the NotchNook page"
    # Pro is the dearer plan; the regular price is the highest one shown (a sale price sits below it)
    return {"lifetime": max(once), "monthly": max(monthly), "currency": "EUR"}, None


def gumroad(app):
    page = get(app["source"])
    m = re.search(r'"price"\s*:\s*(\d+(?:\.\d+)?)', page)
    if not m:
        return None, "no price on the Gumroad page"
    return {"lifetime": float(m.group(1))}, None


SYNC = {"polar": polar, "notchnook": notchnook, "gumroad": gumroad}


def main():
    data = json.loads(FILE.read_text())
    today = datetime.date.today().isoformat()
    changed, warnings = [], []
    for name, app in data["apps"].items():
        fn = SYNC.get(app.get("sync") or "")
        if not fn:
            continue
        try:
            new, warn = fn(app)
        except Exception as e:  # network error, page redesign…
            new, warn = None, f"{type(e).__name__}: {e}"
        if warn:
            warnings.append(f"{name}: {warn}")
            continue
        if not all(sane(v) for k, v in new.items() if k != "currency"):
            warnings.append(f"{name}: price looks wrong, ignored: {new}")
            continue
        diff = {k: (app.get(k), v) for k, v in new.items() if app.get(k) != v}
        if diff:
            changed.append(f"{name}: " + ", ".join(f"{k} {a} -> {b}" for k, (a, b) in diff.items()))
        app.update(new)
        # refresh the date when a price moved, or once a week, so the site isn't republished every day for nothing
        old = datetime.date.fromisoformat(app.get("checked", "2000-01-01"))
        if diff or (datetime.date.today() - old).days >= 7:
            app["checked"] = today
    FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    for line in changed:
        print("changed", line)
    for line in warnings:
        print(f"::warning::{line}" if os.environ.get("GITHUB_ACTIONS") else f"warning {line}", file=sys.stderr)
    if not changed:
        print("no price change")


if __name__ == "__main__":
    main()
