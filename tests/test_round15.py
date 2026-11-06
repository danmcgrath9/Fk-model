"""research/greyhound/topaz_round15.py: Harville's place chances and the place market's, by hand."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")
pytest.importorskip("scipy")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round15 as R15  # noqa: E402


def test_harville_two_places_by_hand():
    # win chances 0.5 / 0.3 / 0.2, two places paid.
    # A: wins 0.5; second after B 0.3 x 0.5/0.7 = 0.2143, after C 0.2 x 0.5/0.8 = 0.125; total 0.8393
    # B: 0.3 + 0.5 x 0.3/0.5 + 0.2 x 0.3/0.8 = 0.3 + 0.3 + 0.075 = 0.675
    # C: 0.2 + 0.5 x 0.2/0.5 + 0.3 x 0.2/0.7 = 0.2 + 0.2 + 0.0857 = 0.4857
    out = R15.harville_place([0.5, 0.3, 0.2], 2)
    assert np.allclose(out, [0.5 + 0.3 * 5 / 7 + 0.125, 0.675, 0.4 + 0.06 / 0.7])
    assert abs(out.sum() - 2) < 1e-12


def test_harville_edges():
    p = np.array([0.4, 0.3, 0.2, 0.1])
    assert np.allclose(R15.harville_place(p, 1), p)          # one place is the win
    assert np.allclose(R15.harville_place(p, 4), 1)          # every dog places when all of them are paid
    assert abs(R15.harville_place(p, 3).sum() - 3) < 1e-12
    assert np.allclose(R15.harville_place(p[:2] / p[:2].sum(), 3), 1)   # k above the field is the field


def test_place_columns_keep_full_markets_with_two_or_three_places():
    t = pd.DataFrame({
        "race_id": [1, 1, 1, 2, 2, 2, 3, 3],
        "p": [0.5, 0.3, 0.2, 0.6, 0.3, 0.1, 0.7, 0.3],
        "placed": [1, 1, 0, 1, 1, 0, 1, 0],
        "PLACE_BSP": [1.5, 2.0, 4.0, 1.3, np.nan, 5.0, 1.2, 3.0]})
    out = R15.place_columns(t, "p")
    assert set(out.race_id) == {1}                           # race 2 has a runner with no place BSP; race 3 paid one place
    assert list(out.k) == [2, 2, 2]
    assert np.allclose(out.p_place, R15.harville_place([0.5, 0.3, 0.2], 2))
    # the market: 1/1.5 + 1/2 + 1/4 = 1.4167, rescaled to add to 2
    inv = np.array([1 / 1.5, 0.5, 0.25])
    assert np.allclose(out.q_place, inv / inv.sum() * 2) and abs(out.q_place.sum() - 2) < 1e-12


def test_blend_with_weight_on_ours_alone_returns_ours():
    t = pd.DataFrame({"p_place": [0.2, 0.5, 0.9], "q_place": [0.3, 0.4, 0.8]})
    assert np.allclose(R15.apply_blend(t, [1.0, 0.0, 0.0]), t.p_place, atol=1e-9)
    assert np.allclose(R15.apply_blend(t, [0.0, 1.0, 0.0]), t.q_place, atol=1e-9)


def test_binary_log_loss_by_hand():
    # -(ln 0.8 + ln 0.75) / 2 = (0.2231 + 0.2877) / 2 = 0.2554
    assert abs(R15.bll([0.8, 0.25], [1, 0]) - (-(np.log(0.8) + np.log(0.75)) / 2)) < 1e-12
