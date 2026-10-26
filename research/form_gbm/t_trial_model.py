"""Does adding the trial findings to the model help? (27 Oct 2026, founder: "test it with what you found in 1, the model
and see if it's better"). A correction layer on top of the live v10 price, cross-fitted by halves of the holdout
(fit on one half, score the other): chance = softmax(a x log p10 + b . f) per race, where f is zero unless the horse's
most recent past run is a trial (it trialled this prep): won the trial, placed 2nd-3rd, trial 21+ days back, the trial
jockey's win rate (pre-holdout, 50+ rides; unrated flag). Scored on log loss, then on the open bets (live rule).
python3.13 t_trial_model.py"""
import numpy as np, collections, stake_rule
from scipy.optimize import minimize
z = np.load("ds/model_ds_v10.npz", allow_pickle=True)
ri = z["race_idx"]; nR = int(ri.max()) + 1; rdate = z["date"].astype(str); date = rdate[ri]
p10 = np.load("v10_profit_preds.npz")["p10"]; o = z["open"].astype(float); bs = z["bsp"].astype(float); won = z["finish"] == 1
okr = np.isfinite(o) & (o > 1) & np.isfinite(bs) & (bs > 1) & np.isfinite(p10) & (p10 > 0)
cnt = np.bincount(ri, minlength=nR)
race_ok = (np.bincount(ri, weights=okr.astype(float), minlength=nR) == cnt) & (rdate >= "2026-06-03") & (np.bincount(ri, weights=won.astype(float), minlength=nR) == 1)
m = race_ok[ri]
def nrm(v): s = np.bincount(ri, weights=np.where(m, v, 0), minlength=nR); return np.where(m, v / np.where(s[ri] > 0, s[ri], 1), np.nan)
pm = nrm(np.where(m, p10, 0))
jk = z["jockey"].astype(str); pre = date < "2026-06-03"
rides = collections.Counter(jk[pre].tolist()); wins = collections.Counter(jk[pre & won].tolist())
rate = {j: wins[j] / n for j, n in rides.items() if n >= 50 and j.strip()}
mean_rate = np.mean(list(rate.values()))
P = z["P"]; pf = [str(x) for x in z["past_fields"]]; PJ = z["past_jockeys"].astype(str); prid = z["past_race_ids"]
trial0 = (prid[:, 0] != "") & (P[:, 0, pf.index("trial")] == 1)
fin = P[:, 0, pf.index("finish")]; days = P[:, 0, pf.index("days_before")]
jr = np.array([rate.get(j.strip(), np.nan) for j in PJ[:, 0]])
F = np.column_stack([
    trial0 & (fin == 1), trial0 & (fin >= 2) & (fin <= 3), trial0 & (days > 21),
    np.where(trial0 & np.isfinite(jr), (jr - mean_rate) * 10, 0.0), trial0 & ~np.isfinite(jr)]).astype(float)
NAMES = ["won trial", "placed 2nd-3rd", "trial 21+ days back", "trial jockey win rate (per 10 pts)", "trial jockey unrated"]
print(f"runners in complete holdout races: {m.sum()}; whose latest past run is a trial: {(m & trial0).sum()}")
cut = sorted(set(rdate[race_ok]))[len(set(rdate[race_ok])) // 2]
H = [(m & (date < cut)), (m & (date >= cut))]
lp = np.log(np.where(m, pm, 1))
def chance(theta, mask):
    v = theta[0] * lp + F @ theta[1:]
    v = np.where(mask, v, -np.inf); mx = np.full(nR, -np.inf); np.maximum.at(mx, ri, v)
    e = np.where(mask, np.exp(v - mx[ri]), 0); return e / np.where(np.bincount(ri, weights=e, minlength=nR)[ri] > 0, np.bincount(ri, weights=e, minlength=nR)[ri], 1)
def nll(theta, mask):
    c = chance(theta, mask); g = mask & won; return -np.log(np.maximum(c[g], 1e-12)).sum() / g.sum()
adj = np.full(len(ri), np.nan); th = []
for k in (0, 1):
    tr, te = H[k], H[1 - k]
    res = minimize(nll, np.r_[1.0, np.zeros(F.shape[1])], args=(tr,), method="L-BFGS-B")
    th.append(res.x); c = chance(res.x, te); adj[te] = c[te]
    print(f"\nfit on half {k+1}: ours x{res.x[0]:.2f}; " + "; ".join(f"{n} {b:+.2f}" for n, b in zip(NAMES, res.x[1:])))
    print(f"  scored on half {2-k}: log loss live {nll(np.r_[1.0, np.zeros(F.shape[1])], te):.4f} -> with trials {nll(res.x, te):.4f}")
# betting: the live open rule with each price
TIERS = (1.0, 1.25, 1.5)
def openbets(p):
    st = np.zeros(len(ri))
    for i in np.where(m)[0]:
        pp = p[i]; q = 1 / pp; t0 = o[i]
        if not (1.6 <= q <= 15) or t0 >= 3 * q: continue
        E = 1.15 if t0 < 4 else 1.2; mo = 0.95 * (E / pp ** 0.82) ** (1 / 0.78)
        if t0 < mo: continue
        ts = [mo * kk for kk in TIERS if mo * kk < 3 * q]; tot = prev = 0.0
        for kk, t in enumerate(ts):
            tp = ts[kk + 1] if kk + 1 < len(ts) else t
            s_ = stake_rule.stake(pp ** 0.82 * tp ** -0.22, tp); add = max(0.0, s_ - prev); prev = max(prev, s_)
            if t0 >= t: tot += add
        st[i] = tot
    return st
print("\n| price | half | bets | staked | beat BSP | price/BSP | P/L at open less 16c | at BSP |\n|---|---|---|---|---|---|---|---|")
for lab, p in (("live v10", pm), ("v10 + trial correction", adj)):
    st = openbets(p)
    for k, h in enumerate(H):
        g = h & (st > 0); s = st[g]
        pl = np.where(won[g], s * (o[g] - 1) * 0.84, -s).sum(); pb = np.where(won[g], s * (bs[g] - 1) * 0.92, -s).sum()
        print(f"| {lab} | {k+1} | {g.sum()} | {s.sum():.0f}u | {(o[g] > bs[g]).mean():.0%} | {np.sum(s*o[g]/bs[g])/s.sum():.2f} | {pl:+.0f}u ({pl/s.sum():+.0%}) | {pb/s.sum():+.0%} |")
# where the bets changed
st0 = openbets(pm); st1 = openbets(adj)
for lab, g in (("bets the correction ADDS", (st1 > 0) & (st0 == 0)), ("bets the correction DROPS", (st0 > 0) & (st1 == 0))):
    s = np.where(st1 > 0, st1, st0)[g]
    pl = np.where(won[g], s * (o[g] - 1) * 0.84, -s).sum()
    print(f"\n{lab}: {g.sum()}, winners {won[g].sum()}, P/L {pl:+.0f}u, price/BSP {np.sum(s*o[g]/bs[g])/max(s.sum(),1e-9):.2f}")
