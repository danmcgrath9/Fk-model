"""research/greyhound/topaz_round13.py: the drift and firm measures and their bands, by hand."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round13 as R13  # noqa: E402


def test_drift_is_bsp_over_the_shortest_price_and_firm_the_longest_over_bsp():
    df = pd.DataFrame({"bsp": [19.0, 4.0, 5.0, 6.0], R13.MIN: [3.2, 4.0, np.nan, 0.0], R13.MAX: [19.0, 12.0, 6.0, 7.0]})
    out = R13.drift_columns(df)
    # So Hot Swifty's shape: $3.20 shortest, $19 at the off: drifted 5.9x, never longer than the BSP
    assert abs(out.drift[0] - 19 / 3.2) < 1e-12 and out.firm[0] == 1.0
    assert out.drift[1] == 1.0 and out.firm[1] == 3.0              # never shorter than BSP; once three times it
    assert np.isnan(out.drift[2]) and np.isnan(out.drift[3])       # nothing matched (or a zero) is no drift, not 1x


def test_bands_cover_every_drift_and_leave_nan_alone():
    b = R13.band(pd.Series([1.0, 1.1, 1.29, 1.6, 2.2, 5.9, np.nan]))
    assert list(b[:6]) == ["under 1.1x", "1.1-1.3x", "1.1-1.3x", "1.6-2.2x", "2.2-3.5x", "3.5x+"]
    assert pd.isna(b[6])
