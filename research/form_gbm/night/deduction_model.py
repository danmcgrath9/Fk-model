"""A deduction that varies by race, fitted to what TAB actually charged (night of 10 Nov 2026).

The backtest takes a flat 16c from every winner at the open. But a race's opening prices tell how much of the market was
scratched after it opened: the runners that RAN add up to "the opening book"; a full opening market adds up to about
120%; the shortfall is the scratched runners' share, and TAB's deduction follows it. In 22% of races the runners that
ran add up to under 100%: a fifth or more of the opening market came out, and the bets struck at that open were on
prices that only existed because those horses were still in.
Step 1: TAB's actual deductions (the founder's reports, data/live_bets/*-deductions-actual.txt) against the shortfall of
the same race. Step 2: the live sheet's backtest settled with the fitted deduction instead of the flat 16c.
    python3.13 deduction_model.py   (night folder)"""
import glob, os, re, sys
import numpy as np
sys.argv = ["x"]
exec(open("strat3.py").read().split("P_wf = ")[0])
L = "/home/user/fk-model/data/live_bets"
okop = np.isfinite(o) & (o > 1); book_r = np.bincount(ri, weights=np.where(okop, 1 / np.where(okop, o, 2), 0), minlength=nR)
rid = D["race_id"].astype(str); track = np.char.lower(D["track"].astype(str)); rd = nl.rdate
rows = []
for f in sorted(glob.glob(f"{L}/*-deductions-actual.txt")):
    b = os.path.basename(f)[:-22]; day, trk = b[:10], b[11:].replace("-", " ")
    for l in open(f):
        pa = [x.strip() for x in l.split("#")[0].split(",")]
        if len(pa) < 2 or not pa[0].isdigit(): continue
        m = np.where((rd == day) & (track == trk) & np.array([x.rsplit("_", 1)[-1] == pa[0] for x in rid]))[0]
        if len(m) == 1 and nl.race_ok[m[0]]: rows.append((b, int(pa[0]), float(pa[1]) / 100, book_r[m[0]]))
act = np.array([r[2] for r in rows]); bk = np.array([r[3] for r in rows])
print(f"TAB's actual deductions matched to a race with every open: {len(rows)} races, mean {100*act.mean():.1f}c, median {100*np.median(act):.0f}c, none in {100*np.mean(act == 0):.0f}%")
print("| opening book of the runners that ran | races | mean actual deduction | median | largest |\n|---|---|---|---|---|")
for lo, hi in ((0, 0.9), (0.9, 1.0), (1.0, 1.1), (1.1, 1.2), (1.2, 9)):
    m = (bk >= lo) & (bk < hi)
    if m.any(): print(f"| {lo:.1f}-{hi:.1f} | {int(m.sum())} | {100*act[m].mean():.1f}c | {100*np.median(act[m]):.0f}c | {100*act[m].max():.0f}c |")
# fit: deduction = k * max(0, B0 - book), least squares over a grid of B0
best = None
for B0 in np.arange(1.10, 1.36, 0.01):
    x = np.maximum(0, B0 - bk); k = float(x @ act / max(x @ x, 1e-12)); sse = float(np.sum((act - k * x) ** 2))
    if best is None or sse < best[0]: best = (sse, B0, k)
_, B0, K = best; pred = K * np.maximum(0, B0 - bk)
print(f"\nfit: deduction = {K:.2f} x max(0, {B0:.2f} - opening book); correlation with the actual {np.corrcoef(pred, act)[0,1]:.2f}; mean fitted {100*pred.mean():.1f}c against actual {100*act.mean():.1f}c")
ded_r = np.clip(K * np.maximum(0, B0 - book_r), 0, 0.75); ded = ded_r[ri]
full = nl.race_ok; print(f"fitted deduction over all {int(full.sum())} races with every open: mean {100*ded_r[full].mean():.1f}c, median {100*np.median(ded_r[full]):.0f}c, 30c+ in {100*np.mean(ded_r[full] >= 0.3):.0f}% of races")

P_wf = np.where(date >= "2026-06-03", np.load("preds/base_A.npy"), np.load("preds/base_B.npy")).astype(float)
PERS = (("Jan-17Mar", "2026-01-01", "2026-03-18"), ("18Mar-2Jun", "2026-03-18", "2026-06-03"), ("3Jun-8Oct", "2026-06-03", "2026-10-09"), ("9Oct-9Nov", "2026-10-09", "2027-01-01"))
P_cf = np.load("p_oof_chal.npy").astype(float)
PERS6 = (("Jul-Sep25", "2025-07-01", "2025-10-01"), ("Oct-Dec25", "2025-10-01", "2026-01-01"), ("Jan-Mar26", "2026-01-01", "2026-04-01"), ("Apr-Jun26", "2026-04-01", "2026-07-01"), ("Jul-Sep26", "2026-07-01", "2026-10-01"), ("Oct-9Nov26", "2026-10-01", "2027-01-01"))
def settle(I, S_, Pr, d): return np.where(won[I], S_ * (Pr - 1) * (1 - d), -S_)
for title, pm, pers in (("WALK-FORWARD TREES, 1 Jan - 9 Nov 2026", P_wf, PERS), ("CROSS-FITTED THREE-MODEL BLEND, 1 Jul 2025 - 9 Nov 2026", P_cf, PERS6)):
    pr_ = np.select([(date >= lo) & (date < hi) for _, lo, hi in pers], list(range(len(pers))), -1); oos = pr_ >= 0
    print(f"\n{title}: the live sheet, settled three ways\n| ceiling | deduction | " + " | ".join(p[0] for p in pers) + " | all | ROI | mean deduction on our winners |\n|" + "---|" * (len(pers) + 5))
    for lab, kw in (("3x (live)", dict(ceil=3.0)), ("6x", dict(ceil=6.0))):
        I, S_, Pr = sheet(pm, oos, **kw)
        for dl, d in (("flat 16c (the backtest)", np.full(len(I), 0.16)), ("fitted to the race", ded[I]), ("fitted x 1.5 (harsh)", np.clip(1.5 * ded[I], 0, 0.9))):
            u = settle(I, S_, Pr, d); w = won[I]
            print(f"| {lab} | {dl} | " + " | ".join(f"{u[pr_[I] == k].sum():+.0f}u" for k in range(len(pers))) + f" | {u.sum():+.0f}u | {100*u.sum()/S_.sum():+.0f}% | {100*np.average(d[w], weights=(S_ * (Pr - 1))[w]):.0f}c |")
np.save("ded_r.npy", ded_r)
