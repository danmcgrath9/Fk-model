"""Round 53: calibration by tracking history (topaz_round53)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round53 as R53  # noqa: E402


def test_winners_against_the_chances_given():
    s = R53.ae(np.array([1, 0, 0, 1]), np.array([0.5, 0.5, 0.25, 0.25]))
    assert s["n"] == 4 and s["w"] == 2 and np.isclose(s["e"], 1.5) and np.isclose(s["ae"], 2 / 1.5)
    assert np.isclose(s["z"], 0.5 / np.sqrt(0.25 + 0.25 + 0.1875 + 0.1875))


def test_race_make_up():
    t = pd.DataFrame({"race_id": [1, 1, 2, 2, 3, 3], "iso_runs": [2, 1, 0, 3, np.nan, 0]})
    assert list(R53.make_up(t)) == ["every runner tracked"] * 2 + ["some tracked"] * 2 + ["none tracked"] * 2


def test_the_tables_print_on_a_small_field(capsys):
    rng = np.random.default_rng(7)
    rows = []
    for r in range(400):
        p = rng.dirichlet(np.ones(6))
        w = rng.choice(6, p=p)
        for i in range(6):
            rows.append(dict(race_id=r, won=int(i == w), iso_runs=float((i + r) % 3 == 0) if r % 4 else 1.0,
                             date=pd.Timestamp("2024-06-01") + pd.Timedelta(days=r * 2),
                             **{c: p[i] for c in R53.MODELS.values()}))
    t = pd.DataFrame(rows)
    mk = R53.make_up(t)
    R53.calibration(t, mk)
    R53.by_band(t, mk)
    R53.ll_make_up(t, mk)
    out = capsys.readouterr().out
    assert "| Feb 2025 on | some tracked | none | BSP |" in out and "| Feb 2025 on | every runner tracked |" in out
    assert "| May 2023 to Jan 2025 | none | ours, with Isolynx | under 3 |" in out


def test_nothing_runs_without_both_named_walks(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("BETWATCH_DIR", str(tmp_path))
    monkeypatch.delenv("WALK_ISO_USE", raising=False)
    assert R53.main(str(tmp_path), "t") == 1
    assert "Both saved walks must be named" in capsys.readouterr().out
