"""Who rode the trial (27 Oct 2026, founder: "Do both"). For first-up and first-starter runners on the v10 holdout
(3 Jun-13 Oct): the most recent trial in the stored past runs (trials carry finish, field, distance, half the margins,
and the jockey). Jockey strength = win rate on races before 3 Jun (50+ rides). Read against our price (A/E vs ours), the
market (drift BSP/open, A/E vs BSP), and our open bets. python3.13 t_trial_jockey.py"""
import numpy as np, collections
z = np.load("ds/model_ds_v10.npz", allow_pickle=True)
ri = z["race_idx"]; nR = int(ri.max()) + 1; rdate = z["date"].astype(str); date = rdate[ri]
p10 = np.load("v10_profit_preds.npz")["p10"]; o = z["open"].astype(float); bs = z["bsp"].astype(float); won = z["finish"] == 1
okr = np.isfinite(o) & (o > 1) & np.isfinite(bs) & (bs > 1) & np.isfinite(p10) & (p10 > 0)
cnt = np.bincount(ri, minlength=nR)
race_ok = (np.bincount(ri, weights=okr.astype(float), minlength=nR) == cnt) & (rdate >= "2026-06-03") & (np.bincount(ri, weights=won.astype(float), minlength=nR) >= 1)
m = race_ok[ri]
nrm = lambda v: np.where(m, v / np.where(np.bincount(ri, weights=np.where(m, v, 0), minlength=nR)[ri] > 0, np.bincount(ri, weights=np.where(m, v, 0), minlength=nR)[ri], 1), np.nan)
pm = nrm(np.where(m, p10, 0)); qb = nrm(np.where(m, 1 / np.where(bs > 1, bs, 2), 0)); qo = nrm(np.where(m, 1 / np.where(o > 1, o, 2), 0))
# jockey strength from races before the holdout
jk = z["jockey"].astype(str); pre = date < "2026-06-03"
rides = collections.Counter(jk[pre].tolist()); wins = collections.Counter(jk[pre & won].tolist())
rate = {j: wins[j] / n for j, n in rides.items() if n >= 50 and j.strip()}
top = sorted(rate, key=rate.get, reverse=True)
thr = np.quantile(list(rate.values()), 0.8)
print(f"jockeys with 50+ rides before 3 Jun: {len(rate)}; top fifth = win rate {thr:.1%}+ (e.g. {', '.join(top[:6])})")
P = z["P"]; pf = [str(x) for x in z["past_fields"]]; PJ = z["past_jockeys"].astype(str); prid = z["past_race_ids"]
trial = P[..., pf.index("trial")] == 1
cols = [str(c) for c in z["cols"]]; X = z["X"]; col = lambda n: X[:, cols.index(n)].astype(float)
thin = m & ((col("firstStarter") == 1) | (col("raw_first_up") == 1))
# most recent trial (arrays newest first)
first_tr = np.where(trial.any(1), trial.argmax(1), -1)
idx = np.arange(len(ri))
tj = np.where(first_tr >= 0, PJ[idx, np.maximum(first_tr, 0)], "")
tfin = np.where(first_tr >= 0, P[idx, np.maximum(first_tr, 0), pf.index("finish")], np.nan)
tdays = np.where(first_tr >= 0, P[idx, np.maximum(first_tr, 0), pf.index("days_before")], np.nan)
tj_rate = np.array([rate.get(j.strip(), np.nan) for j in tj])
tj_top = tj_rate >= thr
same = np.array([a.strip() != "" and a.strip().lower() == b.strip().lower() for a, b in zip(tj, jk)])
today_top = np.array([rate.get(j.strip(), 0) >= thr for j in jk])
has = thin & (first_tr >= 0)
print(f"first-up / first-starter runners on the holdout: {thin.sum()}; with a stored trial: {has.sum()}; trial jockey known: {(has & (tj != '')).sum()}; rated jockey: {(has & np.isfinite(tj_rate)).sum()}")
lo = lambda v: f"{v:.2f}"
def grp(mask, lab):
    n = mask.sum()
    if n < 20: print(f"| {lab} | {n} | | | | |"); return
    d = bs[mask] / o[mask]
    print(f"| {lab} | {n} | {won[mask].sum()} | {won[mask].sum()/pm[mask].sum():.2f} | {won[mask].sum()/qb[mask].sum():.2f} | {np.median(d):.2f} | {(d >= 1.25).mean():.0%} |")
print("\n## All first-up / first-starter runners with a trial\n\n| group | runners | winners | A/E vs OUR price | A/E vs BSP | median BSP/open | big drifters |\n|---|---|---|---|---|---|---|")
grp(has, "all")
grp(has & tj_top, "trial ridden by a top-fifth jockey")
grp(has & np.isfinite(tj_rate) & ~tj_top, "trial ridden by another rated jockey")
grp(has & ~np.isfinite(tj_rate), "trial jockey unrated (few race rides: trackwork riders, apprentices)")
grp(has & same, "same jockey trial and today")
grp(has & ~same, "different jockey today")
grp(has & today_top & ~tj_top, "top jockey today, NOT on the trial")
grp(has & tj_top & today_top, "top jockey on the trial AND today")
grp(has & (tfin == 1), "won the trial")
grp(has & (tfin > 1) & (tfin <= 3), "placed 2nd-3rd in the trial")
grp(has & (tfin > 3), "unplaced in the trial")
grp(has & (tdays <= 21), "trial within 21 days")
grp(has & (tdays > 21), "trial more than 21 days back")
# halves for the top-jockey split
cut = "2026-08-03"
print("\n| by half: A/E vs OUR price | first half | second half |\n|---|---|---|")
for mask, lab in ((has & tj_top, "top-fifth jockey on the trial"), (has & ~tj_top & np.isfinite(tj_rate), "other rated jockey on the trial"), (has & ~np.isfinite(tj_rate), "unrated trial jockey"), (has & (tfin == 1), "won the trial"), (has & (tfin > 3), "unplaced in the trial")):
    a = [f"{won[mask & h].sum()}/{pm[mask & h].sum():.1f} = {won[mask & h].sum()/max(pm[mask & h].sum(),1e-9):.2f}" for h in (date < cut, date >= cut)]
    print(f"| {lab} | {a[0]} | {a[1]} |")
print("\n| by half: A/E vs OUR price | first half | second half |\n|---|---|---|")
for mask, lab in ((has & (tdays > 21), "trial more than 21 days back"), (has & (tdays <= 21), "trial within 21 days"), (has & (tfin > 1) & (tfin <= 3), "placed 2nd-3rd in the trial")):
    a = [f"{won[mask & h].sum()}/{pm[mask & h].sum():.1f} = {won[mask & h].sum()/max(pm[mask & h].sum(),1e-9):.2f}" for h in (date < cut, date >= cut)]
    print(f"| {lab} | {a[0]} | {a[1]} |")
# our open bets among these
import stake_rule
print("\nhow many of OUR first-up/first-starter open bets fall in each: won trial / >21 days")
