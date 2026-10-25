"""Join day files (export_dataset npz) into one dataset npz with race_idx offset, so bench.load can read it.
python3.13 concat_days.py OUT.npz DAY1.npz DAY2.npz ..."""
import numpy as np, sys
out, files = sys.argv[1], sys.argv[2:]
parts = [np.load(f, allow_pickle=True) for f in files]
RACE = ("race_id", "date", "track", "distance", "lws", "going", "field", "pre_jump", "race_number")
SAME = ("cols", "past_fields", "sec_fields")
D = {}; off = 0; ri = []
for z in parts:
    r = z["race_idx"]; ri.append(r + off); off += int(r.max()) + 1 if len(r) else 0
D["race_idx"] = np.concatenate(ri)
# X columns can differ by day (a one-hot a day lacks): align by name on the union, in the first file's order first
cols = list(parts[0]["cols"])
for z in parts[1:]:
    cols += [c for c in z["cols"] if c not in cols]
pos = {c: i for i, c in enumerate(cols)}
Xs = []
for z in parts:
    x = np.full((z["X"].shape[0], len(cols)), np.nan, dtype=z["X"].dtype)
    for j, c in enumerate(z["cols"]): x[:, pos[c]] = z["X"][:, j]
    Xs.append(x)
D["X"] = np.concatenate(Xs); D["cols"] = np.array(cols)
for k in parts[0].files:
    if k in ("race_idx", "X", "cols"): continue
    if k in SAME: D[k] = parts[0][k]; continue
    D[k] = np.concatenate([z[k] for z in parts])
np.savez_compressed(out, **D)
print(out, "runners", len(D["race_idx"]), "races", int(D["race_idx"].max()) + 1, "P", D["P"].shape)
