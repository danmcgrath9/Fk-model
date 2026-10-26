"""What our losing bets and big drifters have in common (27 Oct 2026, founder: "if we look at our losing bets / big
drifters, what they have in common?"). Open bets under the live rule on the v10 holdout (3 Jun-13 Oct): ours $1.60-$15,
open under 3x ours, edge 1.15 under $4 else 1.2, min odds 0.95 x (E/p^0.82)^(1/0.78), stake_rule sizing.
Drift = BSP / open. python3.13 t_drifters.py"""
import numpy as np, collections, stake_rule
z = np.load("ds/model_ds_v10.npz", allow_pickle=True)
ri = z["race_idx"]; nR = int(ri.max()) + 1; rdate = z["date"].astype(str); date = rdate[ri]
p10 = np.load("v10_profit_preds.npz")["p10"]; o = z["open"].astype(float); bs = z["bsp"].astype(float); won = z["finish"] == 1
okr = np.isfinite(o) & (o > 1) & np.isfinite(bs) & (bs > 1) & np.isfinite(p10) & (p10 > 0)
cnt = np.bincount(ri, minlength=nR)
race_ok = (np.bincount(ri, weights=okr.astype(float), minlength=nR) == cnt) & (rdate >= "2026-06-03") & (np.bincount(ri, weights=won.astype(float), minlength=nR) >= 1)
m = race_ok[ri]
s = np.bincount(ri, weights=np.where(m, p10, 0), minlength=nR); pm = np.where(m, p10 / np.where(s[ri] > 0, s[ri], 1), np.nan)
qb = np.where(m, (1 / bs) / np.bincount(ri, weights=np.where(m, 1 / bs, 0), minlength=nR)[ri], np.nan)
qo = np.where(m, (1 / o) / np.bincount(ri, weights=np.where(m, 1 / o, 0), minlength=nR)[ri], np.nan)
TIERS = (1.0, 1.25, 1.5)
stake = np.zeros(len(ri))
for i in np.where(m)[0]:
    p = pm[i]; q = 1 / p; t0 = o[i]
    if not (1.6 <= q <= 15) or t0 >= 3 * q: continue
    E = 1.15 if t0 < 4 else 1.2; mo = 0.95 * (E / p ** 0.82) ** (1 / 0.78)
    if t0 < mo: continue
    ts = [mo * k for k in TIERS if mo * k < 3 * q]; tot = prev = 0.0
    for k, t in enumerate(ts):
        tp = ts[k + 1] if k + 1 < len(ts) else t
        s_ = stake_rule.stake(p ** 0.82 * tp ** -0.22, tp); add = max(0.0, s_ - prev); prev = max(prev, s_)
        if t0 >= t: tot += add
    stake[i] = tot
B = np.where(stake > 0)[0]
drift = bs[B] / o[B]; w = won[B]; st = stake[B]
pl = np.where(w, st * (o[B] - 1) * 0.84, -st)
print(f"open bets {len(B)}, winners {w.sum()}, staked {st.sum():.0f}u, P/L at open less 16c {pl.sum():+.0f}u ({pl.sum()/st.sum():+.0%})")
print("\n## 1. By what the market did from the open to BSP\n")
print("| BSP / open | bets | share | winners | win rate | expected at BSP | A/E vs BSP | P/L at the open | ROI |\n|---|---|---|---|---|---|---|---|---|")
G = [(0, 0.6, "firmed 40%+"), (0.6, 0.8, "firmed 20-40%"), (0.8, 1.0, "firmed up to 20%"), (1.0, 1.25, "drifted up to 25%"), (1.25, 1.6, "drifted 25-60%"), (1.6, 99, "drifted 60%+")]
for lo, hi, lab in G:
    g = (drift >= lo) & (drift < hi)
    print(f"| {lab} | {g.sum()} | {g.mean():.0%} | {w[g].sum()} | {w[g].mean():.0%} | {qb[B][g].sum():.1f} | {w[g].sum()/qb[B][g].sum():.2f} | {pl[g].sum():+.0f}u | {pl[g].sum()/st[g].sum():+.0%} |")
# features
cols = [str(c) for c in z["cols"]]; X = z["X"][B].astype(float)
big = drift >= 1.25; firm = drift < 0.8
def col(n): return X[:, cols.index(n)]
extra = {
    "our price": 1 / pm[B], "open price": o[B], "overlay (open x our chance)": o[B] * pm[B], "field size": cnt[ri[B]].astype(float),
    "race number": z["race_number"][ri[B]].astype(float), "distance": z["distance"][ri[B]].astype(float),
    "market % at open": (1 / o[B]) / qo[B] * 100 if True else None,
}
rows = []
for n, v in list(extra.items()) + [(c, col(c)) for c in cols]:
    a, b2 = v[big], v[firm]
    a = a[np.isfinite(a)]; b2 = b2[np.isfinite(b2)]
    if len(a) < 30 or len(b2) < 30: continue
    sd = np.nanstd(np.concatenate([a, b2]))
    if not sd: continue
    rows.append(((a.mean() - b2.mean()) / sd, n, a.mean(), b2.mean(), np.isfinite(v).mean()))
rows.sort(key=lambda r: -abs(r[0]))
print(f"\n## 2. Big drifters (BSP 25%+ over the open, {big.sum()}) against firmers (BSP 20%+ under, {firm.sum()}): biggest differences\n")
print("| feature | drifters | firmers | gap (in SDs) |\n|---|---|---|---|")
for d_, n, a, b2, cov in rows[:30]:
    print(f"| {n} | {a:.3g} | {b2:.3g} | {d_:+.2f} |")
# simple binaries
def rate(mask, lab):
    print(f"| {lab} | {mask[big].mean():.0%} | {mask[firm].mean():.0%} | {mask[~big & ~firm].mean():.0%} | {(w[mask].sum()/max(qb[B][mask].sum(),1e-9)):.2f} | {pl[mask].sum()/max(st[mask].sum(),1e-9):+.0%} ({mask.sum()} bets) |")
print("\n## 3. Plain flags\n\n| flag | share of big drifters | share of firmers | share of the rest | A/E vs BSP when flagged | ROI when flagged |\n|---|---|---|---|---|---|")
fu = col("raw_first_up") == 1 if "raw_first_up" in cols else np.zeros(len(B), bool)
rate(fu, "first up")
rate(col("daysSinceLastRace") > 60, "60+ days since last run")
rate(col("raceInPrep") == 2, "second up")
rate(col("gear_changes") > 0, "gear change")
rate(col("blinkers_first") == 1, "blinkers first time")
rate(col("apprenticeJockey") == 1 if "apprenticeJockey" in cols else np.zeros(len(B), bool), "apprentice")
rate(col("raw_barrier") >= 10, "barrier 10+")
rate(cnt[ri[B]] >= 12, "field 12+")
rate(o[B] * pm[B] >= 2.0, "overlay 2x+ (open twice our price)")
rate(1 / pm[B] >= 8, "ours $8+")
rate(col("jockeyForm_lastTwelveMonthWinPercentage") < 8, "jockey under 8% wins")
rate(col("trainerForm_lastTwelveMonthWinPercentage") < 8, "trainer under 8% wins")
rate(col("raw_starts") <= 3 if "raw_starts" in cols else np.zeros(len(B), bool), "3 or fewer starts")
np.savez("drifters_bets.npz", B=B, drift=drift, w=w, st=st, pl=pl)
