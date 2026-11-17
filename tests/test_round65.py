"""Round 65: the market's history, built out (topaz_round65)."""
import gzip
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round65 as R65  # noqa: E402


def write_betwatch(path, races):
    with gzip.open(path / "betwatch_VIC_G_2024-01.json.gz", "wt", encoding="utf-8") as fh:
        json.dump({"races": races}, fh)


def test_tab_and_the_other_books_are_read_up_to_the_jump(tmp_path):
    write_betwatch(tmp_path, [{"date": "2024-01-05", "start": "2024-01-05T10:00:00Z", "runners": [
        {"name": "Fast Dog", "books": {
            "Tab": {"flucs": [[4.0, "2024-01-05T07:00:00Z"], [4.0, "2024-01-05T07:30:00Z"],
                              [3.5, "2024-01-05T08:00:00Z"], [3.0, "2024-01-05T09:00:00Z"],
                              [2.0, "2024-01-05T10:05:00Z"]]},
            "Sportsbet": {"flucs": [[3.6, "2024-01-05T08:30:00Z"]]}, "Ladbrokes": {"flucs": [[4.0, "2024-01-05T08:40:00Z"]]},
            "Betfair": {"flucs": [[9.0, "2024-01-05T08:40:00Z"]]}}},
        {"name": "Gone", "scratched": "2024-01-05T09:00:00Z", "books": {"Tab": {"flucs": [[5.0, "2024-01-05T07:00:00Z"]]}}},
        {"name": "No Tab", "books": {"Sportsbet": {"flucs": [[6.0, "2024-01-05T08:30:00Z"]]}}}]}])
    bw = R65.tab_and_books(str(tmp_path))
    assert len(bw) == 1
    r = bw.iloc[0]
    assert r.tab_first_bw == 4.0 and r.tab_last == 3.0 and r.tab_change == 3.5 and r.tab_n == 4
    assert np.isclose(r.books_first, np.sqrt(3.6 * 4.0))          # Betfair left out


def test_the_day_market_is_signed_shorter_positive():
    R = pd.DataFrame({"date": pd.to_datetime(["2024-01-05", "2024-01-05"]), "dog_name": ["Fast Dog", "Slow Dog"],
                      "price": [4.0, 5.0]})
    bw = pd.DataFrame({"date": pd.to_datetime(["2024-01-05"]), "_dn": R65.gbm_v0.norm_name(pd.Series(["Fast Dog"])),
                       "tab_first_bw": [4.0], "tab_last": [3.0], "tab_change": [3.5], "tab_n": [4],
                       "books_first": [np.sqrt(14.4)]})
    m = R65.run_market(R, bw, np.array([np.log(1.3), np.nan]))
    assert np.isclose(m.tab[0], np.log(4 / 3)) and np.isclose(m["first"][0], np.log(4 / 3.5))
    assert np.isclose(m.books[0], np.log(4 / np.sqrt(14.4))) and m.steam[0] == 1 and m.drift[0] == 0
    assert m.iloc[1][["tab", "first", "books", "nfl", "steam", "drift"]].isna().all()


def test_the_dog_history_sees_only_earlier_days():
    R = pd.DataFrame({"date": pd.to_datetime(["2024-01-01", "2024-01-03", "2024-01-03", "2024-01-05", "2024-01-02"]),
                      "dog": ["a", "a", "a", "a", "b"]})
    day = pd.DataFrame({"tab": [0.1, 0.2, 0.9, 0.3, 0.5], "first": 0.0, "books": 0.0, "nfl": 1.0,
                        "steam": [1.0, 0.0, 1.0, 1.0, 1.0], "drift": 0.0})
    h = R65.dog_history(R, day)
    assert np.isnan(h.mh_tab_last[0]) and h.mh_tab_last[1] == 0.1
    assert h.mh_tab_last[2] == 0.1 and h.mh_steam5[2] == 1.0   # both runs on day 3 see day 1 only
    assert np.isclose(h.mh_tab_mean5[3], 0.4) and np.isclose(h.mh_steam5[3], 2 / 3)   # day 1 and both of day 3
    assert np.isnan(h.mh_tab_last[4])


def test_the_trainer_window_is_the_days_before_it():
    R = pd.DataFrame({"date": pd.to_datetime(["2024-01-01", "2024-01-01", "2024-03-15", "2024-04-10", "2024-04-10"]),
                      "trainer_id": [7, 7, 7, 7, 8]})
    mv = np.array([0.2, 0.4, -0.3, 0.0, 0.1])
    steam = np.array([0.0, 1.0, 0.0, 0.0, 0.0])
    h = R65.trainer_history(R, mv, steam, shrink=0)
    assert h.mh_tr90_n[0] == 0 and h.mh_tr90_n[1] == 0                       # nothing before the first day
    assert h.mh_tr90_n[2] == 2 and np.isclose(h.mh_tr90_mv[2], 0.3) and np.isclose(h.mh_tr90_steam[2], 0.5)
    assert h.mh_tr90_n[3] == 1 and np.isclose(h.mh_tr90_mv[3], -0.3)         # 1 January is more than 90 days back
    assert h.mh_tr90_n[4] == 0


def test_which_way_splits_into_fifths():
    rng = np.random.default_rng(1)
    v = rng.normal(size=500)
    mv = 0.1 * v
    rows = R65.which_way(v, mv, rng.integers(0, 2, 500).astype(float), np.full(500, 0.5), np.full(500, 0.5))
    assert [r[0] for r in rows] == [1, 2, 3, 4, 5] and sum(r[1] for r in rows) == 500
    assert rows[0][2] < 0 < rows[4][2]


def test_nothing_runs_without_both_named_walks(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("BETWATCH_DIR", str(tmp_path))
    monkeypatch.delenv("WALK_ISO_USE", raising=False)
    assert R65.main(str(tmp_path), "t") == 1
    assert "Both saved walks must be named" in capsys.readouterr().out
