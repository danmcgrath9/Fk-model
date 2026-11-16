"""Round 39: the other books at the moment of the bet (topaz_round39)."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round39 as R39  # noqa: E402


def runner(name, tab, sb=None, lb=None, scratched=None):
    books = {"Tab": {"flucs": tab}}
    if sb:
        books["Sportsbet"] = {"flucs": sb}
    if lb:
        books["Ladbrokes"] = {"flucs": lb}
    return {"name": name, "scratched": scratched, "books": books}


def test_a_book_not_open_at_tabs_first_price_gives_no_price_then():
    r = {"id": "r1", "date": "2026-03-01", "start": "2026-03-01T10:00:00Z", "runners": [
        runner("A", [[4.0, "2026-03-01T00:00:00Z"], [3.5, "2026-03-01T02:00:00Z"]],
               sb=[[4.4, "2026-03-01T01:00:00Z"]], lb=[[3.9, "2026-02-28T23:30:00Z"]]),
        runner("B", [[1.5, "2026-03-01T00:00:00Z"]], sb=[[1.45, "2026-03-01T01:00:00Z"]],
               lb=[[1.5, "2026-02-28T23:30:00Z"]])]}
    rows = R39.race_rows(r)
    o = [x for x in rows if x["when"] == "tab_open" and x["dog_raw"] == "A"][0]
    assert np.isnan(o["sb"]) and o["sb_first"] == 4.4      # Sportsbet opened an hour after TAB
    assert o["lb"] == 3.9 and o["lag_lb"] == -0.5 and o["lag_sb"] == 1.0
    a = [x for x in rows if x["when"] == "all_open" and x["dog_raw"] == "A"][0]
    assert a["price"] == 4.0 and a["sb"] == 4.4 and a["lag_all"] == 1.0   # TAB still 4.0 an hour in
    assert np.isclose(a["to_jump"], 9.0)


def test_a_dog_scratched_after_the_bet_brings_the_deduction():
    r = {"id": "r1", "date": "2026-03-01", "start": "2026-03-01T10:00:00Z", "runners": [
        runner("A", [[4.0, "2026-03-01T00:00:00Z"]]), runner("B", [[2.0, "2026-03-01T00:00:00Z"]]),
        runner("C", [[5.0, "2026-03-01T00:00:00Z"]], scratched="2026-03-01T05:00:00Z")]}
    rows = [x for x in R39.race_rows(r) if x["when"] == "tab_open"]
    assert len(rows) == 3 and all(x["n_later"] == 1 for x in rows)
    assert np.isclose(rows[0]["ded"], 0.20)                 # 100 / $5 = 20c
