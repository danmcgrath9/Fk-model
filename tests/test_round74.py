import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "research", "greyhound"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import topaz_round32 as R32  # noqa: E402
import topaz_round74 as R74  # noqa: E402


def mel(hhmm: str, day: str = "2026-11-18") -> str:
    return f"{day}T{hhmm}:00+11:00"          # November is daylight time in Melbourne, UTC+11


def test_noon_and_clock():
    # midday on 18 Nov 2026 in Melbourne is 01:00 UTC; in June (standard time, UTC+10) it is 02:00 UTC
    assert R74.noon_of("2026-11-18") == R32.ts("2026-11-18T01:00:00Z")
    assert R74.noon_of("2026-06-18") == R32.ts("2026-06-18T02:00:00Z")
    assert np.isnan(R74.noon_of("not a date"))
    assert R74.clock(R32.ts(mel("13:30"))) == 13.5
    assert R74.hhmm(9.999) == "10:00" and R74.hhmm(7.25) == "07:15"


def test_is_metro():
    # 19 Nov 2026 is a Thursday, 21 Nov a Saturday
    assert R74.is_metro("Sandown Park", R32.ts(mel("18:40", "2026-11-19")))
    assert not R74.is_metro("Sandown Park", R32.ts(mel("18:40", "2026-11-21")))     # Sandown on a Saturday
    assert R74.is_metro("The Meadows", R32.ts(mel("19:05", "2026-11-21")))
    assert not R74.is_metro("The Meadows", R32.ts(mel("12:05", "2026-11-21")))      # a day meeting
    assert not R74.is_metro("Warragul", R32.ts(mel("19:05", "2026-11-19")))


def race(start, flucs_a, flucs_b, scratched_c=None, flucs_c=((10.0, "09:15"),)):
    tab = lambda fl: {"Tab": {"flucs": [[p, mel(h)] for p, h in fl]}}       # noqa: E731
    return {"date": "2026-11-18", "track": "Warragul", "start": mel(start), "runners": [
        {"name": "A", "books": tab(flucs_a)}, {"name": "B", "books": tab(flucs_b)},
        {"name": "C", "scratched": mel(scratched_c) if scratched_c else None, "books": tab(flucs_c)}]}


def test_race_rows_at_midday():
    # TAB opens 09:00; at midday A stands at $3.00 (its 13:00 move is later) and B at $5.00 (moved at 11:00).
    # C is scratched at 15:00, after midday, at $10: deduction 100 // 10 = 10c
    r = race("19:00", [(3.0, "09:00"), (2.8, "13:00")], [(4.0, "09:30"), (5.0, "11:00")], scratched_c="15:00")
    rows = R74.race_rows(r, R32.ts(mel("18:30")))
    assert [x["dog_raw"] for x in rows] == ["A", "B"]
    assert [x["lim_price"] for x in rows] == [3.0, 5.0]
    assert rows[0]["lim_ded"] == 0.10 and rows[0]["bwl_late"] and not rows[0]["bwl_metro"]
    assert rows[0]["lim_t"] == R74.noon_of("2026-11-18") and rows[0]["bwl_open"] == R32.ts(mel("09:00"))


def test_race_rows_open_after_midday_and_day_meetings():
    # TAB opens at 13:00, after midday: the limit's moment is the open itself, so A's first price $3.00 stands
    r = race("19:00", [(3.0, "13:00"), (2.8, "14:00")], [(4.0, "13:10")], flucs_c=[(10.0, "13:20")])
    rows = R74.race_rows(r, R32.ts(mel("18:30")))
    assert rows[0]["lim_t"] == R32.ts(mel("13:00")) and rows[0]["lim_price"] == 3.0
    assert np.isnan(rows[1]["lim_price"])                  # B has no price until 13:10
    # a meeting whose first race starts at 12:30: the limit's conditions are not confirmed, no price is taken
    rows = R74.race_rows(race("14:00", [(3.0, "09:00")], [(4.0, "09:00")]), R32.ts(mel("12:30")))
    assert not rows[0]["bwl_late"] and np.isnan(rows[0]["lim_price"]) and np.isnan(rows[0]["lim_t"])


def test_moved_chance():
    # model 0.6 / 0.3 (sum 0.9); TAB at its open 50/50; TAB then $2 / $4 -> shares 2/3 and 1/3
    # raw = 0.6 x (2/3)/(1/2) = 0.8 and 0.3 x (1/3)/(1/2) = 0.2, summed back to 0.9 -> 0.72 and 0.18
    got = R74.moved_chance(np.array([0.6, 0.3]), np.array([0.5, 0.5]), np.array([0.5, 0.25]), np.array([1, 1]))
    assert np.allclose(got, [0.72, 0.18])


def test_to_win_stakes():
    # to win $1,000 at $3 paid: $500; to win $500 at $5 paid: $125
    assert np.allclose(R74.to_win_stakes(np.array([3.0, 5.0, np.nan]), np.array([True, False, False])),
                       [500.0, 125.0, 0.0])


def test_no_betwatch(monkeypatch, capsys):
    monkeypatch.delenv("BETWATCH_DIR", raising=False)
    assert R74.main("nowhere", "t") == 1
    assert "nothing to test" in capsys.readouterr().out
