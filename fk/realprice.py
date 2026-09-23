"""The real-price model: the compact feature set plus the opening average, fitted on the
races that carry a REAL 9am price, priced with the price a bet is struck at.

The deployed model was taught to correct Form King's soft average opening price and
over-corrects a sharp one (0.1007 against the 9am market's 0.0908 on the first 92 races).
This one learns its market weight from the 9am price itself, keeps the opening average
beside it (the move from open to 9am is information the 9am price alone does not carry),
and adds the ten form figures a sample of a hundred races can actually pin down. On those
92 races it scored 0.0851 to the market's 0.0908, picked on the same sample, so the paper
book is the honest test. Pure helpers here; the fit, which needs the database, lives in
scripts/real_price_model.py.
"""
from __future__ import annotations

import math

from fk import backtest as B

MODEL_LABEL = "realprice_compact_open"
AVG_OPEN_FEATURE = "avg_open_logit"
AVG_NOW_FEATURE = "avg_now_logit"
COMPACT_FEATURES = [B.MARKET_FEATURE, "neural_rel", "speed_rel", "last_rel", "peak_rel", "jockey_win", "trainer_win",
                    "class_win", "first_starter", "first_starter_x_market"]
REAL_PRICE_FEATURES = COMPACT_FEATURES + [AVG_OPEN_FEATURE]
REAL_PRICE_RIDGE = 0.1
# Fewer real-price races than this and the model is not fitted. It feeds the PAPER book only,
# where a bet costs nothing and is how the sample grows; eleven coefficients on 45 races is
# thin, and the book's record, not the fit, is what decides whether it is ever recommended.
# (On 24 Sep 53 races carried both a real 9am price and a Betfair SP; the replay's "92" counted
# races before dropping those without a BSP.)
MIN_REAL_PRICE_RACES = 45
# A race is priced only when this share of its runners carry the real price.
MIN_PRICE_COVERAGE = 0.8


def with_price(e: dict, price: float | None) -> dict:
    """The entry with the model's market input (the avgOpen field the features read) set
    to `price`. No price, or a price of 1 or under: the entry is left alone."""
    if not price or price <= 1:
        return e
    odds = dict((e.get("odds") or {}) if isinstance(e.get("odds"), dict) else {})
    odds["avgOpen"] = price
    return {**e, "odds": odds}


def attach_opening_average(priced: list[B.Runner], original: list[B.Runner]) -> None:
    """Copy the opening average's within-race logit from the untouched runners onto the
    runners priced with the real price, as AVG_OPEN_FEATURE. A runner with no match gets
    the real price's own logit, which says 'no move since open'."""
    by_horse = {r.horse_id: r for r in original}
    for r in priced:
        o = by_horse.get(r.horse_id)
        r.x[AVG_OPEN_FEATURE] = o.x.get(B.MARKET_FEATURE, 0.0) if o is not None else r.x.get(B.MARKET_FEATURE, 0.0)


def rated_price(p: float | None) -> float | None:
    return round(1.0 / p, 2) if p and p > 0 else None


def kl_to_bsp(probs: list[float], race: B.Race) -> float:
    q = B.bsp_chances(race.runners)
    return sum(qi * math.log(qi / max(pi, 1e-12)) for qi, pi in zip(q, probs) if qi > 0)
