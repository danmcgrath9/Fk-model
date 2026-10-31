"""Backed and failed last start (1 Nov 2026, founder: "It would be taken into account of well supported and failed though?").
Holdout from 3 Jun: horses whose LAST start was at BSP under $5 and finished 4th or worse, next start: wins v the model's
chance and v the market's (BSP) chance, and the live open rule's return on them."""
import numpy as np, stake_rule
z = np.load("ds/model_ds_v10.npz", allow_pickle=True)
ri = z["race_idx"]; nR = int(ri.max()) + 1
p10 = np.load("v10_profit_preds.npz")["p10"].astype(float)
o = z["open"].astype(float); bs = z["bsp"].astype(float); won = z["finish"] == 1; rdate = z["date"].astype(str)
P = z["P"]; pf = list(z["past_fields"]); cols = list(z["cols"])
db = P[:, :, pf.index("days_before")]
print("days_before row 0..2 sample:", db[5, :3])
lb = P[:, 0, pf.index("bsp")].astype(float); lf = P[:, 0, pf.index("finish")].astype(float); lsp = P[:, 0, pf.index("sp")].astype(float)
print("feature cols mentioning backed/expected/bsp:", [c for c in cols if any(k in c.lower() for k in ("back", "expect", "bsp", "_sp", "market"))][:30])
okr = np.isfinite(bs) & (bs > 1) & np.isfinite(p10) & (p10 > 0) & np.isfinite(o) & (o > 1)
cnt = np.bincount(ri, minlength=nR)
race_ok = (np.bincount(ri, weights=okr.astype(float), minlength=nR) == cnt) & (rdate >= "2026-06-03") & (np.bincount(ri, weights=won.astype(float), minlength=nR) >= 1)
m = race_ok[ri]
s = np.bincount(ri, weights=np.where(m, p10, 0), minlength=nR); pm = np.where(m, p10 / np.where(s[ri] > 0, s[ri], 1), np.nan)
ib = np.where(m, 1 / bs, 0); sb = np.bincount(ri, weights=ib, minlength=nR); pb = np.where(m, ib / np.where(sb[ri] > 0, sb[ri], 1), np.nan)
def row(name, g):
    w = won[g].sum(); e = pm[g].sum(); eb = pb[g].sum(); sd = np.sqrt((pm[g] * (1 - pm[g])).sum())
    print(f"{name:42s} n={g.sum():5d} won {w:4d}  model {e:6.1f} ({w/e:4.2f}, z {(w-e)/sd:+.1f})  market {eb:6.1f} ({w/eb:4.2f})  model/market chance {np.nanmean(pm[g]/pb[g]):.2f}")
price = np.where(np.isfinite(lb) & (lb > 1), lb, lsp)
row("all", m)
row("backed (<$5) and failed (4th+) last start", m & (price < 5) & (lf >= 4))
row("  backed under $3 and failed", m & (price < 3) & (lf >= 4))
row("backed (<$5) and placed last start", m & (price < 5) & (lf >= 1) & (lf <= 3))
row("drifter (>$15) and failed last start", m & (price > 15) & (lf >= 4))
# bets under the live open rule on the backed-and-failed group
g = m & (price < 5) & (lf >= 4); n = st = pl = 0.0
for i in np.where(g)[0]:
    q = 1 / pm[i]
    if not (1.6 <= q <= 15 and o[i] < 3 * q): continue
    E = 1.15 if q < 4 else 1.2; mo = 0.95 * (E / pm[i] ** 0.82) ** (1 / 0.78)
    if o[i] < mo: continue
    u = stake_rule.stake(pm[i] ** 0.82 * mo ** -0.22, mo)
    if u <= 0: continue
    n += 1; st += u; pl += u * ((o[i] - 1) * 0.93 if won[i] else -1)
print(f"live-rule bets on backed-and-failed: {n:.0f} bets, {st:.0f}u, {pl:+.0f}u ({100*pl/st if st else 0:+.0f}%)")
