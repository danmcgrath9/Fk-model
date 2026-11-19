"""Round 82: the band sheet's rule and stake read at the price paid after TAB's deduction, as Test 98 reads them."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "research", "greyhound"))
import topaz_round82 as S   # noqa: E402

GRID = np.array([2.0, 3.0, 4.0, 5.0])


def test_the_price_paid_at_each_ladder_price():
    # a 20c deduction: 1 + (price - 1) x 0.8 = 1.8, 2.6, 3.4, 4.2; no deduction (and a missing one) pays the price
    pg = S.paid_at(GRID, np.array([0.2, 0.0, np.nan]))
    assert np.allclose(pg, [[1.8, 2.6, 3.4, 4.2], [2, 3, 4, 5], [2, 3, 4, 5]])


def test_the_rule_reads_the_price_paid():
    # chance 0.30 against 1 / paid: 0.30 - 1/3.4 = +0.0059; 0.30 - 1/4.2 = +0.0619; the cheaper two are below
    paid = S.paid_at(GRID, np.array([0.2]))
    assert S.ladder_rule(np.full((1, 4), 0.30), paid, 0.02).tolist() == [[False, False, False, True]]
    assert S.ladder_rule(np.full((1, 4), 0.30), paid, 0.0).tolist() == [[False, False, True, True]]
    # with no deduction it is round 81's rule: 0.30 - 1/4 = 0.05 and 0.30 - 1/5 = 0.10 clear 2 points
    none = S.paid_at(GRID, np.array([0.0]))
    assert S.ladder_rule(np.full((1, 4), 0.30), none, 0.02).tolist() == [[False, False, True, True]]


def test_a_band_stakes_the_smaller_kelly_at_the_price_paid():
    paid = S.paid_at(GRID, np.array([0.2]))
    valid, ks = S.band_orders(np.full((1, 4), 0.30), paid, 0.0, 1.0)
    assert valid.tolist() == [[False, False, True]]
    # quarter Kelly at 3.4: 0.25 x (3.4 x 0.30 - 1) / 2.4 = 0.0020833; at 4.2: 0.25 x 0.26 / 3.2 = 0.0203125
    assert np.allclose(ks, [[0.0, 0.0, 0.25 * 0.02 / 2.4]])


def test_the_ladder_is_read_back_only_onto_the_same_rows(tmp_path):
    race = np.array(["a", "a", "b"])
    pg = np.array([[0.1, 0.2], [np.nan, np.nan], [0.3, 0.4]])
    pa = np.array([0.15, np.nan, 0.35])
    res = {nm: (pg, pa) for nm, _ in S.NAMES}
    path = tmp_path / "ladder.npz"
    S.save_ladder(path, S.race_key(race), res)
    back = S.load_ladder(path, S.race_key(race), 3, 2)
    for nm, _ in S.NAMES:
        assert np.allclose(back[nm][0], pg, equal_nan=True)
        assert np.allclose(back[nm][1], pa, equal_nan=True)
    assert S.load_ladder(path, S.race_key(np.array(["a", "b", "b"])), 3, 2) is None
    assert S.load_ladder(tmp_path / "none.npz", S.race_key(race), 3, 2) is None
