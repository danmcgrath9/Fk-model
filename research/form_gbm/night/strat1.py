"""Betting-strategy tests on 11 months of out-of-sample prices (night of 10 Nov 2026).

Prices: the stage-1 trees walk-forward (queue1 base arm): races 1 Jan - 2 Jun 2026 priced by trees trained before 1 Jan,
races 3 Jun - 9 Nov by trees trained before 3 Jun. Stage 1 only (no network, CatBoost or second stage), so the level is a
little below the live price; the comparisons between rules are what count. Bets under the live BetMatic rules at Form
King's open (blend 0.82/0.22, minimum 0.95 x the edge price, three steps, Kelly stake capped at 10u, 16c deduction).
FOUR separate periods: Jan-17 Mar, 18 Mar-2 Jun, 3 Jun-8 Oct, 9 Oct-9 Nov (the live weeks).
A rule or a segment only counts if it points the same way in all four.
    python3.13 strat1.py   (night folder, after queue1's base arm)"""
import sys
import numpy as np
import nl, stake_rule

D, ri, nR, date, won, o, bs = nl.D, nl.ri, nl.nR, nl.date, nl.won, nl.o, nl.bs
P = np.where(date >= "2026-06-03", np.load("preds/base_A.npy"), np.load("preds/base_B.npy")).astype(float)
PER = (("Jan-17Mar", "2026-01-01", "2026-03-18"), ("18Mar-2Jun", "2026-03-18", "2026-06-03"), ("3Jun-8Oct", "2026-06-03", "2026-10-09"), ("9Oct-9Nov", "2026-10-09", "2027-01-01"))
per = np.select([(date >= lo) & (date < hi) for _, lo, hi in PER], [0, 1, 2, 3], -1)
OOS = per >= 0
rng = np.random.default_rng(7)


def bets(pm=P, edge=1.2, lo=1.6, hi=15.0, ceil=3.0, tiers=(1.0, 1.25, 1.5), edge_short=None, kelly=None, cap=None, flat=False):
    """every bet the rule strikes on the OOS races: (runner index, units, price)"""
    base = OOS & nl.race_ok[ri] & np.isfinite(bs) & (pm > 0); qq = 1 / np.maximum(pm, 1e-9)
    e = np.full(len(pm), edge) if edge_short is None else np.where(qq < 4, edge_short, edge)
    mo = 0.95 * (e / np.maximum(pm, 1e-9) ** 0.82) ** (1 / 0.78); out = []
    for i in np.where(base & (qq >= lo) & (qq <= hi) & (o >= mo) & (o < ceil * qq))[0]:
        ch = lambda t: pm[i] ** 0.82 * t ** -0.22
        ts = [mo[i] * s for s in tiers if mo[i] * s < ceil * qq[i]]; tot = prev = 0.0
        for k, t in enumerate(ts):
            tp = ts[k + 1] if k + 1 < len(ts) else t
            if kelly is None: s_ = stake_rule.stake(ch(tp), tp)
            else:
                kk = max(0.0, ((ch(tp) * tp) ** 0.5 - 1) / (tp - 1)); s_ = round(min(cap or 10.0, kelly * kk * 5 / 8), 2)
            add = max(0.0, s_ - prev); prev = max(prev, s_)
            if o[i] >= t: tot += add
        if tot > 0: out.append((i, 1.0 if flat else tot, o[i]))
    a = np.array(out); return a[:, 0].astype(int), a[:, 1], a[:, 2]


def pl(idx, st, pr): return np.where(won[idx], st * (pr - 1) * (1 - nl.DED), -st)


def line(lab, idx, st, pr):
    u = pl(idx, st, pr); cells = []
    for k in range(4):
        m = per[idx] == k; cells.append(f"{int(m.sum()):4d} {u[m].sum():+7.1f}u {100*u[m].sum()/max(st[m].sum(),1e-9):+5.0f}%")
    print(f"| {lab} | " + " | ".join(cells) + f" | {len(idx)} {u.sum():+.1f}u {100*u.sum()/st.sum():+.0f}% |")


HDR = "| rule | " + " | ".join(p[0] for p in PER) + " | all |\n|---|---|---|---|---|---|"
I0, S0, P0 = bets()
print(f"OOS races {len(np.unique(ri[OOS]))}, runners {int(OOS.sum())}; baseline bets {len(I0)}\n")
print("1. THE EDGE (minimum = 0.95 x edge price); cells: bets, profit, ROI on stakes\n" + HDR)
for e in (1.05, 1.10, 1.15, 1.20, 1.25, 1.30, 1.40, 1.50): line(f"edge {e:.2f}" + (" (live)" if e == 1.2 else ""), *bets(edge=e))
line("edge 1.20, 1.15 where we price under $4 (live sheet)", *bets(edge_short=1.15))
line("edge 1.20, 1.10 under $4", *bets(edge_short=1.10))
print("\n2. THE PRICE RANGE (our price), edge 1.20\n" + HDR)
for lo, hi in ((1.6, 8), (1.6, 10), (1.6, 12), (1.6, 15), (1.6, 20), (1.6, 30), (2.0, 15), (3.0, 15), (1.3, 15)): line(f"ours ${lo}-${hi}" + (" (live)" if (lo, hi) == (1.6, 15) else ""), *bets(lo=lo, hi=hi))
print("\n3. THE CEILING (no bet when the open is this many times our price)\n" + HDR)
for c in (1.8, 2.2, 3.0, 4.0, 99): line(f"under {c}x" + (" (live)" if c == 3 else ""), *bets(ceil=c))
print("\n4. THE STEPS (order ladder at multiples of the minimum)\n" + HDR)
for t in ((1.0,), (1.0, 1.25), (1.0, 1.25, 1.5), (1.0, 1.15, 1.3, 1.5), (1.0, 1.5, 2.0)): line(f"steps {t}" + (" (live)" if t == (1.0, 1.25, 1.5) else ""), *bets(tiers=t))
print("\n5. THE STAKE (Kelly multiplier and cap; live 125 and 10u)\n" + HDR)
for k, c in ((125, 10), (125, 5), (125, 20), (60, 10), (250, 10), (250, 20)): line(f"Kelly x{k}, cap {c}u" + (" (live)" if (k, c) == (125, 10) else ""), *bets(kelly=k, cap=c))
line("flat 1u a bet", *bets(flat=True))

print("\n6. BY STAKE SIZE (the live rule's own stakes): does the return rise with the stake?\n" + HDR)
for lo, hi in ((0, 0.5), (0.5, 1), (1, 2), (2, 4), (4, 7), (7, 10.01)):
    m = (S0 >= lo) & (S0 < hi); line(f"stake {lo}-{hi:g}u", I0[m], S0[m], P0[m])

print("\n7. PRICE TAKEN AGAINST BETFAIR SP, by period: share of bets that beat BSP, median open/BSP, and the same bets flat at BSP (8% commission)")
for k, (nm_, _, _) in enumerate(PER):
    m = per[I0] == k; r = P0[m] / bs[I0[m]]; ub = np.where(won[I0[m]], (bs[I0[m]] - 1) * 0.92, -1.0)
    print(f"  {nm_:11s} {int(m.sum()):4d} bets  beat BSP {100*np.mean(r > 1):.0f}%  median open/BSP {np.median(r):.2f}  flat at BSP {ub.sum():+.1f}u ({100*ub.mean():+.0f}%)  flat at the open {pl(I0[m], np.ones(m.sum()), P0[m]).sum():+.1f}u")

# ---- 8. segments of the live rule's bets -----------------------------------------------------------------------------
X, cols = D["X"], list(D["cols"]); col = lambda n: X[:, cols.index(n)].astype(float)
F, NM = nl.F, nl.NM; fc = lambda n: F[:, NM.index(n)].astype(float)
track = np.char.lower(D["track"][ri].astype(str)); METRO = ("flemington", "caulfield", "caulfield heath", "moonee valley", "sandown hillside", "sandown lakeside")
dist = D["distance"][ri].astype(float); going = D["going"][ri].astype(float); field = nl.field
fs_in_race = np.bincount(ri, weights=(col("firstStarter") == 1), minlength=nR)[ri]
qq = 1 / np.maximum(P, 1e-9); ov = o / qq
rank_ours = np.zeros(len(ri)); rank_open = np.zeros(len(ri))
for a_, v in ((rank_ours, -P), (rank_open, np.where(np.isfinite(o), o, 1e9))):
    order = np.lexsort((v, ri)); a_[order] = np.arange(len(ri)) - np.searchsorted(ri[order], ri[order])
import datetime as dt
dow = np.array([dt.date.fromisoformat(d).weekday() for d in nl.rdate])[ri]
starts, age, prep, days = fc("f_careerForm_s"), col("age"), col("raceInPrep"), col("daysSinceLastRace")
pred, bar = fc("sm_predicted_position"), col("barrier")
SEG = {}
def band(name, v, edges, fmt="{}-{}"):
    for lo, hi in zip(edges[:-1], edges[1:]): SEG[f"{name} " + fmt.format(lo, hi)] = (v >= lo) & (v < hi)
band("open $", o, [1, 3, 5, 8, 12, 20, 1e9]); band("ours $", qq, [1, 3, 5, 8, 15.01]); band("overlay x", ov, [1, 1.4, 1.7, 2.2, 3.01])
band("field", field, [1, 8, 11, 14, 99]); band("distance", dist, [0, 1101, 1301, 1601, 2001, 9999]); band("going", going, [0, 4.5, 6.5, 99])
band("first starters in race", fs_in_race, [0, 1, 2, 99]); band("career starts", np.nan_to_num(starts, nan=0), [0, 3, 6, 16, 999]); band("age", age, [2, 3, 4, 5, 99])
band("run in prep", np.nan_to_num(prep, nan=0), [1, 2, 3, 4, 99]); band("days since run", np.nan_to_num(days, nan=999), [0, 14, 29, 61, 9999])
band("barrier", bar, [1, 4, 7, 10, 99]); band("speedmap position", pred, [1, 2, 4, 7, 99]); band("our rank in race", rank_ours + 1, [1, 2, 3, 5, 99])
band("open rank in race", rank_open + 1, [1, 2, 4, 7, 99])
SEG["metro"] = np.isin(track, METRO); SEG["not metro"] = ~SEG["metro"]; SEG["Saturday"] = dow == 5; SEG["Sunday-Friday"] = dow != 5
SEG["jockey's only ride"] = nl.only; SEG["apprentice claim"] = np.nan_to_num(col("apprenticeClaim"), nan=0) > 0
SEG["gear first time"] = np.nan_to_num(fc("gear_first_time"), nan=0) > 0; SEG["blinkers first"] = np.nan_to_num(col("blinkers_first"), nan=0) > 0
SEG["class up (prize up 25%+)"] = fc("x_prize_change") > 0.22; SEG["class down (prize down 25%+)"] = fc("x_prize_change") < -0.22
SEG["beat its price last start"] = fc("beat_market_last") >= 0.05; SEG["missed its price last start"] = fc("beat_market_last") <= -0.05
SEG["longer trip than last start"] = fc("dist_change") > 150; SEG["shorter trip than last start"] = fc("dist_change") < -150
SEG["mare/filly"] = np.isin(col("sex"), (2, 3)) if np.nanmax(col("sex")) > 1 else col("sex") == 1
SEG["we are the top pick AND open favourite"] = (rank_ours == 0) & (rank_open == 0)
SEG["2yo race or maiden with first starters"] = (age == 2) | (fs_in_race >= 2)
U0 = pl(I0, S0, P0); SIMS = 2000
print(f"\n8. SEGMENTS of the live rule's {len(I0)} bets. A segment is flagged only if it sits in the same tail in ALL FOUR periods:")
print("   against random draws of the same number of bets from the same period (pct = share of draws it beat). Luck would flag about "
      f"{2 * len(SEG) * 0.3 ** 4:.1f} of {len(SEG)}.")
rows = []
for name, mask in SEG.items():
    m = np.nan_to_num(mask[I0].astype(float), nan=0) > 0; pcts, cells = [], []
    for k in range(4):
        pk = per[I0] == k; mk = m & pk; n = int(mk.sum())
        if n < 8: pcts.append(np.nan); cells.append(f"{n:3d}      -"); continue
        roi = U0[mk].sum() / S0[mk].sum(); pool_u, pool_s = U0[pk], S0[pk]
        draws = np.array([rng.choice(len(pool_u), n, replace=False) for _ in range(SIMS)])
        sim = pool_u[draws].sum(1) / pool_s[draws].sum(1); pcts.append(float(np.mean(sim < roi))); cells.append(f"{n:3d} {100*roi:+5.0f}% p{100*pcts[-1]:3.0f}")
    rows.append((name, pcts, cells, int(m.sum()), U0[m].sum(), S0[m].sum()))
print("| segment | " + " | ".join(p[0] for p in PER) + " | all: bets, profit, ROI | flag |\n|---|---|---|---|---|---|---|")
for name, pcts, cells, n, u, s in rows:
    ok = not any(np.isnan(pcts)); flag = "WEAK in all four" if ok and max(pcts) < 0.30 else "STRONG in all four" if ok and min(pcts) > 0.70 else ""
    print(f"| {name} | " + " | ".join(cells) + f" | {n} {u:+.1f}u {100*u/max(s,1e-9):+.0f}% | {flag} |")
