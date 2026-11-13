"""Round 36: the card's rule at TAB's open by month and by Betwatch period (topaz_round36)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round36 as R36  # noqa: E402


def test_periods_split_the_bench_without_a_gap_or_an_overlap():
    t = pd.DataFrame({"date": pd.to_datetime(["2023-08-31", "2023-09-01", "2025-01-31", "2025-02-01", "2026-11-12"])})
    got = [R36.in_period(t, a, b) for _, a, b in R36.PERIODS]
    assert [list(g) for g in got] == [[True, False, False, False, False], [False, True, True, False, False],
                                      [False, False, False, True, True]]
    assert (np.sum(got, axis=0) == 1).all()


def test_the_card_pays_after_the_deduction_and_bets_only_at_1_3x_the_blend():
    t = pd.DataFrame({"race_id": [1, 1], "date": pd.to_datetime(["2025-03-01"] * 2), "won": [1, 0],
                      "pb": [0.2, 0.8], "p_book": [0.15, 0.85], "price": [7.0, 1.2], "ded": [0.10, 0.10]})
    m, paid, u = R36.card(t, "pb", "price")
    assert list(m) == [True, False]                     # $7 >= 1.3 x $5; the $1.25 favourite is outside $2-$15
    assert np.isclose(paid[0], 1 + 6 * 0.9)            # 10c off the winnings: $6.40
    assert u[0] > 0


def test_the_fixed_blend_is_the_blend_at_test_51s_weights():
    rng = np.random.default_rng(0)
    x = pd.DataFrame({"race_id": np.repeat(np.arange(50), 4), "p_x_bet": rng.dirichlet(np.ones(4), 50).ravel(),
                      "p_book": rng.dirichlet(np.ones(4), 50).ravel()})
    s = 0.54 * np.log(x.p_x_bet) + 0.67 * np.log(x.p_book)
    want = np.exp(s) / np.exp(s).groupby(x.race_id).transform("sum")
    assert np.allclose(R36.fixed_blend(x).values, want.values)
