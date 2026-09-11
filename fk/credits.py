"""Credit costs per operation.

Costs are money, so they are never assumed. Sources, in precedence order:
1. credits.yaml in the project root (explicit, written by a human after reading the spec).
2. An `x-credits` (or `x-credit-cost`) extension on the operation in the spec.
3. Numbers parsed from the operation's description or the spec's top-level
   description ("... costs 10 credits", "| Get Race Form | 10 |", "free").

If none of these yields a cost for an operation, the client and the estimator
refuse to proceed for that operation. A call whose price we do not know is not
made.

A cost may depend on parameters (the free tier at numBenchmarks<=5 is the
known case), so a cost table entry is a list of rules; the first matching rule
wins and a rule with no `when` is the default.

credits.yaml shape:

    Get Race Form:
      - when: {numBenchmarks: "<=5"}
        cost: 0
      - cost: 10
    Get Upcoming Meetings: 1        # a bare number is a single default rule
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .spec import Operation, Spec


class UnknownCost(Exception):
    pass


@dataclass(frozen=True)
class VariableCost:
    """Form King's benchmark pricing: per_item credits for each BenchmarkedRun returned beyond
    free_per_runner for each runner, rounded up per response."""
    param: str = "numBenchmarks"
    free_per_runner: int = 5
    per_item: float = 0.5

    def upper_bound(self, params: dict[str, Any], runners: int) -> float:
        depth = params.get(self.param)
        try:
            depth = int(depth) if depth is not None else self.free_per_runner
        except (TypeError, ValueError):
            depth = self.free_per_runner
        return self.per_item * max(0, depth - self.free_per_runner) * max(runners, 1)

    def from_counts(self, benchmarks_per_runner: list[int]) -> float:
        return self.per_item * sum(max(0, n - self.free_per_runner) for n in benchmarks_per_runner)


@dataclass(frozen=True)
class CostRule:
    cost: int
    when: dict[str, str] = field(default_factory=dict)  # param -> condition like "<=5", "10", ">5"
    source: str = ""
    variable: VariableCost | None = None

    def matches(self, params: dict[str, Any]) -> bool:
        for name, cond in self.when.items():
            if name not in params:
                return False
            if not _condition_holds(str(cond), params[name]):
                return False
        return True


def _condition_holds(cond: str, value: Any) -> bool:
    m = re.fullmatch(r"\s*(<=|>=|<|>|==|=)?\s*(-?\d+(?:\.\d+)?)\s*", cond)
    if not m:
        return str(value) == cond.strip()
    op, num = m.group(1) or "==", float(m.group(2))
    try:
        v = float(value)
    except (TypeError, ValueError):
        return False
    return {
        "<=": v <= num, ">=": v >= num, "<": v < num, ">": v > num, "==": v == num, "=": v == num,
    }[op]


class CostTable:
    def __init__(self, rules: dict[str, list[CostRule]]):
        self.rules = rules

    def rule_for(self, op_key: str, params: dict[str, Any] | None = None) -> CostRule:
        params = params or {}
        for rule in self.rules.get(op_key, []):
            if rule.matches(params):
                return rule
        raise UnknownCost(
            f"no credit cost known for {op_key!r} with params {params}. "
            "Add it to credits.yaml after reading the spec; an unpriced call is never made."
        )

    def cost_of(self, op_key: str, params: dict[str, Any] | None = None, *, runners: int = 1) -> int:
        """The price to plan on: the flat cost, plus the variable upper bound for the depth
        asked for across `runners` runners, rounded up as Form King rounds."""
        rule = self.rule_for(op_key, params)
        if rule.variable is None:
            return rule.cost
        return math.ceil(rule.cost + rule.variable.upper_bound(params or {}, runners) - 1e-9)

    def actual_cost(self, op_key: str, params: dict[str, Any], benchmarks_per_runner: list[int] | None) -> int:
        """What the response actually cost, from the BenchmarkedRun items it carried."""
        rule = self.rule_for(op_key, params)
        if rule.variable is None or benchmarks_per_runner is None:
            return rule.cost
        return math.ceil(rule.cost + rule.variable.from_counts(benchmarks_per_runner) - 1e-9)


    def known(self, op_key: str) -> bool:
        return bool(self.rules.get(op_key))

    def describe(self) -> list[str]:
        out = []
        for key, rules in sorted(self.rules.items()):
            for r in rules:
                cond = " when " + ", ".join(f"{k}{v}" for k, v in r.when.items()) if r.when else ""
                var = f" + {r.variable.per_item} per BenchmarkedRun beyond {r.variable.free_per_runner} per runner" if r.variable else ""
                out.append(f"{key}: {r.cost} credits{var}{cond}  [{r.source}]")
        return out


# ---- building the table ----------------------------------------------------------

def _rules_from_value(value: Any, source: str) -> list[CostRule]:
    """credits.yaml / x-credits value -> rules. Accepts a number or a list of {cost, when}."""
    if isinstance(value, bool):
        raise ValueError(f"{source}: cost must be a number, got a boolean")
    if isinstance(value, (int, float)):
        return [CostRule(cost=int(value), source=source)]
    if isinstance(value, dict) and "cost" in value:
        return [CostRule(cost=int(value["cost"]), when=dict(value.get("when") or {}), source=source)]
    if isinstance(value, list):
        rules = []
        for item in value:
            if isinstance(item, (int, float)) and not isinstance(item, bool):
                rules.append(CostRule(cost=int(item), source=source))
            elif isinstance(item, dict) and "cost" in item:
                var = item.get("variable")
                rules.append(CostRule(
                    cost=int(item["cost"]), when={k: str(v) for k, v in (item.get("when") or {}).items()}, source=source,
                    variable=VariableCost(str(var.get("param", "numBenchmarks")), int(var.get("free_per_runner", 5)),
                                          float(var.get("per_item", 0.5))) if isinstance(var, dict) else None))
            else:
                raise ValueError(f"{source}: unreadable cost rule {item!r}")
        # Defaults (no `when`) go last so conditional rules get first look.
        return sorted(rules, key=lambda r: 0 if r.when else 1)
    raise ValueError(f"{source}: unreadable cost value {value!r}")


_CREDIT_PATTERNS = [
    # "costs 10 credits", "10 credits per call", "Cost: 10 credits"
    re.compile(r"(?<![\d.])(\d+)\s*credits?\b", re.IGNORECASE),
]
_FREE = re.compile(r"\b(free|no credits?|0 credits?)\b", re.IGNORECASE)


def parse_cost_from_text(text: str) -> int | None:
    """Pull a single credit cost out of prose. Returns None when nothing is stated."""
    if not text:
        return None
    for pat in _CREDIT_PATTERNS:
        m = pat.search(text)
        if m:
            return int(m.group(1))
    if _FREE.search(text):
        return 0
    return None


def parse_cost_table_from_text(text: str, op_keys: list[str]) -> dict[str, int]:
    """Read a markdown-style table or "Name: N credits" lines from the spec's top-level
    description. Matches each operation key by name inside a line."""
    found: dict[str, int] = {}
    if not text:
        return found
    for line in text.splitlines():
        low = line.lower()
        for key in op_keys:
            if key and key.lower() in low:
                rest = low.replace(key.lower(), "")
                cost = parse_cost_from_text(rest)
                if cost is None:
                    # a table row like "| Get Race Form | 10 |": the only number left is the cost
                    nums = re.findall(r"(?<![\w.])(\d+)(?![\w.])", rest)
                    if len(nums) == 1:
                        cost = int(nums[0])
                if cost is not None and key not in found:
                    found[key] = cost
    return found


def build_cost_table(spec: Spec, overrides_path: str | Path | None = None) -> CostTable:
    rules: dict[str, list[CostRule]] = {}

    # 3. prose in the spec (lowest precedence, filled first and overwritten later)
    keys = [op.key for op in spec.operations]
    for key, cost in parse_cost_table_from_text(spec.info_description, keys).items():
        rules[key] = [CostRule(cost=cost, source="spec info.description")]
    for op in spec.operations:
        cost = parse_cost_from_text(op.description)
        if cost is not None:
            rules[op.key] = [CostRule(cost=cost, source=f"spec description of {op.method.upper()} {op.path}")]

    # 2. explicit extension on the operation
    for op in spec.operations:
        for ext in ("x-credits", "x-credit-cost", "x-cost"):
            if ext in op.extensions:
                rules[op.key] = _rules_from_value(op.extensions[ext], f"spec {ext}")

    # 1. human-written overrides
    if overrides_path and Path(overrides_path).exists():
        with Path(overrides_path).open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        if not isinstance(data, dict):
            raise ValueError(f"{overrides_path}: expected a mapping of operation -> cost")
        for key, value in data.items():
            rules[str(key)] = _rules_from_value(value, f"credits.yaml")

    return CostTable(rules)


def cost_for(table: CostTable, op: Operation, params: dict[str, Any]) -> int:
    return table.cost_of(op.key, params)
