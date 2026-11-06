"""Round 22: five seeds, and the metro tracks (6 Nov 2026; the founder's horse brief: "gradient-boosted trees (LightGBM, 5
seeds averaged)" and "Metro fix ... the model overrates its metro picks").

    python research/greyhound/topaz_round22.py DIR LABEL    (BETFAIR_DIR, RACES_DIR; WALK_GRV_RATING / WALK_RELIABLE /
                                                             WALK_LEAD / WALK_DRIFT as the weekly train sets them)

The production inputs, the standard split, scored on the last quarter, both halves:
  1. one seed against the average of five (each early-stopped on the early-stopping months; their raw scores averaged
     before the race softmax): log loss and gap to BSP
  2. the 1.3x rule at GRV's SP track by track (Test 34 found the horse order sheet's bets at Sandown and The Meadows
     winning far less than elsewhere): bets, A/E, flat and Kelly ROI, both halves, metro (SAN, MEA) against the rest
  3. the metro lean: at the metro tracks, our chance leans further to GRV's price before the rule (the blend refitted
     on the early-stopping months' metro races only), and the metro tracks left out altogether
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round2 as R2         # noqa: E402
import topaz_round9 as R9         # noqa: E402
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402

METRO = ("SAN", "SAP", "MEA", "MEP")    # Sandown and The Meadows, each under two codes (run 42189617014)
SEEDS = (1, 2, 3, 4, 5)


def fit_seed(Xtr, ytr, rtr, Xes, wes, res, weight, seed, rounds=6000):
    """topaz_round3.fit_weighted with the seed set (bagging and feature sampling follow it)."""
    import lightgbm as lgb
    groups = rtr.groupby(rtr.values, sort=False).size().values
    starts = np.r_[0, np.cumsum(groups)[:-1]]
    w = np.asarray(weight, dtype=float)

    def obj(preds, data):
        y = data.get_label()
        e = np.exp(preds - np.repeat(np.maximum.reduceat(preds, starts), groups))
        p = e / np.repeat(np.add.reduceat(e, starts), groups)
        return w * (p - y), w * np.maximum(p * (1 - p), 1e-6)
    params = dict(R2.SMALL, objective=obj, metric="None", verbose=-1, seed=seed)
    score = R2.fast_race_ll(res)
    won = np.asarray(wes)
    dtr = lgb.Dataset(Xtr, ytr, categorical_feature=V1.CAT, free_raw_data=False)
    des = lgb.Dataset(Xes, won.astype(float), reference=dtr, categorical_feature=V1.CAT, free_raw_data=False)
    bst = lgb.train(params, dtr, num_boost_round=rounds, valid_sets=[des],
                    feval=lambda pr, data: ("race_ll", score(pr, won), False),
                    callbacks=[lgb.early_stopping(300, verbose=False)])
    return bst, bst.best_iteration


def rule_table(name, t2, pb, h2, sel=None):
    """The 1.3x rule at GRV's SP on blended chances pb, both halves and all."""
    price = t2.start_price.astype(float).values
    m, o, u = R9.horse_bets(t2, pb, t2.p_sp.values, price, 0.0, 1.3, (2, 15))
    if sel is not None:
        m = m & sel
    out = []
    for hn, hm in (("1st", h2), ("2nd", ~h2), ("all", np.ones(len(t2), bool))):
        r = R9.summary(t2, m & hm, o, u, price)
        if r["n"]:
            out.append(f"| {name} | {hn} | {r['n']:,} | {r['w']:,} | {r['ae']:.3f} | {r['flat']:+.1%} | {r['staked']:,.0f} | "
                       f"{r['kroi']:+.1%} | {r['kunits']:+,.0f} |")
        else:
            out.append(f"| {name} | {hn} | 0 | | | | | | |")
    return out


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    df, num, rel, note = W.build_full(d)
    print(f"# {label}: round 22, five seeds and the metro tracks\n\n{note}\n")
    q75 = df.date.quantile(0.75)
    es_start = q75 - min(pd.Timedelta(days=183), (q75 - df.date.min()) / 4)
    pre, te = df[df.date < q75], df[df.date >= q75].copy()
    fp, es = pre[pre.date < es_start].copy(), pre[pre.date >= es_start].copy()
    recency = 0.5 ** (((es_start - fp.date).dt.days / 365.25).values / 3.0)
    Xf, Xe, Xt = T.features(fp, num, rel), T.features(es, num, rel), T.features(te, num, rel)
    se, st, its = [], [], []
    for s in SEEDS:
        bst, k = fit_seed(Xf, fp.p_mkt.values.astype(float), fp.race_id, Xe, es.won.values, es.race_id.values,
                          recency, s)
        se.append(bst.predict(Xe, num_iteration=k, raw_score=True))
        st.append(bst.predict(Xt, num_iteration=k, raw_score=True))
        its.append(k)
    es["p_1"], te["p_1"] = V1.race_softmax(se[0], es.race_id.values), V1.race_softmax(st[0], te.race_id.values)
    es["p_5"] = V1.race_softmax(np.mean(se, axis=0), es.race_id.values)
    te["p_5"] = V1.race_softmax(np.mean(st, axis=0), te.race_id.values)

    w = te.won.values
    hb = te.p_bsp.notna().values
    h = (te.date < te.date.quantile(0.5)).values
    b_all, b1, b2 = (V1.ll(te.p_bsp.values[m], w[m]) for m in (hb, hb & h, hb & ~h))
    print(f"## 1. Five seeds ({', '.join(str(i) for i in its)} rounds; {te[hb].race_id.nunique():,} scored races with BSP, "
          f"BSP {b_all:.4f})\n")
    print("| model | log loss | gap to BSP | 1st half | 2nd half |\n|---|---|---|---|---|")
    for i, s in enumerate(SEEDS):
        p = V1.race_softmax(st[i], te.race_id.values)
        print(f"| seed {s} alone | {V1.ll(p[hb], w[hb]):.4f} | {V1.ll(p[hb], w[hb]) - b_all:+.4f} | "
              f"{V1.ll(p[hb & h], w[hb & h]) - b1:+.4f} | {V1.ll(p[hb & ~h], w[hb & ~h]) - b2:+.4f} |")
    p = te.p_5.values
    print(f"| **the five averaged** | {V1.ll(p[hb], w[hb]):.4f} | {V1.ll(p[hb], w[hb]) - b_all:+.4f} | "
          f"{V1.ll(p[hb & h], w[hb & h]) - b1:+.4f} | {V1.ll(p[hb & ~h], w[hb & ~h]) - b2:+.4f} |")

    # 2. and 3. the 1.3x rule by track, on the five-seed model
    e_ok, t_ok = es.p_sp.notna().values, te.p_sp.notna().values
    e2, t2 = es[e_ok], te[t_ok].copy()
    h2 = (t2.date < t2.date.quantile(0.5)).values
    metro_t = t2.track.astype(str).isin(METRO).values
    metro_e = e2.track.astype(str).isin(METRO).values
    print("\n## 2. The 1.3x rule at GRV's SP, track by track (our price $2-$15, Kelly x75 cap 4)\n")
    print("| rule | half | bets | winners | A/E | flat ROI | units staked | Kelly ROI | units won |\n"
          "|---|---|---|---|---|---|---|---|---|")
    for col in ("p_1", "p_5"):
        wts, _ = V1.blend([col, "p_sp"], e2)
        pb = V1.blend([col, "p_sp"], t2, wts)[1]
        tag = "one seed" if col == "p_1" else "five seeds"
        for line in rule_table(f"{tag}, every track ({wts[0]:.2f} / {wts[1]:.2f})", t2, pb, h2):
            print(line)
        if col == "p_5":
            t2["p_blend5"] = pb
            for line in rule_table(f"{tag}, Sandown and The Meadows", t2, pb, h2, metro_t):
                print(line)
            for line in rule_table(f"{tag}, every other track", t2, pb, h2, ~metro_t):
                print(line)
    print("\n| track | bets | winners | A/E | flat ROI | Kelly ROI | units won |\n|---|---|---|---|---|---|---|")
    price = t2.start_price.astype(float).values
    m, o, u = R9.horse_bets(t2, t2.p_blend5.values, t2.p_sp.values, price, 0.0, 1.3, (2, 15))
    for trk in sorted(t2.track.astype(str).unique()):
        r = R9.summary(t2, m & (t2.track.astype(str) == trk).values, o, u, price)
        if r["n"] >= 20:
            print(f"| {trk} | {r['n']:,} | {r['w']:,} | {r['ae']:.3f} | {r['flat']:+.1%} | {r['kroi']:+.1%} | {r['kunits']:+,.0f} |")

    print("\n## 3. The metro lean (five seeds)\n")
    print("| rule | half | bets | winners | A/E | flat ROI | units staked | Kelly ROI | units won |\n"
          "|---|---|---|---|---|---|---|---|---|")
    if metro_e.sum() > 2000:
        wm, _ = V1.blend(["p_5", "p_sp"], e2[metro_e])
        pm = V1.blend(["p_5", "p_sp"], t2, wm)[1]
        lean = np.where(metro_t, pm, t2.p_blend5.values)
        for line in rule_table(f"the metro blend refitted on metro races ({wm[0]:.2f} / {wm[1]:.2f})", t2, lean, h2):
            print(line)
    for line in rule_table("the metro tracks left out", t2, t2.p_blend5.values, h2, ~metro_t):
        print(line)
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 22")
