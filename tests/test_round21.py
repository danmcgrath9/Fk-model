"""research/greyhound/topaz_round21.py: the horse book's rules, by hand."""
import os
import sys

import numpy as np
import pytest

pytest.importorskip("lightgbm")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round21 as R21  # noqa: E402


def test_kl_by_hand():
    # one race: market 0.5 / 0.5, ours 0.75 / 0.25: 0.5 ln(0.5/0.75) + 0.5 ln(0.5/0.25) = -0.2027 + 0.3466 = 0.1438
    kl = R21.kl_from([0.5, 0.5], [0.75, 0.25], [1, 1])
    assert abs(kl - (0.5 * np.log(0.5 / 0.75) + 0.5 * np.log(2))) < 1e-12
    assert R21.kl_from([0.5, 0.5], [0.5, 0.5], [1, 1]) == 0


def test_lay_and_back_returns():
    assert list(R21.lay_returns([0, 1], [20.0, 20.0])) == [0.92, -19.0]
    assert np.allclose(R21.back_returns([1, 0], [5.0, 5.0], 0.08), [3.68, -1.0])


def test_horse_units_by_hand():
    # p 0.25 at $6: sqrt(1.5) = 1.2247, k = 0.2247 / 5 = 0.04495, units = 125 x 0.04495 x 5/8 = 3.51
    k = (np.sqrt(1.5) - 1) / 5
    assert np.allclose(R21.horse_units([0.25], [6.0]), [125 * k * 5 / 8])
    # p 0.25 at $10 (2.5x our $4, and we are under $8): sqrt(2.5) = 1.5811, k = 0.06457, 5.04 units doubled, capped 10
    assert np.allclose(R21.horse_units([0.25], [10.0]), [10.0])
    assert R21.horse_units([0.25], [3.0])[0] == 0              # no edge, no stake


def test_order_sheet_edges_and_limits():
    # blended chance x price: 0.31 x $4 = 1.24 passes 1.2; 0.29 x $3.90 = 1.131 fails 1.15; 0.30 x $3.90 = 1.17 passes
    p_ours = np.array([0.25, 0.25, 0.25, 0.25, 0.5, 0.25])
    p_blend = np.array([0.31, 0.29, 0.30, 0.31, 0.6, 0.31])
    price = np.array([4.0, 3.9, 3.9, 13.0, 2.5, 4.0])
    first = np.array([False, False, False, False, False, True])
    out = R21.order_sheet(p_ours, p_blend, price, first)
    # row 4: $13 is over 3x our $4; row 5: our price $2.00 is fine, 0.6 x 2.5 = 1.5 passes; row 6: a first starter
    assert list(out) == [True, False, True, False, True, False]
    assert not R21.order_sheet([0.7], [0.8], [2.0], [False])[0]   # our price $1.43 is under $1.60
