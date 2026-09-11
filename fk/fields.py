"""Where response JSON meets our code. THE ONLY file that names response keys.

The spec was not available when this layer was written, so every accessor
carries a list of CANDIDATE keys and raises FieldUnmapped, naming the keys the
payload actually has, when none matches. That is deliberate: a wrong guess here
puts a horse in the wrong race silently; a raised error costs one minute to fix.

To confirm a mapping: run scripts/spec_report.py, read the response schema for
the operation, and put the real key FIRST in the candidate list (or replace the
list with the single real key). Each accessor is one line to change.
"""
from __future__ import annotations

from typing import Any, Iterable


class FieldUnmapped(KeyError):
    def __init__(self, what: str, candidates: Iterable[str], payload: Any):
        keys = sorted(payload.keys()) if isinstance(payload, dict) else type(payload).__name__
        super().__init__(
            f"{what}: none of {list(candidates)} present. Payload keys: {keys}. "
            "Confirm the field in b2c-openapi.yaml and update fk/fields.py."
        )


def pick(payload: Any, what: str, candidates: list[str], *, default: Any = ...) -> Any:
    """Return the first candidate key present in payload (dot paths allowed)."""
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


def as_list(payload: Any, what: str, candidates: list[str]) -> list[Any]:
    """Some endpoints return a bare list, others wrap it. Accept both."""
    if isinstance(payload, list):
        return payload
    value = pick(payload, what, candidates)
    if not isinstance(value, list):
        raise FieldUnmapped(what, candidates, payload)
    return value


# ---- meetings ----------------------------------------------------------------------

def meetings_list(payload: Any) -> list[dict]:
    return as_list(payload, "meetings list", ["meetings", "data", "items", "results"])

def meeting_id(m: dict) -> str:
    return str(pick(m, "meeting id", ["meetingId", "id", "meeting_id"]))

def meeting_state(m: dict) -> str:
    return str(pick(m, "meeting state", ["state", "stateCode", "track.state", "venue.state"]))

def meeting_date(m: dict) -> str:
    return str(pick(m, "meeting date", ["meetingDate", "date", "meeting_date", "raceDate"]))[:10]

def meeting_track(m: dict) -> str:
    return str(pick(m, "meeting track", ["track", "trackName", "venue", "track.name", "venue.name"]))

def meeting_races(m: dict) -> list[dict]:
    return as_list(m, "races in meeting", ["races", "raceList"])

# ---- races ---------------------------------------------------------------------------

def race_id(r: dict) -> str:
    return str(pick(r, "race id", ["raceId", "id", "race_id"]))

def race_number(r: dict) -> int | None:
    v = pick(r, "race number", ["raceNumber", "number", "race_number", "raceNo"], default=None)
    return int(v) if v is not None else None

def race_name(r: dict) -> str | None:
    return pick(r, "race name", ["raceName", "name", "race_name"], default=None)

def race_distance(r: dict) -> int | None:
    v = pick(r, "race distance", ["distance", "distanceMetres", "distance_m"], default=None)
    return int(v) if v is not None else None

def race_start_time(r: dict) -> str | None:
    return pick(r, "race start time", ["startTime", "raceTime", "scheduledStart", "start_time"], default=None)

def race_entries(payload: Any) -> list[dict]:
    return as_list(payload, "entries in race form", ["runners", "entries", "horses", "form"])

# ---- entries / horses -------------------------------------------------------------

def horse_id(e: dict) -> str:
    return str(pick(e, "horse id", ["horseId", "horse.id", "horse_id", "id"]))

def horse_name(e: dict) -> str:
    return str(pick(e, "horse name", ["horseName", "horse.name", "name", "runnerName"]))

def entry_barrier(e: dict) -> int | None:
    v = pick(e, "barrier", ["barrier", "barrierNumber", "gate"], default=None)
    return int(v) if v is not None else None

def entry_weight(e: dict) -> float | None:
    v = pick(e, "weight", ["weight", "handicapWeight", "weightCarried"], default=None)
    return float(v) if v is not None else None

def entry_jockey(e: dict) -> str | None:
    return pick(e, "jockey", ["jockey", "jockeyName", "jockey.name"], default=None)

def entry_trainer(e: dict) -> str | None:
    return pick(e, "trainer", ["trainer", "trainerName", "trainer.name"], default=None)

def entry_scratched(e: dict) -> bool:
    return bool(pick(e, "scratched", ["scratched", "isScratched"], default=False))

def entry_neural_rating(e: dict) -> float | None:
    v = pick(e, "FK Neural rating", ["neural", "neuralRating", "ratings.neural", "fkNeural"], default=None)
    return float(v) if v is not None else None

def entry_exp_rating(e: dict) -> float | None:
    v = pick(e, "FK EXP rating", ["exp", "expRating", "ratings.exp", "fkExp"], default=None)
    return float(v) if v is not None else None

def entry_days_since_last_run(e: dict) -> int | None:
    v = pick(e, "days since last run", ["daysSinceLastRun", "daysSince", "lastStartDays"], default=None)
    return int(v) if v is not None else None

# ---- runs (past events + benchmarks) -------------------------------------------

def entry_runs(e: dict) -> list[dict]:
    """The horse's past runs as carried on a race-form entry or a horse profile."""
    return as_list(e, "benchmarked runs", ["benchmarkedRuns", "benchmarks", "runs", "pastEvents", "form"])

def run_id(r: dict) -> str:
    return str(pick(r, "run id", ["runId", "eventId", "pastEventId", "id"]))

def run_date(r: dict) -> str | None:
    v = pick(r, "run date", ["date", "eventDate", "meetingDate", "raceDate"], default=None)
    return str(v)[:10] if v else None

def run_track_speed_verified(r: dict) -> bool:
    """Every benchmarked_runs row stores this. Absent means unverified, stored as false,
    but it is asked for by name so the payload has to carry it to be trusted."""
    return bool(pick(r, "trackSpeedVerified", ["trackSpeedVerified", "track_speed_verified"]))

def run_positions(r: dict) -> list[float | None]:
    """Position in running across the race sections, in running order (early to finish)."""
    v = pick(r, "position in running", ["positionInRunning", "positions", "pir", "runningPositions"])
    return [None if x is None else float(x) for x in v]

def run_vs_class(r: dict) -> list[float | None]:
    """vs-Class benchmark per section, in running order. Above zero is faster than class."""
    v = pick(r, "vs-class sectionals", ["vsClass", "vs_class", "sectionalsVsClass", "benchmarkVsClass"])
    return [None if x is None else float(x) for x in v]

def run_sections(r: dict) -> list[str] | None:
    return pick(r, "section labels", ["sections", "sectionLabels", "sectionNames"], default=None)

def run_finish_position(r: dict) -> int | None:
    v = pick(r, "finish position", ["finishPosition", "position", "placing", "finish"], default=None)
    return int(v) if v is not None else None

# ---- speedmaps -----------------------------------------------------------------------

def speedmap_races(payload: Any) -> list[dict]:
    return as_list(payload, "speedmap races", ["races", "speedmaps", "data"])

def speedmap_runners(sm: dict) -> list[dict]:
    return as_list(sm, "speedmap runners", ["runners", "horses", "entries"])

def speedmap_early_speed(r: dict) -> float | None:
    v = pick(r, "early speed metric", ["earlySpeed", "speed", "earlySpeedRating", "pace"], default=None)
    return float(v) if v is not None else None

def speedmap_predicted_position(r: dict) -> float | None:
    v = pick(r, "predicted early position", ["predictedPosition", "settlePosition", "position", "mapPosition"], default=None)
    return float(v) if v is not None else None

# ---- odds and results ----------------------------------------------------------------

def odds_list(payload: Any) -> list[dict]:
    return as_list(payload, "odds runners", ["runners", "odds", "prices", "data"])

def odds_current_price(o: dict) -> float | None:
    v = pick(o, "current price", ["currentPrice", "price", "win", "fixedWin"], default=None)
    return float(v) if v is not None else None

def odds_opening_price(o: dict) -> float | None:
    v = pick(o, "opening price", ["openingPrice", "openPrice", "open"], default=None)
    return float(v) if v is not None else None

def odds_starting_price(o: dict) -> float | None:
    v = pick(o, "starting price", ["startingPrice", "sp", "finalPrice"], default=None)
    return float(v) if v is not None else None

def results_list(payload: Any) -> list[dict]:
    return as_list(payload, "results", ["results", "runners", "placings", "data"])

def result_margin(r: dict) -> float | None:
    v = pick(r, "margin", ["margin", "marginLengths"], default=None)
    return float(v) if v is not None else None
