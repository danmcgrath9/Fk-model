import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "research", "greyhound"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import card_page as C  # noqa: E402
import topaz_morning as M  # noqa: E402
import topaz_sheet as S  # noqa: E402


def test_ladder_with_no_correction_is_tab_s_own_chance():
    # no correction rounds: the best model is TAB's book itself. Three dogs, the other two predicted at 1 / price 0.35
    # and 0.25. Dog 0 at $4.00: 0.25 / (0.25 + 0.35 + 0.25) = 0.29412; at $2.00: 0.5 / 1.1 = 0.45455
    X = pd.DataFrame({"lp_ours": [0.0, 0.0, 0.0], "lp_tab": 0.0, "gap": 0.0, "tab_book": 0.0})
    inv = np.array([0.3, 0.35, 0.25])
    P = S.ladder_race(X, np.log([0.4, 0.35, 0.25]), inv, None, list(X.columns), grid=np.array([2.0, 4.0]))
    assert P.shape == (3, 2)
    assert np.isclose(P[0, 1], 0.25 / 0.85) and np.isclose(P[0, 0], 0.5 / 1.1)
    # dog 1 at $2.00: 0.5 / (0.3 + 0.5 + 0.25)
    assert np.isclose(P[1, 0], 0.5 / 1.05)


def test_ladder_rebuilds_the_price_inputs_for_the_whole_field():
    # a stand-in correction that adds tab_book to every dog's score: the own dog's chance must still be the share of
    # its race, and every dog in the race is scored with the same rebuilt book (so the shift cancels)
    class Fake:
        def predict(self, Z, raw_score=True):
            return Z.tab_book.values * 1.0

    X = pd.DataFrame({"lp_ours": [0.0, 0.0], "lp_tab": 0.0, "gap": 0.0, "tab_book": 0.0})
    P = S.ladder_race(X, np.zeros(2), np.array([0.5, 0.6]), Fake(), list(X.columns), grid=np.array([2.5]))
    # dog 0 at $2.50: 0.4 / (0.4 + 0.6) = 0.4, the book's shift adds the same to both scores
    assert np.isclose(P[0, 0], 0.4)


def test_bands_need_the_bet_at_both_ends_and_take_the_smaller_stake():
    # chance 0.30 at every price on a ladder of $3, $4, $5, $6: the 2-point margin holds to $3 (0.333 > 0.30? no),
    # $4 (0.30 - 0.25 = 5 pts), $5 (10 pts), $6 (13.3 pts); so bands $4-$5 and $5-$6
    grid = np.array([3.0, 4.0, 5.0, 6.0])
    P = np.full((1, 4), 0.30)
    b = S.bands(P, grid)
    assert [(lo, hi) for _, lo, hi, _ in b] == [(4.0, 4.99), (5.0, 5.99)]
    # quarter Kelly at $4: 0.25 x (1.2 - 1) / 3 = 0.016667; at $5: 0.25 x 0.5 / 4 = 0.03125; at $6: 0.25 x 0.8 / 5 =
    # 0.04: each band takes its smaller end
    assert np.isclose(b[0][3], 0.0167, atol=1e-4) and np.isclose(b[1][3], 0.0312, atol=1e-4)


def test_bands_leave_a_fair_price_over_15_dollars():
    grid = np.array([20.0, 25.0])
    assert S.bands(np.full((1, 2), 0.06), grid) == []          # fair $16.67


def test_bands_tile_the_prices_to_the_cent():
    lo = [b[1] for b in S.bands(np.full((1, len(S.GRID)), 0.9), S.GRID)]
    hi = [b[2] for b in S.bands(np.full((1, len(S.GRID)), 0.9), S.GRID)]
    # every band starts one cent after the one before ends: a TAB price fires exactly one order
    assert all(np.isclose(a + 0.01, b) for a, b in zip(hi[:-1], lo[1:]))


def test_usual_book_by_field_size():
    d = pd.to_datetime(["2026-10-01"] * 40 + ["2026-10-02"] * 10 + ["2025-01-01"])
    race = np.arange(51)
    book = np.r_[np.full(40, 1.20), np.full(10, 1.30), [2.0]]
    n = np.r_[np.full(40, 8), np.full(10, 6), [8]]
    b = S.usual_book(d, race, book, n)
    # the January 2025 race is outside the six months; size 6 has only 10 races, so it takes the overall median
    assert b["by_n"] == {"8": 1.2} and np.isclose(b["all"], 1.2)
    assert S.book_for(6, b) == 1.2 and S.book_for(8, b) == 1.2


def test_fired_takes_the_band_tab_s_first_price_is_in():
    sheet = pd.DataFrame({"day": "2026-11-21", "race_key": "2026-11-21|The Meadows|2", "venue": "The Meadows",
                          "race_no": "2", "box": "7", "dog_name": "SPHINX KEEPING", "dog": "1",
                          "low": [2.10, 2.40], "high": [2.39, 2.74], "stake": [0.02, 0.031]})
    facts = pd.DataFrame({"date": pd.to_datetime(["2026-11-21", "2026-11-21"]), "dog_name": ["Sphinx Keeping", "Kyenna"],
                          "price": [2.40, 3.4], "tab_first_t": "2026-11-20T20:10:35Z", "venue": "The Meadows",
                          "race_no": "2", "start": "2026-11-21T08:19:00Z", "bw_race": "r1"})
    f = S.fired(sheet, facts)
    assert len(f) == 1 and f[0]["low"] == 2.40 and f[0]["kelly"] == 0.031 and f[0]["tab_open"] == 2.40
    # a first price outside every band fires nothing
    assert S.fired(sheet, facts.assign(price=[2.80, 3.4])) == []


def test_sheet_detect_is_placed_at_tab_s_first_price():
    races = [{"id": "r1", "track": "The Meadows", "number": 2, "runners": [
        {"name": "Sphinx Keeping", "number": 7, "books": {"Tab": {"flucs": [[2.2, "2026-11-20T20:30:00Z"]]}}}]}]
    rows = [{"model": S.SHEET, "venue": "The Meadows", "race_no": "2", "start": "x", "box": "7", "dog": "SPHINX KEEPING",
             "low": 2.4, "high": 2.74, "kelly": 0.031, "tab_open": 2.4, "tab_open_at": "t", "bw_race": "r1"}]
    from datetime import datetime, timezone
    b = M.sheet_detect(rows, races, datetime(2026, 11, 20, 20, 31, tzinfo=timezone.utc), "2026-11-21")[0]
    # a market-open order is paid TAB's first price, even if TAB has cut it since
    assert b["placed"] and b["tab_at_detect"] == 2.4 and b["number"] == 7 and b["bw_race"] == "r1"
    s = M.settle([b], [{**races[0], "results": [[7]]}])[0]
    assert s["won"] and np.isclose(s["profit"], 1.4)


def test_card_page_groups_a_dog_s_orders():
    races = [{"t": "Meadows (MEP)", "n": "2", "s": "2026-11-21T08:19:00Z", "r": [["7.0", "SPHINX KEEPING", 0.5]]}]
    sheet = [["The Meadows", "2", "7.0", "SPHINX KEEPING", 2.10, 2.39, 0.02],
             ["The Meadows", "2", "7.0", "SPHINX KEEPING", 2.40, 2.74, 0.031],
             ["The Meadows", "2", "7.0", "SPHINX KEEPING", 3.20, 3.59, 0.04]]
    d = C.sheet_dogs(sheet, races)
    assert len(d) == 1 and d[0][0] is races[0]
    # the first two orders touch and join; the third is its own range
    assert d[0][6] == [[2.10, 2.74], [3.20, 3.59]]
    out = []
    C.sheet_section(out.append, sheet, races, lambda r: False)
    assert "3 orders" in "".join(out) and "$2.10-$2.74" in "".join(out).replace("&#36;", "$") and "$200-$400" in "".join(out) and "1.07u-2.14u" in "".join(out)


def test_betmatic_orders_are_one_market_open_order_a_band():
    o = pd.DataFrame({"day": "2026-11-21", "race_key": "k", "venue": "The Meadows", "race_no": "2", "box": "7.0",
                      "dog_name": "SPHINX KEEPING", "dog": "1", "low": [2.10, 2.40], "high": [2.39, 2.74],
                      "stake": [0.0213, 0.031]})
    b = S.betmatic_orders(o)
    assert list(b.number) == ["7", "7"] and list(b.venue) == ["THE MEADOWS"] * 2
    # stake_units is percent of the bank: 2.13% and 3.1%
    assert list(b.stake_units) == [2.13, 3.1] and list(b.min_odds) == [2.10, 2.40] and list(b.max_odds) == [2.39, 2.74]


def test_sender_labels_and_venues_for_greyhounds():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "betmatic"))
    import betmatic_send as BS
    o = {"date": "2026-11-21", "venue": "Bendigo", "race": "3", "number": "4"}
    # a greyhound order at Bendigo never shares a label with a gallops order there the same day
    assert BS.label(o, 1, code="Greyhounds").startswith("gh-") and BS.label(o, 1).startswith("fk-")
    assert BS.vnorm("The Meadows") == BS.vnorm("MEADOWS") == "meadows" and BS.vnorm("Theodore") == "theodore"
    assert BS.skip_reason("No. 7 is 'X' on BetMatic, not 'Y'") == "another runner at that number"


def test_a_market_tab_opened_before_the_sheet_is_not_placed():
    # 21 Nov 2026: TAB priced Sandown on Wednesday 18 Nov at 2:38pm, three days before the race and two days before
    # the sheet; Ballarat opened at 8:10am on race day, after it
    races = [{"id": "r1", "track": "Sandown Park", "number": 2, "runners": [
        {"name": "Blue Storm", "number": 6, "books": {"Tab": {"flucs": [[6.0, "2026-11-18T03:38:13.32Z"]]}}}]}]
    from datetime import datetime, timezone
    now = datetime(2026, 11, 20, 19, 45, tzinfo=timezone.utc)
    early = {"model": S.SHEET, "venue": "Sandown Park", "race_no": "2", "start": "x", "box": "6", "dog": "BLUE STORM",
             "low": 5.64, "high": 6.42, "kelly": 0.0315, "tab_open": 6.0, "tab_open_at": "2026-11-18T03:38:13.32Z",
             "bw_race": "r1"}
    late = {**early, "tab_open_at": "2026-11-20T21:10:58Z"}
    a, b = M.sheet_detect([early, late], races, now, "2026-11-21")
    assert not a["placed"] and b["placed"]
    # the sheet's own time wins over the 11pm fallback: an open at 10pm the night before, after a 9pm sheet, fires
    c = M.sheet_detect([{**early, "tab_open_at": "2026-11-20T11:00:00Z", "sheet_at": "2026-11-20T10:00:00Z"}], races,
                       now, "2026-11-21")[0]
    assert c["placed"]
    # a row kept placed before the rule is re-marked; a settled one is left as it was
    kept = [{**a, "placed": True}, {**a, "placed": True, "settled": True}]
    assert [r["placed"] for r in M.recheck_sheet(kept)] == [False, True]
    assert "(1 missed: TAB opened the market before the card was made)" in M.summary([a, b])


def test_fired_carries_the_sheet_s_time():
    sheet = pd.DataFrame({"day": "2026-11-21", "race_key": "k", "venue": "The Meadows", "race_no": "2", "box": "7",
                          "dog_name": "SPHINX KEEPING", "dog": "1", "low": [2.40], "high": [2.74], "stake": [0.031],
                          "made_at": "2026-11-20T12:05:00+00:00"})
    facts = pd.DataFrame({"date": pd.to_datetime(["2026-11-21"]), "dog_name": ["Sphinx Keeping"], "price": [2.40],
                          "tab_first_t": "2026-11-20T20:10:35Z", "venue": "The Meadows", "race_no": "2",
                          "start": "2026-11-21T08:19:00Z", "bw_race": "r1"})
    assert S.fired(sheet, facts)[0]["sheet_at"] == "2026-11-20T12:05:00+00:00"
