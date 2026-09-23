"""After a copy, prove the new database holds what the old one does: every fk table's row
count, side by side, and that each table's browser roles are still shut out. Exits non-zero
on any difference, so the job that copied fails loudly rather than leaving a half-copy
looking finished.

    OLD_DATABASE_URL=... NEW_DATABASE_URL=... python scripts/db_copy_check.py
"""
from __future__ import annotations

import os
import sys

from psycopg import connect

TABLES_SQL = """select c.relname from pg_class c join pg_namespace n on n.oid = c.relnamespace
                where n.nspname = 'fk' and c.relkind = 'r' order by 1"""


def counts(url: str) -> dict[str, int]:
    with connect(url) as conn:
        names = [r[0] for r in conn.execute(TABLES_SQL).fetchall()]
        return {t: conn.execute(f"select count(*) from fk.{t}").fetchone()[0] for t in names}


def browser_grants(url: str) -> list[tuple[str, str]]:
    """Any fk table the anon or authenticated role can touch. Supabase grants both on every
    new table by default; the schema revokes them, and a copy must keep that."""
    with connect(url) as conn:
        return conn.execute(
            """select table_name, grantee from information_schema.role_table_grants
               where table_schema = 'fk' and grantee in ('anon', 'authenticated')
               group by 1, 2 order by 1, 2"""
        ).fetchall()


def main() -> None:
    old, new = counts(os.environ["OLD_DATABASE_URL"]), counts(os.environ["NEW_DATABASE_URL"])
    bad = False
    print(f"{'table':20} {'old':>10} {'new':>10}")
    for t in sorted(set(old) | set(new)):
        o, n = old.get(t), new.get(t)
        mark = "" if o == n else "   <-- DIFFERENT"
        bad |= o != n
        print(f"{t:20} {str(o):>10} {str(n):>10}{mark}")
    leaks = browser_grants(os.environ["NEW_DATABASE_URL"])
    if leaks:
        bad = True
        print("browser roles can reach: " + ", ".join(f"{t} ({g})" for t, g in leaks))
    print("COPY VERIFIED" if not bad else "COPY DOES NOT MATCH")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
