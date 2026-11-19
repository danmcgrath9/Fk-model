"""Where the fk database's space goes, and how much of it is a second copy of something. Read-only.

    python scripts/db_space.py

Written 19 Nov 2026, when the project went read-only on the free plan at 1,510 MB. It answers the
three questions a cut has to answer before anything is deleted:
  - how big each table's rows, out-of-line jsonb (toast) and indexes are, and how much is dead rows
  - which indexes are never used (an unused index is space with no reader)
  - how much of each raw jsonb column is held twice: benchmarked_runs.raw is written from the same
    PastEvent dict as past_events.raw (scripts/daily_pull.py store_past_events), and entries of old
    resulted races are the ones scripts/db_to_history.py already knows how to move to the history files
Every statement is a SELECT; the connection is read-only on purpose.
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
        print(f"database {mb(q('select pg_database_size(current_database())')[0][0])}\n")

        print("## Tables (heap = rows, toast = big jsonb stored out of line)\n")
        print(f"{'table':18} {'total':>11} {'heap':>11} {'toast':>11} {'indexes':>11} {'live':>9} {'dead':>8}  last vacuum")
        for r in q("""select c.relname, pg_total_relation_size(c.oid), pg_relation_size(c.oid),
                             pg_table_size(c.oid) - pg_relation_size(c.oid), pg_indexes_size(c.oid),
                             s.n_live_tup, s.n_dead_tup, greatest(s.last_vacuum, s.last_autovacuum)
                      from pg_class c join pg_namespace n on n.oid = c.relnamespace
                      left join pg_stat_user_tables s on s.relid = c.oid
                      where n.nspname = 'fk' and c.relkind = 'r' order by 2 desc"""):
            print(f"{r[0]:18} {mb(r[1])} {mb(r[2])} {mb(r[3])} {mb(r[4])} {r[5] or 0:9d} {r[6] or 0:8d}  {r[7]}")

        print("\n## Indexes (scans since the stats were last reset)\n")
        for r in q("""select s.relname, s.indexrelname, pg_relation_size(s.indexrelid), s.idx_scan
                      from pg_stat_user_indexes s where s.schemaname = 'fk' order by 3 desc"""):
            print(f"{r[0]:18} {r[1]:42} {mb(r[2])} {r[3]:>10} scans")

        print("\n## Raw jsonb column sizes\n")
        for t in ("entries", "past_events", "benchmarked_runs", "horses", "odds_snapshots", "races"):
            n, s = q(f"select count(*), sum(pg_column_size(raw)) from fk.{t}")[0]
            print(f"fk.{t:17} {n:9d} rows, raw {mb(s)}")

        print("\n## benchmarked_runs.raw against past_events.raw for the same run\n")
        r = q("""select count(*), count(*) filter (where p.past_event_id is null),
                        count(*) filter (where p.past_event_id is not null and b.raw is distinct from p.raw),
                        sum(pg_column_size(b.raw)) filter (where b.raw = p.raw),
                        sum(pg_column_size(b.raw)) filter (where p.past_event_id is null or b.raw is distinct from p.raw)
                 from fk.benchmarked_runs b left join fk.past_events p on p.past_event_id = b.past_event_id""")[0]
        print(f"rows {r[0]}; no past_events row {r[1]}; raw differs {r[2]}")
        print(f"raw identical to past_events.raw: {mb(r[3])}; raw held only here: {mb(r[4])}")

        print("\n## fk.entries by the age of their race (scheduled_at), and whether the race has a result\n")
        for r in q("""select case when r.scheduled_at is null then 'no date'
                                  when r.scheduled_at >= now() - interval '21 days' then 'last 21 days'
                                  when r.scheduled_at >= now() - interval '60 days' then '21 to 60 days'
                                  else 'over 60 days' end as age,
                             (e.raw ? 'horseResult' or exists (select 1 from fk.results x where x.race_id = e.race_id)) as resulted,
                             count(*), count(distinct e.race_id), sum(pg_column_size(e.raw))
                      from fk.entries e join fk.races r using (race_id) group by 1, 2 order by 1, 2"""):
            print(f"{r[0]:14} resulted={str(r[1]):5} {r[2]:8d} runners {r[3]:6d} races, raw {mb(r[4])}")

        print("\n## fk.horses.raw (the profile payload) by when it was fetched\n")
        for r in q("""select case when raw is null then 'no raw'
                                  when profile_fetched_at >= now() - interval '30 days' then 'last 30 days'
                                  when profile_fetched_at is null then 'no profile date'
                                  else 'older' end, count(*), sum(pg_column_size(raw))
                      from fk.horses group by 1 order by 1"""):
            print(f"{r[0]:16} {r[1]:8d} horses, raw {mb(r[2])}")

        print("\n## fk.past_events by year of the run\n")
        for r in q("""select extract(year from event_date)::int, count(*), sum(pg_column_size(raw))
                      from fk.past_events group by 1 order by 1"""):
            print(f"{r[0]}  {r[1]:8d} runs, raw {mb(r[2])}")

        print("\n## fk.odds_snapshots by kind\n")
        for r in q("""select kind, source, count(*), sum(pg_column_size(raw)), count(distinct race_id)
                      from fk.odds_snapshots group by 1, 2 order by 3 desc"""):
            print(f"{r[0]:9} {r[1]:12} {r[2]:9d} rows, raw {mb(r[3])}, {r[4]} races")


if __name__ == "__main__":
    main()
