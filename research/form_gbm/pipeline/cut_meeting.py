"""One meeting out of a day's export (12 Nov 2026: the price run exports each date once and the pricer cuts each meeting
out, instead of one export run per meeting). Keeps the races whose race_id is listed; runner arrays, race arrays and
race_idx are cut together.
    python3.13 cut_meeting.py DAY.npz OUT.npz RACE_ID[,RACE_ID...]"""
import sys
import numpy as np

src, out, ids = sys.argv[1], sys.argv[2], set(sys.argv[3].split(","))
Z = dict(np.load(src, allow_pickle=True)); ri = Z["race_idx"]; nrun, nrace = len(ri), len(Z["race_id"])
keep_r = np.array([str(r) in ids for r in Z["race_id"]]); keep_u = keep_r[ri]; new = np.cumsum(keep_r) - 1
if not keep_r.any():
    sys.exit(f"STOP: none of {sorted(ids)[:3]}... is in {src}")
o = {}
for k, v in Z.items():
    if k == "race_idx":
        continue
    if k not in ("cols", "past_fields", "sec_fields") and v.shape[:1] == (nrun,):
        o[k] = v[keep_u]
    elif k not in ("cols", "past_fields", "sec_fields") and v.shape[:1] == (nrace,):
        o[k] = v[keep_r]
    else:
        o[k] = v
o["race_idx"] = new[ri[keep_u]].astype(ri.dtype)
np.savez(out, **o)
print(f"{out}: {int(keep_r.sum())} races, {int(keep_u.sum())} runners, tracks {sorted(set(map(str, o['track'])))}")
