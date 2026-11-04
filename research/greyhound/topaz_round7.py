"""Round 7: the finishing order as the label (Plackett-Luce, truncated), against BSP (4 Nov 2026, founder: "BUILD THE
BEST MODEL IN THE WORLD"; MODELS_RESEARCH.md row C: use the whole finishing order, not only the winner).

    python research/greyhound/topaz_round7.py DIR LABEL      (BETFAIR_DIR as before; results only)

The model so far learns from one dog a race: the winner, or the market's chance of each dog winning. A race's
finishing order carries more: second beat the six behind it, third beat five. The exploded-logit (Plackett-Luce)
likelihood reads an n-dog race as successive choices, the winner from the field, second from the rest, and so on,
each a softmax over the dogs still standing. Truncating at K stages keeps the top of the order, where the labels are
cleanest (a dog never in it is not racing the one beside it for seventh), and stage weights let the later choices
count for less. A dog with no finish (fell, failed to finish) stands in every denominator and is never chosen, which
is what being beaten by the field means.

Rows, each early stopped on the six months before the scored quarter and scored on the same 22,841 races:
  E0  round 6's D1 (B2 + preview + ratings upgrades), trained on BSP chances          (Test 16: +0.1085)
  E1  the same inputs, Plackett-Luce depth 1: the winner only (a winners model, the ensemble's twin)
  E2  depth 3, equal stage weights
  E3  depth 3, stage weights 1, 0.5, 0.25
  E4  the whole order, equal weights
then each finishing-order row blended with E0 (weights fitted on the early-stopping months). The best single row
and the best blend are chosen on the early-stopping months and the better of the two is staked as Test 12.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import topaz_preview_test as PT   # noqa: E402
import topaz_round2 as R2         # noqa: E402
import topaz_round3 as R3         # noqa: E402
import topaz_round4 as R4         # noqa: E402
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402

FULL = 12      # more stages than any field has: the whole order


def race_order(df):
    """The frame sorted for the objective: by race, finishers first in finishing order, then the rest. Returns the
    sorted frame, each row's 1-based position in its race, and whether it finished."""
    d = df.assign(_fin=df.finish.notna(), _ord=df.finish.fillna(1e9)).sort_values(["date", "race_id", "_ord", "box"])
    pos = d.groupby("race_id", sort=False).cumcount().values + 1
    return d.drop(columns=["_fin", "_ord"]), pos, d._fin.values


def within_race_cumsum(x, starts, groups):
    cs = np.cumsum(x)
    return cs - np.repeat(cs[starts] - x[starts], groups)


def pl_objective(pos, fin, groups, weight, depth, decay):
    """LightGBM objective for the truncated Plackett-Luce likelihood over rows ordered by race_order().

    For a race sorted by finishing position with scores s, stage k chooses the k-th finisher from the dogs at
    positions k..n, so its term is s_k - log(sum_{j>=k} exp s_j). Stage k carries weight decay**(k-1) while k <= depth
    and the k-th row finished; a non-finisher's own stage carries none. For the row at position p:
        grad = e_p * sum_{k<=p} w_k / D_k  -  w_p
        hess = e_p * sum_{k<=p} w_k / D_k  -  e_p^2 * sum_{k<=p} w_k / D_k^2
    with e the exponentials (race max subtracted) and D_k the sum of e from position k to the end of the race. Both
    sums are cumulative within the race, so the whole thing is three cumsums. `weight` multiplies rows (recency)."""
    starts = np.r_[0, np.cumsum(groups)[:-1]]
    own = np.where((pos <= depth) & fin, decay ** (pos - 1), 0.0)
    w = np.asarray(weight, dtype=float)

    def obj(preds, data):
        e = np.exp(preds - np.repeat(np.maximum.reduceat(preds, starts), groups))
        total = np.repeat(np.add.reduceat(e, starts), groups)
        D = total - (within_race_cumsum(e, starts, groups) - e)          # e summed from this position to the end
        A = within_race_cumsum(own / D, starts, groups)
        B = within_race_cumsum(own / D ** 2, starts, groups)
        grad = e * A - own
        hess = e * A - e * e * B
        return w * grad, w * np.maximum(hess, 1e-6)
    return obj


def pl_loss(scores, pos, fin, groups, depth, decay):
    """The truncated Plackett-Luce negative log likelihood the objective descends (for the test, and the record)."""
    starts = np.r_[0, np.cumsum(groups)[:-1]]
    e = np.exp(scores - np.repeat(np.maximum.reduceat(scores, starts), groups))
    total = np.repeat(np.add.reduceat(e, starts), groups)
    D = total - (within_race_cumsum(e, starts, groups) - e)
    own = np.where((pos <= depth) & fin, decay ** (pos - 1), 0.0)
    return -(own * (np.log(e) - np.log(D))).sum()


def fit_pl(Xtr, pos, fin, rtr, Xes, wes, res, weight, depth, decay):
    """R3.fit_weighted's shape with the finishing-order objective; early stopping on the win log loss of `res`."""
    import lightgbm as lgb
    groups = rtr.groupby(rtr.values, sort=False).size().values
    params = dict(R2.SMALL, objective=pl_objective(pos, fin, groups, weight, depth, decay), metric="None", verbose=-1,
                  seed=1)
    score = R2.fast_race_ll(res)
    won = np.asarray(wes)
    dtr = lgb.Dataset(Xtr, np.zeros(len(Xtr)), categorical_feature=V1.CAT, free_raw_data=False)
    des = lgb.Dataset(Xes, won.astype(float), reference=dtr, categorical_feature=V1.CAT, free_raw_data=False)
    bst = lgb.train(params, dtr, num_boost_round=3000, valid_sets=[des],
                    feval=lambda pr, data: ("race_ll", score(pr, won), False),
                    callbacks=[lgb.early_stopping(300, verbose=False)])
    return bst, bst.best_iteration, bst.best_score["valid_0"]["race_ll"]


def main(d, label):
    df, num, rel, bsp_note = W.build(d)
    if "is_best_bet" not in df and "isBestBet" in df:
        df["is_best_bet"] = df.isBestBet
    df, fpv, _ = PT.preview_features(df)
    df = df.copy()
    cols, rl = num + fpv, rel
    q75 = df.date.quantile(0.75)
    es_start = q75 - min(pd.Timedelta(days=183), (q75 - df.date.min()) / 4)
    pre, te = df[df.date < q75], df[df.date >= q75].copy()
    fp, es = pre[pre.date < es_start], pre[pre.date >= es_start].copy()
    hb, hb_es = te.p_bsp.notna().values, es.p_bsp.notna().values
    h = (te.date < te.date.quantile(0.5)).values
    w_te = te.won.values
    bsp_all = V1.ll(te.p_bsp.values[hb], w_te[hb])
    b1, b2 = V1.ll(te.p_bsp.values[hb & h], w_te[hb & h]), V1.ll(te.p_bsp.values[hb & ~h], w_te[hb & ~h])
    fps, pos, fin = race_order(fp)
    recency = 0.5 ** (((es_start - fps.date).dt.days / 365.25).values / 3.0)
    Xf, Xe, Xt = T.features(fps, cols, rl), T.features(es, cols, rl), T.features(te, cols, rl)
    fields = fps.groupby("race_id").size()
    print(f"# {label}: round 7, the finishing order as the label\n\n{bsp_note}\nfit on {fps.race_id.nunique():,} races "
          f"(fields {fields.min()}-{fields.max()}, mean {fields.mean():.1f}); finish recorded on {fin.mean():.1%} of runners; "
          f"scored: {te[hb].race_id.nunique():,} races, BSP {bsp_all:.4f}\n")
    print("| row | rounds | early-stopping log loss | scored log loss | gap to BSP | 1st half | 2nd half |")
    print("|---|---|---|---|---|---|---|")
    rows = [("E0 D1 on BSP chances", None), ("E1 Plackett-Luce depth 1 (the winner)", (1, 1.0)),
            ("E2 depth 3, equal weights", (3, 1.0)), ("E3 depth 3, weights 1, 0.5, 0.25", (3, 0.5)),
            ("E4 the whole order", (FULL, 1.0))]
    preds = {}
    for name, spec in rows:
        if spec is None:
            bst, k, _ = R3.fit_weighted(Xf, fps.p_mkt.values.astype(float), fps.race_id, Xe, es.won.values,
                                        es.race_id.values, recency)
        else:
            bst, k, _ = fit_pl(Xf, pos, fin, fps.race_id, Xe, es.won.values, es.race_id.values, recency, *spec)
        pe = V1.race_softmax(bst.predict(Xe, num_iteration=k, raw_score=True), es.race_id.values)
        pt = V1.race_softmax(bst.predict(Xt, num_iteration=k, raw_score=True), te.race_id.values)
        preds[name] = (pe, pt)
        le = V1.ll(pe[hb_es], es.won.values[hb_es])
        l, l1, l2 = V1.ll(pt[hb], w_te[hb]), V1.ll(pt[hb & h], w_te[hb & h]), V1.ll(pt[hb & ~h], w_te[hb & ~h])
        print(f"| {name} | {k} | {le:.4f} | {l:.4f} | {l - bsp_all:+.4f} | {l1 - b1:+.4f} | {l2 - b2:+.4f} |")
    e0 = rows[0][0]
    print("\n| blend with E0 (weights on the early-stopping months) | weights | early-stopping log loss | scored log loss | gap to BSP | 1st half | 2nd half |")
    print("|---|---|---|---|---|---|---|")
    for name, _ in rows[1:]:
        es2 = es.assign(p0=preds[e0][0], p1=preds[name][0])
        wts, pe = V1.blend(["p0", "p1"], es2)
        pt = V1.blend(["p0", "p1"], te.assign(p0=preds[e0][1], p1=preds[name][1]), wts)[1]
        preds[f"E0 + {name}"] = (pe, pt)
        le = V1.ll(pe[hb_es], es.won.values[hb_es])
        l, l1, l2 = V1.ll(pt[hb], w_te[hb]), V1.ll(pt[hb & h], w_te[hb & h]), V1.ll(pt[hb & ~h], w_te[hb & ~h])
        print(f"| E0 + {name} | {wts[0]:.2f}, {wts[1]:.2f} | {le:.4f} | {l:.4f} | {l - bsp_all:+.4f} | {l1 - b1:+.4f} | {l2 - b2:+.4f} |")
    best = min(preds, key=lambda n: V1.ll(preds[n][0][hb_es], es.won.values[hb_es]))
    pe, pt = preds[best]
    print(f"\nChosen on the early-stopping months: **{best}**")
    for pname, col, comm in (("GRV's SP, no commission", "start_price", 0.0), ("BSP, 8% commission", "bsp", 0.08)):
        if col not in te:
            continue
        cands = []
        for one in (False, True):
            for band in R4.BANDS:
                for e in R4.EDGES:
                    m, o = R4.selections(es, pe, es[col].values, comm, e, band, one)
                    r = R4.result(es, m, o, pe, 0, es[col].values)
                    if r["n"] >= 300:
                        cands.append((r["roi"], one, band, e, r["n"]))
        if not cands:
            continue
        cands.sort(reverse=True)
        roi_es, one, band, e, n_es = cands[0]
        print(f"\n## Staking at {pname}: one a race {'yes' if one else 'no'}, ${band[0]:g}-${band[1]:g}, edge {e:.0%} "
              f"(chosen on the early-stopping months: {n_es:,} bets, {roi_es:+.1%})\n")
        print("| half | bets | winners | A/E | flat ROI | longest losing run |\n|---|---|---|---|---|---|")
        for hn, hm in (("1st", h), ("2nd", ~h)):
            sub = te[hm]
            m, o = R4.selections(sub, pt[hm], sub[col].values, comm, e, band, one)
            r = R4.result(sub, m, o, pt[hm], 0, sub[col].values)
            if r["n"]:
                print(f"| {hn} | {r['n']:,} | {r['w']:,} | {r['ae']:.3f} | {r['roi']:+.1%} | {r['run']} |")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 7")
