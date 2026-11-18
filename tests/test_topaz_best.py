import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "research", "greyhound"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import topaz_best as B  # noqa: E402


def test_runs_history_by_hand():
    bw = pd.DataFrame({"date": ["2026-11-01"], "_dn": ["A"], "tab_first_bw": [4.0], "tab_last": [2.0],
                       "tab_change": [3.2], "tab_n": [3], "books_first": [5.0]})
    h = B.runs_history(bw)
    # tab: log(4/2); first: log(4/3.2); books: log(4/5) (the books opened longer); nfl: log(1 + 3)
    assert np.allclose(h[["tab", "first", "books", "nfl"]].values[0], [np.log(2), np.log(1.25), np.log(0.8), np.log(4)])


def test_mh_for_uses_earlier_days_only():
    hist = pd.DataFrame({"date": pd.to_datetime(["2026-11-01", "2026-11-05", "2026-11-09", "2026-11-05"]),
                         "_dn": ["A", "A", "A", "B"], "tab": [0.1, 0.3, 0.9, 0.5], "first": [0.0] * 4,
                         "books": [np.nan] * 4, "nfl": [1.0] * 4})
    keys = pd.DataFrame({"date": pd.to_datetime(["2026-11-09", "2026-11-12", "2026-11-05", "2026-11-12"]),
                         "_dn": ["A", "A", "B", "C"]})
    m = B.mh_for(keys, hist)
    # A on 9 Nov sees 1 and 5 Nov (not its own 9 Nov run): last 0.3, mean 0.2; on 12 Nov it sees all three: last 0.9,
    # mean (0.1 + 0.3 + 0.9) / 3; B on 5 Nov has nothing earlier; C has no history at all
    assert np.isclose(m.mh_tab_last[0], 0.3) and np.isclose(m.mh_tab_mean5[0], 0.2)
    assert np.isclose(m.mh_tab_last[1], 0.9) and np.isclose(m.mh_tab_mean5[1], 1.3 / 3)
    assert np.isnan(m.mh_tab_last[2]) and np.isnan(m.mh_tab_last[3])
    assert list(m.columns) == [f"mh_{c}_{k}" for c in B.MH for k in ("last", "mean5")]


def test_bets_and_kelly_by_hand():
    # p 0.30 at $4.00: 0.30 - 0.25 = 5 points, a bet; kelly 0.25 x (4 x 0.30 - 1) / 3 = 0.01667
    # p 0.26 at $4.00: 1 point, no bet; p 0.08 at $20: 3 points over but fair $12.50 - a bet;
    # p 0.06 at $40: fair $16.67, over $15, no bet
    p = np.array([0.30, 0.26, 0.08, 0.06])
    price = np.array([4.0, 4.0, 20.0, 40.0])
    assert list(B.bets(p, price)) == [True, False, True, False]
    assert np.isclose(B.kelly(p, price)[0], 0.25 * 0.2 / 3)
    assert B.kelly(np.array([0.9]), np.array([2.0]))[0] == B.CAP           # 0.25 x 0.8 = 0.2, capped at 5%


def test_at_open_offset_only_when_no_rounds():
    # a model that kept no rounds prices the race at TAB's opening book itself: no dog is 2 points over TAB
    x = pd.DataFrame({"bw_race": ["r"] * 3, "date": ["2026-11-19"] * 3, "dog_name": ["A", "B", "C"],
                      "price": [2.0, 3.0, 6.0], "p_i_open": [0.5, 0.3, 0.2]})
    x["p_tab_open"] = (1 / x.price) / (1 / x.price).sum()
    out = B.at_open(x, None, {"cols": ["lp_ours", "lp_tab"], "rounds": 0}, pd.DataFrame())
    assert np.allclose(out.p_best.values, x.p_tab_open.values) and not out.best_bet.any()
