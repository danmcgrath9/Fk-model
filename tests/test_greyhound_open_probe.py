"""Market Open probe for greyhound opening prices: the pure rules."""
from datetime import datetime, timedelta

import pytest

from greyhound.open_probe import MAX_ODDS, MIN_ODDS, STAKE, derive, label, payload, plan, runners
from greyhound.opens import SYDNEY

NOW = datetime(2026, 10, 26, 6, 0, tzinfo=SYDNEY)
ROW = {"code": "Greyhounds", "name": "Sandown Park", "event_number": 3, "startTime": "2026-10-26T19:40:00",
       "runners": "1,2,4", "runner_names": "Fast One#&#Second Dog#&#Box Four"}


def test_runners_and_names_line_up_or_names_are_blank():
    assert runners(ROW) == [("1", "Fast One"), ("2", "Second Dog"), ("4", "Box Four")]
    assert runners({"runners": "1,2", "runner_names": "Only One"}) == [("1", ""), ("2", "")]


def test_plan_is_every_runner_of_upcoming_vic_greyhound_races_less_those_sent():
    rows = [ROW,
            dict(ROW, name="Albion Park"),                                   # QLD: not ours
            dict(ROW, code="Galloping"),
            dict(ROW, startTime="2026-10-26T05:00:00"),                      # already run
            dict(ROW, startTime="2026-10-30T19:00:00")]                      # beyond 3 days
    p = plan(rows, NOW, done={label("2026-10-26", "SANDOWN PARK", 3, "2")})
    assert [(x["venue"], x["race"], x["number"]) for x in p] == [("SANDOWN PARK", 3, "1"), ("SANDOWN PARK", 3, "4")]
    assert p[0]["label"] == "gho-2026-10-26-sandownpark-r3-n1" and p[0]["start_time"] == "2026-10-26T19:40:00"


def test_payload_can_never_fill():
    b = payload(plan([ROW], NOW)[0], "41", "101")
    assert b["check_odds"] and b["check_max_odds"] and b["odds"] == MIN_ODDS and b["max_odds"] == MAX_ODDS
    assert b["odds"] > b["max_odds"]                       # no price satisfies both
    assert b["stake"] == STAKE == 1 and b["max_attempts"] == 1 and b["is_market_open"] is True
    assert b["bookies"] == "41" and b["target_session"] == "101" and b["code"] == "Greyhounds"
    assert not b["boost_if_available"] and not b["spg_if_available"] and not b["take_sp"]
    assert b["start_time"] == "2026-10-26T19:40:00"


def test_payload_refuses_a_non_numeric_session():
    with pytest.raises(ValueError):
        payload(plan([ROW], NOW)[0], "41", "my tab")


LED = {"label": "gho-x", "date": "2026-10-26", "venue": "SANDOWN PARK", "race": "3", "number": "1", "runner": "Fast One",
       "sent_at": "2026-10-25T20:00:00+00:00"}


def rec(created, odds=4.2, amount=0.0, err="Current odds is less than the notification odds."):
    return {"created_at": created, "current_odds": odds, "amount": amount, "submit_result": "Error", "submit_error": err}


def test_refusal_hours_after_sending_is_a_known_open():
    d = derive(LED, [rec("2026-10-26T09:15:02.1+11:00")])
    assert (d["status"], d["tab_price"], d["open_known"]) == ("refused", 4.2, True)
    assert d["fired_at"] == "2026-10-26T09:15:02+11:00"


def test_refusal_right_after_sending_means_the_market_was_already_open():
    d = derive(LED, [rec("2026-10-26T07:00:40+11:00")])            # 40 seconds after sent_at (20:00 UTC)
    assert d["status"] == "refused" and d["open_known"] is False


def test_not_fired_yet_is_pending_and_money_on_is_loud():
    assert derive(LED, [])["status"] == "pending"
    d = derive(LED, [rec("2026-10-26T09:15:02+11:00", amount=1.0, err="")])
    assert d["status"] == "STAKED" and d["open_known"] is False
