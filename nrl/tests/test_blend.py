"""The stage-2 blend recovers known weights from synthetic data, and beats either price alone when both carry
information (no real odds needed)."""
import numpy as np

from nrl.model.blend import Blend, devig_two_way, logit


def test_blend_recovers_weights_and_beats_both():
    rng = np.random.default_rng(0)
    n = 40000
    truth = rng.normal(0, 1.2, n)
    ours = truth + rng.normal(0, 0.8, n)          # each price sees the truth with its own noise
    market = truth + rng.normal(0, 0.6, n)
    y = rng.random(n) < 1 / (1 + np.exp(-truth))
    p_o, p_m = 1 / (1 + np.exp(-ours)), 1 / (1 + np.exp(-market))
    b = Blend().fit(p_o[:30000], p_m[:30000], y[:30000])
    assert b.b > b.a > 0                          # the less noisy price gets more weight
    ll = lambda p: -np.mean(np.where(y[30000:], np.log(p), np.log(1 - p)))
    assert ll(b.predict(p_o[30000:], p_m[30000:])) < min(ll(p_o[30000:]), ll(p_m[30000:]))


def test_devig_removes_the_margin():
    p = devig_two_way(1.80, 2.00)
    assert abs(p - (1 / 1.8) / (1 / 1.8 + 1 / 2.0)) < 1e-12
    assert abs(devig_two_way(1.90, 1.90) - 0.5) < 1e-12
    assert np.isfinite(logit(0.0)) and np.isfinite(logit(1.0))
