"""Horse-profile cache policy (Phase 0, item 3). Pure decisions; the script does the I/O.

Rule:
  * never seen the horse            -> Get Horse Profile with numBenchmarks=FIRST_SIGHT (10)
  * known, and has had a start since our last profile fetch
                                    -> Get Horse Profile with numBenchmarks=KNOWN (5), merge new runs
  * known, no new start             -> no call at all
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from .ops import FIRST_SIGHT_BENCHMARKS, KNOWN_HORSE_BENCHMARKS


@dataclass(frozen=True)
class ProfileDecision:
    horse_id: str
    num_benchmarks: int | None  # None = do not fetch
    reason: str


def decide_profile_fetch(
    horse_id: str,
    known: dict[str, Any] | None,
    latest_stored_run: date | None,
    latest_known_start: date | None,
) -> ProfileDecision:
    """known: the fk.horses row (profile_depth, profile_fetched_at) or None.
    latest_stored_run: newest benchmarked run date we hold for the horse.
    latest_known_start: newest start date the API tells us about on today's form
    (e.g. the entry's last-start date). When it is newer than what we hold, the
    horse has run since and a shallow refresh merges the new run in.
    """
    if known is None or known.get("profile_fetched_at") is None:
        return ProfileDecision(horse_id, FIRST_SIGHT_BENCHMARKS, "first sight")
    if latest_known_start is None:
        return ProfileDecision(horse_id, None, "known horse, last-start date not reported; nothing to merge")
    if latest_stored_run is None or latest_known_start > latest_stored_run:
        return ProfileDecision(horse_id, KNOWN_HORSE_BENCHMARKS, f"known horse with a start on {latest_known_start} newer than stored")
    return ProfileDecision(horse_id, None, "known horse, no new start")


def merge_runs(existing: list[dict[str, Any]], incoming: list[dict[str, Any]], key: str = "run_id") -> list[dict[str, Any]]:
    """Union keyed on run id; incoming wins on a clash (it is the fresher read).
    Order: newest event_date first, ties by run id."""
    by_id: dict[str, dict[str, Any]] = {str(r[key]): r for r in existing}
    for r in incoming:
        by_id[str(r[key])] = r
    def sort_key(r: dict[str, Any]):
        d = r.get("event_date")
        if isinstance(d, (date, datetime)):
            d = d.isoformat()
        return (d or "", str(r[key]))
    return sorted(by_id.values(), key=sort_key, reverse=True)
