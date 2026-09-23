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
}
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


def runner_from_entry(e: dict, race_distance: int | None = None, lws: float | None = None) -> Runner | None:
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
        cols[MARKET_FEATURE] = [math.log(v / tot) for v in inv]
    else:
        cols[MARKET_FEATURE] = [0.0] * n
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


def plan_replay(races: list[Race], features: list[str], folds: int = 5, threshold: float = 0.05,
                target=bsp_chances) -> dict[str, dict]:
    """The paper book's plans run over the stored races as if the page had been built each
    morning, with no race priced by a fit that saw it: the races are cut into `folds`
    contiguous blocks by date and each block is priced by a model fitted on the others.
    Bets go on at the OPENING price (the market the morning page carries) and settle at
    Betfair SP, which is exactly the live book's rule; a second pass judges the flags
    against BSP and bets at BSP, which says whether the edge survives the market firming. Returns
    {"at_open": {plan: PlanSummary}, "at_bsp": {...}, "races": n}."""
    from fk import paper as P
    from fk.report.probability import disagreement
    ordered = sorted(races, key=lambda r: (r.date, r.race_id))
    n = len(ordered)
    blocks = [ordered[i * n // folds:(i + 1) * n // folds] for i in range(folds)]
    settled = {"at_open": [], "at_struck": []}
    for k, block in enumerate(blocks):
        train = [r for j, b in enumerate(blocks) if j != k for r in b]
        if not train or not block:
            continue
        beta = fit(train, features, target=target)
        for race in block:
            probs = predict(beta, race.runners)
            market = market_probs([race])[0]     # the morning market, the one we bet into
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
