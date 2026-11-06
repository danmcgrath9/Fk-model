"""research/greyhound/topaz_round16.py: the place book and the flat ROI at place BSP, by hand."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round16 as R16  # noqa: E402


def frame():
    # race 1: three runners plus a scratching (no win BSP), two places paid; place BSPs 1.5 / 2.5 / 5
    # race 2: one runner has no place BSP; race 3: one place paid
    return pd.DataFrame({
        "WIN_MARKET_ID": [1, 1, 1, 1, 2, 2, 3, 3],
        "WIN_BSP": [2.0, 4.0, 5.0, np.nan, 2.0, 3.0, 1.5, 4.0],
        "PLACE_BSP": [1.5, 2.5, 5.0, np.nan, 1.2, np.nan, 1.1, 2.0],
        "placed": [1, 1, 0, 0, 1, 1, 1, 0],
        "PLACE_LAST_PRICE_TAKEN": [1.4, 2.6, 6.0, np.nan, 1.2, 1.5, 1.1, 2.0],
        "PLACE_WEIGHTED_AVERAGE_PRICE_TAKEN": [1.45, np.nan, 5.5, np.nan, 1.2, 1.5, 1.1, 2.0]})


def test_place_book_by_hand():
    t = R16.races(frame())
    assert set(t.WIN_MARKET_ID) == {1} and len(t) == 3           # the scratching is dropped, races 2 and 3 are not kept
    # (1/1.5 + 1/2.5 + 1/5) / 2 = (0.6667 + 0.4 + 0.2) / 2 = 0.6333: under-round
    assert np.allclose(t.book_bsp, (1 / 1.5 + 0.4 + 0.2) / 2)
    assert np.allclose(t.win_book, 0.5 + 0.25 + 0.2)              # 0.95
    assert np.allclose(t.book_PLACE_LAST_PRICE_TAKEN, (1 / 1.4 + 1 / 2.6 + 1 / 6) / 2)
    assert t.book_PLACE_WEIGHTED_AVERAGE_PRICE_TAKEN.isna().all()  # one runner never traded: no book


def test_flat_roi_and_chance():
    # $1.50 placed pays 0.5 x 0.92 = 0.46, $2.50 placed pays 1.5 x 0.92 = 1.38, $5 lost costs 1: mean 0.84 / 3 = 0.28
    t = R16.races(frame())
    assert abs(R16.flat_roi(t.placed, t.PLACE_BSP) - (0.46 + 1.38 - 1) / 3) < 1e-12
    p = R16.chance(t, "PLACE_BSP")
    assert abs(p.sum() - 2) < 1e-12 and np.allclose(p, np.array([1 / 1.5, 0.4, 0.2]) / (1 / 1.5 + 0.6) * 2)


def test_bands():
    b = R16.band(pd.Series([0.5, 0.77, 0.9, 1.0, 1.2, np.nan]))
    assert list(b[:5]) == ["under 0.77", "0.77-0.85", "0.85-0.95", "0.95-1.05", "1.05 and over"] and pd.isna(b[5])
