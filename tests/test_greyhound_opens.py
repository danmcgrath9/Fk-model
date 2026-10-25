"""Greyhound opening-price recorder: the pure rules (no BetMatic, no clock)."""
from datetime import datetime, timedelta

from greyhound.opens import (SYDNEY, RaceBook, Race, merge_rows, parse_start, prices, select_races, state_of)

T0 = datetime(2026, 10, 26, 9, 0, tzinfo=SYDNEY)


def at(minutes):
    return T0 + timedelta(minutes=minutes)


def runner(num, *books):
    return {"number": num, "bookie_odds": [{"name": b, "win": w, "place": 1.5, "scratched": s} for b, w, s in books]}


def race(start_min=600, venue="SANDOWN PARK", num=1):
    return Race(venue, num, at(start_min), "raw")


def test_naive_start_is_sydney_and_aware_is_kept():
    assert parse_start("2026-10-26T19:30:00") == datetime(2026, 10, 26, 19, 30, tzinfo=SYDNEY)
    assert parse_start("2026-10-26T08:30:00Z").utcoffset() == timedelta(0)
    assert parse_start("") is None and parse_start("not a time") is None


def test_state_from_alias_then_track_list():
    assert state_of({"name": "KYNETON", "competition_alias": "#KYNETON#KYNETON VIC#KYNETON AUS#"}) == "VIC"
    assert state_of({"name": "WENTWORTH PARK", "competition_alias": "#WENTWORTH PARK NSW#"}) == "NSW"
    assert state_of({"name": "The Meadows"}) == "VIC"
    assert state_of({"name": "ALBION PARK"}) is None


def test_select_races_greyhounds_in_window_and_only_the_next_per_venue_number():
    rows = [
        {"code": "Greyhounds", "name": "SANDOWN PARK", "event_number": 1, "startTime": "2026-10-26T19:00:00"},
        {"code": "Greyhounds", "name": "SANDOWN PARK", "event_number": 1, "startTime": "2026-10-27T19:00:00"},
        {"code": "Galloping", "name": "SANDOWN", "event_number": 1, "startTime": "2026-10-26T13:00:00"},
        {"code": "Greyhounds", "name": "ALBION PARK", "event_number": 1, "startTime": "2026-10-26T19:00:00"},
        {"code": "Greyhounds", "name": "HEALESVILLE", "event_number": 2, "startTime": "2026-10-26T08:00:00"},  # run
        {"code": "Greyhounds", "name": "BALLARAT", "event_number": 3, "startTime": "2026-10-28T19:00:00"},    # too far
    ]
    got = select_races(rows, T0, ahead=timedelta(hours=40))
    assert [(r.venue, r.number, r.start.day) for r in got] == [("SANDOWN PARK", 1, 26)]


def test_prices_skip_scratched_and_non_prices():
    p = prices([runner(1, ("TAB", 3.5, False), ("Sportsbet", 0, False)), runner(2, ("TAB", 4.0, True)),
                {"number": 3, "bookie_odds": [{"name": "TAB", "win": "x"}]}])
    assert p == {("1", "TAB"): 3.5}


def test_open_window_is_last_answered_poll_before_first_price():
    rb = RaceBook(race())
    rb.record(at(0), [])                                                    # answered, nothing priced
    rb.record(at(3), [runner(1)])                                           # answered, field but no prices
    rb.record(at(6), [runner(1, ("TAB", 3.4, False)), runner(2, ("TAB", 5.0, False))])
    rb.record(at(9), [runner(1, ("TAB", 3.2, False), ("Sportsbet", 3.3, False))])
    rb.record(at(12), [runner(1, ("Sportsbet", 3.1, False))])               # TAB missing: a gap, not a close
    tab, sb = rb.books["TAB"], rb.books["Sportsbet"]
    assert (tab.last_closed, tab.first_seen, tab.open_known) == (at(3), at(6), True)
    assert tab.first == {"1": 3.4, "2": 5.0} and tab.last == {"1": 3.2} and tab.last_seen == at(9)
    assert (sb.last_closed, sb.first_seen) == (at(6), at(9))                # its window starts at TAB's first poll


def test_already_priced_at_first_look_is_not_an_open():
    rb = RaceBook(race())
    rb.record(at(0), [runner(1, ("TAB", 2.8, False))])
    assert rb.books["TAB"].open_known is False
    assert rb.rows()[0]["open_known"] is False and rb.rows()[0]["closed_at"] == ""


def test_unanswered_polls_are_never_closed_readings():
    rb = RaceBook(race())
    rb.note_poll(at(0))                       # sent, no answer (bot offline?)
    rb.note_poll(at(3))
    rb.record(at(6), [runner(1, ("TAB", 2.8, False))])
    assert rb.polls == 2 and rb.books["TAB"].open_known is False


def test_due_fast_before_tab_opens_slow_after_and_never_after_the_jump():
    rb = RaceBook(race(start_min=60))
    every, slow = timedelta(minutes=3), timedelta(minutes=20)
    assert rb.due(at(0), every, slow)
    rb.note_poll(at(0)); rb.record(at(0), [])
    assert not rb.due(at(2), every, slow) and rb.due(at(3), every, slow)
    rb.note_poll(at(3)); rb.record(at(3), [runner(1, ("TAB", 3.0, False))])
    assert not rb.due(at(10), every, slow) and rb.due(at(23), every, slow)
    assert not rb.due(at(60), every, slow)


def test_rows_carry_the_window_and_both_prices():
    rb = RaceBook(race(num=4))
    rb.record(at(0), [])
    rb.record(at(3), [runner(1, ("TAB", 3.4, False))])
    rb.record(at(23), [runner(1, ("TAB", 3.0, False))])
    (r,) = rb.rows()
    assert r["race"] == 4 and r["runner"] == "1" and r["open_known"] is True
    assert r["closed_at"] == "2026-10-26T09:00:00+11:00" and r["first_seen_at"] == "2026-10-26T09:03:00+11:00"
    assert (r["first_price"], r["last_price"]) == (3.4, 3.0)


def test_merge_keeps_the_earlier_runs_open_and_the_later_runs_last_price():
    rb1 = RaceBook(race()); rb1.record(at(0), []); rb1.record(at(3), [runner(1, ("TAB", 3.4, False))])
    rb2 = RaceBook(race()); rb2.record(at(300), [runner(1, ("TAB", 2.9, False))])   # second run: already open
    (m,) = merge_rows(rb1.rows(), rb2.rows())
    assert m["open_known"] is True and m["first_price"] == 3.4 and m["first_seen_at"].endswith("09:03:00+11:00")
    assert m["last_price"] == 2.9 and m["last_seen_at"].endswith("14:00:00+11:00")
    (m2,) = merge_rows(rb2.rows(), rb1.rows())                                      # order of runs does not matter
    assert m2["first_price"] == 3.4 and m2["last_price"] == 2.9
