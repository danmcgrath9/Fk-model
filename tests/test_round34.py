"""research/greyhound/topaz_round34.py: the monthly blend on clean races, and the top pick of the whole field."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round34 as R34  # noqa: E402


def test_top_pick_is_the_top_of_the_whole_field_at_the_bet():
    x = pd.DataFrame({"race_id": [1, 1, 1, 2, 2], "pb": [0.3, 0.2, 0.5, 0.6, 0.4],
                      "is_ran": [True, True, False, True, True]})
    assert list(R34.top_of_field(x)) == [False, False, True, True, False]   # race 1's top was scratched: no bet


def test_monthly_blend_fits_on_earlier_clean_races_only(monkeypatch):
    seen = []

    def fake_blend(cols, df, w=None):
        if w is None:
            seen.append((df.date.max(), int(df.n_later.max()), bool(df.is_ran.all())))
            return np.array([1.0, 0.0]), None
        return w, df.p_x_bet.values
    monkeypatch.setattr(R34.V1, "blend", fake_blend)
    days = pd.date_range("2024-01-01", "2024-09-30", freq="D")
    n = len(days)
    x = pd.DataFrame({"date": np.repeat(days, 8), "race_id": np.repeat(np.arange(4 * n), 2),   # 2 clean races a day
                      "p_x_bet": 0.5, "p_book": 0.5, "won": np.tile([1, 0], 4 * n),
                      "n_later": np.tile([0, 0, 0, 0, 1, 1, 1, 1], n), "is_ran": True})
    out = R34.monthly_blend_at(x, pd.period_range("2024-07", "2024-09", freq="M"))
    assert out[x.date < "2024-07-01"].isna().all() and out[x.date >= "2024-07-01"].notna().all()
    for (last, later, ran), M in zip(seen, pd.period_range("2024-07", "2024-09", freq="M")):
        assert last < M.start_time and later == 0 and ran
