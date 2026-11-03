"""The paper lay rule (BSP $15-$40 and at least 1.6x our price, 1u lay at BSP, 8% commission) month by month on the
v10 holdout from 3 Jun, in units and at $100 a unit (3 Nov 2026, founder: 'for $100 a unit what's our monthly, just the lay')."""
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
pm = norm(p10, m); ours = 1 / pm
UNIT, COMM = 100.0, 0.08
for lo, hi, lab in ((15, 30, "$15-$30 band"), (15, 40, "$15-$40 band (the live paper rule)")):
    g = m & (bs >= lo) & (bs <= hi) & (bs >= 1.6 * ours)
    pl = np.where(won & g, -(bs - 1), 1 - COMM)
    print(f"\n=== {lab}: {g.sum()} lays, {int(won[g].sum())} winners, {pl[g].sum():+.0f}u ({100*pl[g].sum()/g.sum():+.0f}% on the lay stake), at ${UNIT:.0f} a unit {pl[g].sum()*UNIT:+,.0f}")
    print("| month | lays | winners | P/L units | P/L at $100 | liability out that month (sum of BSP-1) | worst day |")
    mo = collections.OrderedDict(); day = collections.defaultdict(float)
    for i in np.where(g)[0]:
        a = mo.setdefault(date[i][:7], [0, 0, 0.0, 0.0]); a[0] += 1; a[1] += int(won[i]); a[2] += pl[i]; a[3] += bs[i] - 1; day[date[i]] += pl[i]
    for k, (n, w, q, liab) in mo.items():
        wd = min(v for d, v in day.items() if d.startswith(k))
        print(f"| {k} | {n} | {w} | {q:+.1f}u | ${q*UNIT:+,.0f} | ${liab*UNIT:,.0f} | {wd:+.1f}u (${wd*UNIT:+,.0f}) |")
    days = sorted(day); c = np.cumsum([day[d] for d in days]); ddn = np.max(np.maximum.accumulate(c) - c)
    wk = len(set(rdate[race_ok])) / 7.0
    print(f"worst drawdown {ddn:.1f}u (${ddn*UNIT:,.0f}); a week ~{pl[g].sum()/wk:+.1f}u (${pl[g].sum()*UNIT/wk:+,.0f}); a month ~${pl[g].sum()*UNIT/wk*4.33:+,.0f}; "
          f"biggest single loss {np.max(bs[g & won]-1) if (g & won).any() else 0:.1f}u (${np.max(bs[g & won]-1)*UNIT:,.0f}); mean liability per lay {np.mean(bs[g]-1):.1f}u, lays a week {g.sum()/wk:.0f}")
