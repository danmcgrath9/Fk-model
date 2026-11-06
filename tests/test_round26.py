"""research/greyhound/topaz_round26.py: choosing rules on a window and betting a month, by hand."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round26 as R26  # noqa: E402


def _frame(n, won, bsp, p_x, box=4, days=7):
    return pd.DataFrame({"date": pd.Timestamp("2026-01-15"), "won": won, "bsp": bsp, "p_x": p_x, "box": box,
                         "days_since": days, "runs": 5, "runs_track": 2}, index=range(n))


def test_choose_keeps_profitable_rules_with_enough_bets():
    # 10 runners at BSP $10, ours $5 (BSP 2x ours: a back at every edge); 2 win: each back returns 9 x 0.92 = 8.28,
    # so 2 x 8.28 - 8 = 8.56 on 10 bets, ROI +85.6%
    w = _frame(10, [1, 1] + [0] * 8, 10.0, 0.2)
    rules = R26.choose(w, comm=0.08, min_bets=10)
    backs = [r for r in rules if r[0] == "back" and r[1] == "all runners"]
    assert {r[4] for r in backs} == {1.1, 1.3, 1.6}
    assert all(r[5] == 10 and abs(r[6] - 0.856) < 1e-9 for r in backs)
    # with a higher bar on bets, nothing is chosen
    assert R26.choose(w, comm=0.08, min_bets=11) == []


def test_bet_counts_a_runner_once_per_side():
    cur = _frame(3, [1, 0, 0], 10.0, 0.2)
    rules = [("back", "all runners", 8, 15, 1.1, 300, 0.1), ("back", "all runners", 8, 15, 1.6, 300, 0.2)]
    b = R26.bet(cur, rules, comm=0.08)
    assert len(b) == 3                      # three runners, not six
    assert np.allclose(sorted(b.ret), [-1.0, -1.0, 8.28])
    assert R26.bet(cur, []).empty


def test_bet_lays_when_bsp_is_short_of_ours():
    # ours $8 (0.125), BSP $2.50: BSP <= ours / 1.6, so a lay; the loser keeps 0.92, the winner costs 1.50
    cur = _frame(2, [0, 1], 2.5, 0.125)
    b = R26.bet(cur, [("lay", "all runners", 1.5, 3, 1.6, 300, 0.1)], comm=0.08)
    assert np.allclose(sorted(b.ret), [-1.5, 0.92])
