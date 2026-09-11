"""HTTP client for the Form King Modellers API, driven entirely by the spec.

Guarantees:
- The credit cost of a call is known before the request is sent (else UnknownCost).
- Every request that reaches the network is written to the ledger, success or
  failure, because Form King charges for the call, not for our happiness with it.
  (If the spec says failed calls are free, set FK_CHARGE_FAILED=0; default is to
  assume the worst so the ledger over-counts rather than under-counts.)
- Live calls are refused unless the client was built with allow_live=True. The
  scripts only pass that after printing an estimate and getting a "yes".
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests

from .config import TEST_API_KEY
from .credits import CostTable
from .fields import count_benchmarks
from .ledger import Ledger
from .spec import Operation, Spec, SpecError


class FormKingError(Exception):
    def __init__(self, op: Operation, status: int, body: str):
        self.op, self.status, self.body = op, status, body
        super().__init__(f"{op.method.upper()} {op.path} -> HTTP {status}: {body[:500]}")


class LiveCallRefused(Exception):
    pass


@dataclass(frozen=True)
class PlannedCall:
    op: Operation
    params: dict[str, Any]
    credits: int          # the estimate: flat cost plus the variable upper bound
    runners: int = 1      # the estimation hint the variable component was priced over


class FormKingClient:
    def __init__(
        self,
        spec: Spec,
        api_key: str,
        ledger: Ledger,
        costs: CostTable,
        *,
        base_url: str | None = None,
        allow_live: bool = False,
        session: requests.Session | None = None,
        timeout: float = 30.0,
    ):
        self.spec = spec
        self.api_key = api_key
        self.ledger = ledger
        self.costs = costs
        self.base_url = (base_url or spec.base_url()).rstrip("/")
        self.allow_live = allow_live
        self.session = session or requests.Session()
        self.timeout = timeout
        self.header_name = spec.api_key_header()
        self.charge_failed = os.environ.get("FK_CHARGE_FAILED", "1") != "0"

    @property
    def key_kind(self) -> str:
        return "test" if self.api_key == TEST_API_KEY else "live"

    # ---- planning ------------------------------------------------------------------

    def plan(self, op_name: str, *, runners: int = 1, **params: Any) -> PlannedCall:
        """Resolve the operation and price it. No network. `runners` is only an estimation
        hint for the per-BenchmarkedRun component; it is never sent."""
        op = self.spec.find_operation(op_name)
        clean = {k: v for k, v in params.items() if v is not None}
        known = set(op.path_params()) | set(op.query_params())
        unknown = set(clean) - known
        if unknown:
            raise SpecError(
                f"{op.key}: parameters {sorted(unknown)} are not declared in the spec "
                f"(declared: path={op.path_params()} query={op.query_params()})"
            )
        missing = [p.name for p in op.parameters if p.required and p.name not in clean and p.location != "header"]
        if missing:
            raise SpecError(f"{op.key}: required parameters missing: {missing}")
        return PlannedCall(op=op, params=clean, credits=self.costs.cost_of(op.key, clean, runners=runners), runners=runners)

    # ---- calling -------------------------------------------------------------------

    def call(self, op_name: str, **params: Any) -> Any:
        planned = self.plan(op_name, **params)
        return self.execute(planned)

    def execute(self, planned: PlannedCall) -> Any:
        if self.key_kind == "live" and not self.allow_live:
            raise LiveCallRefused(
                f"refusing live call {planned.op.key} for {planned.credits} credits: "
                "client built without allow_live=True (the scripts set it only after you confirm an estimate)"
            )
        op, params = planned.op, planned.params
        url = self.base_url + op.path
        for name in op.path_params():
            url = url.replace("{" + name + "}", str(params[name]))
        query = {k: v for k, v in params.items() if k in op.query_params()}
        headers = {self.header_name: self.api_key, "Accept": "application/json"}

        status: int | None = None
        payload: Any = None
        charged = planned.credits
        note: str | None = None
        try:
            resp = self.session.request(op.method.upper(), url, params=query, headers=headers, timeout=self.timeout)
            status = resp.status_code
            if 200 <= status < 300:
                try:
                    payload = resp.json()
                except ValueError as e:
                    raise FormKingError(op, status, f"non-JSON body: {resp.text[:200]}") from e
                # The variable component is charged on what came back, not what was asked for.
                charged = self.costs.actual_cost(op.key, params, count_benchmarks(payload))
                if charged != planned.credits:
                    note = f"estimated {planned.credits}, charged {charged} from the response"
            else:
                charged = planned.credits if self.charge_failed else 0
                note = f"non-2xx (status={status})"
        except FormKingError:
            raise
        except Exception:
            charged = planned.credits if self.charge_failed else 0
            note = "transport failure before a response"
            raise
        finally:
            self.ledger.record(
                op.key, charged, key_kind=self.key_kind, method=op.method.upper(), path=op.path,
                params=params, http_status=status, note=note,
            )
        if not (200 <= status < 300):
            raise FormKingError(op, status, resp.text)
        return payload
