"""Every unread Form King field, tested group by group (15 Oct 2026, founder: "what else aren't we testing").
Same stage-1 trees and settings as t_gear.py / t_more_data.py: trained on every race before 3 Jun 2026, scored on the
holdout against BSP and winners. Groups, each added to F9 on its own and then all together:
  comments  race-review comment flags of past runs (slow start, held up, wide, keen, eased, ran on, led)
  flucs     how the horse was backed in past runs (first fluc to last fluc)
  pastgear  gear in past runs from Form King's own past-run gear field
  misc      position at 1200m, spell length, night meetings
  horse     age in days from the foal date, racing at its home track, other acceptances
python3.13 t_wide.py WIDE_TABLE.tsv [seeds]"""
import numpy as np, sys, time, json, lab, bench as b
from datetime import date
D = b.load("ds/model_ds_new.npz")
import price_day as pdm, stage2
ri = D["race_idx"]; nR = D["n_races"]; n = len(ri); t0 = time.time()
rid = D["race_id"].astype(str); hid = D["horse_id"].astype(str); rdate = D["date"].astype(str)[ri]; trk = D["track"].astype(str)[ri]
row = {(rid[ri[i]], hid[i]): i for i in range(n)}
W = [None] * n
for line in open(sys.argv[1]):
    if line.startswith("#") or "\t" not in line: continue
    r, h, js = line.rstrip("\n").split("\t", 2); i = row.get((r, h))
    if i is not None:
        try: W[i] = json.loads(js)
        except ValueError: pass
print("matched", sum(w is not None for w in W), "of", n, flush=True)
pf = list(D["past_fields"]); RAT = D["P"][:, :, pf.index("rating")]
FL = "SBWKEFL"; KEY = {"blinkers": "blink", "tongue": "tongue", "noseroll": "nose roll", "earmuffs": "muff", "lugging": "lugging"}
G = {k: {} for k in ("comments", "flucs", "pastgear", "misc", "horse")}
def col(g, name): return G[g].setdefault(name, np.full(n, np.nan, np.float32))
for i, w in enumerate(W):
    if w is None: continue
    past = w.get("past") or []
    # comments
    if past:
        for f in FL: col("comments", f"c_last_{f}")[i] = float(f in (past[0][6] or ""))
        last5 = past[:5]
        for f in FL: col("comments", f"c_n5_{f}")[i] = float(sum(f in (p[6] or "") for p in last5))
        # the horse's rating in runs with an excuse (slow start, held up, wide, eased) against runs without
        exc = [RAT[i, j] for j, p in enumerate(past[:10]) if any(f in (p[6] or "") for f in "SBWE") and np.isfinite(RAT[i, j])]
        clean = [RAT[i, j] for j, p in enumerate(past[:10]) if not any(f in (p[6] or "") for f in "SBWE") and np.isfinite(RAT[i, j])]
        if exc and clean: col("comments", "c_excuse_gap")[i] = np.mean(exc) - np.mean(clean)
        col("comments", "c_last_excuse")[i] = float(any(f in (past[0][6] or "") for f in "SBWE"))
    # flucs: log(last / first) of each past run's betting, negative = backed (prices can arrive as text)
    def fnum(v):
        try:
            v = float(v); return v if v > 1 else None
        except (TypeError, ValueError): return None
    mv = [np.log(fnum(p[5]) / fnum(p[4])) for p in past[:5] if fnum(p[4]) and fnum(p[5])]
    if past and fnum(past[0][4]) and fnum(past[0][5]):
        col("flucs", "m_last_move")[i] = np.log(fnum(past[0][5]) / fnum(past[0][4])); col("flucs", "m_last_first")[i] = np.log(fnum(past[0][4]))
    if mv: col("flucs", "m_mean5_move")[i] = np.mean(mv); col("flucs", "m_n_backed5")[i] = float(sum(m < -0.15 for m in mv))
    # past gear from Form King's past-run gear field
    if past:
        worn0 = (past[0][2] or "").lower()
        for k, pat in KEY.items():
            col("pastgear", f"pg_last_{k}")[i] = float(pat in worn0)
            a = [RAT[i, j] for j, p in enumerate(past[:10]) if pat in (p[2] or "").lower() and np.isfinite(RAT[i, j])]
            bb = [RAT[i, j] for j, p in enumerate(past[:10]) if pat not in (p[2] or "").lower() and np.isfinite(RAT[i, j])]
            if a and bb: col("pastgear", f"pg_effect_{k}")[i] = np.mean(a) - np.mean(bb)
        col("pastgear", "pg_changes_last")[i] = float(len([x for x in (past[0][3] or "").split("|") if x]))
    # misc
    if past:
        p0 = past[0]
        try:
            v = float(p0[8])
            if v > 0: col("misc", "x_pos1200_last")[i] = v
        except (TypeError, ValueError): pass
        try: col("misc", "x_spell_last")[i] = float(p0[9])
        except (TypeError, ValueError): pass
        col("misc", "x_night_share")[i] = float(np.mean([bool(p[11]) for p in past[:10]]))
    # horse
    if w.get("foal"):
        fd = date.fromtimestamp(w["foal"] / 1000); col("horse", "h_age_days")[i] = float((date.fromisoformat(rdate[i]) - fd).days)
        col("horse", "h_foal_month")[i] = float((fd.month - 8) % 12)   # months after 1 Aug, the southern-hemisphere birthday
    if w.get("home"): col("horse", "h_home_track")[i] = float(str(w["home"]).lower() == trk[i].lower())
    if w.get("acc") is not None: col("horse", "h_acceptances")[i] = float(w["acc"])
# comments exist only in races pulled from Oct 2026 on (and the Jul-Sep 2025 backfill), none in the holdout: not testable yet
del G["comments"]; G["horse"].pop("h_acceptances", None)   # acceptances: never populated
for k, v in G.items(): print(k, len(v), "inputs", flush=True)
F, nm = pdm.inputs()
TR = stage2.trials(D["P"], D["past_fields"], ri); SEC = stage2.sections(D["S"], D["sec_fields"], D["P"], D["past_fields"], ri, nR)
F = np.hstack([F, TR, SEC]).astype(np.float32); F[~np.isfinite(F)] = np.nan
nm = list(nm) + [f"tr_{i}" for i in range(TR.shape[1])] + [f"sec_{i}" for i in range(SEC.shape[1])]
assert nm == open("F9_names.txt").read().split("\n")
lab.D = D; lab.ri0 = ri
races = np.arange(nR); hold = races[D["date"] >= "2026-06-03"]; train = races[D["date"] < "2026-06-03"]
q = D["q"]; won = D["finish"] == 1; mk = D["mkt"]
hm = np.isin(ri, hold); hri = np.unique(ri[hm], return_inverse=True)[1]; nh = hri.max() + 1
ok = (np.bincount(hri, weights=(q[hm] > 0) & (mk[hm] > 0), minlength=nh) == np.bincount(hri, minlength=nh)) & (np.bincount(hri, weights=won[hm], minlength=nh) == 1)
def score(p):
    p = p[hm]; s = np.bincount(hri, weights=p, minlength=nh); p = p / s[hri]; m = ok[hri]
    kl = np.sum(np.where(q[hm][m] > 0, q[hm][m] * np.log(np.maximum(q[hm][m], 1e-300) / np.maximum(p[m], 1e-12)), 0)) / ok.sum()
    return kl, -np.mean(np.log(np.maximum(p[m & won[hm]], 1e-12)))
seeds = int(sys.argv[2]) if len(sys.argv) > 2 else 2
def fit(FF, NN, label):
    preds = []
    for s in range(seeds):
        t1 = time.time(); bst, _ = lab.train(FF, NN, train, q, params=dict(feature_fraction=0.2, extra_trees=True), seed=s, fixed_rounds=4000)
        preds.append(np.log(b.softmax_races(bst.predict(FF)))); print(f"{label} seed {s} {time.time()-t1:.0f}s", flush=True)
    return score(b.softmax_races(np.mean(preds, 0)))
res = {"F9 (current inputs)": fit(F, nm, "F9")}
for g, cols in G.items():
    res[f"+ {g}"] = fit(np.hstack([F, np.column_stack(list(cols.values()))]), nm + list(cols), g)
allc = [c for cols in G.values() for c in cols.values()]; alln = [k for cols in G.values() for k in cols]
res["+ all four"] = fit(np.hstack([F, np.column_stack(allc)]), nm + alln, "all")
print(f"\n| inputs | holdout KL to BSP | log loss vs winners |\n|---|---|---|")
for k, (kl, ll) in res.items(): print(f"| {k} | {kl:.4f} | {ll:.4f} |")
print(f"| opening market | {score(mk)[0]:.4f} | {score(mk)[1]:.4f} |")
