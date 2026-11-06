"""research/greyhound/topaz_round27.py: the lay mask and the break-even A/E, by hand."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round27 as R27  # noqa: E402


def test_breakeven_ae_by_hand():
    # a $20 lay at 8%: it breaks even when the dog's chance is 0.92 / 19.92 = 4.618%, against BSP's 5%: A/E 0.9237
    assert abs(R27.breakeven_ae([20.0], 0.08) - 0.92 / 19.92 / 0.05) < 1e-12
    # with no commission a lay at BSP breaks even when BSP is right
    assert abs(R27.breakeven_ae([5.0, 20.0, 50.0], 0.0) - 1.0) < 1e-12


def test_lay_mask_needs_the_band_the_ratio_and_a_previous_start():
    # ours $10 (0.1): BSP $25 is 2.5x ours; BSP $18 is 1.8x; the third is a first starter; the fourth is outside the band
    t = pd.DataFrame({"bsp": [25.0, 18.0, 25.0, 50.0], "p_x": [0.1, 0.1, 0.1, 0.1], "runs": [5, 5, 0, 5]})
    every = np.ones(4, bool)
    assert list(R27.lay_mask(t, every, 15, 40, 2.0)) == [True, False, False, False]
    assert list(R27.lay_mask(t, every, 15, 40, 1.6)) == [True, True, False, False]


def test_row_returns_and_ae():
    # four $20 lays, one winner: 3 x 0.92 - 19 = -16.24 over 4 lays; A/E = 1 / (4 x 0.05) = 5
    t = pd.DataFrame({"won": [1, 0, 0, 0], "bsp": [20.0] * 4, "date": pd.to_datetime(["2026-01-01"] * 4)})
    r = R27.row(t, np.ones(4, bool), np.ones(4, bool), 0.08)
    assert r["all"][0] == 4 and abs(r["all"][1] - (-16.24 / 4)) < 1e-9 and abs(r["all"][2] - 5.0) < 1e-9
    assert r["2nd"][0] == 0 and r["wins"] == 1
