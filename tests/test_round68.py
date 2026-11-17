"""Round 68: the card with its favourites (topaz_round68)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round68 as R68  # noqa: E402


def test_the_margin_is_the_models_chance_over_the_chance_the_price_paid_needs():
    # $2, no deduction: needs 0.5, the model says 0.53, 3 points over
    # $11 with a 10% deduction: paid 1 + 10 x 0.9 = 10, needs 0.1, the model says 0.12, 2 points over
    # $30: the model's fair price $20 is outside the band
    t = pd.DataFrame({"price": [2.0, 11.0, 30.0], "ded": [0.0, 0.10, np.nan]})
    p = np.array([0.53, 0.12, 0.05])
    assert list(R68.margin_bets(t, p, 0.02)) == [True, True, False]
    assert list(R68.margin_bets(t, p, 0.03)) == [True, False, False]
    assert list(R68.margin_bets(t, p, 0.04)) == [False, False, False]


def test_the_card_takes_its_favourites_once_and_only_under_two_dollars():
    # a: fair $4 at $5, the card's 1.1x (5 >= 4.4); b: fair $1.67 at $1.80, expected value 1.8 x 0.6 - 1 = +8%
    # c: fair $1.67 at $1.70, +2%; d: fair $20, outside both
    t = pd.DataFrame({"price": [5.0, 1.8, 1.7, 30.0], "ded": [0.0, 0.0, 0.0, 0.0],
                      "c": [0.25, 0.6, 0.6, 0.05]})
    p = t.c.values
    m, f, paid = R68.card_with_favourites(t, "c", p, 1.1, None)
    assert list(m) == [True, False, False, False] and not f.any()
    m, f, _ = R68.card_with_favourites(t, "c", p, 1.1, 0.05)
    assert list(m) == [True, True, False, False] and list(f) == [False, True, False, False]
    m, f, _ = R68.card_with_favourites(t, "c", p, 1.1, 0.0)
    assert list(m) == [True, True, True, False] and int(f.sum()) == 2
    assert np.allclose(paid, [5.0, 1.8, 1.7, 30.0])


def test_staked_returns_are_per_unit_staked_with_their_errors():
    # stakes 1 and 3; BSP's chances 0.5 and 0.25 at $2.20 and $5: v = 0.1 and 0.25
    # per unit staked (0.1 + 0.75) / 4 = 0.2125; SE sqrt(0.1125^2 + 9 x 0.0375^2) / 4 = 0.039775
    # realised: the first won 1.2, the second lost 3; luck sqrt(2.2^2 x 0.25 + 9 x 25 x 0.1875) = 6.5877
    # the third has no BSP and is left out
    tq = pd.DataFrame({"p_bsp": [0.5, 0.25, np.nan], "won": [1, 0, 1]})
    s = R68.staked(tq, np.array([True, True, True]), np.array([2.2, 5.0, 3.0]), np.array([1.0, 3.0, 2.0]))
    assert s["n"] == 2 and np.isclose(s["staked"], 4.0) and np.isclose(s["units"], 0.85)
    assert np.isclose(s["per"], 0.2125) and np.isclose(s["se"], 0.039775, atol=1e-6)
    assert np.isclose(s["real"], -1.8) and np.isclose(s["luck"], 6.5877, atol=1e-4)


def test_the_deepest_fall_and_the_losing_months_follow_the_dates_not_the_rows():
    # in date order: +2, -1, -1, +3, -1 -> running 2, 1, 0, 3, 2: the deepest fall is 2
    # January +1, February +2, March -1: one losing month of three
    t = pd.DataFrame({"date": pd.to_datetime(["2025-02-10", "2025-01-05", "2025-03-01", "2025-02-02", "2025-01-09"]),
                      "race_id": [4, 1, 5, 3, 2], "won": [1, 1, 0, 0, 0]})
    paid = np.array([4.0, 3.0, 2.0, 2.0, 2.0])
    fall, lose, months = R68.deepest_fall(t, np.ones(5, bool), paid, np.ones(5))
    assert np.isclose(fall, 2.0) and (lose, months) == (1, 3)


def test_three_month_blocks_end_open():
    b = R68.blocks("2025-02-01", "2025-09-01")
    assert b == [("Feb 2025 to Apr 2025", "2025-02-01", "2025-05-01"),
                 ("May 2025 to Jul 2025", "2025-05-01", "2025-08-01"), ("Aug 2025 on", "2025-08-01", None)]


def test_nothing_runs_without_betwatch(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("BETWATCH_DIR", raising=False)
    assert R68.main(str(tmp_path), "t") == 1
    assert "No Betwatch files" in capsys.readouterr().out
