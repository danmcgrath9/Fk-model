from fk.paper import Bet, Row, kelly_stake, place, running, settle, summarise


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
