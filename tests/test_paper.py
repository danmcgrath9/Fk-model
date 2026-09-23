from datetime import datetime, timezone

from fk.paper import (Bet, Row, before_the_jump, jump_time, kelly_stake, movement, movement_summary, place,
                      running, settle, summarise, summarise_at_struck)


def test_kelly_by_hand_and_the_edge_gate():
    assert round(kelly_stake(0.3, 5.0), 4) == 3.125     # (1.2 - 0.7) / 4 = 0.125, a quarter on 100 units
    assert kelly_stake(0.15, 5.0) == 0.0                 # 0.6 - 0.85 < 0: no edge, no bet
    assert kelly_stake(0.9, 3.0) == 5.0                  # capped
    assert kelly_stake(None, 5.0) == 0.0 and kelly_stake(0.5, 1.0) == 0.0


def test_place_every_plan_on_one_race():
    rows = [Row("a", "A", 3.0, 4.0, 0.33, 0.25, "model_higher"),
            Row("b", "B", 6.0, 5.0, 0.17, 0.20, None),
            Row("c", "C", 12.0, 21.0, 0.08, 0.05, "model_higher")]
    bets = place(rows)
    by = {(b.plan, b.horse_id): b for b in bets}
    assert by[("top_pick", "a")].stake == 1.0
    assert round(by[("top_pick_to_win_1", "a")].stake, 4) == round(1 / 3, 4)
    assert ("value_flags", "a") in by and ("value_flags", "c") in by and ("value_flags", "b") not in by
    assert ("value_under_8", "a") in by and ("value_under_8", "c") not in by   # $12 is not under $8
    assert round(by[("kelly_quarter", "a")].stake, 4) == round(0.25 * ((0.33 * 3 - 0.67) / 3) * 100, 4)
    assert ("kelly_quarter", "b") not in by                                      # 0.17 x 4 - 0.83 < 0
    assert place([Row("a", "A", 3.0, 4.0, 0.3, 0.25, None, finish=1)]) == []     # already run
    assert place([]) == []


def test_settle_summarise_and_running():
    assert settle(1.0, True, 4.5) == 4.5 and settle(2.0, False, 4.5) == 0.0 and settle(2.0, True, None) == 2.0
    settled = [dict(bet_id="r1|a|top_pick", plan="top_pick", stake=1, returned=4.5, won=True, meeting_date="2026-09-12", race_number=1),
               dict(bet_id="r2|b|top_pick", plan="top_pick", stake=1, returned=0, won=False, meeting_date="2026-09-12", race_number=2),
               dict(bet_id="r1|c|value_flags", plan="value_flags", stake=1, returned=0, won=False, meeting_date="2026-09-12", race_number=1)]
    s = summarise(settled)
    assert s["top_pick"].bets == 2 and s["top_pick"].winners == 1 and s["top_pick"].profit == 2.5 and round(s["top_pick"].roi, 2) == 1.25
    assert s["value_flags"].roi == -1.0
    r = running(settled)
    assert [v for _, v in r["top_pick"]] == [3.5, 2.5]


def test_jump_time_reads_form_king_start_strings_in_melbourne():
    j = jump_time("2026-09-15", "12:25pm")
    assert j.isoformat() == "2026-09-15T12:25:00+10:00"          # AEST in September
    assert jump_time("2026-09-15", "1:05 PM").hour == 13
    assert jump_time("2026-09-15", "12:05am").hour == 0
    assert jump_time("2026-09-15", "13:05").hour == 13
    assert jump_time("2026-09-15", None) is None and jump_time("2026-09-15", "soon") is None
    assert jump_time("2026-10-10", "12:25pm").isoformat() == "2026-10-10T12:25:00+11:00"   # daylight saving


def test_a_bet_after_the_jump_or_with_no_jump_is_not_a_bet():
    j = jump_time("2026-09-15", "3:00pm")                          # 05:00 UTC
    assert before_the_jump(j, datetime(2026, 9, 15, 4, 59, tzinfo=timezone.utc))
    assert not before_the_jump(j, datetime(2026, 9, 15, 5, 0, tzinfo=timezone.utc))
    assert not before_the_jump(None, datetime(2026, 9, 15, 4, 0, tzinfo=timezone.utc))


def test_movement_from_struck_to_settled_price():
    assert round(movement(5.0, 4.0), 4) == -0.20        # $5 into $4: firmed 20%
    assert round(movement(4.0, 5.0), 4) == 0.25         # $4 out to $5: drifted 25%
    assert movement(None, 4.0) is None and movement(5.0, None) is None and movement(1.0, 4.0) is None


def test_movement_summary_medians_and_firmed_share_per_plan():
    settled = [{"plan": "a", "price": 5.0, "settle_price": 4.0},      # -20%
               {"plan": "a", "price": 4.0, "settle_price": 5.0},      # +25%
               {"plan": "a", "price": 10.0, "settle_price": 8.0},     # -20%
               {"plan": "a", "price": 3.0, "settle_price": None},     # no settle price: not counted
               {"plan": "b", "price": 2.0, "settle_price": 3.0}]      # +50%
    m = movement_summary(settled)
    assert m["a"]["n"] == 3 and round(m["a"]["median"], 4) == -0.20 and round(m["a"]["firmed_share"], 4) == round(2 / 3, 4)
    assert m["b"]["n"] == 1 and round(m["b"]["median"], 4) == 0.50 and m["b"]["firmed_share"] == 0.0


def test_the_opening_price_rides_onto_every_bet():
    rows = [Row("a", "A", 3.0, 4.0, 0.33, 0.25, "model_higher", None, 6.0),
            Row("b", "B", 6.0, 5.0, 0.17, 0.20, None, None, 4.5)]
    bets = place(rows)
    assert {b.horse_id: b.opening for b in bets if b.plan == "kelly_quarter"} or True
    assert all(b.opening == (6.0 if b.horse_id == "a" else 4.5) for b in bets)


def test_the_two_settlement_bases_differ_by_the_movement():
    settled = [{"plan": "a", "stake": 1.0, "won": True, "returned": 13.0, "price": 10.0},   # struck $10, settled $13
               {"plan": "a", "stake": 1.0, "won": False, "returned": 0.0, "price": 4.0},
               {"plan": "a", "stake": 1.0, "won": True, "returned": 2.0, "price": None}]     # no struck price: skipped
    at_bsp, at_struck = summarise(settled), summarise_at_struck(settled)
    assert at_bsp["a"].bets == 3 and round(at_bsp["a"].returned, 2) == 15.0
    assert at_struck["a"].bets == 2 and round(at_struck["a"].returned, 2) == 10.0            # the drifted winner pays $10, not $13
    assert at_struck["a"].winners == 1 and round(at_struck["a"].profit, 2) == 8.0


def test_deductions_hand_values():
    from fk.paper import deduction_for, settle_struck
    assert deduction_for([4.0, 41.0]) == 0.25            # $41 is 2.4%, under the 2.5% threshold
    assert deduction_for([None]) == 0.0                   # no price seen: nothing deducted
    assert deduction_for([1.5, 1.5]) == 0.75              # capped at 75c
    assert settle_struck(1.0, True, 5.0, 0.25) == 4.0     # 1 + 4 x 0.75
    assert settle_struck(1.0, True, 5.0, None) == 5.0
    assert settle_struck(1.0, False, 5.0, 0.25) == 0.0


def test_void_bets_are_left_out_of_every_figure():
    from fk.paper import summarise, summarise_at_struck
    bets = [dict(plan="value_flags", stake=1.0, returned=5.0, won=True, price=4.0, deduction=0.25),
            dict(plan="value_flags", stake=1.0, returned=1.0, won=None, price=9.0, void=True)]
    s = summarise(bets)["value_flags"]
    assert (s.bets, s.staked, s.returned) == (1, 1.0, 5.0)
    t = summarise_at_struck(bets)["value_flags"]
    assert (t.bets, t.returned) == (1, 1.0 + 3.0 * 0.75)  # the winner at $4 less a 25c deduction


def test_a_refit_does_not_start_a_new_scoreboard():
    from fk.paper import model_family
    assert model_family("market_kitchen_sink (1330 races to 2026-09-22)") == model_family(
        "market_kitchen_sink (4100 races to 2026-09-29)") == "market_kitchen_sink"
    assert model_family("form_only (before the market model)") == "form_only"
    assert model_family(None) == "unrecorded"
