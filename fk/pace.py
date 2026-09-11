"""Run many independent API calls at once without breaking Form King's rate limit.

The spec (1.0.6 release note) sets 300 requests per 300 seconds across web and API.
A single horse-form call takes six to ten seconds on the server, so one at a time
two hundred profiles is half an hour; four at a time under a one-per-second limiter
is about four minutes and never exceeds the allowance. A time budget stops the batch
cleanly: what is not fetched today is fetched the next time the horse races.
"""
from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Callable, Iterable, TypeVar

T = TypeVar("T")
R = TypeVar("R")


class RateLimiter:
    """At most `per_second` starts per second, shared across threads."""

    def __init__(self, per_second: float = 1.0):
        self.interval = 1.0 / per_second
        self.lock = threading.Lock()
        self.next_at = 0.0

    def wait(self) -> None:
        with self.lock:
            now = time.monotonic()
            start = max(now, self.next_at)
            self.next_at = start + self.interval
        delay = start - time.monotonic()
        if delay > 0:
            time.sleep(delay)


@dataclass
class BatchResult:
    done: list[tuple[Any, Any]]          # (item, result)
    failed: list[tuple[Any, Exception]]  # (item, error)
    skipped: list[Any]                   # not started: out of time


def run_batch(items: Iterable[T], fn: Callable[[T], R], *, workers: int = 4, per_second: float = 1.0,
              budget_seconds: float | None = None) -> BatchResult:
    """Apply fn to each item concurrently. Items not started before the budget runs out
    are reported as skipped; items already started are allowed to finish."""
    limiter = RateLimiter(per_second)
    deadline = time.monotonic() + budget_seconds if budget_seconds else None
    todo = list(items)
    result = BatchResult([], [], [])
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {}
        for i, item in enumerate(todo):
            if deadline is not None and time.monotonic() > deadline:
                result.skipped.extend(todo[i:])
                break
            def job(it=item):
                limiter.wait()
                return fn(it)
            futures[pool.submit(job)] = item
        for fut in as_completed(futures):
            item = futures[fut]
            try:
                result.done.append((item, fut.result()))
            except Exception as e:  # noqa: BLE001
                result.failed.append((item, e))
    return result
