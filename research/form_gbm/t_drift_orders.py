"""The firm/drift stakes as the BetMatic orders would actually fire them (18 Oct 2026, founder: "let's do it").
Same holdout as t_drift_gbm.py PRICE=stage2 (races from 6 May with every open and BSP, stage-2 v6 price), split in two
by date; the forecast model and its thirds are fitted on one half and score the other. Orders as betmatic_orders.py
builds them: min odds 0.95 x (E / p^0.82)^(1/0.78) with E 1.2 (1.15 for an open under $4), 3 steps x1/1.25/1.5 under
the 3x ceiling, each sized at the next step's price on the live stake rule, our chance at an open t = p^0.82 x t^-0.22.
The multiplier is decided at each step's OWN price (the order is built before the market), opening chance there =
(1/t) / the median opening book for the field size. Totals capped at 5u. Settled at the open, 16c deduction.
Not modelled (the same for every version): first starters, first-up blocks, the race-level first-starter rule.

    python3.13 t_drift_orders.py      (in the model dir, needs ../model_v9/model_ds.npz and blend_hold.npz)"""
import numpy as np, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drift_forecast as dfc, stake_rule
T = dfc.load_training(); m = T["m"]; X, pm, o, field, won = T["X"], T["pm"], T["o"], T["field"], T["won"]
dates = T["date"]; ud = sorted(set(dates[m])); cut = ud[len(ud) // 2]; half = (dates >= cut).astype(int)
DED, TIERS, CAP = 0.16, (1.0, 1.25, 1.5), 5.0
book = lambda f: T["book_by_field"].get(int(f), np.median(list(T["book_by_field"].values())))
results = {}
for h in (0, 1):
    tr = m & (half != h); te = m & (half == h)
    bst, t1, t2 = dfc.fit(X, pm, o, field, T["book_actual"], T["y"], tr, T["book_by_field"])
    for i in np.where(te & (pm > 0))[0]:
        p = pm[i]; q = 1 / p
        if not (1.6 <= q <= 15) or o[i] >= 3 * q: continue
        E = 1.15 if o[i] < 4 else 1.2
        mo = 0.95 * (E / p ** 0.82) ** (1 / 0.78)
        if o[i] < mo: continue
        ts = [mo * s for s in TIERS if mo * s < 3 * q]
        ys = bst.predict(dfc.design(np.repeat(X[i][None, :], len(ts), 0), [p] * len(ts), ts, [field[i]] * len(ts), [book(field[i])] * len(ts)))
        for name, dm, fm in (("live stakes", 1.0, 1.0), ("drop the drift third, x2 on firmers (founder's pick)", 0.0, 2.0),
                             ("half on the drift third, x2 on firmers", 0.5, 2.0), ("drop the drift third, normal on firmers", 0.0, 1.0),
                             ("everyone normal, x2 on firmers only", 1.0, 2.0), ("firm third only, normal stakes", None, 1.0), ("firm third only, x2", None, 2.0)):
            tot = prev = 0.0
            for k, t in enumerate(ts):
                tp = ts[k + 1] if k + 1 < len(ts) else t
                base = stake_rule.stake(p ** 0.82 * tp ** -0.22, tp)
                mult = (0.0 if dm is None else dm) if ys[k] < t1 else fm if ys[k] >= t2 else (0.0 if dm is None else 1.0)
                T_k = min(CAP, base * mult); add = max(0.0, T_k - prev); prev = max(prev, T_k)
                if o[i] >= t: tot += add
            if tot > 0:
                pl = tot * (o[i] - 1) * (1 - DED) if won[i] else -tot
                results.setdefault((name, h), []).append((tot, pl))
print(f"holdout split at {cut}; orders as built before the market, the forecast at each step's own price\n")
print("| stakes | period | bets | units invested | profit | ROI |\n|---|---|---|---|---|---|")
names = []
for (name, h) in results:
    if name not in names: names.append(name)
for name in names:
    tt = []
    for h, lab in ((0, f"before {cut}"), (1, f"from {cut}")):
        r = np.array(results.get((name, h), [(0, 0)])); tt.append(r)
        print(f"| {name} | {lab} | {len(r)} | {r[:, 0].sum():.0f}u | {r[:, 1].sum():+.0f}u | {r[:, 1].sum() / r[:, 0].sum():+.0%} |")
    r = np.vstack(tt)
    print(f"| {name} | both | {len(r)} | {r[:, 0].sum():.0f}u | {r[:, 1].sum():+.0f}u | {r[:, 1].sum() / r[:, 0].sum():+.0%} |")
