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
