"""Round 25: where is the gap to BSP? (6 Nov 2026, founder: "find all the ways to use the data to get closer to bsp, see
where we differ most").

    python research/greyhound/topaz_round25.py DIR LABEL    (BETFAIR_DIR, RACES_DIR, ISOLYNX_DIR; WALK_GRV_RATING /
                                                             WALK_RELIABLE / WALK_LEAD / WALK_DRIFT as the weekly train)

Our best model so far (the production inputs + Isolynx + the checks, Test 35) on the standard split. For every scored
race with a BSP on every runner, the gap on its winner:
  g = ln(BSP's chance for the winner) - ln(our chance for the winner)        (the mean of g is the gap to BSP)
The total is then split slice by slice, and each slice reports its races, its mean gap and its SHARE of the whole gap,
so the biggest buckets show first:
  the race: track, distance, grade, field size, hour, month
  the winner: its BSP, our price, BSP over our price (who was right when we differed), its starts, days since its last
  start, box, GRV's tip, a tracked run before, checked last time, first time at the track, and how far it FIRMED
  before the off (its longest price traded over BSP: the late money no form guide carries)
And runner by runner, BSP's price over ours: when we differ most, who is right (A/E against each).
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round12 as R12       # noqa: E402
import topaz_round18 as R18       # noqa: E402
import topaz_round3 as R3         # noqa: E402
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402

MIN_RACES = int(os.environ.get("GAP_MIN_RACES", "150") or 150)
RATIO_BANDS = [(0, 0.5), (0.5, 0.8), (0.8, 1.25), (1.25, 2), (2, np.inf)]
RATIO_NAMES = ["BSP under half our price", "BSP 0.5-0.8x ours", "within 25%", "BSP 1.25-2x ours", "BSP over 2x ours"]


def cut(x: pd.Series, edges, names) -> pd.Series:
    out = pd.Series(np.nan, index=x.index, dtype=object)
    for (lo, hi), name in zip(edges, names):
        out[(x >= lo) & (x < hi)] = name
    return out


def winner_gaps(t: pd.DataFrame, pcol: str) -> pd.DataFrame:
    """One row per race: the winner's row with g = ln p_bsp - ln p_ours."""
    w = t[t.won == 1].drop_duplicates("race_id").copy()
    w["g"] = np.log(np.clip(w.p_bsp.values, 1e-12, 1)) - np.log(np.clip(w[pcol].values, 1e-12, 1))
    return w


def share_table(w: pd.DataFrame, key, title: str, order=None, min_races=None):
    min_races = MIN_RACES if min_races is None else min_races
    key = pd.Series(np.asarray(key, dtype=object), index=w.index)
    total = w.g.sum()
    print(f"\n| {title} | races | share of races | mean gap | share of the whole gap |\n|---|---|---|---|---|")
    keys = order if order is not None else (w.assign(_k=key).groupby("_k").g.sum().sort_values(ascending=False).index)
    for k in keys:
        m = (key == k).values
        if m.sum() < min_races:
            continue
        print(f"| {k} | {m.sum():,} | {m.mean():.1%} | {w.g.values[m].mean():+.4f} | {w.g.values[m].sum() / total:.1%} |")


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    df, num, rel, note = W.build_full(d)
    df, chk, _ = R18.check_features(df, os.environ.get("ISOLYNX_DIR", ""))
    df = R12.tale_columns(df)
    cols = num + chk
    print(f"# {label}: round 25, where is the gap to BSP?\n\n{note}\n")
    q75 = df.date.quantile(0.75)
    es_start = q75 - min(pd.Timedelta(days=183), (q75 - df.date.min()) / 4)
    pre, te = df[df.date < q75], df[df.date >= q75].copy()
    fp, es = pre[pre.date < es_start].copy(), pre[pre.date >= es_start].copy()
    recency = 0.5 ** (((es_start - fp.date).dt.days / 365.25).values / 3.0)
    Xf, Xe, Xt = T.features(fp, cols, rel), T.features(es, cols, rel), T.features(te, cols, rel)
    bst, k, _ = R3.fit_weighted(Xf, fp.p_mkt.values.astype(float), fp.race_id, Xe, es.won.values, es.race_id.values,
                                recency, rounds=6000)
    te["p_x"] = V1.race_softmax(bst.predict(Xt, num_iteration=k, raw_score=True), te.race_id.values)
    full = te.p_bsp.notna().groupby(te.race_id).transform("all").values
    t = te[full].copy()
    t["p_bsp"] = t.p_bsp / t.p_bsp.groupby(t.race_id).transform("sum")
    w = winner_gaps(t, "p_x")
    print(f"{k} rounds, {len(cols)} inputs. {len(w):,} scored races with a BSP on every runner, from {w.date.min():%Y-%m-%d}: "
          f"our log loss {V1.ll(t.p_x, t.won):.4f}, BSP's {V1.ll(t.p_bsp, t.won):.4f}, **gap {w.g.mean():+.4f}** "
          f"(1st half {w.g[w.date < w.date.quantile(0.5)].mean():+.4f}, 2nd {w.g[w.date >= w.date.quantile(0.5)].mean():+.4f})")

    # the race
    share_table(w, w.track.astype(str), "track")
    dist = pd.cut(w.distance, [0, 350, 420, 520, 620, 2000], labels=["under 350 m", "350-419 m", "420-519 m", "520-619 m",
                                                                     "620 m+"]).astype(str)
    share_table(w, dist, "distance")
    if "grade" in w:
        share_table(w, w.grade.astype(str), "grade")
    share_table(w, w.field.astype("Int64").astype(str), "field size")
    if "hour" in w:
        share_table(w, pd.cut(w.hour, [-1, 14, 17, 20, 24], labels=["before 3pm", "3-6pm", "6-9pm", "9pm on"]).astype(str),
                    "start (Melbourne)")

    # the winner
    bspw = 1 / w.p_bsp
    share_table(w, pd.cut(bspw, [1, 2, 3, 5, 8, 15, 1000], labels=["$1-$2", "$2-$3", "$3-$5", "$5-$8", "$8-$15", "$15+"]).astype(str),
                "the winner's BSP", order=["$1-$2", "$2-$3", "$3-$5", "$5-$8", "$8-$15", "$15+"])
    oursw = 1 / w.p_x
    share_table(w, pd.cut(oursw, [1, 2, 3, 5, 8, 15, 1000], labels=["$1-$2", "$2-$3", "$3-$5", "$5-$8", "$8-$15", "$15+"]).astype(str),
                "the winner's price from us", order=["$1-$2", "$2-$3", "$3-$5", "$5-$8", "$8-$15", "$15+"])
    share_table(w, cut(bspw / oursw, RATIO_BANDS, RATIO_NAMES), "the winner: BSP over our price", order=RATIO_NAMES)
    share_table(w, pd.cut(w.runs, [-1, 0, 3, 10, 30, 1000], labels=["debut", "1-3 starts", "4-10", "11-30", "31+"]).astype(str),
                "the winner's starts before", order=["debut", "1-3 starts", "4-10", "11-30", "31+"])
    share_table(w, pd.cut(w.days_since, [0, 4, 8, 15, 29, 60, 10000], labels=["up to 4 days", "5-8", "9-15", "16-29", "30-60",
                                                                               "61+"]).astype(str),
                "days since the winner's last start", order=["up to 4 days", "5-8", "9-15", "16-29", "30-60", "61+", "nan"])
    share_table(w, pd.to_numeric(w.box, errors="coerce").astype("Int64").astype(str), "the winner's box")
    if "tip_rank" in w:
        share_table(w, w.tip_rank.fillna(0).astype(int).astype(str).replace("0", "not tipped"), "GRV's tip for the winner")
    if "iso_runs" in w:
        share_table(w, np.where(w.iso_runs > 0, "a tracked run before", "no tracked run").astype(object), "tracking")
    if "chk_last" in w:
        share_table(w, w.chk_last.map({1.0: "checked last time", 0.0: "clean last time"}).fillna("no tracked run"),
                    "the winner's last tracked run")
    if "track_runs" in w:
        share_table(w, np.where((w.track_runs == 0) & (w.runs > 0), "first time here", "raced here before").astype(object),
                    "the winner at this track")
    if "firm" in w:
        share_table(w, cut(w.firm, [(0, 1.1), (1.1, 1.3), (1.3, 1.6), (1.6, 2.2), (2.2, np.inf)],
                           ["firmed under 1.1x", "1.1-1.3x", "1.3-1.6x", "1.6-2.2x", "firmed 2.2x+"]).fillna("no price traded"),
                    "how far the winner firmed before the off (longest price over BSP)",
                    order=["firmed under 1.1x", "1.1-1.3x", "1.3-1.6x", "1.6-2.2x", "firmed 2.2x+", "no price traded"])

    # runner by runner: who is right when we differ
    t["ratio"] = (1 / t.p_bsp) / (1 / t.p_x)
    band = cut(t.ratio, RATIO_BANDS, RATIO_NAMES)
    print("\n| runner: BSP over our price | runners | wins | A/E vs ours | A/E vs BSP |\n|---|---|---|---|---|")
    for name in RATIO_NAMES:
        m = (band == name).values
        if m.sum():
            g = t[m]
            print(f"| {name} | {m.sum():,} | {int(g.won.sum()):,} | {g.won.sum() / g.p_x.sum():.3f} | {g.won.sum() / g.p_bsp.sum():.3f} |")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 25")
