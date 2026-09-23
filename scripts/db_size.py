"""How much disk the fk schema is using, table by table, largest first. Read-only.

    python scripts/db_size.py

The back-test's fit died on "No space left on device" after the June and July pull, and
Postgres keeps its sort spill files on the same disk as the data, so a nearly full database
fails the heavy read first and the daily pull's writes next. This says which it is.
"""
from __future__ import annotations

from _common import load_settings
from fk.db import Db


def mb(n: int | None) -> str:
    return f"{(n or 0) / 1024 / 1024:9.1f} MB"


def main() -> None:
    db = Db(load_settings().database_url)
    total = db.conn.execute("select pg_database_size(current_database())").fetchone()[0]
    print(f"database total {mb(total)}")
    rows = db.conn.execute(
        """select c.relname, pg_total_relation_size(c.oid), pg_relation_size(c.oid),
                  pg_total_relation_size(c.oid) - pg_relation_size(c.oid) - coalesce(pg_indexes_size(c.oid), 0),
                  pg_indexes_size(c.oid), c.reltuples::bigint
           from pg_class c join pg_namespace n on n.oid = c.relnamespace
           where n.nspname = 'fk' and c.relkind = 'r'
           order by pg_total_relation_size(c.oid) desc"""
    ).fetchall()
    print(f"{'table':20} {'total':>12} {'heap':>12} {'toast':>12} {'indexes':>12} {'rows':>10}")
    for name, tot, heap, toast, idx, n in rows:
        print(f"{name:20} {mb(tot)} {mb(heap)} {mb(toast)} {mb(idx)} {n:10d}")
    other = db.conn.execute(
        """select coalesce(sum(pg_total_relation_size(c.oid)), 0) from pg_class c
           join pg_namespace n on n.oid = c.relnamespace
           where n.nspname not in ('fk', 'pg_catalog', 'information_schema') and c.relkind = 'r'"""
    ).fetchone()[0]
    print(f"everything outside fk {mb(other)}")


if __name__ == "__main__":
    main()
