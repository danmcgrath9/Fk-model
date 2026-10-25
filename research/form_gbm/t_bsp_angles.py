"""More betting angles around BSP (25 Oct 2026, founder: "back test and find some more betting angles around BSP").
Same clean holdout as t_lay_halves.py: v10 stage-1 trees trained before 3 Jun 2026 (p10), races from 3 Jun with an open
and a BSP on every runner, split into two date halves; an angle counts only if it holds in both. 8% commission on
Betfair winnings, 16c scratching deduction on a bet at the open.
A. Back at the open, lay the same horse at BSP for a level profit (CLV turned into cash).
B. Lay at BSP by how we rate the horse against BSP, all prices.
C. Lay at BSP on market drift alone (BSP/open), no model.
D. Our drifted-roughie lay ($15-$30, rated 1.6x+), split by whether it actually drifted from the open.
E. Back at BSP the value bets the drift model forecasts to firm most.
python3.13 t_bsp_angles.py"""
import numpy as np
z = np.load("ds/model_ds_v10.npz", allow_pickle=True)
ri = z["race_idx"]; nR = int(ri.max()) + 1; rdate = z["date"].astype(str); date = rdate[ri]
p10 = np.load("v10_profit_preds.npz")["p10"]; o = z["open"].astype(float); bs = z["bsp"].astype(float); won = z["finish"] == 1
okr = np.isfinite(o) & (o > 1) & np.isfinite(bs) & (bs > 1) & np.isfinite(p10) & (p10 > 0)
cnt = np.bincount(ri, minlength=nR)
race_ok = (np.bincount(ri, weights=okr.astype(float), minlength=nR) == cnt) & (rdate >= "2026-06-03") & (np.bincount(ri, weights=won.astype(float), minlength=nR) >= 1)
m = race_ok[ri]
def norm(v, mask):
    s = np.bincount(ri, weights=np.where(mask, v, 0), minlength=nR); return np.where(mask, v / np.where(s[ri] > 0, s[ri], 1), np.nan)
pm = norm(p10, m); qb = norm(np.where(m, 1 / bs, 0), m); qo = norm(np.where(m, 1 / o, 0), m); ratio = pm / qb; ours = 1 / pm
COMM, DED = 0.08, 0.16
dates_h = sorted(set(rdate[race_ok])); cut = dates_h[len(dates_h) // 2]
halves = (("early", m & (date < cut)), ("late", m & (date >= cut)))
plan = m & (pm * o >= 1.2) & (ours >= 1.6) & (ours <= 15) & (o < 3 * ours)
lay_pl = lambda g: np.where(won[g], -(bs[g] - 1), 1 - COMM)          # lay 1u at BSP
back_bsp = lambda g: np.where(won[g], (bs[g] - 1) * (1 - COMM), -1.0)  # back 1u at BSP
back_open = lambda g: np.where(won[g], (o[g] - 1) * (1 - DED), -1.0)   # back 1u at the open
def row(name, g):
    out = [name]
    for h, hm in halves:
        s = g & hm; n = s.sum()
        out.append(f"{n} / {won[s].sum()} / {won[s].sum()/max(qb[s].sum(),1e-9):.2f} / {100*lay_pl(s).mean():+.0f}% / {100*back_bsp(s).mean():+.0f}%" if n else "-")
    print("| " + " | ".join(out) + " |")
HEAD = "| angle | early: runners / wins / A/E / lay ROI / back ROI | late: same |\n|---|---|---|"

# A. back at the open, lay at BSP: lay stake L = O_eff / (B - comm) makes the result the same either way
print("## A. Back 1u at the open, lay at BSP for a level result (plan bets)")
print("| half | bets | profit per bet, hedged | share of bets locking a profit | compare: open only | BSP only |\n|---|---|---|---|---|---|")
for h, hm in halves:
    s = plan & hm; oe = 1 + (o[s] - 1) * (1 - DED); L = oe / (bs[s] - COMM)
    hedged = -1 + L * (1 - COMM)    # lose: -1 + L(1-c); win: oe - 1 - L(bs-1) = the same by construction
    print(f"| {h} | {s.sum()} | {100*hedged.mean():+.1f}% | {(hedged > 0).mean():.0%} | {100*back_open(s).mean():+.0f}% | {100*back_bsp(s).mean():+.0f}% |")
print("(hedge needs the horse matched at BSP for the lay; a scratched runner is a refund on both sides)\n")

print("## B. Lay at BSP by our chance / BSP chance, all prices\n" + HEAD)
for lo_, hi_ in ((0, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0), (1.0, 1.25), (1.25, 1.6), (1.6, 99)):
    row(f"ours/BSP {lo_}-{hi_}", m & (ratio >= lo_) & (ratio < hi_))
print("\nours/BSP under 0.6, by BSP price\n" + HEAD)
for lo_, hi_ in ((1, 2.5), (2.5, 4), (4, 8), (8, 15), (15, 30), (30, 1000)):
    row(f"${lo_}-${hi_}", m & (ratio < 0.6) & (bs >= lo_) & (bs < hi_))
print("\nours/BSP under 0.8, by BSP price\n" + HEAD)
for lo_, hi_ in ((1, 2.5), (2.5, 4), (4, 8), (8, 15), (15, 30), (30, 1000)):
    row(f"${lo_}-${hi_}", m & (ratio < 0.8) & (bs >= lo_) & (bs < hi_))

drift = qo / qb   # >1 = drifted (BSP chance below opening chance)
print("\n## C. Lay at BSP on market drift alone (opening chance / BSP chance), no model\n" + HEAD)
for lo_, hi_ in ((0, 0.67), (0.67, 0.8), (0.8, 1.0), (1.0, 1.25), (1.25, 1.5), (1.5, 2), (2, 99)):
    row(f"drift {lo_}-{hi_}", m & (drift >= lo_) & (drift < hi_))
print("\ndrifted 1.5x+, by BSP price\n" + HEAD)
for lo_, hi_ in ((1, 4), (4, 8), (8, 15), (15, 30), (30, 1000)):
    row(f"${lo_}-${hi_}", m & (drift >= 1.5) & (bs >= lo_) & (bs < hi_))

print("\n## D. The roughie lay ($15-$30 at BSP, ours/BSP 1.6+), by what the market did from the open\n" + HEAD)
base = m & (ratio >= 1.6) & (bs >= 15) & (bs < 30)
row("all", base); row("drifted 1.25x+", base & (drift >= 1.25)); row("drifted 1.5x+", base & (drift >= 1.5)); row("held or firmed", base & (drift < 1.25))
row("and we had it as a plan bet at the open", base & plan); row("and NOT a plan bet", base & ~plan)
print("\nsame rule at other prices, ours/BSP 1.6+\n" + HEAD)
for lo_, hi_ in ((8, 12), (12, 15), (15, 20), (20, 30), (30, 50)):
    row(f"${lo_}-${hi_}", m & (ratio >= 1.6) & (bs >= lo_) & (bs < hi_))
print("\nours/BSP 2.0+ instead\n" + HEAD)
for lo_, hi_ in ((8, 15), (15, 30), (30, 50)):
    row(f"${lo_}-${hi_}", m & (ratio >= 2.0) & (bs >= lo_) & (bs < hi_))

# E. drift forecast: gb = predicted log(BSP chance / opening chance) with our price, cross-fitted by half
d = np.load("drift_gbm_preds_v10.npz"); gb = np.full(len(ri), np.nan); gb[d["idx"]] = d["gb"]
print("\n## E. Back at BSP: plan bets by the drift model's forecast (thirds within each half)")
print("| half | third | bets | strike | back at BSP | back at the open | lay at BSP |\n|---|---|---|---|---|---|---|")
for h, hm in halves:
    s0 = plan & hm & np.isfinite(gb); q = np.quantile(gb[s0], [1/3, 2/3])
    for lab, sel in (("forecast to drift", gb < q[0]), ("middle", (gb >= q[0]) & (gb < q[1])), ("forecast to firm", gb >= q[1])):
        s = s0 & sel
        print(f"| {h} | {lab} | {s.sum()} | {won[s].mean():.0%} | {100*back_bsp(s).mean():+.0f}% | {100*back_open(s).mean():+.0f}% | {100*lay_pl(s).mean():+.0f}% |")
print("\nnon-plan runners forecast to drift most (bottom tenth of gb), lay at BSP, by price\n" + HEAD)
for h, hm in halves: pass
g_all = m & np.isfinite(gb); qlo = np.quantile(gb[g_all], 0.1)
for lo_, hi_ in ((1, 4), (4, 8), (8, 15), (15, 30), (30, 1000)):
    row(f"${lo_}-${hi_}", g_all & (gb < qlo) & (bs >= lo_) & (bs < hi_))
