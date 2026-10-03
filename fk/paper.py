"""The paper book. Pure, hand-tested.

Every plan is a rule over one race's summary rows (what the page shows before the race):
which runners to back and for how many units. Bets are placed at the market price on the
page and settled at Betfair SP. summarise() turns settled bets into the running account
per plan, so "would we be ahead" is a chart with a sample behind it.
"""
from __future__ import annotations

from pathlib import Path

import re

from dataclasses import dataclass

UNIT = 1.0
BANK = 100.0          # units the Kelly plan sizes against
KELLY_FRACTION = 0.25
KELLY_CAP = 5.0       # units, so one wild edge cannot dominate the book
# A value bet or a Kelly stake needs the model's chance to be no more than this many times
# the market's. A model that reads the market lands within that of it on any real edge; a
# rating further out (a $71 runner rated $4.91 is 14 times) is a data or model problem
# until shown otherwise, and it is exactly where Kelly stakes the most.
MAX_MODEL_TO_MARKET = 3.0
# No value plan backs a runner WE rate at this price or longer (founder, 23 Sep 2026: "get rid
# of any horse we rate over $50+"). A $50 chance is a 2% chance, and a bet on it is only value
# when the market has it at $60 or more, which is the one part of the market the books have
# beaten us in every time: 0 winners from every value bet struck at $16+ at the real prices.
# The top pick is untouched, since a top pick is never near the line.
MAX_RATED_PRICE = 50.0

PLANS = {
    "top_pick": "the model's top-rated runner, one unit",
    "value_flags": "every runner flagged Neural > market (5+ points of value), one unit",
    "value_under_8": "value flags rated under $8, one unit",
    "top_pick_to_win_1": "the top pick, staked to win one unit at the morning price",
    "kelly_quarter": "quarter Kelly on a 100-unit bank from the model's chance and the morning price, capped at 5 units",
    "value_ev20": "every runner whose chance on our numbers times the morning price beats 1.20 (worth 20c a unit or more), one unit",
    "value_ev05": "every runner worth 5c a unit or more at the morning price, one unit",
    "value_ev10": "every runner worth 10c a unit or more at the morning price, one unit",
    "value_tiered": "worth 5c to 10c: 1 unit; 10c to 20c: 2 units; 20c or more: 3 units (tracked, not recommended: the lower bands lose)",
    "value_ev20_kelly": "worth 20c a unit or more, staked quarter Kelly on a 100-unit bank: value / (price - 1) x 25, capped at 5 units",
    # The real-price model (fk/realprice.py): fitted on the races with a real 9am price, so it
    # is judged here against the price it was built to beat. Tracked, not recommended, until
    # the book says otherwise.
    "rp_top_pick": "the real-price model's top-rated runner, one unit",
    "rp_value_ev05": "every runner the real-price model makes worth 5c a unit or more at the current price, one unit",
    "rp_value_ev10": "every runner the real-price model makes worth 10c a unit or more at the current price, one unit",
    "rp_value_ev05_kelly": "real-price model, worth 5c or more, staked quarter Kelly on a 100-unit bank, capped at 5 units",
}
REAL_PRICE_PLANS = ("rp_top_pick", "rp_value_ev05", "rp_value_ev10", "rp_value_ev05_kelly")
# The FORM-ONLY price (config/form_price.json) against the OPENING price, struck at that price
# (founder, 24 Sep 2026: "I have access to every bookmaker, so I can bet opening price"). Form
# King's avgOpen is the AVERAGE bookmaker price at market open, so an account with every book
# takes the best opener, at least as long. Back-test on 1,083 races it never saw (24 May to
# 23 Sep): 20c+ value rated under $50 made +33% +/- 12% at the opening average and +6% +/- 11%
# at Betfair SP; on the 54 of them pulled live before the jump the same rule LOST 25% +/- 27%
# at the opening average. This book is the tie-breaker.
PLANS.update({
    "fo_top_pick": "the form-only price's top pick, one unit at the opening price",
    "fo_value_ev10": "form-only price x opening price beats 1.10, rated under $50, one unit at the opening price",
    "fo_value_ev20": "form-only price x opening price beats 1.20, rated under $50, one unit at the opening price",
})
FORM_PLANS = ("fo_top_pick", "fo_value_ev10", "fo_value_ev20")
# The value_ev20 rule, chosen by the 23 Sep back-test on 3,260 races: on the older three fifths
# +57% at the average opening price, on the newer two fifths it never saw +85% (1,239 bets,
# two standard errors clear), and +16% at Betfair SP. The live gap rule managed +17% on the
# newer racing, inside its margin of luck. The opening average is an upper bound, so the
# live book is the test of how much survives at a price we can actually take.
EV_THRESHOLD = 0.20


@dataclass
class Row:
    horse_id: str
    name: str
    rated_price: float | None
    price: float | None         # morning market price
    model_prob: float | None
    market_prob: float | None
    flag: str | None            # model_higher / market_higher / None
    finish: int | None = None   # already run: not a bet
    opening: float | None = None   # the market open, for the movement the bet lived through


@dataclass
class Bet:
    plan: str
    horse_id: str
    name: str
    stake: float
    price: float | None
    rated_price: float | None
    model_prob: float | None
    market_prob: float | None
    opening: float | None = None


def kelly_stake(p: float | None, price: float | None) -> float:
    """Quarter Kelly stake in units on BANK: f = (p*b - q) / b with b = price - 1, only when
    positive, capped. Hand-checked: p 0.3 at $5 -> b 4, f = (1.2 - 0.7) / 4 = 0.125,
    quarter of that on 100 units = 3.125."""
    if p is None or price is None or price <= 1:
        return 0.0
    b = price - 1
    f = (p * b - (1 - p)) / b
    if f <= 0:
        return 0.0
    return min(KELLY_CAP, KELLY_FRACTION * f * BANK)


def jump_time(meeting_date, start_time: str | None):
    """The race's scheduled start as an instant, from the meeting date and Form King's
    startTime string ("12:25pm", "1:05 pm", "13:05"), read in Melbourne time.
    None when the string cannot be read: an unknown jump time is never treated as future."""
    from datetime import date, datetime
    from zoneinfo import ZoneInfo
    if start_time is None or meeting_date is None:
        return None
    m = re.fullmatch(r"\s*(\d{1,2})[:.](\d{2})\s*([ap]m)?\s*", str(start_time), re.I)
    if not m:
        return None
    hour, minute, ampm = int(m.group(1)), int(m.group(2)), (m.group(3) or "").lower()
    if ampm == "pm" and hour < 12:
        hour += 12
    if ampm == "am" and hour == 12:
        hour = 0
    if hour > 23 or minute > 59:
        return None
    d = meeting_date if isinstance(meeting_date, date) else date.fromisoformat(str(meeting_date)[:10])
    return datetime(d.year, d.month, d.day, hour, minute, tzinfo=ZoneInfo("Australia/Melbourne"))


def before_the_jump(jump, now) -> bool:
    """A paper bet is only a bet if it is placed before the race is due to start. An
    unknown jump time refuses, because a price captured after the race is not a price
    anyone could have taken."""
    return jump is not None and now < jump


def place(rows: list[Row]) -> list[Bet]:
    """Every plan's bets for one race. A race with a result on any row is not bet on."""
    if not rows or any(r.finish is not None for r in rows):
        return []
    rated = [r for r in rows if r.rated_price]
    if not rated:
        return []
    top = min(rated, key=lambda r: r.rated_price)
    bets: list[Bet] = []

    def bet(plan: str, r: Row, stake: float) -> None:
        if stake > 0:
            bets.append(Bet(plan, r.horse_id, r.name, round(stake, 4), r.price, r.rated_price, r.model_prob, r.market_prob, r.opening))

    bet("top_pick", top, UNIT)
    if top.price and top.price > 1:
        bet("top_pick_to_win_1", top, UNIT / (top.price - 1))
    for r in rows:
        if r.model_prob and r.market_prob and r.model_prob > MAX_MODEL_TO_MARKET * r.market_prob:
            continue   # too far from the market to be an edge: not bet, whatever the plan
        if r.rated_price is not None and r.rated_price >= MAX_RATED_PRICE:
            continue   # rated too long to be trusted as value, whatever the price on offer
        ev = r.model_prob * r.price - 1.0 if r.model_prob and r.price and r.price > 1 else None
        if ev is not None and ev > EV_THRESHOLD:
            bet("value_ev20", r, UNIT)
            # The recommended bet: only the band that has made money, sized so the stake
            # shrinks as the price lengthens (20c of value at $41 is 0.5% of the bank at
            # full Kelly, not a flat unit).
            bet("value_ev20_kelly", r, kelly_stake(r.model_prob, r.price))
        if ev is not None and ev > 0.05:
            bet("value_ev05", r, UNIT)
            bet("value_tiered", r, UNIT * (3 if ev > 0.20 else 2 if ev > 0.10 else 1))
        if ev is not None and ev > 0.10:
            bet("value_ev10", r, UNIT)
        if r.flag == "model_higher":
            bet("value_flags", r, UNIT)
            if r.rated_price and r.rated_price < 8:
                bet("value_under_8", r, UNIT)
        bet("kelly_quarter", r, kelly_stake(r.model_prob, r.price))
    return bets


def place_real_price(rows: list[Row]) -> list[Bet]:
    """The real-price model's plans for one race, over rows whose model_prob and rated_price
    are that model's. Same guards as place(): no race already run, nothing more than three
    times the market's chance."""
    if not rows or any(r.finish is not None for r in rows):
        return []
    rated = [r for r in rows if r.rated_price]
    if not rated:
        return []
    bets: list[Bet] = []

    def bet(plan: str, r: Row, stake: float) -> None:
        if stake > 0:
            bets.append(Bet(plan, r.horse_id, r.name, round(stake, 4), r.price, r.rated_price, r.model_prob, r.market_prob, r.opening))

    bet("rp_top_pick", min(rated, key=lambda r: r.rated_price), UNIT)
    for r in rows:
        if r.model_prob and r.market_prob and r.model_prob > MAX_MODEL_TO_MARKET * r.market_prob:
            continue
        if r.rated_price is not None and r.rated_price >= MAX_RATED_PRICE:
            continue
        ev = r.model_prob * r.price - 1.0 if r.model_prob and r.price and r.price > 1 else None
        if ev is not None and ev > 0.05:
            bet("rp_value_ev05", r, UNIT)
            bet("rp_value_ev05_kelly", r, kelly_stake(r.model_prob, r.price))
        if ev is not None and ev > 0.10:
            bet("rp_value_ev10", r, UNIT)
    return bets


def place_form(rows: list[Row]) -> list[Bet]:
    """The form-only price's plans for one race. Each row's `price` is the OPENING price (the
    bet is struck there) and `model_prob` the form-only chance. Same guards as place(): no
    race already run, no runner rated $50 or longer in a value plan, nothing more than three
    times the opening market's chance."""
    if not rows or any(r.finish is not None for r in rows):
        return []
    rated = [r for r in rows if r.rated_price and r.price and r.price > 1]
    if not rated:
        return []
    bets: list[Bet] = []

    def bet(plan: str, r: Row) -> None:
        bets.append(Bet(plan, r.horse_id, r.name, UNIT, r.price, r.rated_price, r.model_prob, r.market_prob, r.opening))

    bet("fo_top_pick", min(rated, key=lambda r: r.rated_price))
    for r in rated:
        if r.model_prob and r.market_prob and r.model_prob > MAX_MODEL_TO_MARKET * r.market_prob:
            continue
        if r.rated_price >= MAX_RATED_PRICE:
            continue
        ev = r.model_prob * r.price - 1.0 if r.model_prob else None
        if ev is not None and ev > 0.10:
            bet("fo_value_ev10", r)
        if ev is not None and ev > 0.20:
            bet("fo_value_ev20", r)
    return bets


def movement(struck: float | None, settled: float | None) -> float | None:
    """How the market moved between the price a bet was struck at and the price it settled
    at, as a share of the struck price. Negative = it FIRMED (shortened, the market came
    our way); positive = it DRIFTED. None when either price is missing.
    Hand-checked: struck $5.00, settled $4.00 -> (4 - 5) / 5 = -0.20, firmed 20%."""
    if not struck or not settled or struck <= 1 or settled <= 1:
        return None
    return (settled - struck) / struck


def movement_summary(settled: list[dict]) -> dict[str, dict]:
    """Per plan: how many settled bets carry both prices, the median movement from struck
    to settled, and the share that firmed. A plan whose selections drift is one the market
    disagrees with after we have backed them."""
    out: dict[str, dict] = {}
    for b in settled:
        m = movement(b.get("price"), b.get("settle_price"))
        if m is None:
            continue
        out.setdefault(b["plan"], {"n": 0, "moves": [], "firmed": 0})
        row = out[b["plan"]]
        row["n"] += 1
        row["moves"].append(m)
        row["firmed"] += 1 if m < 0 else 0
    for row in out.values():
        moves = sorted(row.pop("moves"))
        row["median"] = moves[len(moves) // 2] if len(moves) % 2 else (moves[len(moves) // 2 - 1] + moves[len(moves) // 2]) / 2
        row["firmed_share"] = row["firmed"] / row["n"]
    return out


# Deductions. A runner scratched after a fixed-odds bet is struck takes a cut of that bet,
# set by the official scale on the scratched runner's fixed price at the time it was
# withdrawn: Tabcorp's published "Schedule of Deductions for Fixed Odds Racing Betting"
# (NSW and Victoria; help.tab.com.au, fetched 3 Oct 2026), kept in config/tab_deductions.csv.
# Every scratched runner's win deduction is looked up and they ADD (TABtouch: "simply add the
# deductions together"); a price over $51 deducts nothing. The cut comes off the WHOLE price
# (the ticket's face value), not just the winnings: $10 with 50c of deductions pays $5.
# Until 3 Oct this used 1/price capped at 75c, which overstated it (Warrnambool R5: 48c
# estimated against TAB's 31c).
DEDUCTION_TABLE = Path(__file__).resolve().parent.parent / "config" / "tab_deductions.csv"
_SCALE: list[tuple[float, float, int]] | None = None


def deduction_scale() -> list[tuple[float, float, int]]:
    """(price_from, price_to, win_cents) rows of the official scale, read once."""
    global _SCALE
    if _SCALE is None:
        import csv
        with open(DEDUCTION_TABLE, newline="") as fh:
            _SCALE = [(float(r["price_from"]), float(r["price_to"]), int(r["win_cents"])) for r in csv.DictReader(fh)]
    return _SCALE


def win_deduction(price: float | None) -> float:
    """Win deduction for one scratched runner at this fixed price, as a share of the dollar.
    Hand-checked against the scale: $2.00 -> 0.47, $3.00 -> 0.31, $41.00 -> 0.02, $60 -> 0."""
    if not price or price <= 1.0:
        return 0.0
    p = round(price, 2)
    for lo, hi, cents in deduction_scale():
        if lo <= p <= hi:
            return cents / 100.0
    return 0.0


def model_family(label: str | None) -> str:
    """The kind of model a bet was priced by, for the live scoreboard: whether it reads the
    morning market or prices from form alone. The weekly refit, and the fit switching between
    close cousins (the market model with or without the first-starter terms), are the same
    strategy getting sharper; only reading the market or not changes what is being tested.
    'market_kitchen_sink (1330 races to 2026-09-22)' -> 'reads the market'."""
    if not label:
        return "unrecorded"
    name = label.split(" (")[0].strip()
    if name.startswith("realprice"):
        return "real-price refit"
    if name.startswith("market_") or name.endswith("open_market"):
        return "reads the market"
    return "form only"


def deduction_for(scratched_prices: list[float | None]) -> float:
    """Total deduction for late scratchings: each scratched runner's scale deduction at its
    last fixed price, added together, never more than the whole dollar. A runner with no
    price seen deducts nothing (unknown). Hand-checked: $4.00 and $41 scratched -> 0.23 + 0.02 = 0.25."""
    return min(sum(win_deduction(p) for p in scratched_prices), 1.0)


def settle_struck(stake: float, won: bool, price: float, deduction: float | None) -> float:
    """Units back at the struck price after deductions, taken off the WHOLE price (the face
    value of the ticket), as the bookmaker pays. Hand-checked: 1 unit at $5 with 25c of
    deductions -> 5 x 0.75 = 3.75; at $10 with 50c -> 5.0."""
    if not won:
        return 0.0
    return stake * price * (1.0 - (deduction or 0.0))


def settle(stake: float, won: bool, settle_price: float | None) -> float:
    """Units returned: stake x price on a winner, nothing on a loser; a winner with no
    settlement price returns the stake (void), never a guess."""
    if not won:
        return 0.0
    if settle_price is None or settle_price <= 1:
        return stake
    return stake * settle_price


@dataclass
class PlanSummary:
    plan: str
    bets: int
    winners: int
    staked: float
    returned: float

    @property
    def profit(self) -> float:
        return self.returned - self.staked

    @property
    def roi(self) -> float | None:
        return (self.returned / self.staked - 1) if self.staked else None


def summarise_at_struck(settled: list[dict]) -> dict[str, PlanSummary]:
    """The same bets paid at the price they were STRUCK at rather than at Betfair SP.
    The book decides at the morning market and settles at BSP, which is coherent only if
    you bet into BSP; a punter who actually took the morning price gets the price on the
    screen. Where the selections drift, BSP is the longer price and the book flatters the
    plan, so both bases belong side by side. A bet with no struck price is skipped."""
    out: dict[str, PlanSummary] = {}
    for b in settled:
        price = b.get("price")
        if b.get("void") or not price or price <= 1:
            continue
        s = out.setdefault(b["plan"], PlanSummary(b["plan"], 0, 0, 0.0, 0.0))
        s.bets += 1
        s.winners += 1 if b.get("won") else 0
        s.staked += float(b["stake"])
        s.returned += settle_struck(float(b["stake"]), bool(b.get("won")), float(price),
                                    float(b["deduction"]) if b.get("deduction") is not None else None)
    return out


def summarise(settled: list[dict]) -> dict[str, PlanSummary]:
    """settled: dicts with plan, stake, returned, won. Per-plan totals. A void bet (the horse
    was scratched after the bet) is no bet at all and is left out."""
    out: dict[str, PlanSummary] = {}
    for b in settled:
        if b.get("void"):
            continue
        s = out.setdefault(b["plan"], PlanSummary(b["plan"], 0, 0, 0.0, 0.0))
        s.bets += 1
        s.winners += 1 if b.get("won") else 0
        s.staked += float(b["stake"])
        s.returned += float(b.get("returned") or 0.0)
    return out


def running(settled: list[dict]) -> dict[str, list[tuple[str, float]]]:
    """Cumulative profit per plan in bet order (meeting_date, race_number, bet_id):
    [(label, cumulative units), ...]."""
    out: dict[str, list[tuple[str, float]]] = {}
    for b in sorted(settled, key=lambda b: (str(b.get("meeting_date")), b.get("race_number") or 0, b.get("bet_id") or "")):
        seq = out.setdefault(b["plan"], [])
        prev = seq[-1][1] if seq else 0.0
        seq.append((f"{b.get('meeting_date')} R{b.get('race_number')}", prev + float(b.get("returned") or 0.0) - float(b["stake"])))
    return out
