"""First look at a Form King historical archive (unzipped folder): the README, the file tree, sizes, and one sample
record from each endpoint folder, with the fields it carries. python scripts/archive_inspect.py ARCHIVE_DIR"""
import json, os, sys
root = sys.argv[1]
print(f"# Archive: {root}\n")
for dp, dn, fn in os.walk(root):
    for f in fn:
        if f.lower().startswith("readme"):
            print(f"## {os.path.join(dp, f)}\n```\n{open(os.path.join(dp, f), errors='replace').read()[:12000]}\n```\n")
print("## Tree (folders, file counts, total size)\n")
for dp, dn, fn in sorted(os.walk(root)):
    if fn:
        size = sum(os.path.getsize(os.path.join(dp, f)) for f in fn)
        print(f"- {os.path.relpath(dp, root)}: {len(fn)} files, {size/1e6:.1f} MB, e.g. {sorted(fn)[:3]}")
print("\n## Sample records\n")
seen = set()
for dp, dn, fn in sorted(os.walk(root)):
    for f in sorted(fn):
        if not f.endswith(".json") or dp in seen: continue
        seen.add(dp)
        try:
            d = json.load(open(os.path.join(dp, f)))
        except Exception as e:
            print(f"- {f}: unreadable ({e})"); continue
        def keys(x, depth=0, pre=""):
            out = []
            if isinstance(x, dict):
                for k, v in list(x.items())[:60]:
                    out.append(f"{pre}{k}: {type(v).__name__}")
                    if depth < 2 and isinstance(v, (dict, list)): out += keys(v if isinstance(v, dict) else (v[0] if v else {}), depth + 1, pre + "  ")
            return out
        top = d if isinstance(d, dict) else (d[0] if d else {})
        print(f"### {os.path.relpath(os.path.join(dp, f), root)}\n```\n" + "\n".join(keys(top)[:150]) + "\n```\n")
for dp, dn, fn in os.walk(root):
    for f in fn:
        if f.endswith(".py"): print(f"## Script {os.path.relpath(os.path.join(dp, f), root)}: {sum(1 for _ in open(os.path.join(dp, f), errors='replace'))} lines")
