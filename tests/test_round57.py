"""Round 57: the card's bets by the blend's leans, and the blend with terms (topaz_round57)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round51 as R51  # noqa: E402
import topaz_round57 as R57  # noqa: E402


def test_the_terms_mark_their_groups():
    t = pd.DataFrame({"tip_rank": [1, 0, np.nan, 2], "box": [1, 2, 1, 8], "weight_change": [0.5, 0.4, np.nan, -1]})
    x = R57.term_columns(t)
    assert np.allclose(np.log(x.t_tip1), [1, 0, 0, 0]) and np.allclose(np.log(x.t_box1), [1, 0, 1, 0])
    assert np.allclose(np.log(x.t_wup), [1, 0, 0, 0])


def test_five_weights_are_recovered():
    # true chance: book^1.2 x 0.9 for a first tip x 0.95 for box 1, renormalised; nothing for the weight
    rng = np.random.default_rng(8)
    rows = []
    for r in range(6000):
        b = rng.dirichlet(np.full(6, 2.0))
        tip = np.zeros(6)
        tip[rng.integers(6)] = 1
        box = np.arange(1, 7)
        wch = rng.normal(0, 0.5, 6)
        true = b ** 1.2 * np.where(tip == 1, 0.9, 1.0) * np.where(box == 1, 0.95, 1.0)
        true /= true.sum()
        w = rng.choice(6, p=true)
        for i in range(6):
            rows.append(dict(race_id=r, won=int(i == w), n_later=0, book=b[i], ours=b[i], tip_rank=tip[i], box=box[i],
                             weight_change=wch[i], date=pd.Timestamp("2024-01-01") + pd.Timedelta(days=r % 180)))
    x = R57.term_columns(pd.DataFrame(rows))
    wb = R51.fit_weights(x, ["book", "t_tip1", "t_box1", "t_wup"], "2023-12-01", "2024-07-01")
    assert abs(wb[0] - 1.2) < 0.12
    assert abs(np.exp(wb[1]) - 0.9) < 0.06 and abs(np.exp(wb[2]) - 0.95) < 0.06 and abs(np.exp(wb[3]) - 1) < 0.06


def test_nothing_runs_without_both_named_walks(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("BETWATCH_DIR", str(tmp_path))
    monkeypatch.delenv("WALK_ISO_USE", raising=False)
    assert R57.main(str(tmp_path), "t") == 1
    assert "Both saved walks must be named" in capsys.readouterr().out
