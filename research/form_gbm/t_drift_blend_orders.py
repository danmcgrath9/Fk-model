"""Follow-up to t_drift_in_price.py: the forecast-BSP blend as the orders are really built, BEFORE the market exists.

At every order step price t the forecast is worked out exactly as drift_forecast.Forecast.y does: opening chance at t =
(1/t) / the median opening book for the field size (from the training races), design(x, p, t, field, book). The
forecast-BSP chance at t is the APPROXIMATION qBSP(t) = (1/t)/book x exp(y_hat(t)), NOT renormalised over the race (the
other runners' prices do not exist when the order is built). Our chance at the step = p10^w x qBSP(t)^(1-w).

Both arms: $1.60-$15 and the 3x ceiling on our model price, edge 1.15 when the open is under $4 else 1.2 (the two live
ladders), steps x1/x1.25/x1.5 under the ceiling, each step sized at the next step's price with stake_rule.stake,
times the live firm/drift multiplier at the step's own price (0.5 drift third / 1 / 2.0 firm third, thirds from the
refit), capped at 5u; fires when the open reaches the step. Current arm: chance = p^0.82 t^-0.22, min odds
0.95 x (E/p^0.82)^(1/0.78). Blend arm: min odds = 0.95 x the lowest t (fine log grid) where chance(t) x t >= E.
Settled at the open less 16c; BSP P/L = the same stakes at BSP less 8% commission.

Forecast refit: late races scored by a model fitted on all races before 2026-08-15; early races cross-fitted (two date
halves). No first-starter / first-up block rules (the same for both arms).   python3.13 t_drift_blend_orders.py"""
import json, numpy as np, drift_forecast as dfc, stake_rule

z = np.load("ds/model_ds_v10.npz", allow_pickle=True)
ri = z["race_idx"]; nR = int(ri.max()) + 1; rdate = z["date"]
cols = [str(c) for c in z["cols"]]; meta = json.load(open("drift_meta.json"))
Xd = z["X"][:, [cols.index(c) for c in meta["cols"]]].astype(np.float32)
p10 = np.load("v10_profit_preds.npz")["p10"].astype(float)
o = z["open"].astype(float); bs = z["bsp"].astype(float); won = (z["finish"] == 1).astype(float)
CUT, HOLD, DED, COMM, TIERS, CAP = "2026-08-15", "2026-06-03", 0.16, 0.08, (1.0, 1.25, 1.5), 5.0
okr = np.isfinite(o) & (o > 1) & np.isfinite(bs) & (bs > 1) & np.isfinite(p10) & (p10 > 0)
cnt = np.bincount(ri, minlength=nR)
race_ok = (np.bincount(ri, weights=okr.astype(float), minlength=nR) == cnt) & (rdate >= HOLD) & \
          (np.bincount(ri, weights=won, minlength=nR) >= 1)
m = race_ok[ri]; field = cnt[ri]; date = rdate[ri]


def norm(v):
    s = np.bincount(ri, weights=np.where(m, v, 0.0), minlength=nR)
    return np.where(m, v / np.where(s[ri] > 0, s[ri], 1), np.nan)


qo = norm(1 / np.where(okr, o, 2)); qb = norm(1 / np.where(okr, bs, 2)); pm = norm(np.where(okr, p10, 1))
book_actual = np.bincount(ri, weights=np.where(m, 1 / np.where(okr, o, 2), 0), minlength=nR)[ri]
y = np.log(qb) - np.log(qo)
early_r = race_ok & (rdate < CUT); late_r = race_ok & (rdate >= CUT); E_, L_ = early_r[ri], late_r[ri]
ed = sorted(set(rdate[early_r])); mid = ed[len(ed) // 2]; e1, e2 = E_ & (date < mid), E_ & (date >= mid)


class Fc:
    """A refit forecast with the Forecast.y conventions (median book per field, nearest field size)."""
    def __init__(self, rows):
        self.book = {int(f): float(np.median(book_actual[rows & (field == f)])) for f in np.unique(field[rows])}
        self.bst, self.t1, self.t2 = dfc.fit(Xd, pm, o, field, book_actual, y, rows, self.book)

    def book_for(self, f):
        ks = sorted(self.book); return self.book[min(ks, key=lambda k: abs(k - f))]

    def y(self, idx, prices):
        """y_hat for runners idx (repeated) at prices, batched."""
        idx = np.asarray(idx); bk = np.array([self.book_for(int(f)) for f in field[idx]])
        return self.bst.predict(dfc.design(Xd[idx], pm[idx], prices, field[idx], bk)), bk

    def mult(self, yv):
        return np.where(yv < self.t1, dfc.DRIFT_MULT, np.where(yv >= self.t2, dfc.FIRM_MULT, 1.0))


GRID = np.exp(np.linspace(np.log(1.05), np.log(46.0), 400))   # candidate prices for the blend's break-even


def simulate(fc, rows, w):
    """w None = current rule; else the blend. Returns [(date, staked, pl_open, pl_bsp, won)]."""
    cand = np.where(rows & (pm > 0) & (1 / pm >= 1.6) & (1 / pm <= 15))[0]
    q = 1 / pm[cand]; E = np.where(o[cand] < 4, 1.15, 1.2)
    if w is None:
        mo = 0.95 * (E / pm[cand] ** 0.82) ** (1 / 0.78)
    else:   # chance(t) x t >= E on a fine grid, under the 3x ceiling
        n, g = len(cand), len(GRID); idx = np.repeat(cand, g); tt = np.tile(GRID, n)
        yv, bk = fc.y(idx, tt)
        val = (pm[idx] ** w * ((1 / tt) / bk * np.exp(yv)) ** (1 - w) * tt).reshape(n, g)
        ok = (val >= E[:, None]) & (GRID[None, :] < 3 * q[:, None])
        first = np.where(ok.any(1), ok.argmax(1), -1)
        mo = np.where(first >= 0, 0.95 * GRID[np.maximum(first, 0)], np.inf)
    keep = (o[cand] >= mo) & (o[cand] < 3 * q)
    cand, q, mo = cand[keep], q[keep], mo[keep]
    # steps and their forecasts, batched
    steps = [[mo[j] * s for s in TIERS if mo[j] * s < 3 * q[j]] for j in range(len(cand))]
    fi = np.concatenate([[cand[j]] * len(s) for j, s in enumerate(steps)]).astype(int); ft = np.concatenate(steps)
    yv, bk = fc.y(fi, ft); mul = fc.mult(yv)
    ch = (pm[fi] ** 0.82 * ft ** -0.22) if w is None else pm[fi] ** w * ((1 / ft) / bk * np.exp(yv)) ** (1 - w)
    out, pos = [], 0
    for j, ts in enumerate(steps):
        i = cand[j]; c = ch[pos:pos + len(ts)]; mu = mul[pos:pos + len(ts)]; pos += len(ts); tot = prev = 0.0
        for k, t in enumerate(ts):
            kp = k + 1 if k + 1 < len(ts) else k
            s_ = min(CAP, stake_rule.stake(c[kp], ts[kp]) * mu[k]); add = max(0.0, s_ - prev); prev = max(prev, s_)
            if o[i] >= t: tot += add
        if tot > 0:
            out.append((date[i], tot, tot * (o[i] - 1) * (1 - DED) if won[i] else -tot,
                        tot * (bs[i] - 1) * (1 - COMM) if won[i] else -tot, won[i]))
    return sorted(out, key=lambda r: r[0])


def merge(*parts):
    return sorted([r for p in parts for r in p], key=lambda r: r[0])


fc_late = Fc(E_); fc_a = Fc(e1); fc_b = Fc(e2)   # fc_a scores e2, fc_b scores e1
WS = (None, 0.15, 0.3, 0.5)
res = {}
for w in WS:
    res[(w, "early")] = merge(simulate(fc_a, e2, w), simulate(fc_b, e1, w))
    res[(w, "late")] = simulate(fc_late, L_, w)


def row(label, r):
    st = np.array([x[1] for x in r]); pl = np.array([x[2] for x in r]); pb = np.array([x[3] for x in r]); c = np.cumsum(pl)
    return (f"| {label} | {len(r)} | {int(sum(x[4] for x in r))} | {st.sum():.0f}u | {pl.sum():+.0f}u | {pl.sum() / st.sum():+.1%} | "
            f"{pb.sum():+.0f}u | {(np.maximum.accumulate(c) - c).max():.0f}u |")


print("| arm | period | bets | winners | staked | profit at open | ROI | BSP P/L | worst drawdown |\n|---|---|---|---|---|---|---|---|---|")
for per in ("early", "late"):
    for w in WS:
        print(row(f"{'current' if w is None else f'blend w={w}'} | {per}{' (cross-fitted)' if per == 'early' else ''}", res[(w, per)]))
wbest = max([w for w in WS if w is not None], key=lambda w: sum(x[2] for x in res[(w, "early")]))
print(f"\nw chosen on early profit: {wbest}")
rng = np.random.default_rng(0)
for per in ("early", "late"):
    days = sorted({x[0] for x in res[(None, per)]} | {x[0] for w in WS if w for x in res[(w, per)]}); di = {d: j for j, d in enumerate(days)}
    def byday(r):
        v = np.zeros(len(days))
        for x in r: v[di[x[0]]] += x[2]
        return v
    for w in WS[1:]:
        d = byday(res[(w, per)]) - byday(res[(None, per)]); bb = np.array([d[rng.integers(0, len(days), len(days))].sum() for _ in range(4000)])
        print(f"{per}: blend w={w} minus current {d.sum():+.0f}u over {len(days)} days; day-bootstrap 90% {np.quantile(bb, .05):+.0f}u to {np.quantile(bb, .95):+.0f}u; P(<=0) {np.mean(bb <= 0):.2f}")
