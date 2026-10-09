"""Every stored entry for one horse name (any meeting), newest first: meeting, race, barrier, status. DB only, no credits.

    python scripts/horse_entries.py "Cavill Avenue"
"""
from __future__ import annotations

import os
import sys

import psycopg

name = " ".join(sys.argv[1:])
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    rows = c.execute("""select r.meeting_id, r.race_number, e.raw->>'barrierNumber', e.raw->>'emergency', e.raw->>'scratched',
                               coalesce(e.raw->'horse'->>'name', e.raw->>'horseName', e.raw->>'name')
                        from fk.entries e join fk.races r using (race_id)
                        where lower(coalesce(e.raw->'horse'->>'name', e.raw->>'horseName', e.raw->>'name')) like lower(%s)
                        order by r.meeting_id desc limit 20""", (f"%{name}%",)).fetchall()
    print(f"## {name}: {len(rows)} entries")
    for m, rn, bar, em, sc, nm in rows:
        print(f"{m} R{rn} {nm} barrier {bar} emergency {em} scratched {sc}")
