import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "research", "greyhound"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import topaz_round76 as R76  # noqa: E402


def test_no_betwatch(monkeypatch, capsys):
    monkeypatch.delenv("BETWATCH_DIR", raising=False)
    assert R76.main("nowhere", "t") == 1
    assert "nothing to test" in capsys.readouterr().out


def test_the_sheet_needs_nothing_from_tab():
    # every sheet rule reads only our own chance (round 62's columns over TAB's field); none reads TAB's book
    assert set(R76.OWN.values()) == {"p_i_bet", "p_x_bet"}
    assert R76.SHEET_RATIOS[0] == 1.1 and max(R76.SHEET_RATIOS) == 2.0
