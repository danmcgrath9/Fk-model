"""The paper book. Pure, hand-tested.

Every plan is a rule over one race's summary rows (what the page shows before the race):
which runners to back and for how many units. Bets are placed at the market price on the
page and settled at Betfair SP. summarise() turns settled bets into the running account
per plan, so "would we be ahead" is a chart with a sample behind it.
"""
from __future__ import annotations

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

PLANS = {
    "top_pick": "the model's top-rated runner, one unit",
    "value_flags": "every runner flagged Neural > market (5+ points of value), one unit",
    "value_under_8": "value flags rated under $8, one unit",
    "top_pick_to_win_1": "the top pick, staked to win one unit at the morning price",
    "kelly_quarter": "quarter Kelly on a 100-unit bank from the model's chance and the morning price, capped at 5 units",
}


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
        if r.flag == "model_higher":
            bet("value_flags", r, UNIT)
            if r.rated_price and r.rated_price < 8:
                bet("value_under_8", r, UNIT)
        bet("kelly_quarter", r, kelly_stake(r.model_prob, r.price))
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


# Deductions. A runner scratched after a fixed-odds bet is struck takes a share of that
# bet's winnings: roughly the scratched runner's chance at its last price, the basis of both
# the Australian bookmakers' tables and Betfair's reduction factors. Runners under 2.5% take
# nothing (Betfair's threshold), and the total is capped at 75c in the dollar.
DEDUCTION_MIN = 0.025
DEDUCTION_CAP = 0.75


def deduction_for(scratched_prices: list[float | None]) -> float:
    """Share of winnings deducted for late scratchings, from each scratched runner's last
    price. Hand-checked: $4 and $41 scratched -> 1/4 = 0.25 counts, 1/41 = 0.024 is under
    2.5% and does not -> 0.25. A runner with no price seen deducts nothing (unknown)."""
    d = sum(1.0 / p for p in scratched_prices if p and p > 1 and 1.0 / p >= DEDUCTION_MIN)
    return min(d, DEDUCTION_CAP)


def settle_struck(stake: float, won: bool, price: float, deduction: float | None) -> float:
    """Units back at the struck price after deductions, which come off the winnings, not
    the stake. Hand-checked: 1 unit at $5, 25c deduction -> 1 + 4 x 0.75 = 4.0."""
    if not won:
        return 0.0
    return stake + stake * (price - 1.0) * (1.0 - (deduction or 0.0))


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
