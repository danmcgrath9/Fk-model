"""Round 23: can we beat BSP? (6 Nov 2026, founder: "It would be nice to beat BSP, do we have any edges with that?")

    python research/greyhound/topaz_round23.py DIR LABEL    (BETFAIR_DIR, RACES_DIR, ISOLYNX_DIR; WALK_GRV_RATING /
                                                             WALK_RELIABLE / WALK_LEAD as the weekly train sets them)

Every Benter blend of our price with BSP so far has given ours about nothing (walk-forward: -0.09 to +0.07 on ours,
0.94 to 1.07 on BSP), so once BSP is known the model adds nothing. Isolynx and the checks (Test 35) are the first
inputs BSP may not hold in full. Standard split, scored on the last quarter's races with BSP, both halves:
  1. P, the production model, and I, P + Isolynx + the checks: each blended with BSP (fitted on the early-stopping
     months). Does the blend beat BSP alone? Weight on ours, log loss of BSP alone and of each blend
  2. the rule at BSP (8% commission on winnings): back when BSP >= r x the blended price, our price $2-$15, Kelly x75
     on halfway between the blend and BSP, cap 4; r = 1.1, 1.2, 1.3
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round3 as R3         # noqa: E402
import topaz_round9 as R9         # noqa: E402
import topaz_round18 as R18       # noqa: E402
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402

COMM = 0.08


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    df, num, rel, note = W.build_full(d)
    print(f"# {label}: round 23, can we beat BSP?\n\n{note}\n")
    df, chk, _ = R18.check_features(df, os.environ.get("ISOLYNX_DIR", ""))
    (num0, rel0), (num1, rel1), iso = R18.split_inputs(num, rel)
    rows = [("P the production model", num0, rel0)]
    if iso:
        rows.append(("I + Isolynx and the checks", num1 + chk, rel1))
    else:
        print("No Isolynx inputs: only P is scored\n")
    q75 = df.date.quantile(0.75)
    es_start = q75 - min(pd.Timedelta(days=183), (q75 - df.date.min()) / 4)
    pre, te = df[df.date < q75], df[df.date >= q75].copy()
    fp, es = pre[pre.date < es_start].copy(), pre[pre.date >= es_start].copy()
    recency = 0.5 ** (((es_start - fp.date).dt.days / 365.25).values / 3.0)
    e_ok = es.p_bsp.notna().groupby(es.race_id).transform("all").values
    t_ok = te.p_bsp.notna().groupby(te.race_id).transform("all").values & (te.bsp > 1).groupby(te.race_id).transform("all").values
    e2 = es[e_ok].copy()
    t2 = te[t_ok].copy()
    h = (t2.date < t2.date.quantile(0.5)).values
    w = t2.won.values
    b, b1, b2 = (V1.ll(t2.p_bsp.values[m], w[m]) for m in (np.ones(len(t2), bool), h, ~h))
    print(f"Scored: {t2.race_id.nunique():,} races with BSP on every runner; BSP alone {b:.4f} (1st half {b1:.4f}, 2nd {b2:.4f})\n")
    print("| model | rounds | weights (ours / BSP) | ours alone | blend with BSP | blend less BSP | 1st half | 2nd half |\n"
          "|---|---|---|---|---|---|---|---|")
    preds = {}
    for name, cols, rels in rows:
        Xf, Xe, Xt = T.features(fp, cols, rels), T.features(e2, cols, rels), T.features(t2, cols, rels)
        bst, k, _ = R3.fit_weighted(Xf, fp.p_mkt.values.astype(float), fp.race_id, T.features(es, cols, rels),
                                    es.won.values, es.race_id.values, recency, rounds=6000)
        e2["p_x"] = V1.race_softmax(bst.predict(Xe, num_iteration=k, raw_score=True), e2.race_id.values)
        t2["p_x"] = V1.race_softmax(bst.predict(Xt, num_iteration=k, raw_score=True), t2.race_id.values)
        wts, _ = V1.blend(["p_x", "p_bsp"], e2)
        pb = V1.blend(["p_x", "p_bsp"], t2, wts)[1]
        preds[name] = pb
        l, l1, l2 = V1.ll(pb, w), V1.ll(pb[h], w[h]), V1.ll(pb[~h], w[~h])
        print(f"| {name} | {k} | {wts[0]:.3f} / {wts[1]:.3f} | {V1.ll(t2.p_x.values, w):.4f} | {l:.4f} | {l - b:+.4f} | "
              f"{l1 - b1:+.4f} | {l2 - b2:+.4f} |")

    price = t2.bsp.astype(float).values
    print("\n## The rule at BSP (8% commission; our price $2-$15; Kelly x75 cap 4)\n")
    print("| model | ratio | half | bets | winners | A/E | flat ROI | units staked | Kelly ROI | units won |\n"
          "|---|---|---|---|---|---|---|---|---|---|")
    for name, pb in preds.items():
        for ratio in (1.1, 1.2, 1.3):
            m, o, u = R9.horse_bets(t2, pb, t2.p_bsp.values, price, COMM, ratio, (2, 15))
            for hn, hm in (("1st", h), ("2nd", ~h), ("all", np.ones(len(t2), bool))):
                r = R9.summary(t2, m & hm, o, u, price)
                if r["n"]:
                    print(f"| {name[:1]} | {ratio:g}x | {hn} | {r['n']:,} | {r['w']:,} | {r['ae']:.3f} | {r['flat']:+.1%} | "
                          f"{r['staked']:,.0f} | {r['kroi']:+.1%} | {r['kunits']:+,.0f} |")
                else:
                    print(f"| {name[:1]} | {ratio:g}x | {hn} | 0 | | | | | | |")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 23")
