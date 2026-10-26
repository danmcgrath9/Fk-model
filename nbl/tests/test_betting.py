"""Market chances, Benter's combination and staking, hand-checked (no cache needed)."""
import numpy as np
import pandas as pd
import pytest

from nbl.betting import market, staking


def test_margin_removed_proportionally_and_by_power():
    a, b = market.fair_chances(np.array([1.87]), np.array([1.87]))
    assert a[0] == pytest.approx(0.5) and b[0] == pytest.approx(0.5)
    a, b = market.fair_chances(np.array([1.50]), np.array([2.50]))
    assert a[0] + b[0] == pytest.approx(1.0)
    assert a[0] == pytest.approx((1 / 1.5) / (1 / 1.5 + 1 / 2.5))       # 0.625
    pa, pb = market.fair_chances(np.array([1.50]), np.array([2.50]), method='power')
    assert pa[0] + pb[0] == pytest.approx(1.0, abs=1e-9)
    assert pa[0] > a[0]                                                  # power shades the favourite less


def test_default_combination_is_the_racing_rule_until_enough_results():
    w = market.fit_combination([0.6] * 10, [0.5] * 10, [1] * 10)
    assert not w['fitted'] and w['w_ours'] == 0.5 and w['w_market'] == 0.5
    assert market.combine(0.5, 0.5) == pytest.approx(0.5)
    p = market.combine(0.7, 0.5)                                         # half our logit, half the market's
    assert p == pytest.approx(1 / (1 + np.exp(-0.5 * np.log(0.7 / 0.3))))


def test_fit_recovers_known_weights():
    rng = np.random.default_rng(0)
    n = 20000
    truth = rng.uniform(0.2, 0.8, n)
    lt = np.log(truth / (1 - truth))
    ours = 1 / (1 + np.exp(-(lt + rng.normal(0, 0.6, n))))                # noisy view of the truth
    mkt = 1 / (1 + np.exp(-(lt + rng.normal(0, 0.3, n))))                 # sharper view
    won = (rng.uniform(size=n) < truth).astype(float)
    w = market.fit_combination(ours, mkt, won)
    assert w['fitted'] and w['w_market'] > w['w_ours'] > 0               # the sharper source earns more weight


def test_kelly_and_correlated_shrink():
    assert staking.kelly([0.6], [1.87])[0] == pytest.approx((0.6 * 1.87 - 1) / 0.87)
    assert staking.kelly([0.5], [1.87])[0] == 0.0
    bets = pd.DataFrame([dict(game='g', team='T', player='A', market='pts', side='over', p=0.6, price=1.9),
                         dict(game='g', team='T', player='A', market='pra', side='over', p=0.6, price=1.9),
                         dict(game='h', team='U', player='B', market='reb', side='over', p=0.6, price=1.9)])
    s = staking.stakes(bets, bank=10000)
    assert s.shrink[0] == pytest.approx(1 / np.sqrt(1 + 0.915))         # points and PRA on one player
    assert s.shrink[2] == pytest.approx(1.0)                              # a bet alone in its game
    assert (s.stake <= 0.02 * 10000).all()
