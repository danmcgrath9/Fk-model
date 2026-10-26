"""What works as a betting proposition 30-60 minutes after the open (26 Oct 2026, founder: "what would a sharp betting
strategy look like ... when we bet 30-60 minutes after markets open. Because that's when all the books open and we can
spread"). Input: fluc_windows.py CSV, Sep 1 to Oct 26 (archive flucs exist from Sep 1 only).
Ours: v10 p10 on the holdout (races to 13 Oct); the live v6 p_model for 14 Oct on. DESIGN = to 13 Oct, CHECK = 14 Oct on.
Expected value against the Betfair market: fair chance = 1/BSP normalised per race, EV = price x fair - 1 (steady);
P/L at the price taken and at BSP after 8% (noisy). 'best' = average x the final best/average ratio (only snapshot).
python3.13 t_window_strat.py CSV"""
import sys, csv, json, glob, collections, numpy as np, stake_rule
L = open(sys.argv[1]).read().split("CSV-BEGIN")[1].split("CSV-END")[0].strip().splitlines()
R = [r for r in csv.DictReader(L)]
z = np.load("ds/model_ds_v10.npz", allow_pickle=True); p10 = np.load("v10_profit_preds.npz")["p10"]
rid = z["race_id"].tolist(); ri = z["race_idx"].tolist(); hid = z["horse_id"].tolist()
P10 = {(rid[r], h): p for r, h, p in zip(ri, hid, p10.tolist())}
V6 = {}
for f in sorted(glob.glob("/home/user/fk-model/data/live_bets/2026-10-*-v6.json")):
    if f.rsplit("/", 1)[1][:10] < "2026-10-14": continue
    for x in json.load(open(f)):
        if x.get("p_model"): V6[(x["race_id"], x["horse_id"])] = float(x["p_model"])
def rdate(r):  # TRACK_DDMMYY_N
    d = r.rsplit("_", 2)[1]; return f"20{d[4:6]}-{d[2:4]}-{d[0:2]}"
byr = collections.defaultdict(list)
for r in R:
    if r["bsp"] and float(r["bsp"]) > 1 and r["finish"]: byr[r["race_id"]].append(r)
MIN = ["open", "m15", "m20", "m30", "m40", "m45", "m50", "m60", "m90", "m120", "m180"]
rows = []
for k, xs in byr.items():
    d = rdate(k); src = P10 if d <= "2026-10-13" else V6
    if not all((k, x["horse_id"]) in src for x in xs) or sum(int(x["finish"]) == 1 for x in xs) != 1: continue
    s = sum(src[(k, x["horse_id"])] for x in xs); fb = sum(1 / float(x["bsp"]) for x in xs)
    for x in xs:
        o = {c: (float(x[c]) if x.get(c) else np.nan) for c in MIN}
        rows.append(dict(race=k, date=d, p=src[(k, x["horse_id"])] / s, won=int(x["finish"]) == 1, bsp=float(x["bsp"]),
                         fair=(1 / float(x["bsp"])) / fb, boa=float(x["best_over_avg"]) if x.get("best_over_avg") else 1.0, field=len(xs), **o))
races = sorted({x["race"] for x in rows})
print(f"races {len(races)} ({sum(rdate(r) <= '2026-10-13' for r in races)} design, {sum(rdate(r) > '2026-10-13' for r in races)} check), runners {len(rows)}")
TIERS = (1.0, 1.25, 1.5)
def live_stake(p, t0, E_lo=1.15, E_hi=1.2):
    q = 1 / p
    if not (1.6 <= q <= 15) or t0 >= 3 * q: return 0.0
    E = E_lo if t0 < 4 else E_hi; mo = 0.95 * (E / p ** 0.82) ** (1 / 0.78)
    if t0 < mo: return 0.0
    ts = [mo * k for k in TIERS if mo * k < 3 * q]; tot = prev = 0.0
    for k, t in enumerate(ts):
        tp = ts[k + 1] if k + 1 < len(ts) else t
        s_ = stake_rule.stake(p ** 0.82 * tp ** -0.22, tp); add = max(0.0, s_ - prev); prev = max(prev, s_)
        if t0 >= t: tot += add
    return tot
def bets(entry, filt=lambda x, t: True, E=(1.15, 1.2), stake="live", period="design", spread=False):
    """entry: a column, or a tuple of columns = take the first in the window where the rule fires (a watcher)."""
    out = []
    for x in rows:
        if (period == "design") != (x["date"] <= "2026-10-13") and period != "all": continue
        cols = entry if isinstance(entry, tuple) else (entry,)
        for c in cols:
            t = x[c]
            if not np.isfinite(t) or t <= 1: continue
            tt = t * (x["boa"] if spread else 1.0)
            s = live_stake(x["p"], tt, *E)
            if s > 0 and filt(x, t):
                if stake == "flat": s = 1.0
                out.append((x, tt, s, c)); break
    return out
def summary(B, label):
    if not B: return f"| {label} | 0 |"
    s = np.array([b[2] for b in B]); t = np.array([b[1] for b in B]); w = np.array([b[0]["won"] for b in B])
    bsp = np.array([b[0]["bsp"] for b in B]); fair = np.array([b[0]["fair"] for b in B])
    ev = np.sum(s * (t * fair - 1)) / s.sum(); pl = np.where(w, s * (t - 1), -s).sum(); pb = np.where(w, s * (bsp - 1) * .92, -s).sum()
    # race bootstrap on P/L ROI
    rr = collections.defaultdict(lambda: [0.0, 0.0])
    for b, sv in zip(B, np.where(w, s * (t - 1), -s)): rr[b[0]["race"]][0] += b[2]; rr[b[0]["race"]][1] += sv
    A = np.array(list(rr.values())); g = np.random.default_rng(3); bt = []
    for _ in range(1000):
        S = A[g.integers(0, len(A), len(A))]; bt.append(S[:, 1].sum() / S[:, 0].sum())
    lo, hi = np.percentile(bt, [5, 95])
    return (f"| {label} | {len(B)} | {s.sum():.0f}u | {(t > bsp).mean():.0%} | {np.sum(s*t/bsp)/s.sum():.2f} | {ev:+.1%} | "
            f"{pl:+.0f}u ({pl/s.sum():+.0%}, {lo:+.0%} to {hi:+.0%}) | {pb/s.sum():+.0%} |")
H = "| strategy | bets | staked | beat BSP | price/BSP | EV vs Betfair | P/L at price taken (90% range) | same bets at BSP |\n|---|---|---|---|---|---|---|---|"
W = ("m30", "m40", "m45", "m50", "m60")
for period in ("design", "check", "all"):
    print(f"\n## {period.upper()}\n\n{H}")
    print(summary(bets("open", period=period), "A. live rule at the open (benchmark)"))
    for c in ("m30", "m45", "m60"): print(summary(bets(c, period=period), f"B. live rule at {c[1:]} min"))
    print(summary(bets(W, period=period), "C. watcher: first value 30-60 min"))
    print(summary(bets(W, period=period, spread=True), "C+ same, at best of accounts"))
    mv = lambda lo, hi: (lambda x, t: lo <= t / x["open"] < hi)
    print(summary(bets(W, mv(0, 0.97), period=period), "D1. watcher, firmed since open (<0.97x)"))
    print(summary(bets(W, mv(0.97, 1.03), period=period), "D2. watcher, steady (0.97-1.03x)"))
    print(summary(bets(W, mv(1.03, 1.2), period=period), "D3. watcher, drifted a little (1.03-1.2x)"))
    print(summary(bets(W, mv(1.2, 99), period=period), "D4. watcher, drifted a lot (1.2x+)"))
    for e in ((1.3, 1.3), (1.4, 1.4), (1.5, 1.5)):
        print(summary(bets(W, E=e, period=period), f"E. watcher, edge {e[0]}"))
    print(summary(bets(W, lambda x, t: 1 / x["p"] < 5, period=period), "F1. watcher, our price under $5"))
    print(summary(bets(W, lambda x, t: 5 <= 1 / x["p"], period=period), "F2. watcher, our price $5+"))
    print(summary(bets(W, stake="flat", period=period), "G. watcher, flat 1u"))
# momentum: does the open->30 min move predict the 30 min->BSP move?
print("\n## Does the first 30 minutes predict the rest? (all runners with ours $1.60-$15, all dates)\n")
print("| move open to 30 min | runners | median 30-min price / BSP | share where BSP shorter than 30-min price |\n|---|---|---|---|")
for lo, hi, lab in ((0, .85, "firmed 15%+"), (.85, .97, "firmed 3-15%"), (.97, 1.03, "steady"), (1.03, 1.2, "drifted 3-20%"), (1.2, 99, "drifted 20%+")):
    xs = [x for x in rows if 1.6 <= 1 / x["p"] <= 15 and np.isfinite(x["m30"]) and lo <= x["m30"] / x["open"] < hi]
    if xs: print(f"| {lab} | {len(xs)} | {np.median([x['m30']/x['bsp'] for x in xs]):.2f} | {np.mean([x['bsp'] < x['m30'] for x in xs]):.0%} |")
print(f"\nmedian best/avg (final snapshot): {np.median([x['boa'] for x in rows]):.3f}")
