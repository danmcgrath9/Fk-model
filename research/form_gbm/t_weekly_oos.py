"""Weekly out-of-sample test of the LIVE betting rule on newly settled races (founder, 19 Oct 2026: "Have we been back
testing with results"; the daily replay tests the old 9am methods, nothing re-tested the rule we actually bet).

For each Monday-to-Sunday week not yet in oos/weekly.csv: stage-1 v10 trees (3 seeds, as t_v10_profit.py) trained ONLY
on races before that Monday, our price for the week's races, then the BetMatic orders as they would fire at Form King's
opening price: minimum odds 0.95 x (E / p^0.82)^(1/0.78) with E 1.2 (1.15 under $4), steps x1 / x1.25 / x1.5 under the
3x ceiling, $1.60-$15, each step sized on stake_rule at the next step's price, the firm/drift multiplier at each step's
own price (drift_forecast, models/drift_model.txt), 5u cap, 16c deduction. Also the same bets at BSP and the closing
line (our price taken / BSP).

RULES (20 Oct 2026, founder: "switch models"): both the forecast-BSP blend the orders use from 20 Oct (chance at a step
t = p^0.15 x qBSP(t)^0.85, minimum odds 0.95 x the lowest t where chance x t reaches the edge; betmatic_orders.py) and
the 13 Oct rule it replaced (p^0.82 t^-0.22), from the same trees, so the switch is measured on the same races. The
blend's ledgers are oos/{daily,weekly}_blend.csv and {DAILY,WEEKLY}_BLEND.md; the 13 Oct rule keeps the original names.

Approximations, stated: stage 1 only (the live price adds stage 2 and back-shading), a flat 16c deduction, and the
first-starter / first-up / bounce blocks are not applied.

    python t_weekly_oos.py [--period week|day] [--from 2026-10-12]   (day: one row per race day, oos/daily.csv)     (in research/form_gbm, needs ds/model_ds.npz from export_dataset.py)"""
import argparse, csv, datetime as dt, os, time
import numpy as np
import bench as b, lab, price_day as pdm, stage2, stake_rule, drift_forecast as dfc

ap = argparse.ArgumentParser(); ap.add_argument("--from", dest="start", default="2026-10-12"); ap.add_argument("--seeds", type=int, default=3); ap.add_argument("--rounds", type=int, default=4000)
ap.add_argument("--period", choices=("week", "day"), default="week")
a = ap.parse_args()
OUT = "oos"
LEDGERS = {"plain": os.path.join(OUT, f"{'weekly' if a.period == 'week' else 'daily'}.csv"),
           "blend": os.path.join(OUT, f"{'weekly' if a.period == 'week' else 'daily'}_blend.csv")}
BLEND_W = 0.15; GRID = np.exp(np.linspace(np.log(1.05), np.log(46.0), 1500))
STEP = 7 if a.period == "week" else 1; os.makedirs(OUT, exist_ok=True)
D = b.load("ds/model_ds.npz"); ri = D["race_idx"]; nR = D["n_races"]; rdate = D["date"].astype(str)
done = {k: ({r["week_start"] for r in csv.DictReader(open(f))} if os.path.exists(f) else set()) for k, f in LEDGERS.items()}
last = max(rdate); mon = dt.date.fromisoformat(a.start)
weeks = []
while mon + dt.timedelta(days=STEP - 1) <= dt.date.fromisoformat(last):   # whole periods only: the last day's races must be settled
    if any(mon.isoformat() not in d for d in done.values()): weeks.append(mon)
    mon += dt.timedelta(days=STEP)
if not weeks:
    print(f"nothing new: data to {last}"); raise SystemExit
F, nm = pdm.inputs()
TR = stage2.trials(D["P"], D["past_fields"], ri); SEC = stage2.sections(D["S"], D["sec_fields"], D["P"], D["past_fields"], ri, nR)
F = np.hstack([F, TR, SEC]).astype(np.float32); F[~np.isfinite(F)] = np.nan
nm = list(nm) + [f"tr_{i}" for i in range(TR.shape[1])] + [f"sec_{i}" for i in range(SEC.shape[1])]
lab.D = D; lab.ri0 = ri
o = np.asarray(D["open"], float); bs = np.asarray(D["bsp"], float); won = np.asarray(D["finish"], float) == 1
okp = np.isfinite(o) & (o > 1); race_ok = np.bincount(ri, weights=~okp, minlength=nR) == 0
fld = np.bincount(ri, minlength=nR)[ri]
fc = dfc.Forecast("models"); X = np.asarray(D["X"], np.float32); ci = {str(c): j for j, c in enumerate(D["cols"])}
XD = X[:, [ci[c] for c in fc.cols]]
DED, TIERS, CAP = 0.16, (1.0, 1.25, 1.5), stake_rule.MAX_UNITS
HEAD = ["week_start", "week_end", "trained_to", "races", "bets", "winners", "staked_u", "profit_u", "roi",
        "bsp_profit_u", "bsp_roi", "clv_open_over_bsp"]


def stake_for(i, p, rule):
    """Units the BetMatic ladder would have bet on runner i at its open, under the plain (13 Oct) or blend rule."""
    q = 1 / p
    if not (1.6 <= q <= 15) or o[i] >= 3 * q: return 0.0
    E = 1.15 if o[i] < 4 else 1.2; f = int(fld[i])
    if rule == "plain":
        mo = 0.95 * (E / p ** 0.82) ** (1 / 0.78); ch = lambda t: p ** 0.82 * t ** -0.22
    else:
        g = GRID[GRID < 3 * q]
        if not len(g): return 0.0
        ok = p ** BLEND_W * fc.qbsp(XD[i], p, g, f) ** (1 - BLEND_W) * g >= E
        if not ok.any(): return 0.0
        mo = 0.95 * float(g[np.argmax(ok)]); ch = lambda t: float(p ** BLEND_W * fc.qbsp(XD[i], p, [t], f)[0] ** (1 - BLEND_W))
    if o[i] < mo: return 0.0
    ts = [mo * k for k in TIERS if mo * k < 3 * q]
    tot = prev = 0.0
    for k, t in enumerate(ts):
        tp = ts[k + 1] if k + 1 < len(ts) else t
        mult, _ = fc.mult(XD[i], p, t, f)
        T_k = min(CAP, stake_rule.stake(ch(tp), tp) * mult)
        add = max(0.0, T_k - prev); prev = max(prev, T_k)
        if o[i] >= t: tot += add
    return tot


fhs = {}
for rule, f in LEDGERS.items():
    new = not os.path.exists(f); fhs[rule] = open(f, "a", newline="")
    if new: csv.writer(fhs[rule]).writerow(HEAD)
for mon in weeks:
    s, e = mon.isoformat(), (mon + dt.timedelta(days=STEP - 1)).isoformat()
    todo = [r for r in LEDGERS if s not in done[r]]
    races = np.arange(nR); train = races[rdate < s]; wk = races[(rdate >= s) & (rdate <= e)]
    if len(wk) == 0:   # no races: recorded (so not retrained every run) once it is 3+ days old, in case results are late
        if (dt.date.fromisoformat(last) - dt.date.fromisoformat(e)).days < 3: continue
        for r in todo: csv.writer(fhs[r]).writerow([s, e, '', 0, 0, 0, 0, 0, '', 0, '', '']); fhs[r].flush()
        continue
    preds = []
    for sd in range(a.seeds):
        t1 = time.time()
        bst, _ = lab.train(F, nm, train, D["q"], params=dict(feature_fraction=0.2, extra_trees=True), seed=sd, fixed_rounds=a.rounds)
        preds.append(np.log(b.softmax_races(bst.predict(F)))); print(f"week {s} seed {sd} {time.time()-t1:.0f}s", flush=True)
    pm = b.softmax_races(np.mean(preds, 0))
    in_wk = np.isin(ri, wk) & race_ok[ri] & np.isfinite(bs) & (bs > 1)
    for rule in todo:
        rows = []; st = pl = plb = 0.0; n = nw = 0; clv = []
        for i in np.where(in_wk & (pm > 0))[0]:
            tot = stake_for(i, pm[i], rule)
            if tot <= 0: continue
            r = tot * (o[i] - 1) * (1 - DED) if won[i] else -tot
            rb = tot * (bs[i] - 1) if won[i] else -tot
            n += 1; nw += int(won[i]); st += tot; pl += r; plb += rb; clv.append(o[i] / bs[i])
            rows.append([rdate[ri[i]], str(D["track"][ri[i]]), int(D["race_number"][ri[i]]), str(D["name"][i]), round(1 / pm[i], 2),
                         o[i], bs[i], int(won[i]), round(tot, 2), round(r, 2)])
        sfx = "" if rule == "plain" else "_blend"
        with open(os.path.join(OUT, f"bets_{a.period}{sfx}_{s}.csv"), "w", newline="") as bf:
            bw = csv.writer(bf); bw.writerow(["date", "track", "race", "horse", "our_price", "open", "bsp", "won", "stake_u", "pl_u"]); bw.writerows(rows)
        csv.writer(fhs[rule]).writerow([s, e, max(rdate[train]) if len(train) else "", len(wk), n, nw, round(st, 2), round(pl, 2),
                    f"{pl/st:+.1%}" if st else "", round(plb, 2), f"{plb/st:+.1%}" if st else "", f"{np.mean(clv):.3f}" if clv else ""])
        fhs[rule].flush()
        print(f"{rule} {s}..{e}: {len(wk)} races, {n} bets, {nw} won, {st:.1f}u staked, {pl:+.1f}u, BSP {plb:+.1f}u")
for fh in fhs.values(): fh.close()
# the reports: every period so far and the running total, one per rule
for rule, LEDGER in LEDGERS.items():
    R = list(csv.DictReader(open(LEDGER)))
    tot = {k: sum(float(r[k] or 0) for r in R) for k in ("bets", "winners", "staked_u", "profit_u", "bsp_profit_u")}
    what = ("the forecast-BSP blend (live from 20 Oct 2026)" if rule == "blend" else "the 13 Oct rule (blend with the open, live to 19 Oct 2026)")
    lines = [f"# {'Weekly' if a.period == 'week' else 'Daily'} out-of-sample test: {what}", "", "Generated by research/form_gbm/t_weekly_oos.py: each period priced by a model trained only on earlier races, bets as the BetMatic orders would fire at the open (firm/drift stakes, 16c deduction). Stage 1 only; blocks not applied.", "",
             f"| {a.period} | races | bets | won | staked | profit | ROI | at BSP | open / BSP |", "|---|---|---|---|---|---|---|---|---|"]
    for r in R:
        lines.append(f"| {r['week_start'] if a.period == 'day' else r['week_start'] + ' to ' + r['week_end']} | {r['races']} | {r['bets']} | {r['winners']} | {float(r['staked_u'] or 0):.1f}u | {float(r['profit_u'] or 0):+.1f}u | {r['roi']} | {float(r['bsp_profit_u'] or 0):+.1f}u ({r['bsp_roi']}) | {r['clv_open_over_bsp']} |")
    if tot["staked_u"]:
        lines.append(f"| **all {a.period}s** | | {int(tot['bets'])} | {int(tot['winners'])} | {tot['staked_u']:.1f}u | {tot['profit_u']:+.1f}u | {tot['profit_u']/tot['staked_u']:+.1%} | {tot['bsp_profit_u']:+.1f}u | |")
    base = "WEEKLY" if a.period == "week" else "DAILY"
    open(os.path.join(OUT, base + ("_BLEND" if rule == "blend" else "") + ".md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
