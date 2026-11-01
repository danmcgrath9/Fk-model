"""Flemington straight, full history (Jul 2025 - Oct 2026) on out-of-fold predictions (p_oof_blend9: each race priced by
trees that never saw it). Calibration by course and barrier third; bets under the open rule at full stakes."""
import numpy as np, stake_rule
z = np.load("ds/model_ds.npz", allow_pickle=True); p = np.load("p_oof_blend9.npy").astype(float)
assert len(p) == len(z["race_idx"]), (len(p), len(z["race_idx"]))
ri = z["race_idx"]; nR = int(ri.max()) + 1; won = z["finish"] == 1; o = z["open"].astype(float); bs = z["bsp"].astype(float)
trk = z["track"].astype(str); dist = z["distance"].astype(float)[ri]; cnt = np.bincount(ri, minlength=nR); fld = cnt[ri]
base = lambda t: t.replace(" Synthetic","").replace(" Hillside","").replace(" Lakeside","").replace(" Heath","").replace(" Park","").strip()
bt = np.array([base(t) for t in trk])[ri]
ok = np.isfinite(p) & (p > 0) & np.isfinite(bs) & (bs > 1)
race_ok = (np.bincount(ri, weights=ok.astype(float), minlength=nR) == cnt) & (np.bincount(ri, weights=won.astype(float), minlength=nR) >= 1); m = race_ok[ri]
nrm = lambda v: np.where(m, v / np.where(np.bincount(ri, weights=np.where(m, v, 0), minlength=nR)[ri] > 0, np.bincount(ri, weights=np.where(m, v, 0), minlength=nR)[ri], 1), np.nan)
pm = nrm(p); pb = nrm(np.where(m, 1 / bs, 0))
cols = list(z["cols"]); bar = z["X"][:, cols.index("barrier")].astype(float); sh = (bar - 1) / np.maximum(fld - 1, 1)
third = np.where(np.isnan(bar), "", np.where(sh < 1/3, "inside", np.where(sh < 2/3, "middle", "outside")))
straight = (bt == "Flemington") & (dist <= 1200); bend = (bt != "Flemington") & (dist <= 1200)
def row(lab, g):
    g = g & m; w = won[g].sum(); e = pm[g].sum(); eb = pb[g].sum(); sd = np.sqrt((pm[g] * (1 - pm[g])).sum())
    if g.sum(): print(f"  {lab:34s} runners {g.sum():5d} races {len(set(ri[g])):4d} won {w:4d}  model {e:6.1f} ({w/e:4.2f}, z {(w-e)/sd:+.1f})  market {eb:6.1f} ({w/eb:4.2f})")
row("Flemington straight (<=1200m)", straight); row("Flemington round", (bt == "Flemington") & (dist > 1200)); row("bend sprints (<=1200m)", bend)
for t in ("inside", "middle", "outside"): row(f"  straight, barrier {t}", straight & (third == t))
for t in ("inside", "middle", "outside"): row(f"  bend sprints, barrier {t}", bend & (third == t))
# favourites v longer prices on the straight
for lo, hi in ((0, 5), (5, 12), (12, 999)): row(f"  straight, open ${lo}-{hi if hi<999 else 'up'}", straight & (o >= lo) & (o < hi))
def bets(sel):
    out = []
    for i in np.where(m & sel)[0]:
        q = 1 / pm[i]
        if not (1.6 <= q <= 15 and np.isfinite(o[i]) and o[i] < 3 * q and o[i] < 12): continue
        E = 1.15 if q < 4 else 1.2; mo = 0.95 * (E / pm[i] ** 0.82) ** (1 / 0.78)
        if o[i] < mo: continue
        s = stake_rule.stake(pm[i] ** 0.82 * o[i] ** -0.22, o[i]); out.append((i, s))
    return out
print("\nBETS at the open (no metro fix here: OOF chance as is, $12 cap, stake at the open price)")
for lab, sel in (("Flemington straight", straight), ("Flemington round", (bt == "Flemington") & (dist > 1200)), ("bend sprints", bend)):
    r = bets(sel); idx = np.array([i for i, _ in r]); st = np.array([s for _, s in r]); pl = np.where(won[idx], st * (o[idx] - 1) * 0.93, -st)
    print(f"  {lab:22s} {len(r):4d} bets {won[idx].sum():3d} won (exp {pm[idx].sum():5.1f}) {st.sum():6.1f}u {pl.sum():+7.1f}u ({100*pl.sum()/st.sum():+.0f}%)")
