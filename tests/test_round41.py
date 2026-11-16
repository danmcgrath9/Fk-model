"""Round 41: a correction fitted on top of the held blend (topaz_round41)."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round41 as R41  # noqa: E402
import topaz_v1 as V1        # noqa: E402


def races(n, k, rng, signal=1.0, start="2023-05-01", days=900):
    """n races of k runners: a feature f that shifts the true score by `signal`, an offset that knows nothing of it."""
    race = np.repeat(np.arange(n), k)
    f = rng.integers(0, 2, n * k).astype(float)
    off = np.zeros(n * k)
    p = V1.race_softmax(off + signal * f, race)
    won = np.zeros(n * k)
    cum = pd.Series(p).groupby(race).cumsum().values
    u = np.repeat(rng.random(n), k)
    hit = cum >= u
    first = hit & (pd.Series(hit.astype(int)).groupby(race).cumsum().values == 1)
    won[first] = 1
    date = pd.to_datetime(start) + pd.to_timedelta(np.repeat(np.sort(rng.integers(0, days, n)), k), unit="D")
    return pd.DataFrame({"race_id": race, "date": date, "won": won, "off": off}), pd.DataFrame({"f": f})


def test_groups_of_needs_each_race_together():
    assert list(R41.groups_of([3, 3, 1, 1, 1, 7])) == [2, 3, 1]
    with pytest.raises(ValueError):
        R41.groups_of([3, 1, 3])


def test_with_no_trees_the_gradient_is_the_offset_softmax_less_the_label():
    off = np.log(np.array([0.5, 0.3, 0.2, 0.6, 0.4]))
    y = np.array([0, 1, 0, 1, 0.0])

    class D:
        def get_label(self):
            return y
    g, h = R41.offset_obj(off, np.array([3, 2]))(np.zeros(5), D())
    assert np.allclose(g, [0.5, -0.7, 0.2, -0.4, 0.4])
    assert np.allclose(h, [0.25, 0.21, 0.16, 0.24, 0.24])


def test_no_rounds_is_the_offset_itself():
    off = np.log(np.array([0.5, 0.3, 0.2]))
    assert R41.fit(pd.DataFrame({"f": [1.0, 0, 0]}), np.array([1, 0, 0.0]), off, np.zeros(3), 0) is None
    assert np.allclose(R41.score(None, None, off, np.zeros(3)), [0.5, 0.3, 0.2])


def test_the_correction_learns_what_the_offset_misses_and_stops_when_there_is_nothing():
    rng = np.random.default_rng(1)
    R, X = races(6000, 6, rng, signal=1.0)
    half = R.race_id.values < 4000
    old_max = R41.MAX_ROUNDS
    R41.MAX_ROUNDS = 300
    try:
        k, l0, lk = R41.choose_rounds((X[half], R.won.values[half], R.off.values[half], R.race_id.values[half]),
                                      (X[~half], R.won.values[~half], R.off.values[~half], R.race_id.values[~half]))
        assert k > 0 and lk < l0
        bst = R41.fit(X[half], R.won.values[half], R.off.values[half], R.race_id.values[half], k)
        p = R41.score(bst, X[~half], R.off.values[~half], R.race_id.values[~half])
        f = X.f.values[~half]
        assert p[f == 1].mean() > 1.5 * p[f == 0].mean()       # the truth is e^1 = 2.7 times, at f's mix
        Rn, Xn = races(6000, 6, np.random.default_rng(2), signal=0.0)
        half = Rn.race_id.values < 4000
        k0, b0, l0n = R41.choose_rounds(
            (Xn[half], Rn.won.values[half], Rn.off.values[half], Rn.race_id.values[half]),
            (Xn[~half], Rn.won.values[~half], Rn.off.values[~half], Rn.race_id.values[~half]))
        assert l0n <= b0 and l0n > b0 - 0.003                  # nothing to learn: at most noise
    finally:
        R41.MAX_ROUNDS = old_max


def test_the_walk_prices_nothing_before_FROM_and_only_from_races_before_each_month():
    rng = np.random.default_rng(3)
    R, X = races(4000, 5, rng, signal=0.8, start="2023-05-01", days=800)
    old = R41.FROM, R41.MAX_ROUNDS
    R41.FROM, R41.MAX_ROUNDS = "2024-11", 100
    try:
        p, log, share = R41.walk_correction(R, X, R.won.values, np.ones(len(R), bool))
    finally:
        R41.FROM, R41.MAX_ROUNDS = old
    before = (R.date < "2024-11-01").values
    assert np.isnan(p[before]).all() and not np.isnan(p[~before]).any()
    assert np.allclose(pd.Series(p[~before]).groupby(R.race_id.values[~before]).sum(), 1)
    assert log[0].startswith("2024-11:") and log[1].startswith("2025-01:")   # every two months
    assert len(share) == 0 or abs(share.sum() - 1) < 1e-9


def test_the_ran_field_carries_the_blend_over_the_runners_that_ran():
    x = pd.DataFrame({"race_id": [1, 1, 1, 2, 2], "date": pd.to_datetime(["2025-01-01"] * 3 + ["2025-01-02"] * 2),
                      "price": [2.0, 4.0, 5.0, 1.8, 2.2], "p_book": [0.5, 0.25, 0.25, 0.55, 0.45],
                      "p_x_bet": [0.4, 0.35, 0.25, 0.6, 0.4], "pb6": [0.45, 0.3, 0.25, 0.58, 0.42],
                      "is_ran": [True, True, False, True, True], "won": [1, 0, 0, 0, 1],
                      "s_later": [0.25, 0.25, 0.25, 0.0, 0.0], "_row": [0, 1, np.nan, 2, 3]})
    X = pd.DataFrame({"f": [10.0, 11, 12, 13]})
    R, XR = R41.ran_field(x, X)
    assert list(R.race_id) == [1, 1, 2, 2] and list(XR.f) == [10, 11, 12, 13]
    assert np.allclose(R.s_ran, [0.75, 0.75, 1.0, 1.0])
    assert np.allclose(np.exp(R.off), [0.6, 0.4, 0.58, 0.42])
    assert np.allclose(np.exp(XR.lp_tab), [2 / 3, 1 / 3, 0.55, 0.45])
    assert np.allclose(XR.tab_book, [0.5 + 0.25 + 0.2, 0.95, 1 / 1.8 + 1 / 2.2, 1 / 1.8 + 1 / 2.2])
    assert list(XR.n_bet) == [3, 3, 2, 2]


def test_bsp_labels_only_races_priced_at_bsp_on_every_runner():
    R = pd.DataFrame({"race_id": [1, 1, 2, 2], "p_bsp": [0.6, 0.2, 0.5, np.nan]})
    q, full = R41.bsp_label(R)
    assert list(full) == [True, True, False, False]
    assert np.allclose(q, [0.75, 0.25, 0, 0])
