"""Scratchings and current prices for a stored meeting, from the latest entries we hold. DB only, no credits.

    python scripts/scratchings.py pakenham-synthetic-20261005
"""
from __future__ import annotations

import json
import os
import re
import sys

import psycopg


def find(d, pat, pre=""):
    """(path, value) pairs whose key matches pat, excluding past events."""
    if isinstance(d, dict):
        for k, v in d.items():
            if k == "pastEvents":
                continue
            if re.search(pat, k, re.I) and not isinstance(v, (dict, list)):
                yield f"{pre}{k}", v
            yield from find(v, pat, f"{pre}{k}.")
    elif isinstance(d, list):
        for i, v in enumerate(d[:5]):
            yield from find(v, pat, f"{pre}{i}.")


with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    for mid in sys.argv[1:]:
        rows = c.execute("""select r.race_number, e.raw, e.fetched_at from fk.entries e join fk.races r using (race_id)
                            where r.meeting_id = %s order by r.race_number""", (mid,)).fetchall()
        print(f"## {mid}: {len(rows)} entries, latest fetched {max((r[2] for r in rows), default=None)}")
        for rn, raw, at in rows:
            name = raw.get("name") or raw.get("horseName") or raw.get("horse", {}).get("name") if isinstance(raw, dict) else "?"
            flags = {k: v for k, v in find(raw, r"scratch|emergenc|status")}
            prices = {k: v for k, v in find(raw, r"^(price|currentPrice|bestPrice|open|openingPrice|averageOpen|firmOrDrift)$")}
            scr = any(("scratch" in k.lower() and v) for k, v in flags.items())
            print(f"R{rn} {name!s:24s} {'SCR' if scr else '   '} {json.dumps(prices)[:120]} {json.dumps({k:v for k,v in flags.items() if v})[:120]}")

    # The same meeting as a live_bets prices file: best price now in both columns, Form King's average
    # opening price fifth, scratched runners as SCR (6 Oct 2026). Paste below "## prices file".
    for mid in sys.argv[1:]:
        rows = c.execute("""select r.race_number, e.raw from fk.entries e join fk.races r using (race_id)
                            where r.meeting_id = %s order by r.race_number""", (mid,)).fetchall()
        print(f"\n## prices file: {mid}")
        for rn, raw in rows:
            name = raw.get("name") or raw.get("horseName") or (raw.get("horse") or {}).get("name") or "?"
            scr = any(("scratch" in k.lower() and v) for k, v in find(raw, r"scratch"))
            o = raw.get("odds") if isinstance(raw.get("odds"), dict) else {}
            now, op = o.get("bestNow"), o.get("avgOpen")
            if scr:
                print(f"{rn}, {name}, SCR")
            elif now:
                print(f"{rn}, {name}, {float(now):.2f}, {float(now):.2f}" + (f", fk_open {float(op):.2f}" if op else ""))
            else:
                print(f"# {rn}, {name}, NOPRICE")
