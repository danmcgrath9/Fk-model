"""research/greyhound/topaz_round14.py: the lead label and the trainer's runners, by hand."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round14 as R14  # noqa: E402


def test_lead_label_needs_exactly_one_leader_and_every_position():
    df = pd.DataFrame({"race_id": [1, 1, 1, 2, 2, 3, 3], "pir": ["123", "234", "312", "1", "1", "2", ""]})
    out = R14.lead_label(df)
    assert list(out.led[:3]) == [1.0, 0.0, 0.0] and out.one_leader[:3].all()
    assert not out.one_leader[3:5].any()                     # two dogs marked first: a dead heat or a typo, left out
    assert not out.one_leader[5:].any()                      # a dog with no in-running: the leader is unknown


def test_trainer_runners_rank_the_stable_by_time_rating():
    df = pd.DataFrame({"race_id": [1, 1, 1, 1], "trainer_id": [7, 7, 8, np.nan], "time_rating_mean5": [5.0, 9.0, 3.0, 1.0]})
    out = R14.stable_features(df)
    assert list(out.trainer_runners[:3]) == [2, 2, 1] and np.isnan(out.trainer_runners[3])
    assert list(out.trainer_rank[:3]) == [2, 1, 1]           # trainer 7's 9.0 dog is its elect
    assert list(out.stable_elect[:3]) == [0.0, 1.0, 0.0]     # a trainer's only runner is not an "elect"


def test_walk_lead_forward_fits_each_half_year_on_earlier_races_only(monkeypatch):
    import topaz_walk as W
    monkeypatch.setattr(W, "MIN_TRAIN_RACES", 1)
    dates = pd.to_datetime(["2024-02-01", "2024-02-01", "2024-08-01", "2024-08-01", "2025-02-01", "2025-02-01"])
    df = pd.DataFrame({"race_id": [1, 1, 2, 2, 3, 3], "date": dates, "box": [1, 2, 1, 2, 1, 2],
                       "pir": ["1", "2", "2", "1", "1", "2"], "track": "X", "grade": "5", "sex": "D"})
    seen = []

    class Stub:
        def predict(self, X, raw_score=True):
            return np.zeros(len(X))

    def fit(X, y, race, w, rounds):
        seen.append((race.max(), rounds))
        return Stub()
    out, n = W.lead_forward(df, ["box"], [], fit=fit, rounds=7)
    # three half-years: the first has nothing before it, the second fits on race 1, the third on races 1 and 2
    assert n == 2 and seen == [(1, 7), (2, 7)]
    assert out.p_lead[:2].isna().all() and (out.p_lead[2:] == 0.5).all() and (out.lead_rank[2:] == 1).all()
