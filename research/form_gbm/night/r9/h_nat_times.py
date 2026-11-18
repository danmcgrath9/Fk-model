"""h_nat_times.py: the market-only rule at each time of day, every state (18 Nov 2026).
At 9:00am local, and 240 / 60 / 10 / 1 minutes before the jump: fair price from the majors' MEDIAN price then and the
move from TAB's first price (conditional logit, weights fitted walk-forward by month at that time on every state); a bet
to win $1,000 ($2,000 metro) with each major whose own price THEN is at least 1.05x the fair price ($1.60-$15).
A runner scratched before that time is out of the market; scratched after it = in the market, void, deduction."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy.optimize import minimize
from nat_load import MAJORS, METRO, HERE
D = np.load(os.path.join(HERE, "nat.npz"), allow_pickle=True)
date, state, track, race = D["date"].astype(str), D["state"].astype(str), D["track"].astype(str), D["race"]
n = len(date); month = np.array([d[:7] for d in date])
key = np.char.add(np.char.add(np.char.add(date, "|"), np.char.add(state, "|")), np.char.add(np.char.add(track, "|"), race.astype(str)))
_, ri = np.unique(key, return_inverse=True); nR = ri.max() + 1
scr, nine, pos, first = D["scr"], D["nine"], D["pos"], D["tab_first"]
ran = ~np.isfinite(scr); won = ran & (pos == 1)
metro = np.array([any(t.lower().startswith(m) for m in METRO.get(s, ())) for t, s in zip(track, state)]); lim = np.where(metro, 2000.0, 1000.0)


def soft(s, m):
    s = np.where(m, s, -np.inf); mx = np.full(nR, -np.inf); np.maximum.at(mx, ri, s)
    with np.errstate(all="ignore"):
        e = np.where(m, np.exp(s - mx[ri]), 0.0)
    t = np.bincount(ri, weights=e, minlength=nR); return np.where(m, e / np.maximum(t[ri], 1e-300), 0.0)


def fit(m, Xc):
    nr = len(np.unique(ri[m])); Xo = np.where(m[:, None], Xc, 0.0)
    def f(b):
        p = soft(Xo @ b, m); return -np.log(np.maximum(p[m & won], 1e-300)).sum() / nr, -(Xo[m & won].sum(0) - (p[:, None] * Xo).sum(0)) / nr
    return minimize(f, np.zeros(Xc.shape[1]), jac=True, method="L-BFGS-B").x
print("| time | usable races | weights (median, move) | runners bet | bookie bets | winners | staked | profit | ROI | months up | Victoria | every other state |\n|---|---|---|---|---|---|---|---|---|---|---|---|")
for label, sfx, tmin in (("9:00am local", "0900", None), ("4 h before the jump", "t240", -240.0), ("1 h before", "t60", -60.0), ("10 min before", "t10", -10.0), ("1 min before", "t1", -1.0)):
    B = np.column_stack([D[f"{b}_{sfx}"] for b in MAJORS]); B[B <= 1.011] = np.nan
    tt = nine if tmin is None else np.full(n, tmin)
    gone = np.isfinite(scr) & (scr < tt)
    late_ok = np.ones(n, bool) if tmin is None else (nine <= tmin)          # the limits start at 9am: skip a time before 9am race day
    with np.errstate(all="ignore"):
        med = np.nanmedian(B, 1)
    inm = ~gone & late_ok & (np.isfinite(B).sum(1) >= 4) & np.isfinite(B[:, 0]) & np.isfinite(first) & (first > 1.011)
    cnt = np.bincount(ri, weights=inm, minlength=nR); w1 = np.bincount(ri, weights=inm & won, minlength=nR); miss = np.bincount(ri, weights=ran & ~inm, minlength=nR)
    ok = inm & (cnt[ri] >= 4) & (w1[ri] == 1) & (miss[ri] == 0)
    inv = np.where(ok, 1 / np.where(ok, med, 2.0), 0.0); tot = np.bincount(ri, weights=inv, minlength=nR)
    # the whole-book guard (m_exact.py): leave out a race whose book then is under 90% of the usual book at that time
    used = np.bincount(ri, weights=ok, minlength=nR) > 0; usual = np.median(tot[used]); ok = ok & (tot[ri] >= 0.90 * usual)
    inv = np.where(ok, 1 / np.where(ok, med, 2.0), 0.0); tot = np.bincount(ri, weights=inv, minlength=nR)
    DED = np.minimum(np.bincount(ri, weights=np.where(ok & ~ran, inv / np.maximum(tot[ri], 1e-12), 0), minlength=nR), 0.9)[ri]
    X = np.column_stack([-np.log(np.where(ok, med, 1.0)), np.log(np.where(ok, B[:, 0], 1.0)) - np.log(np.where(ok, first, 1.0))])
    months = sorted(set(month[ok])); p = np.zeros(n); b = np.zeros(2)
    for mo in months[4:]:
        b = fit(ok & (month < mo), X); te = ok & (month == mo); p[te] = soft(X @ b, ok)[te]
    test = ok & np.isin(month, months[4:]); fp = np.where(p > 0, 1 / np.maximum(p, 1e-12), np.nan)
    e = test & ran & (fp >= 1.6) & (fp <= 15); hit = e[:, None] & np.isfinite(B) & (B >= 1.05 * fp[:, None])
    st = np.where(hit, lim[:, None] / np.maximum(B - 1, 1e-9), 0.0); pl = np.where(hit, np.where(won[:, None], (lim * (1 - DED))[:, None], -st), 0.0)
    mos = sorted(set(month[hit.any(1)])); up = sum(pl[month == mo].sum() > 0 for mo in mos)
    seg = lambda m: f"{int(hit[m].sum())} bets ${pl[m].sum():+,.0f} {pl[m].sum() / max(st[m].sum(), 1):+.0%}"
    print(f"| {label} | {len(np.unique(ri[test]))} | {b[0]:+.2f}, {b[1]:+.2f} | {int(hit.any(1).sum())} | {int(hit.sum())} | {int((hit.any(1) & won).sum())} | ${st.sum():,.0f} | ${pl.sum():+,.0f} | "
          f"{pl.sum() / max(st.sum(), 1):+.1%} | {up} of {len(mos)} | {seg(state == 'VIC')} | {seg(state != 'VIC')} |", flush=True)
