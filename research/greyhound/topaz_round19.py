"""Round 19: the label (6 Nov 2026, founder: "keep testing while it pulls").

    python research/greyhound/topaz_round19.py DIR LABEL    (BETFAIR_DIR, RACES_DIR; WALK_GRV_RATING / WALK_RELIABLE /
                                                             WALK_LEAD as the weekly train sets them)

The card's model learns the market's chances: BSP's where Betfair's files have the dog (2020 on), GRV's SP where they do
not (every race before 2020, and the runners Betfair's files miss after). GRV's SP is a bookmaker's price with a 19%
margin and its own tilts (Test 24: it under-rates favourites and GRV's best bets, over-rates dogs over 4 and
debutants), and a race whose runners mix the two prices has labels that do not add to 1. The training rows, four ways:
  L0  as the weekly train: BSP's chance, else GRV's SP's, runner by runner
  L1  only races with a BSP on every runner (2020 on)
  L2  as L0, races without a BSP on every runner at half weight
  L3  races without a BSP on every runner labelled with GRV's SP corrected to BSP: chances ~ p_sp ^ b, with b fitted on
      the training races that have both prices on every runner
The production inputs, the standard split; scored on the last quarter: log loss and gap to BSP, both halves, the gap to
GRV's SP, and the SP favourite's A/E.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round3 as R3         # noqa: E402
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402


def full_bsp(df: pd.DataFrame) -> pd.Series:
    """True for every runner of a race in which every runner has a BSP chance."""
    return df.p_bsp.notna().groupby(df.race_id).transform("all")


def fit_sp_power(df: pd.DataFrame) -> float:
    """b minimising the cross-entropy of softmax(b log p_sp) against p_bsp, over races with both on every runner."""
    from scipy.optimize import minimize_scalar
    both = full_bsp(df) & df.p_sp.notna().groupby(df.race_id).transform("all")
    g = df[both]
    if g.race_id.nunique() < 100:
        return 1.0
    lp, q, race = np.log(np.clip(g.p_sp.values, 1e-9, 1)), g.p_bsp.values, g.race_id.values

    def ce(b):
        p = V1.race_softmax(b * lp, race)
        return -(q * np.log(np.clip(p, 1e-12, 1))).sum() / g.race_id.nunique()
    return float(minimize_scalar(ce, bounds=(0.5, 2.0), method="bounded").x)


def sp_corrected(df: pd.DataFrame, b: float) -> np.ndarray:
    """GRV's SP chances raised to b and rescaled within each race."""
    return V1.race_softmax(b * np.log(np.clip(df.p_sp.values, 1e-9, 1)), df.race_id.values)


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    df, num, rel, note = W.build_full(d)
    print(f"# {label}: round 19, the label\n\n{note}\n")
    q75 = df.date.quantile(0.75)
    es_start = q75 - min(pd.Timedelta(days=183), (q75 - df.date.min()) / 4)
    pre, te = df[df.date < q75], df[df.date >= q75].copy()
    fp, es = pre[pre.date < es_start].copy(), pre[pre.date >= es_start].copy()
    recency = 0.5 ** (((es_start - fp.date).dt.days / 365.25).values / 3.0)
    full = full_bsp(fp).values
    b = fit_sp_power(fp)
    has_sp = fp.p_sp.notna().groupby(fp.race_id).transform("all").values
    print(f"Training rows: {fp.race_id.nunique():,} races, {fp.race_id[full].nunique():,} with a BSP on every runner "
          f"(from {fp.date[full].min():%Y-%m-%d}); GRV's SP corrected to BSP with power {b:.3f}\n")
    Xf, Xe, Xt = T.features(fp, num, rel), T.features(es, num, rel), T.features(te, num, rel)
    l3 = fp.p_mkt.values.astype(float).copy()
    fix = ~full & has_sp
    l3[fix] = sp_corrected(fp, b)[fix]
    rows = (("L0 BSP's chance, else GRV's SP's (the weekly train)", np.ones(len(fp), bool), fp.p_mkt.values, recency),
            ("L1 only races with a BSP on every runner", full, fp.p_mkt.values, recency),
            ("L2 the rest at half weight", np.ones(len(fp), bool), fp.p_mkt.values, recency * np.where(full, 1.0, 0.5)),
            (f"L3 the rest on GRV's SP corrected to BSP (power {b:.2f})", np.ones(len(fp), bool), l3, recency))

    w = te.won.values
    hb, hs = te.p_bsp.notna().values, te.p_sp.notna().values
    h = (te.date < te.date.quantile(0.5)).values
    b_all, b1, b2 = (V1.ll(te.p_bsp.values[m], w[m]) for m in (hb, hb & h, hb & ~h))
    sp_ll = V1.ll(te.p_sp.values[hs], w[hs])
    sp = te.start_price.where(te.start_price > 1)
    fav = (sp.groupby(te.race_id).rank(method="min") == 1).values & hb
    print(f"Scored: {te[hb].race_id.nunique():,} races with BSP (BSP {b_all:.4f}), {te[hs].race_id.nunique():,} with GRV's "
          f"SP (SP {sp_ll:.4f})\n")
    print("| training label | races | rounds | log loss | gap to BSP | 1st half | 2nd half | gap to GRV's SP | "
          "SP favourite A/E |\n|---|---|---|---|---|---|---|---|---|")
    for name, keep, y, wt in rows:
        rid = fp.race_id[keep]
        bst, k, _ = R3.fit_weighted(Xf[keep], np.asarray(y, float)[keep], rid, Xe, es.won.values, es.race_id.values,
                                    wt[keep], rounds=6000)
        p = V1.race_softmax(bst.predict(Xt, num_iteration=k, raw_score=True), te.race_id.values)
        l, l1, l2 = V1.ll(p[hb], w[hb]), V1.ll(p[hb & h], w[hb & h]), V1.ll(p[hb & ~h], w[hb & ~h])
        print(f"| {name} | {rid.nunique():,} | {k} | {l:.4f} | {l - b_all:+.4f} | {l1 - b1:+.4f} | {l2 - b2:+.4f} | "
              f"{V1.ll(p[hs], w[hs]) - sp_ll:+.4f} | {w[fav].sum() / p[fav].sum():.3f} |")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 19")
