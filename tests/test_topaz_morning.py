import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "research", "greyhound"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import topaz_morning as M  # noqa: E402


def test_latest_prices_takes_the_last_tab_fluc():
    races = [{"track": "Bendigo", "number": 7, "runners": [
        {"name": "Perfect Ace", "books": {"Tab": {"flucs": [[1.65, "2026-11-17T23:05:00Z"], [1.9, "2026-11-17T20:19:00Z"]]},
                                          "Sportsbet": {"last": [1.7, "2026-11-17T23:00:00Z"]}}}]}]
    got = M.latest_prices(races)
    k = ("Bendigo", "7", M.T.norm(pd.Series(["Perfect Ace"]))[0])
    assert got[k]["tab_now"] == 1.65 and got[k]["sportsbet_now"] == 1.7 and got[k]["ladbrokes_now"] is None


def test_morning_bets_rule_and_marks():
    # corrected chance 0.25 -> fair $4.00; need $4.40 at 1.1x and $4.80 at 1.2x
    # dog A: TAB opened $5.00 -> a bet at both; dog B: $4.50 -> 1.1x only; dog C: $4.00 -> no bet;
    # dog D: chance 0.6 -> fair $1.67, under $2 -> no bet however long TAB opened
    x = pd.DataFrame({"p_corr": [0.25, 0.25, 0.25, 0.6], "price": [5.0, 4.5, 4.0, 3.0],
                      "venue": ["Bendigo"] * 4, "race_no": ["7"] * 4, "start": ["2026-11-18T04:20:00Z"] * 4,
                      "card_box": ["1", "2", "3", "4"], "card_dog": ["A", "B", "C", "D"], "dog_name": ["A", "B", "C", "D"],
                      "tab_first_t": ["2026-11-17T20:19:00Z"] * 4})
    now = {("Bendigo", "7", M.T.norm(pd.Series(["A"]))[0]): {"tab_now": 4.2}}
    b = M.morning_bets(x, now)
    assert [r["dog"] for r in b] == ["A", "B"]
    assert [r["at_12"] for r in b] == [True, False]
    assert b[0]["need_11"] == 4.4 and b[0]["need_12"] == 4.8 and b[0]["tab_open"] == 5.0 and b[0]["tab_now"] == 4.2
    assert "tab_now" not in b[1]
