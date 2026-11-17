import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "research", "greyhound"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import topaz_round72 as R72  # noqa: E402


def test_fixed_kelly_one_scale():
    # quarter Kelly: f = 0.25 (paid p - 1) / (paid - 1), capped at 0.05
    # dog 1: paid 3, p 0.40 -> 0.25 x 0.2 / 2 = 0.025; dog 2: paid 5, p 0.22 -> 0.25 x 0.1 / 4 = 0.00625
    # dog 3: paid 2, p 0.40 -> negative -> 0; dog 4: paid 2, p 0.80 -> 0.25 x 0.6 / 1 = 0.15 -> capped 0.05
    p = np.array([0.40, 0.22, 0.40, 0.80])
    paid = np.array([3.0, 5.0, 2.0, 2.0])
    ref = np.array([True, False, False, True])          # mean over the reference bets: (0.025 + 0.05) / 2 = 0.0375
    u = R72.fixed_kelly(p, paid, ref)
    assert np.allclose(u, [0.025 / 0.0375, 0.00625 / 0.0375, 0.0, 0.05 / 0.0375])
    assert np.isclose(u[ref].mean(), 1.0)


def test_fixed_kelly_lower_margin_leaves_stakes_alone():
    p = np.array([0.40, 0.22, np.nan])
    paid = np.array([3.0, 5.0, 4.0])
    a = R72.fixed_kelly(p, paid, np.array([True, False, False]))
    assert a[2] == 0.0 and np.isclose(a[0], 1.0)        # a missing chance stakes nothing
    assert np.isclose(a[1], 0.00625 / 0.025)


def test_read_fits_renames(monkeypatch):
    x = pd.DataFrame({"p_book": [0.5, 0.5]})

    def saved(x_, tag, col):
        if tag == "r71b":
            return False
        x_[col] = {"r70": 1.0, "r71a": 2.0}[tag]
        return True

    monkeypatch.setattr(R72.R67, "read_saved", saved)
    got = R72.read_fits(x)
    assert got == {"Test 88's fit": "c_f", "twice the rounds": "c_a"}
    assert (x.c_f == 1.0).all() and (x.c_a == 2.0).all() and "c_g" not in x


def test_no_betwatch(monkeypatch, capsys):
    monkeypatch.delenv("BETWATCH_DIR", raising=False)
    assert R72.main("nowhere", "t") == 1
    assert "nothing to test" in capsys.readouterr().out
