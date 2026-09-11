"""Where response JSON meets our code. THE ONLY file that names response keys.

Every key here is taken from b2c-openapi.yaml 1.0.8 (components.schemas). Required
fields are read directly; optional ones return None. A missing REQUIRED key raises
FieldUnmapped naming what was present, because a payload that breaks the spec is
something to look at, not paper over.
"""
from __future__ import annotations

import math
from datetime import date, datetime, timezone
from typing import Any, Iterable
from zoneinfo import ZoneInfo

MELBOURNE = ZoneInfo("Australia/Melbourne")


class FieldUnmapped(KeyError):
    def __init__(self, what: str, candidates: Iterable[str], payload: Any):
        keys = sorted(payload.keys()) if isinstance(payload, dict) else type(payload).__name__
        super().__init__(
            f"{what}: none of {list(candidates)} present. Payload keys: {keys}. "
            "Check b2c-openapi.yaml and fk/fields.py."
        )


def pick(payload: Any, what: str, candidates: list[str], *, default: Any = ...) -> Any:
    """Return the first candidate key present (dot paths allowed), else default, else raise."""
    if isinstance(payload, dict):
        for cand in candidates:
            node: Any = payload
            ok = True
            for part in cand.split("."):
                if isinstance(node, dict) and part in node:
                    node = node[part]
                else:
                    ok = False
                    break
            if ok:
                return node
    if default is not ...:
        return default
    raise FieldUnmapped(what, candidates, payload)


def _num(v: Any) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f


def _int(v: Any) -> int | None:
    f = _num(v)
    return int(f) if f is not None else None


def epoch_ms_to_melbourne_date(ms: Any) -> str | None:
    """Form King dates are Unix milliseconds (UTC). A meeting's civil date is Melbourne's."""
    if ms is None:
        return None
    return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).astimezone(MELBOURNE).date().isoformat()


def epoch_ms_to_utc(ms: Any) -> datetime | None:
    return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc) if ms is not None else None


# ---- meetings (MeetingSummaryLite / MeetingSummary) -------------------------------------

def meetings_list(payload: Any) -> list[dict]:
    if not isinstance(payload, list):
        raise FieldUnmapped("meetings list", ["<array>"], payload)
    return payload

def meeting_id(m: dict) -> str:
    return str(pick(m, "meeting id", ["id"]))

def meeting_state(m: dict) -> str:
    return str(pick(m, "meeting state", ["state"], default="") or "")

def meeting_date(m: dict) -> str | None:
    return epoch_ms_to_melbourne_date(pick(m, "meeting date", ["date"], default=None))

def meeting_track(m: dict) -> str:
    return str(pick(m, "meeting track", ["trackName"], default="") or "")

def meeting_status(m: dict) -> str:
    return str(pick(m, "meeting status", ["status"], default="") or "")

def meeting_races(m: dict) -> list[dict]:
    return list(pick(m, "races in meeting", ["races"], default=[]) or [])

# ---- races (RaceLite / RaceSummary) --------------------------------------------------------

def race_id(r: dict) -> str:
    return str(pick(r, "race id", ["raceId"]))

def race_number(r: dict) -> int | None:
    return _int(pick(r, "race number", ["number"], default=None))

def race_name(r: dict) -> str | None:
    return pick(r, "race name", ["name"], default=None)

def race_distance(r: dict) -> int | None:
    return _int(pick(r, "race distance", ["distance"], default=None))

def race_start_time(r: dict) -> str | None:
    """RaceSummary.startTime is a string the spec does not shape; kept verbatim."""
    v = pick(r, "race start time", ["startTime"], default=None)
    return str(v) if v is not None else None

def race_status(r: dict) -> str | None:
    return pick(r, "race status", ["status"], default=None)

def race_market_percentage(r: dict) -> float | None:
    """RaceSummary.syntheticHold: 1.2 means a 120% market. Returned as a percentage."""
    v = _num(pick(r, "syntheticHold", ["syntheticHold"], default=None))
    return v * 100 if v is not None else None

def race_entries(r: dict) -> list[dict]:
    return list(pick(r, "entries in race", ["entries"], default=[]) or [])

def race_runner_count(r: dict) -> int:
    """Runners on the card less scratchings: what a race-form call is priced over."""
    return sum(1 for e in race_entries(r) if not entry_scratched(e))

# ---- entries (RaceEntryLite / RaceEntry) ---------------------------------------------------

def horse_id(e: dict) -> str:
    """breedingId is Form King's horse identifier on race entries and speedmap entries."""
    return str(pick(e, "horse id", ["breedingId"]))

def horse_name(e: dict) -> str:
    return str(pick(e, "horse name", ["horse.name", "horse"]))

def entry_number(e: dict) -> int | None:
    return _int(pick(e, "saddlecloth", ["number"], default=None))

def entry_barrier(e: dict) -> int | None:
    return _int(pick(e, "barrier", ["barrier"], default=None))

def entry_weight(e: dict) -> float | None:
    return _num(pick(e, "weight", ["weightCarried", "weight"], default=None))

def entry_jockey(e: dict) -> str | None:
    return pick(e, "jockey", ["jockey"], default=None)

def entry_trainer(e: dict) -> str | None:
    return pick(e, "trainer", ["trainer"], default=None)

def entry_scratched(e: dict) -> bool:
    return bool(pick(e, "scratched", ["scratched"], default=False))

def entry_neural_rating(e: dict) -> float | None:
    return _num(pick(e, "Neural rating", ["ratings.neural"], default=None))

def entry_exp_rating(e: dict) -> float | None:
    return _num(pick(e, "EXP rating", ["ratings.exp"], default=None))

def entry_days_since_last_run(e: dict) -> int | None:
    return _int(pick(e, "days since last race", ["daysSinceLastRace"], default=None))

def entry_past_events(e: dict) -> list[dict]:
    return list(pick(e, "past events", ["pastEvents"], default=[]) or [])

# odds (RaceEntryOdds), present only when a market exists
def entry_odds(e: dict) -> dict | None:
    o = pick(e, "odds", ["odds"], default=None)
    return o if isinstance(o, dict) else None

def odds_current_price(o: dict) -> float | None:
    return _num(pick(o, "best price now", ["bestNow"], default=None))

def odds_average_price(o: dict) -> float | None:
    return _num(pick(o, "average price now", ["avgNow"], default=None))

def odds_opening_price(o: dict) -> float | None:
    return _num(pick(o, "average opening price", ["avgOpen"], default=None))

def odds_firm_or_drift(o: dict) -> float | None:
    """Form King's own move since open, in points of win chance, normalised for the
    bookmaker percentage and scratchings. Negative is a drift."""
    return _num(pick(o, "firmOrDrift", ["firmOrDrift"], default=None))

def odds_timestamp(o: dict) -> datetime | None:
    return epoch_ms_to_utc(pick(o, "odds timestamp", ["timestamp"], default=None))

# result (HorseResult), present once the race is resulted
def entry_result(e: dict) -> dict | None:
    r = pick(e, "horse result", ["horseResult"], default=None)
    return r if isinstance(r, dict) else None

def result_finish_position(r: dict) -> int | None:
    return _int(pick(r, "finish position", ["finishPosition"], default=None))

def result_margin(r: dict) -> float | None:
    return _num(pick(r, "margin", ["margin"], default=None))

def result_starting_price(r: dict) -> float | None:
    return _num(pick(r, "starting price", ["startingPrice"], default=None))

def result_betfair_sp(r: dict) -> float | None:
    return _num(pick(r, "Betfair SP", ["betfairStartingPrice"], default=None))

# ---- past events (PastEvent) and benchmarks (BenchmarkedRun) -----------------------------

def past_event_is_race(p: dict) -> bool:
    return bool(pick(p, "race flag", ["race"], default=True)) and not bool(pick(p, "scratched", ["scratched"], default=False))

def past_event_race_id(p: dict) -> str | None:
    v = pick(p, "past race id", ["raceId"], default=None)
    return str(v) if v is not None else None

def past_event_date(p: dict) -> str | None:
    return epoch_ms_to_melbourne_date(pick(p, "past event date", ["date"], default=None))

def past_event_track(p: dict) -> str | None:
    return pick(p, "past event track", ["track"], default=None)

def past_event_distance(p: dict) -> int | None:
    return _int(pick(p, "past event distance", ["distance"], default=None))

def past_event_finish(p: dict) -> int | None:
    return _int(pick(p, "past finish position", ["finishPosition"], default=None))

def past_event_margin(p: dict) -> float | None:
    return _num(pick(p, "past margin", ["margin"], default=None))

def past_event_track_speed_verified(p: dict) -> bool:
    """Required by the spec on every PastEvent. Stored on every benchmarked_runs row."""
    return bool(pick(p, "trackSpeedVerified", ["trackSpeedVerified"]))

def past_event_benchmark(p: dict) -> dict | None:
    b = pick(p, "benchmark", ["benchmark"], default=None)
    return b if isinstance(b, dict) else None


# Position in running, in running order. The benchmark's pir fields are per 200m marker;
# the PastEvent carries a coarser set on every run. Labels are fixed so runs over
# different distances share an axis; a marker the race did not have is None.
POSITION_LABELS = ["Settle", "1200m", "1000m", "800m", "600m", "400m", "200m", "Finish"]


def _pos(v: Any) -> float | None:
    """A position in running is 1 or more; Form King sends 0 for a marker the race did not have."""
    f = _num(v)
    return f if f is not None and f >= 1 else None


def run_positions(p: dict) -> list[float | None]:
    b = past_event_benchmark(p) or {}
    def g(key, fallback=None):
        v = _pos(b.get(key)) if key in b else None
        return v if v is not None else _pos(p.get(fallback)) if fallback else v
    return [
        _pos(p.get("posSettling")),
        g("pir12", "pos1200m"),
        g("pir10"),
        g("pir8", "pos800m"),
        g("pir6"),
        g("pir4", "pos400m"),
        g("pir2"),
        _pos(p.get("finishPosition")),
    ]


# Sectional splits vs the Class benchmark, in running order. The first slot is the run
# from the start to the first marker the race has (S-12, S-10, S-8 or S-6), then the
# 200m splits to the finish. Section keys per the spec's SectionKey enum.
SPLIT_LABELS = ["Start to first marker", "1200-1000", "1000-800", "800-600", "600-400", "400-200", "200-Finish"]
_SPLIT_KEYS = ["12-10", "10-8", "8-6", "6-4", "4-2", "2-F"]
LAST_600_SLOTS = 3  # the final three labels are the last 600m


def run_splits_vs_class(p: dict, metric: str = "vsClass") -> list[float | None]:
    b = past_event_benchmark(p)
    if not b or not isinstance(b.get("sections"), dict):
        return [None] * len(SPLIT_LABELS)
    secs = b["sections"]
    def val(key):
        s = secs.get(key)
        return _num(s.get(metric)) if isinstance(s, dict) else None
    if "12-10" in secs:
        first = val("S-12")
    elif "10-8" in secs:
        first = val("S-10")
    elif "8-6" in secs:
        first = val("S-8")
    else:
        first = val("S-6")
    return [first] + [val(k) for k in _SPLIT_KEYS]


def run_to_600_vs_class(p: dict) -> float | None:
    b = past_event_benchmark(p) or {}
    s = (b.get("sections") or {}).get("S-6")
    return _num(s.get("vsClass")) if isinstance(s, dict) else None


def run_last_600_vs_class(p: dict) -> float | None:
    b = past_event_benchmark(p) or {}
    s = (b.get("sections") or {}).get("6-F")
    return _num(s.get("vsClass")) if isinstance(s, dict) else None


def run_overall_vs_class(p: dict) -> float | None:
    b = past_event_benchmark(p) or {}
    return _num(b.get("vsClass"))


def count_benchmarks(payload: Any) -> list[int] | None:
    """BenchmarkedRun items per runner in a Get Race Form or Get Horse Form response:
    what Form King charges the variable component on."""
    if not isinstance(payload, dict):
        return None
    if isinstance(payload.get("entries"), list):
        return [sum(1 for p in entry_past_events(e) if past_event_benchmark(p)) for e in payload["entries"]]
    if isinstance(payload.get("pastEvents"), list):
        return [sum(1 for p in payload["pastEvents"] if past_event_benchmark(p))]
    return None


# ---- horse form (HorseForm) ---------------------------------------------------------------------

def horse_form_id(payload: dict) -> str:
    return str(pick(payload, "horse form id", ["id"]))

def horse_form_name(payload: dict) -> str | None:
    return pick(payload, "horse form name", ["horse.name"], default=None)

def horse_form_past_events(payload: dict) -> list[dict]:
    return list(pick(payload, "horse past events", ["pastEvents"], default=[]) or [])


# ---- speedmaps (Speedmap / SpeedmapEntry / ExpectedTempo) ------------------------------

def speedmap_list(payload: Any) -> list[dict]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and "raceId" in payload:
        return [payload]
    raise FieldUnmapped("speedmaps", ["<array of Speedmap>"], payload)

def speedmap_race_id(sm: dict) -> str:
    return str(pick(sm, "speedmap race id", ["raceId"]))

def speedmap_entries(sm: dict) -> list[dict]:
    return list(pick(sm, "speedmap entries", ["entries"], default=[]) or [])

def speedmap_tempo(sm: dict) -> dict | None:
    t = pick(sm, "expected tempo", ["expectedTempo"], default=None)
    return t if isinstance(t, dict) else None

def tempo_description(t: dict) -> str | None:
    return pick(t, "tempo description", ["description"], default=None)

def speedmap_early_speed(e: dict) -> float | None:
    """earlySpeedValues.overall: a 1 to 10 speed figure (type SPEED_FIGURE) or the raw score."""
    return _num(pick(e, "early speed overall", ["earlySpeedValues.overall"], default=None))

def speedmap_pir(e: dict) -> float | None:
    return _num(pick(e, "early speed pir", ["earlySpeedValues.pir"], default=None))

def speedmap_median_vs_benchmark(e: dict) -> float | None:
    return _num(pick(e, "median early vs benchmark", ["medianEarlyVsBenchmark"], default=None))


def speedmap_predicted_order(entries: list[dict]) -> list[tuple[dict, int]]:
    """(entry, predicted early position) with 1 the runner mapped to lead: highest early
    speed score first, ties broken by the lower settling position score."""
    scored = [e for e in entries if speedmap_early_speed(e) is not None]
    scored.sort(key=lambda e: (-(speedmap_early_speed(e) or 0), speedmap_pir(e) if speedmap_pir(e) is not None else 99))
    return [(e, i + 1) for i, e in enumerate(scored)]


# ---- usage log (DailyUsageSummary) ----------------------------------------------------------

def usage_daily_rows(payload: Any) -> list[tuple[str, int, int]]:
    """(date, calls, credits) per day from Get Usage Log with aggregate=daily."""
    if not isinstance(payload, list):
        raise FieldUnmapped("daily usage", ["<array of DailyUsageSummary>"], payload)
    return [(str(r.get("date")), int(r.get("totalCalls") or 0), int(r.get("creditsDeducted") or 0)) for r in payload]
