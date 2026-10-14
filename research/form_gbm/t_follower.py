"""How much of the edge is left for someone who gets the tip after the open? (14 Oct 2026, founder: "run a test of
2 minutes after opening, 5 minutes, 10 minutes and 20 minutes. How many bookmakers, average less price etc").

    python t_follower.py TIMING.csv        (scripts/fluc_timing.py output with the m2/m5/m10/m20 columns)

Per race with timed Form King flucs and the live model's own price (data/live_bets/*-v6.json): our BetMatic orders
(minimum odds from the model's pre-scratch chance, 5% shade, 8 steps sized at the next step, 3x ceiling), filled at
the price standing at each time after the open: the open itself (what we get), then +2, +5, +10 and +20 minutes (what
a member who gets the tip then would get). Two follower rules: (a) the same orders, so a step only fires if the price
then still clears its minimum; (b) everything we got at the open, bet at whatever the price then is. Winnings less the
race's scratching deduction (as at the open: conservative for later bets). The fluc series is Form King's average
across the corporate books, so it is the price a member gets at an AVERAGE book, not the best one, and it carries no
bookmaker count: the number of price moves in the first 10 minutes stands in for how busy the market is."""
import csv, glob, json, math, os, sys, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
from betmatic_orders import tiers
L = os.path.join(here, "../../data/live_bets")
f = lambda v: float(v) if v not in ("", None) else None
pm = {}
for fn in sorted(glob.glob(f"{L}/2026-10-*-v6.json")):
    for r in json.load(open(fn)):
        pm[(r["race_id"], r["horse_id"])] = (r.get("p_model", r["p"]), r.get("only_ride", False))
T = list(csv.DictReader(open(sys.argv[1])))
by = collections.defaultdict(list)
for t in T: by[t["race_id"]].append(t)
TIMES = [("at the open", "open"), ("+2 min", "m2"), ("+5 min", "m5"), ("+10 min", "m10"), ("+20 min", "m20")]
A = {k: [0, 0, 0.0, 0.0] for _, k in TIMES}; B = {k: [0, 0, 0.0, 0.0] for _, k in TIMES}
ratio = collections.defaultdict(list); moves = []; n_races = 0
def add(S, k, st, price, won, d):
    if st <= 0: return
    S[k][0] += 1; S[k][1] += won; S[k][2] += st; S[k][3] += st * (price - 1) * (1 - d) if won else -st
for rid, rs in by.items():
    starters = [t for t in rs if not t["scratched"] and f(t["open"]) and t["finish"]]
    scr = [t for t in rs if t["scratched"] and f(t["open"])]
    if not starters or not any(t["finish"] == "1" for t in starters) or not all((rid, t["horse_id"]) in pm for t in starters): continue
    if not all(t.get("m20") not in (None, "") for t in starters): continue   # the market must have run 20 minutes
    n_races += 1
    q = sum(1 / f(t["open"]) for t in scr) / sum(1 / f(t["open"]) for t in starters + scr)
    d = min(0.95, sum(min(0.9, 0.95 / f(t["open"])) for t in scr))
    fld = len(starters)
    for t in starters:
        p_fin, only = pm[(rid, t["horse_id"])]; p = p_fin * (1 - q); won = t["finish"] == "1"
        if not 1.6 <= 1 / p <= 15: continue
        mo = round(0.95 * (1.2 / p ** 0.82) ** (1 / 0.78), 2); cap = 3 / p
        ts = tiers(mo, cap, lambda tt, pp=p: pp ** 0.82 * tt ** -0.22, only, fld)
        op = f(t["open"]); got_open = sum(x for tp, x, _ in ts if op >= tp and op < cap)
        if got_open > 0:
            moves.append(int(t.get("nflucs_10m") or 0))
        for _, k in TIMES:
            pr = f(t[k]) if k != "open" else op
            if pr is None: continue
            add(A, k, sum(x for tp, x, _ in ts if pr >= tp and pr < cap), pr, won, d)
            if got_open > 0:
                add(B, k, got_open, pr, won, d); ratio[k].append(pr / op)
print(f"{n_races} resulted races with timed prices, the live model's price and a market at least 20 minutes old\n")
print("| when the tip is bet | (a) orders still clearing their minimum: bets | won | staked | profit | ROI | (b) our open bets taken at that price: avg price vs open | profit | ROI |")
print("|---|---|---|---|---|---|---|---|---|")
for lab, k in TIMES:
    a, b = A[k], B[k]; r = ratio[k]
    print(f"| {lab} | {a[0]} | {a[1]} | {a[2]:.2f}u | {a[3]:+.2f}u | {100*a[3]/a[2] if a[2] else 0:+.0f}% | "
          f"{(sum(r)/len(r) if r else 0):.3f} ({100*((sum(r)/len(r) if r else 1)-1):+.1f}%) | {b[3]:+.2f}u | {100*b[3]/b[2] if b[2] else 0:+.0f}% |")
if moves: print(f"\nprice moves in the first 10 minutes on the runners we got at the open: median {sorted(moves)[len(moves)//2]}, mean {sum(moves)/len(moves):.1f}")
