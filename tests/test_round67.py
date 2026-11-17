"""Round 67: more bets from the best model (topaz_round67)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round67 as R67  # noqa: E402


def test_the_models_chance_undoes_the_books_sum():
    # race 1: TAB's book sums to 1.25, the saved column is the chance x 1.25
    t = pd.DataFrame({"race_id": [1, 1, 2, 2], "p_book": [0.75, 0.5, 0.6, 0.6],
                      "c": [0.5 * 1.25, 0.5 * 1.25, 0.3 * 1.2, 0.7 * 1.2]})
    assert np.allclose(R67.model_chance(t, "c"), [0.5, 0.5, 0.3, 0.7])


def test_value_bets_use_the_price_after_the_deduction_and_the_band():
    # price $5, 10% deduction: paid 1 + 4 x 0.9 = 4.6; chance 0.25 -> EV 4.6 x 0.25 - 1 = +15%, fair $4
    # price $3, no deduction, chance 0.4 -> EV +20%, fair $2.50; price $20, chance 0.06 -> EV +20%, fair $16.67
    t = pd.DataFrame({"price": [5.0, 3.0, 20.0], "ded": [0.10, 0.0, np.nan]})
    p = np.array([0.25, 0.4, 0.06])
    m, paid, ev = R67.value_bets(t, p, 0.10, np.inf, (2.0, 15.0))
    assert np.allclose(paid, [4.6, 3.0, 20.0]) and np.allclose(ev, [0.15, 0.2, 0.2])
    assert list(m) == [True, True, False]                  # the $16.67 dog is outside the card's band
    m, _, _ = R67.value_bets(t, p, 0.10, 0.18, (0.0, np.inf))
    assert list(m) == [True, False, False]                 # a slice is [lo, hi)


def test_kelly_stakes_are_fractional_capped_and_scaled_to_a_mean_of_one():
    # quarter Kelly: 0.25 x (paid x p - 1) / (paid - 1)
    # a: paid 3, p 0.4 -> 0.25 x 0.2 / 2 = 0.025; b: paid 11, p 0.2 -> 0.25 x 1.2 / 10 = 0.03, under the 5% cap
    # c: paid 2, p 0.9 -> 0.25 x 0.8 / 1 = 0.2 -> capped at 0.05; d is not a bet
    p = np.array([0.4, 0.2, 0.9, 0.5])
    paid = np.array([3.0, 11.0, 2.0, 3.0])
    m = np.array([True, True, True, False])
    u = R67.kelly_stakes(p, paid, m)
    raw = np.array([0.025, 0.03, 0.05])
    assert np.allclose(u[:3], raw / raw.mean()) and u[3] == 0
    assert np.isclose(u[m].mean(), 1.0)


def test_a_saved_model_lands_on_the_runners_that_ran(tmp_path, monkeypatch):
    pd.DataFrame({"race_id": [1, 1], "dog": ["a", "b"], "c_m": [0.7, 0.4]}).to_csv(tmp_path / "corr_r65.csv.gz",
                                                                                index=False)
    monkeypatch.setenv("WALK_CACHE_DIR", str(tmp_path))
    x = pd.DataFrame({"race_id": [1, 1, 1], "dog": ["a", "b", "c"], "is_ran": [1, 1, 0], "p_book": [0.5, 0.5, 0.2]})
    assert R67.read_saved(x, "r65", "c_m")
    assert np.allclose(x.c_m.values, [0.7, 0.4, 0.2])      # the scratched dog keeps TAB's book
    assert not R67.read_saved(x, "r99", "c_m")
