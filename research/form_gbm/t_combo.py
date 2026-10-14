"""Gear detail trial (15 Oct 2026, founder: "Why don't we do any of that?"). Adds to the F9 inputs:
  - today, per common item: worn, first time, coming off (from each entry's full gear list, gear_table.py)
  - from the horse's own earlier races in our data (the past-run rows carry no gear): what it wore last start, and
    how its ratings in that item compare with its ratings without it
Same stage-1 trees and settings as t_more_data.py, trained on everything before 3 Jun 2026, scored on the holdout.
python3.13 t_combo.py GEAR_TABLE.tsv WIDE_TABLE.tsv [seeds]"""
import numpy as np, sys, time, json, re, collections, lab, lightgbm as lgb, bench as b
D = b.load("ds/model_ds_new.npz")
import price_day as pdm, stage2
ri = D["race_idx"]; nR = D["n_races"]; t0 = time.time()
rid = D["race_id"].astype(str); hid = D["horse_id"].astype(str); rdate = D["date"].astype(str)
# ---- the gear table
G = {}
for line in open(sys.argv[1]):
    if line.startswith("#") or "\t" not in line: continue
    r, d, h, js = line.rstrip("\n").split("\t", 3)
    try: G[(r, h)] = json.loads(js)
    except ValueError: pass
def item(name):
    n = name.lower()
    for k, pat in (("blinkers", "blink"), ("winkers", "winker"), ("visors", "visor"), ("tongue", "tongue"), ("noseroll", "nose roll"),
                   ("earmuffs", "ear muff|earmuff|ear plug|earplug|hood"), ("lugging", "lugging|bit|cross"), ("pacifier", "pacifier"),
                   ("bandages", "bandage|boot"), ("shoes", "shoe|plate|bar")):
        if re.search(pat, n): return k
    return "other"
ITEMS = ["blinkers", "winkers", "visors", "tongue", "noseroll", "earmuffs", "lugging", "pacifier", "bandages", "shoes", "other"]
codes = collections.Counter(c for v in G.values() for _, _, c in v); print("change codes", codes.most_common(12), flush=True)
first = lambda c: c.upper() == "ON_FIRST_TIME"
off = lambda c: c.upper().startswith("OFF")
backon = lambda c: c.upper() == "ON_AGAIN"
n = len(ri); cov = 0
cur = {f"g_{k}_{w}": np.zeros(n, np.float32) for k in ITEMS for w in ("worn", "first", "off")}
cur["g_n_off"] = np.zeros(n, np.float32); cur["g_n_on"] = np.zeros(n, np.float32); cur["g_n_back"] = np.zeros(n, np.float32)
worn_set = [None] * n
for i in range(n):
    g = G.get((rid[ri[i]], hid[i]))
    if g is None:
        for k in cur: cur[k][i] = np.nan
        continue
    cov += 1; ws = set()
    for name, on, ch in g:
        k = item(name)
        if on: cur[f"g_{k}_worn"][i] = 1; ws.add(k)
        if first(ch): cur[f"g_{k}_first"][i] = 1; cur["g_n_on"][i] += 1
        if off(ch): cur[f"g_{k}_off"][i] = 1; cur["g_n_off"][i] += 1
        if backon(ch): cur["g_n_back"][i] += 1
    worn_set[i] = ws
print(f"gear rows matched {cov} of {n}", flush=True)
# ---- the horse's own earlier races in our data: last start's gear, and its rating with vs without each key item
pf = list(D["past_fields"]); RAT = D["P"][:, :, pf.index("rating")]
row_of = {(rid[ri[i]], hid[i]): i for i in range(n)}
pri = D["past_race_ids"].astype(str)
past = {}
KEY = ["blinkers", "tongue", "noseroll", "earmuffs", "lugging"]
for k in KEY:
    past[f"p_{k}_last"] = np.full(n, np.nan, np.float32); past[f"p_{k}_effect"] = np.full(n, np.nan, np.float32)
past["p_same_as_last"] = np.full(n, np.nan, np.float32); past["p_runs_known"] = np.zeros(n, np.float32)
for i in range(n):
    known = []
    for j in range(pri.shape[1]):
        r = pri[i, j]
        if not r: continue
        k = row_of.get((r, hid[i]))
        if k is not None and worn_set[k] is not None and np.isfinite(RAT[i, j]):
            known.append((j, worn_set[k], RAT[i, j]))
    past["p_runs_known"][i] = len(known)
    if not known: continue
    j0, last, _ = min(known, key=lambda t: t[0])
    if worn_set[i] is not None: past["p_same_as_last"][i] = float(last == worn_set[i])
    for k in KEY:
        past[f"p_{k}_last"][i] = float(k in last)
        a = [rt for _, s, rt in known if k in s]; bb = [rt for _, s, rt in known if k not in s]
        if a and bb: past[f"p_{k}_effect"][i] = np.mean(a) - np.mean(bb)
GX = np.column_stack(list(cur.values()) + list(past.values())).astype(np.float32); gnames = list(cur) + list(past)
print("gear inputs", GX.shape, f"{time.time()-t0:.0f}s", flush=True)

# ---- past-run price flucs (t_wide.py)
W = [None] * n
for line in open(sys.argv[2]):
    if line.startswith("#") or "\t" not in line: continue
    r, h, js = line.rstrip("\n").split("\t", 2); i = row_of.get((r, h))
    if i is not None:
        try: W[i] = json.loads(js)
        except ValueError: pass
G = {"flucs": {}}
def col(g, name): return G[g].setdefault(name, np.full(n, np.nan, np.float32))
for i, w in enumerate(W):
    if w is None: continue
    past = w.get("past") or []
    # flucs: log(last / first) of each past run's betting, negative = backed (prices can arrive as text)
    def fnum(v):
        try:
            v = float(v); return v if v > 1 else None
        except (TypeError, ValueError): return None
    mv = [np.log(fnum(p[5]) / fnum(p[4])) for p in past[:5] if fnum(p[4]) and fnum(p[5])]
    if past and fnum(past[0][4]) and fnum(past[0][5]):
        col("flucs", "m_last_move")[i] = np.log(fnum(past[0][5]) / fnum(past[0][4])); col("flucs", "m_last_first")[i] = np.log(fnum(past[0][4]))
    if mv: col("flucs", "m_mean5_move")[i] = np.mean(mv); col("flucs", "m_n_backed5")[i] = float(sum(m < -0.15 for m in mv))

FX = np.column_stack(list(G["flucs"].values())).astype(np.float32); fnames = list(G["flucs"])
# ---- F9 as the live model builds it
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
seeds = int(sys.argv[3]) if len(sys.argv) > 3 else 2
out = {}
for name, FF, NN in (("F9", F, nm), ("F9 + gear detail", np.hstack([F, GX]), nm + gnames), ("F9 + past price flucs", np.hstack([F, FX]), nm + fnames), ("F9 + gear detail + flucs", np.hstack([F, GX, FX]), nm + gnames + fnames)):
    preds = []
    for s in range(seeds):
        t1 = time.time(); bst, _ = lab.train(FF, NN, train, q, params=dict(feature_fraction=0.2, extra_trees=True), seed=s, fixed_rounds=4000)
        preds.append(np.log(b.softmax_races(bst.predict(FF)))); print(f"{name} seed {s} {time.time()-t1:.0f}s", flush=True)
        if False:
            g = bst.feature_importance("gain"); top = np.argsort(-g)
            print("gear inputs by gain rank:", [(NN[j], int(np.where(top == j)[0][0]) + 1) for j in range(len(nm), len(NN)) if g[j] > 0][:15], flush=True)
    out[name] = score(b.softmax_races(np.mean(preds, 0)))
print(f"\n| inputs | holdout KL to BSP | log loss vs winners |\n|---|---|---|")
for k, (kl, ll) in out.items(): print(f"| {k} | {kl:.4f} | {ll:.4f} |")
print(f"| opening market | {score(mk)[0]:.4f} | {score(mk)[1]:.4f} |")
