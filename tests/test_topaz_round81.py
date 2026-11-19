"""Round 81's band sheet: orders on price bands with a ceiling and their own stake."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "research", "greyhound"))
import topaz_round81 as S   # noqa: E402

GRID = np.array([2.0, 3.0, 4.0, 5.0])


def test_the_rule_at_each_ladder_price():
    # chance 0.30 at every price: 0.30 - 1/2 < 0; 0.30 - 1/3 < 0; 0.30 - 1/4 = 0.05; 0.30 - 1/5 = 0.10
    ok = S.ladder_rule(np.full((1, 4), 0.30), GRID, 0.02)
    assert ok.tolist() == [[False, False, True, True]]
    # at 6 points the $4 end (5 points) fails
    assert S.ladder_rule(np.full((1, 4), 0.30), GRID, 0.06).tolist() == [[False, False, False, True]]
    # a fair price of $20 is never a bet
    assert not S.ladder_rule(np.full((1, 4), 0.05), GRID, 0.0).any()


def test_a_band_needs_the_rule_at_both_ends_and_stakes_the_smaller_kelly():
    pg = np.array([[0.30, 0.30, 0.30, 0.30]])
    valid, ks = S.band_orders(pg, GRID, 0.02, 1.0)
    # bands $2-3, $3-4, $4-5: only $4-5 has the rule at both ends
    assert valid.tolist() == [[False, False, True]]
    # quarter Kelly at $4: 0.25 x (4 x 0.30 - 1) / 3 = 0.016667; at $5: 0.25 x (5 x 0.30 - 1) / 4 = 0.03125
    assert np.allclose(ks, [[0.0, 0.0, 0.25 * 0.2 / 3]])


def test_the_kelly_stake_is_on_test_98s_scale():
    valid, ks = S.band_orders(np.array([[0.30, 0.30, 0.30, 0.30]]), GRID, 0.02, 0.5)
    assert np.isclose(ks[0, 2], 2 * 0.25 * 0.2 / 3)


def test_each_price_falls_in_one_band():
    j = S.band_of(np.array([1.5, 2.0, 2.99, 3.0, 4.5, 5.0, 7.0, np.nan]), GRID)
    assert j.tolist() == [-1, 0, 0, 1, 2, -1, -1, -1]


def test_an_order_fires_only_in_its_own_band():
    valid = np.array([[False, False, True], [False, False, True], [True, True, False]])
    ks = np.where(valid, 0.5, 0.0)
    hit, u = S.fire(valid, ks, np.array([2, 1, -1]))
    assert hit.tolist() == [True, False, False]
    assert u.tolist() == [0.5, 0.0, 0.0]


def test_neighbouring_bands_are_one_flat_order():
    valid = np.array([[True, True, False, True], [False, False, False, False], [False, True, True, True]])
    assert S.orders_flat(valid).tolist() == [2, 0, 1]


def test_the_rule_at_tab_s_actual_price():
    # 0.30 at $4: 5 points over (a bet at 2 and 4 points, not at 6); at $3: below 1 / price
    ok = [S.rule_at(np.array([0.30, 0.30]), np.array([4.0, 3.0]), dm).tolist() for dm in (0.02, 0.04, 0.06)]
    assert ok == [[True, False], [True, False], [False, False]]
