"""Read-only probe: do the live-pulled races' stored runners carry past-run benchmarks?"""
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common import load_settings  # noqa: E402
from fk import fields as F  # noqa: E402
from fk.db import Db  # noqa: E402

db = Db(load_settings().database_url)
pre = sorted(db.races_pulled_before_the_jump("VIC"))
print(len(pre), "live-pulled races")
tot = Counter()
for rid in pre[-12:]:
    rows = db.conn.execute("select horse_id, raw, fetched_at from fk.entries where race_id = %s", (rid,)).fetchall()
    c = Counter()
    for hid, raw, at in rows:
        evs = F.entry_past_events(raw or {})
        c["runners"] += 1
        c["events"] += len(evs)
        c["with_benchmark"] += sum(1 for p in evs if F.past_event_benchmark(p))
        c["runner_has_any"] += 1 if any(F.past_event_benchmark(p) for p in evs) else 0
    tot.update(c)
    at = rows[0][2] if rows else None
    print(rid, dict(c), "fetched", at)
    if rows:
        evs = F.entry_past_events(rows[0][1] or {})
        if evs:
            print("   first past event keys:", sorted(evs[0].keys())[:40])
print("total", dict(tot))
n = db.conn.execute("select count(*) from fk.benchmarked_runs").fetchone()[0]
print("benchmarked_runs rows", n)
