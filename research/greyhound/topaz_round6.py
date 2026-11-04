"""Round 6: the ratings engine upgrades, then Isolynx and GRV's own fields as they arrive, against BSP
(4 Nov 2026, founder: "BUILD THE BEST MODEL IN THE WORLD").

    python research/greyhound/topaz_round6.py DIR LABEL     (BETFAIR_DIR as before; ISOLYNX_DIR when the tracking
                                                              pull exists; results only)

Rows, each fitted as round 3's B2 (recent years weighted more, BSP chances, early stopping on the six months before
the scored quarter), scored on the same 22,841 races:
  D0  round 3's B2 plus this race's preview (Test 15: +0.1172), WITHOUT the new ratings
  D1  + the ratings upgrades: shrinkage toward the grade prior, ability by distance band and at this track, Elo over
        margins (greyhound/ratings.py, 4 Nov)
  D2  + Isolynx tracking ratings for the dog's earlier tracked runs, when ISOLYNX_DIR is set: its jump time, time to
        50 m and 100 m, last 100 m and average rail distance, each as a par-relative rating by track and distance
        (last run and mean of last 3), plus how many tracked runs it has
The best row is chosen on the early-stopping months and staked as Test 12 (rules chosen there, scored once).
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_preview_test as PT   # noqa: E402
import topaz_round3 as R3         # noqa: E402
import topaz_round4 as R4         # noqa: E402
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402

ISO_MEASURES = ["jump_time", "t50", "t100", "last100", "avg_rail", "v100", "max_speed"]


def isolynx_features(df, iso_dir):
    """Par-relative ratings of each dog's EARLIER tracked runs (end of the previous day), from the Isolynx table."""
    from greyhound.isolynx import table
    from greyhound.ratings import _asof
    t = table(iso_dir)
    if t is None or not len(t):
        return df, [], "Isolynx: no tracked runs found"
    t = t.dropna(subset=["date"]).copy()
    t["dog"] = t.dog.astype("Int64").astype(str)
    t = t.sort_values("date")
    feats = []
    for m in ISO_MEASURES:
        if m not in t:
            continue
        ok = t[m].notna()
        g = t[ok].groupby(["venue", "distance"])[m]
        par = g.transform(lambda s: s.expanding().median().shift())
        sign = -1.0 if m in ("jump_time", "t50", "t100", "last100", "avg_rail") else 1.0   # lower is better for times
        t.loc[ok, f"_r_{m}"] = sign * (t.loc[ok, m] - par)
        x = t.dropna(subset=[f"_r_{m}"]).sort_values(["dog", "date"])
        gd = x.groupby("dog")[f"_r_{m}"]
        x = x.assign(_last=x[f"_r_{m}"], _m3=gd.rolling(3, min_periods=1).mean().reset_index(level=0, drop=True))
        day = x.groupby(["dog", "date"])[["_last", "_m3"]].last().reset_index()
        df[f"iso_{m}_last"] = _asof(df[["dog", "date"]], day, ["dog"], "_last")
        df[f"iso_{m}_m3"] = _asof(df[["dog", "date"]], day, ["dog"], "_m3")
        feats += [f"iso_{m}_last", f"iso_{m}_m3"]
    cnt = t.groupby(["dog", "date"]).size().groupby(level=0).cumsum().reset_index(name="_n")
    df["iso_runs"] = _asof(df[["dog", "date"]], cnt, ["dog"], "_n").fillna(0.0)
    feats.append("iso_runs")
    note = (f"Isolynx: {len(t):,} tracked runs, {t.dog.nunique():,} dogs, {t.date.min():%Y-%m-%d} to "
            f"{t.date.max():%Y-%m-%d}; a tracked run before the race for {(df.iso_runs > 0).mean():.0%} of runners")
    return df, feats, note


def main(d, label):
    df, num, rel, bsp_note = W.build(d)
    if "is_best_bet" not in df and "isBestBet" in df:
        df["is_best_bet"] = df.isBestBet
    df, fpv, _ = PT.preview_features(df)
    iso_dir = os.environ.get("ISOLYNX_DIR", "")
    df, fiso, iso_note = isolynx_features(df, iso_dir) if iso_dir and os.path.isdir(iso_dir) else (df, [], "no ISOLYNX_DIR")
    df = df.copy()
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
    old = [c for c in num if c not in V1.NEW_RATINGS] + fpv
    old_rel = [c for c in rel if c not in V1.NEW_REL]
    print(f"# {label}: round 6\n\n{bsp_note}\n{iso_note}\nscored: {te[hb].race_id.nunique():,} races, BSP {bsp_all:.4f}\n")
    print("| row | features | rounds | early-stopping log loss | scored log loss | gap to BSP | 1st half | 2nd half |")
    print("|---|---|---|---|---|---|---|---|")
    rows = [("D0 B2 + preview, old ratings", old, old_rel), ("D1 + ratings upgrades", old + V1.NEW_RATINGS, old_rel + V1.NEW_REL)]
    if fiso:
        rows.append(("D2 + Isolynx ratings", old + V1.NEW_RATINGS + fiso, old_rel + V1.NEW_REL + [f for f in fiso if f.endswith("_m3")]))
    best = None
    for name, cols, rl in rows:
        Xf, Xe, Xt = T.features(fp, cols, rl), T.features(es, cols, rl), T.features(te, cols, rl)
        bst, k, _ = R3.fit_weighted(Xf, fp.p_mkt.values.astype(float), fp.race_id, Xe, es.won.values, es.race_id.values, recency)
        pe = V1.race_softmax(bst.predict(Xe, num_iteration=k, raw_score=True), es.race_id.values)
        pt = V1.race_softmax(bst.predict(Xt, num_iteration=k, raw_score=True), te.race_id.values)
        le = V1.ll(pe[hb_es], es.won.values[hb_es])
        l, l1, l2 = V1.ll(pt[hb], w_te[hb]), V1.ll(pt[hb & h], w_te[hb & h]), V1.ll(pt[hb & ~h], w_te[hb & ~h])
        print(f"| {name} | {Xf.shape[1]} | {k} | {le:.4f} | {l:.4f} | {l - bsp_all:+.4f} | {l1 - b1:+.4f} | {l2 - b2:+.4f} |")
        imp = pd.Series(bst.feature_importance("gain"), index=Xf.columns).sort_values(ascending=False)
        new = imp[[c for c in imp.index if c.split("_rel")[0] in V1.NEW_RATINGS or c.startswith("iso_")]]
        if len(new):
            print(f"  new inputs' share {new.sum() / imp.sum():.1%}: " + ", ".join(f"{i} {v / imp.sum():.1%}" for i, v in new.head(8).items()))
        if best is None or le < best[0]:
            best = (le, name, pe, pt)
    _, name, pe, pt = best
    print(f"\nChosen on the early-stopping months: **{name}**")
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
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 6")
