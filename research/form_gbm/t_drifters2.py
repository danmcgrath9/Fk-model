"""Part 2 of t_drifters.py: can the big drifters be spotted before the open, and does leaving them out help?
Rules and a cross-fitted LightGBM (train on one half of the holdout dates, score the other)."""
import numpy as np, lightgbm as lgb
from sklearn.metrics import roc_auc_score
exec(open("t_drifters.py").read().split("print(f\"open bets")[0])
B = np.where(stake > 0)[0]; drift = bs[B] / o[B]; w = won[B]; st = stake[B]
pl = np.where(w, st * (o[B] - 1) * 0.84, -st); plb = np.where(w, st * (bs[B] - 1) * 0.92, -st)
cols = [str(c) for c in z["cols"]]; X = z["X"][B].astype(float); col = lambda n: X[:, cols.index(n)]
d = date[B]; cut = sorted(set(d))[len(set(d)) // 2]; H1 = d < cut; H2 = ~H1
fs = col("firstStarter") == 1; unr = col("unrated") == 1; few = col("raw_starts") <= 3; fu = col("raw_first_up") == 1
def show(keep, lab):
    out = []
    for h in (H1, H2):
        g = keep & h
        out.append(f"{g.sum()} bets, {np.sum(st[g]*o[B][g]/bs[B][g])/st[g].sum():.2f}x BSP, {pl[g].sum()/st[g].sum():+.0%}")
    print(f"| {lab} | {out[0]} | {out[1]} |")
print(f"halves split at {cut}\n\n| rule | first half | second half |\n|---|---|---|")
allb = np.ones(len(B), bool)
show(allb, "all open bets (as now in this test)")
show(~fs, "no first starters")
show(~fs & ~unr, "no first starters, no unrated")
show(~few, "no horses with 3 or fewer starts")
show(~(fu & few), "no first-up horses with 3 or fewer starts")
print("\nWhat the dropped bets did:\n\n| dropped group | first half | second half |\n|---|---|---|")
show(fs, "first starters")
show(unr & ~fs, "unrated (not first starters)")
show(few & ~fs, "3 or fewer starts (not first starters)")
# GBM: predict big drift (BSP >= 1.25 x open) from what is known before the open + the open itself
F = np.column_stack([X, 1 / pm[B], o[B], o[B] * pm[B], cnt[ri[B]], z["distance"][ri[B]], (1 / o[B]) / qo[B]])
y = (drift >= 1.25).astype(int)
pred = np.zeros(len(B))
for tr, te in ((H1, H2), (H2, H1)):
    mdl = lgb.LGBMClassifier(n_estimators=200, learning_rate=0.03, num_leaves=8, min_child_samples=20, subsample=0.8,
                             subsample_freq=1, colsample_bytree=0.5, verbose=-1).fit(F[tr], y[tr])
    pred[te] = mdl.predict_proba(F[te])[:, 1]
print(f"\nGBM predicting big drift, cross-fitted: AUC first half {roc_auc_score(y[H1], pred[H1]):.3f}, second half {roc_auc_score(y[H2], pred[H2]):.3f} (0.5 = no skill)")
print("\n| drop the bets the GBM rates most likely to drift | first half | second half |\n|---|---|---|")
for q in (0, 0.1, 0.2, 0.3):
    keep = np.ones(len(B), bool)
    for h in (H1, H2):
        if q: thr = np.quantile(pred[h], 1 - q); keep[h & (pred >= thr)] = False
    show(keep, f"drop top {q:.0%}" if q else "keep all")
print("\n| the dropped slice itself | first half | second half |\n|---|---|---|")
for q in (0.1, 0.2):
    drop = np.zeros(len(B), bool)
    for h in (H1, H2):
        thr = np.quantile(pred[h], 1 - q); drop[h & (pred >= thr)] = True
    show(drop, f"top {q:.0%} by predicted drift")
