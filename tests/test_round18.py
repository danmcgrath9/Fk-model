"""research/greyhound/topaz_round18.py: the Isolynx input split and the lead model's hit rate, by hand."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round18 as R18  # noqa: E402


def test_split_inputs_takes_every_isolynx_column_out_of_both_lists():
    (n0, r0), (n1, r1), iso = R18.split_inputs(["box", "iso_jump_time_last", "iso_runs"], ["box", "iso_t50_m3"])
    assert n0 == ["box"] and r0 == ["box"] and iso == ["iso_jump_time_last", "iso_runs"]
    assert n1 == ["box", "iso_jump_time_last", "iso_runs"] and r1 == ["box", "iso_t50_m3"]


def test_lead_hits_by_hand():
    # race 1: the top pick led; race 2: the top pick did not; race 3: two leaders marked, not a one-leader race
    t = pd.DataFrame({"race_id": [1, 1, 2, 2, 3, 3], "led": [1, 0, 0, 1, 1, 1],
                      "one_leader": [True, True, True, True, False, False], "rank": [1, 2, 1, 2, 1, 2]})
    races, rate = R18.lead_hits(t, "rank")
    assert races == 2 and rate == 0.5
    assert np.isnan(R18.lead_hits(t[t.race_id == 3], "rank")[1])


def test_check_features_use_only_earlier_days(tmp_path):
    import gzip
    import json

    def run(race, day, dip_speed, pos_after):
        sp = [{"splitDistance": d, "splitSpeed": v, "positionInRunning": p} for d, v, p in
              ((50, 14, 2), (100, 16.5, 2), (150, 17, 2), (200, dip_speed, pos_after), (250, 17, pos_after),
               (300, 17, pos_after), (350, 16.5, pos_after), (400, 16, pos_after))]
        return {"raceId": race, "dogId": 7, "raceDate": day, "venueCode": "MEP", "raceDistance": 400,
                "runnerSplitsFromStart50": sp}
    # 1 Mar: checked (dip to 15, 2nd to 5th); 8 Mar: clean
    payload = [{"dogId": 7, "runs": [run(1, "2026-03-01", 15.0, 5), run(2, "2026-03-08", 17.0, 2)]}]
    with gzip.open(tmp_path / "isolynx_dogs_0000.json.gz", "wt") as fh:
        json.dump(payload, fh)
    df = pd.DataFrame({"dog": ["7", "7", "7"], "date": pd.to_datetime(["2026-03-01", "2026-03-05", "2026-03-10"])})
    out, cols, share = R18.check_features(df, str(tmp_path))
    assert cols == R18.CHECK_COLS and share == 0.5
    assert np.isnan(out.chk_last[0])                                  # its own day is not known yet
    assert out.chk_last[1] == 1 and out.chk_lost_last[1] == 3 and abs(out.chk_dip_last[1] - (15.0 - 17.0)) < 1e-12
    assert out.chk_last[2] == 0 and out.chk_rate5[2] == 0.5            # one of its two tracked runs was checked
