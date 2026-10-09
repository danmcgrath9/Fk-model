"""Does our stored (post-race-pulled) form price races differently from Dave's point-in-time archive? (9 Oct 2026)
Day files for 20-26 Aug 2026 VIC built by the SAME pull + export code from each copy (fk-archive-replay workflow).
A stage-1 tree model is trained only on races before 20 Aug (so neither copy's races were seen in training), then
prices both copies. If post-race information leaked into our copy, our copy gives the winners more chance than the
clean copy does. Scored per race on the winner: log of the chance given, and against the market at BSP.
python t_archive_eval.py DIR_WITH_NPZ"""
import numpy as np, glob, os, sys, bench as b, price_day as pdm, lab, stage2, lightgbm as lgb
src = sys.argv[1]
def concat(files):
    Us = [dict(np.load(f, allow_pickle=True)) for f in files]
    allc = []
    for u in Us:
        for c in u["cols"]:
            if c not in allc: allc.append(c)
    for u in Us:   # align X to the union of columns (days differ by a column or two)
        ci = {c: j for j, c in enumerate(u["cols"])}; X = np.full((u["X"].shape[0], len(allc)), np.nan, np.float32)
        for j, c in enumerate(allc):
            if c in ci: X[:, j] = u["X"][:, ci[c]]
        u["X"] = X; u["cols"] = np.array(allc)
    out = {}; off = 0
    nrun = [len(u["race_idx"]) for u in Us]; nrac = [len(u["race_id"]) for u in Us]
    for k in Us[0]:
        v0 = Us[0][k]
        if k == "race_idx":
            parts = []; off = 0
            for u in Us: parts.append(u[k] + off); off += len(u["race_id"])
            out[k] = np.concatenate(parts)
        elif hasattr(v0, "shape") and v0.ndim >= 1 and all(u[k].shape[:1] == (nr,) for u, nr in zip(Us, nrun)) and k not in ("cols", "past_fields", "sec_fields"):
            out[k] = np.concatenate([u[k] for u in Us])
        elif hasattr(v0, "shape") and v0.ndim >= 1 and all(u[k].shape[:1] == (nc,) for u, nc in zip(Us, nrac)) and k not in ("cols", "past_fields", "sec_fields"):
            out[k] = np.concatenate([u[k] for u in Us])
        else:
            out[k] = v0
    return out
copies = {}
for tag in ("arch", "ours"):
    fs = sorted(glob.glob(os.path.join(src, f"{tag}_*.npz")))
    U = concat(fs); p = f"/tmp/{tag}_all.npz"; np.savez(p, **U); copies[tag] = p
    print(tag, len(fs), "days", len(U["race_id"]), "races", len(U["race_idx"]), "runners")
res = {}; model = None
for tag in ("arch", "ours"):
    D, nR, U, missing = pdm.combined(day=copies[tag]); pdm.install(D)
    F, nm = pdm.inputs()
    S_all = np.concatenate([np.load("S_hist.npy"), U["S"]]); SF = U["sec_fields"]
    TR = stage2.trials(D["P"], D["past_fields"], D["race_idx"]); SEC = stage2.sections(S_all, SF, D["P"], D["past_fields"], D["race_idx"], int(D["race_idx"].max()) + 1)
    F = np.hstack([F, TR, SEC]).astype(np.float32); F[~np.isfinite(F)] = np.nan
    ri = D["race_idx"]; dates = D["date"].astype(str)
    if model is None:
        lab.D = D; lab.ri0 = ri
        train = np.where((np.arange(D["n_races"]) < nR) & (dates < "2026-08-20") & np.isfinite(np.bincount(ri, weights=D["q"], minlength=D["n_races"])))[0]
        print("training on", len(train), "races before 20 Aug", flush=True)
        model, _ = lab.train(F, list(nm) + [f"tr_{i}" for i in range(TR.shape[1])] + [f"sec_{i}" for i in range(SEC.shape[1])],
                             train, D["q"], params=dict(feature_fraction=0.2, extra_trees=True), seed=0, fixed_rounds=1500)
    p = b.softmax_races(model.predict(F))
    day = ri >= nR
    res[tag] = dict(p=p[day], ri=ri[day] - nR, won=D["won"][day], q=D["q"][day], name=D["name"][day], rid=D["race_id"][ri[day]], missing=missing,
                    op=D["open"][day], bsp=D["bsp"][day])
    print(tag, "missing cols", len(missing))
A, O = res["arch"], res["ours"]
# pair runners across copies by race id + name
ka = {(r, str(n).lower()): i for i, (r, n) in enumerate(zip(A["rid"], A["name"]))}
pairs = [(ka[(r, str(n).lower())], j) for j, (r, n) in enumerate(zip(O["rid"], O["name"])) if (r, str(n).lower()) in ka]
ia = np.array([x for x, _ in pairs]); io = np.array([y for _, y in pairs])
print(f"\nrunners paired: {len(pairs)}")
w = A["won"][ia] == 1
for nm_, P in (("archive (clean)", A["p"][ia]), ("ours (post-race pull)", O["p"][io]), ("market at BSP", A["q"][ia])):
    lw = np.log(np.clip(P[w], 1e-9, 1))
    print(f"  {nm_:24s} winners {w.sum()}  mean log chance on winner {lw.mean():+.3f}  mean chance on winner {P[w].mean()*100:.1f}%")
d = np.log(O["p"][io][w]) - np.log(A["p"][ia][w])
print(f"  ours minus archive on the winner (log): mean {d.mean():+.3f}, sd {d.std():.3f}, ours higher in {(d>0).mean()*100:.0f}% of races; t = {d.mean()/(d.std()/np.sqrt(len(d))):.2f}")
dl = np.log(O["p"][io][~w]) - np.log(A["p"][ia][~w])
print(f"  same on the losers: mean {dl.mean():+.3f}")
corr = np.corrcoef(np.log(A["p"][ia]), np.log(O["p"][io]))[0, 1]
print(f"  correlation of log chances between copies: {corr:.3f}; mean abs difference in price: {np.mean(np.abs(1/A['p'][ia]-1/O['p'][io])/(1/A['p'][ia]))*100:.1f}%")

np.savez("/tmp/archive_eval_res.npz", pa=A["p"][ia], po=O["p"][io], won=A["won"][ia], op_a=A["op"][ia], op_o=O["op"][io], bsp=A["bsp"][ia], rid=A["rid"][ia], name=A["name"][ia])
print("\nopening price, ours vs archive: mean abs difference", f"{np.nanmean(np.abs(O['op'][io]/A['op'][ia]-1))*100:.1f}%", "identical", f"{np.mean(np.isclose(O['op'][io], A['op'][ia]))*100:.0f}%")
def bt(P, op, label):
    ok = np.isfinite(op) & (op > 1); v = P * op - 1; ours_ = 1 / P
    m = ok & (v >= 0.2) & (ours_ >= 1.6) & (ours_ <= 15) & (op < 3 / P)
    st = np.minimum(4.0, 75 * np.clip(((P / op) ** 0.5 * op - 1) / (op - 1), 0, None)) * 5 / 8
    wn = A["won"][ia] == 1
    prof = np.where(m, np.where(wn, st * (op - 1), -st), 0)
    print(f"  {label:44s} bets {m.sum():3d}  winners {(m & wn).sum():2d}  staked {st[m].sum():6.1f}u  profit {prof.sum():+7.1f}u  ROI {prof.sum()/max(st[m].sum(),1e-9)*100:+6.1f}%")
    return m
print("\nBetting rules on these 66 races (value 20c+ at the open, our price $1.60-$15, open under 3x ours, stakes x5/8; no first-up/first-starter blocks):")
ma = bt(A["p"][ia], A["op"][ia], "clean copy, clean opening price")
mo = bt(O["p"][io], A["op"][ia], "our copy, same (clean) opening price")
bt(O["p"][io], O["op"][io], "our copy, our stored opening price")
print(f"  bets in both: {(ma&mo).sum()}, only clean: {(ma&~mo).sum()}, only ours: {(mo&~ma).sum()}")
