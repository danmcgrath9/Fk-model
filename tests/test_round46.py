"""Round 46: the stakes' risk (topaz_round46)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round46 as R46  # noqa: E402


def test_the_worst_drawdown_is_from_the_running_peak_starting_at_zero():
    won = np.array([0, 1, 0, 0, 1, 0.0])
    paid = np.array([3.0, 3.0, 2.0, 5.0, 2.0, 4.0])
    u = np.array([1.0, 2, 1, 1, 3, 1])
    cum, dd = R46.path(won, paid, u)
    # -1, +3 (to 3), -1 (2), -1 (1), +3 (4), -1 (3): worst fall is 3 -> 1
    assert np.allclose(cum, [-1, 3, 2, 1, 4, 3]) and np.isclose(dd, 2)
    _, dd0 = R46.path(np.zeros(3), np.full(3, 4.0), np.ones(3))
    assert np.isclose(dd0, 3)                     # straight down from the start
    _, ddm = R46.path(np.array([[0, 1.0], [1, 0]]), np.array([3.0, 3.0]), np.ones(2))
    assert np.allclose(ddm, [1, 1])               # one per replay


def test_as_it_happened_sorts_by_date_and_reads_the_month():
    t = pd.DataFrame({"date": pd.to_datetime(["2025-03-02", "2025-03-01", "2025-04-01"]), "won": [1, 0, 0],
                      "p_bsp": [0.4, 0.3, np.nan]})
    s = R46.as_it_happened(t, np.ones(3, bool), np.array([3.0, 4.0, 5.0]), np.array([1.0, 2.0, 1.0]))
    assert s["n"] == 3 and np.isclose(s["staked"], 4) and np.isclose(s["won"], -2 + 2 - 1)
    assert np.isclose(s["dd"], 2) and s["run"] == 1 and s["months"] == "0 of 2"
    assert np.isclose(s["worst"], -1) and np.isclose(s["bsp"], 1 * (3 * 0.4 - 1) + 2 * (4 * 0.3 - 1))
    assert s["nb"] == 2 and s["top"] == 2


def test_replays_win_with_bsps_chance():
    n = 400
    t = pd.DataFrame({"date": pd.to_datetime("2025-03-01") + pd.to_timedelta(np.arange(n), unit="D"),
                      "p_bsp": np.full(n, 0.25)})
    old = R46.REPLAYS
    R46.REPLAYS = 4000
    try:
        s = R46.replays(t, np.ones(n, bool), np.full(n, 4.0), np.ones(n))
    finally:
        R46.REPLAYS = old
    assert abs(s["med"]) < 8                      # fair odds: about nothing on average
    assert 0.35 < s["behind"] < 0.6 and s["p5"] < 0 < s["p95"] and s["dd95"] > s["dd50"] > 0
