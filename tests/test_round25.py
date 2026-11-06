"""research/greyhound/topaz_round25.py: the winner's gap and the bands, by hand."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round25 as R25  # noqa: E402


def test_winner_gap_by_hand():
    # race 1: BSP gave the winner 0.5, we gave 0.25: g = ln 0.5 - ln 0.25 = ln 2 = 0.6931; race 2: we were right, 0.4 vs 0.2
    t = pd.DataFrame({"race_id": [1, 1, 2, 2], "won": [1, 0, 0, 1], "p_bsp": [0.5, 0.5, 0.8, 0.2], "p_x": [0.25, 0.75, 0.6, 0.4]})
    w = R25.winner_gaps(t, "p_x")
    assert list(w.race_id) == [1, 2]
    assert np.allclose(w.g, [np.log(2), np.log(0.5)])


def test_cut_bands():
    b = R25.cut(pd.Series([0.3, 0.6, 1.0, 1.5, 3.0]), R25.RATIO_BANDS, R25.RATIO_NAMES)
    assert list(b) == R25.RATIO_NAMES
