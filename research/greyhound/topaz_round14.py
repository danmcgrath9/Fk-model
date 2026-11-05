"""Round 14: predict the leader, then price with it (5 Nov 2026, founder, on Lemonade Lass: "Was it always going to
lead").

    python research/greyhound/topaz_round14.py DIR LABEL     (BETFAIR_DIR, RACES_DIR as before; results only)

Test 21: the dog that leads at the first point wins 52.7%, and the fastest early dog on our past-splits rating leads
only 30.3%. So the leader is worth predicting on its own. A LEAD MODEL: the same LightGBM race softmax and the same
pre-race inputs as the win model, but the label is "led at the first point" (from GRV's in-running, races with exactly
one leader). Scored on the last quarter against two plain rules: the fastest early dog on past splits, and the dog
that has led most often.

Then the win model with the lead model's chance as an input (STACKED). The training rows get their lead chance OUT OF
FOLD (the lead model fitted on the other two date blocks of the fitting set), the early-stopping and scored rows
from a lead model fitted on the whole fitting set, so no row's own result reaches its own input.
  G0  F2 (D1 + preview + tips), as rounds 10-13
  G1  + the lead chance and its rank in the race
  G2  G1 + the trainer's runners (Test 24: our model over-prices a trainer's second dog): how many the trainer has
      in the race, this dog's rank among them on the time rating, and whether it is the stable's top-rated dog
Each row: rounds, early-stopping and scored log loss, gap to BSP, both halves. Then A/E by lead chance against G0, G1,
BSP and GRV's SP: does the market price the likely leader, and does our model now?
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

LEAD = ["p_lead", "lead_rank"]
STABLE = ["trainer_runners", "trainer_rank", "stable_elect"]
FOLDS = 3


def lead_label(df: pd.DataFrame) -> pd.DataFrame:
    """led = 1 for the dog first at the first point; one_leader marks races with exactly one (ties and gaps out)."""
    first, _ = pir_positions(df.get("pir", pd.Series(np.nan, index=df.index)))
    df["led"] = (first == 1).astype(float).where(first.notna())
    n = df.led.groupby(df.race_id).transform("sum")
    known = df.led.notna().groupby(df.race_id).transform("all")
    df["one_leader"] = (n == 1) & known
    return df


def stable_features(df: pd.DataFrame) -> pd.DataFrame:
    """The trainer's runners in this race, and this dog's place among them on the pre-race time rating."""
    tr = df.trainer_id if "trainer_id" in df else pd.Series(np.nan, index=df.index)
    key = [df.race_id, tr.fillna(-1)]
    rating = df.time_rating_mean5 if "time_rating_mean5" in df else pd.Series(np.nan, index=df.index)
    df["trainer_runners"] = df.groupby(key).race_id.transform("size").where(tr.notna())
    df["trainer_rank"] = rating.groupby(key).rank(ascending=False, method="min").where(tr.notna())
    df["stable_elect"] = ((df.trainer_rank == 1) & (df.trainer_runners >= 2)).astype(float).where(tr.notna())
    return df


def lead_rank(p: pd.Series, race: pd.Series) -> pd.Series:
    return p.groupby(race.values).rank(ascending=False, method="min")


def fit_lead(X, d, Xe, e, recency):
    """The lead model on the rows of d with one leader, early-stopped on e's one-leader races."""
    m, me = d.one_leader.values, e.one_leader.values
    bst, k, _ = R3.fit_weighted(X[m], d.led.values[m].astype(float), d.race_id[m], Xe[me], e.led.values[me],
                                e.race_id.values[me], recency[m], rounds=4000)
    return bst, k


def predict(bst, k, X, race):
    return V1.race_softmax(bst.predict(X, num_iteration=k, raw_score=True), np.asarray(race))


def main(d, label):
    df, num, rel, bsp_note = W.build(d)
    if "is_best_bet" not in df and "isBestBet" in df:
        df["is_best_bet"] = df.isBestBet
    df, fpv, _ = PT.preview_features(df)
    ftip = []
    if os.environ.get("RACES_DIR") and os.path.isdir(os.environ["RACES_DIR"]):
        from greyhound.races import load_races, tip_features
        df, ftip = tip_features(df, load_races(os.environ["RACES_DIR"]))
    df = stable_features(lead_label(df)).copy()
    cols = num + fpv + ftip
    q75 = df.date.quantile(0.75)
    es_start = q75 - min(pd.Timedelta(days=183), (q75 - df.date.min()) / 4)
    pre, te = df[df.date < q75], df[df.date >= q75].copy()
    fp, es = pre[pre.date < es_start].copy(), pre[pre.date >= es_start].copy()
    recency = 0.5 ** (((es_start - fp.date).dt.days / 365.25).values / 3.0)
    Xf, Xe, Xt = T.features(fp, cols, rel), T.features(es, cols, rel), T.features(te, cols, rel)
    print(f"# {label}: round 14, the lead model\n\n{bsp_note}\nraces with one leader: {df.one_leader.groupby(df.race_id).first().mean():.0%}; "
          f"fitting {fp.race_id.nunique():,} races to {es_start:%Y-%m-%d}, early stopping to {q75:%Y-%m-%d}, scored after\n")

    # the lead model: out of fold on the fitting set (date blocks), whole-set fit for the rest
    fp["p_lead"] = np.nan
    blocks = pd.qcut(fp.date.rank(method="dense"), FOLDS, labels=False).values      # whole days, so no race is split
    for b in range(FOLDS):
        tr_m = blocks != b
        bst, k = fit_lead(Xf[tr_m], fp[tr_m], Xe, es, recency[tr_m])
        fp.loc[~tr_m, "p_lead"] = predict(bst, k, Xf[~tr_m], fp.race_id[~tr_m])
        print(f"  lead model, fold {b + 1} of {FOLDS}: {k} rounds")
    bst_l, k_l = fit_lead(Xf, fp, Xe, es, recency)
    es["p_lead"], te["p_lead"] = predict(bst_l, k_l, Xe, es.race_id), predict(bst_l, k_l, Xt, te.race_id)
    for x in (fp, es, te):
        x["lead_rank"] = lead_rank(x.p_lead, x.race_id)

    t1 = te[te.one_leader]
    ll_lead = V1.ll(t1.p_lead.values, t1.led.values)
    fair = V1.ll((1 / t1.field).values, t1.led.values)
    print(f"\nlead model: {k_l} rounds; on the scored quarter's {t1.race_id.nunique():,} one-leader races, log loss "
          f"{ll_lead:.4f} against {fair:.4f} for an equal chance each\n")
    print("| rule | its pick leads | its pick wins |\n|---|---|---|")
    for name, pick in (("the lead model's top pick", t1.lead_rank == 1), ("fastest early on past splits", t1.map_speed_rank == 1),
                       ("led most often (last 10)", t1.style_led_rate.groupby(t1.race_id).rank(ascending=False, method="min") == 1)):
        g = t1[pick.values]
        g = g[~g.race_id.duplicated(keep=False)]            # ties in the plain rules: no single pick, left out
        print(f"| {name} | {g.led.mean():.1%} of {len(g):,} races | {g.won.mean():.1%} |")
    print("\n| lead chance | runners | led | lead model expected | won | win % |\n|---|---|---|---|---|---|")
    for lo, hi in ((0, 0.1), (0.1, 0.2), (0.2, 0.35), (0.35, 0.5), (0.5, 0.7), (0.7, 1.01)):
        g = t1[(t1.p_lead >= lo) & (t1.p_lead < hi)]
        if len(g) >= 100:
            print(f"| {lo:.0%}-{min(hi, 1):.0%} | {len(g):,} | {int(g.led.sum()):,} | {g.p_lead.sum():,.0f} | "
                  f"{int(g.won.sum()):,} | {g.won.mean():.1%} |")

    # the win model with the lead chance stacked in
    hb, hb_es = te.p_bsp.notna().values, es.p_bsp.notna().values
    h = (te.date < te.date.quantile(0.5)).values
    w_te = te.won.values
    bsp_all = V1.ll(te.p_bsp.values[hb], w_te[hb])
    b1, b2 = V1.ll(te.p_bsp.values[hb & h], w_te[hb & h]), V1.ll(te.p_bsp.values[hb & ~h], w_te[hb & ~h])
    print(f"\n## The win model, {te[hb].race_id.nunique():,} scored races with BSP, BSP {bsp_all:.4f}\n")
    print("| row | inputs | rounds | early-stopping log loss | scored log loss | gap to BSP | 1st half | 2nd half |")
    print("|---|---|---|---|---|---|---|---|")
    base = num + fpv + ftip
    preds = {}
    for name, extra, rl in (("G0 F2 (D1 + preview + tips)", [], []),
                            ("G1 + the lead chance", LEAD, ["p_lead"]),
                            ("G2 G1 + the trainer's runners", LEAD + STABLE, ["p_lead"])):
        c = base + extra
        Xf2, Xe2, Xt2 = T.features(fp, c, rel + rl), T.features(es, c, rel + rl), T.features(te, c, rel + rl)
        bst, k, _ = R3.fit_weighted(Xf2, fp.p_mkt.values.astype(float), fp.race_id, Xe2, es.won.values, es.race_id.values,
                                    recency, rounds=6000)
        pe, pt = predict(bst, k, Xe2, es.race_id), predict(bst, k, Xt2, te.race_id)
        preds[name] = pt
        le = V1.ll(pe[hb_es], es.won.values[hb_es])
        l, l1, l2 = V1.ll(pt[hb], w_te[hb]), V1.ll(pt[hb & h], w_te[hb & h]), V1.ll(pt[hb & ~h], w_te[hb & ~h])
        print(f"| {name} | {Xf2.shape[1]} | {k} | {le:.4f} | {l:.4f} | {l - bsp_all:+.4f} | {l1 - b1:+.4f} | {l2 - b2:+.4f} |")
        if extra:
            imp = pd.Series(bst.feature_importance("gain"), index=Xf2.columns)
            new = imp[[i for i in imp.index if i.split("_rel")[0] in extra]]
            print(f"  new inputs' share of splits {new.sum() / imp.sum():.1%}: "
                  + ", ".join(f"{i} {v / imp.sum():.1%}" for i, v in new.sort_values(ascending=False).items()))

    t = te[hb].assign(g0=preds["G0 F2 (D1 + preview + tips)"][hb], g1=preds["G1 + the lead chance"][hb],
                      g2=preds["G2 G1 + the trainer's runners"][hb])
    print("\n| dogs (scored quarter, races with BSP) | runners | wins | win % | A/E vs G0 | A/E vs G1 | A/E vs G2 | "
          "A/E vs BSP | A/E vs GRV's SP |\n|---|---|---|---|---|---|---|---|---|")
    groups = [("lead chance 50%+", t.p_lead >= 0.5), ("lead chance 35-50%", (t.p_lead >= 0.35) & (t.p_lead < 0.5)),
              ("lead chance 20-35%", (t.p_lead >= 0.2) & (t.p_lead < 0.35)), ("lead chance under 20%", t.p_lead < 0.2),
              ("lead model's top pick, box 1", (t.lead_rank == 1) & (t.box == 1)),
              ("lead model's top pick, boxes 2-8", (t.lead_rank == 1) & (t.box > 1)),
              ("trainer's second runner or lower", t.trainer_rank >= 2), ("the stable's elect", t.stable_elect == 1)]
    for name, m in groups:
        g = t[m.values]
        if len(g) < 200:
            continue
        w = g.won.sum()
        print(f"| {name} | {len(g):,} | {int(w):,} | {w / len(g):.1%} | {w / g.g0.sum():.3f} | {w / g.g1.sum():.3f} | "
              f"{w / g.g2.sum():.3f} | {w / g.p_bsp.sum():.3f} | {w / g.p_sp.sum():.3f} |")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 14")
