"""Round 47: the edge map (topaz_round47)."""
import gzip
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round47 as R47  # noqa: E402


def test_tabs_first_price_time_is_the_earliest_tab_fluc_before_the_start(tmp_path):
    r = {"id": "r1", "start": "2026-03-01T10:00:00Z", "runners": [
        {"books": {"Tab": {"flucs": [[3.0, "2026-02-28T22:00:00Z"], [2.8, "2026-03-01T02:00:00Z"]]},
                   "Sportsbet": {"flucs": [[3.1, "2026-02-28T20:00:00Z"]]}}},
        {"books": {"Tab": {"flucs": [[5.0, "2026-02-28T21:30:00Z"], [1.0, "2026-02-28T20:00:00Z"]]}}},
        {"books": {"Tab": {"flucs": [[9.0, "2026-03-01T11:00:00Z"]]}}}]}
    rt = R47.race_times(r)
    assert rt["bw_race"] == "r1" and rt["start_t"] - rt["open_t"] == 12.5 * 3600   # 21:30, not the $1 or Sportsbet
    with gzip.open(tmp_path / "betwatch_VIC_G_2026-03.json.gz", "wt", encoding="utf-8") as fh:
        json.dump({"races": [r, r]}, fh)
    ot = R47.open_times(str(tmp_path))
    assert len(ot) == 1
    h = R47.mel_hour(pd.Series([rt["open_t"], np.nan]))
    assert h.iloc[0] == 8 and np.isnan(h.iloc[1])                       # 21:30 UTC is 8:30am in Melbourne (AEDT)


def test_bands_label_every_runner_and_keep_their_order():
    lab, order = R47.cut(pd.Series([1.0, 3.0, np.nan, 99.0]), [0, 2, 5], ["low", "high"])
    assert list(lab) == ["low", "high", "unknown", "unknown"] and order == ["low", "high", "unknown"]


def field(n=40):
    rng = np.random.default_rng(1)
    t = pd.DataFrame({"race_id": np.repeat(np.arange(n // 4), 4), "date": pd.to_datetime("2025-06-01")
                      + pd.to_timedelta(np.repeat(np.arange(n // 4), 4) * 40, unit="D"),
                      "track": rng.choice(["SAN", "HVL", "BEN"], n), "distance": rng.choice([300, 400, 500, 600], n),
                      "race_class": rng.choice([3, 5, 6, 8, np.nan], n), "box": rng.integers(1, 9, n).astype(float),
                      "pb6": rng.uniform(0.08, 0.4, n), "price": rng.uniform(2, 14, n), "p_book": 0.25,
                      "n_bet": 8, "n_later": rng.integers(0, 2, n), "tab_book": 1.2, "to_jump": 10.0,
                      "open_hour": 8.0, "start_hour": 20.0, "won": rng.integers(0, 2, n), "ded": 0.0,
                      "p_bsp": rng.uniform(0.05, 0.4, n)})
    return t


def test_every_slice_labels_every_runner_with_a_listed_value():
    t = field()
    for name, (lab, order) in R47.slices(t).items():
        assert len(lab) == len(t) and set(lab.unique()) <= set(order), name


def test_the_table_is_well_formed(capsys):
    R47.table(field(400))
    out = [r for r in capsys.readouterr().out.splitlines() if r.startswith("| ") and "---" not in r][1:]
    assert out and all(r.count("|") == 14 for r in out), out[:2]
