"""Every start we hold for a horse (its stored career form, fk.past_events), by part of its name. DB only, no credits.
Spells and scratchings are never stored, so every row is a race or a barrier trial.

    python scripts/horse_career.py jigsaw
"""
from __future__ import annotations

import os
import sys

import psycopg

with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    for pat in sys.argv[1:]:
        hs = c.execute("select horse_id, name from fk.horses where name ilike %s order by name limit 10", (f"%{pat}%",)).fetchall()
        print(f"## '{pat}': {len(hs)} horse(s)")
        for hid, name in hs:
            rows = c.execute("""select event_date::date, track, distance_m, finish_position, margin,
                                       coalesce((raw->>'trial')::boolean, false), raw->>'startingPrice',
                                       raw->>'trackCondition', raw->>'runners', raw->>'raceClass'
                                from fk.past_events where horse_id = %s order by event_date desc""", (hid,)).fetchall()
            print(f"\n{name} ({hid}): {len(rows)} starts stored")
            for d, trk, dist, fin, mar, trial, sp, cond, n, cls in rows:
                print(f"  {d} {'TRIAL ' if trial else ''}{trk} {dist}m finish {fin}{'/' + n if n else ''} margin {mar}"
                      f" SP {sp} {cond or ''} {cls or ''}")
