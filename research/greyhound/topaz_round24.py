"""Round 24: a rule search at BSP, chosen on old months, scored once on new ones (6 Nov 2026, founder: "Surely we could
find rules with our markets to beat bsp").

    python research/greyhound/topaz_round24.py DIR LABEL    (BETFAIR_DIR, RACES_DIR, ISOLYNX_DIR optional; WALK_GRV_RATING
                                                             / WALK_RELIABLE / WALK_LEAD as the weekly train sets them;
                                                             BSP_COMM to change the 8% commission)

The production model (with Isolynx and the checks when ISOLYNX_DIR is set) on the standard split. Its prices on the
early-stopping months (the 6 months before the scored quarter, never trained on) choose the rules; the scored quarter
tests them, once, both halves. A rule is
  segment (all runners; backing up within 4 days; first time at the track; checked in its last tracked run; a clean
  last tracked run; boxes 1-2; boxes 7-8; first starters)
  x BSP band ($1.50-$3, $3-$5, $5-$8, $8-$15, $15-$30)
  x side and edge: BACK at BSP when BSP >= r x our price, or LAY at BSP when BSP <= our price / r, r = 1.1, 1.3, 1.6
Flat 1-unit stakes, commission on winnings (a back pays (BSP - 1) x (1 - c); a lay that wins keeps 1 - c and loses
BSP - 1). Chosen: at least 200 bets and a profit on the early-stopping months. Reported: how many rules were tried, how
many were chosen, how many we would expect to be chosen by luck (the share with a profit when every rule is a fair
coin), and every chosen rule's result in both halves of the scored quarter.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round3 as R3         # noqa: E402
import topaz_round18 as R18       # noqa: E402
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402

COMM = float(os.environ.get("BSP_COMM", "0.08") or 0.08)
BANDS = [(1.5, 3), (3, 5), (5, 8), (8, 15), (15, 30)]
RATIOS = (1.1, 1.3, 1.6)
MIN_BETS = 200


def segments(t: pd.DataFrame) -> dict:
    out = {"all runners": np.ones(len(t), bool)}
    if "days_since" in t:
        out["backing up within 4 days"] = (t.days_since <= 4).values
    if "runs_track" in t and "runs" in t:
        out["first time at the track"] = ((t.runs_track == 0) & (t.runs > 0)).values
        out["first starters"] = (t.runs == 0).values
    if "chk_last" in t:
        out["checked last tracked run"] = (t.chk_last == 1).values
        out["clean last tracked run"] = (t.chk_last == 0).values
    box = pd.to_numeric(t.box, errors="coerce")
    out["boxes 1-2"] = (box <= 2).values
    out["boxes 7-8"] = (box >= 7).values
    return out


def returns(side: str, won, bsp, comm=COMM) -> np.ndarray:
    won, bsp = np.asarray(won), np.asarray(bsp, float)
    if side == "back":
        return np.where(won == 1, (bsp - 1) * (1 - comm), -1.0)
    return np.where(won == 1, -(bsp - 1), 1 - comm)


def rule_mask(t, seg, lo, hi, side, r):
    bsp, ours = t.bsp.values.astype(float), 1 / t.p_x.values
    m = seg & (bsp >= lo) & (bsp < hi)
    return m & (bsp >= r * ours) if side == "back" else m & (bsp <= ours / r)


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    df, num, rel, note = W.build_full(d)
    df, chk, _ = R18.check_features(df, os.environ.get("ISOLYNX_DIR", ""))
    cols, rels = num + chk, rel
    print(f"# {label}: round 24, a rule search at BSP ({COMM:.0%} commission)\n\n{note}\n")
    q75 = df.date.quantile(0.75)
    es_start = q75 - min(pd.Timedelta(days=183), (q75 - df.date.min()) / 4)
    pre, te = df[df.date < q75], df[df.date >= q75].copy()
    fp, es = pre[pre.date < es_start].copy(), pre[pre.date >= es_start].copy()
    recency = 0.5 ** (((es_start - fp.date).dt.days / 365.25).values / 3.0)
    Xf, Xe, Xt = T.features(fp, cols, rels), T.features(es, cols, rels), T.features(te, cols, rels)
    bst, k, _ = R3.fit_weighted(Xf, fp.p_mkt.values.astype(float), fp.race_id, Xe, es.won.values, es.race_id.values,
                                recency, rounds=6000)
    es["p_x"] = V1.race_softmax(bst.predict(Xe, num_iteration=k, raw_score=True), es.race_id.values)
    te["p_x"] = V1.race_softmax(bst.predict(Xt, num_iteration=k, raw_score=True), te.race_id.values)
    e = es[es.bsp.notna() & (es.bsp > 1)].copy()
    t = te[te.bsp.notna() & (te.bsp > 1)].copy()
    h = (t.date < t.date.quantile(0.5)).values
    se, st = segments(e), segments(t)
    tried, chosen = 0, []
    for name in se:
        for lo, hi in BANDS:
            for side in ("back", "lay"):
                for r in RATIOS:
                    me = rule_mask(e, se[name], lo, hi, side, r)
                    if me.sum() < MIN_BETS:
                        continue
                    tried += 1
                    re_ = returns(side, e.won.values[me], e.bsp.values[me])
                    if re_.mean() > 0:
                        chosen.append((name, lo, hi, side, r, int(me.sum()), float(re_.mean())))
    print(f"{k} rounds; {len(cols)} inputs. Rules with {MIN_BETS}+ bets on the early-stopping months "
          f"({e.date.min():%Y-%m-%d} to {e.date.max():%Y-%m-%d}): {tried}; with a profit there: {len(chosen)}. "
          f"With no edge at all, about a third to a half would show a profit by luck over a sample this size.\n")
    print("| rule | early-stopping months (bets, ROI) | scored 1st half: bets, ROI | 2nd half: bets, ROI | all: bets, winners, "
          "A/E vs BSP, ROI, units |\n|---|---|---|---|---|")
    held = 0
    for name, lo, hi, side, r, n_e, roi_e in sorted(chosen, key=lambda x: -x[6]):
        mt = rule_mask(t, st[name], lo, hi, side, r)
        if not mt.any():
            continue
        ret = returns(side, t.won.values, t.bsp.values)
        r1, r2 = ret[mt & h], ret[mt & ~h]
        ae = t.won.values[mt].sum() / (1 / t.bsp.values[mt]).sum()
        both = (len(r1) and r1.mean() > 0) and (len(r2) and r2.mean() > 0)
        held += bool(both)
        cond = f"BSP >= {r:g}x ours" if side == "back" else f"BSP <= ours / {r:g}"
        print(f"| {side} {name}, BSP ${lo:g}-${hi:g}, {cond} | {n_e:,}, {roi_e:+.1%} | {len(r1):,}, "
              f"{(r1.mean() if len(r1) else np.nan):+.1%} | {len(r2):,}, {(r2.mean() if len(r2) else np.nan):+.1%} | "
              f"{mt.sum():,}, {int(t.won.values[mt].sum()):,}, {ae:.3f}, {ret[mt].mean():+.1%}, {ret[mt].sum():+,.0f}"
              f"{' **both halves**' if both else ''} |")
    print(f"\nChosen rules in profit in both halves of the scored quarter: {held} of {len(chosen)}")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 24")
