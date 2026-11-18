"""research/harness/bw_data.py: Betwatch rows read as written, the Betfair join by id only, and driver/trainer/barrier
form from earlier races only. Made-up races; no Betwatch data is in this repository."""
import sys
from pathlib import Path

import numpy as np, pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "research" / "harness"))
import bw_data as W  # noqa: E402


def test_market_id_and_ints():
    assert W.bf_market("1.234567890") == 234567890          # Betfair's files store the digits after "1."
    assert W.bf_market("234567890") == 234567890
    assert W.bf_market(None) is None and W.bf_market("2.123") is None and W.bf_market("") is None
    assert W.as_int("7") == 7 and W.as_int(None) is None and W.as_int("SR1") is None


def test_positions_read_every_shape_and_refuse_the_rest():
    assert W.positions([[3], [5, 7], [1]]) == {3: 1, 5: 2, 7: 2, 1: 3}   # dead heat for second
    assert W.positions([3, 5, 1]) == {3: 1, 5: 2, 1: 3}
    assert W.positions("3,5,1") == {3: 1, 5: 2, 1: 3} == W.positions("3-5-1")
    assert W.positions([{"x": 1}]) == {} and W.positions(None) == {} and W.positions({"a": 1}) == {}


def bw_race(start="2026-02-01T09:00:00Z", flucs=((5.0, "2026-02-01T00:00:00Z"), (4.0, "2026-02-01T08:30:00Z"),
                                                 (3.5, "2026-02-01T09:05:00Z"))):
    return {"id": "bw1", "date": "2026-02-01", "track": "Melton", "location": "VIC", "betfair_win": "1.555",
            "start": start, "distance": 2240, "class": "NR 50 to 55", "track_condition": "Good",
            "results": [[2], [1]],
            "runners": [{"number": 1, "barrier": 4, "betfair_id": "11", "rider": " a driver ", "trainer": "T One",
                         "scratched": None, "emergency": False, "books": {"Tab": {"flucs": [list(f) for f in flucs]}}},
                        {"number": 2, "barrier": 1, "betfair_id": "22", "rider": None, "trainer": "T Two",
                         "scratched": None, "emergency": False, "books": {}}]}


def test_runner_rows_first_price_and_last_before_the_start():
    a, b = W.runner_rows(bw_race())
    assert a["race_bw_bf"] == 555 and a["horse_bw"] == 11 and a["driver"] == "A DRIVER"
    assert a["tab_open"] == 5.0 and a["tab_open_hours"] == 9.0      # first price 9 hours before the 09:00 start
    assert a["tab_last"] == 4.0                                     # the 09:05 change is after the start
    assert a["tab_n"] == 3 and a["bw_pos"] == 2 and b["bw_pos"] == 1
    assert np.isnan(b["tab_open"]) and b["driver"] is None          # no TAB price, no driver: missing, not guessed


def bf_rows():
    return pd.DataFrame({"race": [555, 555, 999], "horse": [11, 22, 11], "won": [0, 1, 1], "TAB_NUMBER": [1, 2, 1],
                         "date": pd.to_datetime(["2026-02-01"] * 3), "STATE_CODE": ["VIC"] * 3})


def test_join_by_ids_only():
    bw = pd.DataFrame(W.runner_rows(bw_race()))
    df, c = W.join(bf_rows(), bw)
    df = df.set_index(["race", "horse"])
    assert df.loc[(555, 11), "driver"] == "A DRIVER" and df.loc[(555, 22), "trainer"] == "T TWO"
    assert pd.isna(df.loc[(999, 11), "bw_race"])                    # same horse, other race: not joined
    assert c["bf_au_runners_joined"] == 2 and c["bf_au_runners_in_span"] == 3
    assert c["winner_agree"] == 1 and c["winner_checks"] == 1 and c["tab_number_agree"] == 1.0


def people_frame():
    # driver D drives horse 1 in three races a week apart; wins the first only. Fields of two, each at chance 0.5.
    rows = []
    for i, w in enumerate((1, 0, 0)):
        d = pd.Timestamp("2026-01-01") + pd.Timedelta(days=7 * i)
        rows += [dict(race=i, horse=1, start=d, won=w, p_bsp=0.5, driver="D", trainer="T", barrier=1, field=2,
                      TRACK="MELTON", trot=0, tab_open=2.0, tab_last=2.0, track_condition="Good", **{"class": "NR 50"}),
                 dict(race=i, horse=100 + i, start=d, won=1 - w, p_bsp=0.5, driver="E", trainer="U", barrier=2,
                      field=2, TRACK="MELTON", trot=0, tab_open=2.0, tab_last=np.nan, track_condition=None,
                      **{"class": "NR 50"})]
    return pd.DataFrame(rows)


def test_driver_form_uses_earlier_races_only():
    h = W.add_people(people_frame()).set_index(["race", "horse"])
    assert h.loc[(0, 1), "driver_runs"] == 0 and h.loc[(0, 1), "driver_resid"] == 0
    assert h.loc[(1, 1), "driver_runs"] == 1
    assert np.isclose(h.loc[(1, 1), "driver_resid"], 0.5 / (1 + 30))             # one win at chance 0.5, shrunk
    assert np.isclose(h.loc[(2, 1), "driver_resid"], (0.5 - 0.5) / (2 + 30))     # then a loss at 0.5
    assert np.isclose(h.loc[(1, 1), "driver_win_rate"], (1 + 1) / (1 + 10))
    assert h.loc[(1, 1), "driver_change"] == 0                                   # same driver as last start
    assert h.loc[(0, 1), "bar_runs"] == 0 and h.loc[(2, 1), "bar_runs"] == 2
    assert h.loc[(0, 1), "class_num"] == 50 and h.loc[(0, 100), "cond"] == "none"


def test_tab_chances_only_where_every_runner_has_a_price():
    h = W.add_people(people_frame())
    assert np.allclose(h.p_tab_open, 0.5)                    # both runners at 2.0
    assert h.p_tab_last.isna().all()                         # one runner has no last price: the race gets none
