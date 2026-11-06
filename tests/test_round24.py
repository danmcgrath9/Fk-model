"""research/greyhound/topaz_round24.py: the returns and the rule masks, by hand."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round24 as R24  # noqa: E402


def test_returns_by_hand():
    # a $5 back that wins pays 4 x 0.92 = 3.68; a $5 lay that loses (the dog wins) costs 4; a lay that wins keeps 0.92
    assert np.allclose(R24.returns("back", [1, 0], [5.0, 5.0], 0.08), [3.68, -1.0])
    assert np.allclose(R24.returns("lay", [1, 0], [5.0, 5.0], 0.08), [-4.0, 0.92])


def test_rule_mask_backs_and_lays():
    # ours $4 (0.25): BSP $6 is 1.5x ours (a back at 1.3x, not 1.6x); BSP $3 is ours / 1.33 (a lay at 1.3x)
    t = pd.DataFrame({"bsp": [6.0, 3.0, 6.0], "p_x": [0.25, 0.25, 0.25]})
    seg = np.array([True, True, False])
    assert list(R24.rule_mask(t, seg, 1.5, 8, "back", 1.3)) == [True, False, False]
    assert list(R24.rule_mask(t, seg, 1.5, 8, "back", 1.6)) == [False, False, False]
    assert list(R24.rule_mask(t, seg, 1.5, 8, "lay", 1.3)) == [False, True, False]
