"""i_vic_times.py: Victoria with OUR PRICE, the majors' median and exact scratching times, at each time of day (18 Nov 2026).
The national pull (scripts/betwatch_national.py) holds every major's price at 9:00am and 240 / 60 / 10 / 1 minutes
before the jump and the minute each runner was scratched. Joined to the model dataset by date, race number and name:
   log p = a log(ours) + b log(1 / median major price then) + c log(TAB then / TAB first),  fitted walk-forward at each time
and a bet to win the limit with each major whose own price THEN is at least 1.05x the fair price.
At 9:00am this repeats a_model.py's 'ours + median + move' with EXACT scratching times in place of r9/build.py's
'still being re-priced after 9am' (the check on Part 1). Later times are the later list g_later.py could only make
from TAB's price. Run from the night folder."""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy.optimize import minimize
from nat_load import MAJORS, METRO, HERE
norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())
z = np.load("ds/model_ds.npz", allow_pickle=True); P0 = np.load("p_oof_chal.npy").astype(float)
zri = z["race_idx"]; zdate = z["date"].astype(str)[zri]; zname = z["name"].astype(str)
zrno = np.array([int(r.rsplit("_", 1)[1]) for r in z["race_id"].astype(str)])[zri]
zfs = z["X"][:, list(z["cols"]).index("firstStarter")] == 1
zkey = {(zdate[i], int(zrno[i]), norm(zname[i])): i for i in range(len(zri))}
D = np.load(os.path.join(HERE, "nat.npz"), allow_pickle=True)
v = D["state"].astype(str) == "VIC"
date, track, race, name = D["date"].astype(str)[v], D["track"].astype(str)[v], D["race"][v], D["name"].astype(str)[v]
n = len(date); month = np.array([d[:7] for d in date])
scr, nine, pos, first = D["scr"][v], D["nine"][v], D["pos"][v], D["tab_first"][v]
zi = np.array([zkey.get((date[i], int(race[i]), norm(name[i])), -1) for i in range(n)])
ran = ~np.isfinite(scr); won = ran & (pos == 1)
key = np.char.add(np.char.add(date, "|"), np.char.add(track, np.char.add("|", race.astype(str))))
_, ri = np.unique(key, return_inverse=True); nR = ri.max() + 1
metro = np.array([any(t.lower().startswith(m) for m in METRO["VIC"]) for t in track]); lim = np.where(metro, 2000.0, 1000.0)
fs = np.where(zi >= 0, zfs[np.maximum(zi, 0)], False)
Pm = np.where(zi >= 0, P0[np.maximum(zi, 0)], np.nan)
jh = 9 - nine / 60; mk = np.char.add(date, np.char.add("|", track)); _, mi = np.unique(mk, return_inverse=True)
r1 = np.full(mi.max() + 1, 99.0); np.minimum.at(r1, mi, np.where(np.isfinite(jh), jh, 99.0)); night = r1[mi] >= 17.0
print(f"Victoria in the national pull: {n} runners, {nR} races, {min(date)} to {max(date)}; runners that ran matched to the dataset: {int((ran & (zi >= 0)).sum())} of {int(ran.sum())}")


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
print("\n| time | races | weights (ours, median then, move) | runners bet | bookie bets | winners | staked | profit | ROI | months up | not on an earlier list: bets, profit, ROI |\n|---|---|---|---|---|---|---|---|---|---|---|")
earlier = np.zeros((n, len(MAJORS)), bool)
for label, sfx, tmin in (("9:00am", "0900", None), ("4 h before the jump", "t240", -240.0), ("1 h before", "t60", -60.0), ("10 min before", "t10", -10.0), ("1 min before", "t1", -1.0)):
    B = np.column_stack([D[f"{b}_{sfx}"][v] for b in MAJORS]); B[B <= 1.011] = np.nan
    tt = nine if tmin is None else np.full(n, tmin)
    gone = np.isfinite(scr) & (scr < tt); after9 = np.ones(n, bool) if tmin is None else (nine <= tmin)
    with np.errstate(all="ignore"):
        med = np.nanmedian(B, 1)
    inm = ~gone & after9 & ~night & (np.isfinite(B).sum(1) >= 4) & np.isfinite(B[:, 0]) & np.isfinite(first) & (first > 1.011) & (~ran | np.isfinite(Pm))
    cnt = np.bincount(ri, weights=inm, minlength=nR); w1 = np.bincount(ri, weights=inm & won, minlength=nR); miss = np.bincount(ri, weights=ran & ~inm, minlength=nR)
    ok = inm & (cnt[ri] >= 4) & (w1[ri] == 1) & (miss[ri] == 0)
    inv = np.where(ok, 1 / np.where(ok, med, 2.0), 0.0); tot = np.bincount(ri, weights=inv, minlength=nR); share = inv / np.maximum(tot[ri], 1e-12)
    Q = np.bincount(ri, weights=np.where(ok & ~ran, share, 0), minlength=nR); DED = np.minimum(Q, 0.9)[ri]
    ps = np.bincount(ri, weights=np.where(ok & ran, Pm, 0.0), minlength=nR)
    Pe = np.where(ok & ran, Pm / np.maximum(ps[ri], 1e-12) * (1 - Q[ri]), np.where(ok, share, 0.0))      # a late scratching takes its market share
    Lg = lambda x: np.log(np.where(ok & np.isfinite(x) & (x > 0), x, 1.0))
    X = np.column_stack([Lg(Pe), -Lg(med), Lg(B[:, 0]) - Lg(first)])
    months = sorted(set(month[ok])); p = np.zeros(n); b = np.zeros(3)
    for mo in months[4:]:
        b = fit(ok & (month < mo), X); te = ok & (month == mo); p[te] = soft(X @ b, ok)[te]
    test = ok & np.isin(month, months[4:]); fp = np.where(p > 0, 1 / np.maximum(p, 1e-12), np.nan)
    e = test & ran & ~fs & (fp >= 1.6) & (fp <= 15); hit = e[:, None] & np.isfinite(B) & (B >= 1.05 * fp[:, None])
    st = np.where(hit, lim[:, None] / np.maximum(B - 1, 1e-9), 0.0); pl = np.where(hit, np.where(won[:, None], (lim * (1 - DED))[:, None], -st), 0.0)
    mos = sorted(set(month[hit.any(1)])); up = sum(pl[month == mo].sum() > 0 for mo in mos); new = hit & ~earlier
    print(f"| {label} | {len(np.unique(ri[test]))} | {b[0]:+.2f}, {b[1]:+.2f}, {b[2]:+.2f} | {int(hit.any(1).sum())} | {int(hit.sum())} | {int((hit.any(1) & won).sum())} | ${st.sum():,.0f} | ${pl.sum():+,.0f} | "
          f"{pl.sum() / max(st.sum(), 1):+.1%} | {up} of {len(mos)} | {int(new.sum())}, ${pl[new].sum():+,.0f}, {pl[new].sum() / max(st[new].sum(), 1):+.0%} |", flush=True)
    earlier |= hit
    if tmin is None:
        print(f"|   (9:00am: late scratchings by their exact time: {int((ok & ~ran).sum())} in {len(np.unique(ri[ok & ~ran]))} races) | | | | | | | | | | |")
