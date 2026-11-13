"""Betwatch beta API, read from its own published spec (13 Nov 2026). Prints the auth scheme, every path with its
method, summary and parameters, then the API overview doc. Public pages only; no key needed or printed.
    python scripts/betwatch_beta_spec.py"""
import json, urllib.request

UA = {"User-Agent": "fk-model/1.0"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read().decode("utf-8", "replace")


spec = json.loads(get("https://beta.betwatch.com/api/openapi.json"))
print("servers:", spec.get("servers"))
print("security schemes:", json.dumps(spec.get("components", {}).get("securitySchemes"), indent=1))
print("global security:", spec.get("security"))
for path, ops in spec.get("paths", {}).items():
    for method, op in ops.items():
        if not isinstance(op, dict): continue
        params = ", ".join(f"{p.get('name')}({p.get('in')}{', required' if p.get('required') else ''})" for p in op.get("parameters", []))
        print(f"\n{method.upper()} {path}: {op.get('summary') or op.get('operationId') or ''}")
        if op.get("description"): print("  " + op["description"][:400].replace("\n", " "))
        if params: print("  params: " + params)
print("\n\n==== API overview doc ====")
txt = get("https://beta.betwatch.com/docs/api/llms.txt")
print(txt[:6000])
