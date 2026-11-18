"""m_exact.py: the Victorian 9am test again with EXACT scratching times (18 Nov 2026).
The national pull holds the minute each runner was scratched, so who was in the 9am market is known, not inferred.
Three fair prices, fixed weights (the fitted ones are from a_model's last walk-forward fit; three numbers on 4,000 races):
   FITTED  0.28 log(ours) + 0.88 log(1/median major) - 0.22 log(TAB 9am / TAB first)
   LIVE    0.20 log(ours) + 1.00 log(1/TAB 9am)
   MARKET  1.19 log(1/median major)
A bet to win the limit with each major by how far its 9am price is over the fair price. Winners are paid after a
deduction equal to the late scratchings' share of the 9am book. Night meetings left out. Nov 2025 - Nov 2026."""
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
n = len(date); scr, nine, pos, first = D["scr"][v], D["nine"][v], D["pos"][v], D["tab_first"][v]
zi = np.array([zkey.get((date[i], int(race[i]), norm(name[i])), -1) for i in range(n)])
ran = ~np.isfinite(scr); won = ran & (pos == 1)
key = np.char.add(np.char.add(date, "|"), np.char.add(track, np.char.add("|", race.astype(str)))); _, ri = np.unique(key, return_inverse=True); nR = ri.max() + 1
metro = np.array([any(t.lower().startswith(m) for m in METRO["VIC"]) for t in track]); lim = np.where(metro, 2000.0, 1000.0)
fs = np.where(zi >= 0, zfs[np.maximum(zi, 0)], False); Pm = np.where(zi >= 0, P0[np.maximum(zi, 0)], np.nan)
jh = 9 - nine / 60; mk = np.char.add(date, np.char.add("|", track)); _, mi = np.unique(mk, return_inverse=True)
r1 = np.full(mi.max() + 1, 99.0); np.minimum.at(r1, mi, np.where(np.isfinite(jh), jh, 99.0)); night = r1[mi] >= 17.0
B = np.column_stack([D[f"{b}_0900"][v] for b in MAJORS]); B[B <= 1.011] = np.nan
gone = np.isfinite(scr) & (scr < nine)
with np.errstate(all="ignore"): med = np.nanmedian(B, 1)
inm = (date >= "2025-11-01") & ~gone & ~night & (np.isfinite(B).sum(1) >= 4) & np.isfinite(B[:, 0]) & np.isfinite(first) & (first > 1.011) & (~ran | np.isfinite(Pm))
cnt = np.bincount(ri, weights=inm, minlength=nR); w1 = np.bincount(ri, weights=inm & won, minlength=nR); miss = np.bincount(ri, weights=ran & ~inm, minlength=nR)
ok = inm & (cnt[ri] >= 4) & (w1[ri] == 1) & (miss[ri] == 0)
inv = np.where(ok, 1 / np.where(ok, med, 2.0), 0.0); tot = np.bincount(ri, weights=inv, minlength=nR); share = inv / np.maximum(tot[ri], 1e-12)
Q = np.bincount(ri, weights=np.where(ok & ~ran, share, 0), minlength=nR); DED = np.minimum(Q, 0.9)[ri]; late_race = Q[ri] > 0
ps = np.bincount(ri, weights=np.where(ok & ran, Pm, 0.0), minlength=nR)
Pe = np.where(ok & ran, Pm / np.maximum(ps[ri], 1e-12) * (1 - Q[ri]), np.where(ok, share, 0.0))
Lg = lambda x: np.log(np.where(ok & np.isfinite(x) & (x > 0), x, 1.0))


def soft(s):
    s = np.where(ok, s, -np.inf); mx = np.full(nR, -np.inf); np.maximum.at(mx, ri, s)
    with np.errstate(all="ignore"): e = np.where(ok, np.exp(s - mx[ri]), 0.0)
    t = np.bincount(ri, weights=e, minlength=nR); return np.where(ok, e / np.maximum(t[ri], 1e-300), 0.0)


MODELS = (("FITTED: 0.28 ours + 0.88 median - 0.22 move", 0.28 * Lg(Pe) - 0.88 * Lg(med) - 0.22 * (Lg(B[:, 0]) - Lg(first))),
          ("LIVE: 0.20 ours + 1.00 TAB", 0.20 * Lg(Pe) - Lg(B[:, 0])), ("MARKET ONLY: 1.19 median", -1.19 * Lg(med)),
          ("LIVE AS BUILT: 0.20 ours + 1.00 best major price", 0.20 * Lg(Pe) - Lg(np.nanmax(np.where(np.isfinite(B), B, -1.0), 1))),
          ("LIVE WEIGHTS ON THE MEDIAN: 0.20 ours + 1.00 median", 0.20 * Lg(Pe) - Lg(med)),
          ("MORE OF OURS: 0.40 ours + 0.80 median - 0.22 move", 0.40 * Lg(Pe) - 0.80 * Lg(med) - 0.22 * (Lg(B[:, 0]) - Lg(first))))
print(f"Victoria, {min(date)} to {max(date)}: {len(np.unique(ri[ok]))} day races usable at 9am; exact late scratchings in them {int((ok & ~ran).sum())} in {len(np.unique(ri[ok & ~ran]))} races")
OUT = {}
for label, sc in MODELS:
    p = soft(sc); fp = np.where(p > 0, 1 / np.maximum(p, 1e-12), np.nan); e = ok & ran & ~fs & (fp >= 1.6) & (fp <= 15); r = B / fp[:, None]
    print(f"\n### {label}\n\n| 9am price / fair | bookie bets | runners | winners | expected | staked | profit | ROI | months up | Nov-Jun | Jul-Nov | no late scratching in the race | a late scratching |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    month = np.array([d[:7] for d in date])
    for a, b in ((0.95, 1.00), (1.00, 1.03), (1.03, 1.05), (1.05, 1.08), (1.08, 1.12), (1.12, 1.20), (1.20, 1.35), (1.35, 9), (1.05, 9), (1.08, 9)):
        hit = e[:, None] & np.isfinite(B) & (r >= a) & (r < b)
        st = np.where(hit, lim[:, None] / np.maximum(B - 1, 1e-9), 0.0); pl = np.where(hit, np.where(won[:, None], (lim * (1 - DED))[:, None], -st), 0.0)
        ru = hit.any(1); mos = sorted(set(month[ru])); up = sum(pl[month == mo].sum() > 0 for mo in mos)
        seg = lambda x: f"{int(hit[x].sum())} bets {pl[x].sum() / max(st[x].sum(), 1):+.0%}"
        print(f"| {'**' if b == 9 and a < 1.3 else ''}{a:.2f}{'x and over' if b == 9 else f'-{b:.2f}x'}{'**' if b == 9 and a < 1.3 else ''} | {int(hit.sum())} | {int(ru.sum())} | {int((ru & won).sum())} | {p[ru].sum():.0f} | ${st.sum():,.0f} | ${pl.sum():+,.0f} | {pl.sum() / max(st.sum(), 1):+.1%} | {up} of {len(mos)} | "
              f"{seg(date < '2026-07-01')} | {seg(date >= '2026-07-01')} | {seg(~late_race)} | {seg(late_race)} |")
        if (a, b) == (1.05, 9): OUT[label] = (hit.copy(), st.copy(), pl.copy(), fp.copy())
    hit, st, pl, fp = OUT[label]; nm = hit.sum(1)
    print("\n1.05x and over, by how many majors are at the take price: " + "; ".join(f"{lab}: {int(hit[(nm >= lo_) & (nm <= hi_)].sum())} bets ${pl[(nm >= lo_) & (nm <= hi_)].sum():+,.0f} ({pl[(nm >= lo_) & (nm <= hi_)].sum() / max(st[(nm >= lo_) & (nm <= hi_)].sum(), 1):+.0%})" for lab, lo_, hi_ in (("one", 1, 1), ("two or three", 2, 3), ("four or more", 4, 7))))
    print("1.05x and over, by fair price: " + "; ".join(f"${a:g}-${b:g}: {int(hit[(fp >= a) & (fp < b)].sum())} bets ${pl[(fp >= a) & (fp < b)].sum():+,.0f} ({pl[(fp >= a) & (fp < b)].sum() / max(st[(fp >= a) & (fp < b)].sum(), 1):+.0%})" for a, b in ((1.6, 3), (3, 5), (5, 8), (8, 15.01))))
    print("1.05x and over, by month: " + "; ".join(f"{mo[2:]} {int(hit[month == mo].sum())} ${pl[month == mo].sum() / 1000:+.1f}k" for mo in sorted(set(month[hit.any(1)]))))

# ---- is the book whole at 9am? A horse scratched just BEFORE 9am leaves prices that have not been re-framed yet:
# the race's 9am book adds to well under the usual 115-125% and every runner looks over the odds.
book = tot[ri]                                                    # sum of 1/median over the runners in the 9am market
pre = np.isfinite(scr) & (scr < nine)                             # scratched before 9am
mins_before = np.where(pre, nine - scr, np.nan)                   # how long before 9am
last_pre = np.full(nR, np.inf); np.minimum.at(last_pre, ri, np.where(pre, mins_before, np.inf)); lp = last_pre[ri]
npre = np.bincount(ri, weights=pre, minlength=nR)[ri]
print(f"\n## Is the 9am book whole?\n\nusable races: median book {np.median(tot[np.unique(ri[ok])]):.3f}; 5th-95th {np.percentile(tot[np.unique(ri[ok])], 5):.3f}-{np.percentile(tot[np.unique(ri[ok])], 95):.3f}; "
      f"races with a horse scratched in the 2 h before 9am: {len(np.unique(ri[ok & (lp <= 120)]))}, their median book {np.median(tot[np.unique(ri[ok & (lp <= 120)])]):.3f}")
for label in OUT:
    hit, st, pl, fp = OUT[label]
    seg = lambda x: f"{int(hit[x].sum())} bets on {int(hit[x].any(1).sum())} runners, ${pl[x].sum():+,.0f} on ${st[x].sum():,.0f} ({pl[x].sum() / max(st[x].sum(), 1):+.0%})"
    print(f"\n### {label}, 1.05x and over\n")
    print("| 9am book (sum of 1/median) | bets |\n|---|---|")
    for a, b in ((0, 1.00), (1.00, 1.08), (1.08, 1.14), (1.14, 1.20), (1.20, 9)):
        print(f"| {a:.2f}-{b:.2f} | {seg((book >= a) & (book < b))} |")
    print("\n| last scratching before 9am in the race | bets |\n|---|---|")
    for lab, x in (("none before 9am", ~np.isfinite(lp)), ("within 30 min of 9am", lp <= 30), ("30-120 min before", (lp > 30) & (lp <= 120)), ("more than 2 h before", (lp > 120) & np.isfinite(lp))):
        print(f"| {lab} | {seg(x)} |")
    clean = (book >= 1.08)
    month = np.array([d[:7] for d in date])
    mos = sorted(set(month[(hit & clean[:, None]).any(1)])); up = sum(pl[(month == mo) & clean].sum() > 0 for mo in mos)
    print(f"\nwhole books only (1.08 and over): {seg(clean)}; months up {up} of {len(mos)}; Nov-Jun {seg(clean & (date < '2026-07-01'))}; Jul-Nov {seg(clean & (date >= '2026-07-01'))}")
    r = B / fp[:, None]
    print("whole books only, by margin: " + "; ".join(f"{a:.2f}-{b:.2f}x: {int((hit & clean[:, None] & (r >= a) & (r < b)).sum())} bets {pl[(hit & clean[:, None] & (r >= a) & (r < b))].sum() / max(st[(hit & clean[:, None] & (r >= a) & (r < b))].sum(), 1):+.0%}" for a, b in ((1.05, 1.08), (1.08, 1.12), (1.12, 1.20), (1.20, 9))))

# ---- what do the short books look like? and how sure is the whole-book result (resampling race days)
hit, st, pl, fp = OUT[list(OUT)[0]]
short = np.unique(ri[hit.any(1) & (book < 1.0)])
print(f"\n## The short books: {len(short)} races. First eight, every runner the pull holds:")
for rr in short[:8]:
    ix = np.where(ri == rr)[0]
    print(f"\n{date[ix[0]]} {track[ix[0]]} R{race[ix[0]]}: 9am book {tot[rr]:.2f}, 9am was {-nine[ix[0]]:.0f} min before the jump")
    for i in ix:
        stt = "ran" if ran[i] else (f"scratched {nine[i] - scr[i]:.0f} min before 9am" if scr[i] < nine[i] else f"scratched {scr[i] - nine[i]:.0f} min after 9am")
        print(f"   {name[i][:22]:22s} {stt:32s} majors with a 9am price {int(np.isfinite(B[i]).sum())}, median {med[i] if np.isfinite(med[i]) else float('nan'):.2f}, TAB first {first[i]:.2f}, in the 9am market: {bool(ok[i])}" + (" BET" if hit[i].any() else "") + (" WON" if won[i] else ""))
rng = np.random.default_rng(7); days = np.array(sorted(set(date))); dix = {d: k for k, d in enumerate(days)}; di = np.array([dix[d] for d in date])
print("\n## How sure? 1.05x and over, whole books (1.20 and over), race days resampled 4,000 times\n\n| model | bets | runners | staked | profit | ROI | 90% range of the ROI | chance it is above zero |\n|---|---|---|---|---|---|---|---|")
for label in OUT:
    hit, st, pl, fp = OUT[label]; cl = book >= 1.20
    sd = np.bincount(di, weights=np.where(cl, st.sum(1), 0), minlength=len(days)); pd_ = np.bincount(di, weights=np.where(cl, pl.sum(1), 0), minlength=len(days))
    k = rng.integers(0, len(days), (4000, len(days))); rs = pd_[k].sum(1) / np.maximum(sd[k].sum(1), 1)
    print(f"| {label} | {int((hit & cl[:, None]).sum())} | {int((hit.any(1) & cl).sum())} | ${sd.sum():,.0f} | ${pd_.sum():+,.0f} | {pd_.sum() / sd.sum():+.1%} | {np.percentile(rs, 5):+.0%} to {np.percentile(rs, 95):+.0%} | {np.mean(rs > 0):.0%} |")

# ---- what survives of the morning's splits, on whole books with exact scratching times
labs = list(OUT); hF, sF, lF, fF = OUT[labs[0]]; hL, sL, lL, fL = OUT[labs[1]]; cl = book >= 1.20; month = np.array([d[:7] for d in date])
def row(lab, h, s_, l_, x):
    x = x & cl; ru = h.any(1) & x; mos = sorted(set(month[ru])); up = sum(l_[(month == mo) & x].sum() > 0 for mo in mos)
    return f"| {lab} | {int(h[x].sum())} | {int(ru.sum())} | {int((ru & won).sum())} | ${s_[x].sum():,.0f} | ${l_[x].sum():+,.0f} | {l_[x].sum() / max(s_[x].sum(), 1):+.1%} | {up} of {len(mos)} |"
HEAD = "| | bookie bets | runners | winners | staked | profit | ROI | months up |\n|---|---|---|---|---|---|---|---|"
inF, inL = hF.any(1), hL.any(1)
print("\n## Grades, whole books: on the live list, on the fitted list, or both\n\n" + HEAD)
print(row("A: on both lists (bet at the fitted list's prices)", hF, sF, lF, inF & inL))
print(row("B1: on the live list only", hL, sL, lL, inL & ~inF))
print(row("B2: on the fitted list only", hF, sF, lF, inF & ~inL))
hrs = -nine / 60
print("\n## The fitted list by hours from 9am to the jump, whole books\n\n" + HEAD)
for a, b in ((0, 4), (4, 5), (5, 6), (6, 7), (7, 12)):
    print(row(f"{a}-{b} h", hF, sF, lF, (hrs >= a) & (hrs < b)))
print("\n## The fitted list by the move before 9am (TAB 9am against TAB's first price), whole books\n\n" + HEAD)
mvr = B[:, 0] / first
for lab, x in (("firmed 20%+", mvr < 0.8), ("firmed 5-20%", (mvr >= 0.8) & (mvr < 0.95)), ("held", (mvr >= 0.95) & (mvr <= 1.05)), ("drifted 5%+", mvr > 1.05)):
    print(row(lab, hF, sF, lF, x))
print("\n## The fitted list by our price against the 9am median, whole books\n\n" + HEAD)
ours = 1 / np.maximum(Pe, 1e-9); rr_ = med / ours
for lab, x in (("ours longer than the market", rr_ < 1.0), ("ours up to 1.5x shorter", (rr_ >= 1.0) & (rr_ < 1.5)), ("ours 1.5-2.5x shorter", (rr_ >= 1.5) & (rr_ < 2.5)), ("ours 2.5x+ shorter", rr_ >= 2.5)):
    print(row(lab, hF, sF, lF, x))
print("\n## The fitted list by track type and day, whole books\n\n" + HEAD)
import datetime as _dt
dow = np.array([_dt.date.fromisoformat(d).weekday() for d in date])
for lab, x in (("metro", metro), ("country and provincial", ~metro), ("Saturday", dow == 5), ("Sunday", dow == 6), ("Monday-Friday", dow < 5)):
    print(row(lab, hF, sF, lF, x))
