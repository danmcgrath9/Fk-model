"""Credit estimates for a batch of planned calls. Printed before anything is spent."""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass

from .client import PlannedCall


@dataclass(frozen=True)
class EstimateLine:
    operation: str
    calls: int
    credits_each: int
    credits: int


@dataclass(frozen=True)
class Estimate:
    lines: tuple[EstimateLine, ...]
    total: int

    def render(self, balance: int | None = None) -> str:
        width = max([len(l.operation) for l in self.lines] + [len("TOTAL")])
        out = [f"{'operation'.ljust(width)}  calls  each   credits"]
        for l in self.lines:
            out.append(f"{l.operation.ljust(width)}  {l.calls:>5}  {l.credits_each:>4}   {l.credits:>7}")
        out.append(f"{'TOTAL'.ljust(width)}  {sum(l.calls for l in self.lines):>5}         {self.total:>7}")
        if balance is not None:
            out.append(f"live balance now {balance}, after this run {balance - self.total}")
        return "\n".join(out)


def estimate(calls: list[PlannedCall]) -> Estimate:
    groups: "OrderedDict[tuple[str, int], int]" = OrderedDict()
    for c in calls:
        key = (c.op.key, c.credits)
        groups[key] = groups.get(key, 0) + 1
    lines = tuple(EstimateLine(op, n, each, n * each) for (op, each), n in groups.items())
    return Estimate(lines=lines, total=sum(l.credits for l in lines))
