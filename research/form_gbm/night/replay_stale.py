"""What does the FROZEN HISTORY cost the live price? (night of 10 Nov 2026)

The live day pricer (price_day3 -> apply_stage2f) reads its history from the model work folder: ds/model_ds.npz and
p_oof_blend9.npy as they were when v10 went live, trained through 14 Oct. Nothing refreshes them. So on 9 Nov a live
price was built with
  * rolling trainer / jockey / sire / stable records that stop at 14 Oct (plus whatever today's runners' own past runs add),
  * the second stage's "what did the market think of this horse / trainer / jockey last time" gaps from races to 14 Oct only:
    a horse that has run since then is priced on the gap from the run BEFORE its last one,
  * collateral form (how last start's rivals went next time) blind to every race after 14 Oct.
Every backtest computes all three from every earlier race, so the backtest is fresher than live and the gap grows daily.

Replay, races 15 Oct - 9 Nov 2026, the FROZEN live v10 models (trees and CatBoost; the network third is left out of both
arms, so both are the no-network blend 0.7 trees + 0.3 CatBoost), stage 2 v6, inputs from the rebuilt dataset:
  STALE  history = races to 14 Oct, the day's own results blanked (what live does)
  FRESH  history = every race before the day (what a nightly refresh of the history files would give)
Both arms take the same out-of-fold prices for the history rows (the 10 Nov challenger's p_oof_blend9, aligned to the
dataset). Scored against BSP and winners; also joined to the committed live files, to see how far the pre-race inputs
were from the rebuilt ones (same trees, same stale history: any difference in p_trees is the inputs).
    python3.13 replay_stale.py     (from a folder holding the frozen live model files, ds/model_ds.npz, p_oof_chal.npy)"""
import json, sys, time
import numpy as np, lightgbm as lgb
import bench as b, price_day as pdm, stage2
from catboost import CatBoost

Z = dict(np.load("ds/model_ds.npz", allow_pickle=True)); POOF = np.load("p_oof_chal.npy")
nrun, nrace = len(Z["race_idx"]), len(Z["race_id"]); rdate = Z["date"].astype(str)
RUN = [k for k, v in Z.items() if v.shape[:1] == (nrun,) and k != "race_idx"]; RACE = [k for k, v in Z.items() if v.shape[:1] == (nrace,)]
FIX = ("cols", "past_fields", "sec_fields")
SM = [lgb.Booster(model_file=f"all9_sm{s}.txt") for s in range(5)]; RG = [lgb.Booster(model_file=f"all9_rg{s}.txt") for s in range(5)]
CB = CatBoost(); CB.load_model("cb_all9.cbm"); S2 = [lgb.Booster(model_file=f"stage2f_{k}.txt") for k in range(3)]
F9 = open("F9_names.txt").read().split("\n")


def subset(rm):
    idx = np.where(rm[Z["race_idx"]])[0]; newr = np.cumsum(rm) - 1
    out = {k: Z[k][idx] for k in RUN}; out.update({k: Z[k][rm] for k in RACE}); out.update({k: Z[k] for k in FIX})
    out["race_idx"] = newr[Z["race_idx"][idx]].astype(np.int32)
    return out, idx


def blank(U):
    """a day as live sees it: no result, no starting price, no open"""
    U = dict(U); U["finish"] = np.zeros_like(U["finish"])
    for k in ("bsp", "sp", "open"): U[k] = np.full(len(U[k]), np.nan)
    return U


def combine(H, U):
    D = {"X": np.vstack([H["X"], U["X"]]), "cols": H["cols"], "past_fields": H["past_fields"]}
    for k in ("P", "horse_id", "name", "bsp", "sp", "finish", "open", "past_race_ids", "past_jockeys", "jockey", "trainer", "sire", "dam_sire", "training_location"):
        D[k] = np.concatenate([H[k], U[k]])
    D["race_idx"] = np.concatenate([H["race_idx"], U["race_idx"] + len(H["race_id"])])
    for k in ("race_id", "date", "track", "distance", "lws", "going", "field", "pre_jump"):
        D[k] = np.concatenate([H[k], U[k]])
    return D


def smx(s, ri, n):
    mx = np.full(n, -np.inf); np.maximum.at(mx, ri, s); e = np.exp(s - mx[ri]); return e / np.bincount(ri, weights=e, minlength=n)[ri]


def stage1(H, U):
    D = combine(H, U); pdm.install(D); F, nm = pdm.inputs()
    S_all = np.concatenate([H["S"], U["S"]])
    TR = stage2.trials(D["P"], D["past_fields"], D["race_idx"]); SEC = stage2.sections(S_all, U["sec_fields"], D["P"], D["past_fields"], D["race_idx"], D["n_races"])
    F = np.hstack([F, TR, SEC]).astype(np.float32); F[~np.isfinite(F)] = np.nan
    nm = list(nm) + [f"tr_{i}" for i in range(TR.shape[1])] + [f"sec_{i}" for i in range(SEC.shape[1])]
    assert nm == F9, "inputs do not match the live model's list"
    Fu = F[len(H["race_idx"]):]; uri, n = U["race_idx"], len(U["race_id"]); f = lambda s: smx(s, uri, n)
    psm = f(np.mean([np.log(f(m.predict(Fu))) for m in SM], 0)); prg = f(np.mean([np.log(f(m.predict(Fu))) for m in RG], 0))
    pt = f(0.7 * np.log(psm) + 0.3 * np.log(prg)); pc = f(CB.predict(Fu))
    return pt, pc, f(0.7 * np.log(pt) + 0.3 * np.log(pc))


def stage2f(H, p_hist, U, up_p):
    """apply_stage2f.py as a function: H the history (with results), U the day, up_p the day's stage-1 price"""
    D = dict(H); pdm.install(D); ri = D["race_idx"]; uri = U["race_idx"]; nRu = len(U["race_id"]); hn = len(ri)
    res = np.clip(np.log(np.maximum(D["q"], 1e-4)) - np.log(np.maximum(p_hist, 1e-4)), -3, 3)
    cat = lambda a, bb: np.concatenate([np.asarray(a).astype(str), np.asarray(bb).astype(str)])
    rd = cat(D["date"][ri], U["date"][uri]); riall = np.concatenate([ri, uri + D["n_races"]]); pall = np.concatenate([p_hist, up_p])
    resall = np.concatenate([res, np.full(len(uri), np.nan)])
    jc = D["colidx"]["jockeyForm_lastTwelveMonthWinPercentage"]
    jw = np.concatenate([np.nan_to_num(D["X"][:, jc].astype(float), nan=0), np.nan_to_num(U["X"][:, jc].astype(float), nan=0)])
    pj = np.vstack([D["past_jockeys"].astype(str), U["past_jockeys"].astype(str)]); lastj = np.array([next((x for x in row if x), "") for row in pj])
    H_ = cat(D["horse_id"], U["horse_id"]); T_ = cat(D["trainer"], U["trainer"]); J_ = cat(D["jockey"], U["jockey"])
    E = stage2.encodings(rd, H_, T_, J_, cat(D["sire"], U["sire"]), cat(D["track"][ri], U["track"][uri]), resall)[hn:]
    A, Bk, C = stage2.extras(rd, riall, H_, T_, J_, lastj, pall, jw, resall)
    X, L = stage2.design(E, up_p, uri, nRu); SEC = stage2.sections(U["S"], U["sec_fields"], U["P"], U["past_fields"], uri, nRu)
    TV = stage2.travel(U["training_location"], U["track"][uri], uri, nRu); lid, lf = stage2.last_start(U["P"], U["past_fields"], U["past_race_ids"])
    CO = stage2.collateral(D["race_id"][ri], D["date"][ri], D["horse_id"], D["finish"], D["q"], lid, U["date"][uri], U["horse_id"], lf, uri, nRu)
    X = np.column_stack([X, A[hn:], Bk[hn:], C[hn:], SEC, stage2.trials(U["P"], U["past_fields"], uri), TV, CO])
    return smx(np.mean([m.predict(X) for m in S2], 0) + L, uri, nRu)


CUT = "2026-10-14"; days = sorted(set(rdate[rdate > CUT])); ARMS = ("stale", "fresh")
OUT = {a: np.full((nrun, 4), np.nan) for a in ARMS}
for d in days:
    t0 = time.time(); Um, uidx = subset(rdate == d); Ub = blank(Um)
    for arm, hm in (("stale", rdate <= CUT), ("fresh", rdate < d)):
        Hd, hidx = subset(hm); pt, pc, p1 = stage1(Hd, Ub); p2 = stage2f(Hd, POOF[hidx], Ub, p1)
        OUT[arm][uidx] = np.column_stack([pt, pc, p1, p2])
    print(f"{d} {len(Um['race_id'])} races {time.time()-t0:.0f}s", flush=True)
np.savez("replay_stale.npz", stale=OUT["stale"], fresh=OUT["fresh"])
