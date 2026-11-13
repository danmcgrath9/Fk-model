"""research/greyhound/topaz_round32.py: TAB's first price, how long it stood, the price later, and the scratchings."""
import os
import sys

import numpy as np
import pytest

pytest.importorskip("lightgbm")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round32 as R32  # noqa: E402


def _race():
    # the market opens 08:00Z and the race is at 18:00Z; Dog C is scratched at 12:00Z, after every bet time (the
    # latest, 120 minutes after the open, is 10:00Z)
    return {"date": "2026-11-10", "start": "2026-11-10T18:00:00Z", "runners": [
        {"name": "Dog A", "scratched": None, "books": {"Tab": {"flucs": [
            [5.0, "2026-11-10T08:00:00Z"], [5.0, "2026-11-10T08:02:00Z"], [4.0, "2026-11-10T08:20:00Z"],
            [3.0, "2026-11-10T19:00:00Z"]]}}},                     # the last is after the jump: never used
        {"name": "Dog B", "scratched": None, "books": {"Tab": {"flucs": [
            [2.0, "2026-11-10T08:00:00Z"], [2.5, "2026-11-10T09:30:00Z"]]}}},
        {"name": "Dog C", "scratched": "2026-11-10T12:00:00Z", "books": {"Tab": {"flucs": [
            [4.0, "2026-11-10T08:00:00Z"], [8.0, "2026-11-10T11:00:00Z"]]}}}]}


def test_first_price_how_long_it_stood_and_later_prices():
    rows = {r["dog_raw"]: r for r in R32.race_rows(_race())}
    assert set(rows) == {"Dog A", "Dog B"}                          # the scratched dog has no row
    a, b = rows["Dog A"], rows["Dog B"]
    assert a["tab_first"] == 5.0 and a["stood_min"] == 20 and a["next_shorter"] == 1.0   # 08:02 repeats the price
    assert b["stood_min"] == 90 and b["next_shorter"] == 0.0
    assert (a["tab_5m"], a["tab_30m"], a["tab_60m"], a["tab_120m"]) == (5.0, 4.0, 4.0, 4.0)
    assert (b["tab_60m"], b["tab_120m"]) == (2.0, 2.5)


def test_scratchings_after_each_bet_time_and_their_share_of_the_opening_book():
    a = R32.race_rows(_race())[0]
    book = 1 / 5 + 1 / 2 + 1 / 4                                     # every runner's first price, the scratched included
    assert a["scr_after_open"] == 1 and a["scr_after_120m"] == 1 and a["scr_priced_open"] == 1
    assert abs(a["ded_open"] - (1 / 8) / book) < 1e-12              # its price when it was scratched


def test_price_at_and_ts():
    fl = [(5.0, 100.0), (4.0, 200.0)]
    assert np.isnan(R32.price_at(fl, 99)) and R32.price_at(fl, 100) == 5.0 and R32.price_at(fl, 250) == 4.0
    assert R32.ts("2026-11-10T08:00:00Z") == R32.ts("2026-11-10T19:00:00+11:00") and np.isnan(R32.ts(None))
