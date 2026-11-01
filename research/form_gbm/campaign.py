"""BSP campaign (1 Nov 2026, founder: "find a way for us to get closer to BSP. I have so much time, just run").
Stage-1 trees member (race-softmax against BSP, as oof_trees.py's sm), lab split: fitted on INNER (oldest 56% of races),
early-stopped on VALID (the next 14%, from 13 Mar 2026), scored on VALID (decision) and on TE (the newest 30%, from 12 May,
never used for any decision; scored with the INNER-fitted model, the same handicap for every row). Each row appends to
campaign.md as it finishes. KL to BSP is the target; winner log loss and the open-rule plan on TE are reported beside it."""
import numpy as np, lab, bench as b, gbm, lightgbm as lgb, time, json, sys, functools
D = b.D; ri = D["race_idx"]; nR = D["n_races"]; q = D["q"]
F = np.load("F9.npy"); names = open("F9_names.txt").read().split("\n"); assert F.shape[1] == len(names), (F.shape, len(names))
z = np.load("ds/model_ds.npz", allow_pickle=True); o = z["open"].astype(float); bs = z["bsp"].astype(float); won = D["won"]
BASE = dict(feature_fraction=0.2, extra_trees=True)
LOG = "campaign.md"
def plan(p, races):
    m = b.runner_mask(races) & np.isfinite(o) & (o > 1); ours = 1 / np.maximum(p, 1e-12)
    bet = m & (p * o >= 1.2) & (ours >= 1.6) & (ours <= 15) & (o < 3 * ours)
    if bet.sum() == 0: return 0, 0.0
    return int(bet.sum()), float(np.where(won == 1, (o - 1) * 0.93, -1.0)[bet].mean() * 100)
def log(name, p, rounds, t0, note=""):
    v = b.score(p, lab.VALID); te = b.score(p, lab.TE); n, roi = plan(p, lab.TE)
    line = f"| {name} | {v[0]:.4f} | {te[0]:.4f} | {te[1]:.4f} | {te[2]:.1%} | {n} / {roi:+.1f}% | {rounds} | {(time.time()-t0)/60:.0f} | {note} |"
    print(line, flush=True); open(LOG, "a").write(line + "\n")
    return v[0], te[0]
def fit(params, seed=0, Fm=None, races=None, aug=True, share=0.8):
    Fm = F if Fm is None else Fm; races = lab.INNER if races is None else races
    orig = lab.augmented
    if share != 0.8: lab.augmented = lambda Fx, nx, share_=share, seed=1: orig(Fx, nx, share_, seed)
    try:
        bst, it = lab.train(Fm, names if Fm is F else [f"c{i}" for i in range(Fm.shape[1])], races, q, params={**BASE, **params}, valid_races=lab.VALID, seed=seed, aug=aug, rounds=5000)
    finally:
        lab.augmented = orig
    return bst, it
def run(name, params={}, seeds=(0,), Fm=None, races=None, aug=True, share=0.8, note=""):
    t0 = time.time(); logs = []; its = []
    for s in seeds:
        bst, it = fit(params, s, Fm, races, aug, share); its.append(it)
        logs.append(np.log(np.maximum(b.softmax_races(bst.predict(F if Fm is None else Fm, num_iteration=it)), 1e-12)))
    p = b.softmax_races(np.mean(logs, 0)); np.save(f"camp_{name}.npy", p)
    log(name, p, "/".join(map(str, its)), t0, note); return p, bst
if not __import__("os").path.exists(LOG):
    open(LOG, "w").write("| experiment | VALID KL | TE KL | TE log loss | TE top pick | TE plan bets / ROI open | rounds | min | note |\n|---|---|---|---|---|---|---|---|---|\n")
todo = sys.argv[1:] or ["base", "grid", "bag", "aug", "dart", "prune", "learn", "linear", "prep"]
P0, B0 = None, None
if "base" in todo: P0, B0 = run("base", note="feature_fraction 0.2, extra_trees, lr 0.06, 15 leaves, min_data 100, l2 10 (live)")
if "grid" in todo:
    for nm_, pr in [("lr0.03", dict(learning_rate=0.03)), ("leaves7", dict(num_leaves=7)), ("leaves31", dict(num_leaves=31)),
                    ("mindata50", dict(min_data_in_leaf=50)), ("mindata200", dict(min_data_in_leaf=200)), ("l2_30", dict(lambda_l2=30.0)),
                    ("l2_3", dict(lambda_l2=3.0)), ("ff0.1", dict(feature_fraction=0.1)), ("ff0.3", dict(feature_fraction=0.3)),
                    ("no_extra_trees", dict(extra_trees=False)), ("mindata30_leaves31", dict(min_data_in_leaf=30, num_leaves=31))]:
        run(nm_, pr)
if "bag" in todo: run("base_bag3", seeds=(0, 1, 2), note="3 seeds averaged in log space")
if "aug" in todo:
    run("aug_off", aug=False, note="no blanked copy"); run("aug_share0.5", share=0.5, note="blanked copy on 50% not 80%")
if "dart" in todo:
    try: run("dart", dict(boosting="dart", drop_rate=0.1, skip_drop=0.5))
    except Exception as e: open(LOG, "a").write(f"| dart | failed: {e} |\n")
if "prune" in todo:
    if B0 is None: P0, B0 = run("base")
    g = B0.feature_importance("gain"); keep = np.argsort(-g)[: len(g) // 2]; keep.sort()
    run("prune_top50", Fm=F[:, keep], note=f"{len(keep)} of {len(g)} inputs by gain")
    keep = np.argsort(-g)[: len(g) // 4]; keep.sort(); run("prune_top25", Fm=F[:, keep], note=f"{len(keep)} inputs")
if "learn" in todo:
    dts = D["date"][lab.INNER]; order = lab.INNER[np.argsort(dts, kind="stable")]
    for sh in (0.5, 0.75):
        run(f"learn_newest{int(sh*100)}", races=order[-int(len(order) * sh):], note=f"trained on the newest {int(sh*100)}% of INNER (learning curve: does more data help?)")
if "linear" in todo:
    t0 = time.time(); mu = np.nanmean(F[b.runner_mask(lab.INNER)], 0); sd = np.nanstd(F[b.runner_mask(lab.INNER)], 0); sd[~np.isfinite(sd) | (sd == 0)] = 1
    Z = np.clip(np.nan_to_num((F - mu) / sd, nan=0.0), -5, 5)
    beta = b.clogit(Z, lab.INNER, q, ridge=30.0, iters=30); pl = b.softmax_races(Z @ beta); np.save("camp_linear.npy", pl)
    log("linear_clogit", pl, "-", t0, "ridge conditional logit on standardised F9, BSP target")
    if P0 is None: P0 = np.load("camp_base.npy")
    best = None
    for w in (0.0, 0.1, 0.2, 0.3):
        pb = b.softmax_races((1 - w) * np.log(np.maximum(P0, 1e-12)) + w * np.log(np.maximum(pl, 1e-12))); v = b.score(pb, lab.VALID)[0]
        if best is None or v < best[0]: best = (v, w, pb)
    log(f"base+linear w={best[1]}", best[2], "-", t0, "blend weight chosen on VALID")
if "prep" in todo:
    import prep_feats
    Fp = prep_feats.build(D["P"], list(D["past_fields"]), D["X"][:, D["colidx"]["raw_run_in_prep"]].astype(float))
    F2 = np.hstack([F] + [v[:, None].astype(np.float32) for v in Fp.values()]); F2[~np.isfinite(F2)] = np.nan
    run("prep_inputs", Fm=F2, note="came back better/worse, prep trend, runs since best, prev prep rise")
print("CAMPAIGN DONE", flush=True)
