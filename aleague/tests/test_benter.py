"""Stage two (aleague/model/benter.py) on cases with known answers."""
import numpy as np
import pytest

from aleague.model.benter import blend, devig_power, devig_shin, fit_blend, fit_by_season, stake


def test_devig_sums_to_one_and_keeps_order():
    prices = [1.80, 3.60, 4.50]   # overround 1/1.8 + 1/3.6 + 1/4.5 = 1.0556
    for f in (devig_power, devig_shin):
        p = f(prices)
        assert p.sum() == pytest.approx(1)
        assert p[0] > p[1] > p[2]
        # removing a margin lowers every implied probability
        assert all(p < 1 / np.array(prices))
    # a fair book is left alone
    assert devig_power([2.0, 2.0]) == pytest.approx([0.5, 0.5])


def test_blend_weights_recovered():
    # truth: outcomes drawn from the MARKET's probabilities; the model is noise. The fit must give the
    # market the weight and the model about none.
    rng = np.random.default_rng(0)
    n = 6000
    pk = rng.dirichlet([4, 2, 3], size=n)
    pm = rng.dirichlet([3, 3, 3], size=n)
    y = np.array([rng.choice(3, p=r) for r in pk])
    a, b = fit_blend(pm, pk, y)
    assert abs(a) < 0.1 and b == pytest.approx(1, abs=0.1)


def test_blend_finds_a_model_with_information():
    # truth is the geometric mix of the two: both should get weight near 0.5
    rng = np.random.default_rng(1)
    n = 8000
    pk = rng.dirichlet([3, 2, 3], size=n)
    pm = rng.dirichlet([3, 2, 3], size=n)
    truth = blend(pm, pk, 0.5, 0.5)
    y = np.array([rng.choice(3, p=r) for r in truth])
    a, b = fit_blend(pm, pk, y)
    assert a == pytest.approx(0.5, abs=0.12) and b == pytest.approx(0.5, abs=0.12)


def test_fit_by_season_uses_only_earlier_seasons():
    rng = np.random.default_rng(2)
    seasons = np.repeat([1, 2, 3], 400)
    pk = rng.dirichlet([3, 2, 3], size=1200)
    pm = rng.dirichlet([3, 2, 3], size=1200)
    y = np.array([rng.choice(3, p=r) for r in pk])
    p1, w1 = fit_by_season(seasons, pm, pk, y)
    assert np.isnan(p1[seasons == 1]).all() and 2 in w1 and 3 in w1
    # changing season 3's results cannot change season 3's (or 2's) blended probabilities
    y2 = y.copy(); y2[seasons == 3] = (y2[seasons == 3] + 1) % 3
    p2, _ = fit_by_season(seasons, pm, pk, y2)
    assert np.allclose(p1[seasons <= 3][400:], p2[seasons <= 3][400:])


def test_stake():
    # p 0.55 at 2.0: edge 0.10, full Kelly 0.10, quarter Kelly 0.025
    assert stake(0.55, 2.0) == pytest.approx(0.025)
    assert stake(0.51, 2.0) == 0.0   # edge 0.02 below the 0.03 threshold
