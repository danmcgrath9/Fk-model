"""d_national.py: the 9am rule WITHOUT our model, in every state (18 Nov 2026).
Data: scripts/betwatch_national.py (Betwatch; majors' 9am prices, TAB's first price, exact scratching times, results).
A runner is in the 9am market if it holds 4+ majors' 9am prices and was not scratched before 9:00am local; scratched
after 9am = in the market, bet void, its market share comes off a winner as the deduction.
Fair price: conditional logit  log p = a x log(1 / median major 9am price) + b x log(TAB 9am / TAB first price).
  A. weights fitted on VICTORIA ONLY, tested on every other state (nothing of theirs was ever looked at)
  B. weights fitted walk-forward by month on every state
Bet: to win $1,000 ($2,000 metro) with each major whose own 9am price is at least 1.05x the fair price ($1.60-$15)."""
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
B = np.column_stack([D[f"{b}_0900"] for b in MAJORS]); B[B <= 1.011] = np.nan
scr, nine, pos = D["scr"], D["nine"], D["pos"]
gone = np.isfinite(scr) & (scr < nine)                         # scratched before 9am: not in the 9am market
ran = ~np.isfinite(scr); won = ran & (pos == 1)
n7 = np.isfinite(B).sum(1)
with np.errstate(all="ignore"):
    med = np.nanmedian(B, 1)
T9 = B[:, 0]; first = D["tab_first"]
inm = ~gone & (n7 >= 4) & np.isfinite(T9) & np.isfinite(first) & (first > 1.011)
cnt = np.bincount(ri, weights=inm, minlength=nR); w1 = np.bincount(ri, weights=inm & won, minlength=nR)
miss = np.bincount(ri, weights=ran & ~inm, minlength=nR)
ok = inm & (cnt[ri] >= 4) & (w1[ri] == 1) & (miss[ri] == 0)
# day or night: the limits start at 9am for a day meeting and 2pm for a night one, so a 9am list is for day meetings
jh = 9 - nine / 60; mkey = np.char.add(np.char.add(date, "|"), np.char.add(state, np.char.add("|", track)))
_, mi = np.unique(mkey, return_inverse=True); r1 = np.full(mi.max() + 1, 99.0); np.minimum.at(r1, mi, np.where(np.isfinite(jh), jh, 99.0))
night = r1[mi] >= 17.0
ok_all = ok.copy(); ok = ok & ~night
metro = np.array([any(t.lower().startswith(m) for m in METRO.get(s, ())) for t, s in zip(track, state)])
lim = np.where(metro, 2000.0, 1000.0)
inv = np.where(ok, 1 / np.where(ok, med, 2.0), 0.0); tot = np.bincount(ri, weights=inv, minlength=nR)
share = inv / np.maximum(tot[ri], 1e-12); DED = np.minimum(np.bincount(ri, weights=np.where(ok & ~ran, share, 0), minlength=nR), 0.9)[ri]
lm = -np.log(np.where(ok, med, 1.0)); mv = np.log(np.where(ok, T9, 1.0)) - np.log(np.where(ok, first, 1.0))
X = np.column_stack([lm, mv])


def soft(s, m):
    s = np.where(m, s, -np.inf); mx = np.full(nR, -np.inf); np.maximum.at(mx, ri, s)
    e = np.where(m, np.exp(s - mx[ri]), 0.0); t = np.bincount(ri, weights=e, minlength=nR)
    return np.where(m, e / np.maximum(t[ri], 1e-300), 0.0)


def fit(m, Xc):
    nr = len(np.unique(ri[m])); Xo = np.where(m[:, None], Xc, 0.0)
    def f(b):
        p = soft(Xo @ b, m); return -np.log(np.maximum(p[m & won], 1e-300)).sum() / nr, -(Xo[m & won].sum(0) - (p[:, None] * Xo).sum(0)) / nr
    return minimize(f, np.zeros(Xc.shape[1]), jac=True, method="L-BFGS-B").x


def bets(p, m, thr=1.05):
    fp = np.where(p > 0, 1 / np.maximum(p, 1e-12), np.nan)
    e = m & ran & (fp >= 1.6) & (fp <= 15)
    hit = e[:, None] & np.isfinite(B) & (B >= thr * fp[:, None])
    st = np.where(hit, lim[:, None] / np.maximum(B - 1, 1e-9), 0.0)
    pl = np.where(hit, np.where(won[:, None], (lim * (1 - DED))[:, None], -st), 0.0)
    return hit, st, pl


def row(label, hit, st, pl, m):
    h = hit & m[:, None]; s, p_ = st[m].sum(), pl[m].sum(); mos = sorted(set(month[h.any(1)]))
    up = sum(pl[(month == mo) & m].sum() > 0 for mo in mos)
    return f"| {label} | {len(np.unique(ri[m & ok]))} | {int(h.any(1).sum())} | {int(h.sum())} | {int((h.any(1) & won).sum())} | ${s:,.0f} | ${p_:+,.0f} | {(p_ / s if s else 0):+.1%} | {up} of {len(mos)} |"
HEAD = "| | races | runners bet | bookie bets | winners | staked | profit | ROI | months up |\n|---|---|---|---|---|---|---|---|---|"
print(f"{n} runners, {nR} races, {min(date)} to {max(date)}; day-meeting races usable at 9am: {len(np.unique(ri[ok]))} (night meetings left out: "
      f"{len(np.unique(ri[ok_all & night]))} races); late scratchings in them: {int((ok & ~ran).sum())}")
vic = state == "VIC"
for label, Xc, names in (("market only", X[:, :1], ["median"]), ("market + move", X, ["median", "move"])):
    b = fit(ok & vic, Xc); p = soft(Xc @ b, ok)
    print(f"\n### A. {label}: weights fitted on Victoria only (" + ", ".join(f"{nm} {v:+.2f}" for nm, v in zip(names, b)) + "), every state\n\n" + HEAD)
    hit, st, pl = bets(p, ok)
    for s_ in ("VIC", "NSW", "QLD", "SA", "WA", "TAS", "ACT", "NT"):
        if (ok & (state == s_)).any(): print(row(s_ + (" (fitted here)" if s_ == "VIC" else ""), hit, st, pl, ok & (state == s_)))
    print(row("**every state but Victoria**", hit, st, pl, ok & ~vic))
    oth = ok & ~vic
    ll = -np.log(np.maximum(p[oth & won], 1e-300)).mean(); p0 = soft(X[:, 0], ok); ll0 = -np.log(np.maximum(p0[oth & won], 1e-300)).mean()
    print(f"\nwinner log loss outside Victoria: {ll:.4f} against {ll0:.4f} for the raw median price")
    if label == "market + move":
        print("\nby half-year, every state but Victoria\n" + HEAD)
        for a, b_, lab in (("2025-07", "2026-01", "Jul-Dec 2025"), ("2026-01", "2026-07", "Jan-Jun 2026"), ("2026-07", "2027-01", "Jul-Nov 2026")):
            print(row(lab, hit, st, pl, oth & (month >= a) & (month < b_)))
        print("\nby threshold, every state but Victoria: " + "; ".join(f"{t:.2f}x {int(h.sum())} bets ${pl_.sum():+,.0f} {pl_.sum() / max(s_.sum(), 1):+.0%}" for t in (1.0, 1.03, 1.05, 1.08, 1.12)
              for h, s_, pl_ in [tuple(x[oth] for x in bets(p, ok, t))]))
        np.save(os.path.join(HERE, "nat_fair.npy"), p)
        k = hit.sum(1); print("\nby how many majors are at the take price, every state but Victoria (one bookmaker alone can be a stale price in the feed)\n" + HEAD)
        for a_, b2, lab in ((1, 1, "one major"), (2, 3, "2-3 majors"), (4, 7, "4 or more")): print(row(lab, hit, st, pl, oth & (k >= a_) & (k <= b2)))
        fpz = np.where(p > 0, 1 / np.maximum(p, 1e-12), np.nan); print("\nby fair price, every state but Victoria\n" + HEAD)
        for a_, b2 in ((1.6, 3), (3, 5), (5, 8), (8, 15)): print(row(f"${a_:g}-${b2:g}", hit, st, pl, oth & (fpz >= a_) & (fpz < b2)))
        print("\nby the move before 9am, every state but Victoria\n" + HEAD)
        for a_, b2, lab in ((-9, -0.22, "firmed 20%+ since the open"), (-0.22, -0.05, "firmed 5-20%"), (-0.05, 0.05, "held"), (0.05, 9, "drifted 5%+")): print(row(lab, hit, st, pl, oth & (mv >= a_) & (mv < b2)))
# B. walk-forward by month on everything
months = sorted(set(month[ok])); p = np.zeros(n); b = None
for mo in months[4:]:
    b = fit(ok & (month < mo), X); te = ok & (month == mo); p[te] = soft(X @ b, ok)[te]
test = ok & np.isin(month, months[4:])
print(f"\n### B. market + move, weights fitted walk-forward on every state (last fit: median {b[0]:+.2f}, move {b[1]:+.2f}), test months {months[4]} on\n\n" + HEAD)
hit, st, pl = bets(p, test)
for s_ in ("VIC", "NSW", "QLD", "SA", "WA", "TAS", "ACT", "NT"):
    if (test & (state == s_)).any(): print(row(s_, hit, st, pl, test & (state == s_)))
print(row("**all**", hit, st, pl, test))
print("\nby major, all states: " + "; ".join(f"{k} {int(hit[:, j].sum())} bets ${pl[:, j].sum():+,.0f} {pl[:, j].sum() / max(st[:, j].sum(), 1):+.0%}" for j, k in enumerate(MAJORS)))
