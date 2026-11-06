"""research/greyhound/topaz_round20.py: track character and the dog's form by kind of track, earlier days only."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round20 as R20  # noqa: E402


def races():
    # three days at X 500 m, two dogs a race. Day 1: box 1 leads and wins by 2 lengths; day 2: box 8 wins from 4th,
    # by 1 length; day 3: the race being priced
    d = pd.to_datetime(["2026-01-01", "2026-01-01", "2026-01-08", "2026-01-08", "2026-01-15", "2026-01-15"])
    return pd.DataFrame({"race_id": [1, 1, 2, 2, 3, 3], "date": d, "track": "X", "distance": 500,
                         "dog": ["A", "B", "A", "B", "A", "B"], "box": [1, 2, 8, 1, 1, 8],
                         "finish": [1, 2, 1, 2, 1, 2], "margin": [0, 2.0, 0, 1.0, 0, 3.0],
                         "pir": ["11", "22", "41", "13", "1", "2"], "won": [1, 0, 1, 0, 1, 0],
                         "p_mkt": [0.6, 0.4, 0.3, 0.7, 0.5, 0.5]})


def test_track_character_by_hand(monkeypatch):
    monkeypatch.setattr(R20, "MIN_RACES", 1)
    out = R20.track_character(races())
    day3 = out[out.race_id == 3].iloc[0]
    assert day3.trk_lead_win == 0.5 and day3.trk_closer_win == 0.5      # one of two winners led, one came from 4th
    assert day3.trk_margin == 1.5                                       # (2 + 1) / 2 lengths
    assert day3.trk_inside == 1.0                                       # box 1-2 won 1 of 2, box 7-8 won 1 of 2
    assert np.isnan(out.trk_lead_win[0])                                # nothing before day 1
    assert out[out.race_id == 2].trk_lead_win.iloc[0] == 1.0            # only day 1 known on day 2


def test_dog_type_form_by_hand():
    df = races()
    df["trk_lead_win"] = [np.nan, np.nan, 0.6, 0.6, 0.3, 0.3]           # day 2 a speed track, day 3 not (cut 0.5)
    out = R20.dog_type_form(df, 0.5)
    a3 = out[(out.race_id == 3) & (out.dog == "A")].iloc[0]
    # A's only earlier run with a known kind is day 2, a speed track: won at 0.3, surprise +0.7. Day 3 is the other kind
    assert np.isnan(a3.dog_type_surprise) and a3.dog_type_runs == 0 and abs(a3.dog_other_surprise - 0.7) < 1e-12
    b3 = out[(out.race_id == 3) & (out.dog == "B")].iloc[0]
    assert abs(b3.dog_other_surprise - (0 - 0.7)) < 1e-12
