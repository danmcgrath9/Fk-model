import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "research", "greyhound"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import topaz_lines as L  # noqa: E402


def test_comment_tokens_letters_only():
    got = L.comment_tokens(pd.Series(["SAW,CRD1", "chk 3 wide", None]))
    assert list(got) == [["SAW", "CRD"], ["CHK", "WIDE"], []]


def test_race_map_by_hand():
    # one race, box 3 vacant. box 1: wide (+1.0 m) and quickest (5); box 2: a railer (-1.0 m), slowest (3);
    # box 4: middle (0.0 m), speed 4
    df = pd.DataFrame({"race_id": [7, 7, 7], "box": [1, 2, 4], "line_any": [1.0, -1.0, 0.0],
                       "split_rating_mean5": [5.0, 3.0, 4.0]})
    m = L.race_map(df)
    # line ranks (railer first): box 1 -> 3, box 2 -> 1, box 4 -> 2; clash = line rank - box rank
    assert list(m.clash) == [2.0, -1.0, -1.0] and list(m.clash_share) == [1.0, -0.5, -0.5]
    # gaps: the rail inside box 1 (1), box 1 to box 2 (1), box 2 to box 4 (2: box 3 is vacant), room outside box 4 (5)
    assert list(m.nb_in_gap) == [1.0, 1.0, 2.0] and list(m.nb_out_gap) == [1.0, 2.0, 5.0]
    # box 1's outside neighbour runs 2 m closer to the rail (converge_out 2) but is slower, so it is not squeezed;
    # box 2 has the quicker wide runner inside it coming out across it: converge_in 2, gap 1 -> squeeze 2
    assert m.converge_out.iloc[0] == 2.0 and m["squeeze"].iloc[0] == 0.0 and m["squeeze"].iloc[1] == 2.0
    # box 2: one quicker dog inside runs wider (crossers_in 1); box 4 outside it is quicker but not closer to the rail
    assert m.crossers_in.iloc[1] == 1 and m.crossers_out.iloc[1] == 0 and m.contention.iloc[1] == 0
    # slow_clash: early-speed rank share x clash (box 1 is quickest: 1/3 x 2)
    assert np.isclose(m.slow_clash.iloc[0], 2 / 3) and m.slow_clash.iloc[1] == 0.0


def test_comment_history_is_from_earlier_days_only():
    df = pd.DataFrame({"dog": ["a", "a", "a"], "date": pd.to_datetime(["2025-01-01", "2025-01-08", "2025-01-15"]),
                       "race_id": [1, 2, 3], "box": [1, 1, 1], "comment": ["SAW", "", "SAW"],
                       "split_rating_mean5": [1.0, 1.0, 1.0]})
    out, feats, _ = L.add_lines(df)
    # day 1 has no earlier run; day 2 sees day 1's SAW; day 3 sees days 1 and 2 (one of two): its own SAW is not seen
    assert "tk_SAW" in feats
    assert np.isnan(out.tk_SAW.iloc[0]) and out.tk_SAW.iloc[1] == 1.0 and out.tk_SAW.iloc[2] == 0.5


def test_code_metres_needs_enough_tracked_runs(monkeypatch):
    monkeypatch.setattr(L, "CODE_MIN_TRACKED", 2)
    runs = pd.DataFrame({"date": pd.to_datetime(["2024-01-01"] * 4 + ["2026-01-01"])})
    codes = pd.Series(["W", "W", "R", "M", "W"])
    resid = pd.Series([1.0, 2.0, -1.0, 0.0, 9.0])
    # W: 1.0 and 2.0 before the cut (the 2026 run is after it) -> 1.5; R and M have one tracked run each -> left out
    assert L.code_metres(runs, codes, resid, "2025-02-01") == {"W": 1.5}
