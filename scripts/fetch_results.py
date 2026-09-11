"""Next-morning results and final odds for yesterday's VIC races (Phase 0, item 5).

  python scripts/fetch_results.py --key test --dry-run
  python scripts/fetch_results.py --key live [--date YYYY-MM-DD]

One Get Meeting Summary per stored meeting (5 credits): every race's entries with
horseResult (finish, margin, SP, Betfair SP) and the closing odds.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta

from _common import bootstrap, confirm, make_client, today_melbourne
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
    live = client.key_kind == "live"
    db = Db(settings.database_url)
    meetings = db.meetings_on(target.isoformat(), a.state)
    if not meetings:
        sys.exit(f"no {a.state} meetings stored for {target}; run daily_pull.py for that date first")

    plans = [(m, client.plan(ops.MEETING_SUMMARY, meetingId=m["meeting_id"])) for m in meetings]
    est = estimate([p for _, p in plans])
    print(f"{len(meetings)} {a.state} meeting(s) on {target}: " + ", ".join(m["track"] for m in meetings))
    print(est.render(ledger.balance() if live else None))
    if a.dry_run:
        return
    if not confirm("Proceed?", a.yes, estimated=est.total, balance=ledger.balance(), live=live):
        sys.exit("stopped")

    client.allow_live = True
    stored = 0
    try:
        for m, p in plans:
            payload = client.execute(p)
            at = utc_now()
            for r in F.meeting_races(payload):
                rid = F.race_id(r)
                db.upsert("races", ["race_id"], dict(race_id=rid, meeting_id=m["meeting_id"], race_number=F.race_number(r),
                                                    race_name=F.race_name(r), distance_m=F.race_distance(r), raw=r, fetched_at=at))
                for e in F.race_entries(r):
                    hid = F.horse_id(e)
                    db.upsert("horses", ["horse_id"], dict(horse_id=hid, name=F.horse_name(e), fetched_at=at))
                    res = F.entry_result(e)
                    if res:
                        db.upsert("results", ["race_id", "horse_id"], dict(
                            race_id=rid, horse_id=hid, finish_position=F.result_finish_position(res), margin=F.result_margin(res),
                            starting_price=F.result_starting_price(res), raw=res, fetched_at=at))
                        stored += 1
                        for source, price in (("formking", F.result_starting_price(res)), ("betfair", F.result_betfair_sp(res))):
                            if price is not None:
                                db.upsert("odds_snapshots", ["race_id", "horse_id", "source", "kind", "observed_at"], dict(
                                    race_id=rid, horse_id=hid, source=source, kind="starting", price=price, observed_at=at, raw=res, fetched_at=at))
                    odds = F.entry_odds(e)
                    if odds and F.odds_current_price(odds) is not None:
                        db.upsert("odds_snapshots", ["race_id", "horse_id", "source", "kind", "observed_at"], dict(
                            race_id=rid, horse_id=hid, source="formking", kind="current", price=F.odds_current_price(odds),
                            observed_at=F.odds_timestamp(odds) or at, raw=odds, fetched_at=at))
            db.commit()
    finally:
        client.allow_live = False
    print(f"done: {stored} results stored. ledger balance {ledger.balance()}")


if __name__ == "__main__":
    main()
