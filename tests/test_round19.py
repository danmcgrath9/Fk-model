"""research/greyhound/topaz_round19.py: the BSP-race filter and the SP-to-BSP power, by hand."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")
pytest.importorskip("scipy")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round19 as R19  # noqa: E402
import topaz_v1 as V1        # noqa: E402


def test_full_bsp_needs_every_runner():
    df = pd.DataFrame({"race_id": [1, 1, 2, 2], "p_bsp": [0.6, 0.4, 0.7, np.nan]})
    assert list(R19.full_bsp(df)) == [True, True, False, False]


def test_sp_power_recovers_the_power_that_made_bsp():
    # BSP built as GRV's SP raised to 1.3 and rescaled: the fit should find 1.3
    rng = np.random.default_rng(1)
    race = np.repeat(np.arange(300), 6)
    sp = pd.Series(rng.dirichlet(np.ones(6), 300).ravel())
    df = pd.DataFrame({"race_id": race, "p_sp": sp})
    df["p_bsp"] = V1.race_softmax(1.3 * np.log(df.p_sp.values), race)
    assert abs(R19.fit_sp_power(df) - 1.3) < 0.01
    out = R19.sp_corrected(df, 1.3)
    assert np.allclose(out, df.p_bsp) and np.allclose(pd.Series(out).groupby(race).sum(), 1)
    # 0.5 x 0.5^1.3 ... by hand for one race of two: 0.6/0.4 at power 2 is 0.36/0.16 rescaled = 0.6923 / 0.3077
    two = pd.DataFrame({"race_id": [9, 9], "p_sp": [0.6, 0.4]})
    assert np.allclose(R19.sp_corrected(two, 2.0), [0.36 / 0.52, 0.16 / 0.52])


def test_sp_power_defaults_to_one_without_enough_races():
    df = pd.DataFrame({"race_id": [1, 1], "p_sp": [0.6, 0.4], "p_bsp": [0.5, 0.5]})
    assert R19.fit_sp_power(df) == 1.0
