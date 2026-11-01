"""Flemington's straight (1 Nov 2026, founder: "Flemington 1000m and 1200m down the straight is a lot different than a 1000m or
1200m bend"). Flemington runs up to 1200m on the straight six; every other Victorian sprint is around a turn. v10 holdout
from 3 Jun: wins v the model and the market, by course type and by barrier third, and the bets under the live rule."""
import numpy as np, collections
pm_cur = None
exec(open("t_metro_fix.py").read().split("H1 = ")[0])
dist = z["distance"].astype(float)[ri]; base_ = np.array([base(t) for t in trk])[ri]
cols = list(z["cols"]); bar = z["X"][:, cols.index("barrier")].astype(float); fld = cnt[ri]
third = np.where(np.isnan(bar), "", np.where((bar - 1) / np.maximum(fld - 1, 1) < 1 / 3, "inside", np.where((bar - 1) / np.maximum(fld - 1, 1) < 2 / 3, "middle", "outside")))
ib = np.where(m, 1 / bs, 0); sb = np.bincount(ri, weights=ib, minlength=nR); pb = np.where(m, ib / np.where(sb[ri] > 0, sb[ri], 1), np.nan)
straight = (base_ == "Flemington") & (dist <= 1200)
def row(lab, g):
    g = g & m; w = won[g].sum(); e = pm0[g].sum(); eb = pb[g].sum()
    if g.sum(): print(f"  {lab:40s} runners {g.sum():5d} races {len(set(ri[g])):4d} won {w:4d}  model {e:6.1f} ({w/e:4.2f})  market {eb:6.1f} ({w/eb:4.2f})")
print("CALIBRATION")
row("Flemington straight (<=1200m)", straight)
row("Flemington round (>1200m)", (base_ == "Flemington") & (dist > 1200))
row("other tracks <=1200m (around a bend)", (base_ != "Flemington") & (dist <= 1200))
for t in ("inside", "middle", "outside"):
    row(f"  straight, barrier {t}", straight & (third == t))
for t in ("inside", "middle", "outside"):
    row(f"  bend sprints, barrier {t}", (base_ != "Flemington") & (dist <= 1200) & (third == t))
print("\nBETS (metro fix, $12 cap, full stakes)")
_t = open("t_metro_orders.py").read(); exec("C, W = 0.986, 0.8\ndef run2(" + _t.split("def run2(")[1].split("pm_cur = pm0")[0])
for lab, sel in (("Flemington straight", straight), ("Flemington round", (base_ == "Flemington") & (dist > 1200))):
    r = [(i, s) for i, s in run2(metro, False) if o[i] < 12 and sel[i]]
    if r:
        idx = np.array([i for i, _ in r]); st = np.array([s for _, s in r]); pl = np.where(won[idx], st * (o[idx] - 1) * 0.93, -st)
        print(f"  {lab:22s} {len(r)} bets {won[idx].sum()} won {st.sum():.1f}u {pl.sum():+.1f}u ({100*pl.sum()/st.sum():+.0f}%)")
    else: print(f"  {lab:22s} no bets")
