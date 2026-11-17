"""Round 70: the longer fit, let run further (topaz_round70)."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round70 as R70  # noqa: E402


def test_the_faster_walk_runs_at_its_own_rate_and_puts_the_settings_back(monkeypatch):
    seen = {}

    def fake(R, X, q, use):
        seen.update(rate=R70.R41.PARAMS["learning_rate"], rounds=R70.R41.MAX_ROUNDS)
        raise RuntimeError("stop")

    old_rate, old_rounds = R70.R41.PARAMS["learning_rate"], R70.R41.MAX_ROUNDS
    monkeypatch.setattr(R70.R41, "walk_correction", fake)
    with pytest.raises(RuntimeError):
        R70.walk_faster(None, None, None, None)
    assert seen == {"rate": 0.04, "rounds": 4000}
    assert (R70.R41.PARAMS["learning_rate"], R70.R41.MAX_ROUNDS) == (old_rate, old_rounds)


def test_a_saved_model_lines_up_on_the_rows_by_race_and_dog():
    # race 1: a and b saved at 0.6 and 0.2 (the chance times the book's sum): their shares are 0.75 and 0.25
    t = pd.DataFrame({"race_id": [1, 1], "dog": ["a", "b"], "c": [0.6, 0.2]})
    R = pd.DataFrame({"race_id": [1, 1, 2], "dog": ["b", "a", "c"]})
    v = R70.on_runners(R, t, "c")
    assert np.allclose(v[:2], [0.25, 0.75]) and np.isnan(v[2])


def test_nothing_runs_without_betwatch(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("BETWATCH_DIR", raising=False)
    assert R70.main(str(tmp_path), "t") == 1
    assert "No Betwatch files" in capsys.readouterr().out
