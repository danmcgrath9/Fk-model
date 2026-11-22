"""When does each meeting reach final fields? One week of watching, every state (founder, 23 Nov 2026: "Lets check for
the next week, because horse racing schedule is exactly the same every single week ... do it for every state so we know
exactly when we have to do all of them").

    python scripts/fields_watch.py --out data/schedule/fields-watch.csv [--states VIC,NSW,...] [--dry-run]

One Get Upcoming Meetings call for every state at once (1 credit; the same call daily_pull.py makes, with the states
comma separated). It appends a row to OUT for every meeting seen for the first time and for every meeting whose status
has changed since its last row: observed_utc, date, state, track, status, races, meeting_id. Run every 15 minutes
(fk-fields-watch.yml), the first FINAL_FIELDS row of a meeting is when its acceptances were out, to within 15 minutes.
The market-open side comes free afterwards from Betwatch's first-price times (TAB's first price, by the minute).
Nothing else is fetched and nothing is written to the database.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import datetime, timezone

from _common import bootstrap, confirm, make_client
from fk import fields as F
from fk import ops

COLS = ["observed_utc", "date", "state", "track", "status", "races", "meeting_id"]
ALL_STATES = "VIC,NSW,QLD,SA,WA,TAS,ACT,NT"


def last_status(path: str) -> dict[str, str]:
    """The status each meeting had in its latest row, so an unchanged meeting is not written again."""
    out: dict[str, str] = {}
    if os.path.exists(path):
        with open(path, newline="") as fh:
            for r in csv.DictReader(fh):
                out[r["meeting_id"]] = r["status"]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--states", default=ALL_STATES)
    ap.add_argument("--dry-run", action="store_true", help="plan and price the call only; no network")
    a = ap.parse_args()

    settings, spec, costs, ledger = bootstrap("live")
    client = make_client("live", settings, spec, costs, ledger, allow_live=False)
    call = client.plan(ops.UPCOMING_MEETINGS, states=a.states)
    print(f"{call.op.key} for {a.states}: {call.credits} credit (balance {ledger.balance()})")
    if a.dry_run:
        return
    if not confirm("watch", True, estimated=call.credits, balance=ledger.balance(), live=True):
        sys.exit("stopped")
    client.allow_live = True
    try:
        payload = client.execute(call)
    finally:
        client.allow_live = False

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    seen = last_status(a.out)
    new_rows = []
    for m in F.meetings_list(payload):
        mid, status = F.meeting_id(m), F.meeting_status(m)
        if seen.get(mid) == status:
            continue
        new_rows.append(dict(observed_utc=now, date=F.meeting_date(m), state=F.meeting_state(m), track=F.meeting_track(m),
                             status=status, races=len(F.meeting_races(m)), meeting_id=mid))
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    fresh = not os.path.exists(a.out)
    with open(a.out, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        if fresh:
            w.writeheader()
        w.writerows(new_rows)
    print(f"{len(F.meetings_list(payload))} meetings listed; {len(new_rows)} new or changed:")
    for r in new_rows:
        print(f"  {r['date']} {r['state']:4} {r['track']:24} {r['status']:16} {r['races']} races")


if __name__ == "__main__":
    main()
