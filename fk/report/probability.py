"""Market-implied and rating-implied win probabilities, with the method stated on the page."""
from __future__ import annotations

import math


def market_implied(prices: dict[str, float | None]) -> dict[str, float | None]:
    """1/price, normalised so the field sums to 1 (removes the bookmaker's overround).
    Runners with no price get None and are excluded from the normalisation."""
    raw = {k: (1.0 / float(p)) for k, p in prices.items() if p is not None and float(p) > 1.0}
    total = sum(raw.values())
    if total <= 0:
        return {k: None for k in prices}
    return {k: (raw[k] / total if k in raw else None) for k in prices}


def rating_implied(ratings: dict[str, float | None], scale: float | None = None) -> dict[str, float | None]:
    """Neural-implied win chance.

    Form King describes Neural as "a collection of points awarded to runners based on
    traditional form and statistics", and its scale moves from race to race (a field can
    top out at 15 points or at 40), so every runner is first read RELATIVE TO THE TOP
    RUNNER of its race (x = points / top, so the top horse is 1.0). With a `scale` k the
    chance is a softmax on that: p_i proportional to exp(k * x_i). k says how much of the
    race a gap in points is worth and is FITTED to the market (fit_scale) rather than
    assumed, because a flat share of points (scale None, the old stand-in) rated a $1.65
    favourite at $5.63: it cannot tell a dominant top horse from a close one.
    A runner with zero or negative points gets a floor of 1% of the top runner.
    """
    have = {k: float(v) for k, v in ratings.items() if v is not None}
    if not have:
        return {k: None for k in ratings}
    top = max(have.values())
    if top <= 0:
        n = len(have)
        return {k: (1.0 / n if k in have else None) for k in ratings}
    x = {k: max(v, top * 0.01) / top for k, v in have.items()}
    if scale is None:
        total = sum(x.values())
        return {k: (x[k] / total if k in x else None) for k in ratings}
    w = {k: math.exp(scale * v) for k, v in x.items()}
    total = sum(w.values())
    return {k: (w[k] / total if k in w else None) for k in ratings}


DEFAULT_SCALE = 10.0   # used only when a meeting has no market to fit against; stated on the page


def fit_scale(races: list[tuple[dict[str, float | None], dict[str, float | None]]],
              lo: float = 0.5, hi: float = 40.0) -> float | None:
    """The softmax scale k that best matches the market across a set of races: minimises
    the sum over runners of market_p * ln(market_p / model_p) (the cross-entropy of the
    market against the model), by golden-section search on [lo, hi]. Each race is a
    (Neural ratings, market probabilities) pair; runners missing either are skipped, and
    a race with fewer than two usable runners contributes nothing. None when no race can.

    Hand-calculated check: two runners at 80 and 70 points, market 75% / 25%. x = 1 and
    0.875, so p_a / p_b = exp(0.125 k) = 3 and k = ln 3 / 0.125 = 8.7889.
    """
    usable = []
    for ratings, market in races:
        keys = [k for k in ratings if ratings.get(k) is not None and market.get(k) is not None]
        if len(keys) < 2:
            continue
        mk = {k: market[k] for k in keys}
        tot = sum(mk.values())
        if tot <= 0:
            continue
        usable.append(({k: ratings[k] for k in keys}, {k: v / tot for k, v in mk.items()}))
    if not usable:
        return None

    def loss(k: float) -> float:
        total = 0.0
        for ratings, market in usable:
            model = rating_implied(ratings, k)
            for key, p in market.items():
                if p > 0:
                    total += p * math.log(p / max(model[key] or 1e-12, 1e-12))
        return total

    g = (math.sqrt(5) - 1) / 2
    a, b = lo, hi
    c, d = b - g * (b - a), a + g * (b - a)
    fc, fd = loss(c), loss(d)
    for _ in range(80):
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - g * (b - a)
            fc = loss(c)
        else:
            a, c, fc = c, d, fd
            d = a + g * (b - a)
            fd = loss(d)
    return (a + b) / 2


def disagreement(market: float | None, model: float | None, threshold: float = 0.05) -> str | None:
    """'model_higher' or 'market_higher' when they differ by more than the threshold, else None."""
    if market is None or model is None:
        return None
    diff = model - market
    if diff > threshold:
        return "model_higher"
    if diff < -threshold:
        return "market_higher"
    return None


def market_percentage(prices: dict[str, float | None]) -> float | None:
    """The bookmaker's market percentage (overround): sum of 1/price x 100. About 118 to 132
    for a fixed-odds book. None when no runner has a price."""
    inv = [1.0 / p for p in prices.values() if p is not None and p > 1.0]
    return sum(inv) * 100 if inv else None


def rated_price(prob: float | None) -> float | None:
    """A probability framed to 100% expressed as a price: 1/p."""
    if prob is None or prob <= 0:
        return None
    return 1.0 / prob


def value_points(market: float | None, model: float | None) -> float | None:
    """Betfair Hub's value %: (1 / rated price) minus (1 / market price), in probability
    points. +7.5 means the model gives the runner 7.5 points more chance than the market."""
    if market is None or model is None:
        return None
    return (model - market) * 100


def settling_group(rank: int, field_size: int) -> str:
    """Australian speed-map convention: Leader, On pace, Midfield, Off pace, Backmarker.
    rank is 1 for the predicted leader. Groups by share of the field so a 6-horse race
    and a 16-horse race both read sensibly."""
    if rank <= 1:
        return "Leader"
    share = (rank - 1) / max(field_size - 1, 1)
    if share <= 0.34:
        return "On pace"
    if share <= 0.60:
        return "Midfield"
    if share <= 0.85:
        return "Off pace"
    return "Backmarker"


def tempo_reading(leader_or_on_pace: int) -> str:
    """A plain rule, stated so it can be argued with: three or more runners mapping Leader
    or On pace is pressure on the speed; two is a genuine tempo; one is likely slow."""
    if leader_or_on_pace >= 3:
        return "pressure on the speed: favours runners getting home"
    if leader_or_on_pace == 2:
        return "genuine tempo"
    return "likely slow: favours the on-pace runners"
