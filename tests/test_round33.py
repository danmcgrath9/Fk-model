"""research/greyhound/topaz_round33.py: the field at the bet time, ours scaled for the dogs scratched later, TAB's
deduction."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round33 as R33  # noqa: E402


def _race():
    # opens 08:00Z, runs 18:00Z; Dog C ($4 at the open, $5 when scratched at 08:45Z) is out after the open and the
    # 30-minute bet, and gone by the 60-minute one; Dog D was scratched before the open
    return {"id": "r1", "date": "2026-11-10", "start": "2026-11-10T18:00:00Z", "runners": [
        {"name": "Dog A", "scratched": None, "books": {"Tab": {"flucs": [[2.0, "2026-11-10T08:00:00Z"],
                                                                           [1.8, "2026-11-10T08:40:00Z"]]}}},
        {"name": "Dog B", "scratched": None, "books": {"Tab": {"flucs": [[4.0, "2026-11-10T08:00:00Z"]]}}},
        {"name": "Dog C", "scratched": "2026-11-10T08:45:00Z", "books": {"Tab": {"flucs": [
            [4.0, "2026-11-10T08:00:00Z"], [5.0, "2026-11-10T08:30:00Z"]]}}},
        {"name": "Dog D", "scratched": "2026-11-10T07:00:00Z", "books": {"Tab": {"flucs": []}}}]}


def test_field_at_each_bet_time():
    rows = pd.DataFrame(R33.field_rows(_race()))
    k0 = rows[rows.k == 0].set_index("dog_raw")
    assert set(k0.index) == {"Dog A", "Dog B", "Dog C"}
    book = 1 / 2 + 1 / 4 + 1 / 4
    assert abs(k0.loc["Dog C", "p_book"] - 0.25 / book) < 1e-12 and not k0.loc["Dog C", "ran"]
    assert abs(k0.loc["Dog A", "s_later"] - 0.25 / book) < 1e-12 and k0.loc["Dog A", "n_later"] == 1
    assert k0.loc["Dog A", "ded"] == 0.20                               # $5 when scratched: 20c
    k60 = rows[rows.k == 60].set_index("dog_raw")
    assert set(k60.index) == {"Dog A", "Dog B"} and k60.loc["Dog A", "price"] == 1.8
    assert k60.loc["Dog A", "s_later"] == 0 and k60.loc["Dog A", "ded"] == 0


def test_at_time_scales_ours_and_puts_the_scratched_dog_back():
    fr = pd.DataFrame(R33.field_rows(_race()))
    fr["date"] = pd.to_datetime(fr.date)
    fr["_dn"] = R33.gbm_v0.norm_name(fr.dog_raw)
    t = pd.DataFrame({"race_id": [7, 7], "date": pd.to_datetime(["2026-11-10"] * 2), "dog_name": ["DOG A", "Dog B"],
                      "won": [1, 0], "p_x": [0.6, 0.4]})
    x = R33.at_time(t, fr, 0)
    s = 0.25 / (1 / 2 + 1 / 4 + 1 / 4)
    ran = x[x.is_ran].set_index("dog_name")
    assert np.allclose(ran.p_x_bet.loc[["DOG A", "Dog B"]], [0.6 * (1 - s), 0.4 * (1 - s)])
    back = x[~x.is_ran]
    assert len(back) == 1 and back.race_id.iloc[0] == 7 and abs(back.p_x_bet.iloc[0] - s) < 1e-12
    assert abs(x.groupby("race_id").p_x_bet.sum().iloc[0] - 1) < 1e-12   # the field at the bet adds to one
