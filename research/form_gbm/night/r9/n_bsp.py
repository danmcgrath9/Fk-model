"""n_bsp.py: the 9am list against Betfair SP (18 Nov 2026; founder: "give me the profit at BSP for this as well and how
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
MODELS = (("NEW VERSION: 0.28 ours + 0.88 median - 0.22 move", 0.28 * Lg(Pe) - 0.88 * Lg(med) - 0.22 * (Lg(B[:, 0]) - Lg(first))),
          ("TODAY'S LIST: 0.20 ours + 1.00 best major price", 0.20 * Lg(Pe) - Lg(bestB)))
COMM = 0.08
print(f"Victoria {min(date[ok])} to {max(date[ok])}: {len(np.unique(ri[ok]))} day races with a whole 9am book")
for label, sc in MODELS:
    p = soft(sc); fp = np.where(p > 0, 1 / np.maximum(p, 1e-12), np.nan); e = ok & ran & ~fs & (fp >= 1.6) & (fp <= 15)
    hit = e[:, None] & np.isfinite(B) & (B >= 1.05 * fp[:, None]); ru = hit.any(1)
    best = np.nanmax(np.where(hit, B, np.nan), 1, initial=np.nan, where=hit)          # the best major price at the take price
    hb = ru & np.isfinite(bsp) & (bsp > 1.0)
    print(f"\n## {label}\n\nhorses on the list: {int(ru.sum())}; with a Betfair SP: {int(hb.sum())}; winners {int((hb & won).sum())}")
    # one bet a horse to win the limit
    sB = np.where(hb, lim / (best - 1), 0.0); pB = np.where(hb, np.where(won, lim * (1 - DED), -sB), 0.0)
    sS = np.where(hb, lim / (bsp - 1), 0.0); pS0 = np.where(hb, np.where(won, lim, -sS), 0.0); pS = np.where(hb, np.where(won, lim * (1 - COMM), -sS), 0.0)
    # level stakes $100 a horse
    fB = np.where(hb, np.where(won, 100 * (best - 1) * (1 - DED), -100.0), 0.0); fS = np.where(hb, np.where(won, 100 * (bsp - 1) * (1 - COMM), -100.0), 0.0)
    print("\n| one bet a horse | staked | profit | return |\n|---|---|---|---|")
    print(f"| best major price at 9am, to win the limit | ${sB.sum():,.0f} | ${pB.sum():+,.0f} | {pB.sum() / sB.sum():+.1%} |")
    print(f"| Betfair SP, to win the limit, before commission | ${sS.sum():,.0f} | ${pS0.sum():+,.0f} | {pS0.sum() / sS.sum():+.1%} |")
    print(f"| Betfair SP, to win the limit, after 8% commission | ${sS.sum():,.0f} | ${pS.sum():+,.0f} | {pS.sum() / sS.sum():+.1%} |")
    print(f"| level $100 a horse at the 9am best price | ${100 * hb.sum():,.0f} | ${fB.sum():+,.0f} | {fB.sum() / (100 * hb.sum()):+.1%} |")
    print(f"| level $100 a horse at Betfair SP, after commission | ${100 * hb.sum():,.0f} | ${fS.sum():+,.0f} | {fS.sum() / (100 * hb.sum()):+.1%} |")
    r = best[hb] / bsp[hb]
    print(f"\n9am best price against Betfair SP: beat BSP on {int((r > 1).sum())} of {int(hb.sum())} ({(r > 1).mean():.0%}); median 9am price ${np.median(best[hb]):.2f}, median BSP ${np.median(bsp[hb]):.2f}; "
          f"9am / BSP median {np.median(r):.2f}x, average {r.mean():.2f}x, weighted by stake {(sB[hb] * r).sum() / sB[hb].sum():.2f}x")
    print("  spread of 9am / BSP: " + ", ".join(f"{lab} {int(((r >= a) & (r < b)).sum())}" for lab, a, b in (("shorter at 9am than BSP by 10%+", 0, 0.9), ("within 10%", 0.9, 1.1), ("10-30% longer at 9am", 1.1, 1.3), ("30-60% longer", 1.3, 1.6), ("60%+ longer", 1.6, 99))))
    # each bookie bet: that bookmaker's own price an hour out and a minute out
    for lab, T in (("an hour before the jump", T60), ("a minute before the jump", T1)):
        okb = hit & np.isfinite(T); rr = B[okb] / T[okb]
        print(f"  the same bookmaker {lab} ({int(okb.sum())} of {int(hit.sum())} bookie bets): shorter than its 9am price on {(rr > 1.005).mean():.0%}, the same on {(np.abs(rr - 1) <= 0.005).mean():.0%}, longer on {(rr < 0.995).mean():.0%}; 9am / then median {np.median(rr):.2f}x, average {rr.mean():.2f}x")
    mm = hb & np.isfinite(med1)
    print(f"  the majors' median price a minute before the jump against their median at 9am ({int(mm.sum())} horses): 9am / jump median {np.median(med[mm] / med1[mm]):.2f}x; firmed on {(med1[mm] < med[mm] * 0.995).mean():.0%}")
    # by era, at BSP after commission and at the 9am price
    print("  by period (one bet a horse to win the limit): " + "; ".join(f"{lab}: 9am {pB[x].sum() / max(sB[x].sum(), 1):+.0%}, BSP {pS[x].sum() / max(sS[x].sum(), 1):+.0%} ({int((hb & x).sum())} horses)" for lab, x in (("Jul-Oct 2025", date < "2025-11-01"), ("Nov 2025-Jun 2026", (date >= "2025-11-01") & (date < "2026-07-01")), ("Jul-Nov 2026", date >= "2026-07-01"))))
    # the winners' expected count at BSP
    print(f"  winners {int((hb & won).sum())} against {np.sum(1 / bsp[hb]):.1f} that BSP expects and {p[hb].sum():.1f} that the list's fair price expects")
