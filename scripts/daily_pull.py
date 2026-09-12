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
from fk.client import FormKingError, PlannedCall
from fk.db import Db, utc_now
from fk.estimate import estimate
from fk.guard import credit_cap, fit_under_cap, time_budget_seconds
from fk.pace import run_batch

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
        # Races and barrier trials are kept (a trial is a first-upper's only recent form);
        # spells and scratchings are not runs.
        if F.past_event_is_spell(p) or bool(p.get("scratched", False)):
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


def meetings_call(client, target: date, today: date, state: str):
    """A day already run is asked for by date (Get Meetings By Date, DDMMYY); today and
    later come from the upcoming list, which is the only one that carries future days."""
    if target < today:
        return client.plan(ops.MEETINGS_BY_DATE, ddmmyy=target.strftime("%d%m%y"), states=state)
    return client.plan(ops.UPCOMING_MEETINGS, states=state)


def select_meetings(meetings: list[dict], track: str | None, races: set[int] | None) -> list[dict]:
    """Keep the meetings whose track starts with one of `track`'s comma-separated names
    (case-insensitive) and, within them, only the race numbers asked for. A meeting left
    with no races is dropped."""
    wanted = [t.strip().lower() for t in (track or "").split(",") if t.strip()]
    out = []
    for m in meetings:
        if wanted and not any(F.meeting_track(m).lower().startswith(t) for t in wanted):
            continue
        if races:
            m = dict(m)
            m["races"] = [r for r in F.meeting_races(m) if F.race_number(r) in races]
            if not m["races"]:
                continue
        out.append(m)
    return out


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
    ap.add_argument("--track", help="only these tracks, comma separated prefixes (e.g. flemington,caulfield)")
    ap.add_argument("--races", help="only these race numbers, comma separated (e.g. 1,3)")
    a = ap.parse_args()

    today = today_melbourne()
    target = date.fromisoformat(a.date) if a.date else today + timedelta(days=1)
    race_filter = {int(x) for x in a.races.split(",") if x.strip()} if a.races else None
    settings, spec, costs, ledger = bootstrap(a.key)
    client = make_client(a.key, settings, spec, costs, ledger, allow_live=False)
    live = client.key_kind == "live"

    first = meetings_call(client, target, today, a.state)
    print(f"{target} {a.state}: step 1 is {first.op.key} for {first.credits} credit (balance {ledger.balance()})")
    if a.dry_run:
        rf12 = client.plan(ops.RACE_FORM, meetingId="M", raceId="R", numBenchmarks=a.race_benchmarks, racesOnly=False, runners=12)
        sm = client.plan(ops.MEETING_SPEEDMAPS, meetingId="M")
        hf = client.plan(ops.HORSE_FORM, horseId="H", numBenchmarks=ops.FIRST_SIGHT_BENCHMARKS, racesOnly=False)
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
    all_meetings = select_meetings(all_meetings, a.track, race_filter)
    # A day already run is pulled whatever its status reads; the filter is for the days ahead.
    held = [m for m in all_meetings if not a.all_statuses and target >= today and F.meeting_status(m) not in PULL_STATUSES]
    meetings = [m for m in all_meetings if m not in held]
    for m in held:
        print(f"  {F.meeting_track(m)}: status {F.meeting_status(m)}, not at final fields yet; skipped (use --all-statuses to pull anyway)")
    if not meetings:
        print(f"no {a.state} meetings on {target} to pull; nothing else to fetch")
        everything = F.meetings_list(meetings_payload)
        print(f"the upcoming list held {len(everything)} meeting(s) in total:")
        for m in everything:
            print(f"  {F.meeting_date(m)}  {F.meeting_state(m):4} {F.meeting_track(m):24} {F.meeting_status(m):16} {len(F.meeting_races(m))} races  id={F.meeting_id(m)}")
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
        for r in F.meeting_races(m):
            planned.append(("race", F.race_id(r), client.plan(
                ops.RACE_FORM, meetingId=mid, raceId=F.race_id(r), numBenchmarks=a.race_benchmarks, racesOnly=False,
                runners=max(F.race_runner_count(r), 1))))
    for m in meetings:   # after the forms: a speedmap failure must never cost the race data
        planned.append(("speedmaps", F.meeting_id(m), client.plan(ops.MEETING_SPEEDMAPS, meetingId=F.meeting_id(m))))
    est = estimate([p for _, _, p in planned])
    print(f"\n{len(meetings)} {a.state} meeting(s) on {target}: " + ", ".join(f"{F.meeting_track(m)} ({len(F.meeting_races(m))} races)" for m in meetings))
    print(est.render(ledger.balance() if live else None))
    if not confirm("Proceed?", a.yes, estimated=est.total, balance=ledger.balance(), live=live):
        sys.exit("stopped")

    race_meeting = {F.race_id(r): F.meeting_id(m) for m in meetings for r in F.meeting_races(m)}
    horses_on_cards: dict[str, str] = {}
    failures: list[str] = []
    ok_races = 0
    client.allow_live = True
    try:
        for kind, owner_id, p in planned:
            try:
                payload = client.execute(p)
            except FormKingError as e:
                # Recorded in the ledger already. Keep going: one bad call is not a bad day.
                failures.append(f"{p.op.key} {p.params}: HTTP {e.status} {e.body[:120]}")
                print(f"FAILED {failures[-1]}")
                continue
            at = utc_now()
            if kind == "speedmaps":
                # The meeting call returns every race's speedmap; with --races only some of
                # those races exist in the database, and a speedmap keys on its race.
                for sm in F.speedmap_list(payload):
                    if F.speedmap_race_id(sm) not in race_meeting:
                        continue
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
                ok_races += 1
            db.commit()
    finally:
        client.allow_live = False
    print(f"stored {len(horses_on_cards)} runners across {ok_races} of {sum(1 for k, _, _ in planned if k == 'race')} races")
    if failures:
        print(f"\n{len(failures)} call(s) failed and were skipped:")
        for f in failures:
            print("  " + f)
    if ok_races == 0:
        sys.exit("no race form succeeded; nothing to report on")

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
    plans = [(d, client.plan(ops.HORSE_FORM, horseId=d.horse_id, numBenchmarks=d.num_benchmarks, racesOnly=False)) for d in to_fetch]
    if a.yes and live:
        # Unattended: fetch as many as the cap and floor allow, and say what was left.
        spent_so_far = sum(p.credits for _, _, p in planned) + first.credits
        n_fit = fit_under_cap([p.credits for _, p in plans], ledger.balance(), cap=max(0, credit_cap() - spent_so_far))
        if n_fit < len(plans):
            print(f"credit cap: fetching {n_fit} of {len(plans)} profiles today; the rest are picked up when those horses next race")
            plans = plans[:n_fit]
        if not plans:
            print(f"done. ledger balance {ledger.balance()}")
            return
    pest = estimate([p for _, p in plans])
    print(pest.render(ledger.balance() if live else None))
    if not (a.yes and live):
        if not confirm("Fetch profiles?", a.yes, estimated=pest.total, balance=ledger.balance(), live=live):
            sys.exit("stopped before profiles")

    def fetch(item):
        d, p = item
        return client.execute(p)

    client.allow_live = True
    try:
        batch = run_batch(plans, fetch, workers=4, per_second=1.0, budget_seconds=time_budget_seconds())
    finally:
        client.allow_live = False
    for (d, p), payload in batch.done:
        at = utc_now()
        store_past_events(db, d.horse_id, F.horse_form_past_events(payload), at)
        db.upsert("horses", ["horse_id"], dict(horse_id=d.horse_id, name=F.horse_form_name(payload) or horses_on_cards[d.horse_id],
                                               profile_depth=d.num_benchmarks, profile_fetched_at=at, raw=payload, fetched_at=at))
    db.commit()
    for (d, p), e in batch.failed:
        msg = f"{p.op.key} {p.params}: {getattr(e, 'status', '')} {str(e)[:120]}"
        failures.append(msg)
        print(f"FAILED {msg}")
    print(f"profiles: {len(batch.done)} fetched, {len(batch.failed)} failed, {len(batch.skipped)} left for another day (time budget)")
    print(f"done. ledger balance {ledger.balance()}")


if __name__ == "__main__":
    main()
