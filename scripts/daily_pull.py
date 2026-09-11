"""Daily pull for Victoria (Phase 0, item 4), on the Form King Modellers API 1.0.8.

  python scripts/daily_pull.py --key test --dry-run       plan and price only, no network, no database
  python scripts/daily_pull.py --key test                  against FK-TEST-API-KEY
  python scripts/daily_pull.py --key live                  prints the estimate, asks, then runs

Flow: Get Upcoming Meetings filtered to the state (1 credit) -> keep meetings on --date
(default: tomorrow, Melbourne) at FINAL_FIELDS -> per meeting: Get Meeting Speedmaps
(5 credits) and per race Get Race Form at numBenchmarks=5 (2 credits; every runner's
newest five benchmarked runs and full race career) -> per horse never held before:
Get Horse Form at numBenchmarks=10 (5 credits) to fill in runs six to ten.

Each paid step is estimated and confirmed before it runs. Unattended (--yes), the credit
cap and the balance floor answer instead of a person.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta

from _common import bootstrap, confirm, make_client, today_melbourne
from fk import fields as F
from fk import ops
from fk.cache import decide_profile_fetch
from fk.client import PlannedCall
from fk.db import Db, utc_now
from fk.estimate import estimate

PULL_STATUSES = {"FINAL_FIELDS", "INTERIM_RESULTS", "RESULTED"}


def store_meeting(db: Db, m: dict, fetched_at: datetime) -> str:
    mid = F.meeting_id(m)
    db.upsert("meetings", ["meeting_id"], dict(
        meeting_id=mid, meeting_date=F.meeting_date(m), track=F.meeting_track(m), state=F.meeting_state(m),
        raw=m, fetched_at=fetched_at))
    return mid


def store_race(db: Db, mid: str, r: dict, fetched_at: datetime) -> str:
    rid = F.race_id(r)
    db.upsert("races", ["race_id"], dict(
        race_id=rid, meeting_id=mid, race_number=F.race_number(r), race_name=F.race_name(r),
        distance_m=F.race_distance(r), raw=r, fetched_at=fetched_at))
    return rid


def store_past_events(db: Db, hid: str, events: list[dict], fetched_at: datetime) -> int:
    """Race past events into past_events; those carrying a BenchmarkedRun also into
    benchmarked_runs. Returns the number of benchmarked runs stored."""
    stored = 0
    for p in events:
        if not F.past_event_is_race(p):
            continue
        rid = F.past_event_race_id(p)
        if not rid:
            continue
        pid = f"{hid}:{rid}"
        d = F.past_event_date(p)
        db.upsert("past_events", ["past_event_id"], dict(
            past_event_id=pid, horse_id=hid, event_date=d, track=F.past_event_track(p), distance_m=F.past_event_distance(p),
            finish_position=F.past_event_finish(p), margin=F.past_event_margin(p), raw=p, fetched_at=fetched_at))
        if F.past_event_benchmark(p):
            db.upsert("benchmarked_runs", ["run_id"], dict(
                run_id=pid, horse_id=hid, past_event_id=pid, event_date=d,
                track_speed_verified=F.past_event_track_speed_verified(p),
                sections=F.SPLIT_LABELS, positions=F.run_positions(p), vs_class=F.run_splits_vs_class(p),
                raw=p, fetched_at=fetched_at))
            stored += 1
    return stored


def store_entry(db: Db, rid: str, e: dict, at: datetime) -> str:
    hid = F.horse_id(e)
    db.upsert("horses", ["horse_id"], dict(horse_id=hid, name=F.horse_name(e), fetched_at=at))
    db.upsert("entries", ["race_id", "horse_id"], dict(
        race_id=rid, horse_id=hid, barrier=F.entry_barrier(e), weight_kg=F.entry_weight(e),
        jockey=F.entry_jockey(e), trainer=F.entry_trainer(e), scratched=F.entry_scratched(e),
        neural_rating=F.entry_neural_rating(e), exp_rating=F.entry_exp_rating(e),
        days_since_last_run=F.entry_days_since_last_run(e), raw=e, fetched_at=at))
    odds = F.entry_odds(e)
    if odds:
        observed = F.odds_timestamp(odds) or at
        for kind, price in (("opening", F.odds_opening_price(odds)), ("current", F.odds_current_price(odds))):
            if price is not None:
                db.upsert("odds_snapshots", ["race_id", "horse_id", "source", "kind", "observed_at"], dict(
                    race_id=rid, horse_id=hid, source="formking", kind=kind, price=price, observed_at=observed, raw=odds, fetched_at=at))
    return hid


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", choices=["test", "live"], default="test")
    ap.add_argument("--date", help="meeting date YYYY-MM-DD (default: tomorrow, Melbourne)")
    ap.add_argument("--state", default="VIC")
    ap.add_argument("--race-benchmarks", type=int, default=ops.RACE_FORM_BENCHMARKS,
                    help=f"numBenchmarks per race form (default {ops.RACE_FORM_BENCHMARKS}; 10 costs 2 + 2.5 x runners per race)")
    ap.add_argument("--dry-run", action="store_true", help="plan and price only; no network, no database")
    ap.add_argument("--yes", action="store_true", help="unattended: the credit cap and balance floor decide")
    ap.add_argument("--no-profiles", action="store_true", help="skip Get Horse Form for new horses")
    ap.add_argument("--all-statuses", action="store_true", help="pull meetings not yet at final fields too")
    a = ap.parse_args()

    target = date.fromisoformat(a.date) if a.date else today_melbourne() + timedelta(days=1)
    settings, spec, costs, ledger = bootstrap(a.key)
    client = make_client(a.key, settings, spec, costs, ledger, allow_live=False)
    live = client.key_kind == "live"

    first = client.plan(ops.UPCOMING_MEETINGS, states=a.state)
    print(f"{target} {a.state}: step 1 is {first.op.key} for {first.credits} credit (balance {ledger.balance()})")
    if a.dry_run:
        rf12 = client.plan(ops.RACE_FORM, meetingId="M", raceId="R", numBenchmarks=a.race_benchmarks, racesOnly=True, runners=12)
        sm = client.plan(ops.MEETING_SPEEDMAPS, meetingId="M")
        hf = client.plan(ops.HORSE_FORM, horseId="H", numBenchmarks=ops.FIRST_SIGHT_BENCHMARKS, racesOnly=True)
        print("dry run, unit prices from credits.yaml:")
        print(f"  {sm.op.key}: {sm.credits} per meeting")
        print(f"  {rf12.op.key} at numBenchmarks={a.race_benchmarks}: {rf12.credits} per race of 12 runners")
        print(f"  {hf.op.key} at numBenchmarks={ops.FIRST_SIGHT_BENCHMARKS}: {hf.credits} per horse never held before")
        nine = first.credits + sm.credits + 9 * rf12.credits
        print(f"  one nine-race meeting of twelve-horse fields, no profiles: {nine}; with 100 new horses: {nine + 100 * hf.credits}")
        return
    if not confirm(f"Make the {first.op.key} call ({first.credits} credit, {client.key_kind} key)?", a.yes,
                   estimated=first.credits, balance=ledger.balance(), live=live):
        sys.exit("stopped")
    client.allow_live = True
    fetched_at = utc_now()
    try:
        meetings_payload = client.execute(first)
    finally:
        client.allow_live = False

    all_meetings = [m for m in F.meetings_list(meetings_payload) if F.meeting_date(m) == target.isoformat()]
    held = [m for m in all_meetings if not a.all_statuses and F.meeting_status(m) not in PULL_STATUSES]
    meetings = [m for m in all_meetings if m not in held]
    for m in held:
        print(f"  {F.meeting_track(m)}: status {F.meeting_status(m)}, not at final fields yet; skipped (use --all-statuses to pull anyway)")
    if not meetings:
        print(f"no {a.state} meetings on {target} to pull; nothing else to fetch")
        return
    db = Db(settings.database_url)
    for m in meetings:
        mid = store_meeting(db, m, fetched_at)
        for r in F.meeting_races(m):
            store_race(db, mid, r, fetched_at)
    db.commit()

    # ---- step 2: speedmaps and race forms, priced over the runners on each card -----------
    planned: list[tuple[str, str, PlannedCall]] = []
    for m in meetings:
        mid = F.meeting_id(m)
        planned.append(("speedmaps", mid, client.plan(ops.MEETING_SPEEDMAPS, meetingId=mid)))
        for r in F.meeting_races(m):
            planned.append(("race", F.race_id(r), client.plan(
                ops.RACE_FORM, meetingId=mid, raceId=F.race_id(r), numBenchmarks=a.race_benchmarks, racesOnly=True,
                runners=max(F.race_runner_count(r), 1))))
    est = estimate([p for _, _, p in planned])
    print(f"\n{len(meetings)} {a.state} meeting(s) on {target}: " + ", ".join(f"{F.meeting_track(m)} ({len(F.meeting_races(m))} races)" for m in meetings))
    print(est.render(ledger.balance() if live else None))
    if not confirm("Proceed?", a.yes, estimated=est.total, balance=ledger.balance(), live=live):
        sys.exit("stopped")

    race_meeting = {F.race_id(r): F.meeting_id(m) for m in meetings for r in F.meeting_races(m)}
    horses_on_cards: dict[str, str] = {}
    client.allow_live = True
    try:
        for kind, owner_id, p in planned:
            payload = client.execute(p)
            at = utc_now()
            if kind == "speedmaps":
                for sm in F.speedmap_list(payload):
                    runners = [dict(horse_id=F.horse_id(e), name=F.horse_name(e), number=F.entry_number(e), barrier=F.entry_barrier(e),
                                    predicted_position=rank, early_speed=F.speedmap_early_speed(e), pir=F.speedmap_pir(e),
                                    median_vs_benchmark=F.speedmap_median_vs_benchmark(e))
                               for e, rank in F.speedmap_predicted_order(F.speedmap_entries(sm))]
                    db.upsert("speedmaps", ["race_id"], dict(race_id=F.speedmap_race_id(sm), runners=runners, raw=sm, fetched_at=at))
            else:
                rid = owner_id
                db.upsert("races", ["race_id"], dict(
                    race_id=rid, meeting_id=race_meeting[rid], race_number=F.race_number(payload), race_name=F.race_name(payload),
                    distance_m=F.race_distance(payload), raw=payload, fetched_at=at))
                for e in F.race_entries(payload):
                    hid = store_entry(db, rid, e, at)
                    horses_on_cards[hid] = F.horse_name(e)
                    store_past_events(db, hid, F.entry_past_events(e), at)
            db.commit()
    finally:
        client.allow_live = False
    print(f"stored {len(horses_on_cards)} runners across {sum(1 for k, _, _ in planned if k == 'race')} races")

    if a.no_profiles or not horses_on_cards:
        print(f"done (no profile fetches). ledger balance {ledger.balance()}")
        return

    # ---- step 3: one deep Get Horse Form per horse never held before ------------------------
    known = db.known_horses(horses_on_cards)
    counts = db.benchmarked_run_counts(horses_on_cards)
    decisions = [decide_profile_fetch(hid, known.get(hid), counts.get(hid, 0)) for hid in horses_on_cards]
    to_fetch = [d for d in decisions if d.num_benchmarks is not None]
    print(f"\nhorse profiles: {len(to_fetch)} never held before, {len(decisions) - len(to_fetch)} already current")
    if not to_fetch:
        print(f"done. ledger balance {ledger.balance()}")
        return
    plans = [(d, client.plan(ops.HORSE_FORM, horseId=d.horse_id, numBenchmarks=d.num_benchmarks, racesOnly=True)) for d in to_fetch]
    pest = estimate([p for _, p in plans])
    print(pest.render(ledger.balance() if live else None))
    if not confirm("Fetch profiles?", a.yes, estimated=pest.total, balance=ledger.balance(), live=live):
        sys.exit("stopped before profiles")
    client.allow_live = True
    try:
        for d, p in plans:
            payload = client.execute(p)
            at = utc_now()
            n = store_past_events(db, d.horse_id, F.horse_form_past_events(payload), at)
            db.upsert("horses", ["horse_id"], dict(horse_id=d.horse_id, name=F.horse_form_name(payload) or horses_on_cards[d.horse_id],
                                                   profile_depth=d.num_benchmarks, profile_fetched_at=at, raw=payload, fetched_at=at))
            db.commit()
    finally:
        client.allow_live = False
    print(f"done. ledger balance {ledger.balance()}")


if __name__ == "__main__":
    main()
