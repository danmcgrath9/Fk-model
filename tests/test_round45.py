"""Round 45: the card's rule at 1.2x and its stakes (topaz_round45)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round45 as R45  # noqa: E402


def field():
    return pd.DataFrame({"race_id": [1, 1, 1, 2, 2], "date": pd.to_datetime(["2025-03-01"] * 3 + ["2026-03-01"] * 2),
                         "price": [3.0, 6.0, 20.0, 2.5, 4.0], "p_book": [0.3, 0.15, 0.05, 0.6, 0.4],
                         "pb6": [0.42, 0.25, 0.10, 0.45, 0.30], "ps": [0.45, 0.22, 0.08, 0.45, 0.30],
                         "won": [1, 0, 0, 0, 1], "ded": [0.0, 0.0, 0.0, 0.1, 0.1],
                         "p_bsp": [0.45, 0.2, np.nan, 0.3, 0.25]})


def test_kelly_on_the_model_sizes_on_its_own_chance_at_tabs_price():
    t = field()
    m, paid, u = R45.bets(t, "pb6", 1.2, R45.STAKES[1])
    # edges 1.26, 1.5, 2.0, 1.125, 1.2: the fourth is under 1.2
    assert list(m) == [True, True, True, False, True]
    f = (0.42 * 3 - 1) / 2
    assert np.isclose(u[0], min(75 * f, 4)) and np.isclose(u[4], min(75 * (0.3 * 4 - 1) / 3, 4))
    assert np.allclose(paid[3:], [1 + 1.5 * 0.9, 1 + 3 * 0.9])


def test_the_cards_stake_is_the_cards_rule():
    t = field()
    m, paid, u = R45.bets(t, "pb6", 1.3, R45.STAKES[0])
    m0, paid0, u0 = R45.R37.rule(t, "pb6", 1.3)
    assert (m == m0).all() and np.allclose(paid, paid0) and np.allclose(u, u0)


def test_judged_counts_only_bets_with_a_bsp():
    t = field()
    paid = np.array([3.0, 6.0, 20.0, 2.35, 3.7])
    s = R45.judged(t, np.array([True, True, True, False, True]), paid, np.array([2.0, 1, 1, 1, 3]))
    assert s["n"] == 3 and s["w"] == 2 and np.isclose(s["e"], 0.9) and np.isclose(s["staked"], 6)
    assert np.isclose(s["real"], 2 * 2 - 1 + 3 * 2.7)
    assert np.isclose(s["bsp"], 2 * (3 * 0.45 - 1) + (6 * 0.2 - 1) + 3 * (3.7 * 0.25 - 1))


def test_the_table_is_well_formed(capsys):
    R45.table(field())
    out = [r for r in capsys.readouterr().out.splitlines() if r.startswith("| Feb")]
    assert len(out) == 3 * 2 * 2 * 3 and all(r.count("|") == 13 for r in out), out[:2]
