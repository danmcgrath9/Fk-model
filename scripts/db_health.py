"""Is the database writable, and how full is it? (18 Nov 2026: fk-odds failed with "cannot execute INSERT in a
read-only transaction"). Read-only queries only; no credits.    python scripts/db_health.py"""
import os
import psycopg
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    q = lambda s: c.execute(s).fetchall()
    print("host:", os.environ["DATABASE_URL"].split("@")[-1].split("/")[0].split(":")[0].split(".", 1)[-1])
    u = os.environ["DATABASE_URL"].split("//", 1)[-1].split("@")[0].split(":")[0]
    print("project ref:", u.split(".", 1)[1] if "." in u else "(not in the user name)")      # a project id, not a credential
    for s in ("show default_transaction_read_only", "show transaction_read_only", "select pg_is_in_recovery()", "select version()",
              "select pg_size_pretty(pg_database_size(current_database()))", "select current_user"):
        try: print(f"{s}: {q(s)[0][0]}")
        except Exception as e: print(f"{s}: ERROR {type(e).__name__}: {str(e)[:200]}"); c.rollback()
    try:
        for r in q("""select n.nspname || '.' || c.relname, pg_size_pretty(pg_total_relation_size(c.oid))
                      from pg_class c join pg_namespace n on n.oid = c.relnamespace
                      where c.relkind = 'r' and n.nspname not in ('pg_catalog', 'information_schema')
                      order by pg_total_relation_size(c.oid) desc limit 12"""):
            print("  ", r[0], r[1])
    except Exception as e:
        print("table sizes: ERROR", str(e)[:200])
    for s in ("select max(fetched_at) from fk.odds_snapshots", "select max(ts) from fk.credit_ledger"):
        try: print(f"{s}: {q(s)[0][0]}")
        except Exception as e: print(f"{s}: ERROR {str(e)[:150]}"); c.rollback()
    try:
        c.execute("create temporary table _w (x int)"); c.execute("insert into _w values (1)"); print("temp-table write: OK")
    except Exception as e:
        print("temp-table write: ERROR", type(e).__name__, str(e)[:200])
