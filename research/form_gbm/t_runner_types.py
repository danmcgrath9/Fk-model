"""Runner TYPES worth backing (10 Nov 2026, founder: "Maybe a type of runner we back? Big sectionals? Pace against etc").
No model: each type is read off Form King's figures from before the race (last start's sectionals, where it settled,
how it finished, today's speedmap, the run in the prep, gear). Backed two ways: at Form King's OPENING price (fixed odds,
what our TAB open bets take, no commission) and at Betfair SP (8% commission on a winner). 1u a bet, first starters out.

Four separate periods, 16 months: P1 Jul-Dec 2025, P2 Jan-May 2026, P3 Jun-8 Oct 2026, LIVE 9 Oct-9 Nov 2026 (the
dataset rebuilt 10 Nov from every resulted race). A type HOLDS in a band if it makes money in all four with 25+ bets in
each. The luck baseline: each band's own back-every-runner rate in each period, 200 draws.
    python3.13 t_runner_types.py DATASET.npz"""
import sys
import numpy as np

z = np.load(sys.argv[1], allow_pickle=True)
ri = z["race_idx"]; nR = int(ri.max()) + 1; rdate = z["date"].astype(str); date = rdate[ri]
cols = list(map(str, z["cols"])); X = z["X"]; col = lambda n: X[:, cols.index(n)]
P = z["P"]; pf = list(map(str, z["past_fields"]))
bs = z["bsp"].astype(float); op = z["open"].astype(float); won = z["finish"] == 1
fs = col("firstStarter") == 1
field = np.bincount(ri, minlength=nR)[ri]
one_winner = (np.bincount(ri, weights=won.astype(float), minlength=nR) == 1)[ri]

# last start (most recent non-trial run with a finish)
tr, fin, mar, rel = P[:, :, pf.index("trial")], P[:, :, pf.index("finish")], P[:, :, pf.index("margin")], np.isfinite(P[:, :, pf.index("finish")])
real = rel & ~(np.nan_to_num(tr) > 0)
k0 = np.where(real.any(1), real.argmax(1), -1)
last_fin = np.where(k0 >= 0, fin[np.arange(len(k0)), np.maximum(k0, 0)], np.nan)
last_mar = np.where(k0 >= 0, mar[np.arange(len(k0)), np.maximum(k0, 0)], np.nan)

l600, fsp, spd = col("last600_rel"), col("finish_speed_rel"), col("speed_rel")
settle, gain = col("raw_settle_share"), col("raw_pos_gain")
pred, habit, prep = col("sm_predicted_position"), col("map_vs_habit"), col("raceInPrep")
gear, beatm = col("gear_first_time"), col("beat_market_last")
close = (last_mar <= 2) & (last_fin > 1)
TYPES = {
    "best closing 600m in the field last start": l600 >= -0.25,
    "closing 600m within 1 of the best": l600 >= -1.0,
    "best finishing speed in the field": fsp >= -0.25,
    "best speed rating in the field": spd >= -0.25,
    "settled back last start (back 35%)": settle >= 0.65,
    "led last start (front 15%)": settle <= 0.15,
    "ran on from the back (gained 25%+)": (settle >= 0.6) & (gain >= 0.25),
    "pace against: back and beaten <= 2L": (settle >= 0.6) & close,
    "led and beaten <= 2L": (settle <= 0.2) & close,
    "big 600m and beaten <= 2L": (l600 >= -1.0) & close,
    "speedmap: leader today": pred == 1,
    "speedmap: on pace today (1-3)": pred <= 3,
    "speedmap: back today": pred >= 0.6 * field,
    "pace against last time, on pace today": (settle >= 0.6) & close & (pred <= 3),
    "map well forward of habit": habit >= 0.2,
    "map well behind habit": habit <= -0.2,
    "first-up": prep == 1,
    "second-up": prep == 2,
    "third-up": prep == 3,
    "gear first time": gear > 0,
    "beat its price last start": beatm >= 0.05,
    "won last start": last_fin == 1,
    "placed 2nd-3rd last start": (last_fin >= 2) & (last_fin <= 3),
}
CTX = {"": np.ones(len(bs), bool), "metro": np.isin(np.char.lower(z["track"][ri].astype(str)),
                                                       ["flemington", "caulfield", "caulfield heath", "moonee valley", "sandown hillside", "sandown lakeside"])}
CTX["country/provincial"] = ~CTX["metro"]
PER = np.select([date < "2026-01-01", date < "2026-06-01", date < "2026-10-09"], ["P1", "P2", "P3"], "LIVE")
PERS = ("P1", "P2", "P3", "LIVE")
BANDS = ((2, 4), (4, 7), (7, 12), (12, 25))
rng = np.random.default_rng(11)
MIN_N, SIMS = 25, 200


def bet(price, w, kind):
    return np.where(w, (price - 1) * (0.92 if kind == "BSP" else 1.0), -1.0)


print(f"{len(bs)} runners, {nR} races; per period: " + ", ".join(f"{p} {np.sum(PER == p)}" for p in PERS))
out, sims, tried = [], np.zeros(SIMS), 0
for kind in ("OPEN", "BSP"):
    price = op if kind == "OPEN" else bs
    valid = np.isfinite(price) & (price > 1) & ~fs & one_winner
    base = {}
    print(f"\nBACK EVERY RUNNER at {kind} (the luck baseline):")
    for lo, hi in BANDS:
        cells = []
        for p in PERS:
            sel = valid & (price >= lo) & (price < hi) & (PER == p)
            e = np.sum(1 / price[sel]); base[(lo, hi, p)] = won[sel].sum() / e; u = bet(price[sel], won[sel], kind).sum()
            cells.append(f"{p} A/E {base[(lo, hi, p)]:.2f} {100*u/sel.sum():+.0f}%")
        print(f"  ${lo}-${hi:<3} " + " | ".join(cells))
    for tn, tm in TYPES.items():
        for xn, xm in CTX.items():
            for lo, hi in BANDS:
                stats, spos = [], np.ones(SIMS, bool)
                for p in PERS:
                    sel = valid & np.nan_to_num(tm, nan=0).astype(bool) & xm & (price >= lo) & (price < hi) & (PER == p)
                    pr, w = price[sel], won[sel]; u = bet(pr, w, kind).sum()
                    q = np.clip(base[(lo, hi, p)] / pr, 0, 1)
                    sw = rng.random((SIMS, len(pr))) < q
                    su = np.where(sw, (pr - 1) * (0.92 if kind == "BSP" else 1.0), -1.0).sum(1)
                    spos &= su > 0
                    stats.append((len(pr), int(w.sum()), float(np.sum(1 / pr)), float(u), float(np.mean(su >= u)) if len(pr) else 1.0))
                if min(s[0] for s in stats) < MIN_N: continue
                tried += 1; sims += spos
                if all(s[3] > 0 for s in stats):
                    out.append((float(np.prod([s[4] for s in stats])), kind, lo, hi, tn, xn, stats))
print(f"\n{tried} type x band rules with {MIN_N}+ bets in every period; {len(out)} made money in all four. "
      f"By luck alone: {sims.mean():.1f} (90% of draws {np.percentile(sims, 5):.0f}-{np.percentile(sims, 95):.0f})\n")
print("p = chance a no-skill draw does as well in all four periods (smaller is better)")
for pj, kind, lo, hi, tn, xn, st in sorted(out):
    n = sum(s[0] for s in st); w = sum(s[1] for s in st); e = sum(s[2] for s in st); u = sum(s[3] for s in st)
    print(f"{pj:.6f} BACK at {kind:4} ${lo}-${hi:<3} {tn}{' | ' + xn if xn else ''}\n          "
          + " | ".join(f"{p} {s[0]:4d} {s[1]:3d} ({s[2]:5.1f}) {s[3]:+6.1f}u" for p, s in zip(PERS, st))
          + f" | all {n} bets {w} won ({e:.1f}) {u:+.1f}u ({100*u/n:+.0f}%)")
