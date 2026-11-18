import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "research", "greyhound"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import topaz_round79 as R79  # noqa: E402


def test_live_inputs_drop_only_the_bsp_based_history():
    inputs = ["lp_tab", "lp_ours", "gap", "dog_mv_last", "dog_mv_mean5", "trainer_mv", "trainer_mv_n",
              "mh_steam5", "mh_drift5", "mh_tr90_mv", "mh_tab_last", "mh_first_mean5", "mh_books_last", "mkt_lsp_mean5"]
    keep, drop = R79.live_inputs(inputs)
    assert drop == ["dog_mv_last", "dog_mv_mean5", "trainer_mv", "trainer_mv_n", "mh_steam5", "mh_drift5", "mh_tr90_mv"]
    # TAB's own moves, the other books' opening prices and the dog's past starting prices are known on the morning
    assert keep == ["lp_tab", "lp_ours", "gap", "mh_tab_last", "mh_first_mean5", "mh_books_last", "mkt_lsp_mean5"]


def test_no_betwatch(monkeypatch, capsys):
    monkeypatch.delenv("BETWATCH_DIR", raising=False)
    assert R79.main("nowhere", "t") == 1
    assert "nothing to test" in capsys.readouterr().out
