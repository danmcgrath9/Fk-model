"""What does pricing BEFORE riders are declared cost? (night of 10 Nov 2026). The 12:17pm run waits for riders; several
meetings open before then. Replay, races 15 Oct - 9 Nov, frozen live models, history to 14 Oct as live: the same races
priced with NO rider declared on any runner (jockey name blank, every jockey input set to the history's median rider,
which is what the 1 Nov rider fix does for an undeclared rider), against the normal replay.
    python3.13 replay_noriders.py   (replay folder, after replay_stale.py)"""
import re, sys, time
import numpy as np
sys.argv = ["x"]
src = open("replay_stale.py").read(); exec(src.split('CUT = "2026-10-14"')[0])
CUT = "2026-10-14"; days = sorted(set(rdate[rdate > CUT])); cols = [str(c) for c in Z["cols"]]
jcols = [i for i, n in enumerate(cols) if re.search(r"(jockey|^jt_|^j_|apprentice|ridingweight)", n, re.I)]
hist_rows = rdate[Z["race_idx"]] <= CUT; med = np.nanmedian(Z["X"][hist_rows][:, jcols], axis=0)
print("jockey inputs blanked:", len(jcols), [cols[i] for i in jcols][:8], flush=True)
OUT = np.full((nrun, 4), np.nan)
for d in days:
    t0 = time.time(); Um, uidx = subset(rdate == d); Ub = blank(Um)
    Ub["X"] = Ub["X"].copy(); Ub["X"][:, jcols] = med; Ub["jockey"] = np.array([""] * len(Ub["jockey"]), dtype=Ub["jockey"].dtype)
    Hd, hidx = subset(rdate <= CUT); pt, pc, p1 = stage1(Hd, Ub); p2 = stage2f(Hd, POOF[hidx], Ub, p1)
    OUT[uidx] = np.column_stack([pt, pc, p1, p2]); print(d, f"{time.time()-t0:.0f}s", flush=True)
np.save("replay_noriders.npy", OUT)
R = np.load("replay_stale.npz"); ri = Z["race_idx"]; bs = Z["bsp"].astype(float); won = Z["finish"] == 1; nR = nrace
okb = np.isfinite(bs) & (bs > 1); inv = np.where(okb, 1 / np.where(okb, bs, 2), 0); q = inv / np.maximum(np.bincount(ri, weights=inv, minlength=nR)[ri], 1e-12)
g = ((np.bincount(ri, weights=~okb, minlength=nR) == 0) & (np.bincount(ri, weights=won, minlength=nR) == 1))[ri] & np.isfinite(OUT[:, 3]) & np.isfinite(R["stale"][:, 3])
races = len(np.unique(ri[g])); kl = lambda p: np.sum(np.where(q[g] > 0, q[g] * np.log(np.maximum(q[g], 1e-300) / np.maximum(p[g], 1e-12)), 0)) / races
ll = lambda p: -np.mean(np.log(np.maximum(p[g & won], 1e-12)))
print(f"\n{races} races, 15 Oct - 9 Nov\n| price | KL to BSP | winner log loss |\n|---|---|---|")
for lab, p in (("stage 1, riders in", R["stale"][:, 2]), ("stage 1, NO riders", OUT[:, 2]), ("stage 2, riders in", R["stale"][:, 3]), ("stage 2, NO riders", OUT[:, 3])):
    print(f"| {lab} | {kl(p):.4f} | {ll(p):.4f} |")
d = np.abs(np.log(OUT[g, 3] / R["stale"][g, 3])); print(f"\nrunner by runner the no-rider price is a median {100*np.median(d):.1f}% from the price with riders (90th pct {100*np.percentile(d, 90):.0f}%, over 10%: {100*np.mean(d > 0.0953):.0f}%)")
