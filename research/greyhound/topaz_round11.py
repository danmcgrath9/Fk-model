"""Round 11: reliable beginners, and dogs that like a box (5 Nov 2026, founder: "What about reliable beginners versus
not? They won't do the same every time as they miss it sometimes ... and speed from certain boxes? Some dogs like
being inside versus outside and vice versa").

    python research/greyhound/topaz_round11.py DIR LABEL     (BETFAIR_DIR, RACES_DIR as before; results only)

The model has each dog's AVERAGE first-split rating and how often it has led. Not how steady its starts are, and not
how it goes from the inside against the outside. New inputs, every one from runs on EARLIER days only:

Reliable beginners
  split_sd10        spread (standard deviation) of its first-split rating over its last 10 runs: high = erratic
  split_worst5      its worst first-split rating in its last 5: how bad a miss gets
  missed_rate10     share of its last 10 runs where it was out 3+ places worse than its early-speed rank in that race
  early_sd10        spread of its position at the first point over its last 10 runs
Box preference (inside = boxes 1-3, middle 4-5, outside 6-8)
  box_pref_time     its time rating from today's kind of box minus its rating overall, shrunk toward 0 by 3 runs
  box_pref_split    the same for its first-split rating
  box_runs_here     how many runs it has had from today's kind of box
  inside_vs_out     its shrunk inside rating minus its shrunk outside rating, signed by today's draw (+ inside today)

Rows, as round 8's F2 (D1 + preview + tips, 6,000-round cap, recency weighted, early stopped, same 22,841 races):
  H0 F2;  H1 + reliable beginners;  H2 + box preference;  H3 + both.
Then actual wins against H0's, H3's, BSP's and GRV's SP's expected for the groups the founder means.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_preview_test as PT   # noqa: E402
import topaz_round3 as R3         # noqa: E402
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402
from topaz_v2 import pir_positions  # noqa: E402

RELIABLE = ["split_sd10", "split_worst5", "missed_rate10", "early_sd10"]
BOXPREF = ["box_pref_time", "box_pref_split", "box_runs_here", "inside_vs_out"]
SHRINK = 3.0


def _prev_rolling(df: pd.DataFrame, col: str, n: int, how: str, min_periods: int = 3) -> np.ndarray:
    """`how` (std, min, mean) of `col` over the dog's last n runs on EARLIER days, as at the end of the previous day."""
    x = df[["dog", "date", col]].copy()
    x["_i"] = np.arange(len(x))
    x = x.sort_values(["dog", "date", "_i"])
    roll = getattr(x.groupby("dog")[col].rolling(n, min_periods=min_periods), how)().reset_index(level=0, drop=True)
    x["_m"] = roll
    day = x.groupby(["dog", "date"])._m.last().reset_index()
    day["prev"] = day.groupby("dog")._m.shift()
    return df[["dog", "date"]].merge(day[["dog", "date", "prev"]], on=["dog", "date"], how="left").prev.values


def _prev_sum_count(df: pd.DataFrame, keys: list, col: str):
    """Sum and count of `col` over all of the keys' runs on EARLIER days, carried to every later row of the same keys
    (an as-of join: a day on which the keys have no value of their own, today included, still gets the history)."""
    d = df[keys + ["date", col]].dropna(subset=[col])
    day = d.groupby(keys + ["date"])[col].agg(["sum", "count"]).reset_index().sort_values("date")
    day[["s", "c"]] = day.groupby(keys)[["sum", "count"]].cumsum()
    left = df[keys + ["date"]].assign(_pos=np.arange(len(df))).sort_values("date")
    m = pd.merge_asof(left, day[keys + ["date", "s", "c"]], on="date", by=keys, allow_exact_matches=False,
                      direction="backward").sort_values("_pos")
    return m.s.fillna(0).values, m.c.fillna(0).values


def box_group(box) -> pd.Series:
    b = pd.to_numeric(box, errors="coerce")
    return pd.Series(np.where(b <= 3, "in", np.where(b <= 5, "mid", "out")), index=getattr(box, "index", None)).where(b.notna())


def reliable_features(df: pd.DataFrame) -> pd.DataFrame:
    first, _ = pir_positions(df.get("pir", pd.Series(np.nan, index=df.index)))
    out = df.assign(_early=(first - 1) / (df.field.astype(float) - 1).clip(lower=1),
                    _srank=df.groupby("race_id").split.rank(method="min"))
    out["_missed"] = ((out._srank - out.map_speed_rank) >= 3).astype(float).where(out._srank.notna() & out.map_speed_rank.notna())
    out["split_sd10"] = _prev_rolling(out, "own_split_rating", 10, "std")
    out["split_worst5"] = _prev_rolling(out, "own_split_rating", 5, "min", 2)
    out["missed_rate10"] = _prev_rolling(out, "_missed", 10, "mean", 2)
    out["early_sd10"] = _prev_rolling(out, "_early", 10, "std")
    return out.drop(columns=["_early", "_srank", "_missed"])


def box_pref_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.assign(_bg=box_group(df.box))
    for col, name in (("own_time_rating", "box_pref_time"), ("own_split_rating", "box_pref_split")):
        s_all, c_all = _prev_sum_count(out, ["dog"], col)
        s_g, c_g = _prev_sum_count(out, ["dog", "_bg"], col)
        mean_all = np.where(c_all > 0, s_all / np.maximum(c_all, 1), np.nan)
        # the group's mean shrunk toward the dog's overall mean by SHRINK pseudo-runs, minus the overall mean
        shrunk = (s_g + SHRINK * mean_all) / (c_g + SHRINK)
        out[name] = np.where(c_all > 0, shrunk - mean_all, np.nan)
        if col == "own_time_rating":
            out["box_runs_here"] = c_g
    # inside minus outside: each side's shrunk mean, from the dog's runs on earlier days from that side
    for side in ("in", "out"):
        sub = out.assign(_v=out.own_time_rating.where(out._bg == side))
        s, c = _prev_sum_count(sub, ["dog"], "_v")
        s_all, c_all = _prev_sum_count(out, ["dog"], "own_time_rating")
        mean_all = np.where(c_all > 0, s_all / np.maximum(c_all, 1), np.nan)
        out[f"_{side}"] = (s + SHRINK * mean_all) / (c + SHRINK)
    sign = np.where(out._bg == "in", 1.0, np.where(out._bg == "out", -1.0, 0.0))
    out["inside_vs_out"] = (out._in - out._out) * sign
    out.loc[out._bg.isna(), BOXPREF] = np.nan                       # no box, no preference to read
    return out.drop(columns=["_bg", "_in", "_out"])


def main(d, label):
    df, num, rel, bsp_note = W.build(d)
    if "is_best_bet" not in df and "isBestBet" in df:
        df["is_best_bet"] = df.isBestBet
    df, fpv, _ = PT.preview_features(df)
    ftip = []
    if os.environ.get("RACES_DIR") and os.path.isdir(os.environ["RACES_DIR"]):
        from greyhound.races import load_races, tip_features
        df, ftip = tip_features(df, load_races(os.environ["RACES_DIR"]))
    df = box_pref_features(reliable_features(df)).copy()
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
    fills = ", ".join(f"{c} {df[c].notna().mean():.0%}" for c in RELIABLE + BOXPREF)
    print(f"# {label}: round 11, reliable beginners and box preference\n\n{bsp_note}\nfilled: {fills}\n"
          f"scored: {te[hb].race_id.nunique():,} races, BSP {bsp_all:.4f}\n")
    print("| row | features | rounds | early-stopping log loss | scored log loss | gap to BSP | 1st half | 2nd half |")
    print("|---|---|---|---|---|---|---|---|")
    base = num + fpv + ftip
    rows = [("H0 F2 (D1 + preview + tips)", base, rel),
            ("H1 + reliable beginners", base + RELIABLE, rel + ["split_sd10", "missed_rate10"]),
            ("H2 + box preference", base + BOXPREF, rel + ["box_pref_time", "box_pref_split"]),
            ("H3 + both", base + RELIABLE + BOXPREF, rel + ["split_sd10", "missed_rate10", "box_pref_time", "box_pref_split"])]
    preds = {}
    for name, cols, rl in rows:
        Xf, Xe, Xt = T.features(fp, cols, rl), T.features(es, cols, rl), T.features(te, cols, rl)
        bst, k, _ = R3.fit_weighted(Xf, fp.p_mkt.values.astype(float), fp.race_id, Xe, es.won.values, es.race_id.values,
                                    recency, rounds=6000)
        pe = V1.race_softmax(bst.predict(Xe, num_iteration=k, raw_score=True), es.race_id.values)
        pt = V1.race_softmax(bst.predict(Xt, num_iteration=k, raw_score=True), te.race_id.values)
        preds[name[:2]] = pt
        le = V1.ll(pe[hb_es], es.won.values[hb_es])
        l, l1, l2 = V1.ll(pt[hb], w_te[hb]), V1.ll(pt[hb & h], w_te[hb & h]), V1.ll(pt[hb & ~h], w_te[hb & ~h])
        print(f"| {name} | {Xf.shape[1]} | {k} | {le:.4f} | {l:.4f} | {l - bsp_all:+.4f} | {l1 - b1:+.4f} | {l2 - b2:+.4f} |")
        imp = pd.Series(bst.feature_importance("gain"), index=Xf.columns)
        new = imp[[c for c in imp.index if c.split("_rel")[0] in RELIABLE + BOXPREF]]
        if len(new):
            print(f"  new inputs' share of splits {new.sum() / imp.sum():.1%}: "
                  + ", ".join(f"{i} {v / imp.sum():.1%}" for i, v in new.sort_values(ascending=False).items()))
    t = te[hb].assign(h0=preds["H0"][hb], h3=preds["H3"][hb])
    fast = t.map_speed_rank == 1
    sd_hi = t.split_sd10 >= t.split_sd10.quantile(0.75)
    sd_lo = t.split_sd10 <= t.split_sd10.quantile(0.25)
    pref = t.box_pref_time.fillna(0)
    groups = [("fastest early, reliable beginner (steadiest quarter)", fast & sd_lo),
              ("fastest early, erratic beginner (most erratic quarter)", fast & sd_hi),
              ("missed the start in 30%+ of its last 10", t.missed_rate10 >= 0.3),
              ("drawn in the kind of box it races best from (top quarter)", pref >= pref.quantile(0.75)),
              ("drawn in the kind of box it races worst from (bottom quarter)", pref <= pref.quantile(0.25)),
              ("inside dog drawn inside", t.inside_vs_out >= t.inside_vs_out.quantile(0.9)),
              ("inside dog drawn outside / outside dog drawn inside", t.inside_vs_out <= t.inside_vs_out.quantile(0.1))]
    print("\n| dogs (scored quarter, races with BSP) | runners | wins | win % | H0 expected | A/E vs H0 | A/E vs H3 | A/E vs BSP | A/E vs GRV's SP |")
    print("|---|---|---|---|---|---|---|---|---|")
    for name, m in groups:
        g = t[m]
        if not len(g):
            continue
        w = g.won.sum()
        print(f"| {name} | {len(g):,} | {int(w):,} | {w / len(g):.1%} | {g.h0.sum():,.0f} | {w / g.h0.sum():.3f} | "
              f"{w / g.h3.sum():.3f} | {w / g.p_bsp.sum():.3f} | {w / g.p_sp.sum():.3f} |")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 11")
