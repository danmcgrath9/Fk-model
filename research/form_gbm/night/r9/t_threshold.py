"""t_threshold.py (from n_bsp.py): the 9am list against Betfair SP (18 Nov 2026; founder: "give me the profit at BSP for this as well and how
much it shortens from 9am to jump"). Victoria, exact scratching times, whole 9am books (1.20 and over), Jul 2025 to
Nov 2026. For each version of the list: the horses on it, ONE bet a horse to win the limit
   at the BEST major price at 9am (after the deduction for any late scratching)   against
   at Betfair SP (no deduction; shown before and after 8% commission),
and how the price moved: 9am best price / BSP, 9am price / that bookmaker's own price a minute before the jump."""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from nat_load import MAJORS, METRO, HERE
norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())
z = np.load("ds/model_ds.npz", allow_pickle=True); P0 = np.load("p_oof_chal.npy").astype(float)
zri = z["race_idx"]; zdate = z["date"].astype(str)[zri]; zname = z["name"].astype(str)
zrno = np.array([int(r.rsplit("_", 1)[1]) for r in z["race_id"].astype(str)])[zri]
zfs = z["X"][:, list(z["cols"]).index("firstStarter")] == 1
zkey = {(zdate[i], int(zrno[i]), norm(zname[i])): i for i in range(len(zri))}
D = np.load(os.path.join(HERE, "nat.npz"), allow_pickle=True); v = D["state"].astype(str) == "VIC"
date, track, race, name = D["date"].astype(str)[v], D["track"].astype(str)[v], D["race"][v], D["name"].astype(str)[v]
n = len(date); scr, nine, pos, first, bsp = D["scr"][v], D["nine"][v], D["pos"][v], D["tab_first"][v], D["bsp"][v]
zi = np.array([zkey.get((date[i], int(race[i]), norm(name[i])), -1) for i in range(n)])
ran = ~np.isfinite(scr); won = ran & (pos == 1)
key = np.char.add(np.char.add(date, "|"), np.char.add(track, np.char.add("|", race.astype(str)))); _, ri = np.unique(key, return_inverse=True); nR = ri.max() + 1
metro = np.array([any(t.lower().startswith(m) for m in METRO["VIC"]) for t in track]); lim = np.where(metro, 2000.0, 1000.0)
fs = np.where(zi >= 0, zfs[np.maximum(zi, 0)], False); Pm = np.where(zi >= 0, P0[np.maximum(zi, 0)], np.nan)
jh = 9 - nine / 60; mk = np.char.add(date, np.char.add("|", track)); _, mi = np.unique(mk, return_inverse=True)
r1 = np.full(mi.max() + 1, 99.0); np.minimum.at(r1, mi, np.where(np.isfinite(jh), jh, 99.0)); night = r1[mi] >= 17.0
B = np.column_stack([D[f"{b}_0900"][v] for b in MAJORS]); B[B <= 1.011] = np.nan
T1 = np.column_stack([D[f"{b}_t1"][v] for b in MAJORS]); T1[T1 <= 1.011] = np.nan
T60 = np.column_stack([D[f"{b}_t60"][v] for b in MAJORS]); T60[T60 <= 1.011] = np.nan
gone = np.isfinite(scr) & (scr < nine)
with np.errstate(all="ignore"): med = np.nanmedian(B, 1); med1 = np.nanmedian(T1, 1)
inm = ~gone & ~night & (np.isfinite(B).sum(1) >= 4) & np.isfinite(B[:, 0]) & np.isfinite(first) & (first > 1.011) & (~ran | np.isfinite(Pm))
cnt = np.bincount(ri, weights=inm, minlength=nR); w1 = np.bincount(ri, weights=inm & won, minlength=nR); miss = np.bincount(ri, weights=ran & ~inm, minlength=nR)
ok = inm & (cnt[ri] >= 4) & (w1[ri] == 1) & (miss[ri] == 0)
inv = np.where(ok, 1 / np.where(ok, med, 2.0), 0.0); tot = np.bincount(ri, weights=inv, minlength=nR); share = inv / np.maximum(tot[ri], 1e-12)
ok = ok & (tot[ri] >= 1.20)                                                     # whole books only
inv = np.where(ok, 1 / np.where(ok, med, 2.0), 0.0); tot = np.bincount(ri, weights=inv, minlength=nR); share = inv / np.maximum(tot[ri], 1e-12)
Q = np.bincount(ri, weights=np.where(ok & ~ran, share, 0), minlength=nR); DED = np.minimum(Q, 0.9)[ri]
ps = np.bincount(ri, weights=np.where(ok & ran, Pm, 0.0), minlength=nR)
Pe = np.where(ok & ran, Pm / np.maximum(ps[ri], 1e-12) * (1 - Q[ri]), np.where(ok, share, 0.0))
Lg = lambda x: np.log(np.where(ok & np.isfinite(x) & (x > 0), x, 1.0))


def soft(s):
    s = np.where(ok, s, -np.inf); mx = np.full(nR, -np.inf); np.maximum.at(mx, ri, s)
    with np.errstate(all="ignore"): e = np.where(ok, np.exp(s - mx[ri]), 0.0)
    t = np.bincount(ri, weights=e, minlength=nR); return np.where(ok, e / np.maximum(t[ri], 1e-300), 0.0)


bestB = np.nanmax(np.where(np.isfinite(B), B, -1.0), 1)

# THE LIVE 9AM RULE (blend_9am_v2.py): 0.267 ours + 0.903 median of the majors - 0.215 TAB's move since its first price;
# one bet a horse at the best major price at 9am when best >= TAKE x fair; open-book units min(10, 78.125 (best/fair - 1)/(best - 1)), $50 a unit.
sc = 0.267 * Lg(Pe) - 0.903 * Lg(med) - 0.215 * (Lg(B[:, 0]) - Lg(first))
p = soft(sc); fp = np.where(p > 0, 1 / np.maximum(p, 1e-12), np.nan)
e = ok & ran & ~fs & (fp >= 1.6) & (fp <= 15) & np.isfinite(bsp) & (bsp > 1.0) & (bestB > 1)
ratio = np.where(e, bestB / fp, 0.0)
units = np.where(e, np.minimum(10.0, 78.125 * np.maximum(ratio - 1, 0) / np.maximum(bestB - 1, 1e-9)), 0.0)
stake = 50 * units
p9 = np.where(won, stake * (bestB - 1) * (1 - DED), -stake)
pS = np.where(won, stake * (bsp - 1) * 0.92, -stake)
month = np.array([d[:7] for d in date]); rng = np.random.default_rng(7)
def line(lab, m):
    st = stake[m].sum(); w = int((m & won).sum())
    if not m.any() or st <= 0: return f"| {lab} | 0 | | | | | | | |"
    mons = sorted(set(month[m])); up = sum(p9[m & (month == x)].sum() > 0 for x in mons)
    days = np.unique(date[m]); dp = np.array([p9[m & (date == d)].sum() for d in days]); ds = np.array([stake[m & (date == d)].sum() for d in days])
    bs = [dp[i].sum() / ds[i].sum() for i in (rng.integers(0, len(days), len(days)) for _ in range(4000))]
    return (f"| {lab} | {int(m.sum())} | {w} ({p[m].sum():.1f} fair) | ${st:,.0f} ({units[m].mean():.2f}u avg) | ${p9[m].sum():+,.0f} | {p9[m].sum() / st:+.1%} | "
            f"${pS[m].sum():+,.0f} | {pS[m].sum() / st:+.1%} | {up} of {len(mons)} | {np.mean(np.array(bs) > 0):.0%} |")
H = "| | horses | winners | staked | P/L at 9am best price | ROI | P/L at BSP after 8% | ROI | months up | chance above zero |\n|---|---|---|---|---|---|---|---|---|---|"
print(f"Victoria {min(date[e])} to {max(date[e])}, whole books, exact scratching times\n\n## Take line (best price / fair), everything at or above it\n\n{H}")
for T in (1.00, 1.01, 1.02, 1.03, 1.04, 1.05):
    print(line(f"{T:.2f}x and over", e & (ratio >= T)))
print(f"\n## Band by band (what each step down ADDS)\n\n{H}")
for a, b in ((0.97, 1.00), (1.00, 1.02), (1.02, 1.03), (1.03, 1.04), (1.04, 1.05), (1.05, 1.08), (1.08, 99)):
    print(line(f"{a:.2f}-{b:.2f}x", e & (ratio >= a) & (ratio < b)))
print(f"\n## The 1.03-1.05x band by period\n\n{H}")
band = e & (ratio >= 1.03) & (ratio < 1.05)
for lab, x in (("Jul-Oct 2025", date < "2025-11-01"), ("Nov 2025-Jun 2026", (date >= "2025-11-01") & (date < "2026-07-01")), ("Jul-Nov 2026", date >= "2026-07-01")):
    print(line(lab, band & x))
print(f"\n## 1.05x and over by period (today's rule)\n\n{H}")
for lab, x in (("Jul-Oct 2025", date < "2025-11-01"), ("Nov 2025-Jun 2026", (date >= "2025-11-01") & (date < "2026-07-01")), ("Jul-Nov 2026", date >= "2026-07-01")):
    print(line(lab, e & (ratio >= 1.05) & x))
