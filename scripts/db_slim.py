"""Take the second copies out of the fk database so it can be written to again, losing nothing.

    python scripts/db_slim.py backup --out DIR            read-only: every byte the slim removes, to files
    python scripts/db_slim.py verify --check DIR          read-only: the files hold exactly what the database holds
    python scripts/db_slim.py apply  --check DIR --yes    verify again, remove the copies, give the disk back
    python scripts/db_slim.py restore --check DIR --yes   put benchmarked_runs.raw back from the files

19 Nov 2026. The project went read-only at 1,510 MB with its disk full (a plain SELECT died writing a
sort spill: "No space left on device"). scripts/db_space.py found two second copies:

  fk.benchmarked_runs.raw  written from the same PastEvent dict as fk.past_events.raw in the same call
                           (scripts/daily_pull.py store_past_events); 109 MB of it still identical
  fk.races.raw 'entries'   833 races carrying their runners again, which fetch_results.py re-added

The slim keeps benchmarked_runs.raw only where it differs from past_events.raw (a later past_events
write replaced it), and fk/db.py runs_for_horse reads past_events.raw for the rest, so every run the
form pages read comes back byte for byte (apply proves it row by row). The races lose only their
'entries' key, which every reader of races.raw ignores (sql/005).

Why TRUNCATE and not UPDATE: on a full disk an UPDATE needs room for new row versions and their
write-ahead log before it frees anything. TRUNCATE frees the table's files at commit with a few bytes
of log, and the verified files put the rows back into the space it freed. No statement sorts or
groups (a sort spill is what failed on the full disk): every check is a dictionary built in Python.

The database's own default is read-only; apply lifts it for its own session only
(SET SESSION CHARACTERISTICS), the route Supabase documents for getting back under a limit.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path

from psycopg import connect

from _common import load_settings

BENCH_COLS = ["run_id", "horse_id", "past_event_id", "event_date", "track_speed_verified",
              "sections", "positions", "vs_class", "raw", "fetched_at"]
# every column as Postgres prints it, so a restore through ::type is the same value
BENCH_SELECT = ", ".join(f"{c}::text" for c in BENCH_COLS)
BENCH_ROW_MD5 = "md5(concat_ws('|', " + ", ".join(f"coalesce({c}::text, '\\N')" for c in BENCH_COLS) + "))"


def md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def row_md5(vals: list) -> str:
    return md5("|".join("\\N" if v is None else v for v in vals))


def mb(n) -> str:
    return f"{(n or 0) / 1024 / 1024:.1f} MB"


def batches(conn, key_sql: str, rows_sql: str, size: int):
    """Rows a batch of keys at a time. No cursor and no sort: on 19 Nov even a server-side cursor
    wrote temporary files, and the full disk refused them. Each batch is a plain query on the
    primary key, which streams straight to us."""
    keys = [r[0] for r in conn.execute(key_sql).fetchall()]
    for i in range(0, len(keys), size):
        yield from conn.execute(rows_sql, (keys[i:i + size],)).fetchall()


def sizes(conn) -> str:
    db = conn.execute("select pg_database_size(current_database())").fetchone()[0]
    t = conn.execute("select pg_total_relation_size('fk.benchmarked_runs'), pg_total_relation_size('fk.races')").fetchone()
    return f"database {mb(db)}, fk.benchmarked_runs {mb(t[0])}, fk.races {mb(t[1])}"


def backup(a) -> None:
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    with connect(load_settings().database_url) as conn:
        conn.autocommit = True
        conn.read_only = True
        print(sizes(conn))
        man = {"bench": {}, "races": {}}
        with gzip.open(out / "bench.jsonl.gz", "wt", encoding="utf-8") as f:
            for row in batches(conn, "select run_id from fk.benchmarked_runs",
                               f"select {BENCH_SELECT} from fk.benchmarked_runs where run_id = any(%s)", 1000):
                vals = list(row)
                f.write(json.dumps(vals) + "\n")
                man["bench"][vals[0]] = row_md5(vals)
        with gzip.open(out / "races.jsonl.gz", "wt", encoding="utf-8") as f:
            for rid, raw in batches(conn, "select race_id from fk.races where raw ? 'entries'",
                                    "select race_id, raw::text from fk.races where race_id = any(%s)", 25):
                f.write(json.dumps([rid, raw]) + "\n")
                man["races"][rid] = md5(raw)
        (out / "manifest.json").write_text(json.dumps(man), encoding="utf-8")
        print(f"backed up {len(man['bench'])} benchmarked_runs rows and {len(man['races'])} races with their runners")
        print(f"files: bench {mb((out / 'bench.jsonl.gz').stat().st_size)}, races {mb((out / 'races.jsonl.gz').stat().st_size)} (gzip)")


def read_files(d: Path):
    """The backup, checked against its own manifest: a file that does not match it is refused."""
    man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    bench = {}
    with gzip.open(d / "bench.jsonl.gz", "rt", encoding="utf-8") as f:
        for line in f:
            vals = json.loads(line)
            if row_md5(vals) != man["bench"].get(vals[0]):
                sys.exit(f"REFUSED: bench row {vals[0]} in the file does not match the manifest")
            bench[vals[0]] = vals
    races = {}
    with gzip.open(d / "races.jsonl.gz", "rt", encoding="utf-8") as f:
        for line in f:
            rid, raw = json.loads(line)
            if md5(raw) != man["races"].get(rid):
                sys.exit(f"REFUSED: race {rid} in the file does not match the manifest")
            races[rid] = raw
    if len(bench) != len(man["bench"]) or len(races) != len(man["races"]):
        sys.exit(f"REFUSED: the files hold {len(bench)} runs and {len(races)} races, the manifest {len(man['bench'])} and {len(man['races'])}")
    return man, bench, races


def check_against_db(conn, man) -> tuple[int, int]:
    """Every row the slim will touch is in the files exactly. Returns (bench rows, races) in the DB."""
    db_bench = {k: v for k, v in conn.execute(f"select run_id, {BENCH_ROW_MD5} from fk.benchmarked_runs").fetchall()}
    if db_bench:
        missing = [k for k, v in db_bench.items() if man["bench"].get(k) != v]
        if missing:
            sys.exit(f"REFUSED: {len(missing)} benchmarked_runs rows are not in the files as they are now, e.g. {missing[:3]}")
    db_races = {k: v for k, v in conn.execute("select race_id, md5(raw::text) from fk.races where raw ? 'entries'").fetchall()}
    missing = [k for k, v in db_races.items() if man["races"].get(k) != v]
    if missing:
        sys.exit(f"REFUSED: {len(missing)} races carrying runners are not in the files as they are now, e.g. {missing[:3]}")
    return len(db_bench), len(db_races)


def verify(a) -> None:
    man, bench, races = read_files(Path(a.check))
    with connect(load_settings().database_url) as conn:
        conn.read_only = True
        nb, nr = check_against_db(conn, man)
    print(f"verified: the files hold all {nb} benchmarked_runs rows and all {nr} races with runners, byte for byte")


def apply(a) -> None:
    if not a.yes:
        sys.exit("apply removes data from the database: pass --yes")
    man, bench, races = read_files(Path(a.check))
    with connect(load_settings().database_url, autocommit=True) as conn:
        print("before: " + sizes(conn))
        nb, nr = check_against_db(conn, man)
        if nb not in (0, len(bench)):
            sys.exit(f"REFUSED: the table holds {nb} rows and the files {len(bench)}; take a fresh backup")
        conn.execute("set session characteristics as transaction read write")

        # 1. benchmarked_runs: empty it (frees its disk at once), then reload from the verified files,
        #    raw kept only where past_events.raw for the same run is not the same jsonb.
        conn.execute("alter table fk.benchmarked_runs alter column raw drop not null")
        if nb:
            conn.execute("truncate fk.benchmarked_runs")
            print("after emptying benchmarked_runs: " + sizes(conn))
        pe = {k: v for k, v in conn.execute(
            "select past_event_id, md5(raw::text) from fk.past_events where past_event_id = any(%s)",
            ([v[2] for v in bench.values() if v[2]],)).fetchall()}
        kept = 0
        with conn.transaction():
            with conn.cursor().copy(f"copy fk.benchmarked_runs ({', '.join(BENCH_COLS)}) from stdin") as cp:
                for vals in bench.values():
                    raw = vals[8]
                    same = vals[2] is not None and pe.get(vals[2]) == md5(raw) and "benchmark" in json.loads(raw)
                    kept += not same
                    cp.write_row(vals[:8] + [None if same else raw] + vals[9:])
        print(f"reloaded {len(bench)} runs: {kept} keep their own raw, {len(bench) - kept} read past_events.raw")

        # The proof: every run reads back, through the same expression fk/db.py runs_for_horse uses,
        # exactly as it was before the slim, and every other column is unchanged.
        back = {k: (r, rest) for k, r, rest in conn.execute(
            """select b.run_id, md5(coalesce(b.raw, case when p.raw ? 'benchmark' then p.raw end)::text),
                      md5(concat_ws('|', b.horse_id, coalesce(b.past_event_id, '\\N'), coalesce(b.event_date::text, '\\N'),
                          b.track_speed_verified::text, coalesce(b.sections::text, '\\N'), coalesce(b.positions::text, '\\N'),
                          coalesce(b.vs_class::text, '\\N'), b.fetched_at::text))
               from fk.benchmarked_runs b left join fk.past_events p on p.past_event_id = b.past_event_id""").fetchall()}
        bad = [k for k, v in bench.items()
               if k not in back or back[k][0] != md5(v[8])
               or back[k][1] != row_md5([v[1], v[2], v[3], v[4], v[5], v[6], v[7], v[9]])]
        if bad or len(back) != len(bench):
            sys.exit(f"STOPPED: {len(bad)} runs do not read back as they were, e.g. {bad[:3]}; "
                     f"run restore from the same files to put every raw back")
        print(f"proved: all {len(back)} runs read back byte for byte")

        # 2. races: the runners come out of races.raw; nothing else in the row moves.
        if races:
            want = {k: v for k, v in conn.execute(
                "select race_id, md5((raw - 'entries')::text) from fk.races where raw ? 'entries'").fetchall()}
            conn.execute("update fk.races set raw = raw - 'entries' where raw ? 'entries'")
            got = {k: v for k, v in conn.execute(
                "select race_id, md5(raw::text) from fk.races where race_id = any(%s)", (list(want),)).fetchall()}
            bad = [k for k in want if got.get(k) != want[k]]
            if bad:
                sys.exit(f"STOPPED: {len(bad)} races changed beyond losing their runners, e.g. {bad[:3]}")
            conn.execute("vacuum full fk.races")
            print(f"took the runners out of {len(want)} races (each race's own facts unchanged)")
        conn.execute("vacuum analyze fk.benchmarked_runs")
        print("after: " + sizes(conn))


def restore(a) -> None:
    if not a.yes:
        sys.exit("restore writes to the database: pass --yes")
    man, bench, races = read_files(Path(a.check))
    with connect(load_settings().database_url, autocommit=True) as conn:
        conn.execute("set session characteristics as transaction read write")
        n = 0
        with conn.transaction():
            for k, vals in bench.items():
                n += conn.execute("update fk.benchmarked_runs set raw = %s::jsonb where run_id = %s and raw is null",
                                  (vals[8], k)).rowcount
        print(f"restored raw on {n} runs; the races' runners are in races.jsonl.gz if they are ever wanted")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("step", choices=["backup", "verify", "apply", "restore"])
    p.add_argument("--out"); p.add_argument("--check"); p.add_argument("--yes", action="store_true")
    a = p.parse_args()
    {"backup": backup, "verify": verify, "apply": apply, "restore": restore}[a.step](a)


if __name__ == "__main__":
    main()
