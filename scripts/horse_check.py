"""One horse, from Form King: its latest runs with finish, margin, price and every rating,
and the past events stored so the report and the back-test see them.

    python scripts/horse_check.py --key live --name "Cavill Avenue" --yes
    python scripts/horse_check.py --key live --horse-id 2021_capitalist_cavill --yes

The name is looked up in fk.horses (a horse we have held before); an id from Form King's
own URLs works without that. Costs 2 credits plus 0.5 per benchmarked run beyond five.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from _common import bootstrap, confirm, make_client
from daily_pull import store_past_events
from fk import fields as F
from fk import ops
from fk.db import Db


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", choices=["test", "live"], default="test")
    ap.add_argument("--name")
    ap.add_argument("--horse-id")
    ap.add_argument("--benchmarks", type=int, default=5)
    ap.add_argument("--yes", action="store_true")
    a = ap.parse_args()
    settings, spec, costs, ledger = bootstrap(a.key)
    db = Db(settings.database_url)
    hid = a.horse_id
    if not hid:
        if not a.name:
            sys.exit("give --name or --horse-id")
        row = db.conn.execute("select horse_id, name from fk.horses where lower(name) = lower(%s) limit 1", (a.name,)).fetchone()
        if not row:
            sys.exit(f"no horse named {a.name!r} in the database; give --horse-id from Form King")
        hid = row[0]
        print(f"{row[1]}: {hid}")
    client = make_client(a.key, settings, spec, costs, ledger, allow_live=False)
    plan = client.plan(ops.HORSE_FORM, horseId=hid, numBenchmarks=a.benchmarks, racesOnly=False)
    if not confirm(f"Get Horse Form for {hid} ({plan.credits} credits, {client.key_kind} key)?", a.yes,
                   estimated=plan.credits, balance=ledger.balance(), live=client.key_kind == "live"):
        sys.exit("stopped")
    client.allow_live = True
    try:
        payload = client.execute(plan)
    finally:
        client.allow_live = False
    events = F.horse_form_past_events(payload)
    store_past_events(db, hid, events, datetime.now(timezone.utc))   # the one writer the daily pull uses
    db.commit()
    print(f"{F.horse_form_name(payload) or hid}: {len(events)} past events stored")
    runs = sorted([p for p in events if F.past_event_date(p)], key=F.past_event_date, reverse=True)[:max(5, a.benchmarks)]
    for p in runs:
        r = F.run_ratings(p)
        m = F.run_market(p)
        kind = "trial" if r.get("trial") else "race"
        print(f"  {r['date']}  {r.get('track') or '?':18} {r.get('distance') or '?'}m  {kind:5}  finish {r.get('finish')}/{r.get('runners')}"
              f"  margin {m.get('margin')}  SP {m.get('sp')}  BSP {m.get('bsp')}"
              f"\n      at weights {r.get('atWeights')}  adj today {r.get('adjToday')}  WFA {r.get('wfaRat') or r.get('wfa')}"
              f"  race rating {r.get('raceRating')}  expected {r.get('expected')}  vs class {r.get('vsClass')}"
              f"  speed {r.get('speedRating')}  finishing speed {r.get('finishingSpeed')}  ranks {r.get('ranks')}"
              f"  {'verified' if r.get('trackSpeedVerified') else 'unverified'}")
        b = p.get("benchmark") or {}
        if b:
            pir = [(k, b.get(k)) for k in ("pir12", "pir10", "pir8", "pir6", "pir4", "pir2") if b.get(k) is not None]
            print(f"      stage {b.get('dataStage')}  positions " + "  ".join(f"{k[3:]}00m {v}" for k, v in pir))
        order = ["S-12", "12-10", "10-8", "8-6", "6-4", "4-2", "2-F", "S-10", "S-8", "S-6", "S-4", "8-4", "12-F", "10-F", "8-F", "6-F", "4-F"]
        secs = b.get("sections") or {}
        for key in sorted(secs, key=lambda k: order.index(k) if k in order else 99):
            v = secs[key]
            print(f"      {key:6} vs leader {v.get('vsLeader'):+6.2f}L  vs field {v.get('vsField'):+6.2f}L  vs winner {v.get('vsWinner'):+6.2f}L"
                  f"  vs class {v.get('vsClass'):+6.2f}L" + (f"  race rank {v['raceRank']}" if v.get('raceRank') else ""))
    print(f"ledger balance {ledger.balance()}")


if __name__ == "__main__":
    main()
