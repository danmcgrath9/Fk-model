"""research/greyhound/topaz_round10.py: the held-out inputs come from the dog's previous race only."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round10 as R10  # noqa: E402


def test_held_out_is_last_start_beaten_out_and_fastest_today():
    # race 1 (1 Jan): dog A out in 5.30 but B out in 5.25 and leads; race 2 (8 Jan): A is the fastest on today's rating
    df = pd.DataFrame({"race_id": [1, 1, 1, 2, 2, 2], "dog": ["A", "B", "C", "A", "D", "E"],
                       "date": pd.to_datetime(["2026-01-01"] * 3 + ["2026-01-08"] * 3),
                       "box": [3, 1, 5, 1, 2, 3], "split": [5.30, 5.25, 5.50, np.nan, np.nan, np.nan],
                       "pir": ["22", "11", "33", "", "", ""], "map_speed_rank": [2, 1, 3, 1, 2, 3]})
    out = R10.held_out_features(df)
    a2 = out[(out.race_id == 2) & (out.dog == "A")].iloc[0]
    assert (a2.prev_led, a2.prev_split_rank, round(a2.prev_split_gap, 2), a2.prev_speed_rank) == (0.0, 2.0, 0.05, 2.0)
    assert a2.speed_rank_up == 1.0 and a2.held_out == 1.0
    # nothing from race 2 itself, and a first start has no previous run
    assert out[out.race_id == 1].prev_led.isna().all() and np.isnan(out[(out.race_id == 2) & (out.dog == "D")].iloc[0].held_out)
