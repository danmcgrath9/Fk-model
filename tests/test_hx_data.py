"""research/harness/hx_data.py: every history input uses earlier races only."""
import sys
from pathlib import Path
import numpy as np, pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "research" / "harness"))
import hx_data  # noqa: E402


def races(rows):
    df = pd.DataFrame(rows)
    df["start"] = pd.to_datetime(df.date)
    df["date"] = df.start
    df["won"] = df.pop("w"); df["placed"] = df.won
    df["WIN_INPLAY_MIN_PRICE_TAKEN"] = np.where(df.won == 1, 1.1, 5.0)
    df["WIN_INPLAY_MAX_PRICE_TAKEN"] = 20.0
    df["PLACE_BSP"] = 1.5
    df["field"] = df.groupby("race").horse.transform("size")
    df["p_bsp"] = df.p
    df["bsp_rank"] = df.groupby("race").p.rank(ascending=False)
    df["race_vol"], df["DISTANCE"], df["trot"], df["TRACK"] = 100.0, 2100.0, 0, "MELTON"
    return df


def test_history_uses_earlier_races_only():
    # horse 1 runs three times: chances 0.5, 0.25, 0.4 in fields of two; it wins the first only
    rows = []
    for i, (d, p1, w1) in enumerate((("2024-01-01", 0.5, 1), ("2024-01-08", 0.25, 0), ("2024-01-15", 0.4, 0))):
        rows += [dict(race=i, date=d, horse=1, TAB_NUMBER=1, p=p1, w=w1),
                 dict(race=i, date=d, horse=100 + i, TAB_NUMBER=2, p=1 - p1, w=1 - w1)]
    h = hx_data.history(races(rows)).set_index(["race", "horse"])
    assert np.isnan(h.loc[(0, 1), "mr_ewm"])                         # first run: no history
    assert h.loc[(1, 1), "mr_ewm"] == np.log(0.5 * 2)               # = 0: the first run's rating, not this one's
    # EWMA alpha 0.3 of [log(1.0), log(0.5)] = (0.7*0 + 1*log 0.5) / (0.7 + 1)
    assert np.isclose(h.loc[(2, 1), "mr_ewm"], np.log(0.5) / 1.7)
    assert h.loc[(1, 1), "wins_prev"] == 1 and h.loc[(2, 1), "wins_prev"] == 1
    # the draw at MELTON, pacers, TAB 1: no earlier race at the first meeting; one win from one run at the second
    assert h.loc[(0, 1), "draw_runs"] == 0
    assert h.loc[(1, 1), "draw_runs"] == 1 and np.isclose(h.loc[(1, 1), "draw_win_rate"], (1 + 1) / (1 + 10))
    assert np.isclose(h.loc[(2, 1), "draw_win_rate"], (1 + 1) / (2 + 10))


def test_v3_inputs_use_earlier_races_only():
    rows = []
    for i, (d, p1, w1) in enumerate((("2024-01-01", 0.5, 1), ("2024-01-08", 0.25, 0), ("2024-01-15", 0.4, 0))):
        rows += [dict(race=i, date=d, horse=1, TAB_NUMBER=1, p=p1, w=w1),
                 dict(race=i, date=d, horse=100 + i, TAB_NUMBER=2, p=1 - p1, w=1 - w1)]
    h = hx_data.history(races(rows)).set_index(["race", "horse"])
    assert np.isnan(h.loc[(0, 1), "track_mr"]) and h.loc[(0, 1), "track_runs"] == 0
    assert h.loc[(1, 1), "track_mr"] == 0 and h.loc[(2, 1), "track_runs"] == 2   # same track every time
    # place chance in a field of two (2 places paid): both runners at place BSP 1.5 -> 1 each, capped at 0.99
    assert np.isclose(h.loc[(1, 1), "p_place_ewm"], 0.99)
