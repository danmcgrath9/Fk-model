"""Benter's blend on made-up markets: does the fit recover how good each source is, and does the blend beat both?"""
import numpy as np

from bbl.model import benter


def test_devig_sums_to_one_and_power_shades_longshots():
    prices = [1.50, 2.70]                        # 66.7% + 37.0% = 103.7%: a 3.7% margin
    for m in ('proportional', 'power'):
        p = benter.devig(prices, m)
        assert abs(p.sum() - 1) < 1e-9
    prop, power = benter.devig(prices, 'proportional'), benter.devig(prices, 'power')
    assert power[1] < prop[1]                    # the power method takes more off the longshot


def synth(n, seed, model_noise, market_noise):
    """True two-way chances; the model and the market each see them through their own noise."""
    rng = np.random.default_rng(seed)
    ev = []
    for _ in range(n):
        t = rng.normal(0, 0.8)
        truth = 1 / (1 + np.exp(-t))
        y = int(rng.random() > truth)            # outcome 0 = the side with chance `truth`
        pm = 1 / (1 + np.exp(-(t + rng.normal(0, model_noise))))
        pk = 1 / (1 + np.exp(-(t + rng.normal(0, market_noise))))
        ev.append((np.array([pm, 1 - pm]), np.array([pk, 1 - pk]), y))
    return ev


def test_blend_beats_both_when_each_knows_something():
    train, test = synth(4000, 1, 0.6, 0.6), synth(4000, 2, 0.6, 0.6)
    a, b, _ = benter.fit(train)
    assert 0.3 < a < 0.9 and 0.3 < b < 0.9      # equally informative: similar weights
    ll_blend = benter.log_loss(test, a, b)
    assert ll_blend < benter.log_loss(test, which='model') and ll_blend < benter.log_loss(test, which='market')


def test_a_model_that_adds_nothing_gets_no_weight():
    rng = np.random.default_rng(5)
    ev = [(np.array([p, 1 - p]), pk, y) for (pm, pk, y), p in
          zip(synth(4000, 3, 0.6, 0.2), rng.uniform(0.2, 0.8, 4000))]          # model = pure noise
    a, b, _ = benter.fit(ev)
    assert abs(a) < 0.1 and b > 0.8


def test_kelly():
    assert benter.kelly(0.5, 1.90) == 0.0                 # no edge at 1.90 on a coin flip
    assert abs(benter.kelly(0.55, 2.00, fraction=1.0) - 0.10) < 1e-9   # (0.55*1 - 0.45)/1 = 0.10
