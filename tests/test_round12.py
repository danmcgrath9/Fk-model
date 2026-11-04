"""research/greyhound/topaz_round12.py: the tales' helper columns use only earlier days, and flat ROI, by hand."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round12 as R12  # noqa: E402


def frame():
    # dog A: day 1 favourite and wins, day 2 favourite and loses, day 3 (after a 30-day break) at a new track;
    # dog B runs beside it each day for the same trainer on day 3
    d = pd.to_datetime(["2026-01-01", "2026-01-01", "2026-01-08", "2026-01-08", "2026-02-07", "2026-02-07"])
    return pd.DataFrame({"race_id": [1, 1, 2, 2, 3, 3], "dog": ["A", "B"] * 3, "date": d,
                         "box": [1, 2, 1, 2, 1, 2], "start_price": [1.8, 3.0, 2.0, 2.5, 4.0, 3.0],
                         "won": [1, 0, 0, 1, 0, 1], "days_since": [np.nan, np.nan, 7, 7, 30, 30],
                         "track": ["X", "X", "X", "X", "Y", "Y"], "trainer_id": [10, 11, 10, 11, 10, 10],
                         "start_time": ["2026-01-01T09:00:00Z", "2026-01-01T09:00:00Z", "2026-01-08T02:00:00Z",
                                        "2026-01-08T02:00:00Z", "2026-02-07T09:30:00Z", "2026-02-07T09:30:00Z"],
                         "grade": ["Maiden", "Maiden", "Grade 5", "Grade 5", "Grade 5", "Grade 5"]})


def test_tale_columns_use_earlier_days_only():
    out = R12.tale_columns(frame())
    a = out[out.dog == "A"].reset_index(drop=True)
    assert list(a.sp_fav) == [1.0, 1.0, 0.0]                 # SP favourite on days 1 and 2, not day 3
    assert np.isnan(a.prev_won[0]) and a.prev_won[1] == 1 and a.prev_won[2] == 0
    assert a.prev_fav[2] == 1                                 # favourite last start, and beaten: the tale's dog
    assert a.prev_days_since[2] == 7
    assert list(a.track_runs) == [0, 1, 0]                    # first time at Y on day 3
    assert np.isnan(a.won_last2[1]) and a.won_last2[2] == 0.5
    assert list(out.trainer_runners) == [1, 1, 1, 1, 2, 2]    # trainer 10 has both on day 3
    # 9:00 UTC on 1 Jan is 8pm in Melbourne (daylight time); 2:00 UTC on 8 Jan is 1pm
    assert list(a.hour) == [20, 13, 20] and list(a.maiden) == [1.0, 0.0, 0.0]


def test_flat_roi_takes_commission_off_winnings():
    # a $3 winner pays 2 x 0.92 = 1.84 at 8%, a loser costs 1: mean (1.84 - 1) / 2
    assert abs(R12.flat_roi([1, 0], [3.0, 5.0], 0.08) - 0.42) < 1e-12
    assert abs(R12.flat_roi([1, 0], [3.0, 5.0]) - 0.5) < 1e-12
