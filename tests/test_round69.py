"""Round 69: the margin rule, taken apart and staked (topaz_round69)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round69 as R69  # noqa: E402


def test_the_spread_margin_grows_with_the_prices_own_spread():
    # $2: needs 0.5, spread sqrt(0.5 x 0.5) = 0.5; the model's 0.53 is 0.03 over, 0.06 spreads
    # $10: needs 0.1, spread sqrt(0.1 x 0.9) = 0.3; the model's 0.115 is 0.015 over, 0.05 spreads
    # $40: the model's fair price $25 is outside the band
    t = pd.DataFrame({"price": [2.0, 10.0, 40.0], "ded": [0.0, 0.0, 0.0]})
    p = np.array([0.53, 0.115, 0.04])
    assert list(R69.spread_bets(t, p, 0.05)) == [True, True, False]
    assert list(R69.spread_bets(t, p, 0.06)) == [True, False, False]
    assert list(R69.spread_bets(t, p, 0.08)) == [False, False, False]


def test_points_are_named_plainly():
    assert [R69.points(d) for d in (0.01, 0.015, 0.02, 0.025)] == ["1 point", "1.5 points", "2 points", "2.5 points"]


def test_nothing_runs_without_betwatch(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("BETWATCH_DIR", raising=False)
    assert R69.main(str(tmp_path), "t") == 1
    assert "No Betwatch files" in capsys.readouterr().out
