"""Round 56: the calibration scan, both halves, every forecast (topaz_round56)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round56 as R56  # noqa: E402


def test_runner_groups_drop_the_race_level_ones_and_add_two():
    t = pd.DataFrame({"race_id": [1, 1, 1], "p_book": [0.5, 0.3, 0.2], "box": [1, 2, 3],
                      "weight_change": [-0.6, 0.2, np.nan], "style_early": [3.0, 1.0, 2.0]})
    g = R56.runner_groups(t)
    assert not set(R56.RACE_LEVEL) & set(g)
    assert list(g["the weight change"][0]) == ["down 0.5 kg or more", "within 0.5 kg", "unknown"]
    assert list(g["the early-speed order"][0]) == ["third", "most early speed", "second"]


def test_the_scan_finds_a_lean_in_one_forecast_and_not_another(capsys):
    rng = np.random.default_rng(4)
    rows = []
    for r in range(4000):
        b = rng.dirichlet(np.full(6, 2.0))
        true = b * np.where(np.arange(6) == 4, 1.5, 1.0)
        true /= true.sum()
        w = rng.choice(6, p=true)
        for i in range(6):
            rows.append(dict(race_id=r, won=int(i == w), box=i + 1, p_book=b[i], p_tab_fl=b[i], h_p_x_bet=b[i],
                             h_p_i_bet=b[i], p_i_bet=b[i], p_bsp=true[i],
                             date=pd.Timestamp("2023-06-01") + pd.Timedelta(days=r // 3)))
    t = pd.DataFrame(rows)
    found = R56.scan(t, {"box": R56.runner_groups(t)["box"]})
    names = {f[2] for f in found if f[:2] == ("box", "5")}
    assert "the card's blend" in names and "BSP" not in names
    assert "| box | 5 |" in capsys.readouterr().out
