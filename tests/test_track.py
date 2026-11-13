"""The live tracker (topaz_track): the card's bets as sent, settled at TAB's first price; the rule at TAB's open."""
import gzip
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_track as TR  # noqa: E402


def card_payload():
    """Two races of four. Race 1: GRV has dog A at $12 while ours says 25%, so the card's rule bets on it."""
    return {"day": "2026-11-10", "blend": [0.51, 0.66], "races": [
        {"t": "Healesville", "n": "1", "s": "", "r": [["1", "Dog A", 0.25, 12.0], ["2", "Dog B", 0.38, 2.2],
                                                       ["3", "Dog C", 0.23, 3.5], ["4", "Dog D", 0.14, 6.0]]},
        {"t": "Healesville", "n": "2", "s": "", "r": [["1", "Dog E", 0.25, 4.0], ["2", "Dog F", 0.25, 4.0],
                                                       ["3", "Dog G", 0.25, 4.0], ["4", "Dog H", 0.25, 4.0]]}]}


def fact(dog, price, p_book, ran=True, ded=0.0, won=0.0, bw="bw1", n="1", **kw):
    return {"date": "2026-11-10", "bw_race": bw, "venue": "Healesville", "race_no": n, "start": "", "dog_name": dog,
            "price": price, "p_book": p_book, "ran": ran, "s_later": 0.0, "n_later": 0, "ded": ded,
            "tab_first_t": "", "sportsbet_first": kw.get("sb", np.nan), "ladbrokes_first": np.nan, "won": won,
            "bsp": kw.get("bsp", np.nan)}


def test_the_cards_rule_is_the_nightly_rule():
    import topaz_price_upcoming as PU
    c = TR.cards_from_payload(card_payload())
    mine = TR.card_rule(c)
    card = c.rename(columns={"venue": "track_name", "race_no": "race_number"}).assign(
        race_id=c.race_key, track=c.venue, grv_pct=1 / c.grv_price)
    theirs, _ = PU.rule_bets(card)
    assert [(r.dog_name, round(r.units, 2)) for _, r in mine.iterrows()] == [(b[3], b[7]) for b in theirs]
    assert list(mine.dog_name) == ["Dog A"]


def test_a_card_bet_is_paid_at_tabs_first_price_less_the_deduction():
    c = TR.cards_from_payload(card_payload())
    inv = np.array([1 / 10, 1 / 2.1, 1 / 3.4, 1 / 6.5])
    facts = pd.DataFrame([fact(d, p, q, ded=0.05, won=w) for d, p, q, w in
                          zip(["Dog A", "Dog B", "Dog C", "Dog D"], [10.0, 2.1, 3.4, 6.5], inv / inv.sum(), [1, 0, 0, 0])])
    led, _ = TR.ledger(c, facts)
    a = led[led.variant == "card"].iloc[0]
    assert a.dog_name == "Dog A" and a.status == "won"
    assert np.isclose(a.paid, 1 + 9 * 0.95)                       # $10 less 5c in the dollar off the winnings
    assert np.isclose(a.units_won, a.units * 9 * 0.95)


def test_scratched_after_the_bet_is_a_refund_and_never_in_the_market_is_void():
    c = TR.cards_from_payload(card_payload())
    led, _ = TR.ledger(c, pd.DataFrame([fact("Dog A", 10.0, 0.1, ran=False)]))
    assert led[led.variant == "card"].status.iloc[0].startswith("refund")
    led, _ = TR.ledger(c, pd.DataFrame([fact("Dog B", 2.1, 0.5)]))
    a = led[led.variant == "card"].iloc[0]
    assert a.status.startswith("void") and a.units_won == 0


def test_the_card_bet_stays_a_bet_at_the_open_only_when_tab_is_still_1_3x_the_blend():
    c = TR.cards_from_payload(card_payload())
    p_blend = TR.card_rule(c).p_blend.iloc[0]
    short = 1.3 / p_blend - 0.5
    led, _ = TR.ledger(c, pd.DataFrame([fact("Dog A", short, 0.2)]))
    assert set(led.variant) == {"card"}
    led, _ = TR.ledger(c, pd.DataFrame([fact("Dog A", 1.3 / p_blend + 0.5, 0.1)]))
    assert set(led.variant) == {"card", "card_still"}


def test_the_rule_at_the_open_prices_a_race_only_when_every_dog_at_the_open_is_on_the_card():
    c = TR.cards_from_payload(card_payload())
    # race 2 at TAB's open: ours says 25% each; TAB has Dog E at $11 (its book's chance about 9%)
    prices = [11.0, 3.2, 3.2, 3.2]
    inv = 1 / np.array(prices)
    facts = [fact(d, p, q, bw="bw2", n="2", won=w) for d, p, q, w in
             zip(["Dog E", "Dog F", "Dog G", "Dog H"], prices, inv / inv.sum(), [1, 0, 0, 0])]
    led, cov = TR.ledger(c, pd.DataFrame(facts))
    o = led[led.variant == "open"]
    assert list(o.dog_name) == ["Dog E"] and o.status.iloc[0] == "won" and cov["priced"] == 1
    # a dog in TAB's field that the card never priced: the race is not priced at the open
    led, cov = TR.ledger(c, pd.DataFrame(facts + [fact("Dog Z", 20.0, 0.05, bw="bw2", n="2")]))
    assert cov["priced"] == 0 and (led.variant == "open").sum() == 0 if len(led) else cov["priced"] == 0


def test_a_saved_card_reads_back_as_the_sealed_card_does(tmp_path):
    import topaz_price_upcoming as PU
    card = pd.DataFrame({"track_name": ["Healesville"] * 4, "track": ["HVL"] * 4, "race_number": [2] * 4,
                         "start_time": [""] * 4, "box": [1, 2, 3, 4], "dog_name": ["Dog E", "Dog F", "Dog G", "Dog H"],
                         "p_model": [0.25] * 4, "grv_price": [4.0] * 4, "race_id": [7] * 4})
    f = PU.save_card(card, "2026-11-10", [0.51, 0.66], tmp_path)
    a = TR.cards_from_dir(str(tmp_path))
    b = TR.cards_from_payload(card_payload())
    b = b[b.race_no == "2"]
    assert f.exists() and list(a.race_key) == list(b.race_key) and list(a.box) == list(b.box)


def test_results_settle_a_dog_that_did_not_finish_as_beaten(tmp_path):
    rows = [{"meetingDate": "2026-11-10T00:00:00", "raceId": 1, "dogName": "Dog A", "place": None, "scratched": False},
            {"meetingDate": "2026-11-10T00:00:00", "raceId": 1, "dogName": "Dog B", "place": 1, "scratched": False},
            {"meetingDate": "2026-11-10T00:00:00", "raceId": 2, "dogName": "Dog C", "place": None, "scratched": False}]
    with gzip.open(tmp_path / "runs_VIC_2026-11.json.gz", "wt") as fh:
        json.dump(rows, fh)
    r = TR.topaz_results(str(tmp_path), ["2026-11-10"]).set_index("_dn").won
    assert r["DOGA"] == 0 and r["DOGB"] == 1 and np.isnan(r["DOGC"])   # race 2 has no result yet
