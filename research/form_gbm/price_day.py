"""Price a day's races with the all-race models: combine history + the day, rebuild the 743 inputs, predict."""
import numpy as np, bench as b, feats, feats2, h2h, rolling, bias, lightgbm as lgb, sys

def combined(hist="ds/model_ds.npz", day="up/upcoming.npz"):
    H = np.load(hist); U = np.load(day)
    cols = list(H["cols"]); ucols = {c: i for i, c in enumerate(U["cols"])}
    UX = np.full((U["X"].shape[0], len(cols)), np.nan, np.float32)
    for j, c in enumerate(cols):
        if c in ucols: UX[:, j] = U["X"][:, ucols[c]]
    missing = [c for c in cols if c not in ucols]
    D = {"X": np.vstack([H["X"], UX]), "cols": H["cols"], "past_fields": H["past_fields"]}
    for k in ("P", "horse_id", "name", "bsp", "sp", "finish", "open", "past_race_ids", "past_jockeys", "jockey", "trainer", "sire", "dam_sire", "training_location"):
        D[k] = np.concatenate([H[k], U[k]])
    nR = len(H["race_id"])
    D["race_idx"] = np.concatenate([H["race_idx"], U["race_idx"] + nR])
    for k in ("race_id", "date", "track", "distance", "lws", "going", "field", "pre_jump"):
        D[k] = np.concatenate([H[k], U[k]])
    return D, nR, U, missing

def install(D):
    b.D = D; ri = D["race_idx"]; n_r = int(ri.max()) + 1
    starts = np.searchsorted(ri, np.arange(n_r)); D["starts"], D["ends"], D["n_races"] = starts, np.append(starts[1:], len(ri)), n_r
    D["q"] = b.norm_inv(D["bsp"]); D["mkt"] = b.norm_inv(D["open"]); D["won"] = (D["finish"] == 1).astype(float)
    D["colidx"] = {c: i for i, c in enumerate(D["cols"])}

def inputs():
    D = b.D
    F2, n2 = feats.build()
    E = feats2.extra(); cols = [F2]; nm = list(n2)
    for k, v in E.items():
        v = np.asarray(v, float); cols.append(v[:, None]); nm.append(k)
        if k.startswith("x_") and k not in ("x_is_firstup", "x_n_firstup", "x_runs_this_prep"):
            a, m, r = feats.relative(v); cols += [a[:, None], m[:, None], r[:, None]]; nm += [f"{k}__vmax", f"{k}__vmean", f"{k}__rank"]
    for k, v in h2h.features().items():
        cols.append(v[:, None]); nm.append(k)
        if k.startswith("h_"):
            a, m, r = feats.relative(v); cols += [a[:, None], r[:, None]]; nm += [f"{k}__vmax", f"{k}__rank"]
    for k, v in rolling.features().items():
        cols.append(v[:, None]); nm.append(k)
        if k.endswith("_ae") or k.endswith("_wr"):
            a, m, r = feats.relative(v); cols += [a[:, None], r[:, None]]; nm += [f"{k}__vmax", f"{k}__rank"]
    for k, v in bias.features().items(): cols.append(v[:, None]); nm.append(k)
    F = np.hstack(cols).astype(np.float32); F[~np.isfinite(F)] = np.nan
    return F, nm

def predict_trees(F):
    sm = [np.log(b.softmax_races(lgb.Booster(model_file=f"all_sm{s}.txt").predict(F))) for s in range(5)]
    rg = [np.log(b.softmax_races(lgb.Booster(model_file=f"all_rg{s}.txt").predict(F))) for s in range(5)]
    return b.softmax_races(0.7 * np.log(b.softmax_races(np.mean(sm, 0))) + 0.3 * np.log(b.softmax_races(np.mean(rg, 0))))


def predict(F, n_hist_races, names, epochs=14, seeds=5):
    """trees (all-race models) blended with race-softmax nets trained here on the history races: 40/25/35."""
    D = b.D                     # the combined history + day, installed by install()
    import lab, nn              # importing lab loads the history-only data into b.D; put the combined back
    b.D = D
    lab.D = D; lab.ri0 = D["race_idx"]; nn.D = D; nn.ri = D["race_idx"]; nn.nR = D["n_races"]
    sm = [np.log(b.softmax_races(lgb.Booster(model_file=f"all_sm{s}.txt").predict(F))) for s in range(5)]
    rg = [np.log(b.softmax_races(lgb.Booster(model_file=f"all_rg{s}.txt").predict(F))) for s in range(5)]
    p_sm = b.softmax_races(np.mean(sm, 0)); p_rg = b.softmax_races(np.mean(rg, 0))
    hist = np.arange(n_hist_races)
    nets = [np.log(np.maximum(nn.fit(F, names, hist, None, seed=s, fixed_epochs=epochs)[0], 1e-12)) for s in range(seeds)]
    p_nn = b.softmax_races(np.mean(nets, 0))
    return b.softmax_races(0.4 * np.log(p_sm) + 0.25 * np.log(p_rg) + 0.35 * np.log(p_nn))
