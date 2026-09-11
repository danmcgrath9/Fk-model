"""Phase 0.5: the form report for a meeting, from stored data only. No API calls.

  python scripts/build_report.py --date 2026-09-12 --track Flemington
  python scripts/build_report.py --date 2026-09-12            all VIC meetings stored for the date
  python scripts/build_report.py --demo                        synthetic data, to check the layout

Writes reports/YYYY-MM-DD-<track>.html and opens it (unless --no-open).
"""
from __future__ import annotations

import argparse
import random
import re
import webbrowser
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from _common import load_settings, today_melbourne
from fk import fields as F
from fk.report.charts import (LateSpeedRow, RunnerRuns, SpeedmapRunner, lane_assignments, market_move_chart,
                              position_worm, recency_weighted_mean, sectional_worm, speedmap_chart, value_ladder)
from fk.report.html import RaceSection, SummaryRow, render_meeting
from fk.report.probability import (disagreement, market_implied, market_percentage, rated_price, rating_implied,
                                   tempo_reading, value_points)

POSITION_RUNS = 5      # last 5 benchmarked runs for the position worm
SECTIONAL_RUNS = 10    # last 10 for the sectional worm
NEURAL_SCALE = 10.0    # softmax temperature for Neural -> probability; see report note
FLAG_THRESHOLD = 0.05

METHOD_NOTE = (
    "Price is Form King's best bookmaker price now; Open is the average price at market open. Market % is 1/price "
    "normalised over the field (the race's market percentage is stated in its header). Neural % is a stand-in: "
    f"softmax(Neural / {NEURAL_SCALE:g}) over runners with a rating; Form King publishes no rated price for Neural, and EXP "
    "is derived from the market so it cannot price against it. Rated $ is 1 / Neural %. Value is Neural % minus Market %, "
    "in probability points (the Betfair Hub definition); Flag marks more than 5 points either way. Move is Form King's "
    "firmOrDrift: points of win chance since open, normalised for the book and scratchings. Sectional worm: recency-weighted "
    "mean (newest 1.0, then x0.8 per run) of the vs-Class benchmark for each 200m split over the last 10 benchmarked runs, "
    "in lengths, above zero faster than class. Position worm: position in running at each marker, last 5 runs, newest solid. "
    "Speedmap: Form King's early speed score (higher = faster early) orders the field; lanes are by that order; the tempo "
    "line is Form King's expected tempo for the race."
)


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def build_section(race: dict, entries: list[dict], runs_by_horse: dict[str, list[dict]],
                  speedmap: list[dict] | None, odds: dict[str, dict[str, float]], tempo: str | None = None) -> RaceSection:
    heading = f"Race {race.get('race_number') or '?'}: {race.get('race_name') or ''}".strip()
    sub = " ".join(x for x in [f"{race['distance_m']}m" if race.get("distance_m") else "", str(race.get("scheduled_at") or "")] if x)
    section = RaceSection(heading=heading, subheading=sub)
    active = [e for e in entries if not e.get("scratched")]

    pos_runners, sec_runners, late_rows = [], [], []
    for e in active:
        runs = runs_by_horse.get(e["horse_id"], [])
        if not runs:
            continue
        # Positions and splits come from the stored PastEvent (raw) so a mapping fix never
        # needs a re-fetch; the columns hold the same series for quick reads.
        pos_series = [F.run_positions(r["raw"]) if r.get("raw") else (r.get("positions") or []) for r in runs[:POSITION_RUNS]]
        split_series = [F.run_splits_vs_class(r["raw"]) if r.get("raw") else (r.get("vs_class") or []) for r in runs[:SECTIONAL_RUNS]]
        labels = [str(r.get("event_date") or "") for r in runs]
        pos_runners.append(RunnerRuns(e["horse_id"], e["name"], list(F.POSITION_LABELS), pos_series, labels[:POSITION_RUNS]))
        sec_runners.append(RunnerRuns(e["horse_id"], e["name"], list(F.SPLIT_LABELS), split_series, labels[:SECTIONAL_RUNS]))
        # Late speed: Form King's own S-6 (to the 600m) and 6-F (last 600m) sections, recency weighted.
        to600 = [[F.run_to_600_vs_class(r["raw"])] for r in runs[:SECTIONAL_RUNS] if r.get("raw")]
        last600 = [[F.run_last_600_vs_class(r["raw"])] for r in runs[:SECTIONAL_RUNS] if r.get("raw")]
        late_rows.append(LateSpeedRow(e["name"], recency_weighted_mean(to600, 1)[0] if to600 else None,
                                      recency_weighted_mean(last600, 1)[0] if last600 else None, len(runs[:SECTIONAL_RUNS])))
    # Speedmap first: it is the first thing a punter reads about a race.
    if speedmap:
        names = {e["horse_id"]: e["name"] for e in entries}
        barriers = {e["horse_id"]: e.get("barrier") for e in entries}
        sm_runners = [SpeedmapRunner(names.get(r["horse_id"], r.get("name") or r["horse_id"]), r.get("predicted_position"),
                                     r.get("early_speed"), r.get("barrier") if r.get("barrier") is not None else barriers.get(r["horse_id"]))
                      for r in speedmap]
        placed = lane_assignments(sm_runners)
        front = [r.name for r, _, lane in placed if lane in ("Leader", "On pace")]
        if tempo:
            section.facts.append(f"Tempo (Form King): {tempo}. Mapping Leader or On pace: {', '.join(front) or 'none'}")
        else:
            section.facts.append(f"Tempo: {len(front)} mapping Leader or On pace ({', '.join(front)}), {tempo_reading(len(front))}")
        unmapped = [r.name for r in sm_runners if r.predicted_position is None]
        if unmapped:
            section.notes.append("Not on the speedmap (no predicted position): " + ", ".join(unmapped))
        section.figures.append(speedmap_chart(sm_runners, "Speedmap: predicted settling position by lane, barrier in the marker, colour is early speed"))
    else:
        section.notes.append("No speedmap stored for this race.")

    prices = {e["horse_id"]: (odds.get(e["horse_id"], {}).get("current")) for e in active}
    market = market_implied(prices)
    model = rating_implied({e["horse_id"]: e.get("neural_rating") for e in active}, NEURAL_SCALE)
    mp = market_percentage(prices)
    if mp is not None:
        section.facts.append(f"Market {mp:.0f}% on current prices")
    for e in active:
        hid = e["horse_id"]
        section.rows.append(SummaryRow(
            name=e["name"], barrier=e.get("barrier"), weight=float(e["weight_kg"]) if e.get("weight_kg") is not None else None,
            jockey=e.get("jockey"), days_since=e.get("days_since_last_run"),
            neural=float(e["neural_rating"]) if e.get("neural_rating") is not None else None,
            exp=float(e["exp_rating"]) if e.get("exp_rating") is not None else None,
            price=prices.get(hid), opening=odds.get(hid, {}).get("opening"),
            market_prob=market.get(hid), model_prob=model.get(hid),
            flag=disagreement(market.get(hid), model.get(hid), FLAG_THRESHOLD),
            rated_price=rated_price(model.get(hid)), value_pts=value_points(market.get(hid), model.get(hid))))
    names_l = [e["name"] for e in active]
    if any(r.value_pts is not None for r in section.rows):
        section.figures.append(value_ladder(names_l, [r.value_pts for r in section.rows], "Value: Neural chance minus market chance, best value at the top"))
    # Form King's firmOrDrift (points of win chance since open) when the entry carries it;
    # else the % change from the stored opening to the current price.
    fod = {e["horse_id"]: F.odds_firm_or_drift(F.entry_odds(e["raw"])) if e.get("raw") and F.entry_odds(e["raw"]) else None for e in active}
    if any(v is not None for v in fod.values()):
        section.figures.append(market_move_chart(
            names_l, [fod.get(e["horse_id"]) for e in active], None,
            "Market moves since opening: Form King firm or drift, points of win chance, firmers first"))
    elif any(r.opening is not None and r.price is not None for r in section.rows):
        section.figures.append(market_move_chart(names_l, [r.opening for r in section.rows], [r.price for r in section.rows],
                                                 "Market moves since opening: firmers first"))

    if pos_runners:
        section.figures.append(position_worm(pos_runners, "Position worm: where each runner settles and finishes (last 5 runs, newest solid)"))
        section.figures.append(sectional_worm(sec_runners, "Sectional worm: vs-Class by section, recency weighted (last 10 runs)"))
        late_rows.sort(key=lambda x: (x.last_600 is None, -(x.last_600 or 0)))
        section.late_speed = late_rows
    else:
        section.notes.append("No benchmarked runs stored for this field.")
    return section


def write_report(meeting_date: str, track: str, sections: list[RaceSection], out_dir: Path, open_it: bool) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{meeting_date}-{slug(track)}.html"
    path.write_text(render_meeting(f"{track}, {meeting_date}", f"{len(sections)} races. Built from stored Form King data.", sections, METHOD_NOTE), encoding="utf-8")
    print(f"wrote {path}")
    if open_it:
        webbrowser.open(path.resolve().as_uri())
    return path


def from_database(target: str, track: str | None, out_dir: Path, open_it: bool) -> None:
    from fk.db import Db
    settings = load_settings()
    db = Db(settings.database_url)
    races = db.races_on(target, "VIC")
    if track:
        races = [r for r in races if r["track"].lower() == track.lower()]
    if not races:
        # A day with no racing stored is not an error; the pull already said why.
        print(f"no VIC races stored for {target}{' at ' + track if track else ''}; no report to build")
        return
    by_track: dict[str, list[dict]] = {}
    for r in races:
        by_track.setdefault(r["track"], []).append(r)
    for trk, rs in by_track.items():
        sections = []
        for r in rs:
            entries = db.entries_for_race(r["race_id"])
            runs = {e["horse_id"]: db.runs_for_horse(e["horse_id"], SECTIONAL_RUNS) for e in entries}
            sm, tempo = db.speedmap_for_race(r["race_id"]), db.speedmap_tempo(r["race_id"])
            sections.append(build_section(r, entries, runs, sm, db.latest_odds(r["race_id"]), tempo))
        write_report(target, trk, sections, out_dir, open_it)


def demo(out_dir: Path, open_it: bool) -> Path:
    """Synthetic field so the layout can be checked with no data and no credits."""
    rng = random.Random(7)
    race_sections = []
    for n in range(1, 4):
        entries, runs, speed, odds = [], {}, [], {}
        bases = []
        for i in range(8):
            hid = f"H{n}{i}"
            base = rng.uniform(-1.5, 1.5)
            entries.append(dict(horse_id=hid, name=f"Demo Horse {n}-{i+1}", barrier=i + 1, weight_kg=54 + rng.random() * 5, raw={},
                                jockey=f"J. Rider {i+1}", trainer="T. Trainer", scratched=False,
                                neural_rating=60 + base * 8 + rng.uniform(-3, 3), exp_rating=60 + rng.uniform(-8, 8),
                                days_since_last_run=rng.choice([7, 14, 21, 28, 42])))
            runs[hid] = []
            settle = rng.uniform(1, 8)
            for k in range(10):
                d = (date(2026, 9, 12) - timedelta(days=14 * (k + 1))).isoformat()
                pir = {m: max(1, round(settle + rng.uniform(-1, 1) - step)) for m, step in (("pir8", 0), ("pir6", 0), ("pir4", 1), ("pir2", 2))}
                secs = {key: {"vsClass": base + rng.uniform(-1, 1)} for key in ("S-8", "8-6", "6-4", "4-2", "2-F", "S-6", "6-F")}
                raw = dict(raceId=f"R{hid}{k}", date=int(datetime(2026, 9, 12, tzinfo=timezone.utc).timestamp() * 1000) - 14 * 86400000 * (k + 1),
                           posSettling=pir["pir8"], finishPosition=max(1, round(settle - 3 + rng.uniform(-1, 2))), trackSpeedVerified=k % 3 != 0,
                           race=True, benchmark=dict(sections=secs, vsClass=base, **pir))
                runs[hid].append(dict(run_id=f"{hid}-{k}", event_date=d, track_speed_verified=k % 3 != 0, raw=raw))
            speed.append(dict(horse_id=hid, predicted_position=settle, early_speed=100 - settle * 6 + rng.uniform(-3, 3)))
            bases.append((hid, base))
        # a 118% book: chances from the same shape as the ratings with noise, then 1.18 / chance
        weights = {hid: 2.0 ** (b * 1.6 + rng.uniform(-0.6, 0.6)) for hid, b in bases}
        total = sum(weights.values())
        for hid, w in weights.items():
            price = round((total / w) / 1.18, 2)   # 1 / chance, shortened by the 118% overround
            odds[hid] = dict(current=price, opening=round(price * rng.uniform(0.85, 1.2), 2))
        race = dict(race_number=n, race_name=f"Demo Handicap {n}", distance_m=1200 + 200 * n, scheduled_at="13:00")
        race_sections.append(build_section(race, entries, runs, speed, odds, tempo="Average to Fast"))
    return write_report("demo", "Demo Park", race_sections, out_dir, open_it)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="meeting date YYYY-MM-DD (default: tomorrow, Melbourne)")
    ap.add_argument("--track")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "reports"))
    ap.add_argument("--no-open", action="store_true")
    a = ap.parse_args()
    out_dir = Path(a.out)
    if a.demo:
        demo(out_dir, not a.no_open)
        return
    target = a.date or (today_melbourne() + timedelta(days=1)).isoformat()
    from_database(target, a.track, out_dir, not a.no_open)


if __name__ == "__main__":
    main()
