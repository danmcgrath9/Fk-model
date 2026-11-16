"""Round 52: the blends at the same number of bets (topaz_round52)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round52 as R52  # noqa: E402


def frame():
    # our odds 1/p: 2.5, 4, 10, 20 (out of band), 1.5 (out of band), 5 (no BSP)
    return pd.DataFrame({"p": [0.4, 0.25, 0.1, 0.05, 0.6, 0.2], "price": [3.0, 6.0, 20.0, 40.0, 2.0, 10.0],
                         "ded": [0.0, 0.1, 0.0, 0.0, 0.0, 0.0], "p_bsp": [0.35, 0.2, 0.08, 0.04, 0.5, np.nan]})


def test_the_best_n_by_edge_inside_the_band_with_a_bsp():
    t = frame()
    # edges: 1.2, 1.5, 2.0 in the band with a BSP; 2.0 out of band; 1.2 out of band; 2.0 with no BSP
    x, paid, edge = R52.top_n(t, "p", np.ones(len(t), bool), 2)
    assert list(np.flatnonzero(x)) == [1, 2] and np.isclose(edge, 1.5)
    assert np.isclose(paid[1], 1 + 5 * 0.9)                 # after TAB's deduction
    x, _, edge = R52.top_n(t, "p", np.array([1, 1, 0, 1, 1, 1], bool), 2)
    assert list(np.flatnonzero(x)) == [0, 1] and np.isclose(edge, 1.2)
    assert R52.top_n(t, "p", np.ones(len(t), bool), 4)[0] is None


def test_the_splits_read_the_track_codes_and_the_tracked_runs():
    t = pd.DataFrame({"track": ["mea", "BEN", "SAP", "WGL"], "iso_runs": [3, 0, np.nan, 1]})
    g = R52.splits(t)
    assert list(g["at a tracked track"]) == [True, False, True, False]
    assert list(g["runner with a tracked run before"]) == [True, False, False, True]
    assert list(g["runner with none"]) == [False, True, True, False]


def test_nothing_runs_without_both_named_walks(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("BETWATCH_DIR", str(tmp_path))
    monkeypatch.delenv("WALK_ISO_USE", raising=False)
    assert R52.main(str(tmp_path), "t") == 1
    assert "Both saved walks must be named" in capsys.readouterr().out


def test_the_tables_print_on_a_small_field(capsys):
    rng = np.random.default_rng(5)
    rows = []
    for r in range(300):
        p = rng.dirichlet(np.ones(6))
        w = rng.choice(6, p=p)
        for i in range(6):
            rows.append(dict(race_id=r, won=int(i == w), n_later=0, track="SAN" if r % 3 == 0 else "BEN",
                             iso_runs=float(i % 2), date=pd.Timestamp("2024-06-01") + pd.Timedelta(days=r * 3),
                             p_book=p[i], p_x_bet=p[i], p_i_bet=p[i], p_bsp=p[i], price=0.8 / p[i] * 1.6, ded=0.0,
                             **{c: p[i] for c in R52.BLENDS.values()}))
    t = pd.DataFrame(rows)
    since = (t.date >= R52.SINCE).values
    R52.ladder(t, {"every race": since}, (5, 10))
    R52.ll_split(t, {k: v for k, v in R52.splits(t).items()})
    out = capsys.readouterr().out
    assert "| every race | no Isolynx, 0.54 / 0.67 (the card) | 5 |" in out and "| Feb 2025 on | at a tracked track |" in out
