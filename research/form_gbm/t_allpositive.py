"""Founder, 3 Nov 2026: "if there's no negatives, and it's just +++ it's a potential plunge horse? Does that work?"
The page's Why line: the live trees' contributions (all9_sm0-4, pred_contrib) grouped into the page's themes, relative to
the race; a theme shows as + above 0.08 and as - below -0.08. Here the same figures for every v10 holdout runner, and
the sheet bets split by whether any theme is negative. CAVEAT: the all9 trees were trained on every race, holdout
included, so these attributions are in-sample; winners will read a little rosier than a live page would show."""
import numpy as np, re, lightgbm as lgb
src = open("t_all_rules.py").read().split('summ(plan(pm0), "all rules')[0]
exec(src)
ms = open("/home/user/fk-model/research/form_gbm/market_sheet.py").read()
exec(ms[ms.index("THEMES = ["):ms.index("theme_of = []")])
A = np.load("ds/model_ds.npz", allow_pickle=True); F = np.load("F9.npy", mmap_mode="r"); names = open("F9_names.txt").read().split("\n")
ka = {k: i for i, k in enumerate(zip(A["race_id"].astype(str)[A["race_idx"]], A["horse_id"].astype(str)))}
kv = list(zip(z["race_id"].astype(str)[ri], z["horse_id"].astype(str)))
sel = np.where(m)[0]; rows_a = np.array([ka[kv[i]] for i in sel])
Fh = np.asarray(F[rows_a], np.float32)
CT = np.mean([lgb.Booster(model_file=f"all9_sm{s}.txt").predict(Fh, pred_contrib=True)[:, :-1] for s in range(5)], 0)
rr = ri[sel]
for r in np.unique(rr):
    k = rr == r; CT[k] -= CT[k].mean(0)
theme_of = []
for nmn in names:
    for t, rx in THEMES:
        if re.search(rx, nmn): theme_of.append(t); break
theme_of = np.array(theme_of); tnames = [t for t, _ in THEMES]
T = np.column_stack([CT[:, theme_of == t].sum(1) for t in tnames])
nneg = (T < -0.08).sum(1); npos = (T > 0.08).sum(1); worst = T.min(1); best = T.max(1)
pos_of = {i: j for j, i in enumerate(sel)}
b = plan(pmS); idx = np.array([i for i, _ in b]); st = np.array([s for _, s in b]); ratio = bs / o
def line(lab, k, base, stake=None):
    ii = base[k]; n = len(ii)
    if n < 20: print(f"  {lab:40s} {n:4d} (too few)"); return
    s = stake[k] if stake is not None else np.ones(n); w = won[ii]
    plo = np.where(w, s * (o[ii] - 1) * 0.93, -s).sum(); plb = np.where(w, s * (bs[ii] - 1) * 0.92, -s).sum()
    h1 = dd[ii] < "2026-08-01"; p1 = np.where(w, s * (o[ii] - 1) * 0.93, -s)
    print(f"  {lab:40s} {n:4d} bets {w.sum():3d} won | plunge {100*(ratio[ii]<=0.6).mean():3.0f}% BSP/open {np.median(ratio[ii]):.2f} | ours exp {pmS[ii].sum():5.1f} A/E {w.sum()/pmS[ii].sum():4.2f} | open {100*plo/s.sum():+5.0f}% (halves {100*p1[h1].sum()/s[h1].sum():+4.0f}%/{100*p1[~h1].sum()/s[~h1].sum():+4.0f}%) BSP {100*plb/s.sum():+4.0f}%")
J = np.array([pos_of[i] for i in idx]); NN = nneg[J]; NP = npos[J]
print("SHEET BETS (every live rule), by the Why line:")
line("no negative theme at all", NN == 0, idx, st)
line("no negative, 2+ positives", (NN == 0) & (NP >= 2), idx, st)
line("no negative, 3+ positives", (NN == 0) & (NP >= 3), idx, st)
line("one negative theme", NN == 1, idx, st)
line("two or more negatives", NN >= 2, idx, st)
line("worst theme under -0.25", worst[J] < -0.25, idx, st)
line("all sheet bets", np.ones(len(idx), bool), idx, st)
print("\n  by count of negative themes, plunge rate / open ROI:")
for k in range(0, 6):
    kk = NN == k
    if kk.sum() >= 20: line(f"  {k} negatives", kk, idx, st)
print("\nALL RATED RUNNERS $1.60-$15 (first starters out), 1u each:")
Aset = np.array([i for i in sel if not fs[i] and 1.6 <= 1/pmS[i] <= 15]); JA = np.array([pos_of[i] for i in Aset])
line("no negative theme", nneg[JA] == 0, Aset); line("no negative, 2+ positives", (nneg[JA] == 0) & (npos[JA] >= 2), Aset)
line("one negative", nneg[JA] == 1, Aset); line("two or more negatives", nneg[JA] >= 2, Aset); line("all", np.ones(len(Aset), bool), Aset)
print("\n  no negative theme AND the open is 1.2x+ ours (a sheet-style bet):"); line("  ", (nneg[JA] == 0) & (o[Aset] >= 1.2 / pmS[Aset]), Aset)
print("  one+ negative AND the open is 1.2x+ ours:"); line("  ", (nneg[JA] >= 1) & (o[Aset] >= 1.2 / pmS[Aset]), Aset)
