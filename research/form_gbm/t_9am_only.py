"""Bet only at 9:30am race day, nothing at the open (25 Oct 2026, founder: "a test of only betting at 9am, so finding
ways we can blend our model, not taking into account our opening prices, and only betting at 9am. I don't want this
live just on the side").
Races: every resulted VIC race since 3 Oct 2026 with Form King's timed flucs (scripts/fluc_timing.py: am930 = the price
standing at 9:30am race day) and a live price from our model (data/live_bets/*-v6.json, p_model = the model BEFORE any
blend with the open). Starters only; our chances renormalised over them; the 9:30 market's chances normalised.
Blend: chance = normalise(ours^a x market930^b), a and b fitted by maximum likelihood on one half of the race days and
scored on the other (both ways). Bets: blended chance x 9:30 price >= 1 + edge, blended price $1.60-$15. Settled at the
9:30 price (struck after the scratchings, so no deduction; a later scratching is ignored, which flatters slightly),
flat 1u, beside the same horses at BSP (8% commission).
python3.13 t_9am_only.py TIMING.csv"""
import csv, glob, json, math, os, sys, collections
import numpy as np
L = "/home/user/fk-model/data/live_bets"
pm = {}
for fn in sorted(glob.glob(f"{L}/2026-10-*-v6.json")):
    for r in json.load(open(fn)): pm[(str(r["race_id"]), str(r["horse_id"]))] = r.get("p_model", r["p"])
T = [t for t in csv.DictReader(open(sys.argv[1]))]
f = lambda v: float(v) if v not in ("", None, "None") else None
races = collections.defaultdict(list)
for t in T:
    if t.get("scratched") in ("1", "True", "true"): continue
    races[t["race_id"]].append(t)
R = []
for rid, rs in races.items():
    ok = [t for t in rs if f(t["am930"]) and f(t["am930"]) > 1 and f(t["bsp"]) and f(t["bsp"]) > 1 and (rid, t["horse_id"]) in pm and t["finish"] not in ("", None)]
    if len(ok) < 4 or len(ok) < len(rs) - 1 or not any(t["finish"] == "1" for t in ok): continue
    p = np.array([pm[(rid, t["horse_id"])] for t in ok]); p = p / p.sum()
    m = np.array([1 / f(t["am930"]) for t in ok]); m = m / m.sum()
    dd = rid.split("_")[1]; day = f"20{dd[4:6]}-{dd[2:4]}-{dd[0:2]}"   # race ids carry DDMMYY; jump_mel is a time only
    R.append(dict(rid=rid, day=day, p=p, m=m, px=np.array([f(t["am930"]) for t in ok]),
                  bsp=np.array([f(t["bsp"]) for t in ok]), won=np.array([t["finish"] == "1" for t in ok])))
days = sorted(set(r["day"] for r in R)); half = {d: i % 2 for i, d in enumerate(days)}   # alternate days, so both halves span the period
print(f"{len(R)} races, {sum(len(r['p']) for r in R)} runners, {len(days)} days ({days[0]} to {days[-1]})")
def blend(r, a, b):
    q = np.exp(a * np.log(np.maximum(r["p"], 1e-9)) + b * np.log(np.maximum(r["m"], 1e-9))); return q / q.sum()
def ll(rs, a, b): return -np.mean([np.log(blend(r, a, b)[r["won"]][0]) for r in rs])
def fit(rs):
    best = None
    for a in np.arange(0, 0.81, 0.05):
        for b in np.arange(0.5, 1.31, 0.05):
            v = ll(rs, a, b)
            if best is None or v < best[0]: best = (v, a, b)
    return best[1], best[2]
def kl(rs, q):
    out = []
    for r in rs:
        qb = 1 / r["bsp"]; qb = qb / qb.sum(); x = q(r); out.append(np.sum(qb * np.log(qb / np.maximum(x, 1e-12))))
    return np.mean(out)
print("\n| test half | fitted on | a (ours) | b (market 9:30) | KL to BSP: ours | 9:30 market | blend | winner log loss: 9:30 market | blend |\n|---|---|---|---|---|---|---|---|---|")
W = {}
for h in (0, 1):
    tr = [r for r in R if half[r["day"]] != h]; te = [r for r in R if half[r["day"]] == h]
    a, b = fit(tr); W[h] = (a, b)
    print(f"| {h} | other half | {a:.2f} | {b:.2f} | {kl(te, lambda r: r['p']):.4f} | {kl(te, lambda r: r['m']):.4f} | {kl(te, lambda r: blend(r, a, b)):.4f} | {ll(te, 0, 1):.4f} | {ll(te, a, b):.4f} |")
bk = np.array([np.sum(1 / r["px"]) for r in R]); print(f"9:30 corporate book: median {np.median(bk):.3f}, mean {bk.mean():.3f}")
print("\n| rule | half | bets | won | flat ROI at 9:30 price | same horses at BSP | median 9:30 / BSP |\n|---|---|---|---|---|---|---|")
for edge in (0.10, 0.20, 0.30):
    for name, use_blend in (("blend", True), ("ours alone", False)):
        tot = [0, 0, 0.0, 0.0]
        for h in (0, 1):
            a, b = W[h]; n = w = 0; p930 = pb = 0.0; rat = []
            for r in R:
                if half[r["day"]] != h: continue
                q = blend(r, a, b) if use_blend else r["p"]
                sel = (q * r["px"] >= 1 + edge) & (1 / q >= 1.6) & (1 / q <= 15)
                for i in np.where(sel)[0]:
                    n += 1; w += r["won"][i]; rat.append(r["px"][i] / r["bsp"][i])
                    p930 += (r["px"][i] - 1) if r["won"][i] else -1; pb += ((r["bsp"][i] - 1) * 0.92) if r["won"][i] else -1
            print(f"| {name}, value {int(edge*100)}c+ | {h} | {n} | {w} | {100*p930/max(n,1):+.0f}% | {100*pb/max(n,1):+.0f}% | {np.median(rat) if rat else float('nan'):.2f} |")
            tot[0] += n; tot[1] += w; tot[2] += p930; tot[3] += pb
        print(f"| {name}, value {int(edge*100)}c+ | both | {tot[0]} | {tot[1]} | {100*tot[2]/max(tot[0],1):+.0f}% | {100*tot[3]/max(tot[0],1):+.0f}% | |")
