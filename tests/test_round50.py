"""Round 50: Isolynx in ours, walked forward (topaz_round50)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round50 as R50  # noqa: E402


def test_nothing_runs_without_betwatch_or_the_isolynx_pull(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("BETWATCH_DIR", raising=False)
    assert R50.main(str(tmp_path), "t") == 1
    monkeypatch.setenv("BETWATCH_DIR", str(tmp_path))
    monkeypatch.delenv("ISOLYNX_DIR", raising=False)
    assert R50.main(str(tmp_path), "t") == 1
    assert "No Isolynx pull" in capsys.readouterr().out


def test_log_loss_reads_the_winners_chances():
    g = pd.DataFrame({"p": [0.5, 0.25, 0.0]})
    assert np.isclose(R50.ll(g, "p"), (np.log(2) + np.log(4) - np.log(1e-9)) / 3)


def test_the_periods_cover_the_betwatch_years_and_the_card_window():
    assert R50.PERIODS[0][1] == R50.BW_FROM and R50.PERIODS[-1] == ("Feb 2025 on", "2025-02-01", None)
    assert R50.FIXED == (0.54, 0.67) and R50.FIRST == "2022-11"
