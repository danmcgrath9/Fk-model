"""Take the duplicated runners out of fk.races and give the space back to the disk.

    python scripts/db_reclaim.py

Applies sql/005 (idempotent), then VACUUM FULL fk.races, which rewrites the table at its
new size and returns the rest to the operating system. VACUUM FULL cannot run inside a
transaction, so it runs on an autocommit connection. It needs room for one copy of the
table at its NEW size, which after the strip is about a megabyte, so it is safe on a
nearly full disk. Prints the size before and after.
"""
from __future__ import annotations

from pathlib import Path

from psycopg import connect

from _common import load_settings

ROOT = Path(__file__).resolve().parents[1]


def size(conn, rel: str) -> str:
    n = conn.execute(f"select pg_total_relation_size('{rel}')").fetchone()[0]
    return f"{n / 1024 / 1024:.1f} MB"


def main() -> None:
    url = load_settings().database_url
    with connect(url, autocommit=True) as conn:
        total = lambda: f"{conn.execute('select pg_database_size(current_database())').fetchone()[0] / 1024 / 1024:.1f} MB"
        print(f"before: database {total()}, fk.races {size(conn, 'fk.races')}")
        n = conn.execute("select count(*) from fk.races where raw ? 'entries'").fetchone()[0]
        print(f"races carrying a copy of their runners: {n}")
        conn.execute((ROOT / "sql" / "005_strip_race_entries.sql").read_text(encoding="utf-8"))
        conn.execute("vacuum full fk.races")
        print(f"after:  database {total()}, fk.races {size(conn, 'fk.races')}")


if __name__ == "__main__":
    main()
