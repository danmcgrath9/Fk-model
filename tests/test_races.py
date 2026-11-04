"""greyhound/races.py: the race records' tips matched to runners by id, box or name; nothing from the result."""
import gzip
import json

import numpy as np
import pandas as pd

from greyhound import races as RC


def write(d, name, rows):
    with gzip.open(d / name, "wt", encoding="utf-8") as f:
        json.dump(rows, f)


def test_load_and_tip_features(tmp_path):
    write(tmp_path, "races_VIC_2024-03.json.gz", [
        {"raceId": 1, "analystComment": "Open race.", "tip1": 3, "tip2": 1, "tip3": None, "tip4": None, "suggestedBet": "3 to win"},
        {"raceId": 2, "analystComment": "", "tip1": 5005, "tip2": 5006},
        {"raceId": 3, "tip1": "FAST DOG", "tip2": "Slow Dog "},
        {"raceId": 4}, {"raceId": 1, "tip1": 3, "tip2": 1, "analystComment": "Open race.", "suggestedBet": "3 to win"}])   # a repeat keeps the last
    races = RC.load_races(tmp_path)
    assert len(races) == 4 and races.set_index("race_id").tips[1] == [3, 1] and races.set_index("race_id").tips[4] == []
    df = pd.DataFrame({"race_id": [1, 1, 1, 2, 2, 3, 3, 4, 9], "dog": [5001, 5002, 5003, 5005, 5006, 5007, 5008, 5009, 5010],
                       "box": [1, 2, 3, 1, 2, 1, 2, 1, 1],
                       "dog_name": ["A", "B", "C", "D", "E", "Fast Dog", "SLOW DOG", "H", "I"]})
    out, feats = RC.tip_features(df, races)
    assert feats == ["tip_rank", "race_tips", "analyst_len", "has_suggested", "tip_top"]
    # race 1: tips are boxes 3 then 1; race 2: dog ids; race 3: names; race 4: a record with no tips; race 9: no record
    assert out.tip_rank.tolist()[:3] == [2.0, 0.0, 1.0]
    assert out.tip_rank.tolist()[3:5] == [1.0, 2.0] and out.tip_rank.tolist()[5:7] == [1.0, 2.0]
    assert out.tip_rank.tolist()[7] == 0.0 and np.isnan(out.tip_rank.tolist()[8])
    assert out.race_tips.tolist()[:3] == [2.0] * 3 and out.race_tips.tolist()[7] == 0.0 and np.isnan(out.race_tips.iloc[8])
    assert out.analyst_len.iloc[0] == 10 and out.has_suggested.iloc[0] == 1.0 and out.has_suggested.iloc[3] == 0.0
    assert out.tip_top.tolist()[:3] == [0.0, 0.0, 1.0] and np.isnan(out.tip_top.iloc[8])


def test_no_records_at_all_gives_nan_everywhere(tmp_path):
    races = RC.load_races(tmp_path)
    out, _ = RC.tip_features(pd.DataFrame({"race_id": [1], "dog": [1], "box": [1]}), races)
    assert np.isnan(out.tip_rank.iloc[0]) and np.isnan(out.analyst_len.iloc[0])
