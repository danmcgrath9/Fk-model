"""The last minutes before the jump: is there a long-run edge in what the public does late? (25 Oct 2026, founder:
"surely there's a way in the last 10 minutes of the race... something the public over reacts to").
Data: Dave's one-week archive sample (20-26 Aug 2026, all states), every runner's corporate-average price flucs with
timestamps up to the jump (the last fluc sits on the scheduled start), Betfair SP and the result. Our price from the
Vic model's state run (priced_states/*.v6.json). Settled at BSP with 8% commission, because the exchange is the only
place late money is unlimited and BSP is the only exchange price we hold: a late back is treated as taking BSP.
  1. Late corp move (price at T minutes out / final corp price) against A/E at BSP: do late firmers win more than BSP
     says (back) and late drifters less (lay)?
  2. Value against the T-minute corp price by our model, settled at BSP.
  3. Corp price at T against BSP: where is the corp book softer than the exchange late?
python3.13 t_late_market.py ARCHIVE_DIR PRICED_DIR"""
import json, glob, os, sys, collections, bisect
import numpy as np
root, pdir = sys.argv[1], sys.argv[2]
COMM = 0.08
ours = {}
for f in glob.glob(os.path.join(pdir, "*.v6.json")):
    for r in json.load(open(f)): ours[(r["race_id"], r["horse_id"])] = r["p"]
rows = []
for p in sorted(glob.glob(os.path.join(root, "meetings/*/races/*.json"))):
    A = json.load(open(p)); rid = str(A["raceId"]); ent = [e for e in A["entries"] if not e.get("scratched")]
    jump = max((((e.get("odds") or {}).get("flucs") or [{"time": 0}])[-1]["time"] for e in ent), default=0)
    if not jump: continue
    R = []
    for e in ent:
        hr = e.get("horseResult") or {}; od = e.get("odds") or {}; fl = od.get("flucs") or []
        bsp = hr.get("betfairStartingPrice"); fin = hr.get("finishPosition")
        if not fl or not bsp or bsp <= 1 or fin is None: R = []; break
        t = [x["time"] for x in fl]; pr = [x["price"] for x in fl]
        def at(mins):  # last fluc at or before T minutes out
            i = bisect.bisect_right(t, jump - mins * 60000) - 1
            return pr[i] if i >= 0 else pr[0]
        R.append(dict(rid=rid, won=fin == 1, bsp=float(bsp), final=pr[-1], open=pr[0], fs=bool(e.get("firstStarter")),
                      p=ours.get((rid, str(e.get("breedingId")))), **{f"t{m}": at(m) for m in (2, 5, 10, 20, 30, 60)}))
    if len(R) >= 4 and any(r["won"] for r in R): rows += R
print(f"{len(rows)} runners, {len(set(r['rid'] for r in rows))} races with full flucs, BSP and a result")
won = np.array([r["won"] for r in rows]); bsp = np.array([r["bsp"] for r in rows]); rid = np.array([r["rid"] for r in rows])
# normalised BSP chance per race
qb = 1 / bsp; s = collections.defaultdict(float)
for k, v in zip(rid, qb): s[k] += v
qb = qb / np.array([s[k] for k in rid])
back = np.where(won, (bsp - 1) * (1 - COMM), -1.0); lay = np.where(won, -(bsp - 1), 1 - COMM)
def line(name, g):
    n = g.sum(); e = qb[g].sum(); w = won[g].sum()
    print(f"| {name} | {n} | {w} | {e:.1f} | {w/max(e,1e-9):.2f} | {100*back[g].mean():+.0f}% | {100*lay[g].mean():+.0f}% |")
H = "| group | runners | wins | expected at BSP | A/E | back at BSP | lay at BSP |\n|---|---|---|---|---|---|---|"
for T in (10, 30, 60):
    pt = np.array([r[f"t{T}"] for r in rows]); fin = np.array([r["final"] for r in rows]); mv = pt / fin  # >1 = firmed late
    print(f"\n## 1. Corp price {T} min out / final corp price (above 1 = firmed in the last {T} min)\n" + H)
    for lo, hi, nm in ((0, 0.8, "drifted 25%+"), (0.8, 0.95, "drifted a little"), (0.95, 1.05, "held"), (1.05, 1.25, "firmed a little"), (1.25, 99, "firmed 25%+")):
        line(nm, (mv >= lo) & (mv < hi))
    print(f"\nfirmed 25%+ in the last {T} min, by BSP\n" + H)
    for lo, hi in ((1, 4), (4, 10), (10, 30), (30, 1000)): line(f"${lo}-${hi}", (mv >= 1.25) & (bsp >= lo) & (bsp < hi))
    print(f"\ndrifted 25%+ in the last {T} min, by BSP\n" + H)
    for lo, hi in ((1, 4), (4, 10), (10, 30), (30, 1000)): line(f"${lo}-${hi}", (mv < 0.8) & (bsp >= lo) & (bsp < hi))
# 2. our model against the late corp price
pm = np.array([r["p"] if r["p"] else np.nan for r in rows]); okp = np.isfinite(pm)
sp_ = collections.defaultdict(float)
for k, v, o_ in zip(rid, pm, okp):
    if o_: sp_[k] += v
pm = np.where(okp, pm / np.array([sp_[k] if sp_[k] > 0 else 1 for k in rid]), np.nan)
fs = np.array([r["fs"] for r in rows])
print("\n## 2. Value by our model against the corp price T minutes out, settled at BSP (no first starters)\n| T | value 20c+ runners | wins | back at BSP | and our price $1.60-$15 | wins | back at BSP | ours/BSP chance 1.6+ among them: lay at BSP |\n|---|---|---|---|---|---|---|---|")
ratio = pm / qb
for T in (2, 5, 10, 30, 60):
    pt = np.array([r[f"t{T}"] for r in rows]); v = okp & ~fs & (pm * pt >= 1.2); v2 = v & (1 / pm >= 1.6) & (1 / pm <= 15); l3 = v2 & (ratio >= 1.6)
    print(f"| {T} min | {v.sum()} | {won[v].sum()} | {100*back[v].mean():+.0f}% | {v2.sum()} | {won[v2].sum()} | {100*back[v2].mean():+.0f}% | {l3.sum()} lays {100*lay[l3].mean():+.0f}% |")
# 3. corp late price vs BSP
print("\n## 3. Corp price T minutes out against BSP (median corp/BSP; above 1 = the corps are longer than the exchange)\n| T | all runners | $1-$4 | $4-$10 | $10-$30 | $30+ | share of runners where corp > BSP |\n|---|---|---|---|---|---|---|")
for T in (2, 5, 10, 30, 60):
    pt = np.array([r[f"t{T}"] for r in rows]); rr = pt / bsp
    cells = [f"{np.median(rr[(bsp>=lo)&(bsp<hi)]):.2f}" for lo, hi in ((1, 4), (4, 10), (10, 30), (30, 1000))]
    print(f"| {T} min | {np.median(rr):.2f} | " + " | ".join(cells) + f" | {(rr > 1).mean():.0%} |")
