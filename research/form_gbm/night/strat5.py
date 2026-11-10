"""Audit of the order sheet's blocking rules on 11 months (night of 10 Nov 2026).
The first-up block, the bounce block, the second-up (EARLY) $15 cap and the metro $12 cap were each set on the holdout
from June. Here: every bet the live edge rule would strike WITHOUT those blocks (first starters still out), walk-forward
trees, 1 Jan - 9 Nov 2026, deduction fitted by race; the bets each block stops, in four periods, at the open and flat
at BSP. A block earns its place if the bets it stops lose (or make clearly less than the book) in most periods.
    python3.13 strat5.py   (night folder)"""
import numpy as np, sys
sys.argv = ["x"]
exec(open("strat3.py").read().split("P_wf = ")[0])
P_wf = np.where(date >= "2026-06-03", np.load("preds/base_A.npy"), np.load("preds/base_B.npy")).astype(float)
ded = np.load("ded_r.npy")[ri]; oos = date >= "2026-01-01"
# the fu_json.py rules over the whole dataset
P_ = D["P"].astype(float); f = {str(n): i for i, n in enumerate(D["past_fields"])}; cols = {str(x): i for i, x in enumerate(D["cols"])}
tr = P_[:, :, f["trial"]] == 1; fin = P_[:, :, f["finish"]]; days = P_[:, :, f["days_before"]]; run_ = P_[:, :, f["runners"]]; dist_ = P_[:, :, f["distance"]]
rat = P_[:, :, f["rating"]]; mg = P_[:, :, f["margin"]]; prep = P_[:, :, f["prep"]]; real = ~tr & np.isfinite(fin) & (fin > 0); rdist = D["distance"].astype(float)[ri]
n = len(ri); bounce = np.zeros(n, bool); fu_short = np.zeros(n, bool); fu_trial = np.zeros(n, bool); early = np.zeros(n, bool)
for k in range(n):
    idx = np.where(real[k])[0]
    if not len(idx): continue
    j = idx[0]; gap = days[k, j]
    if len(idx) > 1 and np.isfinite(rat[k, j]):
        best = np.nanmax(rat[k, idx[1:]])
        if np.isfinite(best) and rat[k, j] >= best + 3: bounce[k] = True
    if prep[k, j] == 1 and (fin[k, j] <= 3 or (np.isfinite(mg[k, j]) and mg[k, j] <= 2)): early[k] = True
    if not (gap >= 60): continue
    if dist_[k, j] - rdist[k] >= 200: fu_short[k] = True
    t = np.where(tr[k] & np.isfinite(fin[k]) & (fin[k] > 0) & (days[k] < gap))[0]
    if len(t) and (fin[k, t[0]] - 1) / max(run_[k, t[0]] - 1, 1) > 0.5: fu_trial[k] = True
track = np.char.lower(D["track"][ri].astype(str)); metro = np.isin(track, ("flemington", "caulfield", "caulfield heath", "moonee valley", "sandown hillside", "sandown lakeside"))
print(f"flags over {n} runners: bounce {bounce.mean():.3f}, first-up short of trip {fu_short.mean():.3f}, first-up off a poor trial {fu_trial.mean():.3f}, second-up after a good first-up {early.mean():.3f}, metro {metro.mean():.3f}")
I, S_, Pr = sheet(P_wf, oos, ceil=3.0); u = np.where(won[I], S_ * (Pr - 1) * (1 - ded[I]), -S_); ub = np.where(won[I], (bs[I] - 1) * 0.92, -1.0)
PERS = (("Jan-17Mar", "2026-01-01", "2026-03-18"), ("18Mar-2Jun", "2026-03-18", "2026-06-03"), ("3Jun-8Oct", "2026-06-03", "2026-10-09"), ("9Oct-9Nov", "2026-10-09", "2027-01-01"))
pr_ = np.select([(date[I] >= lo) & (date[I] < hi) for _, lo, hi in PERS], [0, 1, 2, 3], -1)
def line(lab, m):
    cells = [f"{int((m & (pr_ == j)).sum())} {u[m & (pr_ == j)].sum():+.0f}u {100*u[m & (pr_ == j)].sum()/max(S_[m & (pr_ == j)].sum(),1e-9):+.0f}%" for j in range(4)]
    print(f"| {lab} | " + " | ".join(cells) + f" | {int(m.sum())}, {u[m].sum():+.0f}u, {100*u[m].sum()/max(S_[m].sum(),1e-9):+.0f}% | {100*ub[m].mean():+.0f}% | {np.median(bs[I[m]]/Pr[m]):.2f} |")
blocked = (bounce | fu_short | fu_trial)[I]; e = early[I] & ~blocked; mt = metro[I]
print("\n| bets | " + " | ".join(p[0] for p in PERS) + " | all: bets, profit, ROI at the open | flat at BSP | BSP/open |\n|---|---|---|---|---|---|---|---|")
line("every bet the edge rule strikes (no blocks)", np.ones(len(I), bool)); line("clear of the three blocks", ~blocked)
line("BLOCKED: bounce (last start a new peak by 3+)", bounce[I]); line("BLOCKED: resuming 60+ days, 200m+ short of last start", fu_short[I]); line("BLOCKED: resuming 60+ days off a bottom-half trial", fu_trial[I])
line("any of the three blocks", blocked)
print("| | | | | | | | |")
line("second-up after a good first-up (EARLY), open to $8", e & (Pr < 8)); line("EARLY, open $8-$15 (allowed since 1 Nov)", e & (Pr >= 8) & (Pr <= 15)); line("EARLY, open over $15 (CAPPED OUT)", e & (Pr > 15))
line("not EARLY, open over $15 (allowed)", ~early[I] & ~blocked & (Pr > 15))
print("| | | | | | | | |")
line("metro, open under $12", mt & ~blocked & (Pr < 12)); line("metro, open $12+ (CAPPED OUT)", mt & ~blocked & (Pr >= 12)); line("not metro, open $12+", ~mt & ~blocked & (Pr >= 12))
