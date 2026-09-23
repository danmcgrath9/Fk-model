"""Phase 0.5: the form report for a meeting, from stored data only. No API calls.

  python scripts/build_report.py --date 2026-09-12 --track Flemington
  python scripts/build_report.py --date 2026-09-12            all VIC meetings stored for the date
  python scripts/build_report.py --demo                        synthetic data, to check the layout

Writes reports/YYYY-MM-DD-<track>.html and opens it (unless --no-open).
"""
from __future__ import annotations

import argparse
import json
import random
import re
import webbrowser
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from _common import default_target, load_settings, now_melbourne
from fk import fields as F
from fk.report.charts import (LateSpeedRow, RunnerProfile, RunnerRuns, SpeedmapRunner, TrendPanel, lane_assignments,
                              market_move_chart, position_worm, ratings_profile_chart, recency_weighted_mean, sectional_worm,
                              speedmap_chart, trend_grid, value_ladder)
from fk.report.html import ContextRow, FormStripRow, ProjectionRow, RaceSection, SummaryRow, render_meeting
from fk.trend import rating_series, trend
from fk.report.probability import (DEFAULT_SCALE, disagreement, fit_scale, market_implied, market_percentage, rated_price,
                                   rating_implied, tempo_reading, value_points)

POSITION_RUNS = 5      # last 5 benchmarked runs for the position worm
SECTIONAL_RUNS = 10    # last 10 for the sectional worm
PROFILE_RUNS = 20      # runs (and trials) on the ratings profile
NEURAL_SCALE = None    # set per meeting by fit_scale (see build_meeting); DEFAULT_SCALE when there is no market
FLAG_THRESHOLD = 0.05

METHOD_NOTE = (
    "Price is Form King's best bookmaker price now; Open is the average price at market open. Market % is 1/price "
    "normalised over the field (the race's market percentage is stated in its header). Neural % converts Form King's "
    "Neural points to a win chance: each runner is read relative to the top runner of its race (the scale of Neural "
    "changes race to race), then a softmax. Once a back-test exists (docs/BACKTEST.md) the chance comes from a model "
    "fitted to Betfair SP over past races on Neural, the latest rated run and the career and 12-month peaks, and each race "
    "header says so; before that the softmax steepness is fitted to this meeting's market (the k in the header). Form King "
    "publishes no rated price for Neural, and EXP is derived from the market so it cannot price against it. Rated $ is "
    "1 / Neural %. Value is Neural % minus Market %, "
    "in probability points (the Betfair Hub definition); Flag marks more than 5 points either way. Move is Form King's "
    "firmOrDrift: points of win chance since open, normalised for the book and scratchings. Sectional worm: recency-weighted "
    "mean (newest 1.0, then x0.8 per run) of the vs-Class benchmark for each 200m split over the last 10 benchmarked runs, "
    "in lengths, above zero faster than class. Position worm: position in running at each marker, last 5 runs, newest solid. "
    "Speedmap: Form King's early speed score (higher = faster early) orders the field; lanes are by that order; the tempo "
    "line is Form King's expected tempo for the race. Trend: least-squares slope, in rating points per run, of the runner's "
    "rating adjusted to today's weight over its last six race runs (trials left out); rising or falling past 0.75 a run, "
    "else steady; Last and Best are the latest and highest of those ratings. The trend grid draws every runner on one scale "
    "with the career peak dashed. Form strip and context are Form King's own form-guide fields, printed as given."
)

PREP_FORM = {1: "firstUpForm", 2: "secondUpForm", 3: "thirdUpForm"}
MODEL_PATH = Path(__file__).resolve().parents[1] / "config" / "rated_price.json"


def load_rated_price_model(path: Path = MODEL_PATH) -> dict | None:
    """The back-tested rated-price model (scripts/backtest.py), or None before one exists."""
    if not path.exists():
        return None
    m = json.loads(path.read_text(encoding="utf-8"))
    return m if m.get("beta") and m.get("features") else None


SIM_RUNS = 20000


def projection_chances(params_dict: dict, entries: list[dict], speedmap: list[dict] | None, tempo_raw: dict | None,
                       late_by_horse: dict[str, float | None] | None = None) -> tuple[dict[str, float | None], list[ProjectionRow]]:
    """The projection model: each active runner's projected figure, the exact win chance,
    and the sim's win and place counts, as rows for the page. `late_by_horse` is the
    last-600m figure the late-speed table prints, so the projection and the table agree."""
    from fk import projection as P
    params = P.Params(**params_dict)
    positions = {r["horse_id"]: r.get("predicted_position") for r in (speedmap or []) if r.get("horse_id")}
    inputs = [i for i in (P.inputs_from_entry(e["raw"], positions.get(e["horse_id"]), len(entries)) for e in entries if e.get("raw")) if i is not None]
    for i in inputs:
        if late_by_horse and late_by_horse.get(i.horse_id) is not None:
            i.late600 = late_by_horse[i.horse_id]
    tempo = P.tempo_score(tempo_raw)
    projs = P.project_field(inputs, tempo, params)
    probs = P.win_probabilities(projs)
    sim = P.simulate(projs, n=SIM_RUNS)
    rows = [ProjectionRow(q.name, q.base, q.scope, q.shape, q.late, q.neural, q.projected, q.sd, probs.get(q.horse_id),
                          sim.get(q.horse_id, {}).get("place"), rated_price(probs.get(q.horse_id)), q.note) for q in projs]
    return probs, rows


# A race is priced and bet only when at least this share of its runners carry an opening
# price. The model's market input is the opening price, and a runner without one is
# filled with the field's average chance, which rates a $151 outsider like an ordinary
# runner; the first live week showed exactly that, before this check existed.
MIN_OPEN_COVERAGE = 0.8


def with_opening(raw: dict, opening: float | None) -> dict:
    """The entry with its odds' avgOpen set to `opening` (the newest morning snapshot's
    opening price, the same Form King field the fit was trained on). The race form is
    pulled the evening before, often before a market has formed, so the snapshot is the
    fuller read. No snapshot price: the entry is left as it is."""
    if opening is None or opening <= 1:
        return raw
    odds = dict((raw.get("odds") or {}) if isinstance(raw.get("odds"), dict) else {})
    odds["avgOpen"] = opening
    return {**raw, "odds": odds}


def open_coverage(entries: list[dict], openings: dict[str, float | None] | None = None) -> tuple[int, int]:
    """(runners with an opening price the model can use, runners)."""
    have = 0
    for e in entries:
        raw = with_opening(e.get("raw") or {}, (openings or {}).get(e["horse_id"]))
        if (F.entry_odds(raw) or {}).get("avgOpen") is not None:
            have += 1
    return have, len(entries)


def model_chances(model: dict, entries: list[dict], distance_m: int | None = None, lws: float | None = None,
                  speedmap: list[dict] | None = None, tempo_raw: dict | None = None,
                  openings: dict[str, float | None] | None = None) -> dict[str, float]:
    """Win chance per active runner from the back-tested conditional logit, on the same
    features the fit used (fk.backtest.race_features over each entry's own record, then
    the race shape from the speedmap and expected tempo). `openings` = {horse_id: the
    morning snapshot's opening price}, which replaces the evening form's."""
    from fk import backtest as B
    from fk import projection as P
    runners = [r for r in (B.runner_from_entry(with_opening(e["raw"], (openings or {}).get(e["horse_id"])), distance_m, lws)
                           for e in entries if e.get("raw")) if r is not None]
    if not runners:
        return {}
    B.race_features(runners)
    B.shape_features(runners, B.positions_from_speedmap(speedmap), P.tempo_score(tempo_raw))
    p = B.predict(model["beta"], runners)
    return {r.horse_id: pi for r, pi in zip(runners, p)}


def _ordinal(n: int) -> str:
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def race_facts_line(raw: dict | None) -> list[str]:
    """Race-level facts for the header, only those the payload carries."""
    if not raw:
        return []
    f = F.race_facts(raw)
    out = []
    if f.get("going"):
        out.append(f"Going {f['going']}" + (f" {f['goingNumber']}" if f.get("goingNumber") is not None else ""))
    if f.get("rail"):
        out.append(f"Rail: {f['rail']}")
    if f.get("restrictions"):
        out.append(str(f["restrictions"]))
    if f.get("grade"):
        out.append(f"Grade {f['grade']}")
    if f.get("prizemoney") is not None:
        out.append(f"Prize ${f['prizemoney']:,.0f}")
    if f.get("lws") is not None:
        out.append(f"LWS {f['lws']:.1f}")
    if f.get("expAdj") is not None:
        out.append(f"expAdj {f['expAdj']:+.1f}")
    if f.get("direction"):
        out.append(str(f["direction"]).replace("_", " ").lower())
    return out


def context_row(e: dict) -> ContextRow:
    raw = e.get("raw") or {}
    fr = F.entry_form_record(raw)
    j, t = F.entry_jockey_form(raw), F.entry_trainer_form(raw)
    _, changes = F.entry_gear(raw)
    c = F.entry_context(raw)
    prep = None
    if c.get("runInPrep") is not None:
        n = int(c["runInPrep"])
        rec = fr.get(PREP_FORM.get(n, ""))
        prep = f"{_ordinal(n)} up" + (f": {rec}" if rec else "")
    elif c.get("firstStarter"):
        prep = "first starter"
    age_sex = " ".join(x for x in [f"{c['age']}yo" if c.get("age") else "", c.get("sex") or ""] if x) or None
    return ContextRow(
        name=e["name"], career=fr.get("careerForm"), track=fr.get("trackForm"), distance=fr.get("distanceForm"),
        track_distance=fr.get("trackAndDistanceForm"), going=fr.get("todaysGoingForm"), prep=prep,
        days_since_win=c.get("daysSinceLastWin"), jockey_win=(j or {}).get("win12m"), trainer_win=(t or {}).get("win12m"),
        combo=(j or {}).get("horseCombo") or None, gear_changes=", ".join(changes) or None, ohr=c.get("ohr"),
        distance_change=c.get("distanceChange"), age_sex=age_sex, prizemoney=c.get("prizemoney"))


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def drop_empty_columns(runners: list[RunnerRuns]) -> list[RunnerRuns]:
    """Remove a section label no run of any runner has a value for, so a sprint's axis does
    not carry the 1200m and 1000m markers it never passed."""
    if not runners:
        return runners
    n = len(runners[0].sections)
    keep = [i for i in range(n) if any(i < len(run) and run[i] is not None for r in runners for run in r.runs)]
    out = []
    for r in runners:
        out.append(RunnerRuns(r.horse_id, r.name, [r.sections[i] for i in keep],
                              [[run[i] if i < len(run) else None for i in keep] for run in r.runs], r.run_labels))
    return out


def neural_scale_for_meeting(races: list[tuple[list[dict], dict[str, dict[str, float]]]]) -> tuple[float, bool]:
    """(k, fitted): the Neural softmax scale fitted to this meeting's market over every race
    with prices, or DEFAULT_SCALE when no race has a market yet."""
    pairs = []
    for entries, odds in races:
        active = [e for e in entries if not e.get("scratched")]
        prices = {e["horse_id"]: odds.get(e["horse_id"], {}).get("current") for e in active}
        pairs.append(({e["horse_id"]: e.get("neural_rating") for e in active}, market_implied(prices)))
    k = fit_scale(pairs)
    return (k, True) if k is not None else (DEFAULT_SCALE, False)


def build_section(race: dict, entries: list[dict], runs_by_horse: dict[str, list[dict]],
                  speedmap: list[dict] | None, odds: dict[str, dict[str, float]], tempo: str | None = None,
                  events_by_horse: dict[str, list[dict]] | None = None, neural_scale: float | None = None,
                  scale_fitted: bool = False, rated_model: dict | None = None, tempo_raw: dict | None = None,
                  results: dict[str, dict] | None = None) -> RaceSection:
    heading = f"Race {race.get('race_number') or '?'}: {race.get('race_name') or ''}".strip()
    sub = " ".join(x for x in [f"{race['distance_m']}m" if race.get("distance_m") else "", str(race.get("scheduled_at") or "")] if x)
    section = RaceSection(heading=heading, subheading=sub)
    section.facts.extend(race_facts_line(race.get("raw")))
    active = [e for e in entries if not e.get("scratched")]

    pos_runners, sec_runners, late_rows = [], [], []
    late_by_horse: dict[str, float | None] = {}
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
        late_by_horse[e["horse_id"]] = late_rows[-1].last_600
    pos_runners = drop_empty_columns(pos_runners)
    sec_runners = drop_empty_columns(sec_runners)
    # Speedmap first: it is the first thing a punter reads about a race.
    if speedmap:
        names = {e["horse_id"]: e["name"] for e in entries}
        barriers = {e["horse_id"]: e.get("barrier") for e in entries}
        sm_runners = [SpeedmapRunner(names.get(r["horse_id"], r.get("name") or r["horse_id"]), r.get("predicted_position"),
                                     r.get("early_speed"), r.get("barrier") if r.get("barrier") is not None else barriers.get(r["horse_id"]),
                                     pir=r.get("pir"), median_vs_benchmark=r.get("median_vs_benchmark"))
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
        section.figures.append(speedmap_chart(sm_runners, "Early speed: who leads and who sits back" + (f". Tempo: {tempo}" if tempo else "")
                                              + " (bar = Form King early speed score, colour and word = mapped lane, barrier in brackets)"))
    else:
        section.notes.append("No speedmap stored for this race.")

    # Ratings by run, oldest first, for the trend column, the trend grid and the profile.
    ratings_by_horse: dict[str, list[dict]] = {}
    for e in active:
        evs = (events_by_horse or {}).get(e["horse_id"], [])
        rr = [F.run_ratings(ev["raw"]) for ev in evs if ev.get("raw")]
        rr = [r for r in rr if r.get("date")]
        rr.sort(key=lambda r: r["date"])
        ratings_by_horse[e["horse_id"]] = rr
    trends = {hid: trend(rating_series(rr)) for hid, rr in ratings_by_horse.items()}

    prices = {e["horse_id"]: (odds.get(e["horse_id"], {}).get("current")) for e in active}
    market = market_implied(prices)
    k = neural_scale if neural_scale is not None else DEFAULT_SCALE
    lws = F.race_facts(race["raw"]).get("lws") if race.get("raw") else None
    model: dict = {}
    priced_by_projection = False
    if rated_model and rated_model.get("model") == "projection_sim" and rated_model.get("params"):
        model, section.projections = projection_chances(rated_model["params"], active, speedmap, tempo_raw, late_by_horse)
        section.sim_runs = SIM_RUNS
        priced_by_projection = True
        model = {e["horse_id"]: model.get(e["horse_id"]) for e in active}
        section.facts.append(f"Rated by the projection model: a projected figure per runner and the race run {SIM_RUNS:,} times; "
                             f"weights fitted to Betfair SP over {rated_model['races']} races to {rated_model['to']}")
    elif rated_model:
        from fk import backtest as _B
        section.model_name = f"{rated_model.get('model')} ({rated_model.get('races')} races to {rated_model.get('to')})"
        section.model_reads_market = _B.MARKET_FEATURE in (rated_model.get("features") or [])
        openings = {e["horse_id"]: odds.get(e["horse_id"], {}).get("opening") for e in active}
        have, n = open_coverage(active, openings)
        if n and have / n < MIN_OPEN_COVERAGE:
            section.bettable = False
            section.facts.append(f"Market not formed: {have} of {n} runners carry an opening price, so the model's market "
                                 f"input is incomplete. Rated for reading only; no paper bets on this race.")
        model = model_chances(rated_model, active, race.get("distance_m"), lws, speedmap, tempo_raw, openings)
        if rated_model.get("projection_params"):
            # The projection is the founder's own method; it is shown beside the price even
            # when the back-test trusts another model to set it.
            _, section.projections = projection_chances(rated_model["projection_params"], active, speedmap, tempo_raw, late_by_horse)
            section.sim_runs = SIM_RUNS
    if model and not priced_by_projection:
        model = {e["horse_id"]: model.get(e["horse_id"]) for e in active}
        section.facts.append(f"Rated by the back-tested model: fitted to Betfair SP over {rated_model['races']} races to {rated_model['to']}")
    else:
        model = rating_implied({e["horse_id"]: e.get("neural_rating") for e in active}, k)
        section.facts.append(f"Neural scale k = {k:.1f}" + (" fitted to this meeting's market" if scale_fitted else " (default, no market to fit to)"))
    mp = market_percentage(prices)
    if mp is not None:
        section.facts.append(f"Market {mp:.0f}% on current prices")
    for e in active:
        hid = e["horse_id"]
        res = F.entry_result(e["raw"]) if e.get("raw") else None
        stored = (results or {}).get(hid)   # the morning job's results table, for a race pulled before it ran
        section.rows.append(SummaryRow(
            name=e["name"], barrier=e.get("barrier"), weight=float(e["weight_kg"]) if e.get("weight_kg") is not None else None,
            jockey=e.get("jockey"), days_since=e.get("days_since_last_run"),
            neural=float(e["neural_rating"]) if e.get("neural_rating") is not None else None,
            exp=float(e["exp_rating"]) if e.get("exp_rating") is not None else None,
            price=prices.get(hid), opening=odds.get(hid, {}).get("opening"),
            market_prob=market.get(hid), model_prob=model.get(hid),
            flag=disagreement(market.get(hid), model.get(hid), FLAG_THRESHOLD),
            rated_price=rated_price(model.get(hid)), value_pts=value_points(market.get(hid), model.get(hid)),
            trend=trends[hid].reading if hid in trends and trends[hid].n else None, slope=trends[hid].slope if hid in trends else None,
            last_rating=trends[hid].last if hid in trends else None, best_rating=trends[hid].best if hid in trends else None,
            finish=F.result_finish_position(res) if res else (stored or {}).get("finish"),
            result_sp=F.result_starting_price(res) if res else (stored or {}).get("sp"), horse_id=hid))
    names_l = [e["name"] for e in active]
    # Context and form strip in the summary's order (Neural, best first).
    order = sorted(active, key=lambda e: (e.get("neural_rating") is None, -float(e.get("neural_rating") or 0)))
    section.context = [context_row(e) for e in order]
    for e in order:
        evs = (events_by_horse or {}).get(e["horse_id"], [])
        ms = [F.run_market(ev["raw"]) for ev in evs if ev.get("raw")]
        ms = [m for m in ms if m.get("date")]
        ms.sort(key=lambda m: m["date"], reverse=True)
        if ms:
            section.form_strip.append(FormStripRow(e["name"], ms))
    # Trend grid: every runner at once, one scale, career peak dashed.
    panels = []
    for e in order:
        rr = ratings_by_horse.get(e["horse_id"], [])
        races = [r for r in rr if not r.get("trial")]
        series = rating_series(races)
        pts = [(r["date"], v) for r, v in zip(races, series) if v is not None][-6:]
        if not pts:
            continue
        peak, _ = F.entry_peak_ratings(e["raw"]) if e.get("raw") else (None, None)
        t = trends[e["horse_id"]]
        panels.append(TrendPanel(e["name"], [v for _, v in pts], [str(d) for d, _ in pts], t.reading, t.slope, peak))
    if panels:
        section.figures.append(trend_grid(panels, "Rating trend, every runner on one scale: last six race runs, career peak dashed, latest run the big dot"))
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
    # Ratings profile: every rating per run, oldest first, one runner at a time.
    profiles = []
    for e in active:
        runs = ratings_by_horse.get(e["horse_id"], [])
        if not runs:
            continue
        peak, peak12 = F.entry_peak_ratings(e["raw"]) if e.get("raw") else (None, None)
        profiles.append(RunnerProfile(e["name"], runs, peak, peak12))
    if profiles:
        section.figures.append(ratings_profile_chart(profiles, "Ratings profile: pick a runner. Beside each point: finish, race rank (r) and meeting rank (m) of the last 600m"))
    else:
        section.notes.append("No benchmarked runs stored for this field.")
    return section


def write_report(meeting_date: str, track: str, sections: list[RaceSection], out_dir: Path, open_it: bool, suffix: str = "") -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{meeting_date}-{slug(track)}{suffix}.html"
    label = " (what-if)" if suffix else ""
    path.write_text(render_meeting(f"{track}, {meeting_date}{label}", f"{len(sections)} races. Built from stored Form King data.", sections, METHOD_NOTE), encoding="utf-8")
    print(f"wrote {path}")
    if open_it:
        webbrowser.open(path.resolve().as_uri())
    return path


def paper_rows(section: RaceSection):
    from fk import paper as P
    return [P.Row(r.horse_id, r.name, r.rated_price, r.price, r.model_prob, r.market_prob, r.flag, r.finish, r.opening)
            for r in section.rows if r.horse_id]


def place_paper(db, race: dict, section: RaceSection) -> int:
    """The paper book: every plan's bets for a race not yet run, at the prices on the page."""
    from datetime import datetime, timezone
    from fk import fields as F
    from fk import paper as P
    now = datetime.now(timezone.utc)
    jump = P.jump_time(race.get("meeting_date"), F.race_start_time(race.get("raw") or {}))
    if not P.before_the_jump(jump, now):
        # A page built after the race has run carries a price nobody could take now.
        when = jump.strftime("%H:%M Melbourne") if jump else "unknown"
        print(f"paper: race {race.get('race_number')} not bet, jump {when} has passed or is unknown")
        return 0
    if not getattr(section, "bettable", True):
        print(f"paper: race {race.get('race_number')} not bet, market not formed (too few opening prices)")
        return 0
    if not getattr(section, "model_reads_market", False):
        # A form-only model back-tests well behind the morning market; every bet it struck in
        # the book's first eight days was a bet against a sharper price.
        print(f"paper: race {race.get('race_number')} not bet, the rated-price model does not read the market")
        return 0
    db.ensure_paper_book()
    # ONE pricing decides a race. A page rebuilt later could only ever ADD bets (a horse
    # already backed was left alone; a horse whose price had drifted far enough to raise a
    # flag was backed on the second pass), so the book took the union of every flag that
    # appeared at any observation, which is not a rule anyone could follow.
    already = db.race_first_priced_at(race["race_id"])
    if already is not None:
        print(f"paper: race {race.get('race_number')} already priced at {already:%Y-%m-%d %H:%M} UTC, not re-bet")
        return 0
    bets = P.place(paper_rows(section))
    if not bets:
        return 0
    return db.place_paper_bets([dict(
        bet_id=f"{race['race_id']}|{b.horse_id}|{b.plan}", race_id=race["race_id"], horse_id=b.horse_id, plan=b.plan,
        meeting_date=race["meeting_date"], track=race.get("track"), race_number=race.get("race_number"), horse_name=b.name,
        placed_at=now, first_priced_at=now, price=b.price, opening_price=b.opening, rated_price=b.rated_price,
        model_prob=b.model_prob, market_prob=b.market_prob, stake=b.stake, model=section.model_name,
    ) for b in bets])


def parse_exclusions(text: str | None) -> list[tuple[str, str]]:
    """'Aethera@2026-08-29, Other Horse@2026-07-01' -> [(name lower-cased, date)]."""
    out = []
    for part in (text or "").split(","):
        part = part.strip()
        if not part:
            continue
        if "@" not in part:
            raise SystemExit(f"--exclude-run wants NAME@YYYY-MM-DD, got {part!r}")
        name, date = part.rsplit("@", 1)
        out.append((name.strip().lower(), date.strip()))
    return out


def apply_exclusions(entries: list[dict], events: dict[str, list[dict]], runs: dict[str, list[dict]],
                     exclusions: list[tuple[str, str]]) -> list[str]:
    """A what-if: drop a horse's run on a given date from everything the page and the
    price read (the entry's past events, the ratings profile and the sectional runs), so a
    run the owner wants disregarded (a wet track it did not handle) prices as if it never
    happened. Mutates in place; returns one note per exclusion that matched."""
    notes = []
    for name, date in exclusions:
        for e in entries:
            raw = e.get("raw") or {}
            if F.horse_name(raw).lower() != name:
                continue
            before = len(F.entry_past_events(raw))
            raw["pastEvents"] = [p for p in F.entry_past_events(raw) if F.past_event_date(p) != date]
            hid = e["horse_id"]
            events[hid] = [ev for ev in events.get(hid, []) if str(ev.get("event_date") or "")[:10] != date]
            runs[hid] = [r for r in runs.get(hid, []) if str(r.get("event_date") or "")[:10] != date]
            if len(raw["pastEvents"]) < before:
                notes.append(f"What-if: {F.horse_name(raw)}'s run on {date} is left out of every figure on this page, at your request")
    return notes


def from_database(target: str, track: str | None, out_dir: Path, open_it: bool, paper: bool = False,
                  exclusions: list[tuple[str, str]] | None = None) -> None:
    from fk.db import Db
    settings = load_settings()
    db = Db(settings.database_url)
    races = db.races_on(target, "VIC")
    if track:
        races = [r for r in races if r["track"].lower().startswith(track.lower())]
    if not races:
        # A day with no racing stored is not an error; the pull already said why.
        print(f"no VIC races stored for {target}{' at ' + track if track else ''}; no report to build")
        return
    by_track: dict[str, list[dict]] = {}
    for r in races:
        by_track.setdefault(r["track"], []).append(r)
    rated_model = load_rated_price_model()
    if rated_model:
        print(f"rated price: back-tested model, {rated_model['races']} races to {rated_model['to']}")
    for trk, rs in by_track.items():
        loaded = [(r, db.entries_for_race(r["race_id"]), db.latest_odds(r["race_id"])) for r in rs]
        k, fitted = neural_scale_for_meeting([(entries, odds) for _, entries, odds in loaded])
        print(f"{trk}: Neural scale k = {k:.2f} ({'fitted to the market' if fitted else 'default, no market'})")
        sections = []
        placed = 0
        for r, entries, odds in loaded:
            runs = {e["horse_id"]: db.runs_for_horse(e["horse_id"], SECTIONAL_RUNS) for e in entries}
            events = {e["horse_id"]: db.past_events_for_horse(e["horse_id"], PROFILE_RUNS) for e in entries}
            sm, tempo = db.speedmap_for_race(r["race_id"]), db.speedmap_tempo(r["race_id"])
            notes = apply_exclusions(entries, events, runs, exclusions or [])
            section = build_section(r, entries, runs, sm, odds, tempo, events, neural_scale=k, scale_fitted=fitted, rated_model=rated_model,
                                    tempo_raw=db.speedmap_tempo_raw(r["race_id"]), results=db.results_for_race(r["race_id"]))
            section.facts = list(notes) + list(section.facts)
            sections.append(section)
            # A what-if page never places bets: the book runs on the figures as published.
            if paper and not exclusions:
                placed += place_paper(db, r, section)
        if paper and not exclusions:
            print(f"{trk}: {placed} paper bets placed")
        write_report(target, trk, sections, out_dir, open_it, suffix="-whatif" if exclusions else "")


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
        race = dict(race_number=n, race_name=f"Demo Handicap {n}", distance_m=1200 + 200 * n, scheduled_at="13:00",
                    raw=dict(going="Good", goingNumber=4, railPosition="True", restrictions="BM78", prizemoneyGrade="MSAT",
                             totalPrizeMoney=150000, lws=92.0, expAdj=-0.4, direction="ANTI_CLOCKWISE"))
        events = {}
        for e in entries:
            e["raw"] = {"ratings": {"peak": 96.0, "peak12m": 93.5},
                        "form": {"careerForm": "14: 3-2-2", "trackForm": "3: 1-0-1", "distanceForm": "5: 2-1-0", "trackAndDistanceForm": "1: 0-0-1",
                                 "todaysGoingForm": "8: 2-1-1", "firstUpForm": "3: 1-0-0", "secondUpForm": "3: 0-1-1"},
                        "jockeyForm": {"lastTwelveMonthWinPercentage": 10 + rng.uniform(0, 12), "horseComboForm": "2: 1-0-0"},
                        "trainerForm": {"lastTwelveMonthWinPercentage": 12 + rng.uniform(0, 10)},
                        "gear": [{"gear": "Blinkers", "on": True, "change": "first time"}] if rng.random() < 0.3 else [],
                        "raceInPrep": rng.choice([1, 2, 3, 4]), "daysSinceLastWin": rng.choice([60, 140, 300, None]),
                        "benchmarkRating": 70 + rng.uniform(0, 20), "distanceChange": rng.choice(["0", "+200", "-100"]),
                        "totalPrizeMoney": rng.uniform(50000, 400000), "age": rng.choice([3, 4, 5, 6]), "type": rng.choice(["G", "M", "H"])}
            evs = []
            for k, run in enumerate(runs[e["horse_id"]]):
                raw = dict(run["raw"])
                drift = (9 - k) * rng.uniform(-0.6, 0.9)   # some runners improve run to run, some go the other way
                raw.update(weightForAgeRating=88 + rng.uniform(-6, 6), adjustedForTodaysWeight=84 + drift + rng.uniform(-2, 2), numRunners=12,
                           track="Demo Park", distance=1400, trial=k == 9, margin=round(rng.uniform(0, 6), 1), going="Good 4",
                           startingPrice=round(rng.uniform(2.5, 30), 1), bsp=round(rng.uniform(2.5, 32), 1))
                raw["benchmark"].update(atWeights=88 + rng.uniform(-6, 6), wfaRat=89 + rng.uniform(-6, 6), raceRating=95 + rng.uniform(-3, 3),
                                        expectedRating=90 + rng.uniform(-5, 5), vsAllAvg=rng.uniform(-2, 2), vsTrack=rng.uniform(-2, 2),
                                        speedRating=100 + rng.uniform(-5, 5), finishingSpeed=100 + rng.uniform(-4, 4))
                raw["benchmark"]["sections"]["6-F"].update(raceRank=rng.randint(1, 12), meetRatingRank=rng.randint(1, 90))
                evs.append({"raw": raw})
            events[e["horse_id"]] = evs
        k, fitted = neural_scale_for_meeting([(entries, odds)])
        race_sections.append(build_section(race, entries, runs, speed, odds, tempo="Average to Fast", events_by_horse=events,
                                           neural_scale=k, scale_fitted=fitted))
    return write_report("demo", "Demo Park", race_sections, out_dir, open_it)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="meeting date YYYY-MM-DD (default: today before noon Melbourne, else tomorrow, the pull's rule)")
    ap.add_argument("--track")
    ap.add_argument("--paper", action="store_true", help="log the paper book's bets for races not yet run, at the prices on the page")
    ap.add_argument("--exclude-run", help="what-if: leave out a horse's run, NAME@YYYY-MM-DD, comma separated; writes a -whatif page and places no bets")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "reports"))
    ap.add_argument("--no-open", action="store_true")
    a = ap.parse_args()
    out_dir = Path(a.out)
    if a.demo:
        demo(out_dir, not a.no_open)
        return
    target = a.date or default_target(now_melbourne()).isoformat()
    from_database(target, a.track, out_dir, not a.no_open, paper=a.paper, exclusions=parse_exclusions(a.exclude_run))


if __name__ == "__main__":
    main()
