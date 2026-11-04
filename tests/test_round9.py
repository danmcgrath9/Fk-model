"""research/greyhound/topaz_round9.py: the gallops value rule's selection and Kelly units on hand-made numbers."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round9 as R9  # noqa: E402


def test_ratio_band_and_kelly_units():
    df = pd.DataFrame({"race_id": [1, 1, 1, 1], "date": pd.Timestamp("2025-01-01"), "won": [1, 0, 0, 0]})
    p_blend = np.array([0.25, 0.25, 0.60, 0.05])      # our prices $4, $4, $1.67, $20
    p_mkt = np.array([0.15, 0.22, 0.55, 0.05])
    price = np.array([6.0, 4.8, 2.4, 30.0])            # 1.5x, 1.2x, 1.44x, 1.5x ours
    m, o, u = R9.horse_bets(df, p_blend, p_mkt, price, 0.0, 1.3, (2.0, 15.0))
    # dog 1: 1.5x and $4 inside the band: pk = 0.2, Kelly f = (0.2*6 - 1)/5 = 0.04 -> 3 units
    # dog 2: only 1.2x; dog 3: our price $1.67 under $2; dog 4: $20 over $15
    assert m.tolist() == [True, False, False, False] and abs(u[0] - 3.0) < 1e-9
    m2, _, u2 = R9.horse_bets(df, p_blend, p_mkt, price, 0.0, 1.2, (1.01, 1000))
    # at 1.2x and any price all four qualify; dog 4: pk = 0.05, f = (0.05*30 - 1)/29 -> 75f = 1.293 units
    assert m2.tolist() == [True, True, True, True] and abs(u2[3] - 75 * 0.5 / 29) < 1e-9 and u2[2] == 4.0
    r = R9.summary(df, m, o, u, price)
    assert r["n"] == 1 and r["w"] == 1 and abs(r["kunits"] - 15.0) < 1e-9 and abs(r["flat"] - 5.0) < 1e-9
