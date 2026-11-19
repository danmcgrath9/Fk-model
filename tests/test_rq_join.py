"""research/harness/rq_join.py: Racing Queensland's file layout read as the shape probe showed it (a row with no horse
opens each race; times as m:ss.ss or ss.ss), speeds from distance over time, and history from earlier runs only."""
import sys
from pathlib import Path

import numpy as np, pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "research" / "harness"))
import rq_join as Q  # noqa: E402

COLS = ["Rank", "TAB", "Horse", "Driver", "TopSpeed", "LeadTimeST", "LeadTimeDT", "FirstHalfST", "FirstHalfDT",
        "LastHalfST", "LastHalfDT", "4thQuarterST", "4thQuarterDT", "1stQuarterRANK", "3rdQuarterRANK",
        "DistanceTravelled"]


def write(tmp, name, races):
    rows = []
    for race in races:
        rows.append({c: (np.nan if c not in ("LeadTimeST", "LastHalfST") else "0:57.00") for c in COLS})  # separator
        rows += race
    p = tmp / name
    pd.DataFrame(rows, columns=COLS).to_csv(p, index=False)
    return p


def horse(rank, tab, name, last_half="0:56.00", dist=2160.0, lead_t="0:31.00"):
    return {"Rank": rank, "TAB": tab, "Horse": name, "Driver": "D", "TopSpeed": 52.1, "LeadTimeST": lead_t,
            "LeadTimeDT": 403.0, "FirstHalfST": "1:00.50", "FirstHalfDT": 805.0, "LastHalfST": last_half,
            "LastHalfDT": 806.0, "4thQuarterST": "27.85", "4thQuarterDT": 404.0, "1stQuarterRANK": tab,
            "3rdQuarterRANK": rank, "DistanceTravelled": dist}


def test_secs():
    assert Q.secs("1:58.34") == 118.34 and Q.secs("27.85") == 27.85 and np.isnan(Q.secs("+9")) and np.isnan(Q.secs(None))


def test_parse_counts_races_from_separator_rows(tmp_path):
    p = write(tmp_path, "20261118_Albion_Park_H.csv",
              [[horse(1, 2, "Fast One"), horse(2, 1, "Slow Two", "0:58.00", 2180.0)], [horse(1, 1, "Third Horse")]])
    r = Q.parse_file(p)
    assert list(r.race_number) == [1, 1, 2] and set(r.track) == {"ALBIONPARK"} and r.name.iloc[0] == "FASTONE"
    assert r.t_last_half.iloc[0] == 56.0 and r.d_last_half.iloc[0] == 806.0 and r.t_q4.iloc[0] == 27.85
    f = Q.run_features(r)
    assert np.isclose(f.v_last_half.iloc[0], 806 / 56) and np.isclose(f.v_last_half_rel.iloc[0],
                                                                       806 / 56 - (806 / 56 + 806 / 58) / 2)
    assert f.extra_dist.iloc[1] == 20.0 and f.q1_pos.iloc[0] == 1.0          # TAB 2 of 2 at the first quarter


def test_history_uses_earlier_runs_only(tmp_path):
    a = write(tmp_path, "20261101_Redcliffe_H.csv", [[horse(1, 1, "Ace", "0:56.00"), horse(2, 2, "Bee")]])
    b = write(tmp_path, "20261108_Redcliffe_H.csv", [[horse(2, 1, "Ace", "0:59.00"), horse(1, 2, "Cee")]])
    h = Q.horse_history(Q.run_features(Q.load_dir(tmp_path))).set_index(["date", "name"])
    first, second = h.loc[(pd.Timestamp("2026-11-01"), "ACE")], h.loc[(pd.Timestamp("2026-11-08"), "ACE")]
    assert first.sec_runs == 0 and np.isnan(first.sec_last_v_last_half)
    assert second.sec_runs == 1 and np.isclose(second.sec_last_v_last_half, 806 / 56)   # not this run's 806/59
