"""Every runner's ratings and sectionals from one resulted meeting, for reading the day back.

    python scripts/meeting_ratings.py --key live --yes --date 2026-09-27 --track Caulfield

One Get Horse Form per runner (2 credits each at 5 benchmarks), past events stored as the daily
pull stores them. For the run ON --date it prints, per runner: finish, margin, SP, BSP, the
ratings (at weights, WFA, race rating, expected, vs class, speed, finishing speed), early pace
(settling position, 800m and 400m positions, run to the 600 vs class) and late pace (last 600 vs
class, each 200m split vs class, late-section ranks). A CSV is written to --out and echoed
between CSV-BEGIN / CSV-END markers so it can be read from the run log.
"""
from __future__ import annotations

import argparse
import csv
import io
import sys
from datetime import datetime, timezone
from pathlib import Path

from _common import bootstrap, confirm, make_client
from daily_pull import store_past_events
from fk import fields as F
from fk import ops
from fk.db import Db

COLS = ["race", "distance", "horse", "barrier", "jockey", "finish", "runners", "margin", "sp", "bsp",
        "at_weights", "wfa", "race_rating", "expected", "vs_class", "speed", "finishing_speed",
        "settle", "pos800", "pos400", "early_to600_vs_class", "late_last600_vs_class",
        "split_start", "split_1200_1000", "split_1000_800", "split_800_600", "split_600_400", "split_400_200", "split_200_f",
        "late_race_rank", "late_meet_rank"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", choices=["test", "live"], default="test")
    ap.add_argument("--date", required=True)
    ap.add_argument("--track", required=True)
    ap.add_argument("--state", default="VIC")
    ap.add_argument("--out", default="data/meeting_ratings")
    ap.add_argument("--yes", action="store_true")
    a = ap.parse_args()
    settings, spec, costs, ledger = bootstrap(a.key)
    db = Db(settings.database_url)
    races = [r for r in db.races_on(a.date, a.state) if (r["track"] or "").lower() == a.track.lower()]
    if not races:
        sys.exit(f"no {a.track} races stored for {a.date}")
    field = []
    for r in races:
        for e in db.entries_for_race(r["race_id"]):
            if not e["scratched"]:
                field.append((r, e))
    client = make_client(a.key, settings, spec, costs, ledger, allow_live=False)
    plans = [client.plan(ops.HORSE_FORM, horseId=e["horse_id"], numBenchmarks=5, racesOnly=False) for _, e in field]
    total = sum(p.credits for p in plans)
    if not confirm(f"{len(field)} horses, {total} credits?", a.yes, estimated=total, balance=ledger.balance(),
                   live=client.key_kind == "live"):
        sys.exit("stopped")
    rows = []
    client.allow_live = True
    try:
        for (r, e), plan in zip(field, plans):
            payload = client.execute(plan)
            events = F.horse_form_past_events(payload)
            store_past_events(db, e["horse_id"], events, datetime.now(timezone.utc))
            run = next((p for p in events if F.past_event_date(p) == a.date and not p.get("trial")), None)
            row = dict(race=r["race_number"], distance=r["distance_m"], horse=e["name"], barrier=e["barrier"], jockey=e["jockey"])
            if run is not None:
                q = F.run_ratings(run); m = F.run_market(run); pos = q.get("positions") or [None] * 8
                sp = F.run_splits_vs_class(run); rk = q.get("ranks") or {}
                row.update(finish=q.get("finish"), runners=q.get("runners"), margin=m.get("margin"), sp=m.get("sp"), bsp=m.get("bsp"),
                           at_weights=q.get("atWeights"), wfa=q.get("wfaRat") or q.get("wfa"), race_rating=q.get("raceRating"),
                           expected=q.get("expected"), vs_class=q.get("vsClass"), speed=q.get("speedRating"),
                           finishing_speed=q.get("finishingSpeed"), settle=pos[0], pos800=pos[3], pos400=pos[5],
                           early_to600_vs_class=q.get("to600"), late_last600_vs_class=q.get("last600"),
                           split_start=sp[0], split_1200_1000=sp[1], split_1000_800=sp[2], split_800_600=sp[3],
                           split_600_400=sp[4], split_400_200=sp[5], split_200_f=sp[6],
                           late_race_rank=rk.get("raceRank"), late_meet_rank=rk.get("meetRank"))
            rows.append(row)
            db.commit()
    finally:
        client.allow_live = False
    buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=COLS); w.writeheader()
    for row in sorted(rows, key=lambda x: (x["race"], x.get("finish") or 99)):
        w.writerow({k: (round(v, 2) if isinstance(v, float) else v) for k, v in row.items() if k in COLS})
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    path = out / f"{a.date}-{a.track.lower().replace(' ', '-')}.csv"; path.write_text(buf.getvalue())
    print("CSV-BEGIN"); print(buf.getvalue(), end=""); print("CSV-END")
    print(f"{len(rows)} runners, {sum(1 for x in rows if x.get('finish'))} with a run on {a.date}; ledger balance {ledger.balance()}")


if __name__ == "__main__":
    main()
