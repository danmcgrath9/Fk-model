"""research/greyhound/topaz_round28.py: the box groups, our view and the lay mask, by hand."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round28 as R28  # noqa: E402


def _t():
    # box 8 weak here (0.7), box 8 strong (1.2), box 8 middling (1.0), box 8 unknown, box 1 weak, box 4
    return pd.DataFrame({"box": [8, 8, 8, 8, 1, 4], "box_ratio": [0.7, 1.2, 1.0, np.nan, 0.6, 1.0],
                         "bsp": [10.0, 3.0, 20.0, 50.0, 6.0, 5.0], "p_x": [0.05, 0.5, 0.05, 0.02, 0.2, 0.2],
                         "runs": [5, 5, 5, 5, 0, 5]})


def test_groups_split_box_8_by_how_it_does_here():
    g = R28.groups(_t())
    assert list(g["box 8, anywhere"]) == [True, True, True, True, False, False]
    assert list(g["box 8, weak here (0.8 or under)"]) == [True, False, False, False, False, False]
    assert list(g["box 8, middling here"]) == [False, False, True, False, False, False]
    assert list(g["box 8, strong here (1.1 or over)"]) == [False, True, False, False, False, False]
    assert list(g["box 1, weak here (0.8 or under)"]) == [False, False, False, False, True, False]


def test_views_and_the_lay_mask():
    t = _t()
    v = R28.views(t)
    # BSP $10 against ours $20: the market likes it more (10 <= 20 / 1.2); BSP $3 against ours $2: it likes it less
    assert v["market likes it more (BSP <= ours / 1.2)"][0] and v["market likes it less (BSP >= 1.3x ours)"][1]
    g = R28.groups(t)["box 8, anywhere"]
    assert list(R28.lay_mask(t, g, v["any view"], 8, 15)) == [True, False, False, False, False, False]
    # a first starter is never laid
    assert not R28.lay_mask(t, R28.groups(t)["box 1, anywhere"], v["any view"], 4, 8)[4]
