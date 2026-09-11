"""Market-implied and rating-implied win probabilities, with the method stated on the page."""
from __future__ import annotations

import math


def market_implied(prices: dict[str, float | None]) -> dict[str, float | None]:
    """1/price, normalised so the field sums to 1 (removes the bookmaker's overround).
    Runners with no price get None and are excluded from the normalisation."""
    raw = {k: (1.0 / p) for k, p in prices.items() if p is not None and p > 1.0}
    total = sum(raw.values())
    if total <= 0:
        return {k: None for k in prices}
    return {k: (raw[k] / total if k in raw else None) for k in prices}


def rating_implied(ratings: dict[str, float | None], scale: float) -> dict[str, float | None]:
    """Softmax of rating/scale over the runners that have a rating.

    ASSUMPTION, printed on the report: Form King's Neural rating is treated as a
    log-odds-like score and converted with softmax(rating / scale). If the spec
    exposes a rated price or probability, map it in fk.fields and prefer that;
    this is a stand-in until then. `scale` is the rating-point gap that doubles
    the odds ratio divided by ln 2; the default in the report is documented there.
    """
    if scale <= 0:
        raise ValueError("scale must be positive")
    have = {k: v for k, v in ratings.items() if v is not None}
    if not have:
        return {k: None for k in ratings}
    top = max(have.values())
    exps = {k: math.exp((v - top) / scale) for k, v in have.items()}
    total = sum(exps.values())
    return {k: (exps[k] / total if k in exps else None) for k in ratings}


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
