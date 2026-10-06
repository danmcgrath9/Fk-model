"""Stored meetings from a date on (what Form King's upcoming list has given us). DB only, no credits.

    python scripts/meetings_on_file.py 2026-10-07
"""
from __future__ import annotations

import os
import sys

import psycopg

with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    for mid, d, track, st, n in c.execute(
            """select m.meeting_id, m.meeting_date, m.track, m.state, count(r.race_id)
               from fk.meetings m left join fk.races r using (meeting_id)
               where m.meeting_date >= %s group by 1, 2, 3, 4 order by 2, 3""", (sys.argv[1],)).fetchall():
        print(d, st, track, mid, f"{n} races stored")
