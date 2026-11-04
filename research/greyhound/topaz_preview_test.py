"""Does GRV's pre-race preview of THIS race (the per-runner comment and the isBestBet flag) get us closer to BSP,
and does it add anything to BSP itself? (4 Nov 2026, after round 5 found the comment is a form-guide preview.)

    python research/greyhound/topaz_preview_test.py DIR LABEL     (BETFAIR_DIR as before; results only)

Rows, each fitted as round 3's B2 (recent years weighted more, BSP chances, early stopping on the last 6 months before
the scored quarter) and scored on the same 22,841 races:
  P0  round 3's B2
  P1  + this race's preview: the 60 commonest comment words (present or not), the comment's length, and isBestBet
Then the market check, on BSP-matched races only, trained on winners: BSP alone (as a feature) against BSP plus the
preview. If the preview adds to BSP it is either an opinion the market under-uses or a field written after the race;
`greyhound/preview.py` settles which by snapshotting the field before the race and comparing it with the bulk feed
the day after. Until that compare is in, treat any gain here as unproven.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import topaz_round2 as R2    # noqa: E402
import topaz_round3 as R3    # noqa: E402
import topaz_walk as W       # noqa: E402
import topaz_theories as T   # noqa: E402
import topaz_v1 as V1        # noqa: E402


def preview_features(df, n_words=60):
    text = df.get("comment", pd.Series("", index=df.index)).fillna("").astype(str).str.upper()
    words = text.str.findall(r"[A-Z]{3,}")
    counts = pd.Series([w for ws in words for w in set(ws)]).value_counts()
    top = [w for w in counts.index if counts[w] >= 0.003 * len(df)][:n_words]
    sets = words.map(set)
    cols = {f"pv_{w}": sets.map(lambda s, w=w: float(w in s)).values for w in top}
    cols["pv_len"] = text.str.len().values
    cols["pv_bestbet"] = df.get("is_best_bet", pd.Series(np.nan, index=df.index)).astype(float).values
    new = pd.DataFrame(cols, index=df.index)
    return pd.concat([df, new], axis=1), list(cols), top


def main(d, label):
    df, num, rel, bsp_note = W.build(d)
    if "is_best_bet" not in df and "isBestBet" in df:
        df["is_best_bet"] = df.isBestBet
    df, fp_, words = preview_features(df)
    df["lbsp"] = np.log(df.p_bsp)
    q75 = df.date.quantile(0.75)
    es_start = q75 - min(pd.Timedelta(days=183), (q75 - df.date.min()) / 4)
    pre, te = df[df.date < q75], df[df.date >= q75].copy()
    fp, es = pre[pre.date < es_start], pre[pre.date >= es_start].copy()
    hb, hb_es = te.p_bsp.notna().values, es.p_bsp.notna().values
    h = (te.date < te.date.quantile(0.5)).values
    w_te = te.won.values
    bsp_all = V1.ll(te.p_bsp.values[hb], w_te[hb])
    b1, b2 = V1.ll(te.p_bsp.values[hb & h], w_te[hb & h]), V1.ll(te.p_bsp.values[hb & ~h], w_te[hb & ~h])
    recency = 0.5 ** (((es_start - fp.date).dt.days / 365.25).values / 3.0)
    print(f"# {label}: this race's preview\n\n{bsp_note}\ncomment words ({len(words)}): {', '.join(words)}\n"
          f"isBestBet true on {df.pv_bestbet.fillna(0).mean():.1%} of runners; comment filled on "
          f"{(df.pv_len > 0).mean():.0%}\n")
    print(f"scored: {te[hb].race_id.nunique():,} races, BSP {bsp_all:.4f}\n")
    print("| row | features | rounds | early-stopping log loss | scored log loss | gap to BSP | 1st half | 2nd half |")
    print("|---|---|---|---|---|---|---|---|")
    for name, cols in (("P0 round 3's B2", num), ("P1 + this race's preview", num + fp_)):
        Xf, Xe, Xt = T.features(fp, cols, rel), T.features(es, cols, rel), T.features(te, cols, rel)
        bst, k, _ = R3.fit_weighted(Xf, fp.p_mkt.values.astype(float), fp.race_id, Xe, es.won.values,
                                    es.race_id.values, recency)
        pe = V1.race_softmax(bst.predict(Xe, num_iteration=k, raw_score=True), es.race_id.values)
        pt = V1.race_softmax(bst.predict(Xt, num_iteration=k, raw_score=True), te.race_id.values)
        l, l1, l2 = V1.ll(pt[hb], w_te[hb]), V1.ll(pt[hb & h], w_te[hb & h]), V1.ll(pt[hb & ~h], w_te[hb & ~h])
        print(f"| {name} | {Xf.shape[1]} | {k} | {V1.ll(pe[hb_es], es.won.values[hb_es]):.4f} | {l:.4f} | "
              f"{l - bsp_all:+.4f} | {l1 - b1:+.4f} | {l2 - b2:+.4f} |")
        if name.startswith("P1"):
            imp = pd.Series(bst.feature_importance("gain"), index=Xf.columns).sort_values(ascending=False)
            pv = imp[[c for c in imp.index if c.startswith("pv_")]]
            print(f"\npreview inputs' share of the model: {pv.sum() / imp.sum():.1%}; top: " +
                  ", ".join(f"{i} {v / imp.sum():.1%}" for i, v in pv.head(10).items()))

    print("\n## Does the preview add to BSP? (BSP-matched races, trained on winners)\n")
    fpb, esb, teb = fp[fp.p_bsp.notna()], es[es.p_bsp.notna()], te[te.p_bsp.notna()]
    print("| inputs | rounds | scored log loss | gap to BSP |\n|---|---|---|---|")
    for name, cols in (("BSP alone", ["lbsp"]), ("BSP + the preview", ["lbsp"] + fp_)):
        Xf, Xe, Xt = (x[cols].astype(float) for x in (fpb, esb, teb))
        for X in (Xf, Xe, Xt):
            for c in V1.CAT:
                X[c] = 0
        bst, k, _ = R2.fit_es(Xf, fpb.won.values.astype(float), fpb.race_id, Xe, esb.won.values, esb.race_id.values,
                              R2.SMALL, 1500)
        pt = V1.race_softmax(bst.predict(Xt, num_iteration=k, raw_score=True), teb.race_id.values)
        print(f"| {name} | {k} | {V1.ll(pt, teb.won):.4f} | {V1.ll(pt, teb.won) - V1.ll(teb.p_bsp, teb.won):+.4f} |")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz preview")
