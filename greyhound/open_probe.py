"""Opening prices from BetMatic's own Market Open trigger (founder, 25 Oct 2026: "With betmatic there's a feature to
have a script waiting for market open").

THE METHOD. For every runner, a Market Open instruction to TAB that can never be filled: minimum odds $1,000 AND
maximum odds $1.01, a $1 stake, one attempt. When TAB's market opens, BetMatic's bot fires it, the odds check refuses
it before anything reaches TAB, and BetMatic keeps the refusal: `current_odds` (TAB's price the bot saw) and
`created_at` (when it fired). Our own gallops records prove the shape: 168 refusals "Current odds is less than the
notification odds.", amount 0, submit_time null, and Geelong R5's stamped 11:45:19 on the morning the founder saw TAB
open it at 11:45.

WHAT A RECORD IS, HONESTLY. It is TAB's price when BetMatic fired, which is the open only when BetMatic fired on time.
It has not always: Geelong 21 Oct R3 fired at 4:11pm and R1-R2 never fired (betmatic-book.md). So:
  - a record that fired within ALREADY_OPEN of our sending it says the market was already up when we sent: open_known
    False, never used as an open;
  - BetMatic's punctuality on dogs is checked against our own odds requests (betmatic/greyhound_opens.py) on test days
    before any record is trusted as an open.

SAFETY. The fill is impossible twice over (min above max), the stake is $1, one bookmaker, one session, one attempt,
no boosts, no SP. A record with any amount staked is reported loudly by `derive`. Pure module: no network.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta

from greyhound.opens import SYDNEY, parse_start, state_of

MIN_ODDS = 1000.0      # no greyhound is ever $1,000 at TAB
MAX_ODDS = 1.01        # and no runner can be both >= $1,000 and <= $1.01
STAKE = 1              # dollars; the worst case if BetMatic ever ignored both checks
ALREADY_OPEN = timedelta(minutes=2)


def label(day: str, venue: str, race: int, number: str) -> str:
    return f"gho-{day}-{re.sub(r'[^a-z0-9]', '', venue.lower())}-r{race}-n{number}"


def runners(row: dict) -> list[tuple[str, str]]:
    """(saddlecloth, name) from a schedule row: "runners" is comma separated, "runner_names" '#&#' separated
    (as betmatic_send.py reads them). Names are blank when the two lists do not line up."""
    nums = [x.strip() for x in str(row.get("runners") or "").split(",") if x.strip()]
    names = str(row.get("runner_names") or "").split("#&#")
    return [(n, names[i].strip() if len(names) == len(nums) else "") for i, n in enumerate(nums)]


def plan(rows: list[dict], now: datetime, state: str = "VIC", ahead: timedelta = timedelta(days=3),
         done: set[str] = frozenset()) -> list[dict]:
    """One instruction per runner in every upcoming greyhound race in `state`, minus labels already sent. Each carries
    its race's start_time, so BetMatic cannot fire it on a different day's race at the same venue and number."""
    out = []
    for r in rows:
        if not isinstance(r, dict) or r.get("code") != "Greyhounds" or (state and state_of(r) != state):
            continue
        t = parse_start(r.get("startTime"))
        if t is None or not (now < t <= now + ahead):
            continue
        venue, race = str(r.get("name", "")).upper(), int(r.get("event_number") or 0)
        day = t.astimezone(SYDNEY).date().isoformat()
        for num, name in runners(r):
            lab = label(day, venue, race, num)
            if lab not in done:
                out.append({"label": lab, "date": day, "venue": venue, "race": race, "number": num, "runner": name,
                            "start_time": r.get("startTime")})
    return out


def payload(p: dict, bookie_id: str, session: str) -> dict:
    if not str(session).isdigit():
        raise ValueError("session must be the numeric id: BetMatic ignores a non-numeric target_session and sends to "
                         "EVERY session (API reference, Create a Bet)")
    return {"type": "Fixed Wager", "sports": "RACING", "competition": p["venue"], "code": "Greyhounds",
            "event_number": int(p["race"]), "market": "Fixed Win", "selection": str(p["number"]), "stake": STAKE,
            "check_odds": True, "odds": MIN_ODDS, "check_max_odds": True, "max_odds": MAX_ODDS,
            "is_market_open": True, "max_attempts": 1, "delay_between_attempts": 1, "allow_double_bets": False,
            "take_sp": False, "boost_if_available": False, "spg_if_available": False,
            "bookies": str(bookie_id), "target_session": str(session), "start_time": p["start_time"],
            "label": p["label"]}


def derive(ledger_row: dict, records: list[dict]) -> dict:
    """One opening-price row from a ledger row and BetMatic's records for it.
    status: 'pending' (not fired yet), 'refused' (the expected outcome: price and time recorded), 'other' (fired
    with some other result), 'STAKED' (money went on: must never happen; reported loudly)."""
    rec = [x for x in records if isinstance(x, dict)]
    out = {k: ledger_row.get(k, "") for k in ("label", "date", "venue", "race", "number", "runner", "sent_at")}
    out.update(status="pending", tab_price="", fired_at="", open_known="", result="", amount="")
    if not rec:
        return out
    x = min(rec, key=lambda r: str(r.get("created_at") or ""))
    amount = sum(float(r.get("amount") or 0) for r in rec)
    fired = datetime.fromisoformat(str(x.get("created_at"))) if x.get("created_at") else None
    sent = datetime.fromisoformat(ledger_row["sent_at"]) if ledger_row.get("sent_at") else None
    out.update(tab_price=x.get("current_odds") or "", amount=amount,
               fired_at=fired.astimezone(SYDNEY).isoformat(timespec="seconds") if fired else "",
               result=f"{x.get('submit_result')}: {x.get('submit_error')}")
    out["status"] = ("STAKED" if amount > 0 else
                     "refused" if "less than the notification odds" in str(x.get("submit_error")).lower()
                     or "greater than" in str(x.get("submit_error")).lower() else "other")
    out["open_known"] = bool(fired and sent and fired - sent > ALREADY_OPEN and out["status"] == "refused")
    return out


DERIVED_FIELDS = ["label", "date", "venue", "race", "number", "runner", "sent_at", "status", "tab_price", "fired_at",
                  "open_known", "result", "amount"]
