"""What is on the fk database's DISK besides the tables, and what the big raw columns hold. Read-only.

    python scripts/db_disk.py

19 Nov 2026: a plain SELECT died on "No space left on device" writing a sort spill, so the disk
itself is full, not just a size quota. Before anything is deleted this says whether the space is
held by the write-ahead log (a stuck replication slot keeps WAL for ever, and dropping the slot
frees it with no data lost) or by the tables, and which keys inside races.raw and horses.raw are
the big ones. Every query is small and unsorted, so it cannot spill to the full disk.
"""
from __future__ import annotations

from psycopg import connect

from _common import load_settings


def mb(n) -> str:
    return f"{(n or 0) / 1024 / 1024:8.1f} MB"


def main() -> None:
    with connect(load_settings().database_url, autocommit=True) as conn:
        def q(s, *a):
            try:
                return conn.execute(s, a).fetchall()
            except Exception as e:  # a permission refusal is an answer too
                print(f"   ({type(e).__name__}: {str(e).splitlines()[0]})")
                return []
        print(f"database {mb(q('select pg_database_size(current_database())')[0][0])}")
        for name in ("max_wal_size", "min_wal_size", "wal_keep_size", "max_slot_wal_keep_size", "wal_level",
                     "archive_mode", "temp_file_limit", "default_transaction_read_only"):
            r = q("select setting, unit from pg_settings where name = %s", name)
            print(f"setting {name}: {r[0] if r else '?'}")
        print("\n## Write-ahead log")
        r = q("select count(*), sum(size) from pg_ls_waldir()")
        if r:
            print(f"WAL files {r[0][0]}, {mb(r[0][1])}")
        print("\n## Replication slots (an inactive slot keeps WAL until it is dropped)")
        for s in q("""select slot_name, slot_type, active, wal_status,
                             pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) from pg_replication_slots"""):
            print(f"{s[0]} {s[1]} active={s[2]} wal_status={s[3]} retaining {mb(s[4])}")
        print("(end of slots)")
        print("\n## Temporary files and other databases")
        for d in q("select datname, pg_database_size(datname), temp_files, temp_bytes from pg_stat_database where datname is not null"):
            print(f"{d[0]:20} {mb(d[1])} temp files {d[2]} ({mb(d[3])} since reset)")
        print("\n## Other schemas")
        for s in q("""select n.nspname, sum(pg_total_relation_size(c.oid)) from pg_class c join pg_namespace n on n.oid = c.relnamespace
                      where c.relkind in ('r','m') group by 1 order by 2 desc limit 12"""):
            print(f"{s[0]:20} {mb(s[1])}")
        print("\n## races.raw: the biggest keys over 60 races (no sort, a sample)")
        tot: dict[str, int] = {}
        for (raw,) in q("select raw from fk.races limit 60"):
            for k, v in (raw or {}).items():
                import json
                tot[k] = tot.get(k, 0) + len(json.dumps(v))
        for k, v in sorted(tot.items(), key=lambda kv: -kv[1])[:8]:
            print(f"   {k:30} {v / 60 / 1024:7.1f} KB a race")
        print(f"races still carrying their runners: {q(chr(115)+'elect count(*) from fk.races where raw ? %s', 'entries')}")
        print("\n## horses.raw: the biggest keys over 40 profiles")
        tot = {}
        for (raw,) in q("select raw from fk.horses where raw is not null limit 40"):
            for k, v in (raw or {}).items():
                import json
                tot[k] = tot.get(k, 0) + len(json.dumps(v))
        for k, v in sorted(tot.items(), key=lambda kv: -kv[1])[:8]:
            print(f"   {k:30} {v / 40 / 1024:7.1f} KB a horse")


if __name__ == "__main__":
    main()
