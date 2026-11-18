import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "research", "greyhound"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import topaz_round78 as R78  # noqa: E402


def test_needs_the_data(monkeypatch, capsys):
    monkeypatch.delenv("BETWATCH_DIR", raising=False)
    assert R78.main("nowhere", "t") == 1
    assert "nothing to test" in capsys.readouterr().out


def test_needs_round_77s_walk(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("BETWATCH_DIR", str(tmp_path))
    monkeypatch.setenv("ISOLYNX_DIR", str(tmp_path))
    monkeypatch.delenv("WALK_LINES_USE", raising=False)
    assert R78.main("nowhere", "t") == 1
    assert "WALK_LINES_USE" in capsys.readouterr().out
