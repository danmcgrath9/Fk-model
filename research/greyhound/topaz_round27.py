"""Round 27: lay the dogs the market dislikes, at BSP (7 Nov 2026, founder: "when we rate a horse between $7-$15 and
it starts $15-$40 with a 1.5x bigger price than us. The market knows something we don't, it's right not us. So if we
lay those horses we make money at bsp").

    python research/greyhound/topaz_round27.py DIR LABEL    (BETFAIR_DIR, RACES_DIR, ISOLYNX_DIR; WALK_GRV_RATING /
                                                             WALK_RELIABLE / WALK_LEAD / WALK_DRIFT as the weekly train;
                                                             BSP_COMM to change the 8% commission)

Test 34 laid at BSP $15-$40 when BSP was 1.6x our price or more: the dogs won 7% less often than BSP said (A/E 0.930),
short of the 8% commission (-2.5%); at 2x, A/E 0.898 and +0.8%. Here the lay is the same (lay 1 unit at BSP: a loser
keeps 1 - c, a winner costs BSP - 1, no first starters) and the question is where the market's dislike is strongest:
  BSP bands $8-$15, $15-$40, $40-$100
  x BSP at least r x our price, r = 1.6, 2, 2.5, 3
  x who: all runners; no tracked run; GRV did not tip it; boxes 7-8; drifted 1.3x or more from its shortest pre-play
    price (known only near the off); did not drift; a tracked run before
Every rule is shown, on the early-stopping months and on both halves of the scored quarter, with A/E against BSP and
the A/E a lay needs to break even at its prices (lay pays when the dogs win less than that). A rule "chosen" made a
profit on 200+ lays on the early-stopping months.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round3 as R3         # noqa: E402
import topaz_round12 as R12       # noqa: E402
import topaz_round18 as R18       # noqa: E402
import topaz_round24 as R24       # noqa: E402
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402

COMM = R24.COMM
BANDS = [(8, 15), (15, 40), (40, 100)]
RATIOS = (1.6, 2.0, 2.5, 3.0)
MIN_LAYS = 200


def who(t: pd.DataFrame) -> dict:
    """The runner groups to lay within; a group whose input is missing is left out."""
    out = {"all runners": np.ones(len(t), bool)}
    if "iso_runs" in t:
        out["no tracked run"] = (t.iso_runs.fillna(0) == 0).values
        out["a tracked run before"] = (t.iso_runs.fillna(0) > 0).values
    if "tip_rank" in t:
        out["GRV did not tip it"] = (t.tip_rank.fillna(0) == 0).values
    box = pd.to_numeric(t.box, errors="coerce")
    out["boxes 7-8"] = (box >= 7).values
    if "drift" in t:
        out["drifted 1.3x+ (near the off)"] = (t.drift >= 1.3).values
        out["did not drift 1.3x"] = (t.drift < 1.3).values
    return out


def lay_mask(t: pd.DataFrame, grp, lo, hi, r) -> np.ndarray:
    """Lay at BSP: BSP in [lo, hi) and at least r x our price, never a first starter."""
    bsp, ours = t.bsp.values.astype(float), 1 / t.p_x.values
    runs = t.runs.values if "runs" in t else np.ones(len(t))
    return grp & (bsp >= lo) & (bsp < hi) & (bsp >= r * ours) & (runs > 0)


def breakeven_ae(bsp, comm=COMM) -> float:
    """The A/E against BSP at which laying these runners breaks even: a lay keeps 1 - c when the dog loses and pays
    BSP - 1 when it wins, so with p the true chance the return is (1 - p)(1 - c) - p(BSP - 1) = 0, p = (1 - c)/(BSP - c).
    Summed over the runners against BSP's own chances, 1/BSP."""
    bsp = np.asarray(bsp, float)
    return float(((1 - comm) / (bsp - comm)).sum() / (1 / bsp).sum())


def row(t, m, h, comm=COMM) -> dict:
    ret = R24.returns("lay", t.won.values, t.bsp.values, comm)
    out = {}
    for name, hm in (("1st", h), ("2nd", ~h), ("all", np.ones(len(t), bool))):
        mm = m & hm
        n = int(mm.sum())
        out[name] = (n, float(ret[mm].mean()) if n else np.nan,
                     float(t.won.values[mm].sum() / (1 / t.bsp.values[mm]).sum()) if n else np.nan)
    out["be"] = breakeven_ae(t.bsp.values[m], comm) if m.any() else np.nan
    out["wins"] = int(t.won.values[m].sum())
    out["units"] = float(ret[m].sum())
    return out


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    df, num, rel, note = W.build_full(d)
    df, chk, _ = R18.check_features(df, os.environ.get("ISOLYNX_DIR", ""))
    df = R12.tale_columns(df)
    cols = num + chk
    print(f"# {label}: round 27, lay the dogs the market dislikes, at BSP ({COMM:.0%} commission)\n\n{note}\n")
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
    we, wt = who(e), who(t)
    print(f"{k} rounds, {len(cols)} inputs. Early-stopping months {e.date.min():%Y-%m-%d} to {e.date.max():%Y-%m-%d}; "
          f"scored {t.date.min():%Y-%m-%d} to {t.date.max():%Y-%m-%d}, halves split at {t.date.quantile(0.5):%Y-%m-%d}. "
          f"A lay pays when its A/E against BSP is under the break-even A/E.\n")
    print("| lay at BSP | early-stopping: lays, A/E, return | 1st half: lays, A/E, return | 2nd half: lays, A/E, return | "
          "all: lays, winners, A/E (break-even), return, units |\n|---|---|---|---|---|")
    chosen = held = 0
    for name in wt:
        for lo, hi in BANDS:
            for r in RATIOS:
                me, mt = lay_mask(e, we[name], lo, hi, r), lay_mask(t, wt[name], lo, hi, r)
                if mt.sum() < 100:
                    continue
                re_, rt = row(e, me, he), row(t, mt, h)
                pick = re_["all"][0] >= MIN_LAYS and re_["all"][1] > 0
                both = rt["1st"][1] > 0 and rt["2nd"][1] > 0
                chosen += pick
                held += pick and both
                tag = (" **chosen**" if pick else "") + (" **both halves**" if both else "")
                f = lambda x: f"{x[0]:,}, {x[2]:.3f}, {x[1]:+.1%}" if x[0] else "0"   # noqa: E731
                print(f"| {name}, BSP ${lo}-${hi}, BSP >= {r:g}x ours | {f(re_['all'])} | {f(rt['1st'])} | {f(rt['2nd'])} | "
                      f"{rt['all'][0]:,}, {rt['wins']:,}, {rt['all'][2]:.3f} ({rt['be']:.3f}), {rt['all'][1]:+.1%}, "
                      f"{rt['units']:+,.0f}{tag} |")
    print(f"\nChosen on the early-stopping months: {chosen}; of them in profit in both scored halves: {held}")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 27")
