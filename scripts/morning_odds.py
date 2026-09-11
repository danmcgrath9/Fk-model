"""Morning odds pass: a second price snapshot for today's stored meetings.

  python scripts/morning_odds.py --key live [--date YYYY-MM-DD] [--yes]

One Get Meeting Summary per meeting (5 credits): the current best price, average price,
opening price and Form King's firmOrDrift for every runner, plus any scratchings, so the
report rebuilt afterwards carries the overnight market. Results for RESULTED races in the
same payload are stored too.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date

from _common import bootstrap, confirm, make_client, today_melbourne
from fk import fields as F
from fk import ops
from fk.db import Db, utc_now
from fk.estimate import estimate


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", choices=["test", "live"], default="test")
    ap.add_argument("--date", help="meeting date YYYY-MM-DD (default: today, Melbourne)")
    ap.add_argument("--state", default="VIC")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--yes", action="store_true")
    a = ap.parse_args()
    target = date.fromisoformat(a.date) if a.date else today_melbourne()

    settings, spec, costs, ledger = bootstrap(a.key)
    client = make_client(a.key, settings, spec, costs, ledger, allow_live=False)
    live = client.key_kind == "live"
    db = Db(settings.database_url)
    meetings = db.meetings_on(target.isoformat(), a.state)
    if not meetings:
        print(f"no {a.state} meetings stored for {target}; nothing to refresh")
        return
    plans = [(m, client.plan(ops.MEETING_SUMMARY, meetingId=m["meeting_id"])) for m in meetings]
    est = estimate([p for _, p in plans])
    print(f"{len(meetings)} {a.state} meeting(s) on {target}: " + ", ".join(m["track"] for m in meetings))
    print(est.render(ledger.balance() if live else None))
    if a.dry_run:
        return
    if not confirm("Refresh odds?", a.yes, estimated=est.total, balance=ledger.balance(), live=live):
        sys.exit("stopped")

    client.allow_live = True
    snapshots = results = 0
    try:
        for m, p in plans:
            payload = client.execute(p)
            at = utc_now()
            for r in F.meeting_races(payload):
                rid = F.race_id(r)
                for e in F.race_entries(r):
                    hid = F.horse_id(e)
                    db.upsert("horses", ["horse_id"], dict(horse_id=hid, name=F.horse_name(e), fetched_at=at))
                    # Refresh the entry (odds, scratching, ratings) without touching its past events.
                    db.upsert("entries", ["race_id", "horse_id"], dict(
                        race_id=rid, horse_id=hid, barrier=F.entry_barrier(e), weight_kg=F.entry_weight(e), jockey=F.entry_jockey(e),
                        trainer=F.entry_trainer(e), scratched=F.entry_scratched(e), neural_rating=F.entry_neural_rating(e),
                        exp_rating=F.entry_exp_rating(e), days_since_last_run=F.entry_days_since_last_run(e), raw=e, fetched_at=at))
                    odds = F.entry_odds(e)
                    if odds:
                        observed = F.odds_timestamp(odds) or at
                        for kind, price in (("opening", F.odds_opening_price(odds)), ("current", F.odds_current_price(odds))):
                            if price is not None:
                                db.upsert("odds_snapshots", ["race_id", "horse_id", "source", "kind", "observed_at"], dict(
                                    race_id=rid, horse_id=hid, source="formking", kind=kind, price=price, observed_at=observed, raw=odds, fetched_at=at))
                                snapshots += 1
                    res = F.entry_result(e)
                    if res and F.result_finish_position(res) is not None:
                        db.upsert("results", ["race_id", "horse_id"], dict(
                            race_id=rid, horse_id=hid, finish_position=F.result_finish_position(res), margin=F.result_margin(res),
                            starting_price=F.result_starting_price(res), raw=res, fetched_at=at))
                        results += 1
            db.commit()
    finally:
        client.allow_live = False
    print(f"done: {snapshots} price snapshots, {results} results. ledger balance {ledger.balance()}")


if __name__ == "__main__":
    main()
