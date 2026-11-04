"""research/greyhound/topaz_round11.py: reliable-beginner and box-preference inputs from earlier days only, by hand."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round11 as R11  # noqa: E402


def frame():
    # one dog, four days: inside (rated 10, split 5), outside (4, 3), inside (8, 1), then today from box 2
    return pd.DataFrame({"race_id": [1, 2, 3, 4], "dog": ["A"] * 4,
                         "date": pd.to_datetime(["2026-01-01", "2026-01-08", "2026-01-15", "2026-01-22"]),
                         "box": [1, 7, 3, 2], "field": [1, 1, 1, 1], "split": [5.3, 5.5, 5.6, np.nan],
                         "pir": ["1", "1", "1", ""], "map_speed_rank": [1, 1, 1, 1],
                         "own_time_rating": [10.0, 4.0, 8.0, np.nan], "own_split_rating": [5.0, 3.0, 1.0, np.nan]})


def test_box_preference_is_shrunk_and_signed_by_todays_draw():
    out = R11.box_pref_features(frame())
    d3, d4 = out.iloc[2], out.iloc[3]
    # day 3 (box 3, inside): before it, overall (10 + 4) / 2 = 7; inside 10 from 1 run -> (10 + 3*7) / 4 = 7.75
    assert abs(d3.box_pref_time - 0.75) < 1e-9 and d3.box_runs_here == 1
    # inside 7.75 against outside (4 + 21) / 4 = 6.25, drawn inside: +1.5
    assert abs(d3.inside_vs_out - 1.5) < 1e-9
    # day 4 (box 2): overall (10+4+8)/3 = 22/3; inside (18 + 22) / 5 = 8; out (4 + 22) / 4 = 6.5
    assert abs(d4.box_pref_time - (8 - 22 / 3)) < 1e-9 and d4.box_runs_here == 2 and abs(d4.inside_vs_out - 1.5) < 1e-9
    assert np.isnan(out.iloc[0].box_pref_time)                     # nothing before the first run


def test_reliable_beginner_inputs_use_only_earlier_runs():
    out = R11.reliable_features(frame())
    assert np.isnan(out.iloc[2].split_sd10)                         # two earlier runs: under the 3 needed
    assert out.iloc[2].split_worst5 == 3.0 and out.iloc[3].split_worst5 == 1.0
    assert abs(out.iloc[3].split_sd10 - np.std([5.0, 3.0, 1.0], ddof=1)) < 1e-9
    assert out.iloc[3].missed_rate10 == 0.0
