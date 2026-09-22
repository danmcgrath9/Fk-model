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


# ---- ratings on a past run (PastEvent + BenchmarkedRun) --------------------------------

def run_ratings(p: dict) -> dict[str, Any]:
    """Every rating Form King attaches to one past run, on their own scales:
    FK scale (roughly 60 to 110): weightForAgeRating, adjustedForTodaysWeight, atWeights,
      wfaRat, raceRating, expectedRating.
    Lengths vs a benchmark: vsClass, vsAllAvg, vsTrack.
    Speed: speedRating (100 = class par), finishingSpeed (last 600 as % of run-to-600 speed).
    Ranks (late sections only, per the spec): raceRank, meetRank, meetRatingRank of the
      last-600m section, else the last-400, else the last-200.
    """
    b = past_event_benchmark(p) or {}
    secs = b.get("sections") if isinstance(b.get("sections"), dict) else {}

    def rated(v: Any) -> float | None:
        # Form King writes 0 on a run it did not rate (a trial, a run before benchmarking).
        # On a scale that runs 60 to 110, 0 is an absence, not a rating, and drawing it
        # crushes every real point into the top of the chart.
        n = _num(v)
        return None if n is None or n == 0 else n

    ranks: dict[str, Any] = {}
    for key in ("6-F", "4-F", "2-F"):
        sec = secs.get(key)
        if isinstance(sec, dict) and any(sec.get(k) is not None for k in ("raceRank", "meetRank", "meetRatingRank")):
            ranks = {"section": key, "raceRank": _int(sec.get("raceRank")), "meetRank": _int(sec.get("meetRank")),
                     "meetRatingRank": _int(sec.get("meetRatingRank"))}
            break
    def section_vs_class(keys: tuple[str, ...]) -> float | None:
        """vsClass for the first of these sections the run carries: lengths against the
        class standard over that part of the race, higher = faster than the standard."""
        for key in keys:
            sec = secs.get(key)
            if isinstance(sec, dict) and _num(sec.get("vsClass")) is not None:
                return _num(sec.get("vsClass"))
        return None

    return {
        # Where the horse was through the run: settling, then each marker, then the finish.
        "positions": run_positions(p),
        # The last 600m and the run to it, against the class standard. Form King names the
        # sections from the distance out ("6-F" is 600m to the finish, "S-6" the start to
        # the 600), and a short race is sectioned shallower, so each falls back in turn.
        "last600": section_vs_class(("6-F", "4-F", "2-F")),
        "to600": section_vs_class(("S-6", "S-8", "S-4")),
        "date": past_event_date(p),
        "track": past_event_track(p),
        "distance": past_event_distance(p),
        "finish": past_event_finish(p),
        "runners": _int(p.get("numRunners")),
        "trial": bool(p.get("trial", False)),
        "wfa": rated(p.get("weightForAgeRating")),
        "adjToday": rated(p.get("adjustedForTodaysWeight")),
        "atWeights": rated(b.get("atWeights")),
        "wfaRat": rated(b.get("wfaRat")),
        "raceRating": rated(b.get("raceRating")),
        "expected": rated(b.get("expectedRating")),
        "vsClass": _num(b.get("vsClass")),
        "vsAllAvg": _num(b.get("vsAllAvg")),
        "vsTrack": _num(b.get("vsTrack")),
        "speedRating": rated(b.get("speedRating")),
        "finishingSpeed": rated(b.get("finishingSpeed")),
        "trackSpeedVerified": bool(p.get("trackSpeedVerified", False)),
        "ranks": ranks,
    }


def entry_peak_ratings(e: dict) -> tuple[float | None, float | None]:
    """RaceEntryRatings.peak (career) and peak12m, adjusted to today's weight."""
    return _num(pick(e, "peak", ["ratings.peak"], default=None)), _num(pick(e, "peak12m", ["ratings.peak12m"], default=None))


def past_event_is_spell(p: dict) -> bool:
    return bool(pick(p, "spell", ["spell"], default=False))


def past_event_is_trial(p: dict) -> bool:
    return bool(pick(p, "trial", ["trial"], default=False))


# ---- the rest of the entry: conditions record, people, gear, race facts --------------

def _s(v: Any) -> str | None:
    return None if v is None else str(v)


def entry_form_record(e: dict) -> dict[str, Any]:
    """The form-guide strings on RaceEntry.form, as Form King writes them ("3: 1-0-1-1"
    is starts: wins-seconds-thirds-other). Kept as strings; they are read, not summed."""
    f = pick(e, "form", ["form"], default=None) or {}
    keys = ("careerForm", "classForm", "distanceForm", "trackForm", "trackAndDistanceForm", "todaysGoingForm", "firstUpForm",
            "secondUpForm", "thirdUpForm", "todaysWeight", "insideBarriers", "middleBarriers", "wideBarriers", "goodForm", "heavyForm",
            "wet", "synthetic", "similarDistance", "sprintRaces", "middleRaces", "mileRaces", "stayingRaces")
    out = {k: _s(f.get(k)) for k in keys if isinstance(f, dict)}
    out["lengthsBeatenLastThree"] = _num(f.get("lengthsBeatenLastThree")) if isinstance(f, dict) else None
    out["wonWithTodaysWeightOrHigher"] = bool(f.get("wonWithTodaysWeightOrHigher")) if isinstance(f, dict) else None
    return out


def entry_track_speed_going_form(e: dict) -> dict[str, str] | None:
    g = pick(e, "trackSpeedGoingForm", ["trackSpeedGoingForm"], default=None)
    return {k: str(v) for k, v in g.items()} if isinstance(g, dict) else None


def entry_jockey_form(e: dict) -> dict[str, Any] | None:
    j = pick(e, "jockeyForm", ["jockeyForm"], default=None)
    if not isinstance(j, dict):
        return None
    return {"rides12m": _int(j.get("lastTwelveMonthRides")), "win12m": _num(j.get("lastTwelveMonthWinPercentage")),
            "place12m": _num(j.get("lastTwelveMonthPlacePercentage")), "horseCombo": _s(j.get("horseComboForm")),
            "horseComboWin": _num(j.get("horseComboWinPercentage")), "trackCombo": _s(j.get("trackComboForm")),
            "trackComboWin": _num(j.get("trackComboWinPercentage"))}


def entry_trainer_form(e: dict) -> dict[str, Any] | None:
    t = pick(e, "trainerForm", ["trainerForm"], default=None)
    if not isinstance(t, dict):
        return None
    return {"win12m": _num(t.get("lastTwelveMonthWinPercentage")), "form12m": _s(t.get("lastTwelveMonthForm")),
            "horseCombo": _s(t.get("horseComboForm")), "jockeyCombo": _s(t.get("jockeyComboForm")),
            "jockeyComboWin": _num(t.get("jockeyComboWinPercentage")), "trackCombo": _s(t.get("trackComboForm")),
            "trackComboWin": _num(t.get("trackComboWinPercentage"))}


def entry_gear(e: dict) -> tuple[list[str], list[str]]:
    """(gear worn, gear changes) as plain names, e.g. (["Blinkers", "Tongue Tie"], ["Blinkers first time"])."""
    worn, changes = [], []
    for g in pick(e, "gear", ["gear"], default=[]) or []:
        if not isinstance(g, dict):
            continue
        name = str(g.get("gear") or "")
        if g.get("on"):
            worn.append(name)
        ch = g.get("change")
        if ch and str(ch).lower() not in ("", "none", "no", "false", "unchanged"):
            changes.append(f"{name} {ch}".strip())
    txt = pick(e, "gearChanges", ["gearChanges"], default=None)
    if txt and not changes:
        changes.append(str(txt))
    return worn, changes


def entry_context(e: dict) -> dict[str, Any]:
    """Odds and ends a form guide prints beside a runner."""
    return {
        "runInPrep": _int(pick(e, "raceInPrep", ["raceInPrep"], default=None)),
        "firstStarter": bool(pick(e, "firstStarter", ["firstStarter"], default=False)),
        "daysSinceLastWin": _int(pick(e, "daysSinceLastWin", ["daysSinceLastWin"], default=None)),
        "distanceChange": _s(pick(e, "distanceChange", ["distanceChange"], default=None)),
        "ohr": _num(pick(e, "benchmarkRating", ["benchmarkRating"], default=None)),
        "apprenticeClaim": _num(pick(e, "apprenticeClaim", ["apprenticeClaim"], default=None)),
        "wfaDiff": _num(pick(e, "wfaDiff", ["wfaDiff"], default=None)),
        "prizemoney": _num(pick(e, "totalPrizeMoney", ["totalPrizeMoney"], default=None)),
        "avgPrizemoney": _num(pick(e, "averagePrizeMoney", ["averagePrizeMoney"], default=None)),
        "emergency": bool(pick(e, "emergency", ["emergency"], default=False)),
        "dualAcceptor": bool(pick(e, "dualAcceptor", ["dualAcceptor"], default=False)),
        "age": _int(pick(e, "age", ["horse.age"], default=None)),
        "sex": _s(pick(e, "type", ["horse.type"], default=None)),
        "sire": _s(pick(e, "sire", ["horse.sire"], default=None)),
        "dam": _s(pick(e, "dam", ["horse.dam"], default=None)),
        "trainingLocation": _s(pick(e, "training location", ["horse.trainingLocation"], default=None)),
    }


def race_facts(r: dict) -> dict[str, Any]:
    """Race-level facts from RaceSummary the header should carry."""
    return {
        "going": _s(pick(r, "going", ["going"], default=None)),
        "goingNumber": _int(pick(r, "goingNumber", ["goingNumber"], default=None)),
        "rail": _s(pick(r, "railPosition", ["railPosition"], default=None)),
        "direction": _s(pick(r, "direction", ["direction"], default=None)),
        "lws": _num(pick(r, "lws", ["lws"], default=None)),
        "expAdj": _num(pick(r, "expAdj", ["expAdj"], default=None)),
        "restrictions": _s(pick(r, "restrictions", ["restrictions"], default=None)),
        "grade": _s(pick(r, "prizemoneyGrade", ["prizemoneyGrade"], default=None)),
        "prizemoney": _num(pick(r, "totalPrizeMoney", ["totalPrizeMoney"], default=None)),
        "runners": _int(pick(r, "numRunners", ["numRunners"], default=None)),
        "startTime": race_start_time(r),
        "status": race_status(r),
    }


def run_market(p: dict) -> dict[str, Any]:
    """What the market thought of a past run and how it went."""
    return {"date": past_event_date(p), "sp": _num(p.get("startingPrice")), "bsp": _num(p.get("bsp")),
            "finish": past_event_finish(p), "runners": _int(p.get("numRunners")), "margin": past_event_margin(p),
            "going": _s(p.get("going")), "distance": past_event_distance(p), "track": past_event_track(p),
            "weight": _num(p.get("weight")), "jockey": _s(p.get("jockey")), "raceInPrep": _int(p.get("raceInPrep")),
            "daysSincePrevious": _int(p.get("daysSincePreviousRace")), "trial": past_event_is_trial(p),
            "fieldStrength": _num(p.get("fieldStrength")), "prizemoney": _num(p.get("totalPrizemoney"))}
