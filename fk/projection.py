"""Projected rating and race simulation. Pure, hand-tested, no numpy.

The founder's method, in his words: "we come out to a number that we think the horse is
going to run on the day, through history, scope, race shape (slower lead, has to have a
bigger last 600m, backmarkers are disadvantaged), then we get a rating for every horse
and run a sim of how many times it wins."

So, per runner:
  base      a recency-weighted mean of its last few rated race runs (adjusted to today's
            weight); a horse on the rise projects at least its last run
  scope     lightly raced horses get room to improve; a rising or falling trend moves it
  shape     tempo x settling position: in a slow-run race the leaders gain and the
            backmarkers lose, in a fast one the reverse
  late      last-600m speed against class, worth more when the tempo is slow
  sd        how much the horse's own ratings wander run to run, wider when lightly raced
and the race is run many times with each horse's figure drawn around its projection.
The win chance is computed exactly (numerical integration of the Gaussian order
statistic) so the fit against Betfair SP has no simulation noise; a Monte Carlo run is
kept for place chances and the report's "wins N of 20,000".

Every weight is a parameter, and fit_params tunes them against BSP over resulted races
(coordinate search), so the method is the founder's and the numbers are the data's.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field, replace

from fk import fields as F
from fk.trend import rating_series, trend


@dataclass(frozen=True)
class Params:
    recent_runs: int = 4         # runs in the base
    decay: float = 0.7           # weight per run further back (newest 1.0)
    scope_bonus: float = 1.5     # points at zero career starts, tapering to nothing at 12
    trend_weight: float = 0.5    # points per (rating point per run) of slope, slope clamped to +-2
    shape_weight: float = 1.5    # points between a leader and a backmarker at full tempo
    late_weight: float = 1.0     # points per length of last-600m vs class at even tempo
    sd_floor: float = 3.0        # least run-to-run spread, rating points
    light_sd: float = 1.5        # extra spread under six starts or three rated runs
    sd_scale: float = 1.0        # overall spread multiplier, fitted
    unrated_gap: float = 3.0     # a runner with no rated run projects this far below the field's mean projection
    unrated_sd: float = 3.0      # and with this much extra spread (before sd_scale)
    neural_weight: float = 0.0   # points added per unit of Neural relative to the race's top (top = 1), centred on the field


TEMPO_WORDS = {"slow": -1.0, "below average": -0.5, "average": 0.0, "above average": 0.5, "fast": 1.0}
TEMPO_FULL_SCALE = 0.3   # lengths per 100m that counts as a fully fast or fully slow tempo


def tempo_score(tempo: dict | None) -> float:
    """-1 (slow) to +1 (fast) from Form King's expectedTempo: the mean of min and max
    (lengths per 100m vs benchmark) over TEMPO_FULL_SCALE, clamped; else the words."""
    if not tempo:
        return 0.0
    vals = []
    for k in ("min", "max"):
        try:
            vals.append(float(tempo.get(k)))
        except (TypeError, ValueError):
            pass
    if vals:
        return max(-1.0, min(1.0, (sum(vals) / len(vals)) / TEMPO_FULL_SCALE))
    words = [str(tempo.get(k) or "").lower() for k in ("minCategory", "maxCategory")]
    scores = [TEMPO_WORDS[w] for w in words if w in TEMPO_WORDS]
    if not scores:
        d = str(tempo.get("description") or "").lower()
        scores = [v for w, v in TEMPO_WORDS.items() if w == d]
    return sum(scores) / len(scores) if scores else 0.0


@dataclass
class Inputs:
    """What a runner brings to the projection, read once from its record."""
    horse_id: str
    name: str
    ratings: list[float]          # rated race runs, oldest first, adjusted to today's weight
    slope: float | None
    starts: int | None
    late600: float | None         # recency-weighted last-600m vs class, lengths (+ = faster than class)
    settle: float | None          # 0 leader .. 1 backmarker, from the speedmap; None if unmapped
    neural: float | None = None   # Form King's Neural points today


def inputs_from_entry(e: dict, predicted_position: float | None = None, field_size: int | None = None) -> Inputs | None:
    if F.entry_scratched(e):
        return None
    runs = [F.run_ratings(p) for p in F.entry_past_events(e)]
    runs = sorted([r for r in runs if r.get("date")], key=lambda r: r["date"])
    races = [r for r in runs if not r.get("trial")]
    series = [v for v in rating_series(races) if v is not None]
    tr = trend(rating_series(races))
    career = F.entry_form_record(e).get("careerForm")
    starts = None
    if career and ":" in str(career):
        try:
            starts = int(str(career).split(":")[0])
        except ValueError:
            starts = None
    lates = [F.run_last_600_vs_class(p) for p in sorted(F.entry_past_events(e), key=lambda p: F.past_event_date(p) or "", reverse=True)]
    lates = [v for v in lates if v is not None][:5]
    late = None
    if lates:
        w = [0.8 ** i for i in range(len(lates))]
        late = sum(v * wi for v, wi in zip(lates, w)) / sum(w)
    settle = None
    if predicted_position is not None and field_size and field_size > 1:
        settle = max(0.0, min(1.0, (float(predicted_position) - 1) / (field_size - 1)))
    return Inputs(F.horse_id(e), F.horse_name(e), series, tr.slope, starts, late, settle, F.entry_neural_rating(e))


@dataclass
class Projection:
    horse_id: str
    name: str
    base: float | None
    scope: float
    shape: float
    late: float
    neural: float                 # the Neural component, when the fit gives it weight
    projected: float | None
    sd: float | None
    n_rated: int
    note: str


def project(inp: Inputs, tempo: float, p: Params) -> Projection:
    """One runner's projected figure for today and the spread around it."""
    rs = inp.ratings[-p.recent_runs:]
    if not rs:
        return Projection(inp.horse_id, inp.name, None, 0.0, 0.0, 0.0, 0.0, None, None, 0, "no rated run")
    w = [p.decay ** i for i in range(len(rs))][::-1]          # newest weight 1.0
    base = sum(r * wi for r, wi in zip(rs, w)) / sum(w)
    notes = []
    if inp.slope is not None and inp.slope >= 0.75 and rs[-1] > base:
        base = rs[-1]                                           # on the rise: at least its last run
        notes.append("rising, projects at its last run")
    scope = 0.0
    if inp.starts is not None and inp.starts < 12:
        scope += p.scope_bonus * (12 - inp.starts) / 12
    if inp.slope is not None:
        scope += p.trend_weight * max(-2.0, min(2.0, inp.slope))
    shape = 0.0
    if inp.settle is not None:
        shape = p.shape_weight * tempo * (inp.settle - 0.5) * 2   # slow tempo: leaders up, backmarkers down
    late = 0.0
    if inp.late600 is not None:
        late = p.late_weight * inp.late600 * (1 - 0.5 * tempo)   # late speed worth more when the tempo is slow
    hist = inp.ratings[-6:]
    if len(hist) >= 2:
        m = sum(hist) / len(hist)
        sd = math.sqrt(sum((v - m) ** 2 for v in hist) / (len(hist) - 1))
    else:
        sd = 0.0
    sd = max(p.sd_floor, sd)
    if (inp.starts is not None and inp.starts < 6) or len(inp.ratings) < 3:
        sd += p.light_sd
    sd *= p.sd_scale
    return Projection(inp.horse_id, inp.name, base, scope, shape, late, 0.0, base + scope + shape + late, sd, len(inp.ratings),
                      "; ".join(notes))


def project_field(inputs: list[Inputs], tempo: float, p: Params) -> list[Projection]:
    """Every runner projected; one with no rated run is not dropped but placed below the
    field's mean projection with a wide spread, because "unknown" is not "cannot win"
    (maidens are full of them and one of them wins)."""
    projs = [project(i, tempo, p) for i in inputs]
    # Neural as a component of the figure: form points relative to the race's top, centred
    # on the field, so a runner with the most points gains and the rest give back.
    if p.neural_weight:
        neur = [i.neural for i in inputs]
        have = [v for v in neur if v is not None]
        if have and max(have) > 0:
            top = max(have)
            rel = [(max(v, top * 0.01) / top) if v is not None else None for v in neur]
            known = [r for r in rel if r is not None]
            mean_rel = sum(known) / len(known)
            for q, r in zip(projs, rel):
                if q.projected is not None and r is not None:
                    q.neural = p.neural_weight * (r - mean_rel)
                    q.projected += q.neural
    rated = [q.projected for q in projs if q.projected is not None]
    if rated:
        mean = sum(rated) / len(rated)
        for q in projs:
            if q.projected is None:
                q.base = mean - p.unrated_gap
                q.projected = q.base
                q.sd = (p.sd_floor + p.light_sd + p.unrated_sd) * p.sd_scale
                q.note = "no rated run: field mean less the unrated gap, wide spread"
    return projs


def _phi(z: float) -> float:
    return math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)


def _Phi(z: float) -> float:
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def win_probabilities(projs: list[Projection], grid: int = 160) -> dict[str, float | None]:
    """Exact chance each runner posts the highest figure when every figure is drawn from
    N(projected, sd): P(i) = integral of phi_i(x) * product_j Phi_j(x) dx, by the
    trapezoid rule. Runners without a projection get None and are left out.

    Hand-calculated check: two runners at 100 and 97, both sd 3. The difference is
    N(3, 3*sqrt2), so P(first) = Phi(3 / 4.2426) = Phi(0.7071) = 0.7602.
    """
    live = [q for q in projs if q.projected is not None and q.sd]
    if not live:
        return {q.horse_id: None for q in projs}
    if len(live) == 1:
        return {q.horse_id: (1.0 if q is live[0] else None) for q in projs}
    lo = min(q.projected - 5 * q.sd for q in live)
    hi = max(q.projected + 5 * q.sd for q in live)
    xs = [lo + (hi - lo) * k / (grid - 1) for k in range(grid)]
    cdf = [[_Phi((x - q.projected) / q.sd) for x in xs] for q in live]
    out: dict[str, float | None] = {q.horse_id: None for q in projs}
    total = 0.0
    for i, q in enumerate(live):
        vals = []
        for k, x in enumerate(xs):
            prod = 1.0
            for j in range(len(live)):
                if j != i:
                    prod *= cdf[j][k]
            vals.append(_phi((x - q.projected) / q.sd) / q.sd * prod)
        area = sum((vals[k] + vals[k + 1]) / 2 * (xs[k + 1] - xs[k]) for k in range(grid - 1))
        out[q.horse_id] = area
        total += area
    for q in live:
        out[q.horse_id] = out[q.horse_id] / total    # the integral's small numerical drift, framed to 100%
    return out


def simulate(projs: list[Projection], n: int = 20000, seed: int = 7) -> dict[str, dict[str, float]]:
    """Run the race n times: each figure drawn around its projection; wins and places (top 3)."""
    rng = random.Random(seed)
    live = [q for q in projs if q.projected is not None and q.sd]
    if not live:
        return {}                       # no runner has a projection yet (e.g. weights-stage fields): nothing to simulate
    wins = {q.horse_id: 0 for q in live}
    places = {q.horse_id: 0 for q in live}
    for _ in range(n):
        drawn = sorted(((rng.gauss(q.projected, q.sd), q.horse_id) for q in live), reverse=True)
        wins[drawn[0][1]] += 1
        for _, hid in drawn[:3]:
            places[hid] += 1
    return {hid: {"win": wins[hid] / n, "place": places[hid] / n, "runs": n} for hid in wins}


@dataclass
class ProjRace:
    race_id: str
    inputs: list[Inputs]
    tempo: float
    bsp: dict[str, float]         # normalised BSP chances by horse id
    winner: str | None


def race_probs(race: ProjRace, p: Params) -> dict[str, float | None]:
    return win_probabilities(project_field(race.inputs, race.tempo, p))


def kl_to_bsp(races: list[ProjRace], p: Params) -> float:
    tot, n = 0.0, 0
    for r in races:
        probs = race_probs(r, p)
        got = {k: v for k, v in probs.items() if v is not None and k in r.bsp}
        if len(got) < 2:
            continue
        s = sum(got.values())
        q = {k: r.bsp[k] for k in got}
        qs = sum(q.values())
        tot += sum((q[k] / qs) * math.log((q[k] / qs) / max(got[k] / s, 1e-12)) for k in got if q[k] > 0)
        n += 1
    return tot / n if n else float("inf")


SEARCH = {
    "sd_scale": [0.7, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 9.0],
    "unrated_gap": [0.0, 2.0, 4.0, 7.0, 10.0],
    "shape_weight": [0.0, 1.0, 2.0, 3.0, 4.5, 6.0],
    "late_weight": [0.0, 0.5, 1.0, 2.0, 3.0, 4.5],
    "scope_bonus": [0.0, 1.0, 2.0, 3.0, 4.5, 6.0],
    "trend_weight": [0.0, 0.5, 1.0, 1.5, 2.5],
    "neural_weight": [0.0, 5.0, 10.0, 15.0, 20.0, 30.0],
}


def fit_params(races: list[ProjRace], start: Params = Params(), sweeps: int = 3) -> Params:
    """Coordinate search: each parameter in turn over its candidates, keeping the value
    that brings the projected chances closest to BSP, repeated until nothing moves."""
    best, best_loss = start, kl_to_bsp(races, start)
    for _ in range(sweeps):
        moved = False
        for name, cands in SEARCH.items():
            for v in cands:
                trial = replace(best, **{name: v})
                loss = kl_to_bsp(races, trial)
                if loss < best_loss - 1e-9:
                    best, best_loss, moved = trial, loss, True
        if not moved:
            break
    return best
