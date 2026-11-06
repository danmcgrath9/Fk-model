"""research/greyhound/topaz_round29.py: returns, the band price, the score and the segments, by hand."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round29 as R29  # noqa: E402


def test_returns_by_hand():
    assert np.allclose(R29.returns("back at BSP", [1, 0], [5.0, 5.0], 0.08), [3.68, -1.0])
    assert np.allclose(R29.returns("lay at BSP", [1, 0], [5.0, 5.0], 0.08), [-4.0, 0.92])
    assert np.allclose(R29.returns("back at GRV's SP", [1, 0], [5.0, 5.0], 0.08), [4.0, -1.0])


def test_band_price_uses_the_last_preplay_price_and_falls_back_to_bsp():
    t = pd.DataFrame({R29.LTP: [6.0, np.nan], "bsp": [5.0, 7.0], "start_price": [4.5, 8.0]})
    assert list(R29.band_price(t, "back at BSP")) == [6.0, 7.0]
    assert list(R29.band_price(t, "back at GRV's SP")) == [4.5, 8.0]
    assert list(R29.paid_price(t, "lay at BSP")) == [5.0, 7.0]


def test_stats_z_is_the_mean_over_its_standard_error():
    r = np.array([1.0, -1.0, 1.0, 1.0])
    n, mean, z = R29.stats(r)
    assert n == 4 and mean == 0.5 and abs(z - 0.5 / (r.std(ddof=1) / 2)) < 1e-12
    assert R29.stats(np.array([1.0]))[2] == 0.0


def test_segments_late_move_and_market_depth():
    t = pd.DataFrame({"race_id": [1, 1, 2, 2], "box": [1, 8, 2, 7], "track": ["SAN"] * 4, "distance": [515] * 4,
                      "field": [2, 2, 2, 2], "runs": [0, 5, 2, 12], "days_since": [np.nan, 3, 10, 40],
                      R29.LTP: [4.0, 10.0, 5.0, 5.0], R29.WAP: [5.0, 8.0, 5.0, 5.2], R29.PVOL: [10, 20, 500, 600]})
    s = R29.segments(t, vol_cuts=(100, 1000))
    assert list(s["box 8"]) == [False, True, False, False]
    assert list(s["debut"]) == [True, False, False, False]
    assert list(s["last start up to 4 days ago"]) == [False, True, False, False]
    # 4 / 5 = 0.8 is a firm of 15%+; 10 / 8 = 1.25 a drift; 5 / 5.2 is steady
    assert list(s["firmed late (last 15%+ under the average)"]) == [True, False, False, False]
    assert list(s["drifted late (last 15%+ over the average)"]) == [False, True, False, False]
    assert list(s["steady late"]) == [False, False, True, True]
    # race 1 traded 30 (thin), race 2 traded 1,100 (deep)
    assert list(s["thin market"]) == [True, True, False, False] and list(s["deep market"]) == [False, False, True, True]


def test_every_period_gets_the_same_track_segments():
    t = pd.DataFrame({"race_id": [1], "box": [1], "track": ["SAN"], "distance": [515], "field": [1], "runs": [3],
                      "days_since": [7]})
    s = R29.segments(t, tracks=["CRN", "SAN"])
    assert list(s["track CRN"]) == [False] and list(s["track SAN"]) == [True]
