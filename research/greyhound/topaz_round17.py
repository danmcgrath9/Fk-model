"""Round 17: the winners twin (6 Nov 2026, founder: "Keep testing").

    python research/greyhound/topaz_round17.py DIR LABEL    (BETFAIR_DIR, RACES_DIR; WALK_GRV_RATING / WALK_RELIABLE /
                                                             WALK_LEAD / WALK_DRIFT as the weekly train sets them)

Every walk-forward since Test 14 has scored two models: A, fitted on the BSP's chances (what the card prices with), and
an "ensemble" of A with B, a twin fitted on the winners. The ensemble has beaten A by 0.010 to 0.013 of log loss every
time (Test 28: 1.6056 against 1.5924, ahead of GRV's SP at 1.5952), yet the gap to BSP and the card both use A alone.

The production inputs, the standard split. A as in round 15 (early stopping, cap 6,000 rounds). B on the winners, the
same inputs and recency weights, early stopping, cap 3,000. The ensemble's weights fitted on the early-stopping months
(V1.blend, a power on each model's chances). Scored on the last quarter, both halves:
  1. log loss and gap to BSP for A, B and the ensemble; log loss against GRV's SP on all races
  2. A/E for the SP favourite and by our price, A against the ensemble (does B fix what A misses?)
  3. the 1.3x rule at GRV's SP (Benter blend of ours with the SP fitted on the early-stopping months; our price $2-$15,
     Kelly x75 cap 4), ours = A against ours = the ensemble, with the drift guard beside it when WALK_DRIFT=yes
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round3 as R3         # noqa: E402
import topaz_round9 as R9         # noqa: E402
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402

DRIFT_CAP = 1.3
BANDS = [(1, 2), (2, 3), (3, 5), (5, 10), (10, 20), (20, 1000)]


def fit_pair(fp, es, X_fp, X_es, recency, rounds_a=6000, rounds_b=3000):
    """A on the BSP's chances and B on the winners, both early-stopped on the early-stopping months."""
    a, ka, _ = R3.fit_weighted(X_fp, fp.p_mkt.values.astype(float), fp.race_id, X_es, es.won.values, es.race_id.values,
                               recency, rounds=rounds_a)
    b, kb, _ = R3.fit_weighted(X_fp, fp.won.values.astype(float), fp.race_id, X_es, es.won.values, es.race_id.values,
                               recency, rounds=rounds_b)
    return (a, ka), (b, kb)


def price_with(models, X, race):
    (a, ka), (b, kb) = models
    return (V1.race_softmax(a.predict(X, num_iteration=ka, raw_score=True), race),
            V1.race_softmax(b.predict(X, num_iteration=kb, raw_score=True), race))


def ae_rows(t: pd.DataFrame, cols):
    """A/E (wins over the summed chance) for the SP favourite and by our price (from A), for each column."""
    sp = t.start_price.where(t.start_price > 1)
    fav = (sp.groupby(t.race_id).rank(method="min") == 1).values
    rows = [("SP favourite", fav)]
    price = 1 / t.p_a.values
    for lo, hi in BANDS:
        rows.append((f"A's price ${lo}-${hi}", (price >= lo) & (price < hi)))
    out = []
    for name, m in rows:
        if m.sum() < 300:
            continue
        w = t.won.values[m].sum()
        out.append((name, int(m.sum()), int(w), [w / t[c].values[m].sum() for c in cols]))
    return out


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    df, num, rel, note = W.build_full(d)
    print(f"# {label}: round 17, the winners twin\n\n{note}\n")
    q75 = df.date.quantile(0.75)
    es_start = q75 - min(pd.Timedelta(days=183), (q75 - df.date.min()) / 4)
    pre, te = df[df.date < q75], df[df.date >= q75].copy()
    fp, es = pre[pre.date < es_start], pre[pre.date >= es_start].copy()
    recency = 0.5 ** (((es_start - fp.date).dt.days / 365.25).values / 3.0)
    Xf, Xe, Xt = T.features(fp, num, rel), T.features(es, num, rel), T.features(te, num, rel)
    models = fit_pair(fp, es, Xf, Xe, recency)
    es["p_a"], es["p_b"] = price_with(models, Xe, es.race_id.values)
    te["p_a"], te["p_b"] = price_with(models, Xt, te.race_id.values)
    wts, _ = V1.blend(["p_a", "p_b"], es)
    te["p_ens"] = V1.blend(["p_a", "p_b"], te, wts)[1]
    es["p_ens"] = V1.blend(["p_a", "p_b"], es, wts)[1]

    w = te.won.values
    hb = te.p_bsp.notna().values
    h = (te.date < te.date.quantile(0.5)).values
    b_all, b1, b2 = (V1.ll(te.p_bsp.values[m], w[m]) for m in (hb, hb & h, hb & ~h))
    hs = te.p_sp.notna().values
    print(f"## Log loss ({models[0][1]} rounds for A, {models[1][1]} for B, {len(num)} inputs; ensemble weights "
          f"{wts[0]:.2f} x A, {wts[1]:.2f} x B, fitted on the early-stopping months)\n")
    print(f"{te[hb].race_id.nunique():,} scored races with BSP (BSP {b_all:.4f}; 1st half {b1:.4f}, 2nd {b2:.4f}); "
          f"{te[hs].race_id.nunique():,} with GRV's SP (SP {V1.ll(te.p_sp.values[hs], w[hs]):.4f})\n")
    print("| price | log loss, BSP races | gap to BSP | 1st half | 2nd half | log loss, SP races | gap to GRV's SP |\n"
          "|---|---|---|---|---|---|---|")
    sp_ll = V1.ll(te.p_sp.values[hs], w[hs])
    for name, col in (("A, the BSP-chance model (the card)", "p_a"), ("B, the winners twin", "p_b"),
                      ("the ensemble of A and B", "p_ens")):
        p = te[col].values
        l, l1, l2 = V1.ll(p[hb], w[hb]), V1.ll(p[hb & h], w[hb & h]), V1.ll(p[hb & ~h], w[hb & ~h])
        ls = V1.ll(p[hs], w[hs])
        print(f"| {name} | {l:.4f} | {l - b_all:+.4f} | {l1 - b1:+.4f} | {l2 - b2:+.4f} | {ls:.4f} | {ls - sp_ll:+.4f} |")

    t = te[hb].copy()
    print("\n| runners (scored races with BSP) | runners | wins | A/E vs A | A/E vs B | A/E vs the ensemble | A/E vs BSP |\n"
          "|---|---|---|---|---|---|---|")
    for name, n, wins, ae in ae_rows(t, ["p_a", "p_b", "p_ens", "p_bsp"]):
        print(f"| {name} | {n:,} | {wins:,} | {ae[0]:.3f} | {ae[1]:.3f} | {ae[2]:.3f} | {ae[3]:.3f} |")

    # the 1.3x rule at GRV's SP, ours = A or the ensemble
    e_ok, t_ok = es.p_sp.notna().values, te.p_sp.notna().values
    t2 = te[t_ok].copy()
    h2 = (t2.date < t2.date.quantile(0.5)).values
    price = t2.start_price.astype(float).values
    has_drift = "drift" in t2
    print("\n## The 1.3x rule at GRV's SP (our price $2-$15, Kelly x75 cap 4, no commission)\n")
    print("| ours | blend weights (ours / SP) | guard | half | bets | winners | A/E | flat ROI | units staked | Kelly ROI | "
          "units won |\n|---|---|---|---|---|---|---|---|---|---|---|")
    for name, col in (("A", "p_a"), ("the ensemble", "p_ens")):
        bw, _ = V1.blend([col, "p_sp"], es[e_ok])
        pb = V1.blend([col, "p_sp"], t2, bw)[1]
        m, o, u = R9.horse_bets(t2, pb, t2.p_sp.values, price, 0.0, 1.3, (2, 15))
        guards = [("none", np.ones(len(t2), bool))]
        if has_drift:
            guards.append((f"drift under {DRIFT_CAP:g}x", ~(t2.drift >= DRIFT_CAP).values))
        for gname, keep in guards:
            for hn, hm in (("1st", h2), ("2nd", ~h2), ("all", np.ones(len(t2), bool))):
                r = R9.summary(t2, m & keep & hm, o, u, price)
                if r["n"]:
                    print(f"| {name} | {bw[0]:.2f} / {bw[1]:.2f} | {gname} | {hn} | {r['n']:,} | {r['w']:,} | "
                          f"{r['ae']:.3f} | {r['flat']:+.1%} | {r['staked']:,.0f} | {r['kroi']:+.1%} | {r['kunits']:+,.0f} |")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 17")
