"""research/greyhound/topaz_round22.py: the rule table respects the track mask."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round22 as R22  # noqa: E402


def test_rule_table_masks_tracks():
    # two races: ours rates the $5 dog at 0.4 (blend), GRV's SP at 0.2: a bet; the mask can take its track out
    t = pd.DataFrame({"race_id": [1, 1, 2, 2], "date": pd.to_datetime(["2026-01-01"] * 2 + ["2026-02-01"] * 2),
                      "won": [1, 0, 0, 1], "start_price": [5.0, 1.25, 5.0, 1.25], "p_sp": [0.2, 0.8, 0.2, 0.8],
                      "track": ["SAN", "SAN", "BAL", "BAL"]})
    pb = np.array([0.4, 0.6, 0.4, 0.6])
    h = np.array([True, True, False, False])
    all_rows = R22.rule_table("x", t, pb, h)
    assert all_rows[2].startswith("| x | all | 2 | 1 |")                  # one bet a race, the SAN one won
    rest = R22.rule_table("x", t, pb, h, (t.track != "SAN").values)
    assert rest[0] == "| x | 1st | 0 | | | | | | |" and rest[2].startswith("| x | all | 1 | 0 |")
