"""Cash flow at $50 a unit on the live stakes (18 Oct 2026, founder: "a quick cash flow analysis of how much is normally
out for $50 a unit"). Same orders and cross-fitted forecast as t_drift_orders.py (firm x2, middle x1, drift x0.5, 5u cap,
16c deduction, settled at the open), holdout from 6 May. Per meeting, per racing day, per week, the money that has to
sit in the account (bets placed at the open, a median 66h before the jump, so up to three days of meetings are out
at once), and the losing runs.   python3.13 t_cashflow.py   (model dir)"""
import numpy as np, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drift_forecast as dfc, stake_rule
from datetime import date, timedelta
UNIT = 50
T = dfc.load_training(); m = T["m"]; X, pm, o, field, won = T["X"], T["pm"], T["o"], T["field"], T["won"]
z = np.load("../model_v9/model_ds.npz", allow_pickle=True); track = z["track"][T["ri"]].astype(str)
dates = T["date"]; ud = sorted(set(dates[m])); cut = ud[len(ud) // 2]; half = (dates >= cut).astype(int)
book = lambda f: T["book_by_field"].get(int(f), np.median(list(T["book_by_field"].values())))
bets = []   # date, meeting, stake u, P/L u, all-fire u
for h in (0, 1):
    tr = m & (half != h); te = m & (half == h)
    bst, t1, t2 = dfc.fit(X, pm, o, field, T["book_actual"], T["y"], tr, T["book_by_field"])
    for i in np.where(te & (pm > 0))[0]:
        p = pm[i]; q = 1 / p
        if not (1.6 <= q <= 15): continue
        E = 1.15 if o[i] < 4 else 1.2
        mo = 0.95 * (E / p ** 0.82) ** (1 / 0.78)
        ts = [mo * s for s in (1.0, 1.25, 1.5) if mo * s < 3 * q]
        if not ts: continue
        ys = bst.predict(dfc.design(np.repeat(X[i][None, :], len(ts), 0), [p] * len(ts), ts, [field[i]] * len(ts), [book(field[i])] * len(ts)))
        tot = prev = 0.0
        for k, t in enumerate(ts):
            tp = ts[k + 1] if k + 1 < len(ts) else t
            mult = dfc.DRIFT_MULT if ys[k] < t1 else dfc.FIRM_MULT if ys[k] >= t2 else 1.0
            T_k = min(5.0, stake_rule.stake(p ** 0.82 * tp ** -0.22, tp) * mult); add = max(0.0, T_k - prev); prev = max(prev, T_k)
            if o[i] >= t and o[i] < 3 * q: tot += add
        if tot > 0:
            bets.append((dates[i], track[i], tot, tot * (o[i] - 1) * (1 - 0.16) if won[i] else -tot))
d0, d1 = date.fromisoformat(min(ud)), date.fromisoformat(max(ud)); days_all = (d1 - d0).days + 1
meet = collections.defaultdict(lambda: [0, 0.0, 0.0]); day = collections.defaultdict(lambda: [0, 0.0, 0.0, set()])
for dt, tk, st, pl in bets:
    a = meet[(dt, tk)]; a[0] += 1; a[1] += st; a[2] += pl
    b = day[dt]; b[0] += 1; b[1] += st; b[2] += pl; b[3].add(tk)
allmeet = len({(d, t) for d, t in zip(dates[m], track[m])})
q = lambda v: f"${np.median(v) * UNIT:,.0f} (busy 1 in 10: ${np.quantile(v, 0.9) * UNIT:,.0f}, most ${max(v) * UNIT:,.0f})"
ms = [v[1] for v in meet.values()]; ds = [v[1] for v in day.values()]
print(f"{len(bets)} bets, {d0} to {d1}: {len(meet)} of {allmeet} meetings had a bet; {len(day)} racing days with a bet\n")
print(f"- staked per meeting with a bet: {np.mean([v[0] for v in meet.values()]):.1f} bets, typical {q(ms)}")
print(f"- staked per racing day: {np.mean([v[0] for v in day.values()]):.1f} bets, typical {q(ds)}")
wk = collections.defaultdict(lambda: [0.0, 0.0])
for dt, v in day.items():
    k = date.fromisoformat(dt) - timedelta(days=date.fromisoformat(dt).weekday()); wk[k][0] += v[1]; wk[k][1] += v[2]
wv = [v[0] for v in wk.values()]; wp = [v[1] for v in wk.values()]
print(f"- staked per week: typical {q(wv)}; profit per week typical ${np.median(wp) * UNIT:+,.0f}, best ${max(wp) * UNIT:+,.0f}, worst ${min(wp) * UNIT:+,.0f}, losing weeks {sum(x < 0 for x in wp)} of {len(wp)}")
mo_ = collections.defaultdict(lambda: [0.0, 0.0])
for dt, v in day.items(): mo_[dt[:7]][0] += v[1]; mo_[dt[:7]][1] += v[2]
print("\n| month | staked | profit | ROI |\n|---|---|---|---|")
for k in sorted(mo_):
    s_, p_ = mo_[k]; print(f"| {k} | ${s_ * UNIT:,.0f} | ${p_ * UNIT:+,.0f} | {p_ / s_:+.0%} |")
# money out at once: bets go on at the open (median 66h before the jump) and come back at settlement, so a day's
# stakes are out from about 3 days before; outstanding = stakes on races in the next 3 days
cal = [d0 + timedelta(days=k) for k in range(days_all)]; stake_by = {date.fromisoformat(k): v[1] for k, v in day.items()}
out = [sum(stake_by.get(c + timedelta(days=j), 0) for j in range(0, 3)) for c in cal]
print(f"\n- money out at once (stakes on the next 3 days' races): typical ${np.median(out) * UNIT:,.0f}, busy 1 in 10 ${np.quantile(out, 0.9) * UNIT:,.0f}, most ${max(out) * UNIT:,.0f}")
cum = np.cumsum([x[3] for x in sorted(bets)]); dd = (np.maximum.accumulate(cum) - cum).max()
print(f"- worst losing run (peak to trough, bets in date order): {dd:.0f}u = ${dd * UNIT:,.0f}")
print(f"- total: staked ${sum(x[2] for x in bets) * UNIT:,.0f}, profit ${sum(x[3] for x in bets) * UNIT:+,.0f} over {days_all} days")
