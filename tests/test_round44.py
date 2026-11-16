"""Round 44: the closing line as the judge (topaz_round44)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round44 as R44  # noqa: E402


def field():
    return pd.DataFrame({"race_id": [1, 1, 1, 2, 2], "date": pd.to_datetime(["2025-03-01"] * 3 + ["2026-03-01"] * 2),
                         "price": [3.0, 6.0, 20.0, 2.5, 4.0], "p_book": [0.3, 0.15, 0.05, 0.6, 0.4],
                         "pb6": [0.40, 0.25, 0.10, 0.45, 0.30], "pq": [0.50, 0.20, 0.05, 0.45, 0.30],
                         "pw": [0.40, 0.25, 0.10, 0.45, 0.30], "ps": [0.45, 0.22, 0.08, 0.45, 0.30],
                         "won": [1, 0, 0, 0, 1], "ded": [0.0, 0.0, 0.0, 0.1, 0.1],
                         "p_bsp": [0.45, 0.2, np.nan, 0.3, 0.25]})


def test_bsp_judges_each_bet_by_the_price_paid_against_its_chance():
    t = field()
    paid = np.array([3.0, 6.0, 20.0, 1 + 1.5 * 0.9, 1 + 3 * 0.9])
    x = np.array([True, True, True, False, True])
    s = R44.judged(t, x, paid, u=np.array([2.0, 1, 1, 1, 3]))
    v = np.array([3 * 0.45 - 1, 6 * 0.2 - 1, 3.7 * 0.25 - 1])          # the third bet has no BSP: left out
    assert s["n"] == 3 and s["w"] == 2 and np.isclose(s["e"], 0.9)
    assert np.isclose(s["z"], (2 - 0.9) / np.sqrt(0.45 * 0.55 + 0.2 * 0.8 + 0.25 * 0.75))
    assert np.isclose(s["bsp"], v.mean()) and np.isclose(s["units"], v.sum())
    assert np.isclose(s["se"], v.std(ddof=1) / np.sqrt(3))
    assert np.isclose(s["flat"], (2 - 1 + 2.7) / 3)
    assert np.isclose(s["kunits"], 2 * v[0] + v[1] + 3 * v[2]) and np.isclose(s["kbsp"], s["kunits"] / 6)
    assert np.isclose(s["kreal"], 2 * 2 - 1 + 3 * 2.7)
    assert R44.judged(t, np.zeros(5, bool), paid) == {"n": 0}


def test_the_tables_are_well_formed(capsys):
    t = field()
    for fn, models, cols in ((R44.ladder, R44.LADDER_MODELS, 10), (R44.rules, R44.RULE_MODELS, 11),
                             (R44.card, R44.RULE_MODELS, 7)):
        fn(t, models)
        out = [r for r in capsys.readouterr().out.splitlines() if r.startswith("| ") and "---" not in r][1:]
        assert out and all(r.count("|") == cols + 1 for r in out), (fn.__name__, out[:2])
