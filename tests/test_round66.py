"""Round 66: a second look, with the morning's moves (topaz_round66)."""
import gzip
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round66 as R66  # noqa: E402


def test_only_the_books_open_by_then_are_counted(tmp_path):
    races = [{"id": 9, "date": "2024-01-05", "start": "2024-01-05T10:00:00Z", "runners": [
        {"name": "Fast Dog", "books": {
            "Tab": {"flucs": [[4.0, "2024-01-05T06:30:00Z"]]},
            "Sportsbet": {"flucs": [[3.6, "2024-01-05T07:00:00Z"], [3.0, "2024-01-05T09:00:00Z"]]},
            "Ladbrokes": {"flucs": [[4.4, "2024-01-05T08:00:00Z"]]},
            "Betfair": {"flucs": [[9.0, "2024-01-05T06:40:00Z"]]}}},
        {"name": "Early Dog", "books": {"Tab": {"flucs": [[2.0, "2024-01-05T06:00:00Z"]]}}},
        {"name": "Gone", "scratched": "2024-01-05T07:00:00Z", "books": {"Tab": {"flucs": [[9.0, "2024-01-05T06:10:00Z"]]}}}]}]
    with gzip.open(tmp_path / "betwatch_VIC_G_2024-01.json.gz", "wt", encoding="utf-8") as fh:
        json.dump({"races": races}, fh)
    b = R66.books_by(str(tmp_path)).set_index("_dn")
    fast = b.loc[R66.gbm_v0.norm_name(pd.Series(["Fast Dog"]))[0]]
    # the market opened at 06:00 (Early Dog's first TAB price): by 07:00 Sportsbet, by 08:00 Ladbrokes too
    assert fast.nbk_60 == 1 and np.isclose(fast.bk_60, 3.6)
    assert fast.nbk_120 == 2 and np.isclose(fast.bk_120, np.sqrt(3.6 * 4.4))
    assert len(b) == 2


def test_the_mornings_moves_are_signed_shorter_positive():
    R0 = pd.DataFrame({"race_id": [1, 1], "dog": ["a", "b"], "p_book": [0.5, 0.5], "price": [2.0, 2.0]})
    Rk = pd.DataFrame({"race_id": [1, 1], "dog": ["a", "b"], "p_book": [0.6, 0.4], "price": [1.6, 2.4],
                       "bw_race": [9, 9], "dog_name": ["A", "B"]})
    bk = pd.DataFrame({"bw_race": [9], "_dn": R66.gbm_v0.norm_name(pd.Series(["A"])), "bk_60": [1.8], "nbk_60": [1]})
    m = R66.today_moves(Rk, R0, bk, 60)
    assert np.isclose(m.td_tab[0], np.log(0.6 / 0.5)) and np.isclose(m.td_price[1], np.log(2.0 / 2.4))
    assert np.isclose(m.td_books[0], np.log(2.0 / 1.8)) and np.isnan(m.td_books[1])
    assert list(m.td_nbooks) == [1.0, 0.0]


def test_the_history_follows_the_runner_not_the_row():
    H0 = pd.DataFrame({"race_id": [1, 1], "dog": ["a", "b"], "mh_steam5": [0.2, 0.8]})
    Rk = pd.DataFrame({"race_id": [1, 1, 2], "dog": ["b", "a", "a"]})
    h = R66.history_for(Rk, H0)
    assert list(h.mh_steam5[:2]) == [0.8, 0.2] and np.isnan(h.mh_steam5[2])


def test_the_second_look_adds_only_runners_the_first_did_not_bet():
    t0 = pd.DataFrame({"race_id": [1, 2], "dog": ["a", "b"], "won": [1, 0], "q_bsp": [0.5, 0.2]})
    tk = pd.DataFrame({"race_id": [1, 3], "dog": ["a", "c"], "won": [1, 1], "q_bsp": [0.5, np.nan]})
    s = R66.combined(t0, np.array([True, True]), np.array([3.0, 6.0]), tk, np.array([True, True]),
                     np.array([2.5, 4.0]))
    assert s["n"] == 3 and s["extra"] == 1 and s["w"] == 2
    assert np.isclose(s["real"], 2.0 - 1.0 + 3.0)                         # the repeat of race 1 is not bet twice
    assert np.isclose(s["bsp_units"], (3.0 * 0.5 - 1) + (6.0 * 0.2 - 1))  # the third has no BSP


def test_nothing_runs_without_both_named_walks(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("BETWATCH_DIR", str(tmp_path))
    monkeypatch.delenv("WALK_ISO_USE", raising=False)
    assert R66.main(str(tmp_path), "t") == 1
    assert "Both saved walks must be named" in capsys.readouterr().out
