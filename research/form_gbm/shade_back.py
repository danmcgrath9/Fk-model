"""Back-settler shade (live from 7 Oct 2026, t_backsettle.py): a runner that usually settles back (settle share
0.65+) has its chance x0.85, then every race is renormalised to 100% IN THE FILE, so the rest of the field picks the
difference up and anything reading p reads a 100% book (added 8 Oct 2026: before that only the betting scripts
renormalised, and a quick read of the raw file came out 0-10% long). Run after apply_stage2f.py on the same day file:
python shade_back.py V6_JSON DAY_NPZ   (rewrites V6_JSON; the unshaded chance stays as p_unshaded)"""
import json, sys
import numpy as np

SHADE, CUT = 0.85, 0.65
mj, npz = sys.argv[1:3]
U = np.load(npz, allow_pickle=True)
c = {str(x): i for i, x in enumerate(U["cols"])}
ss = {(str(U["race_id"][U["race_idx"][i]]), str(U["horse_id"][i])): float(U["X"][i, c["raw_settle_share"]]) for i in range(len(U["name"]))}
rows = json.load(open(mj)); k = 0
for r in rows:
    if "p_unshaded" in r:
        continue
    s = ss.get((r["race_id"], r["horse_id"]), float("nan"))
    r["p_unshaded"] = r["p"]; r["settle_share"] = None if not np.isfinite(s) else round(s, 3)
    if np.isfinite(s) and s >= CUT:
        r["p"] = r["p"] * SHADE; r["back_shaded"] = True; k += 1
tot = {}
for r in rows:
    tot[r["race_id"]] = tot.get(r["race_id"], 0.0) + r["p"]
for r in rows:
    r["p"] = r["p"] / tot[r["race_id"]]
json.dump(rows, open(mj, "w"), indent=1)
print(f"back-settler shade x{SHADE}: {k} of {len(rows)} runners")
