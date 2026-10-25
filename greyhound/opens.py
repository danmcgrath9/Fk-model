"""Recording greyhound opening prices ourselves (founder, 25 Oct 2026: "let's record it ourselves from now on").

No history of timestamped bookmaker opens exists for Australian dogs (research/greyhound/README.md), so we build one:
our own BetMatic bot reads every bookmaker's price for a race on request, and this module turns those readings into
an opening price per runner per bookmaker, with the time window the open happened in.

THE OPEN IS A WINDOW, NOT A GUESS. A race is polled until a bookmaker first shows a price. The open happened after the
last poll that saw no price from that bookmaker and at or before the first poll that saw one. Both times are kept. A
bookmaker that was already priced the first time we looked has NO known open (`open_known` False): its first price is
recorded, but it is a later price, and the model's open-price test must not use it as an open. That is the gallops
lesson (back-filled opens +41.9% against live opens -11.6%): a price that is not the open, called an open, is the
expensive mistake.

Pure: no network, no clock. betmatic/greyhound_opens.py does the polling.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

SYDNEY = ZoneInfo("Australia/Sydney")   # BetMatic's days are Sydney days (API reference, List Bets)

# Victorian greyhound tracks, for when a schedule row carries no state. Normalised: letters only, upper case.
VIC_TRACKS = {"BALLARAT", "BENDIGO", "CRANBOURNE", "GEELONG", "HEALESVILLE", "HORSHAM", "THEMEADOWS", "MEADOWS",
              "SALE", "SANDOWN", "SANDOWNPARK", "SHEPPARTON", "TRARALGON", "WARRAGUL", "WARRNAMBOOL"}


def norm(s) -> str:
    return re.sub(r"[^A-Z]", "", str(s).upper())


def parse_start(s) -> datetime | None:
    """BetMatic's startTime as an aware datetime. A naive time is read as Sydney time (stated, not verified: the
    first run's summary prints a raw sample beside the parsed one so it can be checked)."""
    if not s:
        return None
    try:
        t = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=SYDNEY)


def state_of(row: dict) -> str | None:
    """The state a schedule row is in: from an alias like '#KYNETON#KYNETON VIC#KYNETON AUS#' when the row has one,
    else VIC if the venue is a known Victorian greyhound track, else unknown (None)."""
    alias = str(row.get("competition_alias") or row.get("alias") or "")
    m = re.search(r"\s(VIC|NSW|QLD|SA|WA|TAS|NT|ACT|NZ)#", alias.upper())
    if m:
        return m.group(1)
    return "VIC" if norm(row.get("name")) in VIC_TRACKS else None


@dataclass(frozen=True)
class Race:
    venue: str          # BetMatic's exact uppercase competition name
    number: int
    start: datetime     # aware
    start_raw: str

    @property
    def key(self) -> str:
        return f"{self.start.astimezone(SYDNEY).date().isoformat()}|{self.venue}|R{self.number}"


def select_races(rows: list[dict], now: datetime, state: str = "VIC", ahead: timedelta = timedelta(hours=30),
                 grace: timedelta = timedelta(minutes=2)) -> list[Race]:
    """The greyhound races worth polling now: in `state`, starting between now (less a grace) and now + ahead.

    An odds request names only venue and race number, and BetMatic answers for the NEXT race at that venue and number,
    so only the earliest upcoming race per (venue, number) is pollable; a later one (tomorrow's R3 at a track racing
    today) waits until today's has run, or its prices would be filed against the wrong race."""
    best: dict[tuple[str, int], Race] = {}
    for r in rows:
        if not isinstance(r, dict) or r.get("code") != "Greyhounds":
            continue
        if state and state_of(r) != state:
            continue
        t = parse_start(r.get("startTime"))
        if t is None or not (now - grace <= t <= now + ahead):
            continue
        race = Race(str(r.get("name", "")).upper(), int(r.get("event_number") or 0), t, str(r.get("startTime")))
        k = (race.venue, race.number)
        if race.number and (k not in best or race.start < best[k].start):
            best[k] = race
    return sorted(best.values(), key=lambda x: (x.start, x.venue, x.number))


def prices(answer) -> dict[tuple[str, str], float]:
    """{(runner number, bookmaker): win price} from one odds answer's data. Scratched runners and non-prices are
    left out. The answer shape is the one seen in the gallops logs: [{number, bookie_odds: [{name, win, scratched}]}]."""
    out = {}
    for r in answer or []:
        if not isinstance(r, dict):
            continue
        for b in r.get("bookie_odds") or []:
            if not isinstance(b, dict) or b.get("scratched"):
                continue
            try:
                w = float(b.get("win") or 0)
            except (TypeError, ValueError):
                continue
            if w > 1.0:
                out[(str(r.get("number")), str(b.get("name")))] = w
    return out


@dataclass
class BookOpen:
    """One bookmaker's market on one race."""
    last_closed: datetime | None = None   # last answered poll before this bookmaker's first price
    first_seen: datetime | None = None    # first poll with a price
    first: dict[str, float] = field(default_factory=dict)   # runner -> price at first_seen
    last_seen: datetime | None = None
    last: dict[str, float] = field(default_factory=dict)

    @property
    def open_known(self) -> bool:
        return self.first_seen is not None and self.last_closed is not None


@dataclass
class RaceBook:
    race: Race
    polls: int = 0
    answered: int = 0
    last_poll: datetime | None = None
    last_answered: datetime | None = None
    books: dict[str, BookOpen] = field(default_factory=dict)

    def record(self, at: datetime, answer) -> None:
        """One ANSWERED poll. Every answered poll before a bookmaker's first price is a reading of that bookmaker as
        closed, whether or not the bookmaker had appeared yet, so its open window starts at the last answered poll
        before its first price. Once a bookmaker has opened, a reading without it is a gap in the feed, not a market
        closing. An UNANSWERED poll is never a closed reading: no answer can mean the bot is offline."""
        p = prices(answer)
        by_book: dict[str, dict[str, float]] = {}
        for (num, book), w in p.items():
            by_book.setdefault(book, {})[num] = w
        for book, runners in by_book.items():
            bo = self.books.setdefault(book, BookOpen())
            if bo.first_seen is None:
                bo.first_seen, bo.first, bo.last_closed = at, dict(runners), self.last_answered
            bo.last_seen, bo.last = at, dict(runners)
        self.answered += 1
        self.last_answered = at

    def note_poll(self, at: datetime) -> None:
        self.polls += 1
        self.last_poll = at

    @property
    def tab_open(self) -> bool:
        b = self.books.get("TAB")
        return bool(b and b.first_seen)

    def due(self, now: datetime, every: timedelta, open_every: timedelta) -> bool:
        """Before TAB opens, poll every `every` (the open window is only as narrow as this). After, every `open_every`
        to see the price move, until the jump."""
        if now >= self.race.start:
            return False
        if self.last_poll is None:
            return True
        return now - self.last_poll >= (open_every if self.tab_open else every)

    def rows(self) -> list[dict]:
        """One row per runner per bookmaker that ever priced the race: the open window, the opening price and the
        latest price. Times are Sydney ISO strings."""
        iso = lambda t: t.astimezone(SYDNEY).isoformat(timespec="seconds") if t else ""
        out = []
        for book, bo in sorted(self.books.items()):
            if bo.first_seen is None:
                continue
            for num in sorted(set(bo.first) | set(bo.last), key=lambda n: (len(n), n)):
                out.append({
                    "date": self.race.start.astimezone(SYDNEY).date().isoformat(), "venue": self.race.venue,
                    "race": self.race.number, "start": iso(self.race.start), "runner": num, "bookie": book,
                    "open_known": bo.open_known, "closed_at": iso(bo.last_closed), "first_seen_at": iso(bo.first_seen),
                    "first_price": bo.first.get(num, ""), "last_seen_at": iso(bo.last_seen),
                    "last_price": bo.last.get(num, ""),
                })
        return out


ROW_FIELDS = ["date", "venue", "race", "start", "runner", "bookie", "open_known", "closed_at", "first_seen_at",
              "first_price", "last_seen_at", "last_price"]


def merge_rows(old: list[dict], new: list[dict]) -> list[dict]:
    """Combine a day's rows from an earlier run with this run's, one row per (date, venue, race, runner, bookie).
    The OPEN comes from whichever run saw the bookmaker first (a later run that found the market already priced has
    open_known False and must never replace an open an earlier run caught); the LATEST price comes from whichever saw
    it last. Times compare as instants, not strings, so a daylight-saving change cannot reorder them."""
    t = lambda s: datetime.fromisoformat(s) if s else None
    key = lambda r: (r["date"], r["venue"], str(r["race"]), str(r["runner"]), r["bookie"])
    out = {key(r): dict(r) for r in old}
    for r in new:
        k = key(r)
        if k not in out:
            out[k] = dict(r)
            continue
        m = out[k]
        if t(r["first_seen_at"]) < t(m["first_seen_at"]):
            for f in ("open_known", "closed_at", "first_seen_at", "first_price"):
                m[f] = r[f]
        if t(r["last_seen_at"]) > t(m["last_seen_at"]):
            m["last_seen_at"], m["last_price"] = r["last_seen_at"], r["last_price"]
    return sorted(out.values(), key=lambda r: (r["start"], r["venue"], int(r["race"]), r["bookie"],
                                               (len(str(r["runner"])), str(r["runner"]))))
