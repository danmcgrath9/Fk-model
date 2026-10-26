"""First starters, tests 2 and 3 (26 Oct 2026, founder: "then do it"): the trainer's record with debutants and the jockey
booked on one. rolling.py already keeps a sire record on first starters and a trainer record on first-uppers; it has no
trainer record on first starters. Added, point-in-time (dataset rows strictly before the race day, expected wins from
BSP, shrunk as the other rolling A/Es): trainer_fs (runs, A/E, win rate), jockey_fs (the jockey on debutants), and, for
first starters only, the booked jockey's 12-month win rate and its rank in the race. Same LightGBM as t_5v10.py, three
seeds, trained on races before 3 Jun 2026, scored from 3 Jun in two date halves: winner log loss on first starters' races
and on all races, KL to BSP, the backed first starters' strike v what the model gave them, and the value-at-open plan.
python3.13 t_fs_feats.py"""
import numpy as np, bench as b, price_day as pdm, stage2, rolling, lightgbm as lgb
D = b.load("ds/model_ds_v10.npz"); b.D = D
F0, nm = pdm.inputs()
TR = stage2.trials(D["P"], D["past_fields"], D["race_idx"])
SEC = stage2.sections(D["S"], D["sec_fields"], D["P"], D["past_fields"], D["race_idx"], D["n_races"])
F0 = np.hstack([F0, TR, SEC]).astype(np.float32); F0[~np.isfinite(F0)] = np.nan
ri = D["race_idx"]; nR = int(ri.max()) + 1; c = D["colidx"]; X = D["X"]; n = len(ri)
from datetime import date
rday = np.array([(date.fromisoformat(d) - date(2020, 1, 1)).days for d in D["date"]])[ri]
fs = np.nan_to_num(X[:, c["f_careerForm_s"]], nan=-1) == 0
won = (D["finish"] == 1).astype(float); q = D["q"]; ok = D["finish"] > 0
def rec(key):
    k = np.where(fs & ok, key, ""); r, w, x = rolling.roll(k, rday, won, q, np.where(fs, key, ""), rday)
    return np.log1p(r), np.where(r > 0, (w + 1) / (x + 1), np.nan), np.where(r > 0, (w + 1) / (r + 10), np.nan), r
tr_runs, tr_ae, tr_wr, tr_r = rec(D["trainer"]); jk_runs, jk_ae, jk_wr, jk_r = rec(D["jockey"])
j12 = X[:, c["jockeyForm_lastTwelveMonthWinPercentage"]].astype(float)
jr = np.full(n, np.nan)
for r_ in range(nR):
    idx = np.where(ri == r_)[0]; v = np.nan_to_num(j12[idx], nan=-1); jr[idx] = (-v).argsort().argsort() + 1
new = {"trainer_fs_runs": np.where(fs, tr_runs, np.nan), "trainer_fs_ae": tr_ae, "trainer_fs_wr": tr_wr,
       "jockey_fs_runs": np.where(fs, jk_runs, np.nan), "jockey_fs_ae": jk_ae, "fs_jockey12_win": np.where(fs, j12, np.nan),
       "fs_jockey_rank": np.where(fs, jr, np.nan)}
F1 = np.hstack([F0] + [v[:, None] for v in new.values()]).astype(np.float32); F1[~np.isfinite(F1)] = np.nan
d = D["date"].astype(str)[ri]; o = D["open"].astype(float); bs = D["bsp"].astype(float)
print(f"first starters {fs.sum()}; with a prior trainer debut record {(fs & (tr_r > 0)).sum()} (median {np.median(tr_r[fs & (tr_r > 0)]):.0f} debutants), "
      f"with a prior jockey debut record {(fs & (jk_r > 0)).sum()}")
trn = d < "2026-06-03"; te = ~trn
okr = np.isfinite(o) & (o > 1) & np.isfinite(bs) & (bs > 1)
rok = (np.bincount(ri, weights=okr.astype(float), minlength=nR) == np.bincount(ri, minlength=nR)) & (np.bincount(ri, weights=won, minlength=nR) >= 1)
mm = te & rok[ri]; fsr = np.bincount(ri, weights=(fs & mm).astype(float), minlength=nR) > 0
qb = np.where(mm, 1 / bs, 0); qb = qb / np.maximum(np.bincount(ri, weights=qb, minlength=nR)[ri], 1e-12)
cut = sorted(set(d[mm]))[len(set(d[mm])) // 2]
P = {}
for lab, F in (("live inputs", F0), ("plus debut records", F1)):
    p = np.zeros(n)
    for seed in range(3):
        m = lgb.LGBMClassifier(n_estimators=600, learning_rate=0.03, num_leaves=31, min_child_samples=40, subsample=0.8,
                               subsample_freq=1, colsample_bytree=0.5, reg_lambda=1.0, random_state=seed, verbose=-1)
        m.fit(F[trn], won[trn]); p += m.predict_proba(F)[:, 1] / 3
        if lab != "live inputs" and seed == 0:
            g = m.booster_.feature_importance("gain"); g = g / g.sum(); k0 = F0.shape[1]
            print("  gain share of the new inputs: " + ", ".join(f"{k} {100*g[k0+i]:.2f}%" for i, k in enumerate(new)))
    s = np.bincount(ri, weights=p, minlength=nR); P[lab] = p / s[ri]
print("\n| half | inputs | races | winner log loss, all | KL to BSP, all | FS races | log loss, FS races | KL, FS races | backed FS won / model gave / BSP | plan bets, ROI open, BSP |\n|---|---|---|---|---|---|---|---|---|---|")
for h, hm in (("early", d < cut), ("late", d >= cut)):
    sel = mm & hm; rs = np.zeros(nR, bool); rs[np.unique(ri[sel])] = True
    for lab, pm in P.items():
        def ll(g): return -np.log(pm[g & (won == 1)]).mean()
        def kl(rr):
            g = sel & rr[ri]; v = np.bincount(ri, weights=np.where(g, qb * np.log(np.maximum(qb, 1e-12) / np.maximum(pm, 1e-12)), 0), minlength=nR); return v[rr].mean()
        bk = sel & fs & (o <= 6)
        ours = 1 / pm; bet = sel & (pm * o >= 1.2) & (ours >= 1.6) & (ours <= 15) & (o < 3 * ours)
        ro = np.where(won == 1, (o - 1) * 0.84, -1.0)[bet].mean(); rb = np.where(won == 1, (bs - 1) * 0.92, -1.0)[bet].mean()
        print(f"| {h} | {lab} | {rs.sum()} | {ll(sel):.4f} | {kl(rs):.4f} | {(rs & fsr).sum()} | {ll(sel & fsr[ri]):.4f} | {kl(rs & fsr):.4f} | "
              f"{won[bk].mean():.1%} / {pm[bk].mean():.1%} / {qb[bk].mean():.1%} ({bk.sum()}) | {bet.sum()}, {100*ro:+.1f}%, {100*rb:+.1f}% |", flush=True)
