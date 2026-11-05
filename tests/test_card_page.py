"""research/greyhound/card_page.py: the TAB-open stake ladder, by hand, and a page that renders it."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import card_page as CP  # noqa: E402


def test_stake_grows_with_how_far_tab_is_over_our_price():
    # ours $4 (25%), TAB's margin 25%: pk = 0.125 + 0.5 x (1/price) / 1.25
    assert CP.stake(0.25, 5.0) == 0.0                                  # 1.25x: under the 1.3x line, no bet
    assert abs(CP.stake(0.25, 5.2) - 75 * 0.05 / 4.2) < 1e-9            # 1.3x: pk x 5.2 = 1.05, 0.89 units
    assert abs(CP.stake(0.25, 6.0) - 75 * 0.15 / 5.0) < 1e-9            # 1.5x: pk x 6 = 1.15, 2.25 units
    assert CP.stake(0.25, 8.0) == 4.0                                  # 2x: 4.29 units, capped at 4
    assert abs(CP.stake(0.25, 5.2, book=1.0) - 75 * 0.15 / 4.2) < 1e-9  # no margin taken out: 2.68 units


def test_no_ladder_outside_the_two_to_fifteen_dollar_band():
    assert CP.ladder(0.6) == [] and CP.stake(0.6, 10.0) == 0.0          # ours $1.67
    assert CP.ladder(0.05) == [] and CP.stake(0.05, 40.0) == 0.0        # ours $20
    lad = CP.ladder(0.25)
    assert [m for m, _, _ in lad] == list(CP.LADDER) and [round(pr, 2) for _, pr, _ in lad] == [5.2, 6.0, 8.0, 12.0]
    assert [u for _, _, u in lad] == sorted(u for _, _, u in lad)       # more units the more TAB is out


def test_page_lists_the_watch_dogs_and_prices_a_known_open():
    rows = [["1", "FAST ONE", 0.40, 2.2, "90", 1, 0, "1-1", []],
            ["2", "LONG ONE", 0.25, 6.5, "80", 2, 0, "2-3", []],
            ["3", "SHORT GRV", 0.20, 4.0, "70", 0, 0, "4-4", []],
            ["4", "OUTSIDER", 0.15, 12.0, "60", 0, 0, "6-6", []]]
    card = {"day": "2026-11-05", "fit": 100, "rounds": 10, "fam": [], "tracks": ["Sandown Park"], "edges": [],
            "races": [{"t": "Sandown Park", "n": "1", "s": "2026-11-05T08:00:00.000Z", "d": 515, "g": "5", "b": 1.2, "r": rows}]}
    out = CP.page(card, {"Sandown Park|1|LONG ONE": [7.0, 6.0]}, "noon")
    head = out[out.index("Check these at TAB"):out.index("How to bet it")]
    # LONG ONE ($4 ours, GRV $6.50 = 1.63x) and OUTSIDER ($6.67, GRV $12 = 1.8x) are watched; FAST ONE (GRV 0.88x) and
    # SHORT GRV (GRV 0.8x) are not
    assert "Long One" in head and "Outsider" in head and "Fast One" not in head and "Short Grv" not in head
    assert "TAB opened $7.00: 1.75x" in head


def test_watch_list_leaves_out_races_already_run():
    from datetime import datetime, timezone
    rows = [["2", "LONG ONE", 0.25, 6.5, "80", 2, 0, "2-3", []], ["1", "FAV", 0.75, 1.3, "90", 1, 0, "1-1", []]]
    races = [{"t": "Sandown Park", "n": n, "s": s, "d": 515, "g": "5", "b": 1.2, "r": [list(x) for x in rows]}
             for n, s in (("1", "2026-11-05T08:00:00.000Z"), ("2", "2026-11-05T09:00:00.000Z"))]
    card = {"day": "2026-11-05", "fit": 1, "rounds": 1, "fam": [], "tracks": ["Sandown Park"], "edges": [], "races": races}
    out = CP.page(card, {}, "8:30pm", datetime(2026, 11, 5, 8, 30, tzinfo=timezone.utc))
    head = out[out.index("Check these at TAB"):out.index("How to bet it")]
    assert "(1)" in head and "1 more in races already run" in head and "R2" in head and "R1</a>" not in head


def test_speed_map_line_and_early_reasons_when_the_card_carries_them():
    rows = [["1", "LEADER", 0.30, 3.6, "100", 1, 0, "3-2", [], 1, 0.6, 0],
            ["2", "CHASER", 0.25, 4.0, "90", 2, 0, "2-2", [], 2, 0.2, 1],
            ["3", "OLD CARD", 0.45, 2.0, "80", 0, 0, "1-1", []]]            # a card written before the map: no fields
    card = {"day": "2026-11-05", "fit": 1, "rounds": 1, "fam": [], "tracks": ["Shepparton"], "edges": [],
            "races": [{"t": "Shepparton", "n": "1", "s": "2026-11-04T23:40:00.000Z", "d": 390, "g": "Maiden", "b": 1.2,
                       "r": rows}]}
    out = CP.page(card, {}, "noon")
    assert "fastest early on past splits: 1. Leader" in out and "leads most often: 1. Leader (60% of its runs)" in out
    assert "led at the first point in 20% of its last 10" in out and "1 quicker beginner drawn inside it" in out
    assert "2nd fastest early on past splits" in out


def test_rule_panel_lists_the_cards_bets_in_jump_order():
    rows = [["1", "A DOG", 0.25, 6.5, "80", 2, 0, "2-3", []]]
    races = [{"t": "Sandown Park", "n": n, "s": s, "d": 515, "g": "5", "b": 1.2, "r": [list(x) for x in rows]}
             for n, s in (("2", "2026-11-05T09:00:00.000Z"), ("1", "2026-11-05T08:00:00.000Z"))]
    card = {"day": "2026-11-05", "fit": 1, "rounds": 1, "fam": [], "tracks": ["Sandown Park"], "edges": [], "races": races,
            "bets": [["Sandown Park", "2", "1", "A DOG", 0.25, 0.2, 6.5, 1.5], ["Sandown Park", "1", "1", "A DOG", 0.25, 0.2, 6.5, 2.0]],
            "blend": [0.51, 0.66]}
    out = CP.page(card, {}, "noon")
    panel = out[out.index("The tested rule"):out.index("Check these at TAB")]
    assert "(2, 4 units)" in panel and panel.index("R1</a>") < panel.index("R2</a>") and "2.0u" in panel and "$6.50+" in panel
