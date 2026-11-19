"""The crossing inputs: dogs that get to the first point ahead of a runner and come across it."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "research", "greyhound"))
import topaz_cross as C   # noqa: E402


def race():
    # Warragul race 3's shape: box 6 is usually ahead of box 5 at the first point and runs the same line; box 7 is
    # quicker still but runs a metre wider; box 3 is ahead of 5 and runs 0.8 m wider; box 2 has no line; box 4 has no
    # first-point history. Rows deliberately out of box order.
    return pd.DataFrame({
        "race_id": [1, 1, 1, 1, 1, 1, 2],
        "box": [6, 2, 5, 7, 3, 4, 1],
        "style_early": [0.20, 0.40, 0.30, 0.10, 0.25, np.nan, 0.5],
        "style_led_rate": [0.40, 0.0, 0.33, 0.22, 0.10, 0.5, 0.1],
        "line_any": [0.0, np.nan, 0.0, 1.0, 0.8, 0.0, 0.0],
    }, index=[10, 11, 12, 13, 14, 15, 16])


def test_box_5_is_crossed_by_box_6_and_not_by_the_wide_box_7():
    m = race().pipe(C.cross_map)
    r = m.loc[12]
    assert r.cx_out_first == 1 and r.cx_out_led == 1          # box 6 only: box 7 runs 1.0 m wider (> 0.5)
    assert r.cx_in_first == 1                                  # box 3: ahead (0.25 < 0.30) and 0.8 m wider
    assert np.isclose(r.cx_out_pressure, 0.10)                 # (0.30 - 0.20) / 1 box
    assert np.isclose(r.cx_nb_out_first, 0.10)                 # 0.30 - 0.20
    assert np.isclose(r.cx_nb_out_led, 0.07)                   # 0.40 - 0.33


def test_box_6_has_only_the_wide_runner_outside():
    r = race().pipe(C.cross_map).loc[10]
    assert r.cx_out_first == 0 and r.cx_out_led == 0 and r.cx_in_first == 0 and r.cx_out_pressure == 0
    assert np.isclose(r.cx_nb_out_first, 0.10) and np.isclose(r.cx_nb_out_led, -0.18)


def test_an_unknown_line_is_read_as_level():
    # box 2 (no line): every dog outside that is ahead of it at the first point counts (3, 5, 6, 7; box 4 has no
    # place history), and by the share led every dog outside that has led more often (3, 4, 5, 6, 7)
    r = race().pipe(C.cross_map).loc[11]
    assert r.cx_out_first == 4 and r.cx_out_led == 5
    # (0.40 - 0.25) / 1 + (0.40 - 0.30) / 3 + (0.40 - 0.20) / 4 + (0.40 - 0.10) / 5
    assert np.isclose(r.cx_out_pressure, 0.15 + 0.10 / 3 + 0.05 + 0.06)
    assert np.isclose(r.cx_nb_out_first, 0.15) and np.isclose(r.cx_nb_out_led, 0.10)


def test_the_outermost_dog_and_a_dog_with_no_history():
    m = race().pipe(C.cross_map)
    assert m.loc[13].cx_out_first == 0 and np.isnan(m.loc[13].cx_nb_out_first)
    assert m.loc[15].isna().all()
    assert m.loc[16].cx_out_first == 0                         # alone in its race
    assert list(m.index) == [10, 11, 12, 13, 14, 15, 16]
