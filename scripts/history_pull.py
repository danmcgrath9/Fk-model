"""Pull one past day for the back-test into a compressed file, not the database.

  python scripts/history_pull.py --key live --yes --date 2026-04-12 --out history

Flow, the same calls the back-test pull has always made: Get Meetings By Date (1 credit)
-> per meeting Get Meeting Speedmaps (5) and per race Get Race Form at numBenchmarks=5
(2). No horse profiles. A race already held, in the database or in any file under
--out, is never paid for twice.

What is written is one gzip file per day (fk/history.py), holding exactly what the fit
reads. The database is only read (which races it holds) and the credit ledger written.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from _common import bootstrap, confirm, make_client, today_melbourne
from daily_pull import meetings_call, select_meetings
from fk import fields as F
from fk import history as H
from fk import ops
from fk.client import FormKingError
from fk.db import Db
from fk.estimate import estimate


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", choices=["test", "live"], default="test")
    ap.add_argument("--date", required=True, help="a day already run, YYYY-MM-DD")
    ap.add_argument("--state", default="VIC")
    ap.add_argument("--out", default="history", help="directory of day files")
    ap.add_argument("--track", help="only these tracks, comma separated prefixes")
    ap.add_argument("--yes", action="store_true", help="unattended: the credit cap and balance floor decide")
    a = ap.parse_args()

    target = date.fromisoformat(a.date)
    today = today_melbourne()
    if target >= today:
        sys.exit(f"{target} has not finished racing; history is for days already run")
    settings, spec, costs, ledger = bootstrap(a.key)
    client = make_client(a.key, settings, spec, costs, ledger, allow_live=False)
    live = client.key_kind == "live"
    out = Path(a.out)

    first = meetings_call(client, target, today, a.state)
    print(f"{target} {a.state}: step 1 is {first.op.key} for {first.credits} credit (balance {ledger.balance()})")
    if not confirm(f"Make the {first.op.key} call?", a.yes, estimated=first.credits, balance=ledger.balance(), live=live):
        sys.exit("stopped")
    client.allow_live = True
    try:
        payload = client.execute(first)
    finally:
        client.allow_live = False

    meetings = [m for m in F.meetings_list(payload) if F.meeting_date(m) == target.isoformat()]
    meetings = select_meetings(meetings, a.track, None)

    # Never pay twice for a race: skip what the database holds and what any file holds.
    db = Db(settings.database_url)
    held = db.races_fetched_since(datetime(1970, 1, 1, tzinfo=timezone.utc)) | H.held_race_ids(out)
    kept = []
    for m in meetings:
        m = dict(m)
        m["races"] = [r for r in F.meeting_races(m) if F.race_id(r) not in held]
        if m["races"]:
            kept.append(m)
        else:
            print(f"  {F.meeting_track(m)}: every race already held; skipped")
    meetings = kept
    if not meetings:
        print("nothing new to fetch")
        return

    planned = []
    for m in meetings:
        for r in F.meeting_races(m):
            planned.append(("race", m, r, client.plan(ops.RACE_FORM, meetingId=F.meeting_id(m), raceId=F.race_id(r),
                                                       numBenchmarks=ops.RACE_FORM_BENCHMARKS, racesOnly=False,
                                                       runners=max(F.race_runner_count(r), 1))))
    for m in meetings:   # after the forms: a speedmap failure must never cost the race data
        planned.append(("speedmaps", m, None, client.plan(ops.MEETING_SPEEDMAPS, meetingId=F.meeting_id(m))))
    est = estimate([p for *_, p in planned])
    print(f"\n{len(meetings)} {a.state} meeting(s) on {target}: " + ", ".join(f"{F.meeting_track(m)} ({len(F.meeting_races(m))} races)" for m in meetings))
    print(est.render(ledger.balance() if live else None))
    if not confirm("Proceed?", a.yes, estimated=est.total, balance=ledger.balance(), live=live):
        sys.exit("stopped")

    forms: list[tuple[dict, dict]] = []         # (meeting, race form payload)
    speedmaps: dict[str, dict] = {}              # race id -> speedmap
    failures = []
    client.allow_live = True
    try:
        for kind, m, r, p in planned:
            try:
                got = client.execute(p)
            except FormKingError as e:
                failures.append(f"{p.op.key} {p.params}: HTTP {e.status} {e.body[:120]}")
                print(f"FAILED {failures[-1]}")
                continue
            if kind == "race":
                forms.append((m, got))
            else:
                for sm in F.speedmap_list(got):
                    speedmaps[F.speedmap_race_id(sm)] = sm
    finally:
        client.allow_live = False

    bundles = [H.race_bundle(m, form, speedmaps.get(F.race_id(form))) for m, form in forms]
    if bundles:
        path = H.write_day(out, target.isoformat(), bundles)
        runners = sum(len(b["entries"]) for b in bundles)
        resulted = sum(1 for b in bundles if H.is_resulted(b))
        print(f"stored {runners} runners across {len(bundles)} of {sum(1 for k, *_ in planned if k == 'race')} races "
              f"({resulted} with results) in {path} ({path.stat().st_size // 1024} KB)")
    if failures:
        print(f"\n{len(failures)} call(s) failed and were skipped:")
        for f in failures:
            print("  " + f)
    print(f"done. ledger balance {ledger.balance()}")


if __name__ == "__main__":
    main()
