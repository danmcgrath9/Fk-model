"""Round 2 against BSP: why is the Topaz model 0.150 behind (Test 9), and how much closer can it get?
(4 Nov 2026, founder: "lets see how close we can get to BSP with all the data tools we have").

    python research/greyhound/topaz_round2.py DIR LABEL     (BETFAIR_DIR as for topaz_theories.py; results only)

Same races, same features as Test 9's T7 (everything through T6, built by topaz_theories), same last quarter scored.
What changes, one row at a time:
  R1  the training window: fit on EVERYTHING before the scored quarter, with the number of rounds chosen by early
      stopping on its last 6 months (Test 9 fitted on 2013-2021 only and spent 2021-2024 choosing rounds)
  R2  + each key rating as a rank and a gap within its own field (who is best in THIS race, not overall)
  R3  + a bigger learner: 255 leaves, 100 rows a leaf, learning rate 0.03, up to 6000 rounds
  R4  the R3 learner on a mixed target: half BSP chance, half the actual winner
Each is scored on the scored quarter's races Betfair fully priced: log loss, and the gap to BSP and to GRV's SP, in
both halves; then Benter's stage 2 blend of the best row with BSP.
"""
import os
import re
import sys

import numpy as np
import pandas as pd
import lightgbm as lgb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import topaz_theories as T   # noqa: E402
import topaz_v1 as V1        # noqa: E402

RANKED = ["elo", "time_rating_mean5", "time_rating_best5", "time_rating_last", "split_rating_mean5",
          "split_rating_best5", "finish_mean5", "trainer_rate", "dog_place_91D", "dog_won_91D", "style_early",
          "style_led_rate", "mkt_lsp_mean5", "box_ratio", "last5_mean"]
SMALL = dict(learning_rate=0.05, num_leaves=63, min_data_in_leaf=300, feature_fraction=0.6, bagging_fraction=0.8,
             bagging_freq=1, lambda_l2=10)
BIG = dict(learning_rate=0.03, num_leaves=255, min_data_in_leaf=100, feature_fraction=0.5, bagging_fraction=0.8,
           bagging_freq=1, lambda_l2=10)


def add_ranks(df, cols):
    out = []
    for c in cols:
        if c not in df:
            continue
        g = df.groupby("race_id")[c]
        asc = c in ("finish_mean5", "mkt_lsp_mean5", "style_early", "last5_mean")      # lower is better
        df[f"{c}_rank"] = g.rank(ascending=asc, method="average") / df.field
        best = g.transform("min" if asc else "max")
        df[f"{c}_gap_best"] = (df[c] - best).abs()
        out += [f"{c}_rank", f"{c}_gap_best"]
    return df, out


def fast_race_ll(race_sorted):
    """Winner log loss of the race softmax for rows grouped contiguously by race (numpy only, for early stopping)."""
    r = np.asarray(race_sorted)
    starts = np.r_[0, np.flatnonzero(r[1:] != r[:-1]) + 1]
    sizes = np.diff(np.r_[starts, len(r)])

    def f(preds, won):
        e = np.exp(preds - np.repeat(np.maximum.reduceat(preds, starts), sizes))
        p = e / np.repeat(np.add.reduceat(e, starts), sizes)
        return -np.log(np.clip(p[won == 1], 1e-12, None)).mean()
    return f


def fit_es(Xtr, ytr, rtr, Xes, wes, res, params, rounds, patience=300):
    """Fit with the race softmax, stopping when the early-stopping set's winner log loss has not improved for
    `patience` rounds; returns the booster, the best round and its loss."""
    groups = rtr.groupby(rtr.values, sort=False).size().values
    p = dict(params, objective=V1.softmax_obj(groups), metric="None", verbose=-1, seed=1)
    score = fast_race_ll(res)
    won = np.asarray(wes)

    def feval(preds, data):
        return "race_ll", score(preds, won), False
    dtr = lgb.Dataset(Xtr, ytr, categorical_feature=V1.CAT, free_raw_data=False)
    des = lgb.Dataset(Xes, won.astype(float), reference=dtr, categorical_feature=V1.CAT, free_raw_data=False)
    bst = lgb.train(p, dtr, num_boost_round=rounds, valid_sets=[des], feval=feval,
                    callbacks=[lgb.early_stopping(patience, verbose=False)])
    return bst, bst.best_iteration, bst.best_score["valid_0"]["race_ll"]


def main(d, label):
    df = V1.build(d)
    for src, dst in (("rating", "topaz_rating"), ("totalFormCount", "total_form"), ("careerPrizeMoney", "career_prize"),
                     ("prizeMoney", "prize"), ("last5", "last5")):
        if dst not in df and src in df:
            df[dst] = df[src]
    df, f2 = T.V2.add_map(df)
    df = df.reset_index(drop=True)
    df, f3 = T.t3(df)
    df, f4 = T.t4(df)
    df, f5, _ = T.t5(df, df.columns)
    df, f6 = T.t6(df)
    df, bsp_note = T.add_bsp(df)
    df = df.sort_values(["date", "race_id", "box"]).reset_index(drop=True)
    df["p_mkt"] = df.p_bsp.fillna(df.p_sp) if "p_bsp" in df else df.p_sp
    df, fr = add_ranks(df, RANKED)
    df = df.copy()                                                   # one block in memory after the many columns

    q75 = df.date.quantile(0.75)
    span = q75 - df.date.min()
    es_start = q75 - min(pd.Timedelta(days=183), span / 4)         # 6 months, or a quarter of a short history
    pre, te = df[df.date < q75], df[df.date >= q75].copy()
    fit_part, es = pre[pre.date < es_start], pre[pre.date >= es_start]
    old_tr = df[df.date < df.date.quantile(0.5)]
    hb = te.p_bsp.notna().values
    mid = te.date.quantile(0.5)
    h = (te.date < mid).values
    b, s = te.p_bsp.values, te.p_sp.values
    bsp_all, bsp_h1, bsp_h2 = V1.ll(b[hb], te.won.values[hb]), V1.ll(b[hb & h], te.won.values[hb & h]), \
        V1.ll(b[hb & ~h], te.won.values[hb & ~h])
    sp_bsp = V1.ll(s[hb], te.won.values[hb])
    print(f"# {label}: round 2 against BSP\n\n{bsp_note}\nscored: {te[hb].race_id.nunique():,} races from "
          f"{q75:%Y-%m-%d} Betfair fully priced (halves split {mid:%Y-%m-%d}): BSP {bsp_all:.4f} (halves "
          f"{bsp_h1:.4f} / {bsp_h2:.4f}), GRV SP {sp_bsp:.4f}\nTest 9 fitted on {old_tr.race_id.nunique():,} races to "
          f"{old_tr.date.max():%Y-%m-%d}; R1 on {fit_part.race_id.nunique():,} to {fit_part.date.max():%Y-%m-%d}, "
          f"early stopping on {es.race_id.nunique():,} to {es.date.max():%Y-%m-%d}\n")
    print("| row | features | learner | target | rounds | log loss | gap to BSP | 1st half | 2nd half | gap to GRV SP |")
    print("|---|---|---|---|---|---|---|---|---|---|")

    base = list(dict.fromkeys(V1.NUM + f2 + f3 + f4 + f5 + f6))
    rel_extra = ["style_early", "style_led_rate", "style_gain", "dog_place_91D", "dog_won_91D", "trainer_id_won_91D",
                 "box_vacancy_ratio", "last5_mean", "mkt_lsp_mean5", "mkt_prev_lsp"]
    rel = V1.REL + [f for f in rel_extra if f in base]
    rows = [("R1 all history before the quarter", base, SMALL, "p_mkt", 3000),
            ("R2 + ranks and gaps in the field", base + fr, SMALL, "p_mkt", 3000),
            ("R3 + a bigger learner", base + fr, BIG, "p_mkt", 6000),
            ("R4 the same, half BSP chance and half winner", base + fr, BIG, "mix", 6000)]
    best = None
    for name, num, params, target, rounds in rows:
        Xf, Xe, Xt = T.features(fit_part, num, rel), T.features(es, num, rel), T.features(te, num, rel)
        y = (0.5 * fit_part.p_mkt + 0.5 * fit_part.won).values if target == "mix" else fit_part[target].values
        bst, k, _ = fit_es(Xf, y.astype(float), fit_part.race_id, Xe, es.won.values, es.race_id.values, params, rounds)
        pt = V1.race_softmax(bst.predict(Xt, num_iteration=k, raw_score=True), te.race_id.values)
        w = te.won.values
        l, l1, l2 = V1.ll(pt[hb], w[hb]), V1.ll(pt[hb & h], w[hb & h]), V1.ll(pt[hb & ~h], w[hb & ~h])
        print(f"| {name} | {Xf.shape[1]} | {'big' if params is BIG else 'small'} | "
              f"{'BSP chances' if target == 'p_mkt' else 'mixed'} | {k} | {l:.4f} | {l - bsp_all:+.4f} | "
              f"{l1 - bsp_h1:+.4f} | {l2 - bsp_h2:+.4f} | {l - sp_bsp:+.4f} |")
        if best is None or l < best[0]:
            pe = V1.race_softmax(bst.predict(Xe, num_iteration=k, raw_score=True), es.race_id.values)
            best = (l, name, pt, pe, bst, Xf.columns)
    te["p_best"] = best[2]
    esb = es.copy()
    esb["p_best"] = best[3]
    esb, teb = esb[esb.p_bsp.notna()], te[te.p_bsp.notna()]
    w_, _ = V1.blend(["p_best", "p_bsp"], esb)
    _, p = V1.blend(["p_best", "p_bsp"], teb, w_)
    print(f"\nBenter stage 2, {best[1]} blended with BSP (weights fitted on the early-stopping months) "
          f"{w_[0]:.3f} / {w_[1]:.3f}: {V1.ll(p, teb.won):.4f}, gap to BSP {V1.ll(p, teb.won) - bsp_all:+.4f}")
    imp = pd.Series(best[4].feature_importance("gain"), index=best[5]).sort_values(ascending=False)
    print("\nBest row's top inputs: " + ", ".join(f"{i} {v / imp.sum():.0%}" for i, v in imp.head(15).items()))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 2")
