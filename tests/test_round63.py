"""Round 63: the card's rule at every bookmaker's first price (topaz_round63)."""
import gzip
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round63 as R63  # noqa: E402


def test_load_books_takes_each_books_first_price_before_the_jump(tmp_path):
    races = {"races": [{"id": 1, "date": "2025-03-01", "start": "2025-03-01T10:00:00Z", "runners": [
        {"name": "Fast Dog", "books": {"Tab": {"flucs": [[3.0, "2025-03-01T01:00:00Z"], [2.8, "2025-03-01T05:00:00Z"]]},
                                       "Sportsbet": {"flucs": [[3.4, "2025-03-01T02:30:00Z"]]},
                                       "Bet365": {"flucs": [[3.6, "2025-03-01T11:00:00Z"]]}}},
        {"name": "Gone", "scratched": True, "books": {"Tab": {"flucs": [[5.0, "2025-03-01T01:00:00Z"]]}}}]}]}
    with gzip.open(tmp_path / "betwatch_VIC_G_2025-03.json.gz", "wt", encoding="utf-8") as fh:
        json.dump(races, fh)
    bw = R63.load_books(str(tmp_path))
    assert len(bw) == 1 and bw.Tab_first.iloc[0] == 3.0 and bw.Sportsbet_first.iloc[0] == 3.4
    assert "Bet365_first" not in bw                                    # only after the jump: no first price
    assert np.isclose((bw.Sportsbet_t - bw.Tab_t).iloc[0] / 3600, 1.5)
    assert R63.books_of(bw) == ["Sportsbet"]


def test_the_rule_at_a_price_and_its_row():
    t = pd.DataFrame({"pb": [0.4, 0.25, 0.1, 0.6], "ded": [0, 0.1, 0, 0], "won": [1, 0, 0, 1],
                      "q_bsp": [0.35, 0.2, 0.08, np.nan], "date": pd.to_datetime(["2025-03-01"] * 4)})
    price = np.array([3.5, 5.0, 13.0, 2.0])
    m, paid = R63.bets(t, "pb", price, 1.3)
    assert list(m) == [True, False, True, False]                    # 1.4x, 1.25x, 1.3x; the last is out of the band
    assert np.isclose(paid[1], 1 + 4 * 0.9)
    r = R63.row(t, t.assign(p_bsp=t.q_bsp), m, paid, 2.0)
    assert r.startswith("2 | 1.0 | 1 |") and r.count("|") == 8
