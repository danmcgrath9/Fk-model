"""Round 10: held out last start by a quicker leader, the fastest early dog today (5 Nov 2026, founder: "What about
from last race, if it didn't lead or got held out because there was a faster leader in that race, but this race now
he's the fastest?").

    python research/greyhound/topaz_round10.py DIR LABEL     (BETFAIR_DIR, RACES_DIR as before; results only)

The model already has each dog's first-split RATING (its own times against par) and today's rank on it, which do not
depend on who it ran against. What depends on the rivals is where it was early: a dog that is quick out but met a
quicker one shows a poor early position and a low led-rate, and the model may read that as a slow beginner. New
inputs, each from the dog's previous run (strictly an earlier day, so nothing from today's race):
  prev_led           led at the first point last start (its in-running)
  prev_split_rank    its rank on actual first split in that race (1 = quickest out)
  prev_split_gap     seconds behind the quickest first split in that race (0 when it was the quickest)
  prev_speed_rank    its rank on the pre-race early-speed rating in that race
  speed_rank_up      prev_speed_rank minus today's rank (positive: more favoured early today than last time)
  held_out           did not lead last start, second quickest out or within 0.10s of the quickest, and the fastest
                     early dog on today's rating
Rows (as round 8's F2: D1 + preview + tips, 6,000-round cap, recency weighted, early stopped, same 22,841 races):
  G0 F2;  G1 F2 + the inputs above.
Then, for the dogs held out last start and fastest early today, actual wins against our model's expected (each row),
BSP's and GRV's SP's, the founder's question in one line.
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

HELD = ["prev_led", "prev_split_rank", "prev_split_gap", "prev_speed_rank", "speed_rank_up", "held_out"]


def held_out_features(df: pd.DataFrame) -> pd.DataFrame:
    """The six inputs above, each from the dog's previous day it raced (T.prev_day_values: strictly earlier)."""
    first, _ = pir_positions(df.get("pir", pd.Series(np.nan, index=df.index)))
    g = df.groupby("race_id").split
    out = df.assign(_led=(first == 1).astype(float).where(first.notna()),
                    _srank=g.rank(method="min"), _sgap=df.split - g.transform("min"),
                    _rank=df.map_speed_rank)
    for src, dst in (("_led", "prev_led"), ("_srank", "prev_split_rank"), ("_sgap", "prev_split_gap"),
                     ("_rank", "prev_speed_rank")):
        out[dst] = T.prev_day_values(out, ["dog"], src)
    out["speed_rank_up"] = out.prev_speed_rank - out.map_speed_rank
    held = (out.prev_led == 0) & ((out.prev_split_rank == 2) | (out.prev_split_gap <= 0.10)) & (out.map_speed_rank == 1)
    out["held_out"] = held.astype(float).where(out.prev_led.notna() & out.map_speed_rank.notna())
    return out.drop(columns=["_led", "_srank", "_sgap", "_rank"])


def main(d, label):
    df, num, rel, bsp_note = W.build(d)
    if "is_best_bet" not in df and "isBestBet" in df:
        df["is_best_bet"] = df.isBestBet
    df, fpv, _ = PT.preview_features(df)
    ftip = []
    if os.environ.get("RACES_DIR") and os.path.isdir(os.environ["RACES_DIR"]):
        from greyhound.races import load_races, tip_features
        df, ftip = tip_features(df, load_races(os.environ["RACES_DIR"]))
    df = held_out_features(df).copy()
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
    held = df.held_out == 1
    print(f"# {label}: round 10, held out last start, fastest early today\n\n{bsp_note}\n"
          f"held_out on {held.mean():.1%} of runners ({int(held.sum()):,}); prev_led filled on {df.prev_led.notna().mean():.0%}, "
          f"prev_split_gap on {df.prev_split_gap.notna().mean():.0%}; scored: {te[hb].race_id.nunique():,} races, BSP {bsp_all:.4f}\n")
    print("| row | features | rounds | early-stopping log loss | scored log loss | gap to BSP | 1st half | 2nd half |")
    print("|---|---|---|---|---|---|---|---|")
    base = num + fpv + ftip
    preds = {}
    for name, cols, rl in (("G0 F2 (D1 + preview + tips)", base, rel),
                           ("G1 + held out last start", base + HELD, rel + ["prev_split_gap", "speed_rank_up"])):
        Xf, Xe, Xt = T.features(fp, cols, rl), T.features(es, cols, rl), T.features(te, cols, rl)
        bst, k, _ = R3.fit_weighted(Xf, fp.p_mkt.values.astype(float), fp.race_id, Xe, es.won.values, es.race_id.values,
                                    recency, rounds=6000)
        pe = V1.race_softmax(bst.predict(Xe, num_iteration=k, raw_score=True), es.race_id.values)
        pt = V1.race_softmax(bst.predict(Xt, num_iteration=k, raw_score=True), te.race_id.values)
        preds[name] = pt
        le = V1.ll(pe[hb_es], es.won.values[hb_es])
        l, l1, l2 = V1.ll(pt[hb], w_te[hb]), V1.ll(pt[hb & h], w_te[hb & h]), V1.ll(pt[hb & ~h], w_te[hb & ~h])
        print(f"| {name} | {Xf.shape[1]} | {k} | {le:.4f} | {l:.4f} | {l - bsp_all:+.4f} | {l1 - b1:+.4f} | {l2 - b2:+.4f} |")
        imp = pd.Series(bst.feature_importance("gain"), index=Xf.columns)
        new = imp[[c for c in imp.index if c.split("_rel")[0] in HELD]]
        if len(new):
            print(f"  new inputs' share of splits {new.sum() / imp.sum():.1%}: "
                  + ", ".join(f"{i} {v / imp.sum():.1%}" for i, v in new.sort_values(ascending=False).items()))
    print("\n| dogs (scored quarter, races with BSP) | runners | wins | win % | G0 expected | A/E vs G0 | A/E vs G1 | A/E vs BSP | A/E vs GRV's SP |")
    print("|---|---|---|---|---|---|---|---|---|")
    t = te[hb].assign(g0=preds["G0 F2 (D1 + preview + tips)"][hb], g1=preds["G1 + held out last start"][hb])
    for name, m in (("held out last start, fastest early today", t.held_out == 1),
                    ("  ... and drawn box 1-2", (t.held_out == 1) & (t.box <= 2)),
                    ("fastest early today, led last start", (t.map_speed_rank == 1) & (t.prev_led == 1)),
                    ("fastest early today, did not lead last start", (t.map_speed_rank == 1) & (t.prev_led == 0)),
                    ("all other runners", ~(t.map_speed_rank == 1))):
        g = t[m]
        if not len(g):
            continue
        w = g.won.sum()
        print(f"| {name} | {len(g):,} | {int(w):,} | {w / len(g):.1%} | {g.g0.sum():,.0f} | {w / g.g0.sum():.3f} | "
              f"{w / g.g1.sum():.3f} | {w / g.p_bsp.sum():.3f} | {w / g.p_sp.sum():.3f} |")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 10")
