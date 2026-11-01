"""Every model input, live v training (1 Nov 2026, founder: "Can we test all inputs and make sure they make sense?", after
the undeclared-rider bug). For each of the 333 stage-1 columns, each past-run field and each sectional field: the share
missing, the share exactly zero and the median, on the day files we priced live (12 meetings, 26 Oct - 3 Nov) against the
training data's most recent four months (from 3 Jun). A column whose live shape differs from training is flagged: that is
how an input that arrives empty and is read as zero shows up."""
import numpy as np, glob, sys
S = "/tmp/claude-0/-home-user-cafe-copilot/3bac7eba-1a73-583c-b23d-aae29b750b5b/scratchpad"
T = np.load("ds/model_ds_v10.npz", allow_pickle=True); cols = [str(x) for x in T["cols"]]
tm = T["date"].astype(str)[T["race_idx"]] >= "2026-06-03"; XT = T["X"][tm].astype(float)
files = [f for f in glob.glob(f"{S}/{{nov,sat31,fri30}}/*.npz".replace("{nov,sat31,fri30}", "*")) if not any(k in f for k in ("_s.npz", "jk", "x.npz", "_s6.npz", "_s7.npz"))]
files = [f for f in files if any(f"/{d}/" in f for d in ("nov", "sat31", "fri30"))]
XL = []; names = []
for f in files:
    z = np.load(f, allow_pickle=True)
    if [str(x) for x in z["cols"]] != cols: print("column mismatch", f); continue
    XL.append(z["X"].astype(float)); names.append(f.split("/")[-2] + "/" + f.split("/")[-1])
XL = np.vstack(XL); print(f"live: {len(XL)} runners from {len(names)} files {names}; training slice: {len(XT)} runners")
def shape(A):
    nan = np.isnan(A).mean(0); zero = (A == 0).mean(0)
    with np.errstate(all="ignore"): med = np.nanmedian(np.where(np.isnan(A), np.nan, A), 0); q1 = np.nanpercentile(A, 25, 0); q3 = np.nanpercentile(A, 75, 0)
    return nan, zero, med, q1, q3
nt, zt, mt, q1t, q3t = shape(XT); nl, zl, ml, _, _ = shape(XL)
flag = []
for j, cname in enumerate(cols):
    iqr = (q3t[j] - q1t[j]) if np.isfinite(q3t[j] - q1t[j]) and q3t[j] > q1t[j] else (abs(mt[j]) + 1e-9)
    shift = abs(ml[j] - mt[j]) / iqr if np.isfinite(ml[j]) and np.isfinite(mt[j]) else (0 if np.isnan(ml[j]) == np.isnan(mt[j]) else 9)
    why = []
    if abs(nl[j] - nt[j]) > 0.10: why.append(f"missing {100*nt[j]:.0f}% -> {100*nl[j]:.0f}%")
    if abs(zl[j] - zt[j]) > 0.10: why.append(f"zero {100*zt[j]:.0f}% -> {100*zl[j]:.0f}%")
    if shift > 0.75: why.append(f"median {mt[j]:.3g} -> {ml[j]:.3g}")
    if why: flag.append((cname, "; ".join(why)))
print(f"\nFLAGGED stage-1 columns: {len(flag)} of {len(cols)}")
for c_, w in flag: print(f"  {c_:45s} {w}")
for key, fk in (("P", "past_fields"), ("S", "sec_fields")):
    ft = [str(x) for x in T[fk]]; AT = T[key][tm].astype(float)
    AL = np.vstack([np.load(f, allow_pickle=True)[key].astype(float) for f in files])
    print(f"\n{key} ({'past runs' if key == 'P' else 'sectionals'}): share missing among existing past rows")
    for j, fn in enumerate(ft):
        has_t = np.isfinite(AT[:, :, 0]) if key == "P" else np.isfinite(AT).any(2); has_l = np.isfinite(AL[:, :, 0]) if key == "P" else np.isfinite(AL).any(2)
        a = np.isnan(AT[:, :, j])[has_t].mean() if key == "P" else np.isnan(AT[:, :, j]).mean(); b = np.isnan(AL[:, :, j])[has_l].mean() if key == "P" else np.isnan(AL[:, :, j]).mean()
        za = (AT[:, :, j] == 0).mean(); zb = (AL[:, :, j] == 0).mean()
        if abs(a - b) > 0.08 or abs(za - zb) > 0.08: print(f"  {fn:16s} missing {100*a:.0f}% -> {100*b:.0f}%   zero {100*za:.0f}% -> {100*zb:.0f}%")
