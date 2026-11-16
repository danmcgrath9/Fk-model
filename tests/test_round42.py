"""Round 42: the edge ladder, the top bets and the split (topaz_round42)."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round42 as R42  # noqa: E402


def field():
    """Six runners: price, the model's chance, the result, TAB's deduction."""
    return pd.DataFrame({"race_id": [1, 1, 1, 2, 2, 2], "date": pd.to_datetime(["2025-03-01"] * 6),
                         "price": [3.0, 6.0, 20.0, 2.5, 4.0, 1.5], "p_book": [0.3, 0.15, 0.05, 0.38, 0.24, 0.6],
                         "pm": [0.40, 0.25, 0.10, 0.30, 0.20, 0.55], "won": [1, 0, 0, 0, 1, 0],
                         "ded": [0.0, 0.0, 0.0, 0.10, 0.10, 0.10], "p_bsp": [0.45, 0.2, 0.05, 0.3, 0.25, 0.5]})


def test_candidates_are_the_cards_band_on_our_odds_with_the_edge_and_the_price_paid():
    m, e, paid = R42.candidates(field(), "pm")
    # our odds 2.5, 4, 10, 3.33, 5, 1.82: the last is under 2
    assert list(m) == [True, True, True, True, True, False]
    assert np.allclose(e, [1.2, 1.5, 2.0, 0.75, 0.8, 0.825])
    assert np.allclose(paid, [3.0, 6.0, 20.0, 1 + 1.5 * 0.9, 1 + 3 * 0.9, 1 + 0.5 * 0.9])


def test_stats_claim_against_got_flat_and_the_close():
    t = field()
    _, _, paid = R42.candidates(t, "pm")
    x = np.array([True, True, False, False, True, False])
    s = R42.stats(t, x, "pm", paid)
    implied = 1 / 3 + 1 / 6 + 1 / 4
    assert s["n"] == 3 and s["w"] == 2
    assert np.isclose(s["claim"], (0.40 + 0.25 + 0.20) / implied)
    assert np.isclose(s["ae"], 2 / implied)
    assert np.isclose(s["flat"], ((3 - 1) + -1 + (1 + 3 * 0.9 - 1)) / 3)
    # BSP odds 2.22, 5, 4: under the price paid on 3.0 and 6.0, not on 3.7
    assert np.isclose(s["under"], 2 / 3)
    assert R42.stats(t, np.zeros(6, bool), "pm", paid) == {"n": 0}
    assert R42.row({"n": 0}).count("|") == 7


def test_the_ladder_puts_each_candidate_in_one_rung(capsys):
    R42.ladder(field(), {"m": "pm"})
    out = [r for r in capsys.readouterr().out.splitlines() if r.startswith("| m |")]
    assert len(out) == len(R42.LADDER) - 1
    bets = [r.split(" | ")[2] for r in out]
    # edges 1.2, 1.5, 2.0, 0.75, 0.8: two under 0.9, one at 1.2 to 1.3, two at 1.5 and over
    assert bets == ["2", "0", "0", "0", "1", "0", "2"]
    assert all(r.count("|") == 11 for r in out)


def test_top_takes_the_biggest_edges_among_the_candidates():
    x, _, emin = R42.top(field(), "pm", 2)
    assert list(np.flatnonzero(x)) == [1, 2] and np.isclose(emin, 1.5)
    x, _, _ = R42.top(field(), "pm", 50)
    assert x.sum() == 5                          # no more than there are candidates


def test_the_split_counts_each_bet_in_one_row(capsys):
    t = field().assign(pa=[0.40, 0.25, 0.10, 0.30, 0.20, 0.55], pb=[0.40, 0.10, 0.10, 0.30, 0.40, 0.55])
    R42.split(t, "pa", "pb", ("a", "b"))
    rows = [r for r in capsys.readouterr().out.splitlines() if r.startswith("| both") or r.startswith("| only")]
    n = [int(r.split(" | ")[1]) for r in rows]
    ma = R42.R37.rule(t, "pa", 1.3)[0]
    mb = R42.R37.rule(t, "pb", 1.3)[0]
    assert n == [int((ma & mb).sum()), int((ma & ~mb).sum()), int((mb & ~ma).sum())]
    assert sum(n) == int((ma | mb).sum()) and int((ma & mb).sum()) >= 1


def test_the_corrections_are_read_back_from_the_walk_cache_onto_runners_that_ran(tmp_path, monkeypatch, capsys):
    x = pd.DataFrame({"race_id": [1, 1, 1, 2], "dog": ["a", "b", np.nan, "c"], "pb6": [0.5, 0.3, 0.2, 1.0],
                      "is_ran": [True, True, False, True]})
    pd.DataFrame({"race_id": [1, 1, 2], "dog": ["a", "b", "c"], "pw": [0.6, 0.2, 1.0],
                  "pq": [0.55, 0.25, 1.0]}).to_csv(tmp_path / "corr_r41.csv.gz", index=False)
    (tmp_path / "corr_r41.json").write_text(json.dumps(["**correction on the winners**: from the cache"]))
    monkeypatch.setenv("WALK_CACHE_DIR", str(tmp_path))
    out = R42.corrections(x.copy(), None, None, 0.0)
    assert np.allclose(out.pw, [0.6, 0.2, 0.2, 1.0])     # the scratched dog keeps the blend's chance
    assert np.allclose(out.pq, [0.55, 0.25, 0.2, 1.0])
    assert "from the cache" in capsys.readouterr().out
