"""First starters, test 1: a heavier market weight for them (26 Oct 2026, founder: "then do it", after the first-starter
research). Clean holdout as t_month_bsp.py: v10 stage-1 trees trained before 3 Jun 2026 (p10), races from 3 Jun with an
open and a BSP on every runner, two date halves. The live blend is one weight for every runner (0.82 ours, 0.22 open).
Here the blend log q = a log p + b log open, renormalised, gets its own (a, b) for first starters; everyone else keeps
the weights fitted on all runners. Fitted on one half by winner log likelihood, scored on the other.
Reported: winner log loss and KL to BSP in races with a first starter and overall; the backed first starters' strike v
what each price gives them; the value-at-open plan in first-starter races (16c deduction), where the race rule bites.
python3.13 t_fs_weight.py"""
import numpy as np
z = np.load("ds/model_ds_v10.npz", allow_pickle=True)
ri = z["race_idx"]; nR = int(ri.max()) + 1; rdate = z["date"].astype(str); date = rdate[ri]
p10 = np.load("v10_profit_preds.npz")["p10"]; o = z["open"].astype(float); bs = z["bsp"].astype(float); won = z["finish"] == 1
cols = list(z["cols"]); fs = z["X"][:, cols.index("first_starter")] == 1
okr = np.isfinite(o) & (o > 1) & np.isfinite(bs) & (bs > 1) & np.isfinite(p10) & (p10 > 0)
cnt = np.bincount(ri, minlength=nR)
race_ok = (np.bincount(ri, weights=okr.astype(float), minlength=nR) == cnt) & (rdate >= "2026-06-03") & (np.bincount(ri, weights=won.astype(float), minlength=nR) >= 1)
m = race_ok[ri]
def norm(v, mask):
    s = np.bincount(ri, weights=np.where(mask, v, 0), minlength=nR); return np.where(mask, v / np.where(s[ri] > 0, s[ri], 1), np.nan)
pm = norm(p10, m); qo = norm(np.where(m, 1 / o, 0), m); qb = norm(np.where(m, 1 / bs, 0), m)
fsr = np.bincount(ri, weights=(fs & m).astype(float), minlength=nR) > 0   # races with a first starter
dates_h = sorted(set(rdate[race_ok])); cut = dates_h[len(dates_h) // 2]
H = [("early", date < cut), ("late", date >= cut)]
def blend(a, b, af=None, bf=None):
    A = np.where(fs & (af is not None), af if af is not None else a, a); B = np.where(fs & (bf is not None), bf if bf is not None else b, b)
    lq = np.where(m, A * np.log(np.maximum(pm, 1e-12)) + B * np.log(np.maximum(qo, 1e-12)), -np.inf)
    q = np.where(m, np.exp(lq), 0); s = np.bincount(ri, weights=q, minlength=nR); return np.where(m, q / np.where(s[ri] > 0, s[ri], 1), np.nan)
def ll(q, sel): g = sel & m & won; return -np.mean(np.log(np.maximum(q[g], 1e-12)))
def kl(q, rsel):
    g = m & rsel[ri]; v = np.bincount(ri, weights=np.where(g, qb * np.log(np.maximum(qb, 1e-12) / np.maximum(q, 1e-12)), 0), minlength=nR)
    return v[rsel & race_ok].mean()
grid_a = np.arange(0, 1.21, 0.05); grid_b = np.arange(0, 1.21, 0.05)
print(f"holdout {min(dates_h)} to {max(dates_h)}, split at {cut}; races {race_ok.sum()}, with a first starter {(fsr & race_ok).sum()}, first-starter runners {(fs & m).sum()}")
print("\n| test half | weights (ours, open) all / first starters | winner log loss, FS races: live / global fit / FS fit | KL to BSP, FS races: live / global / FS | KL all races: live / FS fit | open alone, FS races |\n|---|---|---|---|---|---|")
for h, hm in H:
    tr = ~hm
    best = min(((ll(blend(a, b), tr), a, b) for a in grid_a for b in grid_b), key=lambda x: x[0]); a0, b0 = best[1], best[2]
    bestf = min(((ll(blend(a0, b0, af, bf), tr & fsr[ri]), af, bf) for af in grid_a for bf in grid_b), key=lambda x: x[0]); af, bf = bestf[1], bestf[2]
    live = blend(0.82, 0.22); glob = blend(a0, b0); fsw = blend(a0, b0, af, bf); te = hm & fsr[ri]
    rs = np.zeros(nR, bool); rs[np.unique(ri[hm & m])] = True
    print(f"| {h} | {a0:.2f}, {b0:.2f} / {af:.2f}, {bf:.2f} | {ll(live, te):.4f} / {ll(glob, te):.4f} / {ll(fsw, te):.4f} | {kl(live, rs & fsr):.4f} / {kl(glob, rs & fsr):.4f} / {kl(fsw, rs & fsr):.4f} | {kl(live, rs):.4f} / {kl(fsw, rs):.4f} | {kl(qo, rs & fsr):.4f} |")
    bk = te & fs & (o <= 6)
    print(f"  backed first starters (open $6 or under), {h}: {bk.sum()} runners, won {won[bk].mean():.1%}; live gives {np.nanmean(live[bk]):.1%}, FS fit {np.nanmean(fsw[bk]):.1%}, open {np.nanmean(qo[bk]):.1%}, BSP {np.nanmean(qb[bk]):.1%}")
    for nm, q in (("live", live), ("FS fit", fsw)):
        ours = 1 / q; bet = hm & m & fsr[ri] & ~fs & (q * o >= 1.2) & (ours >= 1.6) & (ours <= 15) & (o < 3 * ours)
        bet_r = bet & ~np.isin(ri, ri[fs & m & (o <= 6)])   # the race rule
        for lab, b_ in (("all FS races", bet), ("race rule applied", bet_r)):
            pl = np.where(won, (o - 1) * 0.84, -1.0)[b_]; plb = np.where(won, (bs - 1) * 0.92, -1.0)[b_]
            print(f"  plan in FS races, {nm}, {lab}: {b_.sum()} bets, open {100*pl.mean():+.1f}%, BSP {100*plb.mean():+.1f}%")
