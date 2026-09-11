"""Horse depth policy (Phase 0, item 3), shaped by the credit model.

Get Race Form at numBenchmarks=5 already delivers every runner's newest five
benchmarked runs and full race career for a flat 2 credits, on every card they appear
on. So a KNOWN horse needs no separate call: each race form refreshes its newest runs
and merge_runs keeps the older ones. A horse we have NEVER held gets one Get Horse Form
at numBenchmarks=10 to fill in runs six to ten (5 credits), after which it is known.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from .ops import FIRST_SIGHT_BENCHMARKS


@dataclass(frozen=True)
class ProfileDecision:
    horse_id: str
    num_benchmarks: int | None  # None = do not fetch
    reason: str


def decide_profile_fetch(horse_id: str, known: dict[str, Any] | None, stored_benchmarked_runs: int) -> ProfileDecision:
    """known: the fk.horses row (profile_depth, profile_fetched_at) or None."""
    if known is not None and known.get("profile_fetched_at") is not None:
        return ProfileDecision(horse_id, None, "already profiled at depth; race forms keep it current")
    if stored_benchmarked_runs >= FIRST_SIGHT_BENCHMARKS:
        return ProfileDecision(horse_id, None, f"already holds {stored_benchmarked_runs} benchmarked runs")
    return ProfileDecision(horse_id, FIRST_SIGHT_BENCHMARKS, "first sight: fill runs six to ten")


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
