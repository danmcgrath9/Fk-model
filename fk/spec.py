"""Read the Form King OpenAPI spec and expose the parts the client needs.

Nothing here knows a path or a parameter name. It is all discovered from the
YAML so that the spec is the single source of truth, as the API's own doc is.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


class SpecError(Exception):
    """The spec is missing, unreadable, or does not declare what was asked of it."""


@dataclass(frozen=True)
class Parameter:
    name: str
    location: str  # path | query | header
    required: bool
    schema: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Operation:
    summary: str
    operation_id: str
    method: str  # lower case
    path: str
    description: str
    parameters: tuple[Parameter, ...]
    extensions: dict[str, Any] = field(default_factory=dict)  # x-* keys on the operation

    @property
    def key(self) -> str:
        """The name used in the ledger and the cost table: summary, else operationId."""
        return self.summary or self.operation_id

    def path_params(self) -> list[str]:
        return [p.name for p in self.parameters if p.location == "path"]

    def query_params(self) -> list[str]:
        return [p.name for p in self.parameters if p.location == "query"]


def _norm(s: str | None) -> str:
    return re.sub(r"[\s_\-]+", "", (s or "").lower())


class Spec:
    def __init__(self, raw: dict[str, Any], source: str = "<memory>"):
        if not isinstance(raw, dict) or "paths" not in raw:
            raise SpecError(f"{source}: not an OpenAPI document (no 'paths')")
        self.raw = raw
        self.source = source
        self.operations: list[Operation] = self._collect_operations()

    @classmethod
    def load(cls, path: str | Path) -> "Spec":
        p = Path(path)
        if not p.exists():
            raise SpecError(
                f"Spec not found at {p}. Put b2c-openapi.yaml (version 1.0.8) in the project "
                "root or set FK_SPEC_PATH."
            )
        with p.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)
        return cls(raw, source=str(p))

    # ---- discovery -----------------------------------------------------------------

    @property
    def version(self) -> str:
        return str(self.raw.get("info", {}).get("version", ""))

    @property
    def title(self) -> str:
        return str(self.raw.get("info", {}).get("title", ""))

    @property
    def info_description(self) -> str:
        return str(self.raw.get("info", {}).get("description", "") or "")

    def base_url(self) -> str:
        servers = self.raw.get("servers") or []
        if not servers or not servers[0].get("url"):
            raise SpecError("spec declares no servers[0].url; set FK_BASE_URL")
        return str(servers[0]["url"]).rstrip("/")

    def api_key_header(self) -> str:
        """Name of the header that carries the API key, from components.securitySchemes."""
        schemes = (self.raw.get("components") or {}).get("securitySchemes") or {}
        for name, scheme in schemes.items():
            if (scheme or {}).get("type") == "apiKey" and scheme.get("in") == "header":
                return str(scheme["name"])
        raise SpecError(
            "no apiKey/header security scheme in components.securitySchemes; "
            f"schemes present: {list(schemes)}"
        )

    def _collect_operations(self) -> list[Operation]:
        ops: list[Operation] = []
        for path, item in (self.raw.get("paths") or {}).items():
            if not isinstance(item, dict):
                continue
            shared = item.get("parameters") or []
            for method in ("get", "post", "put", "delete", "patch"):
                op = item.get(method)
                if not isinstance(op, dict):
                    continue
                params = tuple(
                    self._param(p) for p in (list(shared) + list(op.get("parameters") or []))
                )
                ops.append(
                    Operation(
                        summary=str(op.get("summary") or "").strip(),
                        operation_id=str(op.get("operationId") or "").strip(),
                        method=method,
                        path=str(path),
                        description=str(op.get("description") or ""),
                        parameters=params,
                        extensions={k: v for k, v in op.items() if k.startswith("x-")},
                    )
                )
        return ops

    def _param(self, p: dict[str, Any]) -> Parameter:
        if "$ref" in p:
            p = self._resolve(p["$ref"])
        return Parameter(
            name=str(p.get("name")),
            location=str(p.get("in", "query")),
            required=bool(p.get("required", False)),
            schema=dict(p.get("schema") or {}),
        )

    def _resolve(self, ref: str) -> dict[str, Any]:
        if not ref.startswith("#/"):
            raise SpecError(f"external $ref not supported: {ref}")
        node: Any = self.raw
        for part in ref[2:].split("/"):
            node = node[part.replace("~1", "/").replace("~0", "~")]
        return node

    def find_operation(self, name: str) -> Operation:
        """Match by summary, then operationId, ignoring case, spaces, hyphens, underscores."""
        want = _norm(name)
        for op in self.operations:
            if _norm(op.summary) == want:
                return op
        for op in self.operations:
            if _norm(op.operation_id) == want:
                return op
        available = [f"{o.method.upper()} {o.path}  summary={o.summary!r} operationId={o.operation_id!r}" for o in self.operations]
        raise SpecError(
            f"operation {name!r} not in spec {self.source}. Edit fk/ops.py to one of:\n  " + "\n  ".join(available)
        )
