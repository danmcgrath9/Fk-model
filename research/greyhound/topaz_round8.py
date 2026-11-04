"""Round 8: GRV's tips for this race, and the round cap, against BSP (4 Nov 2026, founder: "BUILD THE BEST MODEL IN
THE WORLD"; MODELS_RESEARCH.md item 5, expert prices as inputs).

    python research/greyhound/topaz_round8.py DIR LABEL     (BETFAIR_DIR as before; RACES_DIR = the race records
                                                             pulled with mode=run races=yes; results only)

Rows, each fitted as round 3's B2 (recent years weighted more, BSP chances, early stopping on the six months before
the scored quarter), scored on the same 22,841 races:
  F0  round 6's D1 (B2 + preview + ratings upgrades)                                   (Test 16: +0.1085)
  F1  + GRV's tips for this race: the runner's tip rank (first to fourth, or untipped), how many tips the race
        carries, the analyst comment's length, whether a suggested bet exists. Legitimate for the open because the
        race preview is published the evening before (Test 15); the 5 Nov compare says whether tips change after
  F2  F1 with the round cap lifted from 3,000 to 6,000 (Test 16's D1 stopped at 2,997, the cap, not the data)
Before the table: tip coverage by year and the first tip's strike rate against the SP favourite's, because a tip
that wins far more often than the favourite in some years is a tip written after the race.
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


def tip_report(df):
    """Coverage and the first tip's strike rate by year, beside the SP favourite's."""
    print("| year | races | with a tips record | runners tipped | tip 1 won | SP favourite won |")
    print("|---|---|---|---|---|---|")
    fav = df.assign(_fav=df.groupby("race_id").p_sp.transform("max") == df.p_sp)
    for y, g in fav.groupby(df.date.dt.year):
        races = g.race_id.nunique()
        rec = g[g.tip_rank.notna()]
        rec_races = rec.race_id.nunique()
        t1 = rec[rec.tip_rank == 1]
        t1_won = t1.won.mean() if len(t1) else float("nan")
        fav_won = g[g._fav].drop_duplicates("race_id").won.mean()
        print(f"| {y} | {races:,} | {rec_races / races:.0%} | {(rec.tip_rank > 0).mean() if len(rec) else 0:.0%} | "
              f"{t1_won:.1%} ({len(t1):,}) | {fav_won:.1%} |")


def main(d, label):
    df, num, rel, bsp_note = W.build(d)
    if "is_best_bet" not in df and "isBestBet" in df:
        df["is_best_bet"] = df.isBestBet
    df, fpv, _ = PT.preview_features(df)
    races_dir = os.environ.get("RACES_DIR", "")
    ftip, tip_note = [], "no RACES_DIR: the tips rows are skipped"
    if races_dir and os.path.isdir(races_dir):
        from greyhound.races import load_races, tip_features
        races = load_races(races_dir)
        df, ftip = tip_features(df, races)
        tip_note = (f"tips: {len(races):,} race records, a tips record for {df.tip_rank.notna().mean():.0%} of runners, "
                    f"{(df.tip_rank > 0).mean():.0%} of runners tipped")
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
    print(f"# {label}: round 8, GRV's tips\n\n{bsp_note}\n{tip_note}\nscored: {te[hb].race_id.nunique():,} races, BSP {bsp_all:.4f}\n")
    if ftip:
        tip_report(df)
        print()
    print("| row | features | rounds | early-stopping log loss | scored log loss | gap to BSP | 1st half | 2nd half |")
    print("|---|---|---|---|---|---|---|---|")
    base = num + fpv
    rows = [("F0 D1 (B2 + preview + ratings upgrades)", base, rel, 3000)]
    if ftip:
        rows.append(("F1 + GRV's tips for this race", base + ftip, rel, 3000))
        rows.append(("F2 F1, round cap 6,000", base + ftip, rel, 6000))
    else:
        rows.append(("F2 D1, round cap 6,000", base, rel, 6000))
    best = None
    for name, cols, rl, cap in rows:
        Xf, Xe, Xt = T.features(fp, cols, rl), T.features(es, cols, rl), T.features(te, cols, rl)
        bst, k, _ = R3.fit_weighted(Xf, fp.p_mkt.values.astype(float), fp.race_id, Xe, es.won.values, es.race_id.values,
                                    recency, rounds=cap)
        pe = V1.race_softmax(bst.predict(Xe, num_iteration=k, raw_score=True), es.race_id.values)
        pt = V1.race_softmax(bst.predict(Xt, num_iteration=k, raw_score=True), te.race_id.values)
        le = V1.ll(pe[hb_es], es.won.values[hb_es])
        l, l1, l2 = V1.ll(pt[hb], w_te[hb]), V1.ll(pt[hb & h], w_te[hb & h]), V1.ll(pt[hb & ~h], w_te[hb & ~h])
        print(f"| {name} | {Xf.shape[1]} | {k} | {le:.4f} | {l:.4f} | {l - bsp_all:+.4f} | {l1 - b1:+.4f} | {l2 - b2:+.4f} |")
        imp = pd.Series(bst.feature_importance("gain"), index=Xf.columns).sort_values(ascending=False)
        new = imp[[c for c in imp.index if c in ftip]]
        if len(new):
            print(f"  tips' share of splits {new.sum() / imp.sum():.1%}: " + ", ".join(f"{i} {v / imp.sum():.1%}" for i, v in new.items()))
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
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 8")
