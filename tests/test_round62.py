"""Round 62: the blend corrected for its own mistakes (topaz_round62)."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round57 as R57  # noqa: E402
import topaz_round62 as R62  # noqa: E402


def test_the_bsp_label_is_fitted_before_february_2025_and_applied_everywhere():
    rng = np.random.default_rng(3)
    rows = []
    for r in range(8000):
        q = rng.dirichlet(np.full(6, 2.0))
        tip = np.zeros(6)
        tip[rng.integers(6)] = 1
        true = q * np.where(tip == 1, 0.9, 1.0)
        true /= true.sum()
        w = rng.choice(6, p=true)
        for i in range(6):
            rows.append(dict(race_id=r, won=int(i == w), n_later=0, p_bsp=q[i], tip_rank=tip[i],
                             weight_change=rng.choice([0.0, 0.6]),
                             date=pd.Timestamp("2023-06-01") + pd.Timedelta(days=r // 6)))
    R = R57.term_columns(pd.DataFrame(rows))
    R.loc[(R.race_id == 5) & (R.tip_rank == 1), "p_bsp"] = np.nan
    q, full, w = R62.bsp_label(R, *R62.LABEL_FIT)
    assert abs(np.exp(w[1]) - 0.9) < 0.06 and not full[(R.race_id == 5).values].any()
    late = (R.date >= "2025-02-01").values & full
    assert late.any() and np.allclose(pd.Series(q[late]).groupby(R.race_id.values[late]).sum(), 1)
    assert (q[~full] == 0).all()


def test_the_corrections_are_read_back_from_the_walk_cache(tmp_path, monkeypatch, capsys):
    x = pd.DataFrame({"race_id": [1, 1, 1], "dog": ["a", "b", "c"], "is_ran": [True, True, False],
                      "h_p_i_bet": [0.6, 0.3, 0.1]})
    pd.DataFrame({"race_id": [1, 1], "dog": ["a", "b"], "c_w": [0.55, 0.45], "c_q": [0.5, 0.5]}).to_csv(
        tmp_path / "corr_r62.csv.gz", index=False)
    (tmp_path / "corr_r62.json").write_text(json.dumps(["saved"]))
    monkeypatch.setenv("WALK_CACHE_DIR", str(tmp_path))
    out = R62.corrections(x, None, None, 0.0)
    assert list(out.c_w) == [0.55, 0.45, 0.1] and list(out.c_q) == [0.5, 0.5, 0.1]
    assert "saved" in capsys.readouterr().out


def test_nothing_runs_without_both_named_walks(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("BETWATCH_DIR", str(tmp_path))
    monkeypatch.delenv("WALK_ISO_USE", raising=False)
    assert R62.main(str(tmp_path), "t") == 1
    assert "Both saved walks must be named" in capsys.readouterr().out
