"""Round 37: are the held blend's bets at TAB's open real? (topaz_round37)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round37 as R37  # noqa: E402


def test_z_counts_winners_against_the_price_takens_chances():
    won, price = np.array([1, 0, 0, 0]), np.array([2.0, 4.0, 4.0, 4.0])
    p = 1 / price                                       # 0.5 + 3 x 0.25 = 1.25 expected
    want = (1 - 1.25) / np.sqrt((p * (1 - p)).sum())
    assert np.isclose(R37.z_at_price(won, price), want)


def test_a_higher_ratio_bets_on_fewer_dogs():
    t = pd.DataFrame({"race_id": [1, 1, 2, 2], "date": pd.to_datetime(["2025-03-01"] * 4), "won": [1, 0, 0, 1],
                      "pb": [0.2, 0.8, 0.2, 0.8], "p_book": [0.15, 0.85, 0.17, 0.83], "price": [7.0, 1.2, 5.8, 1.2],
                      "ded": [0.0, 0.0, 0.0, 0.0]})
    m11, _, _ = R37.rule(t, "pb", 1.1)
    m13, _, _ = R37.rule(t, "pb", 1.3)
    assert list(m11) == [True, False, True, False]     # $5.80 >= 1.1 x $5
    assert list(m13) == [True, False, False, False]    # $5.80 < 1.3 x $5


def test_clv_reads_bsp_against_the_price_paid():
    t = pd.DataFrame({"p_bsp": [0.25, 0.10, np.nan]})
    n, under, lr = R37.clv(t, np.array([True, True, True]), np.array([5.0, 8.0, 3.0]))
    assert n == 2                                      # no BSP for the third
    assert np.isclose(under, 0.5)                      # BSP $4 under $5; BSP $10 over $8
    assert np.isclose(lr, (np.log(5 / 4) + np.log(8 / 10)) / 2)
