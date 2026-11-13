"""research/greyhound/topaz_round31.py: the best first price, the monthly blend, the bets, the segments."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round31 as R31  # noqa: E402


def test_best_first_is_the_best_of_the_three_only_where_tab_has_a_price():
    t = pd.DataFrame({"tab_first": [4.0, np.nan, 3.0], "sportsbet_first": [4.5, 9.0, np.nan],
                      "ladbrokes_first": [4.2, 8.0, 1.0]})
    b = R31.best_first(t)
    assert b[0] == 4.5 and np.isnan(b[1]) and b[2] == 3.0          # $1.00 is no price


def test_bases_band_on_the_price_taken_and_value_against_ours():
    t = pd.DataFrame({"race_id": [1, 1, 2, 2], "won": [1, 0, 0, 1],
                      "tab_first": [4.0, 2.0, 6.0, 1.6], "tab_last": [3.0, 2.5, 7.0, 1.5],
                      "best_first": [4.4, 2.0, 6.0, 1.7],
                      "pb_first": [0.30, 0.70, 0.10, 0.90], "pb_last": [0.30, 0.70, 0.10, 0.90]})
    m, r = R31.bases(t)
    first = "TAB's first price"
    assert np.allclose(r[first], [3.0, -1.0, -1.0, 0.6])
    assert list(m[(first, "every runner", 3, 5)]) == [True, False, False, False]
    assert list(m[(first, "our top pick", 1.5, 100)]) == [False, True, False, True]
    # price x ours: 1.2, 1.4, 0.6, 1.44
    assert list(m[(first, "price 1.3x ours or more", 1.5, 100)]) == [False, True, False, True]
    assert list(m[(first, "price 1x ours or more", 1.5, 100)]) == [True, True, False, True]
    assert len(m) == len(R31.PRICES) * len(R31.SIGNALS) * len(R31.BANDS)


def test_monthly_blend_uses_only_the_months_before(monkeypatch):
    seen = []

    def fake_blend(cols, df, w=None):
        if w is None:
            seen.append(df.date.max())
            return np.array([1.0, 0.0]), None
        return w, df.p_a.values
    monkeypatch.setattr(R31.V1, "blend", fake_blend)
    days = pd.date_range("2024-01-01", "2024-12-31", freq="D")
    df = pd.DataFrame({"date": np.repeat(days, 8), "race_id": np.repeat(np.arange(2 * len(days)), 4),
                       "won": np.tile([1, 0, 0, 0], 2 * len(days)), "p_a": 0.25, "p_tab_first": 0.25})
    months = pd.period_range("2024-07", "2024-12", freq="M")
    out = R31.monthly_blend(df, "p_tab_first", months)
    assert out[df.date < "2024-07-01"].isna().all() and out[df.date >= "2024-07-01"].notna().all()
    for M, last in zip(months, seen):
        assert last < M.start_time


def test_bench_segments_drop_what_is_not_known_at_the_open():
    t = pd.DataFrame({"race_id": [1, 1], "box": [1, 2], "track": ["SAN", "SAN"], "distance": [515, 515],
                      "grade": ["5", "5"], "field": [8, 8], "runs": [3, 12], "days_since": [7, 14],
                      "WIN_PREPLAY_LAST_PRICE_TAKEN": [3.0, 5.0], "WIN_PREPLAY_WEIGHTED_AVERAGE_PRICE_TAKEN": [3.0, 4.0]})
    s = R31.bench_segments(t, ["SAN"], False)
    assert "every runner" in s and s["every runner"].all()
    assert not [k for k in s if "late" in k] and "box 1" in s
