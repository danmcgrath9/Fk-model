"""Round 71: the fit pushed further, two ways, and averaged (topaz_round71)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round41 as R41  # noqa: E402
import topaz_round71 as R71  # noqa: E402


def test_the_settings_come_from_the_environment_with_defaults(monkeypatch):
    for k in ("R71_LR", "R71_ROUNDS", "R71_LEAVES", "R71_TAG"):
        monkeypatch.delenv(k, raising=False)
    assert R71.settings() == dict(lr=0.04, rounds=8000, leaves=15, tag="r71")
    monkeypatch.setenv("R71_LR", "0.06")
    monkeypatch.setenv("R71_ROUNDS", "4000")
    monkeypatch.setenv("R71_LEAVES", "31")
    monkeypatch.setenv("R71_TAG", "r71b")
    assert R71.settings() == dict(lr=0.06, rounds=4000, leaves=31, tag="r71b")


def test_the_walk_puts_round_41s_settings_back(monkeypatch):
    seen = {}

    def fake(R, X, q, use):
        seen.update(rounds=R41.MAX_ROUNDS, lr=R41.PARAMS["learning_rate"], leaves=R41.PARAMS["num_leaves"])
        raise RuntimeError("stop")

    before = (R41.MAX_ROUNDS, dict(R41.PARAMS))
    monkeypatch.setattr(R41, "walk_correction", fake)
    try:
        R71.walk_with(None, None, None, None, 0.04, 8000, 31)
    except RuntimeError:
        pass
    assert seen == dict(rounds=8000, lr=0.04, leaves=31)
    assert (R41.MAX_ROUNDS, R41.PARAMS) == before


def test_nothing_runs_without_betwatch(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("BETWATCH_DIR", raising=False)
    assert R71.main(str(tmp_path), "t") == 1
    assert "No Betwatch files" in capsys.readouterr().out
