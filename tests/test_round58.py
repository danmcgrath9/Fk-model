"""Round 58: BSP corrected for its first-tip lean (topaz_round58)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round57 as R57  # noqa: E402
import topaz_round58 as R58  # noqa: E402


def field(n=12000, seed=9):
    # BSP over-rates the first tip: the true chance is BSP's x 0.9 for it, renormalised
    rng = np.random.default_rng(seed)
    rows = []
    for r in range(n):
        q = rng.dirichlet(np.full(6, 2.0))
        tip = np.zeros(6)
        tip[rng.integers(6)] = 1
        true = q * np.where(tip == 1, 0.9, 1.0)
        true /= true.sum()
        w = rng.choice(6, p=true)
        for i in range(6):
            rows.append(dict(race_id=r, won=int(i == w), n_later=0, p_bsp=q[i], tip_rank=tip[i], box=i + 1,
                             weight_change=rng.choice([0.0, 0.6]), date=pd.Timestamp("2023-06-01")
                             + pd.Timedelta(days=r // 10)))
    t = R57.term_columns(pd.DataFrame(rows))
    t.loc[(t.race_id == 7) & (t.box == 1), "p_bsp"] = np.nan        # one race without a BSP on every runner
    return t


def test_the_correction_is_fitted_on_one_half_and_applied_to_the_other():
    t = field()
    q, w = R58.corrected_bsp(t)
    assert set(w) == {"May 2023 to Jan 2025", "Feb 2025 on"}
    for v in w.values():
        assert abs(v[0] - 1) < 0.1 and abs(np.exp(v[1]) - 0.9) < 0.06 and abs(np.exp(v[2]) - 1) < 0.06
    assert q[t.race_id == 7].isna().all()
    s = q.groupby(t.race_id).sum()
    assert np.allclose(s.drop(7), 1)


def test_nothing_runs_without_both_named_walks(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("BETWATCH_DIR", str(tmp_path))
    monkeypatch.delenv("WALK_ISO_USE", raising=False)
    assert R58.main(str(tmp_path), "t") == 1
    assert "Both saved walks must be named" in capsys.readouterr().out
