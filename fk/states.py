"""Which states a read covers (11 Nov 2026, founder: "I want the training for other states as well ... I want the same
model"). Every reader that used to take one state ("VIC") takes a list now, written the same way Form King's own
`states` parameter is: comma separated. "ALL" is the eight Australian states and territories; None is everything held,
as it always was. A plain "VIC" means exactly what it meant before, so nothing that passes "VIC" changes.

    parse("VIC")          -> ("VIC",)
    parse("vic, nsw")     -> ("VIC", "NSW")
    parse("ALL")          -> AUSTRALIA  (NZ and HK only when named)
    parse(None)           -> None       (everything held)
    matches("NSW", ("VIC",)) -> False
"""
from __future__ import annotations

from typing import Iterable

# Form King's state codes for Australian racing (NZ and HK are in the API too and are left out of ALL on purpose:
# they are not part of an all-states Australian model unless asked for by name).
AUSTRALIA = ("VIC", "NSW", "QLD", "SA", "WA", "TAS", "ACT", "NT")


def parse(state: str | Iterable[str] | None) -> tuple[str, ...] | None:
    if state is None:
        return None
    items = state.split(",") if isinstance(state, str) else list(state)
    out = tuple(dict.fromkeys(s.strip().upper() for s in items if s and s.strip()))
    if not out:
        return None
    if "ALL" in out:
        return tuple(dict.fromkeys(AUSTRALIA + tuple(s for s in out if s != "ALL")))
    return out


def matches(state: str | None, want: tuple[str, ...] | None) -> bool:
    return want is None or (state or "").upper() in want


def sql_param(state: str | Iterable[str] | None) -> list[str] | None:
    """For `(%s::text[] is null or m.state = any(%s::text[]))`."""
    p = parse(state)
    return None if p is None else list(p)


def label(state: str | Iterable[str] | None) -> str:
    p = parse(state)
    return "every state held" if p is None else ("all states" if p == AUSTRALIA else ",".join(p))
