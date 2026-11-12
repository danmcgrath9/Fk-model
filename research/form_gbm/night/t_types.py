"""Bet types at BSP and at 9am (12 Nov 2026, founder: "What about certain types of bets?"). The 10 Nov challenger's
out-of-fold blend (p_oof_chal.npy), first starters out, our price $1.60-$15, 1u flat.
  BSP (all 16 months, 1 Jul 2025 - 9 Nov 2026, six periods): (a) the open book's bets (value at the open) struck at BSP;
      (b) value AT BSP (BSP >= 1.3x our price), struck at BSP. 8% commission on a winner.
  9AM (the timed races only, two blocks): (c) the open book's bets struck at 9am race day; (d) value AT 9am (9am price
      >= 1.3x ours) struck at 9am. No deduction.
Every type is a split of race or runner: course group, distance, class (lws), field, going, barrier, days since the last
run, age, apprentice, our rank in the race, the market's rank at the open. About 40 types x 4 books are tried, so a few
will look good by luck: a type only counts with 150+ bets and positive in at least 5 of the 6 periods (BSP) or both
blocks (9am).
    python3.13 t_types.py FLUC_MINUTES.md   (night folder)"""
import csv, io, sys
import numpy as np

z = np.load("ds/model_ds.npz", allow_pickle=True); P = np.load("p_oof_chal.npy").astype(float)
ri = z["race_idx"]; nR = len(z["race_id"]); date = z["date"].astype(str)[ri]; rid = z["race_id"].astype(str)[ri]
hid = z["horse_id"].astype(str); won = np.asarray(z["finish"], float) == 1; cols = list(z["cols"]); X = z["X"]
col = lambda n: X[:, cols.index(n)].astype(float)
o = np.asarray(z["open"], float); bs = np.asarray(z["bsp"], float); fsr = col("firstStarter") == 1
okp = np.isfinite(o) & (o > 1); race_ok = np.bincount(ri, weights=~okp, minlength=nR) == 0
track = z["track"].astype(str)[ri]; dist = np.asarray(z["distance"], float)[ri]; lws = np.asarray(z["lws"], float)[ri]
going = np.asarray(z["going"], float)[ri]; field = np.bincount(ri, minlength=nR)[ri]
bar = col("barrier"); days = col("daysSinceLastRace"); age = col("age"); appr = col("apprenticeJockey")
ours = 1 / np.maximum(P, 1e-9); mo = 0.95 * (1.2 / np.maximum(P, 1e-9) ** 0.82) ** (1 / 0.78)
rank = lambda v: np.array([0] * len(v))
# rank within the race (1 = shortest)
def race_rank(v):
    out = np.zeros(len(v), int)
    for r in range(nR):
        idx = np.where(ri == r)[0]
        if len(idx): out[idx[np.argsort(v[idx])]] = np.arange(1, len(idx) + 1)
    return out
our_rank = race_rank(ours); mkt_rank = race_rank(np.where(np.isfinite(o), o, 999))
METRO = {"Flemington", "Caulfield", "Moonee Valley", "Sandown Hillside", "Sandown Lakeside", "The Valley", "Sandown"}
PROV = {"Geelong", "Ballarat", "Ballarat Synthetic", "Bendigo", "Cranbourne", "Pakenham", "Pakenham Synthetic", "Mornington",
        "Kilmore", "Seymour", "Sale", "Warrnambool", "Kyneton", "Echuca", "Wangaratta", "Yarra Valley", "Moe", "Werribee"}
grp = np.array(["metro" if t in METRO else "provincial" if t in PROV else "country" for t in track])
s = open(sys.argv[1]).read(); a = s.find("CSV-BEGIN") + 9; b = s.find("CSV-END")
key = {(r["race_id"], r["horse_id"]): r for r in csv.DictReader(io.StringIO(s[a:b].strip()))}
p9 = np.array([float(key[(rid[i], hid[i])]["c0900"]) if (rid[i], hid[i]) in key and key[(rid[i], hid[i])]["c0900"] else np.nan
               for i in range(len(ri))])
core = race_ok[ri] & ~fsr & (P > 0) & (ours >= 1.6) & (ours <= 15)
open_book = core & (o >= mo) & (o < 6 * ours)
PER = [("2025-07-01", "2025-10-01"), ("2025-10-01", "2026-01-01"), ("2026-01-01", "2026-04-01"), ("2026-04-01", "2026-07-01"),
       ("2026-07-01", "2026-10-01"), ("2026-10-01", "2027-01-01")]
BLK = [("2025-07-01", "2026-01-01"), ("2026-01-01", "2027-01-01")]
rb = np.where(won, (bs - 1) * 0.92, -1.0); r9 = np.where(won, p9 - 1, -1.0)
BOOKS = {"open book at BSP": (open_book & np.isfinite(bs) & (bs > 1), rb, PER),
         "value at BSP": (core & np.isfinite(bs) & (bs >= 1.3 * ours), rb, PER),
         "open book at 9am": (open_book & np.isfinite(p9), r9, BLK),
         "value at 9am": (core & np.isfinite(p9) & (p9 >= 1.3 * ours), r9, BLK)}
TYPES = [("all", np.ones(len(ri), bool))]
TYPES += [(f"course: {g_}", grp == g_) for g_ in ("metro", "provincial", "country")]
TYPES += [("distance <=1100m", dist <= 1100), ("distance 1101-1400m", (dist > 1100) & (dist <= 1400)),
          ("distance 1401-1800m", (dist > 1400) & (dist <= 1800)), ("distance 1801m+", dist > 1800)]
q = np.nanpercentile(lws, [33, 67])
TYPES += [("class: low (lws)", lws <= q[0]), ("class: middle", (lws > q[0]) & (lws <= q[1])), ("class: high", lws > q[1])]
TYPES += [("field <=8", field <= 8), ("field 9-11", (field >= 9) & (field <= 11)), ("field 12+", field >= 12)]
TYPES += [("going good", going == 1), ("going soft/heavy", (going == 2) | (going == 3)), ("synthetic", going == 4)]
TYPES += [("barrier 1-3", bar <= 3), ("barrier 4-8", (bar >= 4) & (bar <= 8)), ("barrier 9+", bar >= 9)]
TYPES += [("fit (<=21 days)", days <= 21), ("22-69 days", (days > 21) & (days < 70)), ("first-up (70+ days)", days >= 70)]
TYPES += [("age 2-3", age <= 3), ("age 4-5", (age >= 4) & (age <= 5)), ("age 6+", age >= 6)]
TYPES += [("apprentice rider", appr == 1), ("senior rider", appr != 1)]
TYPES += [("our top pick", our_rank == 1), ("our 2nd-3rd", (our_rank >= 2) & (our_rank <= 3)), ("our 4th+", our_rank >= 4)]
TYPES += [("market fav at open", mkt_rank == 1), ("market 2nd-3rd at open", (mkt_rank >= 2) & (mkt_rank <= 3)), ("market 4th+ at open", mkt_rank >= 4)]

found = []
for bk, (base, r_, per) in BOOKS.items():
    print(f"\n## {bk}\n\n| type | bets | ROI | periods positive | " + " | ".join(f"{lo[:7]}" for lo, _ in per) + " |\n|---|---|---|---|" + "---|" * len(per))
    for lab, m in TYPES:
        mm = base & m; n = int(mm.sum())
        if n < 50: continue
        cells, pos, used = [], 0, 0
        for lo, hi in per:
            pm = mm & (date >= lo) & (date < hi)
            if pm.sum() >= 15:
                v = r_[pm].mean(); cells.append(f"{100 * v:+.0f}%"); used += 1; pos += v > 0
            else:
                cells.append("-")
        roi = r_[mm].mean()
        print(f"| {lab} | {n} | {100 * roi:+.1f}% | {pos} of {used} | " + " | ".join(cells) + " |")
        need = 5 if per is PER else 2
        if n >= 150 and roi > 0 and pos >= min(need, used) and used >= (5 if per is PER else 2):
            found.append(f"{bk}: {lab}, {n} bets, {100 * roi:+.1f}%, {pos} of {used} periods positive")
print("\n## Types that pass (150+ bets, positive overall and in 5 of 6 periods / both blocks)\n")
print("\n".join(found) if found else "none")
