"""Status of a day's stored meetings: each race's status fields from the stored race JSON,
how many price snapshots and results it holds. Reads the database only: no credits.

    python scripts/meeting_status.py 2026-10-04 [2026-10-03 ...]
"""
from __future__ import annotations

import json
import os
import sys

import psycopg

KEYS = ("status", "raceStatus", "abandoned", "isAbandoned", "resultStatus", "meetingStatus", "trackCondition", "going")

with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    for day in sys.argv[1:]:
        for mid, track, mraw in c.execute("select meeting_id, track, raw from fk.meetings where meeting_date = %s order by track", (day,)).fetchall():
            ms = {k: (mraw or {}).get(k) for k in KEYS if (mraw or {}).get(k) is not None}
            print(f"## {day} {track} ({mid}) {json.dumps(ms)}")
            for rid, rn, raw in c.execute("select race_id, race_number, raw from fk.races where meeting_id = %s order by race_number", (mid,)).fetchall():
                st = {k: (raw or {}).get(k) for k in KEYS if (raw or {}).get(k) is not None}
                odds = c.execute("select kind, count(*), max(observed_at) from fk.odds_snapshots where race_id = %s group by kind", (rid,)).fetchall()
                res = c.execute("select count(*) from fk.results where race_id = %s", (rid,)).fetchone()[0]
                print(f"- R{rn} {json.dumps(st)} odds {[(k, n, str(t)[:16]) for k, n, t in odds]} results {res}")
