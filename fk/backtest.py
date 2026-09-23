"""Back-test of the rated price against Betfair SP. Pure, hand-tested, no numpy.

The idea, in the founder's words: if BSP is the sharp price, the rated price should get
as close to it as pre-race information allows. So every runner in every race already run
is described by what was knowable before the jump (Form King's Neural points, its
performance ratings, and optionally the opening market), and a conditional-logit model
p_i = exp(beta . x_i) / sum_j exp(beta . x_j) is fitted by Newton's method to minimise
the cross-entropy against the BSP-implied chances. The same model is then scored against
the actual winners, and against BSP itself and the opening market, so it is clear whether
it learnt anything beyond the market.

Features are RELATIVE within a race (the top runner is the reference), which is what
makes a conditional logit need no intercept and makes Neural's changing scale harmless.
A runner missing a feature is given the race's mean of it, which is neutral.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from fk import fields as F
from fk.trend import rating_series, trend

# Candidate pre-race features, all made relative within the race by race_features.
NEURAL = ["neural_rel"]
RATINGS = ["last_rel", "peak_rel", "peak12_rel", "wfa_rel", "wfa_best_rel", "ohr_rel"]
DISTANCE = ["dist_rel", "dist_win"]
# Class and scope: the ratings against the race's own standard (Form King's Likely Winning
# Standard, so a figure above the standard in a Group race is not read like the same gap
# in a country maiden), the trend of the ratings, and how lightly raced the horse is.
CLASS = ["last_vs_lws", "best_vs_lws", "trend_slope", "starts_log"]
# Distance read properly: the LATEST and the BEST rating the horse has run at today's trip
# (not the mean of every run near it), and how far today's trip is from the last run's,
# so a figure earned over a hard 2000m is not read at face value at a soft 1600m.
DISTANCE_AWARE = ["last_dist_rel", "best_dist_rel", "dist_change"]
# Speed and sectionals, the half of Form King's data the model had never seen: its speed
# figure (100 = class par), how much it finished off (last 600 as a share of the run to
# the 600), and the last 600m and the run to it against the class standard, in lengths.
SPEED = ["speed_rel", "speed_best_rel", "finish_speed_rel", "last600_rel", "to600_rel"]
# Position in running, the horse's own racing pattern from its history. Every figure is a
# SHARE OF THE FIELD (0 = on the lead, 1 = last), so fifth of eight and fifth of sixteen are
# not read as the same thing, and each is centred on today's field so it says "more forward
# than these rivals" rather than a bare number.
#   settle_share  where it settles
#   pos800_share  where it is with 800m to run
#   pos_gain      positions made up from settling to the post
#   late_gain     positions made up from the 400m to the post
# The research behind them: the first four settling positions take about 60% of races and
# the identified leader about 43% of metro races, while backmarkers win less often than
# their price implies, which is the drift we are already measuring on our own flags.
POSITION = ["settle_share", "pos800_share", "pos_gain", "late_gain"]
# Race shape: where the horse is mapped to settle (front = 0, back = 1, centred on the
# field) and that position against the expected tempo, so the fit can learn that a slow
# lead helps the leaders and costs the back markers.
SHAPE = ["early_pos", "early_x_tempo"]
# The horse's own pattern against today's race: its habitual settling share read against the
# expected tempo (a backmarker in a slow-run race is the classic disadvantage), and how far
# today's map asks it to race from where it usually does.
STYLE = ["style_x_tempo", "map_vs_habit"]
# Form King's EXP is derived from the market and Form King does not say from WHICH market.
# It scores so far ahead of everything else that late money is the likely explanation, and a
# figure that already knows where the price closed cannot be used to predict where the price
# will close. Measured for information, never deployed.
EXP = ["exp_rel"]
FORM_FEATURES = NEURAL + RATINGS + DISTANCE
MARKET_FEATURE = "open_logit"
# Only EXP is barred. The MORNING PRICE is not: we bet into that price, so a model that
# uses it and lands closer to BSP than it does has beaten the market we are betting against.
# Refusing the market as an input was refusing the only thing that has ever cleared the bar.
NON_DEPLOYABLE = set(EXP)

# The feature sets the back-test compares. The one closest to BSP out of sample is deployed.
# The shape of the market, not just its level. `open_logit` is the log of the opening
# chance; `market_prob` is that chance itself, and carrying both lets the fit bend the
# market's own curve, which is where the favourite-longshot bias lives: short prices are
# historically underbet and long ones overbet, and a model with only log-chance cannot
# correct for it. `market_x_neural` lets the fit trust form more in some races than others.
MARKET_SHAPE = ["market_prob", "market_x_neural"]

# DELIBERATELY NOT A FEATURE: the move from the opening price to the price now (avgNow,
# bestNow, firmOrDrift). It is the single most promising thing we hold, because money
# moving towards a horse between the open and the morning keeps moving to the close. It is
# also leakage in this back-test: a race PULLED AFTER IT RAN carries its FINAL price in
# avgNow, so the feature would be reading the answer on most of the sample and would score
# like EXP does. It becomes usable when the live pipeline has stored enough pre-race
# snapshots to fit on, with the odds timestamp checked against the jump.

# Everything else Form King sends that the model had never been shown. Thirty-odd fields
# sat unused: the draw, the weight, the freshness, the campaign, the jockey and the trainer,
# and a dozen conditional records (this track, today's going, the wet, the class, first-up).
# Rather than guess which matter, all of them go in and the cross-validated ridge decides
# how hard to shrink each one, which is what testing everything looks like when the
# combinatorial search would cost more than the answer is worth.
#   barrier_share   the draw as a share of the field, 0 inside, 1 widest
#   days_log        log days since the last run: freshness
#   run_in_prep     which run of this campaign
#   weight_rel      weight carried against the field
#   wfa_diff        Form King's own weight-for-age difference
#   beaten_3        lengths beaten over the last three runs
#   prize_log       log average prizemoney: a crude class signal the ratings may miss
#   track_win, going_win, class_win, td_win, wet_win, up_win   shrunk win rates from the
#       conditional form strings, each (wins + 1) / (starts + 5) against the field mean
#   jockey_win, trainer_win, jt_combo_win   strike rates, as percentages
EXTRAS = ["barrier_share", "days_log", "run_in_prep", "weight_rel", "wfa_diff", "beaten_3", "prize_log",
          "track_win", "going_win", "class_win", "td_win", "wet_win", "up_win",
          "jockey_win", "trainer_win", "jt_combo_win"]

# Horses with little or no race form. Every rating of a runner without a rated run is
# filled with the field's average, which rates an unraced horse like an ordinary one; these
# say so, so the fit can learn how such runners really go against the market.
#   first_starter      1 when the horse has no race start (trials do not count)
#   unrated            1 when it has no rated run at all, so its ratings are the field mean
#   trial_margin       lengths behind the winner at its latest trial within 120 days
#                      (0 = won), centred on the field; no recent trial = the field mean
#   trialled_recently  1 when it has trialled within 120 days
#   first_starter_x_market   the opening-market chance (log) for a first starter, 0 for the
#                      rest: lets the fit trust the market more where the form is empty
EXPERIENCE = ["first_starter", "unrated", "trial_margin", "trialled_recently", "first_starter_x_market"]
# What the MARKET thought of this horse's past runs, and what became of the horses it met.
# Every past run carries its Betfair SP; about half carry Form King's subsequentForm (how
# the field it raced in went on). None of this is today's price, so none of it is leakage.
#   mkt_class         recency-weighted -log(BSP) over past races: how short the market has priced it
#   beat_market       recency-weighted (won - 1/BSP): ran better than its price, on average
#   beat_market_last  the same for the latest run only
#   collateral_wins   recency-weighted wins-over-expectation per race of the fields it met afterwards
#   collateral_roi    recency-weighted staking return (as a fraction) of those fields afterwards
#   field_strength    recency-weighted strength of the fields it has been racing in
#   strength_last     the latest run's field strength
HISTORY = ["mkt_class", "beat_market", "beat_market_last", "collateral_wins", "collateral_roi", "field_strength", "strength_last"]
TRIAL_WINDOW_DAYS = 120

MODEL_SETS = {
    "neural_only": NEURAL,
    "ratings_only": RATINGS,                 # WFA, handicap and weight-adjusted ratings, no Neural
    "ratings_plus_distance": RATINGS + DISTANCE,
    "all_form": FORM_FEATURES,
    "all_form_plus_class": FORM_FEATURES + CLASS,
    "ratings_class_distance": RATINGS + DISTANCE + CLASS,   # no Neural: ratings read against the standard
    "all_form_plus_open_market": FORM_FEATURES + [MARKET_FEATURE],
    "distance_aware": FORM_FEATURES + CLASS + DISTANCE_AWARE,
    "distance_shape": FORM_FEATURES + CLASS + DISTANCE_AWARE + SHAPE,
    "distance_shape_exp": FORM_FEATURES + CLASS + DISTANCE_AWARE + SHAPE + EXP,   # information only
    "speed_only": SPEED,
    "form_plus_speed": FORM_FEATURES + CLASS + SPEED,
    "distance_speed": FORM_FEATURES + CLASS + DISTANCE_AWARE + SPEED,
    "everything": FORM_FEATURES + CLASS + DISTANCE_AWARE + SHAPE + SPEED,
    "position_only": POSITION,
    "form_plus_position": FORM_FEATURES + CLASS + POSITION,
    "position_and_style": FORM_FEATURES + CLASS + POSITION + SHAPE + STYLE,
    "the_lot": FORM_FEATURES + CLASS + DISTANCE_AWARE + SPEED + POSITION + SHAPE + STYLE,
    # The market plus each layer of form. The model that first beat the morning market
    # carried only Neural, ratings and distance beside the price, so none of the class,
    # distance-at-the-trip, speed, sectional or position work had ever been tried WITH it.
    "market_plus_class": FORM_FEATURES + CLASS + [MARKET_FEATURE],
    "market_plus_distance": FORM_FEATURES + CLASS + DISTANCE_AWARE + [MARKET_FEATURE],
    "market_plus_speed": FORM_FEATURES + CLASS + SPEED + [MARKET_FEATURE],
    "market_plus_position": FORM_FEATURES + CLASS + POSITION + [MARKET_FEATURE],
    "market_plus_everything": FORM_FEATURES + CLASS + DISTANCE_AWARE + SPEED + POSITION + [MARKET_FEATURE],
    "market_the_lot": FORM_FEATURES + CLASS + DISTANCE_AWARE + SPEED + POSITION + SHAPE + STYLE + [MARKET_FEATURE],
    "market_shaped": FORM_FEATURES + CLASS + [MARKET_FEATURE] + MARKET_SHAPE,
    "market_shaped_all": FORM_FEATURES + CLASS + DISTANCE_AWARE + SPEED + POSITION + [MARKET_FEATURE] + MARKET_SHAPE,
    "extras_only": EXTRAS,
    "form_plus_extras": FORM_FEATURES + CLASS + EXTRAS,
    "kitchen_sink": FORM_FEATURES + CLASS + DISTANCE_AWARE + SPEED + POSITION + SHAPE + STYLE + EXTRAS,
    "market_kitchen_sink": FORM_FEATURES + CLASS + DISTANCE_AWARE + SPEED + POSITION + SHAPE + STYLE + EXTRAS
                           + [MARKET_FEATURE] + MARKET_SHAPE,
    "market_kitchen_sink_exp": FORM_FEATURES + CLASS + DISTANCE_AWARE + SPEED + POSITION + SHAPE + STYLE + EXTRAS
                               + [MARKET_FEATURE] + MARKET_SHAPE + EXPERIENCE,
    "market_plus_experience": FORM_FEATURES + CLASS + [MARKET_FEATURE] + EXPERIENCE,
    # The market's own memory of the horse and the collateral form of the fields it met.
    "history_plus_market": HISTORY + [MARKET_FEATURE] + MARKET_SHAPE,
    "market_plus_history": FORM_FEATURES + CLASS + [MARKET_FEATURE] + EXPERIENCE + HISTORY,
    "market_kitchen_sink_history": FORM_FEATURES + CLASS + DISTANCE_AWARE + SPEED + POSITION + SHAPE + STYLE + EXTRAS
                                   + [MARKET_FEATURE] + MARKET_SHAPE + EXPERIENCE + HISTORY,
}
# Ridge strengths tried by cross-validation inside the training races. Every model so far
# has been fitted with effectively none (1e-8) and every one lands far worse out of sample
# than in it, which is the signature of a fit that has memorised its training races.
# Three strengths and three folds, not six and five: the full grid is 1,674 fits at about
# eight seconds each, which is nearly four hours against a two-hour job. This grid is 540.
RIDGES = [1e-8, 1e-2, 1.0]
RIDGE_FOLDS = 3

RECENT_RUNS = 4      # how many recent races a speed or sectional figure is read over
RECENCY_DECAY = 0.8  # each older run counts this much less, the weighting the page's worm uses
DISTANCE_BAND_M = 200   # a run within this of today's trip counts as "at the distance"


@dataclass
class Runner:
    horse_id: str
    name: str
    raw: dict[str, float | None]          # raw feature values before the within-race transform
    bsp: float | None
    sp: float | None
    finish: int | None
    x: dict[str, float] = field(default_factory=dict)   # transformed, filled by race_features


@dataclass
class Race:
    race_id: str
    date: str
    track: str
    runners: list[Runner]


def _form_record(txt: str | None) -> tuple[int, int] | None:
    """'5: 2-1-0' -> (starts 5, wins 2); None when unreadable."""
    if not txt or ":" not in str(txt):
        return None
    try:
        starts, rest = str(txt).split(":", 1)
        wins = rest.strip().split("-")[0]
        return int(starts.strip()), int(wins.strip())
    except ValueError:
        return None


def latest_trial(events: list[dict], today: str | None = None) -> float | None:
    """Lengths behind the winner at the latest trial within TRIAL_WINDOW_DAYS of `today` (the
    race's date), 0 for a trial won; None with no recent trial or no race date. Hand-checked:
    trials 30 and 200 days back, beaten 1.5 and 0.2 lengths -> 1.5."""
    from datetime import date
    trials = [(F.past_event_date(p), p) for p in events if F.past_event_is_trial(p) and F.past_event_date(p)]
    if not trials:
        return None
    if not today:
        return None
    trials = [t for t in trials if t[0][:10] < str(today)[:10]]   # never a trial on or after race day
    if not trials:
        return None
    trials.sort(key=lambda t: t[0])
    d, p = trials[-1]
    try:
        gap = (date.fromisoformat(str(today)[:10]) - date.fromisoformat(d[:10])).days
    except ValueError:
        return None
    if gap > TRIAL_WINDOW_DAYS:
        return None
    if F.past_event_finish(p) == 1:
        return 0.0
    return F.past_event_margin(p)


def market_history(events: list[dict]) -> dict[str, float | None]:
    """The HISTORY raw values from a horse's raw past events (oldest or newest first, sorted
    here). Trials are skipped; a run without a BSP contributes nothing to the market figures.
    Hand-check: two races, newest last, BSP 4 then 2, finishes 1 then 3, decay 0.8:
    beat = [1 - 0.25, 0 - 0.5] = [0.75, -0.5]; recency-weighted (newest first) = (-0.5 x 1 +
    0.75 x 0.8) / 1.8 = 0.0556; beat_market_last = -0.5; mkt_class = (-ln 2 x 1 + -ln 4 x 0.8)
    / 1.8 = -1.0013."""
    runs = []
    for p in events:
        m = F.run_market(p)
        if m.get("trial") or not m.get("date"):
            continue
        row: dict = {"date": m["date"], "fieldStrength": m.get("fieldStrength")}
        bsp, finish = m.get("bsp"), m.get("finish")
        if bsp and bsp > 1 and finish is not None:
            row["logbsp"] = -math.log(bsp)
            row["beat"] = (1.0 if finish == 1 else 0.0) - 1.0 / bsp
        sub = (p.get("subsequentForm") or {}).get("ALL") if isinstance(p.get("subsequentForm"), dict) else None
        if isinstance(sub, dict) and sub.get("races"):
            woe = sub.get("winsOverExpectations")
            roi = sub.get("proportionalStakingROI")
            if woe is not None:
                row["woe"] = float(woe) / float(sub["races"])
            if roi is not None:
                row["roi"] = float(roi) / 100.0
        runs.append(row)
    runs.sort(key=lambda r: r["date"])
    last = runs[-1] if runs else {}
    return {"mkt_class": recent_weighted(runs, "logbsp"), "beat_market": recent_weighted(runs, "beat"),
            "beat_market_last": last.get("beat"), "collateral_wins": recent_weighted(runs, "woe"),
            "collateral_roi": recent_weighted(runs, "roi"), "field_strength": recent_weighted(runs, "fieldStrength"),
            "strength_last": last.get("fieldStrength")}


def runner_from_entry(e: dict, race_distance: int | None = None, lws: float | None = None,
                      race_date: str | None = None) -> Runner | None:
    """A RaceEntry (Get Race Form) already run: features from what was knowable before the
    jump, the result from horseResult. None for a scratching.
    Raw values: Form King's Neural; the latest rating adjusted to today's weight and the
    career and 12-month peaks (that scale); the latest and the best WFA rating; the
    official handicap rating (benchmarkRating); the mean weight-adjusted rating of runs
    within DISTANCE_BAND_M of today's trip; the record at the distance; the opening price."""
    if F.entry_scratched(e):
        return None
    res = F.entry_result(e)
    peak, peak12 = F.entry_peak_ratings(e)
    events = F.entry_past_events(e)
    runs = [F.run_ratings(p) for p in events]
    runs = sorted([r for r in runs if r.get("date")], key=lambda r: r["date"])
    series = [v for v in rating_series(runs) if v is not None]
    races_only = [r for r in runs if not r.get("trial")]
    wfa = [r["wfaRat"] if r.get("wfaRat") is not None else r.get("wfa") for r in races_only]
    wfa = [v for v in wfa if v is not None]
    at_distance = []          # in date order, so the last entry is the latest run at the trip
    last_run_distance = None
    if race_distance:
        for r in races_only:
            d = r.get("distance")
            v = next((r[k] for k in ("adjToday", "atWeights", "wfaRat", "wfa") if r.get(k) is not None), None)
            if d is not None and v is not None and abs(float(d) - float(race_distance)) <= DISTANCE_BAND_M:
                at_distance.append(v)
        last_run_distance = next((float(r["distance"]) for r in reversed(races_only) if r.get("distance") is not None), None)
    ctx = F.entry_context(e)
    form = F.entry_form_record(e)
    rec = _form_record(form.get("distanceForm"))
    career = _form_record(form.get("careerForm"))
    tr = trend(rating_series(runs))
    last = series[-1] if series else None
    best_rated = max(series) if series else None
    odds = F.entry_odds(e)
    open_price = F.odds_opening_price(odds) if odds else None
    trial = latest_trial(events, race_date)
    return Runner(
        horse_id=F.horse_id(e), name=F.horse_name(e),
        raw={"neural": F.entry_neural_rating(e), "last": series[-1] if series else None,
             "peak": peak, "peak12": peak12,
             "wfa": wfa[-1] if wfa else None, "wfa_best": max(wfa) if wfa else None,
             "ohr": ctx.get("ohr"),
             "dist": sum(at_distance) / len(at_distance) if at_distance else None,
             "last_dist": at_distance[-1] if at_distance else None,
             "best_dist": max(at_distance) if at_distance else None,
             # today's trip less the last run's, in hundreds of metres: +4 is stepping up 400m
             "dist_change": (float(race_distance) - last_run_distance) / 100.0 if race_distance and last_run_distance is not None else None,
             "exp": F.entry_exp_rating(e),
             "dist_starts": rec[0] if rec else None, "dist_wins": rec[1] if rec else None,
             **extra_features(e),
             **market_history(events),
             **{k: recent_weighted([{**r, **position_shares(r)} for r in races_only], k) for k in POSITION},
             "speed": recent_weighted(races_only, "speedRating"),
             "speed_best": max((r["speedRating"] for r in races_only if r.get("speedRating") is not None), default=None),
             "finish_speed": recent_weighted(races_only, "finishingSpeed"),
             "last600": recent_weighted(races_only, "last600"),
             "to600": recent_weighted(races_only, "to600"),
             "last_vs_lws": (last - lws) if last is not None and lws is not None else None,
             "best_vs_lws": (best_rated - lws) if best_rated is not None and lws is not None else None,
             "trend_slope": tr.slope,
             "starts": career[0] if career else None,
             "race_starts": len(races_only),
             "rated_runs": len(series),
             "trial_margin": trial,
             "open": open_price},
        bsp=F.result_betfair_sp(res) if res else None,
        sp=F.result_starting_price(res) if res else None,
        finish=F.result_finish_position(res) if res else None,
    )


def positions_from_speedmap(speedmap: list[dict] | None) -> dict[str, int]:
    """horse id -> predicted settling position, from the stored speedmap runners."""
    out = {}
    for r in speedmap or []:
        hid, pos = r.get("horse_id"), r.get("predicted_position")
        if hid and pos is not None:
            try:
                out[hid] = int(pos)
            except (TypeError, ValueError):
                pass
    return out


def shape_features(runners: list[Runner], positions: dict[str, int], tempo: float) -> None:
    """Race shape on top of race_features: early_pos is the mapped settling position scaled
    front 0 to back 1 and centred on the field (a runner the map does not place takes the
    mean, so it neither helps nor hurts); early_x_tempo is that against the expected tempo
    (-1 slow to +1 fast), which is what lets the fit price a leader in a slow race
    differently from a leader in a fast one. Call after race_features."""
    n = len(runners)
    if n < 2 or not positions:
        return
    span = max(1, max(positions.values()) - 1)
    raw = [((positions[r.horse_id] - 1) / span) if r.horse_id in positions else None for r in runners]
    filled = _fill_mean(raw)
    mean = sum(filled) / n
    for r, v in zip(runners, filled):
        r.x["early_pos"] = v - mean
        r.x["early_x_tempo"] = (v - mean) * tempo
        # The horse's own habit against today's race. style_x_tempo is the classic one: a
        # backmarker (positive share) in a slow-run race (negative tempo) reads negative.
        habit = r.x.get("settle_share")
        r.x["style_x_tempo"] = (habit * tempo) if habit is not None else 0.0
        r.x["map_vs_habit"] = ((v - mean) - habit) if habit is not None else 0.0


def position_shares(run: dict) -> dict[str, float | None]:
    """One past run's positions as shares of its own field: 0 = on the lead, 1 = last, so a
    field of 8 and a field of 16 are comparable. `positions` is [settling, 1200, 1000, 800,
    600, 400, 200, finish]. Gains are positive when the horse made ground.
    Hand-check: 10 runners, settled 6th, 400m 4th, finished 2nd ->
    settle (6 - 1) / 9 = 0.5556, late gain (4 - 2) / 9 = 0.2222, gain (6 - 2) / 9 = 0.4444."""
    pos = run.get("positions") or []
    n = run.get("runners")
    if not n or n < 2 or len(pos) < 8:
        return {}
    span = n - 1
    settle, p800, p400, finish = pos[0], pos[3], pos[5], pos[7]

    def share(v):
        return None if v is None else (v - 1) / span

    out = {"settle_share": share(settle), "pos800_share": share(p800)}
    out["pos_gain"] = (settle - finish) / span if settle is not None and finish is not None else None
    out["late_gain"] = (p400 - finish) / span if p400 is not None and finish is not None else None
    return out


def recent_weighted(runs: list[dict], key: str, n: int = RECENT_RUNS, decay: float = RECENCY_DECAY) -> float | None:
    """A figure read over the most recent races, newest counting most. `runs` oldest first;
    runs missing the figure are skipped rather than counted as zero, and None when none
    carry it. Hand-check: values [10, 20] newest last, decay 0.8 ->
    (20 * 1 + 10 * 0.8) / 1.8 = 15.5555..."""
    have = [r[key] for r in reversed(runs) if r.get(key) is not None][:n]
    if not have:
        return None
    weights = [decay ** i for i in range(len(have))]
    return sum(v * w for v, w in zip(have, weights)) / sum(weights)


def _win_rate(txt: str | None) -> float | None:
    """A Form King record string as a shrunk win rate: (wins + 1) / (starts + 5), so one win
    from one start reads 33% and not 100%. None when the string carries no starts."""
    rec = _form_record(txt)
    if not rec or rec[0] is None:
        return None
    starts, wins = rec
    return (wins + 1) / (starts + 5)


def extra_features(e: dict) -> dict[str, float | None]:
    """Everything else Form King sends about a runner, as plain numbers. Missing stays None
    and race_features fills it with the field mean, so a runner with no jockey record is
    neither helped nor hurt by the gap."""
    ctx = F.entry_context(e)
    form = F.entry_form_record(e)
    jockey = F.entry_jockey_form(e) or {}
    trainer = F.entry_trainer_form(e) or {}
    barrier = F.entry_barrier(e)
    days = F.entry_days_since_last_run(e)
    prep = ctx.get("runInPrep")
    # First-up, second-up, third-up: the record that matches where this horse is in its
    # campaign, so one column carries the relevant one instead of three mostly-empty ones.
    up_key = {1: "firstUpForm", 2: "secondUpForm", 3: "thirdUpForm"}.get(prep)
    prize = ctx.get("avgPrizemoney")
    return {
        "barrier": float(barrier) if barrier else None,     # made a share of the field in race_features
        "days_log": math.log(1 + days) if days is not None and days >= 0 else None,
        "run_in_prep": float(prep) if prep is not None else None,
        "weight_rel": F.entry_weight(e),
        "wfa_diff": ctx.get("wfaDiff"),
        "beaten_3": form.get("lengthsBeatenLastThree"),
        "prize_log": math.log(1 + prize) if prize is not None and prize >= 0 else None,
        "track_win": _win_rate(form.get("trackForm")),
        "going_win": _win_rate(form.get("todaysGoingForm")),
        "class_win": _win_rate(form.get("classForm")),
        "td_win": _win_rate(form.get("trackAndDistanceForm")),
        "wet_win": _win_rate(form.get("wet")),
        "up_win": _win_rate(form.get(up_key)) if up_key else None,
        "jockey_win": jockey.get("win12m"),
        "trainer_win": trainer.get("win12m"),
        "jt_combo_win": trainer.get("jockeyComboWin"),
    }


def _fill_mean(vals: list[float | None]) -> list[float]:
    have = [v for v in vals if v is not None]
    m = sum(have) / len(have) if have else 0.0
    return [m if v is None else v for v in vals]


def race_features(runners: list[Runner]) -> None:
    """Fill runner.x for a field: Neural relative to the race's top (top = 1), each rating
    as points below the race's best (best = 0), and the log of the opening-market chance.
    Missing values take the race mean. Mutates in place."""
    n = len(runners)
    if n == 0:
        return
    neural = _fill_mean([r.raw.get("neural") for r in runners])
    top = max(neural) if max(neural) > 0 else 1.0
    cols = {"neural_rel": [max(v, top * 0.01) / top for v in neural]}
    for key, out in (("last", "last_rel"), ("peak", "peak_rel"), ("peak12", "peak12_rel"), ("wfa", "wfa_rel"),
                     ("wfa_best", "wfa_best_rel"), ("ohr", "ohr_rel"), ("dist", "dist_rel"),
                     ("last_dist", "last_dist_rel"), ("best_dist", "best_dist_rel"), ("exp", "exp_rel"),
                     ("speed", "speed_rel"), ("speed_best", "speed_best_rel"), ("finish_speed", "finish_speed_rel"),
                     ("last600", "last600_rel"), ("to600", "to600_rel")):
        vals = _fill_mean([r.raw.get(key) for r in runners])
        best = max(vals)
        cols[out] = [v - best for v in vals]
    # Position shares are already scale-free, so they are centred on the field: "more forward
    # than these rivals", not a bare share.
    for key in POSITION:
        vals = _fill_mean([r.raw.get(key) for r in runners])
        mean = sum(vals) / n
        cols[key] = [v - mean for v in vals]
    # The draw only means anything against the field it was drawn in: barrier 8 is wide in a
    # field of nine and inside in a field of eighteen, so it becomes a share before it is
    # centred. A runner with no barrier takes the field mean like everything else.
    bars = [r.raw.get("barrier") for r in runners]
    widest = max([b for b in bars if b] or [0])
    raw_share = [((b - 1) / (widest - 1)) if b and widest > 1 else None for b in bars]
    for r, v in zip(runners, raw_share):
        r.raw["barrier_share"] = v
    # Every extra is centred on the field: "more than these rivals", never a bare number.
    for key in EXTRAS + HISTORY:
        vals = _fill_mean([r.raw.get(key) for r in runners])
        mean = sum(vals) / n
        cols[key] = [v - mean for v in vals]
    # Distance change is centred on the field, so it reads as "stepping up more than the others".
    changes = _fill_mean([r.raw.get("dist_change") for r in runners])
    mean_change = sum(changes) / n
    cols["dist_change"] = [v - mean_change for v in changes]
    # Shape features are zero until shape_features() is given a speedmap.
    cols["early_pos"] = [0.0] * n
    cols["early_x_tempo"] = [0.0] * n
    cols["style_x_tempo"] = [0.0] * n
    cols["map_vs_habit"] = [0.0] * n
    # Record at the distance as a shrunk win rate: (wins + 1) / (starts + 5), so one win
    # from one start reads 33%, not 100%; a runner with no record takes the race mean.
    rates = [((r.raw["dist_wins"] + 1) / (r.raw["dist_starts"] + 5)) if r.raw.get("dist_starts") is not None and r.raw.get("dist_wins") is not None else None
             for r in runners]
    rates = _fill_mean(rates)
    mean_rate = sum(rates) / n
    cols["dist_win"] = [v - mean_rate for v in rates]
    # Against the race's standard: kept as points, not made relative, because the standard
    # already is the reference; a missing value takes the race mean like everything else.
    for key, out in (("last_vs_lws", "last_vs_lws"), ("best_vs_lws", "best_vs_lws"), ("trend_slope", "trend_slope")):
        cols[out] = _fill_mean([r.raw.get(key) for r in runners])
    starts = _fill_mean([math.log(1 + r.raw["starts"]) if r.raw.get("starts") is not None else None for r in runners])
    mean_starts = sum(starts) / n
    cols["starts_log"] = [v - mean_starts for v in starts]
    opens = [r.raw.get("open") for r in runners]
    inv = [1.0 / o if o is not None and o > 1 else None for o in opens]
    have = [v for v in inv if v is not None]
    if have:
        mean = sum(have) / len(have)
        inv = [mean if v is None else v for v in inv]
        tot = sum(inv)
        probs = [v / tot for v in inv]
        cols[MARKET_FEATURE] = [math.log(v) for v in probs]
        mean_p = sum(probs) / n
        cols["market_prob"] = [v - mean_p for v in probs]
    else:
        cols[MARKET_FEATURE] = [0.0] * n
        cols["market_prob"] = [0.0] * n
    # The market read against the form: lets the fit lean on Neural harder in some races.
    cols["market_x_neural"] = [m * q for m, q in zip(cols[MARKET_FEATURE], cols["neural_rel"])]
    # Little or no form (EXPERIENCE).
    cols["first_starter"] = [1.0 if r.raw.get("race_starts") == 0 else 0.0 for r in runners]
    cols["unrated"] = [1.0 if not r.raw.get("rated_runs") else 0.0 for r in runners]
    cols["trialled_recently"] = [1.0 if r.raw.get("trial_margin") is not None else 0.0 for r in runners]
    margins = _fill_mean([r.raw.get("trial_margin") for r in runners])
    mean_margin = sum(margins) / n
    cols["trial_margin"] = [v - mean_margin for v in margins]
    cols["first_starter_x_market"] = [fs * m for fs, m in zip(cols["first_starter"], cols[MARKET_FEATURE])]
    for i, r in enumerate(runners):
        r.x = {k: cols[k][i] for k in cols}


def bsp_chances(runners: list[Runner]) -> list[float] | None:
    """BSP-implied chances normalised to 1 over the runners with a BSP; None if fewer than
    two runners carry one."""
    inv = [1.0 / r.bsp if r.bsp and r.bsp > 1 else None for r in runners]
    have = [v for v in inv if v is not None]
    if len(have) < 2:
        return None
    mean = sum(have) / len(have)
    inv = [mean if v is None else v for v in inv]
    tot = sum(inv)
    return [v / tot for v in inv]


def softmax(scores: list[float]) -> list[float]:
    m = max(scores)
    w = [math.exp(s - m) for s in scores]
    t = sum(w)
    return [v / t for v in w]


def predict(beta: dict[str, float], runners: list[Runner]) -> list[float]:
    return softmax([sum(beta[k] * r.x.get(k, 0.0) for k in beta) for r in runners])


def _solve(a: list[list[float]], b: list[float]) -> list[float]:
    """Gaussian elimination with partial pivoting for a small dense system."""
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(m[r][c]))
        m[c], m[p] = m[p], m[c]
        if abs(m[c][c]) < 1e-12:
            m[c][c] = 1e-12
        for r in range(n):
            if r != c:
                f = m[r][c] / m[c][c]
                for k in range(c, n + 1):
                    m[r][k] -= f * m[c][k]
    return [m[i][n] / m[i][i] for i in range(n)]


def winner_chances(runners: list[Runner]) -> list[float] | None:
    """The race's actual result as a target: 1 on the winner, 0 on everything else. Fitting
    to this asks the model to be RIGHT. Fitting to BSP asks it to be the MARKET, and a model
    that reached BSP exactly would have no edge by construction, because it would price
    every runner the way the market already does. None when the winner is not stored."""
    idx = next((i for i, r in enumerate(runners) if r.finish == 1), None)
    if idx is None or len(runners) < 2:
        return None
    return [1.0 if i == idx else 0.0 for i in range(len(runners))]


def fit(races: list[Race], features: list[str], iterations: int = 40, ridge: float = 1e-8,
        target=bsp_chances) -> dict[str, float]:
    """Conditional logit fitted by Newton's method to whatever `target` returns per race.
    Minimises sum over races of sum_i q_i * (-log p_i), p from the model.
    Gradient: sum_i (p_i - q_i) x_i. Hessian: sum_i p_i (x_i - xbar)(x_i - xbar)^T.

    `target` is bsp_chances (mimic the market's closing price: low variance, every runner
    carries information, but the best attainable model IS the market) or winner_chances (be
    right about who won: one data point per race, noisier, but an objective that leaves room
    for an edge).

    Hand-calculated check: one race, two runners, one feature x = (1, 0), BSP 75% / 25%.
    p_a / p_b = exp(beta) = 3, so beta = ln 3 = 1.0986.
    """
    d = len(features)
    beta = [0.0] * d
    usable = [(r, q) for r in races if (q := target(r.runners)) is not None]
    if not usable:
        raise ValueError(f"no race {target.__name__} can score; nothing to fit against")
    for _ in range(iterations):
        g = [ridge * b for b in beta]
        h = [[ridge if i == j else 0.0 for j in range(d)] for i in range(d)]
        for race, q in usable:
            xs = [[r.x.get(f, 0.0) for f in features] for r in race.runners]
            p = softmax([sum(b * x for b, x in zip(beta, xr)) for xr in xs])
            xbar = [sum(p[i] * xs[i][j] for i in range(len(xs))) for j in range(d)]
            for i, xr in enumerate(xs):
                diff = p[i] - q[i]
                for j in range(d):
                    g[j] += diff * xr[j]
                for j in range(d):
                    for k in range(d):
                        h[j][k] += p[i] * (xr[j] - xbar[j]) * (xr[k] - xbar[k])
        step = _solve(h, [-v for v in g])
        beta = [b + s for b, s in zip(beta, step)]
        if max(abs(s) for s in step) < 1e-9:
            break
    return dict(zip(features, beta))


@dataclass
class Score:
    races: int
    runners: int
    kl_to_bsp: float          # mean per race of sum q ln(q/p): 0 is BSP itself
    log_loss: float           # mean over races of -ln p(winner)
    winner_top_rated: float   # share of races where the model's top pick won


def fit_cv(races: list[Race], features: list[str], folds: int = RIDGE_FOLDS, target=bsp_chances,
           ridges: list[float] | None = None) -> tuple[dict[str, float], float]:
    """Fit with the ridge strength chosen by cross-validation INSIDE these races, never on
    the races the model is later judged on: the training set is cut into `folds` blocks by
    date, each ridge is fitted on four and scored on the fifth, and the winner is refitted
    on all of them. Returns (beta, ridge). Selecting the ridge on the test block would be
    marking our own homework, which is what makes this worth the extra fitting."""
    ridges = ridges or RIDGES
    ordered = sorted(races, key=lambda r: (r.date, r.race_id))
    n = len(ordered)
    blocks = [ordered[i * n // folds:(i + 1) * n // folds] for i in range(folds)]
    best_ridge, best_loss = ridges[0], float("inf")
    for ridge in ridges:
        loss, scored = 0.0, 0
        for k, block in enumerate(blocks):
            train = [r for j, b in enumerate(blocks) if j != k for r in b]
            if not train or not block:
                continue
            try:
                beta = fit(train, features, ridge=ridge, target=target)
            except ValueError:
                continue
            s = score([predict(beta, r.runners) for r in block], block)
            if s.races:
                loss += s.kl_to_bsp * s.races
                scored += s.races
        if scored and loss / scored < best_loss:
            best_ridge, best_loss = ridge, loss / scored
    return fit(races, features, ridge=best_ridge, target=target), best_ridge


def score(probs_by_race: list[list[float]], races: list[Race]) -> Score:
    kl, ll, tops, n_r, n_run = 0.0, 0.0, 0, 0, 0
    for p, race in zip(probs_by_race, races):
        q = bsp_chances(race.runners)
        winner = next((i for i, r in enumerate(race.runners) if r.finish == 1), None)
        if q is None or winner is None:
            continue
        n_r += 1
        n_run += len(race.runners)
        kl += sum(qi * math.log(qi / max(pi, 1e-12)) for qi, pi in zip(q, p) if qi > 0)
        ll += -math.log(max(p[winner], 1e-12))
        tops += 1 if max(range(len(p)), key=lambda i: p[i]) == winner else 0
    if n_r == 0:
        return Score(0, 0, float("nan"), float("nan"), float("nan"))
    return Score(n_r, n_run, kl / n_r, ll / n_r, tops / n_r)


def calibration(probs_by_race: list[list[float]], races: list[Race], edges=(0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 1.01)) -> list[tuple[str, int, float, float]]:
    """(bucket, runners, mean rated chance, share that won) so a rated 20% can be checked
    against how often a rated-20% runner actually wins."""
    rows = []
    for lo, hi in zip(edges, edges[1:]):
        ps, wins = [], 0
        for p, race in zip(probs_by_race, races):
            for pi, r in zip(p, race.runners):
                if lo <= pi < hi and r.finish is not None:
                    ps.append(pi)
                    wins += 1 if r.finish == 1 else 0
        if ps:
            rows.append((f"{lo:.0%} to {min(hi, 1):.0%}", len(ps), sum(ps) / len(ps), wins / len(ps)))
    return rows


def market_probs(races: list[Race]) -> list[list[float]]:
    """The opening market as a model, for comparison."""
    out = []
    for race in races:
        out.append(softmax([r.x.get(MARKET_FEATURE, 0.0) for r in race.runners]))
    return out


def bsp_probs(races: list[Race]) -> list[list[float]]:
    return [bsp_chances(r.runners) or [1.0 / len(r.runners)] * len(r.runners) for r in races]


def fold_predictions(races: list[Race], features: list[str], folds: int = 5, target=bsp_chances, ridge: float = 1e-8):
    """(block index, race, model chances, morning market chances) for every race, each race
    priced by a model fitted on the OTHER date blocks, so no race is priced by a fit that
    saw it. Block 0 is the oldest racing."""
    ordered = sorted(races, key=lambda r: (r.date, r.race_id))
    n = len(ordered)
    blocks = [ordered[i * n // folds:(i + 1) * n // folds] for i in range(folds)]
    for k, block in enumerate(blocks):
        train = [r for j, b in enumerate(blocks) if j != k for r in b]
        if not train or not block:
            continue
        beta = fit(train, features, ridge=ridge, target=target)
        for race in block:
            yield k, race, predict(beta, race.runners), market_probs([race])[0]   # the morning market, the one we bet into


# The rules a value bet can be chosen by, each with the thresholds tried.
#   gap: the model's chance beats the market's by more than t (the live rule, t = 0.05). A
#        fixed gap in percentage points means far more on a $21 chance than a $2 one.
#   ev:  the model's chance times the morning price is more than 1 + t, i.e. the bet is
#        worth at least t per unit staked at the price we would take, on our numbers.
VALUE_RULES = {"gap": [0.02, 0.03, 0.05, 0.08, 0.10], "ev": [0.05, 0.10, 0.20, 0.30, 0.50]}
SWEEP_CHOOSE_BLOCKS = 3          # of 5: choose on the older three fifths, confirm on the newer two
SWEEP_MIN_BETS = 30              # a rule with fewer bets than this in the choosing half is not chosen


def value_edge(rule: str, model_p: float, market_p: float, price: float | None) -> float | None:
    """How far a runner clears the rule. Hand-checked: gap, model 0.30 v market 0.22 -> 0.08;
    ev, model 0.30 at $4.00 -> 0.30 x 4 - 1 = 0.20."""
    if rule == "gap":
        return model_p - market_p
    if rule == "ev":
        return model_p * price - 1.0 if price and price > 1 else None
    raise ValueError(rule)


@dataclass
class SweepRow:
    rule: str
    threshold: float
    half: str                # "choose" (older racing) or "confirm" (newer racing)
    bets: int
    winners: int
    roi_bsp: float           # one unit per bet, paid at Betfair SP
    roi_struck: float        # the same bets paid at the morning price


def value_sweep(races: list[Race], features: list[str], folds: int = 5, target=bsp_chances,
                ridge: float = 1e-8, under: float | None = None) -> tuple[list[SweepRow], tuple[str, float] | None]:
    """Every value rule and threshold replayed out of sample, split by date into a CHOOSING
    half (the older blocks) and a CONFIRMING half (the newer ones). The rule picked is the
    best by return at Betfair SP in the choosing half alone, so the confirming half is a
    genuine test of the choice rather than part of it. `under` keeps only runners the model
    rates under that price (the value_under_8 plan). Returns (rows, (rule, threshold) or None)."""
    cands = []   # (half, model_p, market_p, open price, won, bsp)
    for k, race, probs, market in fold_predictions(races, features, folds, target=target, ridge=ridge):
        half = "choose" if k < SWEEP_CHOOSE_BLOCKS else "confirm"
        for r, pi, mi in zip(race.runners, probs, market):
            if under is not None and not (pi > 0 and 1.0 / pi < under):
                continue
            cands.append((half, pi, mi, r.raw.get("open"), r.finish == 1, r.bsp if r.bsp else r.sp))
    rows = []
    for rule, thresholds in VALUE_RULES.items():
        for t in thresholds:
            for half in ("choose", "confirm"):
                bets = wins = 0
                ret_bsp = ret_struck = 0.0
                for h, pi, mi, price, won, bsp in cands:
                    if h != half:
                        continue
                    edge = value_edge(rule, pi, mi, price)
                    if edge is None or edge <= t or not price or price <= 1:
                        continue
                    bets += 1
                    wins += won
                    ret_bsp += (bsp if bsp and bsp > 1 else 1.0) if won else 0.0
                    ret_struck += price if won else 0.0
                rows.append(SweepRow(rule, t, half, bets, wins,
                                     (ret_bsp - bets) / bets if bets else 0.0, (ret_struck - bets) / bets if bets else 0.0))
    eligible = [r for r in rows if r.half == "choose" and r.bets >= SWEEP_MIN_BETS]
    best = max(eligible, key=lambda r: r.roi_bsp, default=None)
    return rows, ((best.rule, best.threshold) if best else None)


def plan_replay(races: list[Race], features: list[str], folds: int = 5, threshold: float = 0.05,
                target=bsp_chances, ridge: float = 1e-8) -> dict[str, dict]:
    """The paper book's plans run over the stored races as if the page had been built each
    morning, with no race priced by a fit that saw it: the races are cut into `folds`
    contiguous blocks by date and each block is priced by a model fitted on the others.
    Bets go on at the OPENING price (the market the morning page carries) and settle at
    Betfair SP, which is exactly the live book's rule; the SAME bets are then settled at the
    price they were STRUCK at, which is what taking the morning price actually gets you.
    Where the selections drift, BSP is the longer price and the first column flatters them.
    Both columns are the same bets, so they compare; an earlier version re-flagged against
    BSP, which needed tomorrow's price to pick today's bets and left two different bet sets
    under one bet count.
    Returns {"at_open": {plan: PlanSummary}, "at_struck": {...}, "races": n}."""
    from fk import paper as P
    from fk.report.probability import disagreement
    n = len(races)
    settled = {"at_open": [], "at_struck": []}
    for _k, race, probs, market in fold_predictions(races, features, folds, target=target, ridge=ridge):
        rows = [P.Row(r.horse_id, r.name, (1.0 / pi) if pi > 0 else None, r.raw.get("open"), pi, mi,
                      disagreement(mi, pi, threshold), None)
                for r, pi, mi in zip(race.runners, probs, market)]
        by_id = {r.horse_id: r for r in race.runners}
        for b in P.place(rows):
            runner = by_id[b.horse_id]
            won = runner.finish == 1
            common = {"plan": b.plan, "stake": b.stake, "won": won, "meeting_date": race.date,
                      "race_number": 0, "bet_id": f"{race.race_id}|{b.horse_id}|{b.plan}"}
            bsp = runner.bsp if runner.bsp else runner.sp
            settled["at_open"].append({**common, "returned": P.settle(b.stake, won, bsp)})
            settled["at_struck"].append({**common, "returned": P.settle(b.stake, won, b.price)})
    return {"at_open": P.summarise(settled["at_open"]), "at_struck": P.summarise(settled["at_struck"]), "races": n}


# ---- the strategy search -----------------------------------------------------------------
# A rule for picking a bet, crossed with a slice of the racing, each chosen on the older
# racing and shown on the newer racing it never saw. Many combinations are tried, so some
# will look good in the choosing half by chance alone; the confirming half and the margin
# of luck printed beside every figure are what separate an edge from a streak.

METRO_TRACKS = ("flemington", "caulfield", "moonee valley", "sandown", "the valley")
STRATEGY_RULES = [("ev", 0.05), ("ev", 0.10), ("ev", 0.15), ("ev", 0.20), ("ev", 0.25), ("ev", 0.35), ("ev", 0.50),
                  ("gap", 0.03), ("gap", 0.05), ("gap", 0.10)]


def _slices(price: float, field: int, first_starter: bool, metro: bool, saturday: bool = False,
            our_price: float | None = None, top_pick: bool = False) -> list[str]:
    out = ["all"]
    out.append("Saturdays" if saturday else "weekdays")
    if our_price is not None:
        out.append("we rate <$5" if our_price < 5 else "we rate $5-10" if our_price < 10 else "we rate $10+")
    if top_pick:
        out.append("our top pick")
    out.append("price <$4" if price < 4 else "price $4-8" if price < 8 else "price $8-16" if price < 16 else "price $16+")
    out.append("field <=8" if field <= 8 else "field 9-12" if field <= 12 else "field 13+")
    out.append("first starters" if first_starter else "raced horses")
    out.append("metro" if metro else "country and provincial")
    return out


@dataclass
class StrategyRow:
    rule: str
    threshold: float
    slice: str
    half: str
    bets: int
    winners: int
    roi_bsp: float
    se_bsp: float            # standard error of roi_bsp: the margin of luck, one sigma
    roi_open: float
    se_open: float


def _roi_se(returns: list[float]) -> tuple[float, float]:
    """Mean profit per unit and its standard error. Hand-checked: returns [3, 0, 0, 0]
    (one $3 winner in four) -> profits [2, -1, -1, -1], mean -0.25, sample sd 1.5,
    se 1.5 / 2 = 0.75."""
    n = len(returns)
    if n == 0:
        return 0.0, 0.0
    prof = [r - 1.0 for r in returns]
    mean = sum(prof) / n
    if n < 2:
        return mean, 0.0
    var = sum((p - mean) ** 2 for p in prof) / (n - 1)
    return mean, math.sqrt(var / n)


def strategy_search(races: list[Race], features: list[str], folds: int = 5, target=bsp_chances,
                    ridge: float = 1e-8, min_bets: int = 40) -> list[StrategyRow]:
    """Every (rule, threshold) x slice, out of sample, split into the choosing (older) and
    confirming (newer) halves. One unit a bet; paid at Betfair SP and at the average
    opening price. Slices with fewer than `min_bets` bets in either half are dropped."""
    cands = []
    for k, race, probs, market in fold_predictions(races, features, folds, target=target, ridge=ridge):
        half = "choose" if k < SWEEP_CHOOSE_BLOCKS else "confirm"
        metro = any((race.track or "").lower().startswith(t) for t in METRO_TRACKS)
        field_n = len(race.runners)
        try:
            from datetime import date as _d
            saturday = _d.fromisoformat(str(race.date)[:10]).weekday() == 5
        except ValueError:
            saturday = False
        top = max(range(len(probs)), key=lambda i: probs[i]) if probs else -1
        for i, (r, pi, mi) in enumerate(zip(race.runners, probs, market)):
            price = r.raw.get("open")
            if not price or price <= 1:
                continue
            fs = r.x.get("first_starter", 0.0) == 1.0
            cands.append((half, pi, mi, price, r.finish == 1, r.bsp if r.bsp and r.bsp > 1 else None,
                          _slices(price, field_n, fs, metro, saturday, (1.0 / pi) if pi > 0 else None, i == top)))
    rows = []
    for rule, t in STRATEGY_RULES:
        buckets: dict[tuple[str, str], tuple[list[float], list[float], int]] = {}
        for half, pi, mi, price, won, bsp, slices in cands:
            if pi > 3.0 * mi:          # the live guard: never bet a rating 3x the market
                continue
            edge = value_edge(rule, pi, mi, price)
            if edge is None or edge <= t:
                continue
            for sl in slices:
                rb, ro, w = buckets.get((sl, half), ([], [], 0))
                rb.append((bsp if bsp else 1.0) if won else 0.0)
                ro.append(price if won else 0.0)
                buckets[(sl, half)] = (rb, ro, w + (1 if won else 0))
        for sl in sorted({s for s, _ in buckets}):
            got = {h: buckets.get((sl, h)) for h in ("choose", "confirm")}
            if any(g is None or len(g[0]) < min_bets for g in got.values()):
                continue
            for h, (rb, ro, w) in got.items():
                mb, sb = _roi_se(rb)
                mo, so = _roi_se(ro)
                rows.append(StrategyRow(rule, t, sl, h, len(rb), w, mb, sb, mo, so))
    return rows
