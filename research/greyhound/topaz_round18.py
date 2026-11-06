"""Round 18: Isolynx tracking data (6 Nov 2026; GRV switched the key on for Isolynx that afternoon, founder: "let's
fucking go").

    python research/greyhound/topaz_round18.py DIR LABEL    (BETFAIR_DIR, RACES_DIR, ISOLYNX_DIR; WALK_GRV_RATING /
                                                             WALK_RELIABLE / WALK_DRIFT as the weekly train sets them)

The tracking system times every run at The Meadows, Sandown, Healesville, Traralgon (and Cranbourne): the jump, every
50 m, top speed, the distance off the rail. topaz_round6.isolynx_features turns each dog's EARLIER tracked runs into
par-relative ratings by track and distance: jump time, time to 50 m and 100 m, last 100 m, rail distance, speed at
100 m, top speed, each as the last run and the mean of the last 3, plus how many tracked runs it has.

The production inputs, the standard split, the lead chance forward-chained by half-year as the weekly train fits it:
  F0  the production model, no Isolynx anywhere (the lead model without it too)
  F1  + Isolynx in the win model only
  F2  + Isolynx in the lead model as well
  F3  F2 + the checks: whether the dog was checked in its last tracked run (a sudden dip in speed or places lost in one
      50 m section, greyhound.isolynx.trouble), how deep the dip, how many places, and how often in its last 5
Then the founder's question: does a dog checked last time win more than our price, BSP or GRV's SP says?
Scored on the last quarter, both halves: the lead model's hit rate (its top pick led), log loss and gap to BSP
(overall, at the tracked tracks and the rest), and the 1.3x rule at GRV's SP with the drift guard beside it.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round3 as R3         # noqa: E402
import topaz_round9 as R9         # noqa: E402
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402
from greyhound.isolynx import CHECK_DIP, CHECK_LOST   # noqa: E402

TRACKED = "MEADOWS|SANDOWN|HEALESVILLE|TRARALGON|CRANBOURNE"
DRIFT_CAP = 1.3


def split_inputs(num, rel):
    """(inputs without Isolynx, with), each as (num, rel)."""
    iso = [c for c in num if c.startswith("iso_")]
    return ([c for c in num if c not in iso], [c for c in rel if not c.startswith("iso_")]), (list(num), list(rel)), iso


CHECK_COLS = ["chk_last", "chk_dip_last", "chk_lost_last", "chk_rate5"]


def check_features(df: pd.DataFrame, iso_dir: str):
    """From each dog's EARLIER tracked runs (end of the previous day): was it checked in its last tracked run, how deep
    the speed dip and how many places it lost there, and the share of its last 5 tracked runs with a check
    (greyhound.isolynx.trouble). Returns (df, columns, share of tracked runs checked)."""
    from greyhound.isolynx import table
    from greyhound.ratings import _asof
    t = table(iso_dir)
    if t is None or not len(t) or "checked" not in t:
        return df, [], np.nan
    t = t.dropna(subset=["date"]).copy()
    t["dog"] = t.dog.astype("Int64").astype(str)
    t = t.sort_values(["dog", "date"])
    t["checked"] = pd.to_numeric(t.checked, errors="coerce")
    t["_rate5"] = t.groupby("dog").checked.rolling(5, min_periods=1).mean().reset_index(level=0, drop=True)
    day = t.groupby(["dog", "date"])[["checked", "dip", "pos_lost", "_rate5"]].last().reset_index()
    for src, dst in zip(["checked", "dip", "pos_lost", "_rate5"], CHECK_COLS):
        df[dst] = _asof(df[["dog", "date"]], day.rename(columns={src: dst}), ["dog"], dst).astype(float)
    return df, list(CHECK_COLS), float(t.checked.mean())


def lead_hits(t: pd.DataFrame, rank_col: str) -> tuple[int, float]:
    """One-leader races, and the share in which the lead model's top pick (rank 1) was the dog that led."""
    r = t[t.one_leader.astype(bool)]
    top = r[r[rank_col] == 1]
    races = r.race_id.nunique()
    return races, (top.groupby("race_id").led.max().sum() / races) if races else np.nan


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    os.environ["WALK_LEAD"] = "no"                      # the lead chance is fitted here, twice
    df, num, rel, note = W.build_full(d)
    print(f"# {label}: round 18, Isolynx tracking\n\n{note}\n")
    (num0, rel0), (num1, rel1), iso = split_inputs(num, rel)
    if not iso:
        print("No Isolynx inputs (ISOLYNX_DIR unset or empty): nothing to test")
        return 1
    df, n0 = W.lead_forward(df, num0, rel0)
    df["p_lead0"], df["lead_rank0"] = df.p_lead, df.lead_rank
    df, n1 = W.lead_forward(df, num1, rel1)
    df["p_lead1"], df["lead_rank1"] = df.p_lead, df.lead_rank
    print(f"{len(iso)} Isolynx inputs; lead models: {n0} fits without Isolynx, {n1} with\n")
    df, chk, chk_share = check_features(df, os.environ.get("ISOLYNX_DIR", ""))
    print(f"Checks (a 50 m section {abs(CHECK_DIP):g} m/s slower than the two either side, or {CHECK_LOST}+ places lost "
          f"in one, between the first and the last 100 m): {chk_share:.0%} of tracked "
          f"runs; a checked-or-not last tracked run known for {df.chk_last.notna().mean():.0%} of runners\n" if chk else
          "Checks: no split detail in the pull\n")

    q75 = df.date.quantile(0.75)
    es_start = q75 - min(pd.Timedelta(days=183), (q75 - df.date.min()) / 4)
    pre, te = df[df.date < q75], df[df.date >= q75].copy()
    fp, es = pre[pre.date < es_start].copy(), pre[pre.date >= es_start].copy()
    recency = 0.5 ** (((es_start - fp.date).dt.days / 365.25).values / 3.0)
    h = (te.date < te.date.quantile(0.5)).values
    tracked = te.track.astype(str).str.upper().str.contains(TRACKED).values
    print(f"Scored quarter: {te.race_id.nunique():,} races from {te.date.min():%Y-%m-%d}, "
          f"{te.race_id[tracked].nunique():,} at the tracked tracks; a tracked run before the race for "
          f"{(te.iso_runs > 0).mean():.0%} of runners ({(te.iso_runs[tracked] > 0).mean():.0%} at the tracked tracks)\n")

    print("| lead model | one-leader races | its top pick led | 1st half | 2nd half | at the tracked tracks |\n"
          "|---|---|---|---|---|---|")
    for name, rc in (("without Isolynx", "lead_rank0"), ("with Isolynx", "lead_rank1")):
        n, a = lead_hits(te, rc)
        _, a1 = lead_hits(te[h], rc)
        _, a2 = lead_hits(te[~h], rc)
        _, at = lead_hits(te[tracked], rc)
        print(f"| {name} | {n:,} | {a:.1%} | {a1:.1%} | {a2:.1%} | {at:.1%} |")

    w = te.won.values
    hb = te.p_bsp.notna().values
    b_all, b1, b2, bt, bo = (V1.ll(te.p_bsp.values[m], w[m]) for m in (hb, hb & h, hb & ~h, hb & tracked, hb & ~tracked))
    print(f"\n{te[hb].race_id.nunique():,} scored races with BSP (BSP {b_all:.4f})\n")
    print("| row | inputs | rounds | log loss | gap to BSP | 1st half | 2nd half | gap, tracked tracks | gap, the rest |\n"
          "|---|---|---|---|---|---|---|---|---|")
    rows = (("F0 the production model, no Isolynx", num0, rel0, "0"),
            ("F1 + Isolynx in the win model", num1, rel1, "0"),
            ("F2 + Isolynx in the lead model too", num1, rel1, "1"))
    if chk:
        rows += (("F3 + the checks", num1 + chk, rel1, "1"),)
    for name, n_, r_, lead in rows:
        for x in (fp, es, te):
            x["p_lead"], x["lead_rank"] = x[f"p_lead{lead}"], x[f"lead_rank{lead}"]
        cols, rels = n_ + ["p_lead", "lead_rank"], r_ + ["p_lead"]
        Xf, Xe, Xt = T.features(fp, cols, rels), T.features(es, cols, rels), T.features(te, cols, rels)
        bst, k, _ = R3.fit_weighted(Xf, fp.p_mkt.values.astype(float), fp.race_id, Xe, es.won.values,
                                    es.race_id.values, recency, rounds=6000)
        col = "p_" + name[:2]
        es[col] = V1.race_softmax(bst.predict(Xe, num_iteration=k, raw_score=True), es.race_id.values)
        te[col] = V1.race_softmax(bst.predict(Xt, num_iteration=k, raw_score=True), te.race_id.values)
        p = te[col].values
        g = [V1.ll(p[m], w[m]) - b for m, b in ((hb, b_all), (hb & h, b1), (hb & ~h, b2), (hb & tracked, bt),
                                               (hb & ~tracked, bo))]
        print(f"| {name} | {len(cols)} | {k} | {V1.ll(p[hb], w[hb]):.4f} | {g[0]:+.4f} | {g[1]:+.4f} | {g[2]:+.4f} | "
              f"{g[3]:+.4f} | {g[4]:+.4f} |")

    if chk:
        # the founder's question: is a dog checked in its last tracked run under-rated, by us or by the market?
        t = te[hb]
        print("\n| last tracked run | runners | wins | A/E vs F2 | A/E vs F3 | A/E vs BSP | A/E vs GRV's SP |\n"
              "|---|---|---|---|---|---|---|")
        for name, m in (("checked", (t.chk_last == 1).values), ("not checked", (t.chk_last == 0).values),
                        ("checked, 3+ places lost", (t.chk_lost_last >= 3).values),
                        ("no tracked run before", t.chk_last.isna().values)):
            if m.sum() < 300:
                continue
            g = t[m]
            wn = g.won.sum()
            print(f"| {name} | {m.sum():,} | {int(wn):,} | {wn / g.p_F2.sum():.3f} | {wn / g.p_F3.sum():.3f} | "
                  f"{wn / g.p_bsp.sum():.3f} | {wn / g.p_sp.sum():.3f} |")

    # the 1.3x rule at GRV's SP
    e_ok, t_ok = es.p_sp.notna().values, te.p_sp.notna().values
    t2 = te[t_ok].copy()
    h2 = (t2.date < t2.date.quantile(0.5)).values
    price = t2.start_price.astype(float).values
    print("\n## The 1.3x rule at GRV's SP (our price $2-$15, Kelly x75 cap 4, no commission)\n")
    print("| row | guard | half | bets | winners | A/E | flat ROI | units staked | Kelly ROI | units won |\n"
          "|---|---|---|---|---|---|---|---|---|---|")
    for name, *_ in rows:
        col = "p_" + name[:2]
        bw, _ = V1.blend([col, "p_sp"], es[e_ok])
        pb = V1.blend([col, "p_sp"], t2, bw)[1]
        m, o, u = R9.horse_bets(t2, pb, t2.p_sp.values, price, 0.0, 1.3, (2, 15))
        guards = [("none", np.ones(len(t2), bool))]
        if "drift" in t2:
            guards.append((f"drift under {DRIFT_CAP:g}x", ~(t2.drift >= DRIFT_CAP).values))
        for gname, keep in guards:
            for hn, hm in (("1st", h2), ("2nd", ~h2), ("all", np.ones(len(t2), bool))):
                r = R9.summary(t2, m & keep & hm, o, u, price)
                if r["n"]:
                    print(f"| {name[:2]} | {gname} | {hn} | {r['n']:,} | {r['w']:,} | {r['ae']:.3f} | {r['flat']:+.1%} | "
                          f"{r['staked']:,.0f} | {r['kroi']:+.1%} | {r['kunits']:+,.0f} |")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 18")
