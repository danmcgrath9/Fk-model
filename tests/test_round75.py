import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "research", "greyhound"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import topaz_round75 as R75  # noqa: E402


def test_what_became():
    o = np.array([3.0, 4.0, 5.0, 6.0, 7.0])
    later = np.array([3.0, 3.5, 5.5, np.nan, 7.0])
    f = R75.what_became(o, later, np.array([True, True, True, True, False]))
    # of the four bets: one the same, one shorter, one longer, one gone
    assert f == {"same": 0.25, "shorter": 0.25, "longer": 0.25, "gone": 0.25}


def test_prices_at_matches_by_day_and_name(monkeypatch):
    monkeypatch.setattr(R75.gbm_v0, "norm_name", lambda s: s.str.upper())
    day = pd.Timestamp("2026-03-01")
    t = pd.DataFrame({"date": [day, day, day], "dog_name": ["a", "b", "c"]})
    fr = pd.DataFrame({"date": [day] * 4, "_dn": ["A", "B", "A", "C"], "k": [5, 5, 15, 5],
                       "ran": [True, True, True, False], "price": [3.2, 4.4, 2.9, 9.0], "ded": [0.05, 0.0, 0.0, 0.0]})
    p, d = R75.prices_at(t, fr, 5)
    # a and b at 5 minutes; c was scratched (not ran), so it has no price
    assert np.allclose(p[:2], [3.2, 4.4]) and np.isnan(p[2])
    assert np.allclose(d, [0.05, 0.0, 0.0])


def test_no_betwatch(monkeypatch, capsys):
    monkeypatch.delenv("BETWATCH_DIR", raising=False)
    assert R75.main("nowhere", "t") == 1
    assert "nothing to test" in capsys.readouterr().out
