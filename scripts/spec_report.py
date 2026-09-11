"""Print what the spec declares: server, auth header, every operation, and the credit
costs we could read. Run this FIRST, then fix fk/ops.py and credits.yaml to match."""
from __future__ import annotations

from _common import bootstrap

import fk.ops as ops


def main() -> None:
    settings, spec, costs, _ = bootstrap("test")
    print(f"spec: {spec.source}  title={spec.title!r}  version={spec.version}")
    try:
        print(f"server: {spec.base_url()}")
    except Exception as e:  # noqa: BLE001
        print(f"server: NOT DECLARED ({e})")
    try:
        print(f"api key header: {spec.api_key_header()}")
    except Exception as e:  # noqa: BLE001
        print(f"api key header: NOT FOUND ({e})")
    print("\noperations:")
    for op in spec.operations:
        known = "known" if costs.known(op.key) else "UNKNOWN COST"
        print(f"  {op.method.upper():5} {op.path:45} summary={op.summary!r} operationId={op.operation_id!r}  [{known}]")
        for p in op.parameters:
            req = "required" if p.required else "optional"
            print(f"         - {p.location:6} {p.name} ({req}) {p.schema.get('type','')} {('default=' + str(p.schema['default'])) if 'default' in p.schema else ''}")
    print("\ncredit costs read:")
    for line in costs.describe() or ["  (none: write credits.yaml)"]:
        print("  " + line)
    print("\nfk/ops.py expects these operation names:")
    for name in (ops.UPCOMING_MEETINGS, ops.MEETINGS_BY_DATE, ops.MEETING_SUMMARY, ops.MEETING_SPEEDMAPS, ops.RACE_FORM, ops.HORSE_FORM, ops.USAGE_LOG):
        try:
            op = spec.find_operation(name)
            print(f"  {name!r:28} -> {op.method.upper()} {op.path}  {'priced' if costs.known(op.key) else 'NO COST KNOWN'}")
        except Exception as e:  # noqa: BLE001
            print(f"  {name!r:28} -> NOT IN SPEC: fix fk/ops.py ({str(e).splitlines()[0]})")
    if spec.info_description:
        print("\nspec info.description (credit costs are read from here):\n")
        print(spec.info_description)


if __name__ == "__main__":
    main()
