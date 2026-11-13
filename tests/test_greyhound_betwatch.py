"""greyhound/betwatch.py: the kept shape, the first price, the counts and the month walk, on a made-up race."""
from datetime import date

import pytest

from greyhound import betwatch as B


def _race():
    # start 7:00pm AEDT (08:00 UTC); TAB first priced at 07:00 AEDT (12 hours before), flucs given out of order
    return {"id": "r1", "number": 3, "name": "Race 3", "status": "Resulted", "startTime": "2026-11-10T08:00:00Z",
            "actualStartTime": None, "results": [[2], [1]], "distance": 400, "classConditions": "Grade 5",
            "meeting": {"id": "m1", "location": "VIC", "track": "Geelong", "type": "Greyhound", "date": "2026-11-10"},
            "runners": [
                {"id": "a", "name": "DOG A", "number": 1, "barrier": 1, "scratchedTime": None, "emergency": False,
                 "bookmakerMarkets": [
                     {"bookmaker": "Tab", "fixedWin": {"price": 3.0, "lastUpdated": "2026-11-10T07:59:00Z",
                                                        "flucs": [{"price": 3.5, "lastUpdated": "2026-11-09T22:00:00Z"},
                                                                  {"price": 4.0, "lastUpdated": "2026-11-09T20:00:00Z"}]}},
                     {"bookmaker": "Pointsbet", "fixedWin": {"price": 3.2, "lastUpdated": "2026-11-10T07:58:00Z"}}]},
                {"id": "b", "name": "DOG B", "number": 2, "barrier": 2, "scratchedTime": "2026-11-10T05:00:00Z",
                 "emergency": False, "bookmakerMarkets": []}]}


def test_compact_sorts_flucs_and_keeps_the_last_price():
    c = B.compact(_race())
    assert c["track"] == "Geelong" and c["number"] == 3 and c["date"] == "2026-11-10"
    tab = c["runners"][0]["books"]["Tab"]
    assert tab["flucs"] == [[4.0, "2026-11-09T20:00:00Z"], [3.5, "2026-11-09T22:00:00Z"]]
    assert tab["last"] == [3.0, "2026-11-10T07:59:00Z"]
    assert c["runners"][0]["books"]["Pointsbet"]["flucs"] == []
    assert B.first_price(c["runners"][0]) == (4.0, "2026-11-09T20:00:00Z")
    assert B.first_price(c["runners"][1]) is None


def test_day_counts_leave_out_scratchings_and_time_the_first_price():
    c = B.day_counts([_race()])
    assert c["races"] == 1 and c["runners"] == 1 and c["with_tab_flucs"] == 1 and c["tab_flucs_median"] == 2
    # first TAB fluc 20:00 UTC on the 9th, jump 08:00 UTC on the 10th: 12 hours
    assert c["hours_first_tab_before_jump"] == {"p10": 12.0, "median": 12.0, "p90": 12.0}
    assert c["first_tab_after_jump"] == 0
    assert c["bookmakers_on_10pct_of_runners"] == ["Pointsbet", "Tab"]


def test_months_and_days_stop_before_today():
    assert B.months("2022-11", "2023-02") == ["2022-11", "2022-12", "2023-01", "2023-02"]
    assert B.month_days("2026-11", date(2026, 11, 4)) == ["2026-11-01", "2026-11-02", "2026-11-03"]
    assert len(B.month_days("2024-02", date(2026, 1, 1))) == 29


def test_post_refuses_a_rejected_key(monkeypatch):
    class R:
        status_code = 401
        text = "no"

    class S:
        def post(self, *a, **k):
            return R()
    with pytest.raises(B.BetwatchError, match="refused"):
        B._post(S(), {})


def test_post_raises_on_a_graphql_error_rather_than_returning_no_races():
    class R:
        status_code = 200
        text = ""

        def json(self):
            return {"errors": [{"message": "Cannot query field"}]}

    class S:
        def post(self, *a, **k):
            return R()
    with pytest.raises(B.BetwatchError, match="GraphQL"):
        B._post(S(), {})


def test_compact_keeps_betfair_ids_trainer_and_driver():
    r = _race()
    r["betfairMapping"] = {"win": "1.250", "place": "1.251"}
    r["runners"][0].update({"betfairId": "777", "trainerName": "A Trainer", "riderName": "A Driver"})
    c = B.compact(r)
    assert (c["betfair_win"], c["betfair_place"], c["type"]) == ("1.250", "1.251", "Greyhound")
    ru = c["runners"][0]
    assert (ru["betfair_id"], ru["trainer"], ru["rider"]) == ("777", "A Trainer", "A Driver")
    assert c["runners"][1]["rider"] is None                    # missing fields stay None, never guessed


def test_tags_and_locations():
    assert B.tag(["Greyhound"], ["VIC"]) == "VIC_G"            # the original greyhound files keep their name
    assert B.tag(["Harness"], B.locations_arg("Australia")) == "AU_H"
    assert B.locations_arg("vic, nsw") == ["VIC", "NSW"]


def test_fetch_day_sends_the_type_and_states(monkeypatch):
    seen = {}

    def fake_post(session, variables, tries=6):
        seen.update(variables)
        return []
    monkeypatch.setattr(B, "_post", fake_post)
    B.fetch_day(None, "2026-11-10", ["Harness"], B.AU_STATES)
    assert seen["types"] == ["Harness"] and seen["locations"] == B.AU_STATES and seen["dateFrom"] == "2026-11-10"
    B.fetch_day(None, "2026-11-10")
    assert seen["types"] == ["Greyhound"] and seen["locations"] == ["VIC"]
