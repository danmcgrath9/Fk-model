"""Trend maths for a runner's rating history. Pure, hand-tested.

A trend is a least-squares slope over the last N runs, in rating points per run, with a
plain reading (rising / steady / falling) at a threshold, and the runner's recent mean
against its own longer mean. Nothing here invents a number: a runner with fewer than
`min_runs` rated runs gets None, not a guess.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Trend:
    slope: float | None        # points per run over the window, None under the floor
    recent_mean: float | None  # mean of the last `recent` runs
    longer_mean: float | None  # mean of the window
    last: float | None
    best: float | None
    n: int

    @property
    def reading(self) -> str:
        if self.slope is None:
            return "too few runs"
        if self.slope >= 0.75:
            return "rising"
        if self.slope <= -0.75:
            return "falling"
        return "steady"


def linear_slope(values: list[float]) -> float | None:
    n = len(values)
    if n < 2:
        return None
    xs = list(range(n))
    mx, my = sum(xs) / n, sum(values) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, values)) / sxx


def trend(values_oldest_first: list[float | None], *, window: int = 6, recent: int = 3, min_runs: int = 3) -> Trend:
    vals = [float(v) for v in values_oldest_first if v is not None]
    tail = vals[-window:]
    if len(tail) < min_runs:
        return Trend(None, None, None, vals[-1] if vals else None, max(vals) if vals else None, len(vals))
    return Trend(
        slope=linear_slope(tail),
        recent_mean=sum(tail[-recent:]) / len(tail[-recent:]),
        longer_mean=sum(tail) / len(tail),
        last=tail[-1],
        best=max(vals),
        n=len(vals),
    )
