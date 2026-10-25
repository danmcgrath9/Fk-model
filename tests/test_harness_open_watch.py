"""betmatic/harness_open_watch.py: the open is the first poll with a price, bracketed by the last empty poll; only the
first price per runner is kept; answers are never filed under the wrong race."""
import datetime as dt
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "betmatic"))
import harness_open_watch as w  # noqa: E402

UTC = dt.timezone.utc
T = dt.datetime(2026, 10, 25, 8, 0, tzinfo=UTC)


def race(field=("1", "2", "3")):
    return w.new_race({"venue": "MELTON", "race": 3, "start_time": "2026-10-26T19:30:00+11:00",
                       "date": "2026-10-26", "runners": list(field)})


def tab(number, win, place=0, scratched=False):
    return {"number": number, "bookie_odds": [{"name": "TAB", "win": win, "place": place, "scratched": scratched}]}


def test_open_is_bracketed_by_the_last_empty_poll():
    r = race()
    assert w.record(r, [], T) is False                                  # 08:00 nothing up
    assert w.record(r, [], T + dt.timedelta(minutes=2)) is False        # 08:02 nothing up
    assert w.record(r, [tab(1, 3.5, 1.6), tab(2, 4.0)], T + dt.timedelta(minutes=4)) is True
    assert r["last_empty_at"] == "2026-10-25T08:02:00Z"                 # opened between 08:02 and 08:04
    assert r["opened_at"] == "2026-10-25T08:04:00Z"
    assert r["open_seen_on_first_poll"] is False
    assert r["runners"]["1"]["TAB"] == {"win": 3.5, "place": 1.6, "first_seen_at": "2026-10-25T08:04:00Z"}
    assert r["runners"]["2"]["TAB"]["place"] is None                    # place 0 = no place price, not a $0 price
    assert r["polls"] == 3


def test_already_open_at_first_look_is_flagged():
    r = race()
    assert w.record(r, [tab(1, 3.5)], T) is True
    assert r["open_seen_on_first_poll"] is True and r["last_empty_at"] is None


def test_only_the_first_price_is_kept_and_late_runners_get_their_own_time():
    r = race()
    w.record(r, [tab(1, 3.5)], T)
    w.record(r, [tab(1, 2.8), tab(2, 6.0)], T + dt.timedelta(minutes=2))   # 1 firmed to 2.80: still 3.50 kept
    assert r["runners"]["1"]["TAB"]["win"] == 3.5
    assert r["runners"]["2"]["TAB"] == {"win": 6.0, "place": None, "first_seen_at": "2026-10-25T08:02:00Z"}
    assert r["opened_at"] == "2026-10-25T08:00:00Z"                     # a later answer never moves the open


def test_scratched_runner_and_completion():
    r = race(("1", "2", "3"))
    w.record(r, [tab(1, 3.5), tab(3, 0, scratched=True)], T)
    assert r["runners"]["3"]["TAB"] == {"scratched": True, "first_seen_at": "2026-10-25T08:00:00Z"}
    assert not w.complete(r)                                            # runner 2 has no price yet
    w.record(r, [tab(2, 9.0)], T + dt.timedelta(minutes=2))
    assert w.complete(r)


def test_scratched_is_not_an_open():
    r = race()
    assert w.record(r, [tab(3, 0, scratched=True)], T) is False         # a scratching with no prices: not open
    assert r["opened_at"] is None and r["last_empty_at"] == "2026-10-25T08:00:00Z"


def test_answers_are_paired_with_their_own_race():
    a = w.Answers()
    a.on_message(json.dumps({"category": "request_odds", "data": {"competition": "MELTON", "event_number": 2,
                                                                  "code": "Harness"}}))
    a.on_message(json.dumps({"category": "odds_update_anwser", "data": [tab(1, 5.0)]}))   # late answer for R2
    a.on_message(json.dumps({"category": "request_odds", "data": {"competition": "MELTON", "event_number": 3,
                                                                  "code": "Harness"}}))
    a.on_message(json.dumps({"category": "odds_update_anwser", "data": [tab(1, 3.5)]}))
    data, _ = a.wait_for("MELTON", 3, timeout=1)
    assert data == [tab(1, 3.5)]                                        # R2's answer was discarded, not filed as R3
    assert a.wait_for("MELTON", 3, timeout=0.2) is None


def test_schedule_keeps_harness_inside_the_horizon():
    now = dt.datetime(2026, 10, 25, 0, 0, tzinfo=UTC)
    sched = [
        {"code": "Harness", "name": "melton", "event_number": 1, "startTime": "2026-10-25T19:00:00+11:00",
         "runners": "1,2, 3"},                                          # 08:00Z: in
        {"code": "Harness", "name": "MELTON", "event_number": 2, "startTime": "2026-10-24T19:00:00+11:00",
         "runners": "1"},                                               # yesterday: out
        {"code": "Harness", "name": "MELTON", "event_number": 3, "startTime": "2026-10-27T19:00:00+11:00",
         "runners": "1"},                                               # 56h away: out at a 36h horizon
        {"code": "Galloping", "name": "FLEMINGTON", "event_number": 1, "startTime": "2026-10-25T12:00:00+11:00",
         "runners": "1"},                                               # not harness
    ]
    got = w.schedule_races(sched, now, 36)
    assert got == [{"venue": "MELTON", "race": 1, "start_time": "2026-10-25T19:00:00+11:00", "date": "2026-10-25",
                    "runners": ["1", "2", "3"]}]


def test_an_unreadable_start_time_stops_the_run():
    with pytest.raises(SystemExit):
        w.parse_start("tomorrow 7pm")
    with pytest.raises(SystemExit):
        w.parse_start("2026-10-25T19:00:00")                            # no timezone: refused, not assumed
