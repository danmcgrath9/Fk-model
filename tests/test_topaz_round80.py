"""Round 80's order sheet: each dog's minimum TAB price with the rest of the field fixed."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "research", "greyhound"))
import topaz_round80 as S   # noqa: E402


def test_pairs_cover_every_runner_against_its_own_race():
    own, row, starts = S.pairs(np.array([1, 1, 2, 2, 2]))
    assert own.tolist() == [0, 0, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4]
    assert row.tolist() == [0, 1, 0, 1, 2, 3, 4, 2, 3, 4, 2, 3, 4]
    assert starts.tolist() == [0, 2, 4, 7, 10]


def _sheet(lp_ours, inv_other, predict):
    n = len(lp_ours)
    X = pd.DataFrame({"lp_tab": np.zeros(n), "gap": np.zeros(n), "tab_book": np.zeros(n), "n_bet": np.full(n, n)})
    return S.Sheet(X, np.log(lp_ours), np.asarray(inv_other, float), np.zeros(n), np.ones(n), predict)


def test_with_no_correction_tab_never_beats_itself():
    sh = _sheet([0.5, 0.5], [0.6, 0.6], None)
    m, _ = sh.minimum()
    # the chance is TAB's own, over a book above 1, so it never clears 2 points over 1 / price
    assert np.isnan(m).all()


def test_a_correction_that_returns_ours_sets_the_minimum_by_hand():
    # raw = lp_tab + gap = lp_ours, so the chance is ours (0.5) at any price: 0.5 - 1 / P >= 0.02 from P = 1 / 0.48
    sh = _sheet([0.5, 0.5], [0.6, 0.6], lambda X: X["gap"].values)
    m, top = sh.minimum()
    assert np.allclose(m, 1 / 0.48, rtol=0.003) and np.all(m >= 1 / 0.48 - 1e-9) and np.isnan(top).all()


def test_the_minimum_matches_a_fine_scan_when_the_field_moves_with_the_price():
    # half way between TAB and ours: the chance falls as the dog's own price rises, through the race's book
    sh = _sheet([0.45, 0.35, 0.20], [0.55, 0.45, 0.30], lambda X: 0.5 * X["gap"].values)
    m, _ = sh.minimum()
    grid = np.geomspace(1.15, 41, 4000)
    first = []
    for i in range(3):
        okk = [sh.ok(np.where(np.arange(3) == i, g, 2.0))[i] for g in grid]
        first.append(grid[int(np.argmax(okk))] if any(okk) else np.nan)
    assert np.allclose(np.nan_to_num(m), np.nan_to_num(np.array(first)), rtol=0.004)


def test_the_rule_needs_a_fair_price_under_15():
    # ours 0.05 (fair price $20): never a bet, however long TAB opens it
    sh = _sheet([0.95, 0.05], [0.9, 0.1], lambda X: X["gap"].values)
    m, _ = sh.minimum()
    assert np.isnan(m[1])


def test_holding_the_book_moves_the_rest_of_the_field_not_the_total():
    seen = {}

    def grab(X):
        seen["tab_book"], seen["lp_tab"] = X["tab_book"].values.copy(), X["lp_tab"].values.copy()
        return np.zeros(len(X))
    n = 3
    X = pd.DataFrame({"lp_tab": np.zeros(n), "gap": np.zeros(n), "tab_book": np.zeros(n)})
    inv = np.array([0.5, 0.4, 0.3])                      # TAB's usual book over the field: 1.2
    sh = S.Sheet(X, np.log([0.4, 0.35, 0.25]), inv, np.zeros(n), np.ones(n), grab, hold_book=True)
    sh.chance(np.array([4.0, 2.5, 3.0]))
    assert np.allclose(seen["tab_book"], 1.2)
    # runner 0 at $4 (0.25 of 1.2); the other two share the remaining 0.95 as 0.4 : 0.3
    assert np.allclose(np.exp(seen["lp_tab"][:3]), [0.25 / 1.2, 0.95 * 0.4 / 0.7 / 1.2, 0.95 * 0.3 / 0.7 / 1.2])
    free = S.Sheet(X, np.log([0.4, 0.35, 0.25]), inv, np.zeros(n), np.ones(n), grab, hold_book=False)
    free.chance(np.array([4.0, 2.5, 3.0]))
    assert np.allclose(seen["tab_book"][:3], 0.25 + 0.7)


def test_the_walk_is_kept_and_read_back(tmp_path, monkeypatch):
    import lightgbm as lgb
    rng = np.random.default_rng(1)
    X = pd.DataFrame({"a": rng.normal(size=200)})
    bst = lgb.train(dict(objective="regression", verbose=-1, min_data_in_leaf=5), lgb.Dataset(X, X.a * 2), 5)
    R = pd.DataFrame({"race_id": np.repeat(np.arange(50), 4), "dog": [f"d{i}" for i in range(200)]})
    p = rng.uniform(size=200)

    def walk(Ra, XK, q, use, models=None):
        models += [(pd.Period("2024-11", "M"), None), (pd.Period("2025-01", "M"), bst)]
        return p, ["2024-11: 0 rounds", "2025-01: 5 rounds"], None
    monkeypatch.setattr(S.R70, "walk_faster", walk)
    monkeypatch.setenv("WALK_CACHE_DIR", str(tmp_path))
    monkeypatch.delenv("ROUND80_REUSE", raising=False)
    p1, log1, m1 = S.walk_kept(R, X, None, None, np.zeros(200))
    monkeypatch.setenv("ROUND80_REUSE", "yes")
    monkeypatch.setattr(S.R70, "walk_faster", lambda *a, **k: (_ for _ in ()).throw(AssertionError("walked again")))
    p2, log2, m2 = S.walk_kept(R.iloc[::-1].reset_index(drop=True), X, None, None, np.zeros(200))
    assert np.allclose(p2, p[::-1]) and m2[0][1] is None and str(m2[1][0]) == "2025-01"
    assert np.allclose(m2[1][1].predict(X), bst.predict(X)) and log2[:2] == log1
