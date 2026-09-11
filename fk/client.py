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
    credits: int


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

    def plan(self, op_name: str, **params: Any) -> PlannedCall:
        """Resolve the operation and price it. No network."""
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
        return PlannedCall(op=op, params=clean, credits=self.costs.cost_of(op.key, clean))

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
        try:
            resp = self.session.request(op.method.upper(), url, params=query, headers=headers, timeout=self.timeout)
            status = resp.status_code
        finally:
            charged = planned.credits if (status is not None and 200 <= status < 300) or self.charge_failed else 0
            self.ledger.record(
                op.key, charged, key_kind=self.key_kind, method=op.method.upper(), path=op.path,
                params=params, http_status=status,
                note=None if status and 200 <= status < 300 else f"non-2xx or transport failure (status={status})",
            )
        if not (200 <= resp.status_code < 300):
            raise FormKingError(op, resp.status_code, resp.text)
        try:
            return resp.json()
        except ValueError as e:
            raise FormKingError(op, resp.status_code, f"non-JSON body: {resp.text[:200]}") from e
