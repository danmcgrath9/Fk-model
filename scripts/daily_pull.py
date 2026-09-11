"""Daily pull for Victoria (Phase 0, item 4).

  python scripts/daily_pull.py --key test --dry-run       plan only, no network at all
  python scripts/daily_pull.py --key test                  against FK-TEST-API-KEY
  python scripts/daily_pull.py --key live                  prints the estimate, asks, then runs

Flow: Get Upcoming Meetings (one call) -> keep VIC meetings for --date (default: tomorrow,
Melbourne) -> per meeting: meeting speedmaps once, and per race Get Race Form at
numBenchmarks=10 -> per horse on those cards: profile per the cache policy.

The estimate is printed and confirmed BEFORE the second call is made. The first call
(upcoming meetings) is priced and confirmed on its own, since the rest depends on it.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta

from _common import bootstrap, confirm, make_client, today_melbourne
from fk import fields as F
from fk import ops
from fk.cache import decide_profile_fetch
from fk.client import PlannedCall
from fk.db import Db, utc_now
from fk.estimate import estimate


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
        distance_m=F.race_distance(r), scheduled_at=F.race_start_time(r), raw=r, fetched_at=fetched_at))
    return rid


def store_runs(db: Db, hid: str, runs: list[dict], fetched_at: datetime) -> date | None:
    """Store a horse's runs into past_events + benchmarked_runs. Returns the newest run date."""
    newest: date | None = None
    for run in runs:
        rid = F.run_id(run)
        d = F.run_date(run)
        db.upsert("past_events", ["past_event_id"], dict(
            past_event_id=rid, horse_id=hid, event_date=d, finish_position=F.run_finish_position(run), raw=run, fetched_at=fetched_at))
        db.upsert("benchmarked_runs", ["run_id"], dict(
            run_id=rid, horse_id=hid, past_event_id=rid, event_date=d,
            track_speed_verified=F.run_track_speed_verified(run),
            sections=F.run_sections(run), positions=F.run_positions(run), vs_class=F.run_vs_class(run),
            raw=run, fetched_at=fetched_at))
        if d:
            dd = date.fromisoformat(d)
            newest = dd if newest is None or dd > newest else newest
    return newest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", choices=["test", "live"], default="test")
    ap.add_argument("--date", help="meeting date YYYY-MM-DD (default: tomorrow, Melbourne)")
    ap.add_argument("--state", default="VIC")
    ap.add_argument("--dry-run", action="store_true", help="plan and price only; no network, no database")
    ap.add_argument("--yes", action="store_true", help="skip the confirmation prompts (use with care)")
    ap.add_argument("--no-profiles", action="store_true", help="skip horse profile fetches")
    a = ap.parse_args()

    target = date.fromisoformat(a.date) if a.date else today_melbourne() + timedelta(days=1)
    settings, spec, costs, ledger = bootstrap(a.key)
    client = make_client(a.key, settings, spec, costs, ledger, allow_live=False)

    # ---- step 1: upcoming meetings (priced on its own) --------------------------------
    first = client.plan(ops.UPCOMING_MEETINGS)
    print(f"{target} {a.state}: step 1 is {first.op.key} for {first.credits} credits (balance {ledger.balance()})")
    if a.dry_run:
        # Without the meetings list the count of races is unknown; show the per-unit prices.
        sm = client.plan(ops.MEETING_SPEEDMAPS, **_placeholder(spec, ops.MEETING_SPEEDMAPS))
        rf = client.plan(ops.RACE_FORM, numBenchmarks=ops.RACE_FORM_BENCHMARKS, **_placeholder(spec, ops.RACE_FORM))
        hp10 = client.plan(ops.HORSE_PROFILE, numBenchmarks=ops.FIRST_SIGHT_BENCHMARKS, **_placeholder(spec, ops.HORSE_PROFILE))
        hp5 = client.plan(ops.HORSE_PROFILE, numBenchmarks=ops.KNOWN_HORSE_BENCHMARKS, **_placeholder(spec, ops.HORSE_PROFILE))
        print("dry run: unit prices")
        print(f"  {sm.op.key}: {sm.credits} per meeting")
        print(f"  {rf.op.key} (numBenchmarks={ops.RACE_FORM_BENCHMARKS}): {rf.credits} per race")
        print(f"  {hp10.op.key} (numBenchmarks={ops.FIRST_SIGHT_BENCHMARKS}): {hp10.credits} per new horse")
        print(f"  {hp5.op.key} (numBenchmarks={ops.KNOWN_HORSE_BENCHMARKS}): {hp5.credits} per known horse with a new start")
        nine = first.credits + sm.credits + 9 * rf.credits
        print(f"  one nine-race meeting, no profiles: {nine} credits; with ~90 first-sight horses: {nine + 90 * hp10.credits}")
        return
    live = client.key_kind == "live"
    if not confirm(f"Make the {first.op.key} call ({first.credits} credits, {client.key_kind} key)?", a.yes,
                   estimated=first.credits, balance=ledger.balance(), live=live):
        sys.exit("stopped")
    client.allow_live = True
    fetched_at = utc_now()
    meetings_payload = client.call(ops.UPCOMING_MEETINGS)
    client.allow_live = False

    meetings = [m for m in F.meetings_list(meetings_payload)
                if F.meeting_state(m).upper() == a.state.upper() and F.meeting_date(m) == target.isoformat()]
    if not meetings:
        print(f"no {a.state} meetings on {target} in the upcoming list; nothing else to fetch")
        return
    db = Db(settings.database_url)
    for m in meetings:
        mid = store_meeting(db, m, fetched_at)
        for r in F.meeting_races(m):
            store_race(db, mid, r, fetched_at)
    db.commit()

    # ---- step 2: plan the rest and price it -------------------------------------------
    planned: list[tuple[str, PlannedCall]] = []
    for m in meetings:
        mid = F.meeting_id(m)
        planned.append((mid, client.plan(ops.MEETING_SPEEDMAPS, **_id_param(spec, ops.MEETING_SPEEDMAPS, mid))))
        for r in F.meeting_races(m):
            rid = F.race_id(r)
            planned.append((rid, client.plan(ops.RACE_FORM, numBenchmarks=ops.RACE_FORM_BENCHMARKS, **_id_param(spec, ops.RACE_FORM, rid))))
    est = estimate([p for _, p in planned])
    print(f"\n{len(meetings)} {a.state} meeting(s) on {target}: " + ", ".join(F.meeting_track(m) for m in meetings))
    print(est.render(ledger.balance() if client.key_kind == "live" else None))
    print("(horse profiles are priced after the race forms arrive, since the cache decides per horse)")
    if not confirm("Proceed?", a.yes, estimated=est.total, balance=ledger.balance(), live=live):
        sys.exit("stopped")

    client.allow_live = True
    try:
        horses_on_cards: dict[str, dict] = {}
        for owner_id, p in planned:
            payload = client.execute(p)
            at = utc_now()
            if p.op.key == spec.find_operation(ops.MEETING_SPEEDMAPS).key:
                for sm in F.speedmap_races(payload):
                    rid = F.race_id(sm)
                    runners = [dict(horse_id=F.horse_id(x), predicted_position=F.speedmap_predicted_position(x),
                                    early_speed=F.speedmap_early_speed(x), raw=x) for x in F.speedmap_runners(sm)]
                    db.upsert("speedmaps", ["race_id"], dict(race_id=rid, runners=runners, raw=sm, fetched_at=at))
            else:
                rid = owner_id
                for e in F.race_entries(payload):
                    hid = F.horse_id(e)
                    horses_on_cards[hid] = e
                    db.upsert("horses", ["horse_id"], dict(horse_id=hid, name=F.horse_name(e), fetched_at=at))
                    db.upsert("entries", ["race_id", "horse_id"], dict(
                        race_id=rid, horse_id=hid, barrier=F.entry_barrier(e), weight_kg=F.entry_weight(e),
                        jockey=F.entry_jockey(e), trainer=F.entry_trainer(e), scratched=F.entry_scratched(e),
                        neural_rating=F.entry_neural_rating(e), exp_rating=F.entry_exp_rating(e),
                        days_since_last_run=F.entry_days_since_last_run(e), raw=e, fetched_at=at))
                    try:
                        store_runs(db, hid, F.entry_runs(e), at)
                    except F.FieldUnmapped:
                        pass  # race form may not carry runs; the profile does
            db.commit()
    finally:
        client.allow_live = False

    if a.no_profiles or not horses_on_cards:
        print("done (no profile fetches)")
        return

    # ---- step 3: profiles per the cache policy ---------------------------------------
    known = db.known_horses(horses_on_cards)
    decisions = []
    for hid, e in horses_on_cards.items():
        stored = db.latest_run_date(hid)
        runs_dates = []
        try:
            runs_dates = [F.run_date(r) for r in F.entry_runs(e)]
        except F.FieldUnmapped:
            pass
        latest_start = max((date.fromisoformat(d) for d in runs_dates if d), default=None)
        decisions.append(decide_profile_fetch(hid, known.get(hid), stored, latest_start))
    to_fetch = [d for d in decisions if d.num_benchmarks is not None]
    profile_plans = [(d, client.plan(ops.HORSE_PROFILE, numBenchmarks=d.num_benchmarks, **_id_param(spec, ops.HORSE_PROFILE, d.horse_id))) for d in to_fetch]
    skipped = len(decisions) - len(to_fetch)
    print(f"\nhorse profiles: {len(to_fetch)} to fetch, {skipped} already current")
    if not profile_plans:
        return
    pest = estimate([p for _, p in profile_plans])
    print(pest.render(ledger.balance() if client.key_kind == "live" else None))
    if not confirm("Fetch profiles?", a.yes, estimated=pest.total, balance=ledger.balance(), live=live):
        sys.exit("stopped before profiles")
    client.allow_live = True
    try:
        for d, p in profile_plans:
            payload = client.execute(p)
            at = utc_now()
            store_runs(db, d.horse_id, F.entry_runs(payload), at)
            db.upsert("horses", ["horse_id"], dict(horse_id=d.horse_id, name=F.horse_name(horses_on_cards[d.horse_id]),
                                                   profile_depth=d.num_benchmarks, profile_fetched_at=at, raw=payload, fetched_at=at))
            db.commit()
    finally:
        client.allow_live = False
    print(f"done. ledger balance {ledger.balance()}")


def _id_param(spec, op_name: str, value: str) -> dict:
    """The spec names the id parameter; we do not. Use its single path parameter, else its
    single required query parameter."""
    op = spec.find_operation(op_name)
    paths = op.path_params()
    if len(paths) == 1:
        return {paths[0]: value}
    req = [p.name for p in op.parameters if p.required and p.location == "query"]
    if len(req) == 1:
        return {req[0]: value}
    raise SystemExit(f"{op.key}: cannot tell which parameter takes the id (path={paths}, required query={req}); set it explicitly in daily_pull.py")


def _placeholder(spec, op_name: str) -> dict:
    return _id_param(spec, op_name, "PLACEHOLDER")


if __name__ == "__main__":
    main()
