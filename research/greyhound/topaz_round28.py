"""Round 28: does the market over-rate box 8? Lay it at BSP (7 Nov 2026, founder: "Maybe it's the other way that the
market over rates from box 8 or something").

    python research/greyhound/topaz_round28.py DIR LABEL    (BETFAIR_DIR, RACES_DIR, ISOLYNX_DIR; WALK_GRV_RATING /
                                                             WALK_RELIABLE / WALK_LEAD / WALK_DRIFT as the weekly train;
                                                             BSP_COMM to change the 8% commission)

Test 2 (every Australian race) found box 8 the one box BSP over-rates: A/E 0.970, both halves; Test 24 found the same
in Victoria (0.971 / 0.982). A lay at BSP needs A/E under about 0.92-0.93 to pay 8% commission. Here, in Victoria, on
the standard split, the lay (1 unit at BSP: a loser keeps 1 - c, a winner costs BSP - 1; no first starters) of
  box 8, and box 1 beside it as the control
  x where that box is weak at this track and distance (box_ratio, its win rate over its field-size share from earlier
    days, 0.8 or under), middling, or strong (1.1 or over), and anywhere
  x BSP $1.50-$4, $4-$8, $8-$15, $15-$40, $40-$100
  x our view: any; the market likes it more than we do (BSP at or under our price / 1.2); less (BSP 1.3x ours or more)
Every rule with 100+ lays in the scored quarter is shown, on the early-stopping months and both scored halves, with
A/E against BSP beside the break-even A/E. "Chosen": 200+ lays and a profit on the early-stopping months.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round3 as R3         # noqa: E402
import topaz_round18 as R18       # noqa: E402
import topaz_round27 as R27       # noqa: E402
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402

COMM = R27.COMM
BANDS = [(1.5, 4), (4, 8), (8, 15), (15, 40), (40, 100)]
MIN_LAYS = 200


def groups(t: pd.DataFrame) -> dict:
    """Box 8 and box 1, anywhere and by how that box does at this track and distance on earlier days."""
    box = pd.to_numeric(t.box, errors="coerce").values
    ratio = t.box_ratio.values.astype(float) if "box_ratio" in t else np.full(len(t), np.nan)
    out = {}
    for b in (8, 1):
        m = box == b
        out[f"box {b}, anywhere"] = m
        out[f"box {b}, weak here (0.8 or under)"] = m & (ratio <= 0.8)
        out[f"box {b}, middling here"] = m & (ratio > 0.8) & (ratio < 1.1)
        out[f"box {b}, strong here (1.1 or over)"] = m & (ratio >= 1.1)
    return out


def views(t: pd.DataFrame) -> dict:
    bsp, ours = t.bsp.values.astype(float), 1 / t.p_x.values
    return {"any view": np.ones(len(t), bool), "market likes it more (BSP <= ours / 1.2)": bsp <= ours / 1.2,
            "market likes it less (BSP >= 1.3x ours)": bsp >= 1.3 * ours}


def lay_mask(t: pd.DataFrame, grp, view, lo, hi) -> np.ndarray:
    bsp = t.bsp.values.astype(float)
    runs = t.runs.values if "runs" in t else np.ones(len(t))
    return grp & view & (bsp >= lo) & (bsp < hi) & (runs > 0)


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    df, num, rel, note = W.build_full(d)
    df, chk, _ = R18.check_features(df, os.environ.get("ISOLYNX_DIR", ""))
    cols = num + chk
    print(f"# {label}: round 28, lay box 8 at BSP ({COMM:.0%} commission)\n\n{note}\n")
    q75 = df.date.quantile(0.75)
    es_start = q75 - min(pd.Timedelta(days=183), (q75 - df.date.min()) / 4)
    pre, te = df[df.date < q75], df[df.date >= q75].copy()
    fp, es = pre[pre.date < es_start].copy(), pre[pre.date >= es_start].copy()
    recency = 0.5 ** (((es_start - fp.date).dt.days / 365.25).values / 3.0)
    Xf, Xe, Xt = T.features(fp, cols, rel), T.features(es, cols, rel), T.features(te, cols, rel)
    bst, k, _ = R3.fit_weighted(Xf, fp.p_mkt.values.astype(float), fp.race_id, Xe, es.won.values, es.race_id.values,
                                recency, rounds=6000)
    es["p_x"] = V1.race_softmax(bst.predict(Xe, num_iteration=k, raw_score=True), es.race_id.values)
    te["p_x"] = V1.race_softmax(bst.predict(Xt, num_iteration=k, raw_score=True), te.race_id.values)
    e = es[es.bsp.notna() & (es.bsp > 1)].copy()
    t = te[te.bsp.notna() & (te.bsp > 1)].copy()
    he = np.ones(len(e), bool)
    h = (t.date < t.date.quantile(0.5)).values
    ge, gt, ve, vt = groups(e), groups(t), views(e), views(t)
    print(f"{k} rounds, {len(cols)} inputs; scored {t.date.min():%Y-%m-%d} to {t.date.max():%Y-%m-%d}, halves split at "
          f"{t.date.quantile(0.5):%Y-%m-%d}. A lay pays when its A/E against BSP is under the break-even A/E.\n")
    print("| lay at BSP | early-stopping: lays, A/E, return | 1st half: lays, A/E, return | 2nd half: lays, A/E, return | "
          "all: lays, winners, A/E (break-even), return, units |\n|---|---|---|---|---|")
    chosen = held = shown = 0
    for gname in gt:
        for vname in vt:
            for lo, hi in BANDS:
                me, mt = lay_mask(e, ge[gname], ve[vname], lo, hi), lay_mask(t, gt[gname], vt[vname], lo, hi)
                if mt.sum() < 100:
                    continue
                shown += 1
                re_, rt = R27.row(e, me, he), R27.row(t, mt, h)
                pick = re_["all"][0] >= MIN_LAYS and re_["all"][1] > 0
                both = rt["1st"][1] > 0 and rt["2nd"][1] > 0
                chosen += pick
                held += pick and both
                tag = (" **chosen**" if pick else "") + (" **both halves**" if both else "")
                f = lambda x: f"{x[0]:,}, {x[2]:.3f}, {x[1]:+.1%}" if x[0] else "0"   # noqa: E731
                print(f"| {gname}, {vname}, BSP ${lo:g}-${hi:g} | {f(re_['all'])} | {f(rt['1st'])} | {f(rt['2nd'])} | "
                      f"{rt['all'][0]:,}, {rt['wins']:,}, {rt['all'][2]:.3f} ({rt['be']:.3f}), {rt['all'][1]:+.1%}, "
                      f"{rt['units']:+,.0f}{tag} |")
    print(f"\nRules shown: {shown}. Chosen on the early-stopping months: {chosen}; of them in profit in both scored halves: "
          f"{held}")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 28")
