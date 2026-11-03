"""Backtest of the favourite-back rule (3 Nov 2026): back at BSP the Betfair SP favourite at $4-$7 when we rate it 1.3x
(and 1.6x) the BSP or longer. v10 holdout from 3 Jun, flat 1u, 8% commission, month by month: bets, winners, staked,
returned, P/L, ROI, plus drawdown and the longest losing run."""
import numpy as np, collections
z = np.load("ds/model_ds_v10.npz", allow_pickle=True)
ri = z["race_idx"]; nR = int(ri.max()) + 1; rdate = z["date"].astype(str); date = rdate[ri]
p10 = np.load("v10_profit_preds.npz")["p10"]; o = z["open"].astype(float); bs = z["bsp"].astype(float); won = z["finish"] == 1
okr = np.isfinite(o) & (o > 1) & np.isfinite(bs) & (bs > 1) & np.isfinite(p10) & (p10 > 0)
cnt = np.bincount(ri, minlength=nR)
race_ok = (np.bincount(ri, weights=okr.astype(float), minlength=nR) == cnt) & (rdate >= "2026-06-03") & (np.bincount(ri, weights=won.astype(float), minlength=nR) >= 1)
m = race_ok[ri]; s = np.bincount(ri, weights=np.where(m, p10, 0), minlength=nR); pm = np.where(m, p10 / np.where(s[ri] > 0, s[ri], 1), np.nan); ours = 1 / pm
minb = np.full(nR, np.inf)
for i in np.where(m)[0]: minb[ri[i]] = min(minb[ri[i]], bs[i])
fav = m & (bs <= minb[ri] + 1e-9)
for k in (1.3, 1.6):
    g = fav & (bs >= 4) & (bs < 7) & (ours >= k * bs); idx = np.where(g)[0]; idx = idx[np.argsort(date[idx], kind="stable")]
    ret = np.where(won[idx], 1 + (bs[idx] - 1) * 0.92, 0.0); pl = ret - 1
    print(f"\n=== favourite $4-$7, ours >= {k}x BSP, flat 1u at BSP: {len(idx)} bets, {won[idx].sum()} winners ({won[idx].mean():.0%} strike, BSP said {np.mean(1/bs[idx]):.0%}), median BSP ${np.median(bs[idx]):.2f}")
    print("| month | bets | won | staked | returned | P/L | ROI | at $100 | at $200 |\n|---|---|---|---|---|---|---|---|---|")
    mo = collections.OrderedDict()
    for j, i in enumerate(idx):
        a = mo.setdefault(date[i][:7], [0, 0, 0.0]); a[0] += 1; a[1] += int(won[i]); a[2] += ret[j]
    for mth, (n, w, r) in mo.items():
        print(f"| {mth} | {n} | {w} | {n}u | {r:.2f}u | {r-n:+.2f}u | {100*(r-n)/n:+.0f}% | ${100*(r-n):+,.0f} | ${200*(r-n):+,.0f} |")
    n = len(idx); r = ret.sum(); c = np.cumsum(pl); ddn = np.max(np.maximum.accumulate(c) - c)
    run = cur = 0
    for w_ in won[idx]: cur = 0 if w_ else cur + 1; run = max(run, cur)
    wk = len(set(rdate[race_ok])) / 7
    print(f"| TOTAL | {n} | {won[idx].sum()} | {n}u | {r:.2f}u | {r-n:+.2f}u | {100*(r-n)/n:+.0f}% | ${100*(r-n):+,.0f} | ${200*(r-n):+,.0f} |")
    print(f"worst drawdown {ddn:.1f}u (${100*ddn:,.0f} at $100), longest losing run {run} bets, {n/wk:.1f} bets a week, {(r-n)/wk:+.2f}u a week; a year at $100 about ${100*(r-n)/wk*52:+,.0f}, at $200 ${200*(r-n)/wk*52:+,.0f}")
