"""research/greyhound/topaz_round30.py: reading Betwatch's month files, the join, each price's book and the CLV."""
import gzip
import json
import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round30 as R30  # noqa: E402


def _month(tmp_path):
    race = {"date": "2026-11-10", "start": "2026-11-10T08:00:00Z", "runners": [
        {"name": "Dog A", "scratched": None, "books": {
            "Tab": {"flucs": [[4.0, "2026-11-09T20:00:00Z"], [3.5, "2026-11-10T07:00:00Z"],
                              [9.0, "2026-11-10T08:05:00Z"]]},          # after the jump: never used
            "Sportsbet": {"flucs": [[4.2, "2026-11-09T21:00:00Z"]]}}},
        {"name": "Dog B", "scratched": "2026-11-10T05:00:00Z", "books": {}},
        {"name": "Dog C", "scratched": None, "books": {"Tab": {"flucs": [[2.0, "2026-11-09T20:00:00Z"]]}}}]}
    with gzip.open(tmp_path / "betwatch_VIC_G_2026-11.json.gz", "wt") as fh:
        json.dump({"races": [race]}, fh)


def test_load_takes_first_and_last_tab_price_before_the_jump(tmp_path):
    _month(tmp_path)
    bw = R30.load_betwatch(str(tmp_path))
    a = bw[bw._dn == "DOGA"].iloc[0]
    assert a.tab_first == 4.0 and a.tab_last == 3.5 and a.tab_n == 2 and a.sportsbet_first == 4.2
    assert np.isnan(a.ladbrokes_first)
    assert "DOGB" not in set(bw._dn)                 # scratched
    df = pd.DataFrame({"date": pd.to_datetime(["2026-11-10", "2026-11-10"]), "dog_name": ["DOG A", "Dog C"]})
    j = R30.join_betwatch(df, bw)
    assert list(j.tab_first) == [4.0, 2.0]


def test_book_chance_needs_every_runner_and_sums_to_one():
    t = pd.DataFrame({"race_id": [1, 1, 2, 2], "p": [4.0, 2.0, 3.0, np.nan]})
    c = R30.book_chance(t, "p")
    assert abs(c.iloc[0] + c.iloc[1] - 1) < 1e-12 and np.isnan(c.iloc[2]) and np.isnan(c.iloc[3])


def test_clv_counts_bets_that_shortened():
    t = pd.DataFrame({"tab_first": [5.0, 5.0], "bsp": [4.0, 6.0], "won": [1, 0]})
    c = R30.clv(t, np.array([True, True]), "tab_first")
    assert c["n"] == 2 and c["shorter"] == 0.5 and abs(c["mean_log"] - np.mean(np.log([5 / 4, 5 / 6]))) < 1e-12
    assert abs(c["ae_bsp"] - 1 / (1 / 4 + 1 / 6)) < 1e-12
