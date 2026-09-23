import math

from fk import backtest as B
from fk import paper as P
from fk import realprice as R


def _runner(hid, price):
    return B.Runner(hid, hid, {"open": price}, None, None, None)


def test_with_price_sets_the_market_input_and_leaves_a_missing_price_alone():
    e = {"odds": {"avgOpen": 4.0, "bestNow": 5.0}}
    assert R.with_price(e, 6.0)["odds"] == {"avgOpen": 6.0, "bestNow": 5.0}
    assert R.with_price(e, None) is e
    assert R.with_price(e, 1.0) is e
    assert R.with_price({}, 3.0)["odds"] == {"avgOpen": 3.0}


def test_attach_opening_average_copies_the_untouched_logit():
    priced = [_runner("a", 2.0), _runner("b", 6.0), _runner("c", 9.0)]
    original = [_runner("a", 3.0), _runner("b", 4.0)]
    for r in priced:
        r.x = {B.MARKET_FEATURE: math.log(1 / r.raw["open"])}
    for r in original:
        r.x = {B.MARKET_FEATURE: math.log(1 / r.raw["open"])}
    R.attach_opening_average(priced, original)
    assert priced[0].x[R.AVG_OPEN_FEATURE] == math.log(1 / 3.0)
    assert priced[1].x[R.AVG_OPEN_FEATURE] == math.log(1 / 4.0)
    # no opening average stored for c: 'no move since open', the real price's own logit
    assert priced[2].x[R.AVG_OPEN_FEATURE] == priced[2].x[B.MARKET_FEATURE]


def test_real_price_features_are_the_compact_set_plus_the_opening_average():
    assert R.REAL_PRICE_FEATURES[0] == B.MARKET_FEATURE
    assert R.REAL_PRICE_FEATURES[-1] == R.AVG_OPEN_FEATURE
    assert len(R.REAL_PRICE_FEATURES) == 11
    assert R.rated_price(0.25) == 4.0 and R.rated_price(None) is None


def test_place_real_price_plans_and_guards():
    # a: rated $2.50 (40%) at $3.00 -> worth 20c: top pick, ev05, ev10, kelly
    # b: rated $8 (12.5%) at $8.50 -> worth 6c: ev05 and a small Kelly stake
    # c: rated $3 (33%) at $21 (market 4.8%): seven times the market, refused
    # d: rated $10 at $6 -> negative value, nothing
    rows = [
        P.Row("a", "A", 2.5, 3.0, 0.40, 0.33, None),
        P.Row("b", "B", 8.0, 8.5, 0.125, 0.11, None),
        P.Row("c", "C", 3.0, 21.0, 0.333, 0.048, None),
        P.Row("d", "D", 10.0, 6.0, 0.10, 0.17, None),
    ]
    bets = P.place_real_price(rows)
    plans = sorted((b.plan, b.horse_id) for b in bets)
    assert plans == [("rp_top_pick", "a"), ("rp_value_ev05", "a"), ("rp_value_ev05", "b"),
                     ("rp_value_ev05_kelly", "a"), ("rp_value_ev05_kelly", "b"), ("rp_value_ev10", "a")]
    kelly = next(b for b in bets if b.plan == "rp_value_ev05_kelly" and b.horse_id == "a")
    # f = (0.4 x 2 - 0.6) / 2 = 0.1; quarter of that on 100 units = 2.5
    assert kelly.stake == 2.5
    assert all(p in P.PLANS for p in P.REAL_PRICE_PLANS)
    # a race already run is never bet
    rows[0].finish = 1
    assert P.place_real_price(rows) == []


def test_model_family_names_the_real_price_refit():
    assert P.model_family("realprice_compact_open (95 races to 2026-09-22)") == "real-price refit"
    assert P.model_family("market_kitchen_sink_exp (3382 races to 2026-09-22)") == "reads the market"


def test_no_value_plan_backs_a_runner_rated_at_the_cap_or_longer():
    # rated $60 (1.67%) at $90: 50c of value on paper, nine tenths of a one-book price, refused
    rows = [
        P.Row("fav", "Fav", 2.0, 2.2, 0.50, 0.45, None),
        P.Row("rough", "Rough", 60.0, 90.0, 1 / 60, 1 / 90, "model_higher"),
    ]
    assert all(b.horse_id == "fav" for b in P.place(rows))
    assert all(b.horse_id == "fav" for b in P.place_real_price(rows))
    # one dollar under the cap and it is a candidate again (still subject to the 3x guard)
    rows[1].rated_price = P.MAX_RATED_PRICE - 1
    rows[1].model_prob = 1 / rows[1].rated_price
    assert any(b.horse_id == "rough" for b in P.place(rows))
