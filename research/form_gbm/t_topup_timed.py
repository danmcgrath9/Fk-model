"""Replay of "bet at the open, top up at 9:30am after scratchings" on the races with timed prices (14 Oct 2026, founder:
"Unless you can back test now by pulling the time of the prices").

    python t_topup_timed.py TIMING.csv          (scripts/fluc_timing.py output with the am930 and scratched columns)

Per race, from Form King's timed flucs and the live model's own prices (data/live_bets/*-v6.json):
- Before the scratchings: the field included the runners later scratched. Their share of the opening market
  q = sum(1/open, scratched) / sum(1/open, all) is put back by scaling the starters' model chances by (1 - q).
- Stage 1, at the open: the BetMatic orders (betmatic_orders.py: minimum odds from that pre-scratch chance, 5% shade,
  8 steps sized at the next step) fill where the open is at or over the minimum. Winnings take the deduction the
  scratchings cost a bet struck at the open: sum of min(0.9, 0.95 / open) over the scratched runners, capped 0.95.
- Stage 2, 9:30am race day: our market re-priced on the final field (model chances of the starters blended with their
  opens, renormalised). A runner value at its open on that field (open >= 1.2 / chance) and still at or over take-at at
  the 9:30am price is topped up to the full stake at 9:30am, less what stage 1 already holds. No deduction.
Small sample by construction (timed flucs exist only for races pulled live, from 3 Oct 2026)."""
import csv, glob, json, math, os, re, sys, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import stake_rule
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
S = collections.defaultdict(lambda: [0, 0.0, 0.0, 0]); detail = []
def add(k, st, price, won, d):
    if st <= 0: return
    S[k][0] += 1; S[k][1] += st; S[k][2] += st * (price - 1) * (1 - d) if won else -st; S[k][3] += won
n_races = 0
for rid, rs in by.items():
    starters = [t for t in rs if not t["scratched"] and f(t["open"]) and t["finish"]]
    scr = [t for t in rs if t["scratched"] and f(t["open"])]
    if not starters or not any(t["finish"] == "1" for t in starters) or not all((rid, t["horse_id"]) in pm for t in starters):
        continue
    n_races += 1
    q = sum(1 / f(t["open"]) for t in scr) / sum(1 / f(t["open"]) for t in starters + scr)
    d = min(0.95, sum(min(0.9, 0.95 / f(t["open"])) for t in scr))
    w = [math.exp(0.82 * math.log(pm[(rid, t["horse_id"])][0]) + 0.22 * math.log(1 / f(t["open"]))) for t in starters]; sw = sum(w)
    fld = len(starters)
    for t, x in zip(starters, w):
        p_fin, only = pm[(rid, t["horse_id"])]; p_pre = p_fin * (1 - q); op = f(t["open"]); won = t["finish"] == "1"
        # stage 1: the order file (pre-scratch chance)
        s1 = 0.0
        if 1.6 <= 1 / p_pre <= 15:
            mo = round(0.95 * (1.2 / p_pre ** 0.82) ** (1 / 0.78), 2)
            for tp, extra, _ in tiers(mo, 3 / p_pre, lambda tt, pp=p_pre: pp ** 0.82 * tt ** -0.22, only, fld):
                if op >= tp: s1 += extra
        add("stage 1 only: orders at the open", s1, op, won, d)
        add("stage 1 + 2: orders, then 9:30am top-up", s1, op, won, d)
        # stage 2: final field, 9:30am price
        pb = x / sw; ours = 1 / pb; p9 = f(t["am930"])
        if 1.6 <= ours <= 15 and op >= 1.2 * ours and op < 3 * ours and p9 and p9 >= 1.2 * ours:
            full = stake_rule.stake(pb, p9, only, fld); top = max(0.0, full - s1)
            add("stage 1 + 2: orders, then 9:30am top-up", top, p9, won, 0.0)
            add("  (the 9:30am top-up slice on its own)", top, p9, won, 0.0)
            if top > 0: detail.append(f"| {rid} | {t['horse_id']} | ${op:g} | ${p9:g} | ${ours:.2f} | {s1:.2f}u | +{top:.2f}u | {t['finish']} | {t['bsp'] or '-'} |")
print(f"{n_races} resulted races with timed prices and live model prices\n")
print("| method | bets | won | staked (u) | profit (u) | staked ROI |\n|---|---|---|---|---|---|")
for k in ("stage 1 only: orders at the open", "stage 1 + 2: orders, then 9:30am top-up", "  (the 9:30am top-up slice on its own)"):
    n, st, pl, wn = S[k]; print(f"| {k} | {n} | {wn} | {st:.2f} | {pl:+.2f} | {100 * pl / st if st else 0:+.1f}% |")
print("\n| race | horse | open | 9:30am | ours (final field) | stage 1 | top-up | finish | BSP |\n|---|---|---|---|---|---|---|---|---|")
print("\n".join(detail))
