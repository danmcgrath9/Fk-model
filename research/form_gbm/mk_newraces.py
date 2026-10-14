"""Cut the races the old dataset does not hold out of the new export, as a day-style file the day pipeline can price
(price_day3.py, apply_stage2f.py, shade_back.py), runners without a finishing position (scratched) dropped so the
race is priced on its final field. python mk_newraces.py NEW_EXPORT OLD_EXPORT OUT_NPZ"""
import numpy as np, sys
new, old, outp = sys.argv[1:4]
N = dict(np.load(new, allow_pickle=True)); H = np.load(old, allow_pickle=True)
held = set(map(str, H["race_id"])); ri = N["race_idx"]; nR = len(N["race_id"])
fin = N["finish"].astype(float)
races = [r for r in range(nR) if str(N["race_id"][r]) not in held]
keep = np.isin(ri, races) & np.isfinite(fin) & (fin > 0)
races = [r for r in races if keep[ri == r].any()]
newidx = {r: i for i, r in enumerate(races)}; out = {}
for k, v in N.items():
    if hasattr(v, "shape") and v.shape[:1] == (len(ri),) and k not in ("cols", "past_fields", "sec_fields"): out[k] = v[keep]
    elif hasattr(v, "shape") and v.shape[:1] == (nR,): out[k] = v[races]
    else: out[k] = v
out["race_idx"] = np.array([newidx[r] for r in ri[keep]], dtype=np.int32)
np.savez(outp, **out)
d = np.asarray(out["date"]).astype(str)
import collections; print(len(races), "races", keep.sum(), "runners"); print(sorted(collections.Counter(x[:7] for x in d).items()))
