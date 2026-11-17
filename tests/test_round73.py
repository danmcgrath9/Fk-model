import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "research", "greyhound"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import topaz_round73 as R73  # noqa: E402


def test_raw_kelly():
    # quarter Kelly f = 0.25 (paid p - 1) / (paid - 1), capped at 0.05
    # paid 3, p 0.40 -> 0.25 x 0.2 / 2 = 0.025; paid 2, p 0.40 -> negative -> 0; paid 2, p 0.80 -> 0.15 -> 0.05;
    # paid nan -> 0
    u = R73.raw_kelly(np.array([0.40, 0.40, 0.80, 0.30]), np.array([3.0, 2.0, 2.0, np.nan]))
    assert np.allclose(u, [0.025, 0.0, 0.05, 0.0])


def test_at_price_keeps_the_deduction():
    t = pd.DataFrame({"price": [3.0, 5.0], "ded": [0.10, 0.0]})
    tp = R73.at_price(t, [4.0, np.nan])
    assert list(tp.ded) == [0.10, 0.0] and tp.price.iloc[0] == 4.0 and np.isnan(tp.price.iloc[1])
    assert list(t.price) == [3.0, 5.0]                  # the original is untouched
    # the price paid at the new price: 1 + (4 - 1) x (1 - 0.10) = 3.7
    assert np.isclose(R73.R68.paid_price(tp)[0], 3.7)


def test_second_chance_bets_each_dog_once():
    m1 = np.array([True, True, False, False])
    m2 = np.array([True, False, True, False])
    paid1, paid2 = np.array([3.0, 4.0, 9.0, 9.0]), np.array([3.5, 4.5, 6.0, 7.0])
    u1, u2 = np.array([1.0, 0.5, 9.0, 9.0]), np.array([2.0, 2.0, 0.3, 0.4])
    m, paid, u, extra = R73.second_chance(m1, paid1, u1, m2, paid2, u2)
    assert list(m) == [True, True, True, False]
    assert list(extra) == [False, False, True, False]   # dog 1 is TAB's bet, so the second chance does not bet it again
    assert np.allclose(paid[:3], [3.0, 4.0, 6.0]) and np.isnan(paid[3])
    assert np.allclose(u, [1.0, 0.5, 0.3, 0.0])


def test_no_betwatch(monkeypatch, capsys):
    monkeypatch.delenv("BETWATCH_DIR", raising=False)
    assert R73.main("nowhere", "t") == 1
    assert "nothing to test" in capsys.readouterr().out
