"""How much of the fk database could move out, and what each part is used for. Read-only.

    python scripts/db_plan.py

19 Nov 2026: Supabase's free plan keeps a project read-only while its database is over 500 MB
(supabase.com/docs/guides/platform/database-size, "Free Plan behavior"). After the slim it is
1,238 MB. This sizes every candidate so the cut can be chosen on numbers.
"""
from __future__ import annotations

from psycopg import connect

from _common import load_settings


def mb(n) -> str:
    return f"{(n or 0) / 1024 / 1024:8.1f} MB"


def main() -> None:
    with connect(load_settings().database_url) as conn:
        conn.read_only = True
        q = lambda s, *a: conn.execute(s, a).fetchall()
        print("## fk.entries by meeting date (raw = the runner with its whole form)\n")
        for r in q("""select case when m.meeting_date >= current_date - 7 then 'a: last 7 days'
                                  when m.meeting_date >= current_date - 21 then 'b: 8 to 21 days'
                                  when m.meeting_date >= current_date - 60 then 'c: 22 to 60 days'
                                  else 'd: over 60 days' end,
                             m.state = 'VIC',
                             count(*), sum(pg_column_size(e.raw))
                      from fk.entries e join fk.races r using (race_id) join fk.meetings m using (meeting_id)
                      group by 1, 2 order by 1, 2"""):
            print(f"{r[0]:18} VIC={str(r[1]):5} {r[2]:7d} runners, raw {mb(r[3])}")

        print("\n## fk.horses.raw (the last profile; the pricing reads it only within 12 hours of fetching it)\n")
        for r in q("""select profile_fetched_at > now() - interval '12 hours', raw is not null, count(*), sum(pg_column_size(raw))
                      from fk.horses group by 1, 2 order by 1, 2"""):
            print(f"fetched in the last 12h={r[0]} has raw={r[1]} {r[2]:7d} horses, raw {mb(r[3])}")

        print("\n## fk.odds_snapshots.raw\n")
        for r in q("""select kind, source, count(*), sum(pg_column_size(raw)) from fk.odds_snapshots group by 1, 2 order by 4 desc nulls last"""):
            print(f"{r[0]:9} {r[1]:10} {r[2]:8d} rows, raw {mb(r[3])}")
        r = q("""select count(*), sum(pg_column_size(s.raw)) from fk.odds_snapshots s join fk.results x using (race_id, horse_id)
                 where s.kind = 'starting' and s.raw = x.raw""")[0]
        print(f"starting rows whose raw is the same jsonb as fk.results.raw: {r[0]} rows, {mb(r[1])}")
        r = q("""select count(*), sum(pg_column_size(o.raw)) from fk.odds_snapshots o join fk.odds_snapshots c
                   on c.race_id = o.race_id and c.horse_id = o.horse_id and c.source = o.source and c.observed_at = o.observed_at
                   and c.kind = 'current' where o.kind = 'opening' and o.raw = c.raw""")[0]
        print(f"opening rows whose raw is the same jsonb as the current row beside them: {r[0]} rows, {mb(r[1])}")

        print("\n## fk.past_events by whether the horse has run in a stored race lately\n")
        for r in q("""with recent as (select distinct e.horse_id from fk.entries e join fk.races r using (race_id)
                                      join fk.meetings m using (meeting_id) where m.meeting_date >= current_date - 120)
                      select case when p.horse_id in (select horse_id from recent) then 'horse in a stored field, last 120 days'
                                  else 'horse in no stored field for 120 days' end,
                             count(*), count(distinct p.horse_id), sum(pg_column_size(p.*))
                      from fk.past_events p group by 1 order by 1"""):
            print(f"{r[0]:40} {r[1]:7d} runs, {r[2]:6d} horses, rows {mb(r[3])}")
        for r in q("""select event_date < current_date - 730, count(*), sum(pg_column_size(p.*)) from fk.past_events p group by 1"""):
            print(f"run over two years old={r[0]} {r[1]:7d} runs, rows {mb(r[2])}")
        print(f"\ndatabase {mb(q('select pg_database_size(current_database())')[0][0])}")


if __name__ == "__main__":
    main()
