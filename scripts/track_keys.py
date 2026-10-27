"""What does Form King store about the track itself (rating, rail, rain, irrigation, penetrometer, weather)?
Prints every meeting- and race-level key whose name looks track-related for a few recent Flemington meetings, from the
database and from one history day file. Reads only: no credits (28 Oct 2026, founder: weather and track-rating analysis).

    python scripts/track_keys.py [TRACK]
"""
from __future__ import annotations

import glob
import gzip
import json
import os
import re
import sys

import psycopg

TRACK = sys.argv[1] if len(sys.argv) > 1 else "Flemington"
PAT = re.compile(r"rain|irrig|water|rail|weather|penetro|going|condition|rating|track|surface|wind|temp|forecast", re.I)


def walk(obj, path=""):
    """Every (path, value) under obj whose key matches PAT; values cut short."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            if PAT.search(k) and not isinstance(v, (dict, list)):
                yield p, str(v)[:120]
            yield from walk(v, p)
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:2]):
            yield from walk(v, f"{path}[{i}]")


with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    rows = c.execute("select meeting_id, meeting_date, raw from fk.meetings where track ilike %s order by meeting_date desc limit 3",
                     (TRACK,)).fetchall()
    for mid, day, raw in rows:
        print(f"## DB meeting {day} {mid}: top-level keys {sorted((raw or {}).keys())}")
        for p, v in walk(raw or {}):
            print(f"- {p} = {v}")
        r = c.execute("select raw from fk.races where meeting_id = %s order by race_number limit 1", (mid,)).fetchone()
        if r:
            print(f"### first race top-level keys {sorted((r[0] or {}).keys())}")
            for p, v in walk(r[0] or {}):
                if not re.search(r"runners\[|form|history", p, re.I):
                    print(f"- {p} = {v}")

files = sorted(glob.glob("history/*.jsonl.gz"))
print(f"\n## history files: {len(files)}")
done = False
for f in files[-40:]:
    with gzip.open(f, "rt") as fh:
        for line in fh:
            d = json.loads(line)
            if TRACK.lower() not in json.dumps(d)[:4000].lower():
                continue
            print(f"### {f}: top-level keys {sorted(d.keys()) if isinstance(d, dict) else type(d)}")
            seen = set()
            for p, v in walk(d):
                key = re.sub(r"\[\d+\]", "[]", p)
                if key in seen or re.search(r"runners\[|form\b|history", p, re.I):
                    continue
                seen.add(key)
                print(f"- {p} = {v}")
            done = True
            break
    if done:
        break
