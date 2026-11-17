"""c_timing.py: how long the 9am prices last, and whether a later list is worth making (18 Nov 2026).
Fair price = the walk-forward 'ours + market + move' fit at 9:00am (b_nomodel.py), frozen for the day. Test months
Nov 2025 - Nov 2026. TAB's price and the best major price are read off their paths at later clock times."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
p = np.load(os.path.join(HERE, "fair_move.npy")); fp = np.where(p > 0, 1 / np.maximum(p, 1e-12), np.nan)
test = (p > 0) & (month >= "2025-11"); e = test & ran & ~fs & (fp >= 1.6) & (fp <= 15); take = 1.05 * fp
with np.errstate(all="ignore"):
    best9 = np.nanmax(np.where(np.isfinite(B7), B7, -np.inf), 1)
sel = e & (best9 >= take)                                      # on the 9am list: some major at the take price or better
print(f"on the 9am list: {int(sel.sum())} runners; TAB at the take price at 9:00: {int((sel & (T9 >= take)).sum())}")
OFF = (0, 1, 2, 5, 10, 20, 30, 60, 120, 180)
idx = np.where(sel)[0]
TP = np.array([[price_at(tab[i], nine[i] + o) for o in OFF] for i in idx]); MP = np.array([[price_at(maj[i], nine[i] + o) for o in OFF] for i in idx])
tk = take[idx]; w_ = won[idx]; lm_ = lim[idx]; dd = DED[idx]; left = -nine[idx]          # minutes from 9am to the jump
print("\n### How long the price lasts after 9:00am (runners on the 9am list)\n\n| minutes after 9:00 | best major price still at the take price | median best major / its 9:00 price | TAB still at the take price (of those where it was) | median TAB / its 9:00 price |\n|---|---|---|---|---|")
t_in = TP[:, 0] >= tk
for j, o in enumerate(OFF):
    live = left > o
    print(f"| {o} | {np.mean(MP[live, j] >= tk[live]):.0%} | {np.nanmedian(MP[live, j] / MP[live, 0]):.3f} | {np.mean(TP[live & t_in, j] >= tk[live & t_in]):.0%} | {np.nanmedian(TP[live & t_in, j] / TP[live & t_in, 0]):.3f} |")

def roi(price, m):
    st = np.where(m, lm_ / np.maximum(price - 1, 1e-9), 0); pl = np.where(m, np.where(w_, lm_ * (1 - dd), -st), 0)
    return f"{int(m.sum())} bets, {int((m & w_).sum())} won, ${pl.sum():+,.0f}, {pl.sum() / max(st.sum(), 1):+.0%}"
print("\n### The 9am list bet LATE, one bet at the best major price then, if it is still at the take price\n\n| bet at | result |\n|---|---|")
for j, o in enumerate(OFF):
    m = (MP[:, j] >= tk) & (left > o); print(f"| 9:00 + {o} min | {roi(MP[:, j], m)} |")
print("\nand taking whatever the best major price is then (no take price): " + "; ".join(f"+{o} min {roi(MP[:, j], np.isfinite(MP[:, j]) & (MP[:, j] > 1) & (left > o))}" for j, o in enumerate(OFF) if o in (0, 10, 60, 180)))

# Later lists: runners NOT on the 9am list whose best major price reaches the (9am) take price later in the day
print("\n### Runners that reach the take price AFTER 9am (not on the 9am list), bet at the best major price when first seen\n\n| first seen by | runners | result at the best major price then |\n|---|---|---|")
cand = np.where(e & ~sel & np.isfinite(best9))[0]
CL = (15, 30, 60, 120, 180, 240)                               # minutes after 9:00
first_t = np.full(len(cand), np.nan); first_p = np.full(len(cand), np.nan)
for a, i in enumerate(cand):
    pth = maj[i]
    if pth is None: continue
    k0 = np.searchsorted(pth[0], nine[i], side="right"); t_end = min(-2.0, 0.0)          # stop two minutes before the jump
    for k in range(k0, len(pth[0])):
        if pth[0][k] > t_end: break
        if pth[1][k] >= take[i]:
            first_t[a] = pth[0][k] - nine[i]; first_p[a] = pth[1][k]; break
cw, cl, cd = won[cand], lim[cand], DED[cand]
def roi2(m):
    st = np.where(m, cl / np.maximum(first_p - 1, 1e-9), 0); pl = np.where(m, np.where(cw, cl * (1 - cd), -st), 0)
    return f"{int(m.sum())} | {int((m & cw).sum())} won, staked ${st.sum():,.0f}, ${pl.sum():+,.0f}, {pl.sum() / max(st.sum(), 1):+.0%}"
prev = 0
for c in CL + (100000,):
    m = np.isfinite(first_t) & (first_t > prev) & (first_t <= c)
    print(f"| {'9:00 + ' + str(c) + ' min' if c < 100000 else 'later, to 2 min before the jump'} | {roi2(m)} |"); prev = c
print(f"| all after 9:00 | {roi2(np.isfinite(first_t))} |")
by = lambda lab, m: print(f"| {lab} | {roi2(np.isfinite(first_t) & m)} |")
dr = first_p / best9[cand]
by("reached it by drifting 5%+ from its 9:00 best price", dr >= 1.05); by("reached it with under 5% drift", dr < 1.05)
