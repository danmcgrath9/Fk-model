import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "research", "greyhound"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import topaz_morning as M  # noqa: E402


def test_latest_prices_takes_the_last_tab_fluc():
    races = [{"track": "Bendigo", "number": 7, "runners": [
        {"name": "Perfect Ace", "books": {"Tab": {"flucs": [[1.65, "2026-11-17T23:05:00Z"], [1.9, "2026-11-17T20:19:00Z"]]},
                                          "Sportsbet": {"last": [1.7, "2026-11-17T23:00:00Z"]}}}]}]
    got = M.latest_prices(races)
    k = ("Bendigo", "7", M.T.norm(pd.Series(["Perfect Ace"]))[0])
    assert got[k]["tab_now"] == 1.65 and got[k]["sportsbet_now"] == 1.7 and got[k]["ladbrokes_now"] is None


def test_morning_bets_rule_and_marks():
    # corrected chance 0.25 -> fair $4.00; need $4.40 at 1.1x and $4.80 at 1.2x
    # dog A: TAB opened $5.00 -> a bet at both; dog B: $4.50 -> 1.1x only; dog C: $4.00 -> no bet;
    # dog D: chance 0.6 -> fair $1.67, under $2 -> no bet however long TAB opened
    x = pd.DataFrame({"p_corr": [0.25, 0.25, 0.25, 0.6], "price": [5.0, 4.5, 4.0, 3.0],
                      "venue": ["Bendigo"] * 4, "race_no": ["7"] * 4, "start": ["2026-11-18T04:20:00Z"] * 4,
                      "card_box": ["1", "2", "3", "4"], "card_dog": ["A", "B", "C", "D"], "dog_name": ["A", "B", "C", "D"],
                      "tab_first_t": ["2026-11-17T20:19:00Z"] * 4})
    now = {("Bendigo", "7", M.T.norm(pd.Series(["A"]))[0]): {"tab_now": 4.2}}
    b = M.morning_bets(x, now)
    assert [r["dog"] for r in b] == ["A", "B"]
    assert [r["at_12"] for r in b] == [True, False]
    assert b[0]["need_11"] == 4.4 and b[0]["need_12"] == 4.8 and b[0]["tab_open"] == 5.0 and b[0]["tab_now"] == 4.2
    assert "tab_now" not in b[1]


def race(rid, prices, scratched=(), results=None):
    """A compacted Betwatch race: runner i+1 with TAB flucs [(price, time)] or none."""
    return {"id": rid, "date": "2026-11-18", "track": "Healesville", "number": 3, "start": "2026-11-18T00:27:00Z",
            "results": results, "runners": [
                {"number": i + 1, "name": f"Dog {i + 1}", "scratched": "2026-11-17T22:00:00Z" if i in scratched else None,
                 "books": {"Tab": {"flucs": fl}} if fl else {}} for i, fl in enumerate(prices)]}


def test_full_fields_waits_for_every_runner_not_scratched():
    a = race("a", [[[3.0, "t"]], [[4.0, "t"]]])
    b = race("b", [[[3.0, "t"]], []])                          # runner 2 has no TAB price yet
    c = race("c", [[[3.0, "t"]], []], scratched=(1,))          # runner 2 is scratched: the field is full
    assert M.full_fields([a, b, c]) == {"a", "c"}


def test_detect_marks_a_price_already_cut(monkeypatch):
    from datetime import datetime, timezone
    rows = [{"venue": "Healesville", "race_no": "3", "start": "s", "box": "6", "dog": "Dog 1", "fair": 4.32,
             "need_11": 4.75, "need_12": 5.18, "at_12": True, "tab_open": 5.5, "tab_open_at": "t", "tab_now": 4.0,
             "number": 1, "bw_race": "a"},
            {"venue": "Healesville", "race_no": "3", "start": "s", "box": "2", "dog": "Dog 2", "fair": 3.0,
             "need_11": 3.3, "need_12": 3.6, "at_12": False, "tab_open": 3.4, "tab_open_at": "t", "tab_now": 3.4,
             "number": 2, "bw_race": "a"}]
    monkeypatch.setattr(M, "morning_bets", lambda x, now: rows)
    got = M.detect(None, [], datetime(2026, 11, 17, 20, 17, tzinfo=timezone.utc), "2026-11-18")
    # You Good's morning: $5.50 at the open, $4.00 a minute later, under the $4.75 needed: missed
    assert [b["placed"] for b in got] == [False, True]
    assert got[0]["detected_at"] == "2026-11-17T20:17:00+00:00" and got[1]["tab_at_detect"] == 3.4


def test_settle_by_hand():
    r = race("a", [[[6.0, "2026-11-17T20:16:00Z"]], [[2.0, "2026-11-17T20:16:00Z"]]], results=[[1], [2]])
    rows = [{"placed": True, "bw_race": "a", "number": 1, "tab_at_detect": 6.0, "day": "2026-11-18"},
            {"placed": True, "bw_race": "a", "number": 2, "tab_at_detect": 2.0, "day": "2026-11-18"},
            {"placed": False, "bw_race": "a", "number": 2, "tab_at_detect": 2.0, "day": "2026-11-18"},
            {"placed": True, "bw_race": "zz", "number": 1, "tab_at_detect": 3.0, "day": "2026-11-18"}]
    got = M.settle(rows, [r])
    # dog 1 won at $6.00, no scratching: +5 units; dog 2 lost: -1; the missed bet is not settled; race zz has no result
    assert got[0]["won"] and got[0]["profit"] == 5.0 and got[1]["profit"] == -1.0
    assert "settled" not in got[2] and "settled" not in got[3]
    assert M.summary(got) == ("4 bets seen, 3 placed (1 missed: TAB had cut the price below the price it needed by then), "
                              "2 settled, 1 won, +4.00 units (+200.0% a bet); 0 of 2 beat TAB's final price, by "
                              "+0.0% on average")


def test_settle_keeps_tab_s_final_price():
    # dog 1 taken at $6.00 at the open; TAB's last price before the race $4.50: beaten by 6 / 4.5 - 1 = 33.3%
    r = race("a", [[[6.0, "2026-11-17T20:16:00Z"], [4.5, "2026-11-18T00:20:00Z"]], [[2.0, "t"]]], results=[[2], [1]])
    got = M.settle([{"placed": True, "bw_race": "a", "number": 1, "tab_at_detect": 6.0, "day": "2026-11-18"}], [r])
    assert got[0]["tab_final"] == 4.5 and not got[0]["won"]
    assert M.summary(got).endswith("1 of 1 beat TAB's final price, by +33.3% on average")


def test_watch_prices_each_race_once(monkeypatch):
    from datetime import datetime
    t = iter([datetime(2026, 11, 18, 7, m, tzinfo=M.MEL) for m in (0, 0, 1, 1, 2, 2, 3)])
    calls = []
    monkeypatch.setattr(M.T, "open_field", lambda races: pd.DataFrame({"bw_race": [r["id"] for r in races]}))

    def at_open(facts, cards, bst, meta):
        calls.append(sorted(facts.bw_race))
        return facts
    monkeypatch.setattr(M.topaz_iso, "at_open", at_open)
    monkeypatch.setattr(M, "detect", lambda x, races, now, day: [{"placed": True, "bw_race": b} for b in x.bw_race])
    polls = [[race("a", [[[3.0, "t"]]]), race("b", [[]])],
             [race("a", [[[3.0, "t"]]]), race("b", [[[2.0, "t"]]])],
             [race("a", [[[3.0, "t"]]]), race("b", [[[2.0, "t"]]])]]
    bets, n, seen, h = M.watch("2026-11-18", None, None, None, datetime(2026, 11, 18, 7, 3, tzinfo=M.MEL), 0,
                            lambda: polls.pop(0), clock=lambda: next(t), sleep=lambda s: None)
    # poll 1 prices race a (b is not fully priced yet), poll 2 prices b only, poll 3 nothing new
    assert calls == [["a"], ["b"]] and n == 3 and seen == {"a", "b"} and len(bets) == 2


def test_feed_health_counts_runners_not_scratched():
    races = [race("a", [[[3.0, "t"]], []]), race("b", [[], []])]
    races[1]["runners"][0]["books"]["Sportsbet"] = {"last": [4.0, "t"], "flucs": []}
    races[1]["runners"][1]["scratched"] = "2026-11-19T07:00:00Z"
    h = M.feed_health(races)
    assert h == {"races": 2, "runners": 3, "tab_runners": 1, "tab_races": 1, "any_runners": 2}


def _clock(start, step_s):
    from datetime import timedelta
    state = {"t": start}

    def tick():
        return state["t"]

    def sleep(s):
        state["t"] = state["t"] + timedelta(seconds=step_s)
    return tick, sleep


def test_watch_waits_on_for_a_late_open(monkeypatch):
    """No TAB price at 8:20: the watch runs on to `late`; a stray runner priced is not TAB's open."""
    from datetime import datetime
    monkeypatch.setattr(M.T, "open_field", lambda races: pd.DataFrame())
    tick, sleep = _clock(datetime(2026, 11, 19, 8, 0, tzinfo=M.MEL), 600)
    stray = [race("a", [[[3.0, "t"]], []]), race("b", [[], []]), race("c", [[], []])]
    _, n, seen, h = M.watch("2026-11-19", None, None, None, datetime(2026, 11, 19, 8, 20, tzinfo=M.MEL), 0,
                            lambda: stray, clock=tick, sleep=sleep, late=datetime(2026, 11, 19, 9, 50, tzinfo=M.MEL))
    # polls at 8:00, 8:10, ..., 9:40: eleven, none past 9:50
    assert n == 11 and not seen and h["first_open"] is None and h["tab_runners"] == 1


def test_watch_stops_an_hour_after_a_late_open(monkeypatch):
    from datetime import datetime
    monkeypatch.setattr(M.T, "open_field", lambda races: pd.DataFrame())
    tick, sleep = _clock(datetime(2026, 11, 19, 8, 0, tzinfo=M.MEL), 600)
    closed = [race("a", [[]]), race("b", [[]])]
    opened = [race("a", [[[3.0, "t"]]]), race("b", [[]])]
    feed = iter([closed] * 4 + [opened] * 20)          # TAB opens on the poll at 8:40
    _, n, _, h = M.watch("2026-11-19", None, None, None, datetime(2026, 11, 19, 8, 20, tzinfo=M.MEL), 0,
                         lambda: next(feed), clock=tick, sleep=sleep, late=datetime(2026, 11, 19, 9, 50, tzinfo=M.MEL))
    # open seen at 8:40, so the watch runs to 9:40: polls at 8:00 ... 9:30, ten
    assert h["first_open"].strftime("%H:%M") == "08:40" and n == 10


def test_watch_on_a_normal_morning_stops_at_until(monkeypatch):
    from datetime import datetime
    monkeypatch.setattr(M.T, "open_field", lambda races: pd.DataFrame())
    tick, sleep = _clock(datetime(2026, 11, 19, 7, 0, tzinfo=M.MEL), 600)
    opened = [race("a", [[[3.0, "t"]]])]
    _, n, _, h = M.watch("2026-11-19", None, None, None, datetime(2026, 11, 19, 8, 20, tzinfo=M.MEL), 0,
                         lambda: opened, clock=tick, sleep=sleep, late=datetime(2026, 11, 19, 9, 50, tzinfo=M.MEL))
    # open at 7:00, an hour after is 8:00, before 8:20: polls at 7:00 ... 8:10, eight
    assert n == 8 and h["first_open"].strftime("%H:%M") == "07:00"


def test_race_opened_at_is_the_earliest_tab_price():
    from datetime import datetime, timezone
    r = race("a", [[[3.0, "2026-11-18T22:19:10Z"], [4.4, "2026-11-18T22:18:55Z"]], [[2.0, "t"]], []])
    assert M.race_opened_at(r) == datetime(2026, 11, 18, 22, 18, 55, tzinfo=timezone.utc)
    assert M.race_opened_at(race("b", [[], []])) is None


def test_watch_polls_fast_while_tab_opens_races(monkeypatch):
    """Start to start: 30 seconds while nothing moves, 10 for ten minutes after TAB prices a race."""
    from datetime import datetime
    monkeypatch.setattr(M.T, "open_field", lambda races: pd.DataFrame())
    waits = []
    state = {"t": datetime(2026, 11, 19, 9, 0, tzinfo=M.MEL)}

    def sleep(s):
        waits.append(round(s))
        state["t"] = state["t"] + __import__("datetime").timedelta(seconds=s)
    closed = [race("a", [[]]), race("b", [[]])]
    opened = [race("a", [[[3.0, "t"]]]), race("b", [[]])]
    feed = iter([closed] * 3 + [opened] * 200)            # TAB prices race a on the fourth poll, at 9:01:30
    M.watch("2026-11-19", None, None, None, datetime(2026, 11, 19, 9, 20, tzinfo=M.MEL), 30, lambda: next(feed),
            clock=lambda: state["t"], sleep=sleep, fast=10, fast_for=10, timer=lambda: 0.0)
    assert waits[:3] == [30, 30, 30] and waits[3] == 10
    # fast from 9:01:30 to 9:11:30, then back to 30
    assert waits.count(10) == 60 and set(waits[63:]) == {30}


def test_watch_counts_the_poll_s_own_time_in_the_wait(monkeypatch):
    """A 30-second poll whose fetch took 12 seconds waits 18, not 30 (19 Nov: 45 after the work made 50 to 62)."""
    from datetime import datetime
    monkeypatch.setattr(M.T, "open_field", lambda races: pd.DataFrame())
    t = iter([datetime(2026, 11, 19, 7, 0, 0, tzinfo=M.MEL)] * 2 + [datetime(2026, 11, 19, 7, 0, 2, tzinfo=M.MEL)])
    ticks, waits = iter([0.0, 12.0, 12.0]), []           # the poll's start, its fetch done, the wait worked out
    M.watch("2026-11-19", None, None, None, datetime(2026, 11, 19, 7, 0, 1, tzinfo=M.MEL), 30, lambda: [],
            clock=lambda: next(t), sleep=waits.append, timer=lambda: next(ticks))
    assert waits == [18.0]


def test_watch_records_the_delay_from_tab_open(monkeypatch):
    from datetime import datetime
    monkeypatch.setattr(M.T, "open_field", lambda races: pd.DataFrame({"bw_race": [r["id"] for r in races]}))
    monkeypatch.setattr(M.topaz_iso, "at_open", lambda facts, cards, bst, meta: facts)
    monkeypatch.setattr(M, "detect", lambda x, races, now, day: [])
    t = iter([datetime(2026, 11, 19, 9, 19, 30, tzinfo=M.MEL)] * 2 + [datetime(2026, 11, 19, 9, 30, tzinfo=M.MEL)])
    r = race("a", [[[4.4, "2026-11-18T22:18:55Z"]]])          # 9:18:55 Melbourne; seen at 9:19:30
    _, _, _, h = M.watch("2026-11-19", None, None, None, datetime(2026, 11, 19, 9, 20, tzinfo=M.MEL), 30,
                         lambda: [r], clock=lambda: next(t), sleep=lambda s: None, timer=lambda: 0.0)
    assert h["lags"] == [35.0] and M.delay_line(h["lags"]).startswith("From Betwatch's first TAB price in a race to "
                                                                       "its bets being ready: median 35 seconds")
