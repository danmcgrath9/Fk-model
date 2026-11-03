"""Part 2 of the plunge research: what the drift forecast (drift_forecast.py) keys on, and how its thirds sort our
sheet bets by plunge rate, our A/E and return at the open (3 Nov 2026)."""
import json, re, numpy as np
src = open("t_all_rules.py").read().split('summ(plan(pm0), "all rules')[0]
exec(src)
meta = json.load(open("drift_meta.json")); cols_d = list(meta["cols"]) + ["log opening chance", "field size", "log(our chance) - log(opening chance)"]
t = open("drift_model.txt").read(); sec = t.split("feature_importances:")[1].split("\n\n")[0]
imp = sorted(((cols_d[int(k.split("_")[1])], int(v)) for k, v in (l.split("=") for l in sec.strip().splitlines() if "=" in l)), key=lambda x: -x[1])
print("DRIFT FORECAST, top 20 inputs by splits (what it keys on):")
for k, v in imp[:20]: print(f"  {k:45s} {v}")
d = np.load("drift_gbm_preds_v10.npz", allow_pickle=True)
pred = np.full(len(pmS), np.nan); act = np.full(len(pmS), np.nan)
pred[d["idx"]] = d["gb"]; act[d["idx"]] = d["ga"]
b = plan(pmS); idx = np.array([i for i, _ in b]); st = np.array([s for _, s in b])
ok = np.isfinite(pred[idx]); print(f"\nsheet bets with a forecast: {ok.sum()} of {len(idx)}")
ii = idx[ok]; ss = st[ok]; y = pred[ii]; ratio = bs[ii] / o[ii]
print(f"correlation of forecast with the actual move (log BSP chance / open chance): {np.corrcoef(y, act[ii])[0,1]:.2f}")
q = np.quantile(y, [1/3, 2/3])
print(f"{'forecast third':16s} {'n':>5s} {'plunge':>7s} {'BSP/open':>8s} {'won':>4s} {'ours exp':>8s} {'A/E ours':>8s} {'open ROI':>8s} {'BSP ROI':>7s}")
for lab, k in (("drift (bottom)", y < q[0]), ("middle", (y >= q[0]) & (y < q[1])), ("firm (top)", y >= q[1])):
    w = won[ii[k]]; s = ss[k]; plo = np.where(w, s * (o[ii[k]] - 1) * 0.93, -s).sum(); plb = np.where(w, s * (bs[ii[k]] - 1) * 0.92, -s).sum()
    print(f"{lab:16s} {k.sum():5d} {100*(ratio[k] <= 0.6).mean():6.0f}% {np.median(ratio[k]):8.2f} {w.sum():4d} {pmS[ii[k]].sum():8.1f} {w.sum()/pmS[ii[k]].sum():8.2f} {100*plo/s.sum():+7.0f}% {100*plb/s.sum():+6.0f}%")
print("\nfirm third by our price:")
for lo, hi in ((1.6, 3), (3, 5), (5, 8), (8, 15.01)):
    k = (y >= q[1]) & (1 / pmS[ii] >= lo) & (1 / pmS[ii] < hi)
    if k.sum() < 20: continue
    w = won[ii[k]]; s = ss[k]; plo = np.where(w, s * (o[ii[k]] - 1) * 0.93, -s).sum()
    print(f"  ours ${lo:g}-${hi:g}: {k.sum()} bets, plunge {100*(ratio[k] <= 0.6).mean():.0f}%, won {w.sum()} v ours {pmS[ii[k]].sum():.1f}, open ROI {100*plo/s.sum():+.0f}%")
