"""Round 54: the blend with a term for the tracked dogs (topaz_round54)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round51 as R51  # noqa: E402
import topaz_round54 as R54  # noqa: E402


def test_the_term_is_one_for_a_tracked_runner_and_zero_otherwise():
    v = R54.tracked_term(pd.Series([2.0, 0.0, np.nan, 1.0]))
    assert np.allclose(np.log(v), [1, 0, 0, 1])


def test_the_fit_finds_a_lean_against_the_tracked_dogs():
    # the book under-rates tracked dogs in mixed races: true chance = book x e^0.3 for them, renormalised
    rng = np.random.default_rng(11)
    rows = []
    for r in range(3000):
        b = rng.dirichlet(np.full(6, 2.0))
        trk = rng.random(6) < 0.5
        true = b * np.where(trk, np.exp(0.3), 1.0)
        true /= true.sum()
        w = rng.choice(6, p=true)
        for i in range(6):
            rows.append(dict(race_id=r, won=int(i == w), n_later=0, book=b[i], iso_runs=float(trk[i]),
                             date=pd.Timestamp("2024-01-01") + pd.Timedelta(days=r % 180)))
    x = pd.DataFrame(rows)
    x["trk"] = R54.tracked_term(x.iso_runs)
    wb = R51.fit_weights(x, ["book", "trk"], "2023-12-01", "2024-07-01")
    assert abs(wb[0] - 1) < 0.15 and 0.15 < wb[1] < 0.45


def test_nothing_runs_without_both_named_walks(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("BETWATCH_DIR", str(tmp_path))
    monkeypatch.delenv("WALK_ISO_USE", raising=False)
    assert R54.main(str(tmp_path), "t") == 1
    assert "Both saved walks must be named" in capsys.readouterr().out
