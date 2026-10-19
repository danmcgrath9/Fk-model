"""Weekly out-of-sample test of the LIVE betting rule on newly settled races (founder, 19 Oct 2026: "Have we been back
testing with results"; the daily replay tests the old 9am methods, nothing re-tested the rule we actually bet).

For each Monday-to-Sunday week not yet in oos/weekly.csv: stage-1 v10 trees (3 seeds, as t_v10_profit.py) trained ONLY
on races before that Monday, our price for the week's races, then the BetMatic orders as they would fire at Form King's
opening price: minimum odds 0.95 x (E / p^0.82)^(1/0.78) with E 1.2 (1.15 under $4), steps x1 / x1.25 / x1.5 under the
3x ceiling, $1.60-$15, each step sized on stake_rule at the next step's price, the firm/drift multiplier at each step's
own price (drift_forecast, models/drift_model.txt), 5u cap, 16c deduction. Also the same bets at BSP and the closing
line (our price taken / BSP).

Approximations, stated: stage 1 only (the live price adds stage 2 and back-shading), a flat 16c deduction, and the
first-starter / first-up / bounce blocks are not applied.

    python t_weekly_oos.py [--period week|day] [--from 2026-10-12]   (day: one row per race day, oos/daily.csv)     (in research/form_gbm, needs ds/model_ds.npz from export_dataset.py)"""
import argparse, csv, datetime as dt, os, time
import numpy as np
import bench as b, lab, price_day as pdm, stage2, stake_rule, drift_forecast as dfc

ap = argparse.ArgumentParser(); ap.add_argument("--from", dest="start", default="2026-10-12"); ap.add_argument("--seeds", type=int, default=3); ap.add_argument("--rounds", type=int, default=4000)
ap.add_argument("--period", choices=("week", "day"), default="week")
a = ap.parse_args()
OUT = "oos"; LEDGER = os.path.join(OUT, "weekly.csv" if a.period == "week" else "daily.csv")
STEP = 7 if a.period == "week" else 1; os.makedirs(OUT, exist_ok=True)
D = b.load("ds/model_ds.npz"); ri = D["race_idx"]; nR = D["n_races"]; rdate = D["date"].astype(str)
done = set()
if os.path.exists(LEDGER):
    done = {r["week_start"] for r in csv.DictReader(open(LEDGER))}
last = max(rdate); mon = dt.date.fromisoformat(a.start)
weeks = []
while mon + dt.timedelta(days=STEP - 1) <= dt.date.fromisoformat(last):   # whole periods only: the last day's races must be settled
    if mon.isoformat() not in done: weeks.append(mon)
    mon += dt.timedelta(days=STEP)
if not weeks:
    print(f"nothing new: data to {last}, ledger has {sorted(done)}"); raise SystemExit
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
DED, TIERS, CAP = 0.16, (1.0, 1.25, 1.5), 5.0
new = not os.path.exists(LEDGER)
with open(LEDGER, "a", newline="") as fh:
    w = csv.writer(fh)
    if new:
        w.writerow(["week_start", "week_end", "trained_to", "races", "bets", "winners", "staked_u", "profit_u", "roi",
                    "bsp_profit_u", "bsp_roi", "clv_open_over_bsp"])
    for mon in weeks:
        s, e = mon.isoformat(), (mon + dt.timedelta(days=STEP - 1)).isoformat()
        races = np.arange(nR); train = races[rdate < s]; wk = races[(rdate >= s) & (rdate <= e)]
        if len(wk) == 0:   # no races: recorded (so not retrained every run) once it is 3+ days old, in case results are late
            if (dt.date.fromisoformat(last) - dt.date.fromisoformat(e)).days < 3: continue
            w.writerow([s, e, '', 0, 0, 0, 0, 0, '', 0, '', '']); fh.flush(); continue
        preds = []
        for sd in range(a.seeds):
            t1 = time.time()
            bst, _ = lab.train(F, nm, train, D["q"], params=dict(feature_fraction=0.2, extra_trees=True), seed=sd, fixed_rounds=a.rounds)
            preds.append(np.log(b.softmax_races(bst.predict(F)))); print(f"week {s} seed {sd} {time.time()-t1:.0f}s", flush=True)
        pm = b.softmax_races(np.mean(preds, 0))
        in_wk = np.isin(ri, wk) & race_ok[ri] & np.isfinite(bs) & (bs > 1)
        rows = []; st = pl = plb = 0.0; n = nw = 0; clv = []
        for i in np.where(in_wk & (pm > 0))[0]:
            p = pm[i]; q = 1 / p
            if not (1.6 <= q <= 15) or o[i] >= 3 * q: continue
            E = 1.15 if o[i] < 4 else 1.2
            mo = 0.95 * (E / p ** 0.82) ** (1 / 0.78)
            if o[i] < mo: continue
            ts = [mo * k for k in TIERS if mo * k < 3 * q]
            tot = prev = 0.0
            for k, t in enumerate(ts):
                tp = ts[k + 1] if k + 1 < len(ts) else t
                mult, _ = fc.mult(XD[i], p, t, int(fld[i]))
                T_k = min(CAP, stake_rule.stake(p ** 0.82 * tp ** -0.22, tp) * mult)
                add = max(0.0, T_k - prev); prev = max(prev, T_k)
                if o[i] >= t: tot += add
            if tot <= 0: continue
            r = tot * (o[i] - 1) * (1 - DED) if won[i] else -tot
            rb = tot * (bs[i] - 1) if won[i] else -tot
            n += 1; nw += int(won[i]); st += tot; pl += r; plb += rb; clv.append(o[i] / bs[i])
            rows.append([rdate[ri[i]], str(D["track"][ri[i]]), int(D["race_number"][ri[i]]), str(D["name"][i]), round(q, 2),
                         o[i], bs[i], int(won[i]), round(tot, 2), round(r, 2)])
        with open(os.path.join(OUT, f"bets_{a.period}_{s}.csv"), "w", newline="") as bf:
            bw = csv.writer(bf); bw.writerow(["date", "track", "race", "horse", "our_price", "open", "bsp", "won", "stake_u", "pl_u"]); bw.writerows(rows)
        w.writerow([s, e, max(rdate[train]) if len(train) else "", len(wk), n, nw, round(st, 2), round(pl, 2),
                    f"{pl/st:+.1%}" if st else "", round(plb, 2), f"{plb/st:+.1%}" if st else "", f"{np.mean(clv):.3f}" if clv else ""])
        fh.flush()
        print(f"week {s}..{e}: {len(wk)} races, {n} bets, {nw} won, {st:.1f}u staked, {pl:+.1f}u, BSP {plb:+.1f}u")
# the report: every week so far and the running total
R = list(csv.DictReader(open(LEDGER)))
tot = {k: sum(float(r[k] or 0) for r in R) for k in ("bets", "winners", "staked_u", "profit_u", "bsp_profit_u")}
lines = [f"# {'Weekly' if a.period == 'week' else 'Daily'} out-of-sample test of the live rule", "", "Generated by research/form_gbm/t_weekly_oos.py: each period priced by a model trained only on earlier races, bets as the BetMatic orders would fire at the open (firm/drift stakes, 16c deduction). Stage 1 only; blocks not applied.", "",
         f"| {a.period} | races | bets | won | staked | profit | ROI | at BSP | open / BSP |", "|---|---|---|---|---|---|---|---|---|"]
for r in R:
    lines.append(f"| {r['week_start'] if a.period == 'day' else r['week_start'] + ' to ' + r['week_end']} | {r['races']} | {r['bets']} | {r['winners']} | {float(r['staked_u'] or 0):.1f}u | {float(r['profit_u'] or 0):+.1f}u | {r['roi']} | {float(r['bsp_profit_u'] or 0):+.1f}u ({r['bsp_roi']}) | {r['clv_open_over_bsp']} |")
if tot["staked_u"]:
    lines.append(f"| **all {a.period}s** | | {int(tot['bets'])} | {int(tot['winners'])} | {tot['staked_u']:.1f}u | {tot['profit_u']:+.1f}u | {tot['profit_u']/tot['staked_u']:+.1%} | {tot['bsp_profit_u']:+.1f}u | |")
open(os.path.join(OUT, "WEEKLY.md" if a.period == "week" else "DAILY.md"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
