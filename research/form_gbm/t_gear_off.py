"""Gear stripped off a forward horse from a wide draw: going back, lack of intent? (19 Oct 2026, founder on Prestige
Fantastic, Echuca R1: "blinkers off, visors off, tongue tie off. Drawn wide, they were always going back, shows lack of
intent, where did we have it mapped" - we had it mapped to lead (speed map position 1), from barrier 15.)

Segments by gear coming OFF today (gd_n_off: blinkers, tongue tie, visors, winkers... removed), Form King's speed-map
position (sm_predicted_position) and barrier. Measured as actual winners against expected: by the opening price and BSP
(every race with both, the whole dataset) and by our model (v10 stage 1, holdout from 3 Jun only, out of sample), and
the value-at-open bets in each segment (holdout, live rule on the blend, 16c deduction).   python3.13 t_gear_off.py"""
import numpy as np, bench as b
D = b.load("ds/model_ds_v10.npz")
P = np.load("v10_profit_preds.npz"); p10 = P["p10"]; hold = P["hold"]
ri = D["race_idx"]; nR = D["n_races"]; cols = [str(c) for c in D["cols"]]; X = D["X"]; g = lambda n: X[:, cols.index(n)]
op = np.asarray(D["open"], float); bs = np.asarray(D["bsp"], float); won = np.asarray(D["finish"], float) == 1
okp = lambda x: np.isfinite(x) & (x > 1)
cnt = np.bincount(ri, minlength=nR); full = (np.bincount(ri, weights=(okp(op) & okp(bs)).astype(float), minlength=nR) == cnt)[ri]
def norm(v, m):
    s = np.bincount(ri, weights=np.where(m, v, 0), minlength=nR); return np.where(m, v / np.where(s[ri] > 0, s[ri], 1), np.nan)
qo = norm(1 / np.where(okp(op), op, 2), full); qb = norm(1 / np.where(okp(bs), bs, 2), full)
pm = norm(np.where(hold, p10, 0), hold & full)
off = np.nan_to_num(g("gd_n_off")); smp = g("sm_predicted_position"); bar = g("barrier"); fld = cnt[ri]
fwd = np.nan_to_num(smp, nan=99) <= 3; wide = (np.nan_to_num(bar) >= 10) | (np.nan_to_num(bar) >= 0.75 * fld)
segs = [("all runners", np.ones(len(ri), bool)), ("gear off today: none", off == 0), ("gear off: 1 item", off == 1),
        ("gear off: 2+ items", off >= 2), ("2+ off, mapped top 3", (off >= 2) & fwd), ("2+ off, drawn wide", (off >= 2) & wide),
        ("2+ off, mapped top 3, drawn wide", (off >= 2) & fwd & wide), ("1+ off, mapped top 3, drawn wide", (off >= 1) & fwd & wide),
        ("no gear off, mapped top 3, drawn wide", (off == 0) & fwd & wide), ("blinkers off", np.nan_to_num(g("gd_blinkers_off")) > 0),
        ("tongue tie off", np.nan_to_num(g("gd_tongue_off")) > 0)]
print("| segment | runners (all) | wins | actual / open | actual / BSP | holdout runners | actual / our model |\n|---|---|---|---|---|---|---|")
for lab, s in segs:
    a = s & full; h = s & hold & full
    print(f"| {lab} | {a.sum()} | {won[a].sum()} | {won[a].sum() / qo[a].sum():.2f} | {won[a].sum() / qb[a].sum():.2f} | {h.sum()} | "
          f"{(won[h].sum() / pm[h].sum()) if h.sum() else float('nan'):.2f} |")
# value-at-open bets in the holdout, as the live rule takes them
bl = norm(np.exp(0.82 * np.log(np.where(hold & full, np.maximum(pm, 1e-9), 1)) + 0.22 * np.log(np.where(full, qo, 1))), hold & full)
val = hold & full & (bl * op >= 1.2) & (1 / bl >= 1.6) & (1 / bl <= 15) & (op < 3 / bl)
ret = np.where(won, 1 + (op - 1) * 0.84, 0) - 1
print("\n| value-at-open bets (holdout) | bets | wins | flat at the open, 16c deduction | flat at BSP |\n|---|---|---|---|---|")
for lab, s in segs:
    t = val & s
    if t.sum() >= 5 or lab == "all runners":
        print(f"| {lab} | {t.sum()} | {won[t].sum()} | {ret[t].mean():+.0%} | {(np.where(won, bs, 0) - 1)[t].mean():+.0%} |")
