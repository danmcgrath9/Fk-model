"""Round 38: the blend at TAB's open with more inputs (topaz_round38)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round38 as R38  # noqa: E402


def test_a_books_chances_fill_the_runners_it_did_not_price_with_tabs():
    x = pd.DataFrame({"race_id": [1, 1, 1], "p_book": [0.5, 0.3, 0.2], "sb": [2.0, 2.0, np.nan]})
    p = R38.book_chance(x, "sb")
    assert np.isclose(p.sum(), 1.0)
    assert np.isclose(p.iloc[2], 0.2)                    # Sportsbet did not price it: TAB's chance
    assert np.allclose(p.iloc[:2], [0.4, 0.4])          # Sportsbet's even pair shares TAB's 0.8 for those two


def test_the_twin_is_scaled_like_ours_and_a_dog_scratched_later_takes_tabs_chance():
    x = pd.DataFrame({"race_id": [1, 1, 1], "is_ran": [True, True, False], "p_b": [0.6, 0.4, np.nan],
                      "s_later": [0.25, 0.25, 0.25], "p_book": [0.45, 0.30, 0.25],
                      "sportsbet_first": [2.0, 3.0, np.nan], "ladbrokes_first": [np.nan] * 3})
    y = R38.inputs(x)
    assert np.allclose(y.p_b_bet, [0.45, 0.30, 0.25])   # 0.6 x 0.75, 0.4 x 0.75, then TAB's 0.25
    assert np.allclose(y.p_lb, y.p_book)                # Ladbrokes priced nobody: TAB's book throughout
