"""What a run of past-day pulls added, and what it cost (11 Nov 2026, the VIC gap fill). DB only, no credits.

    python scripts/gapfill_check.py --since-ts 2026-11-11T06:50:00Z 2026-09-12 2026-09-13 ...
Per date: the meetings now stored, races, races with a result. Then the live credits charged since --since-ts by
operation, the month's total, and every day since 1 Jul 2025 that still holds no Victorian meeting."""
from __future__ import annotations

import argparse
import os
from datetime import date, timedelta

import psycopg

ap = argparse.ArgumentParser(); ap.add_argument("--since-ts", required=True); ap.add_argument("dates", nargs="*")
a = ap.parse_args()
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    print("| date | meetings | races | resulted |\n|---|---|---|---|")
    for d in a.dates:
        rows = c.execute("""select m.track, m.state, count(r.race_id),
                                   count(r.race_id) filter (where exists (select 1 from fk.results x where x.race_id = r.race_id and x.finish_position is not null)
                                                            or exists (select 1 from fk.entries e where e.race_id = r.race_id and e.raw ? 'horseResult'))
                            from fk.meetings m left join fk.races r using (meeting_id)
                            where m.meeting_date = %s group by m.track, m.state order by m.state, m.track""", (d,)).fetchall()
        print(f"| {d} | {', '.join(f'{t} ({s})' for t, s, _, _ in rows) or 'none'} | {sum(r[2] for r in rows)} | {sum(r[3] for r in rows)} |")
    print("\nlive credits charged since", a.since_ts)
    tot = 0
    for op, n, cr in c.execute("""select operation, count(*), sum(credits) from fk.credit_ledger
                                  where key_kind = 'live' and ts >= %s group by operation order by 3 desc""", (a.since_ts,)):
        print(f"  {op}: {n} calls, {cr} credits"); tot += cr
    print(f"  total {tot}")
    for m, cr in c.execute("""select month, sum(credits) from fk.credit_ledger where key_kind in ('live','adjust')
                              group by month order by month desc limit 2"""):
        print(f"month {m}: {cr} credits")
    held = {r[0] for r in c.execute("select distinct meeting_date from fk.meetings where state = 'VIC' and meeting_date >= '2025-07-01'")}
    d, end, miss = date(2025, 7, 1), date.today(), []
    while d < end:
        if d not in held: miss.append(d.isoformat())
        d += timedelta(days=1)
    print(f"\ndays since 1 Jul 2025 with no VIC meeting in the database: {len(miss)}")
    print("  " + " ".join(miss))
