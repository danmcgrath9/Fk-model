"""Round 59: the threshold and the stake, re-judged (topaz_round59)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round46 as R46  # noqa: E402
import topaz_round59 as R59  # noqa: E402


def field():
    rng = np.random.default_rng(6)
    rows = []
    for r in range(900):
        b = rng.dirichlet(np.full(6, 2.0))
        ours = b * rng.lognormal(0, 0.3, 6)
        ours /= ours.sum()
        w = rng.choice(6, p=b)
        for i in range(6):
            rows.append(dict(race_id=r, won=int(i == w), p_book=b[i], pb6=ours[i], price=1 / b[i] * 0.8, ded=0.0,
                             p_bsp=b[i], q_bsp=b[i] * (0.95 if i == 0 else 1.0),
                             date=pd.Timestamp("2025-03-01") + pd.Timedelta(days=r // 2)))
    return pd.DataFrame(rows)


def test_both_judges_judge_the_same_bets():
    t = field()
    t.loc[t.race_id == 3, "q_bsp"] = np.nan
    m = np.ones(len(t), bool)
    j = R59.both(t, m, 1 / t.p_bsp.values, np.ones(len(t)))
    assert j["BSP"]["n"] == j["BSP corrected"]["n"] == len(t) - 6
    assert np.isclose(j["BSP"]["bsp"], 0, atol=1e-6) and j["BSP corrected"]["bsp"] < 0   # paid at BSP: zero, then less


def test_the_tables_print(capsys):
    t = field()
    old = R46.REPLAYS
    R46.REPLAYS = 200
    try:
        R59.threshold_table(t)
        R59.replay_table(t)
    finally:
        R46.REPLAYS = old
    out = capsys.readouterr().out
    assert "| Feb 2025 on | the card's stake, 1.2x, not 1.3x |" in out and "| one unit flat | BSP corrected |" in out
