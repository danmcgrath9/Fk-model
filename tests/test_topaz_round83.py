"""Round 83's report pieces: the crossing groups, actual against expected wins, and the drift to BSP."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "research", "greyhound"))
import topaz_round83 as S   # noqa: E402


def test_the_crossing_groups():
    cx = pd.DataFrame({"cx_out_first": [0, 1, 2, np.nan], "cx_out_led": [0, 1, 1, np.nan],
                       "cx_in_first": [0, 1, 0, np.nan], "cx_out_pressure": [0, 0.1, 0.3, np.nan],
                       "cx_nb_out_first": [0.2, 0.0, 0.05, np.nan], "cx_nb_out_led": [0.1, -0.1, np.nan, np.nan]})
    g = dict(S.groups(cx))
    assert g["nothing drawn outside it is usually ahead of it and runs its line"].tolist() == [True, False, False, False]
    assert g["one dog drawn outside is usually ahead of it at the first point and runs no wider"].tolist() == \
        [False, True, False, False]
    assert g["two or more such dogs"].tolist() == [False, False, True, False]
    assert g["the dog drawn next outside has led more often"].tolist() == [True, False, False, False]
    assert g["the dog drawn next outside is a tenth of the field or more ahead at the first point"].tolist() == \
        [True, False, False, False]
    # the positive pressures are 0.1 and 0.3: their 90th percentile is 0.1 + 0.9 x 0.2 = 0.28
    assert g["the crossers' pressure, the top tenth"].tolist() == [False, False, True, False]
    assert g["a dog drawn inside is usually ahead of it and runs wider"].tolist() == [False, True, False, False]
    assert g["no first-point history"].tolist() == [False, False, False, True]


def test_actual_against_expected():
    won, m = np.array([1, 0, 0, 1.0]), np.ones(4, bool)
    p = np.full(4, 0.5)
    # 2 wins against 4 x 0.5 = 2 expected; SE sqrt(4 x 0.25) / 2 = 0.5
    assert S.ae_cells(won, m, [p, p]) == "4 | 2 | 1.000 | 1.000 | 0.500"


def test_the_drift_from_tab_to_bsp():
    # TAB 25% and BSP 20% (drifted), TAB 20% and BSP 25% (backed): the mean log ratio is 0, half drifted
    assert S.drift(np.array([0.25, 0.20]), np.array([0.20, 0.25]), np.ones(2, bool)) == "+0.0% | 50%"
    # TAB 30% against BSP 20%: the price went out by half
    assert S.drift(np.array([0.30]), np.array([0.20]), np.ones(1, bool)) == "+50.0% | 100%"
