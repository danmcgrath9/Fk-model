"""Round 43: the rule by ratio and the BSP correction shrunk halfway (topaz_round43)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round43 as R43  # noqa: E402


def field():
    return pd.DataFrame({"race_id": [1, 1, 1, 2, 2], "date": pd.to_datetime(["2025-03-01"] * 3 + ["2026-03-01"] * 2),
                         "price": [3.0, 6.0, 20.0, 2.5, 4.0], "p_book": [0.3, 0.15, 0.05, 0.6, 0.4],
                         "pb6": [0.40, 0.25, 0.10, 0.45, 0.30], "pq": [0.50, 0.20, 0.05, 0.45, 0.30],
                         "won": [1, 0, 0, 0, 1], "ded": [0.0, 0.0, 0.0, 0.1, 0.1],
                         "p_bsp": [0.45, 0.2, 0.05, 0.3, 0.25]})


def test_halfway_is_the_geometric_mean_holding_the_blends_share_of_the_runners_that_ran():
    t = field()
    ps = R43.halfway(t)
    geo = np.sqrt([0.40 * 0.50, 0.25 * 0.20, 0.10 * 0.05])
    assert np.allclose(ps[:3], geo / geo.sum() * 0.75)        # race 1's runners that ran hold 0.75 of the field
    assert np.allclose(ps[3:], [0.45, 0.30])                  # the two agree: unchanged
    assert np.allclose(pd.Series(ps).groupby(t.race_id).sum(), [0.75, 0.75])


def test_flat_candidates_are_the_band_at_the_ratio_or_over():
    t = field()
    m, paid, u = R43.flat_candidates(t, "pb6", 1.2)
    # edges 1.2, 1.5, 2.0, 1.125, 1.2; our odds 2.5, 4, 10, 2.22, 3.33: all in the band
    assert list(m) == [True, True, True, False, True] and (u == 1).all()
    assert np.allclose(paid[3:], [1 + 1.5 * 0.9, 1 + 3 * 0.9])


def test_the_tables_print_one_well_formed_row_per_period_model_and_ratio(capsys):
    t = field()
    t["ps"] = R43.halfway(t)
    for flat, cols in ((True, 12), (False, 15)):
        R43.rule_rows(t, R43.MODELS, flat=flat)
        out = [r for r in capsys.readouterr().out.splitlines() if r.startswith("| Feb")]
        assert len(out) == len(R43.PERIODS) * len(R43.MODELS) * len(R43.RATIOS)
        assert all(r.count("|") == cols + 1 for r in out), (flat, out[:2])
