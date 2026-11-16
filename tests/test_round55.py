"""Round 55: the calibration scan by group (topaz_round55)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round55 as R55  # noqa: E402


def test_a_lean_needs_both_halves_past_z_with_the_same_sign():
    up, down, flat, empty = dict(n=9, z=2.4), dict(n=9, z=-2.1), dict(n=9, z=1.9), dict(n=0)
    assert R55.lean(up, dict(n=5, z=2.0)) == "wins more than TAB says"
    assert R55.lean(down, dict(n=5, z=-3.0)) == "wins less than TAB says"
    assert R55.lean(up, flat) == "" and R55.lean(up, down) == "" and R55.lean(empty, up) == ""


def test_the_groups_label_every_runner():
    t = pd.DataFrame({"race_id": [1, 1, 1, 2, 2], "p_book": [0.5, 0.3, 0.2, 0.6, 0.4],
                      "tip_rank": [1, 0, 3, np.nan, np.nan], "box": [1, 4, 8, 2, 5], "runs": [0, 2, 30, 5, np.nan],
                      "days_since": [np.nan, 7, 14, 40, 90], "class_step": [1, 0, -1, np.nan, 0],
                      "distance": [300, 400, 500, 600, 400]})
    g = R55.groups(t)
    assert list(g["GRV's tip"][0]) == ["first tip", "not tipped", "second to fourth tip", "no tips record",
                                       "no tips record"]
    assert list(g["TAB's order"][0]) == ["favourite", "second", "third", "favourite", "second"]
    assert list(g["starts before the race"][0]) == ["first start", "1 to 3", "11 or more", "4 to 10", "unknown"]
    assert list(g["class step"][0]) == ["dropping in class", "same class", "rising in class", "unknown", "same class"]
    assert list(g["GRV's best bet"][0]) == ["unknown"] * 5          # no column: unknown, never a guess
    assert list(g["the field at the bet"][0]) == ["6 or fewer"] * 5


def test_the_scan_prints_and_finds_a_planted_lean(capsys):
    rng = np.random.default_rng(2)
    rows = []
    for r in range(4000):
        b = rng.dirichlet(np.full(6, 2.0))
        true = b * np.where(np.arange(6) == 0, 1.5, 1.0)        # box 1 wins half as often again as the book says
        true /= true.sum()
        w = rng.choice(6, p=true)
        for i in range(6):
            rows.append(dict(race_id=r, won=int(i == w), box=i + 1, p_book=b[i], p_i_bet=b[i], h_p_x_bet=b[i],
                             h_p_i_bet=b[i], p_bsp=true[i], date=pd.Timestamp("2023-06-01") + pd.Timedelta(days=r // 3)))
    t = pd.DataFrame(rows)
    found = R55.scan(t, {"box": R55.groups(t)["box"]})
    assert ("box", "1", "wins more than TAB says") in found
    assert "| box | 1 |" in capsys.readouterr().out
