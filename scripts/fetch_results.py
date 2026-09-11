"""Next-morning results and final odds for yesterday's VIC races (Phase 0, item 5).

  python scripts/fetch_results.py --key test --dry-run
  python scripts/fetch_results.py --key live [--date YYYY-MM-DD]

Reads the races we stored for that date (no meetings call), prices one results call and
one odds call per race, prints the estimate, asks, then runs.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta

from _common import bootstrap, confirm, make_client, today_melbourne
from daily_pull import _id_param
from fk import fields as F
from fk import ops
from fk.db import Db, utc_now
from fk.estimate import estimate


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", choices=["test", "live"], default="test")
    ap.add_argument("--date", help="race date YYYY-MM-DD (default: yesterday, Melbourne)")
    ap.add_argument("--state", default="VIC")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--yes", action="store_true")
    a = ap.parse_args()
    target = date.fromisoformat(a.date) if a.date else today_melbourne() - timedelta(days=1)

    settings, spec, costs, ledger = bootstrap(a.key)
    client = make_client(a.key, settings, spec, costs, ledger, allow_live=False)
    db = Db(settings.database_url)
    races = db.races_on(target.isoformat(), a.state)
    if not races:
        sys.exit(f"no {a.state} races stored for {target}; run daily_pull.py for that date first")

    plans = []
    for r in races:
        plans.append((r, client.plan(ops.RACE_RESULTS, **_id_param(spec, ops.RACE_RESULTS, r["race_id"]))))
        plans.append((r, client.plan(ops.RACE_ODDS, **_id_param(spec, ops.RACE_ODDS, r["race_id"]))))
    print(f"{len(races)} {a.state} races on {target}")
    est = estimate([p for _, p in plans])
    print(est.render(ledger.balance() if client.key_kind == "live" else None))
    if a.dry_run:
        return
    if not confirm("Proceed?", a.yes, estimated=est.total, balance=ledger.balance(), live=client.key_kind == "live"):
        sys.exit("stopped")

    client.allow_live = True
    try:
        for r, p in plans:
            payload = client.execute(p)
            at = utc_now()
            rid = r["race_id"]
            if p.op.key == spec.find_operation(ops.RACE_RESULTS).key:
                for x in F.results_list(payload):
                    db.upsert("results", ["race_id", "horse_id"], dict(
                        race_id=rid, horse_id=F.horse_id(x), finish_position=F.run_finish_position(x),
                        margin=F.result_margin(x), starting_price=F.odds_starting_price(x), raw=x, fetched_at=at))
            else:
                for x in F.odds_list(payload):
                    hid = F.horse_id(x)
                    for kind, price in (("opening", F.odds_opening_price(x)), ("current", F.odds_current_price(x)), ("starting", F.odds_starting_price(x))):
                        if price is not None:
                            db.upsert("odds_snapshots", ["race_id", "horse_id", "source", "kind", "observed_at"], dict(
                                race_id=rid, horse_id=hid, source="formking", kind=kind, price=price, observed_at=at, raw=x, fetched_at=at))
            db.commit()
    finally:
        client.allow_live = False
    print(f"done. ledger balance {ledger.balance()}")


if __name__ == "__main__":
    main()
