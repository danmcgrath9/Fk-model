"""How profitable is the live rule if we bet AFTER the market opens, at each point on the clock?
Joins fluc_after_open.py's CSV (archive average-price flucs) to the v10 holdout (3 Jun on).
Rule (current arm of t_cap.py, no drift multiplier): ours $1.60-$15, price < 3x ours, E 1.15 under $4 else 1.2,
min odds 0.95 x (E/p^0.82)^(1/0.78), steps x1/x1.25/x1.5 under the ceiling, stake_rule.stake (10u cap) on
p^0.82 t^-0.22. Price = the average corporate price at that time; 'best' = avg x final best/avg (all accounts).
Settled at that price (no deductions) and at BSP less 8%.
python3.13 t_after_open.py CSV"""
import sys, csv, numpy as np, stake_rule
z = np.load("ds/model_ds_v10.npz", allow_pickle=True)
ri = z["race_idx"]; nR = int(ri.max()) + 1; rid = z["race_id"]; hid = z["horse_id"]
p10 = np.load("v10_profit_preds.npz")["p10"].astype(float)
bs = z["bsp"].astype(float); won = z["finish"] == 1; rdate = z["date"]
okr = np.isfinite(bs) & (bs > 1) & np.isfinite(p10) & (p10 > 0)
cnt = np.bincount(ri, minlength=nR)
race_ok = (np.bincount(ri, weights=okr.astype(float), minlength=nR) == cnt) & (rdate >= "2026-06-03") & \
          (np.bincount(ri, weights=won.astype(float), minlength=nR) >= 1)
m = race_ok[ri]
s = np.bincount(ri, weights=np.where(m, p10, 0), minlength=nR); pm = np.where(m, p10 / np.where(s[ri] > 0, s[ri], 1), np.nan)
key = {(rid[ri[i]], hid[i]): i for i in range(len(ri))}
COLS = ["open", "a15m", "a1h", "a3h", "a6h", "a12h", "am930", "b1h", "last"]
P = {c: np.full(len(ri), np.nan) for c in COLS}; B = np.full(len(ri), np.nan)
lines = open(sys.argv[1]).read().split("CSV-BEGIN")[1].split("CSV-END")[0].strip().splitlines()
hit = 0
for row in csv.DictReader(lines):
    i = key.get((row["race_id"], row["horse_id"]))
    if i is None: continue
    hit += 1
    for c in COLS:
        if row[c]: P[c][i] = float(row[c])
    if row["best_over_avg"]: B[i] = float(row["best_over_avg"])
print(f"csv runners matched to the holdout dataset: {hit}; holdout runners in complete races: {m.sum()}")
B = np.where(np.isfinite(B) & (B >= 1), B, 1.0)
# only races where every runner has a price at the open (the same race set at every time)
have = np.bincount(ri, weights=(m & np.isfinite(P["open"])).astype(float), minlength=nR) == cnt
use = m & have[ri]
print(f"races used: {len(np.unique(ri[use]))}, {use.sum()} runners, {min(rdate[np.unique(ri[use])])} to {max(rdate[np.unique(ri[use])])}")
TIERS = (1.0, 1.25, 1.5)
def run(px, settle):
    st = po = pb = 0.0; n = w = 0; days = {}
    for i in np.where(use & np.isfinite(px) & (px > 1))[0]:
        p = pm[i]; q = 1 / p; t0 = px[i]
        if not (1.6 <= q <= 15) or t0 >= 3 * q: continue
        E = 1.15 if t0 < 4 else 1.2
        mo = 0.95 * (E / p ** 0.82) ** (1 / 0.78)
        if t0 < mo: continue
        ts = [mo * k for k in TIERS if mo * k < 3 * q]; tot = prev = 0.0
        for k, t in enumerate(ts):
            tp = ts[k + 1] if k + 1 < len(ts) else t
            s_ = stake_rule.stake(p ** 0.82 * tp ** -0.22, tp); add = max(0.0, s_ - prev); prev = max(prev, s_)
            if t0 >= t: tot += add
        if tot <= 0: continue
        n += 1; st += tot; w += won[i]
        a = tot * (settle[i] - 1) if won[i] else -tot; po += a
        pb += tot * (bs[i] - 1) * 0.92 if won[i] else -tot
        d = rdate[ri[i]]; days[d] = days.get(d, 0) + a
    c = np.cumsum([days[d] for d in sorted(days)]); dd = (np.maximum.accumulate(c) - c).max() if len(c) else 0
    return n, w, st, po, pb, dd
LBL = {"open": "At the open", "a15m": "15 min after open", "a1h": "1 hour after", "a3h": "3 hours after",
       "a6h": "6 hours after", "a12h": "12 hours after", "am930": "9:30am race day", "b1h": "1 hour before the jump",
       "last": "Last price"}
print("\n| when | bets | winners | staked | profit at avg price | ROI | profit at best of accounts | ROI | same bets at BSP | ROI | worst drawdown (avg) |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for c in COLS:
    px = P[c]
    # a time past the jump has no price: use the last price before it (the CSV leaves it blank) -> carry forward
    if c not in ("open",):
        px = np.where(np.isfinite(px), px, np.nan)
    n, w, st, po, pb, dd = run(px, px)
    _, _, _, pob, _, _ = run(px, px * B)
    print(f"| {LBL[c]} | {n} | {int(w)} | {st:.0f}u | {po:+.0f}u | {po/st:+.1%} | {pob:+.0f}u | {pob/st:+.1%} | {pb:+.0f}u | {pb/st:+.1%} | {dd:.0f}u |")
# also: best-of-accounts price used to DECIDE as well as settle
print("\nDeciding AND settling at the best-of-accounts price:\n\n| when | bets | staked | profit | ROI | at BSP | ROI |\n|---|---|---|---|---|---|---|")
for c in COLS:
    px = P[c] * B
    n, w, st, po, pb, dd = run(px, px)
    print(f"| {LBL[c]} | {n} | {st:.0f}u | {po:+.0f}u | {po/st:+.1%} | {pb:+.0f}u | {pb/st:+.1%} |")
print(f"\nmedian best/avg on the final snapshot: {np.median(B[use]):.3f}; mean {np.mean(B[use]):.3f}")
