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
from fk.trend import rating_series

FORM_FEATURES = ["neural_rel", "last_rel", "peak_rel", "peak12_rel"]
MARKET_FEATURE = "open_logit"


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


def runner_from_entry(e: dict) -> Runner | None:
    """A RaceEntry (Get Race Form) already run: features from what was knowable before the
    jump, the result from horseResult. None for a scratching."""
    if F.entry_scratched(e):
        return None
    res = F.entry_result(e)
    peak, peak12 = F.entry_peak_ratings(e)
    runs = [F.run_ratings(p) for p in F.entry_past_events(e)]
    runs = sorted([r for r in runs if r.get("date")], key=lambda r: r["date"])
    series = [v for v in rating_series(runs) if v is not None]
    odds = F.entry_odds(e)
    open_price = F.odds_opening_price(odds) if odds else None
    return Runner(
        horse_id=F.horse_id(e), name=F.horse_name(e),
        raw={"neural": F.entry_neural_rating(e), "last": series[-1] if series else None,
             "peak": peak, "peak12": peak12, "open": open_price},
        bsp=F.result_betfair_sp(res) if res else None,
        sp=F.result_starting_price(res) if res else None,
        finish=F.result_finish_position(res) if res else None,
    )


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
    for key, out in (("last", "last_rel"), ("peak", "peak_rel"), ("peak12", "peak12_rel")):
        vals = _fill_mean([r.raw.get(key) for r in runners])
        best = max(vals)
        cols[out] = [v - best for v in vals]
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


def fit(races: list[Race], features: list[str], iterations: int = 40, ridge: float = 1e-8) -> dict[str, float]:
    """Conditional logit fitted to the BSP-implied chances by Newton's method.
    Minimises sum over races of sum_i q_i * (-log p_i), q from BSP, p from the model.
    Gradient: sum_i (p_i - q_i) x_i. Hessian: sum_i p_i (x_i - xbar)(x_i - xbar)^T.

    Hand-calculated check: one race, two runners, one feature x = (1, 0), BSP 75% / 25%.
    p_a / p_b = exp(beta) = 3, so beta = ln 3 = 1.0986.
    """
    d = len(features)
    beta = [0.0] * d
    usable = [(r, q) for r in races if (q := bsp_chances(r.runners)) is not None]
    if not usable:
        raise ValueError("no race with two or more BSPs to fit against")
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
