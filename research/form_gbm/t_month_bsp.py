"""Edge stability and the Betfair side (23 Oct 2026). Clean holdout: v10 stage-1 trees trained before 3 Jun 2026
(v10_profit_preds.npz p10), scored on every race from 3 Jun with an open and a BSP on every runner.
1. Month by month: the plan's bets (value 20c+ at the open, ours $1.60-$15, open under 3x ours, flat 1u) settled at
   the opening price (16c deduction) and at BSP (8% commission), CLV, and the model's KL to BSP against the open's.
2. Betfair side: fit log-odds(win) = a + b log q_bsp + c log(ours/bsp) on one half of the holdout, test on the other;
   back / lay at BSP by the ratio ours/BSP; A/E (wins / expected) per bucket.
python t_month_bsp.py"""
import numpy as np, collections
z = np.load("ds/model_ds_v10.npz", allow_pickle=True)
ri = z["race_idx"]; nR = int(ri.max()) + 1; rdate = z["date"].astype(str); date = rdate[ri]
p10 = np.load("v10_profit_preds.npz")["p10"]; o = z["open"].astype(float); bs = z["bsp"].astype(float); won = z["finish"] == 1
okr = np.isfinite(o) & (o > 1) & np.isfinite(bs) & (bs > 1) & np.isfinite(p10) & (p10 > 0)
cnt = np.bincount(ri, minlength=nR)
race_ok = (np.bincount(ri, weights=okr.astype(float), minlength=nR) == cnt) & (rdate >= "2026-06-03") & (np.bincount(ri, weights=won.astype(float), minlength=nR) >= 1)
m = race_ok[ri]
def norm(v, mask):
    s = np.bincount(ri, weights=np.where(mask, v, 0), minlength=nR); return np.where(mask, v / np.where(s[ri] > 0, s[ri], 1), np.nan)
pm = norm(p10, m); qb = norm(np.where(m, 1 / bs, 0), m); qo = norm(np.where(m, 1 / o, 0), m)
ours = 1 / pm
print(f"holdout: {race_ok.sum()} races, {m.sum()} runners, {len(set(rdate[race_ok]))} days, {min(rdate[race_ok])} to {max(rdate[race_ok])}")

# ---- 1. month by month
bet = m & (pm * o >= 1.2) & (ours >= 1.6) & (ours <= 15) & (o < 3 * ours)
DED, COMM = 0.16, 0.08
pl_open = np.where(won, (o - 1) * (1 - DED), -1.0); pl_bsp = np.where(won, (bs - 1) * (1 - COMM), -1.0)
def kl(q, p): return np.bincount(ri, weights=np.where(m, q * np.log(np.maximum(q, 1e-9) / np.maximum(p, 1e-9)), 0), minlength=nR)
klm = kl(qb, pm); klo = kl(qb, qo)
print("\n## Month by month (flat 1u a bet)\n| month | races | KL model | KL open | bets | won | ROI open (16c ded) | ROI at BSP (8% comm) | beat BSP | median open/BSP |\n|---|---|---|---|---|---|---|---|---|---|")
months = sorted(set(d[:7] for d in rdate[race_ok]))
T = collections.defaultdict(float)
for mo in months + ["all"]:
    rm = race_ok & np.array([d[:7] == mo or mo == "all" for d in rdate])
    b_ = bet & rm[ri]; n = b_.sum()
    if n == 0: continue
    r = f"| {mo} | {rm.sum()} | {klm[rm].mean():.4f} | {klo[rm].mean():.4f} | {n} | {won[b_].sum()} | {100*pl_open[b_].mean():+.1f}% | {100*pl_bsp[b_].mean():+.1f}% | {100*np.mean(o[b_] > bs[b_]):.0f}% | {np.median(o[b_]/bs[b_]):.2f} |"
    print(r)

# ---- 2. the Betfair side
print("\n## Betfair side: does the model add anything to BSP?")
dates_h = sorted(set(rdate[race_ok])); cut = dates_h[len(dates_h) // 2]
half = (date >= cut)
lo_q, lo_r = np.log(qb), np.log(pm / qb)
def fit(mask):
    Xd = np.column_stack([np.ones(mask.sum()), lo_q[mask], lo_r[mask]]); y = won[mask].astype(float); w = np.zeros(3)
    for _ in range(200):  # Newton on the logistic
        pr = 1 / (1 + np.exp(-Xd @ w)); g = Xd.T @ (y - pr); H = (Xd * (pr * (1 - pr))[:, None]).T @ Xd + 1e-6 * np.eye(3); w += np.linalg.solve(H, g)
    return w
def ll(p, mask): return -np.mean(np.log(np.where(won[mask], p[mask], 1 - p[mask])))
for name, fit_m, test_m in (("fit early, test late", m & ~half, m & half), ("fit late, test early", m & half, m & ~half)):
    w = fit(fit_m); pbl = 1 / (1 + np.exp(-(w[0] + w[1] * lo_q + w[2] * lo_r)))
    print(f"- {name}: coefficients const {w[0]:+.3f}, log BSP chance {w[1]:+.3f}, log(ours/BSP) {w[2]:+.3f}; winner log loss on the test half: BSP {ll(qb, test_m):.4f}, blend {ll(pbl, test_m):.4f}, ours alone {ll(pm, test_m):.4f}")
print("\n| ours / BSP (chance) | runners | wins | expected at BSP | A/E | flat 1u BACK at BSP, 8% comm | flat 1u LAY at BSP, 8% comm on wins |\n|---|---|---|---|---|---|---|")
ratio = pm / qb
edges = [0, 0.4, 0.6, 0.8, 1.0, 1.25, 1.6, 2.0, 99]
for lo_, hi_ in zip(edges[:-1], edges[1:]):
    g = m & (ratio >= lo_) & (ratio < hi_); n = g.sum()
    if n == 0: continue
    exp = qb[g].sum(); w_ = won[g].sum()
    back = np.where(won[g], (bs[g] - 1) * (1 - COMM), -1.0).mean()
    lay = np.where(won[g], -(bs[g] - 1), 1.0 * (1 - COMM)).mean()  # lay 1u: win the stake less commission, lose (price-1)
    print(f"| {lo_:.2f} to {hi_:.2f} | {n} | {w_} | {exp:.1f} | {w_/exp:.2f} | {100*back:+.1f}% | {100*lay:+.1f}% |")
