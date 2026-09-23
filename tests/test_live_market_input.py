"""The live model's market input: the morning snapshot's opening price, and no bets on a
race whose market has not formed."""
import math
import sys
from pathlib import Path

from fixtures import race_entry

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_report as BR  # noqa: E402
from fk import backtest as B  # noqa: E402


def _entries(opens):
    out = []
    for i, o in enumerate(opens):
        raw = race_entry(f"H{i}", f"Horse {i}", i + 1)
        raw["odds"] = {"avgOpen": o} if o is not None else {}
        out.append({"horse_id": f"H{i}", "raw": raw})
    return out


def test_with_opening_fills_and_replaces_but_never_invents():
    raw = {"odds": {"avgOpen": 9.0, "avgNow": 8.0}, "x": 1}
    assert BR.with_opening(raw, 6.0)["odds"] == {"avgOpen": 6.0, "avgNow": 8.0}
    assert raw["odds"]["avgOpen"] == 9.0                      # the stored entry is untouched
    assert BR.with_opening({"x": 1}, 4.0)["odds"] == {"avgOpen": 4.0}
    assert BR.with_opening(raw, None) is raw and BR.with_opening(raw, 1.0) is raw


def test_open_coverage_counts_entry_or_snapshot():
    ents = _entries([3.0, None, None, None, None])
    assert BR.open_coverage(ents) == (1, 5)
    assert BR.open_coverage(ents, {"H1": 5.0, "H2": 9.0, "H3": 21.0}) == (4, 5)


def test_the_model_reads_the_snapshot_opening_not_the_evening_one():
    # A model that is the opening market and nothing else: its chances ARE the open.
    model = {"beta": {B.MARKET_FEATURE: 1.0}}
    ents = _entries([None, None, None])                      # the evening form had no market
    flat = BR.model_chances(model, ents)
    assert all(abs(p - 1 / 3) < 1e-9 for p in flat.values())  # every runner filled with the mean: the defect
    priced = BR.model_chances(model, ents, openings={"H0": 2.0, "H1": 4.0, "H2": 4.0})
    # 1/2, 1/4, 1/4 normalised = 0.5, 0.25, 0.25
    assert [round(priced[h], 6) for h in ("H0", "H1", "H2")] == [0.5, 0.25, 0.25]


def test_a_race_without_a_formed_market_is_not_bet():
    class NoDb:
        def ensure_paper_book(self):
            raise AssertionError("must not reach the database")
    section = BR.RaceSection(heading="R1", subheading="")
    section.bettable = False
    race = {"race_id": "R", "race_number": 1, "meeting_date": "2099-01-01", "raw": {"startTime": "11:59pm"}}
    assert BR.place_paper(NoDb(), race, section) == 0


def test_a_form_only_model_never_bets():
    class NoDb:
        def ensure_paper_book(self):
            raise AssertionError("must not reach the database")
    section = BR.RaceSection(heading="R1", subheading="")
    section.model_reads_market = False
    race = {"race_id": "R", "race_number": 1, "meeting_date": "2099-01-01", "raw": {"startTime": "11:59pm"}}
    assert BR.place_paper(NoDb(), race, section) == 0


def test_a_rating_miles_from_the_market_is_never_bet():
    from fk import paper as P
    # Pneuma, Geelong 23 Sep: $71 in the market (1.4%), rated $4.91 (20.4%): 14 times the market.
    far = P.Row("P", "Pneuma", 4.91, 71.0, 1 / 4.91, 1 / 71.0, "model_higher", None)
    fav = P.Row("F", "Fav", 2.2, 2.5, 1 / 2.2, 1 / 2.5, None, None)
    bets = P.place([far, fav])
    assert not any(b.horse_id == "P" and b.plan in ("value_flags", "value_under_8", "kelly_quarter") for b in bets)
    # the same gap at three times the market or less is still a bet: 0.30 against 0.12 is 2.5x
    near = P.Row("N", "Near", 1 / 0.30, 8.0, 0.30, 0.12, "model_higher", None)
    assert any(b.horse_id == "N" and b.plan == "value_flags" for b in P.place([near, fav]))


def test_the_model_reads_the_price_we_bet_at(monkeypatch):
    """A horse that opened $4 and drifted to $13 must be priced off $13, the price we bet at,
    or it looks like value by construction."""
    import inspect
    src = inspect.getsource(BR.build_section)
    assert '.get("current") or' in src          # current price first, the open only as a fallback
