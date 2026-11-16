"""Round 49: the edge quarter by quarter (topaz_round49)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round49 as R49  # noqa: E402
from test_round47 import field  # noqa: E402


def test_log_loss_by_quarter_reads_winners_in_clean_races_with_a_full_bsp():
    t = pd.DataFrame({"race_id": [1, 1, 2, 2, 3, 3], "date": pd.to_datetime(["2025-01-05"] * 4 + ["2025-04-02"] * 2),
                      "won": [1, 0, 0, 1, 1, 0], "n_later": [0, 0, 1, 1, 0, 0],
                      "p_book": [0.5, 0.5, 0.4, 0.6, 0.25, 0.75], "p_x_bet": [0.6, 0.4, 0.5, 0.5, 0.2, 0.8],
                      "pb6": [0.55, 0.45, 0.45, 0.55, 0.22, 0.78], "p_bsp": [0.7, 0.3, 0.3, 0.7, 0.4, 0.6]})
    f = R49.forecasts(t)
    assert list(f.quarter) == ["2025Q1", "2025Q2"] and list(f.races) == [1, 1]   # race 2 had a late scratching
    assert np.isclose(f.tab.iloc[0], -np.log(0.5)) and np.isclose(f.bsp.iloc[1], -np.log(0.4))


def test_the_market_reads_one_row_per_race():
    t = pd.DataFrame({"race_id": [1, 1, 2], "date": pd.to_datetime(["2025-01-05", "2025-01-05", "2025-02-01"]),
                      "tab_book": [1.3, 1.3, 1.2], "to_jump": [30.0, 30.0, 8.0], "open_hour": [20.0, 20.0, 9.0]})
    m = R49.market(t)
    assert len(m) == 1 and np.isclose(m.book.iloc[0], 1.25) and np.isclose(m.night.iloc[0], 0.5)
    assert np.isclose(m.day.iloc[0], 0.5) and np.isclose(m.hours.iloc[0], 19.0)


def test_the_report_is_well_formed(capsys):
    t = field(400)
    t["p_x_bet"] = t.pb6
    t["n_later"] = 0
    R49.report(t)
    out = capsys.readouterr().out.splitlines()
    a = [r for r in out if r.startswith("| 20")]
    assert a and all(r.count("|") in (10, 13) for r in a), a[:3]
