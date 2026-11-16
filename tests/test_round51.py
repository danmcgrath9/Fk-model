"""Round 51: the blend refitted for ours with Isolynx (topaz_round51)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round51 as R51  # noqa: E402


def races(n=600, k=6, seed=3):
    """Races where the winner is drawn from 'a' alone; 'b' is noise."""
    rng = np.random.default_rng(seed)
    rows = []
    for r in range(n):
        a = rng.dirichlet(np.ones(k))
        b = rng.dirichlet(np.ones(k))
        w = rng.choice(k, p=a)
        for i in range(k):
            rows.append(dict(race_id=r, a=a[i], b=b[i], won=int(i == w), n_later=0,
                             date=pd.Timestamp("2024-01-01") + pd.Timedelta(days=r % 150)))
    return pd.DataFrame(rows)


def test_the_fit_finds_the_input_that_knows_and_ignores_the_window_outside():
    x = races()
    wb = R51.fit_weights(x, ["a", "b"], "2023-12-01", "2024-07-01")
    assert abs(wb[0] - 1) < 0.25 and abs(wb[1]) < 0.25
    x.loc[x.date >= "2024-04-01", "n_later"] = 1      # scratched after the open: left out of the fit
    assert np.allclose(R51.fit_weights(x, ["a", "b"], "2023-12-01", "2024-07-01"),
                       R51.fit_weights(x[x.date < "2024-04-01"], ["a", "b"], "2023-12-01", "2024-07-01"))


def test_applying_weights_sums_to_one_a_race_and_skips_unpriced_rows():
    x = races(n=5)
    x.loc[x.race_id == 4, "b"] = np.nan
    p = R51.apply_weights(x, ["a", "b"], (1.0, 0.0))
    assert p[x.race_id == 4].isna().all()
    s = p.groupby(x.race_id).sum()
    assert np.allclose(s[s.index < 4], 1)
    assert np.allclose(p[x.race_id < 4], x.a[x.race_id < 4])   # all weight on a: a itself


def test_nothing_runs_without_betwatch_or_both_named_walks(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("BETWATCH_DIR", raising=False)
    assert R51.main(str(tmp_path), "t") == 1
    monkeypatch.setenv("BETWATCH_DIR", str(tmp_path))
    monkeypatch.setenv("WALK_CACHE_USE", "abc")
    monkeypatch.delenv("WALK_ISO_USE", raising=False)
    assert R51.main(str(tmp_path), "t") == 1
    assert "Both saved walks must be named" in capsys.readouterr().out


def test_the_windows():
    assert R51.FIT == ("2023-12-01", "2024-07-01") and R51.RECENT_FIT == ("2025-02-01", "2026-02-01")
    assert R51.RECENT == [("Feb 2026 on", "2026-02-01", None)]
