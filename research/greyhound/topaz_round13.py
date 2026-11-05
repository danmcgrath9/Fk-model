"""Round 13: the drift (5 Nov 2026, founder, on Shepparton R2: "So Hot So Swifty $3.20 to $19 and runs last by 100
lengths ... our model is fkn no where").

    python research/greyhound/topaz_round13.py DIR LABEL     (BETFAIR_DIR, RACES_DIR as before; results only)

A dog whose price blows out before the off is the market saying something no form guide holds (a vet, a kennel word, a
bad trial). Our model cannot see it, and the 1.3x rule would back the drifter BECAUSE the price drifted past its
take-at. Betfair's free files hold, for every runner, the shortest and longest price matched before the off; with BSP
that measures how far each dog drifted or firmed:
  drift = BSP / the shortest pre-play price matched     (1 = never drifted; 3 = BSP three times its shortest price)
  firm  = the longest pre-play price matched / BSP      (1 = never longer; 3 = it was three times BSP at some point)

PART 1, no model, every race since 2020 with BSP on every runner: A/E at BSP and at GRV's SP and flat ROI at BSP (8%
commission), by drift band and by firm band, in two halves. Is the drift fully priced by BSP, and by GRV's SP?

PART 2, our model (round 8's F2, standard split, scored on the last quarter): A/E against our model by drift band
(does our model over-price the drifters?), then the 1.3x rule at GRV's SP (Test 21's headline: our price $2-$15, Kelly
x75 cap 4) split by the dog's drift, both halves: do the rule's profits come from steady dogs and its losses from
drifters? The drift is only known as the off approaches, so a guard built on it is a rule for bets struck late, or for a
live price checked against the open; that is the founder's TAB-open case.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_preview_test as PT   # noqa: E402
import topaz_round12 as R12       # noqa: E402
import topaz_round3 as R3         # noqa: E402
import topaz_round9 as R9         # noqa: E402
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402

MIN, MAX = "WIN_PREPLAY_MIN_PRICE_TAKEN", "WIN_PREPLAY_MAX_PRICE_TAKEN"
DRIFT_BANDS = [(0, 1.1), (1.1, 1.3), (1.3, 1.6), (1.6, 2.2), (2.2, 3.5), (3.5, np.inf)]
NAMES = ["under 1.1x", "1.1-1.3x", "1.3-1.6x", "1.6-2.2x", "2.2-3.5x", "3.5x+"]


def drift_columns(df: pd.DataFrame) -> pd.DataFrame:
    """drift and firm as above; NaN where Betfair matched nothing before the off, or BSP is missing."""
    lo, hi = df[MIN].where(df[MIN] > 1), df[MAX].where(df[MAX] > 1)
    df["drift"] = df.bsp / lo
    df["firm"] = hi / df.bsp
    return df


def band(x: pd.Series) -> pd.Series:
    """The band name for each value (NaN stays NaN)."""
    out = pd.Series(np.nan, index=x.index, dtype=object)
    for (lo, hi), name in zip(DRIFT_BANDS, NAMES):
        out[(x >= lo) & (x < hi)] = name
    return out


def main(d, label):
    df, num, rel, bsp_note = W.build(d)
    if "is_best_bet" not in df and "isBestBet" in df:
        df["is_best_bet"] = df.isBestBet
    df, fpv, _ = PT.preview_features(df)
    ftip = []
    if os.environ.get("RACES_DIR") and os.path.isdir(os.environ["RACES_DIR"]):
        from greyhound.races import load_races, tip_features
        df, ftip = tip_features(df, load_races(os.environ["RACES_DIR"]))
    print(f"# {label}: round 13, the drift\n\n{bsp_note}\n")
    R12.EXTRA[:] = [MIN, MAX, "WIN_PREPLAY_VOLUME"]
    df, have = R12.add_betfair_extra(df)
    if MIN not in have or MAX not in have:
        print("Betfair's files carry no pre-play min/max price: nothing to test")
        return 1
    df = drift_columns(df).copy()

    a = df[df.p_bsp.notna() & df.p_sp.notna() & df.drift.notna()]
    half = (a.date < a.date.quantile(0.5)).values
    print(f"## Part 1: {a.race_id.nunique():,} races from {a.date.min():%Y-%m-%d} with BSP and a pre-play price on the dog, "
          f"halves split at {a.date.quantile(0.5):%Y-%m-%d}; drift filled on {df.drift[df.p_bsp.notna()].notna().mean():.0%} "
          f"of BSP runners\n")
    for col, what in (("drift", "BSP over the shortest price matched before the off (drifted)"),
                      ("firm", "the longest price matched before the off over BSP (firmed)")):
        b = band(a[col])
        print(f"| {what} | runners | win % | A/E at BSP (1st / 2nd) | flat ROI at BSP, 8% comm (1st / 2nd) | "
              "A/E at GRV's SP (1st / 2nd) |\n|---|---|---|---|---|---|")
        for name in NAMES:
            m = (b == name).values
            if m.sum() < 300:
                continue
            r1, r2 = R12.tale_row(a[m & half]), R12.tale_row(a[m & ~half])
            n, w = r1["n"] + r2["n"], r1["w"] + r2["w"]
            print(f"| {name} | {n:,} | {w / n:.1%} | {r1['ae_bsp']:.3f} / {r2['ae_bsp']:.3f} | "
                  f"{r1['roi_bsp']:+.1%} / {r2['roi_bsp']:+.1%} | {r1['ae_sp']:.3f} / {r2['ae_sp']:.3f} |")
        print()

    # PART 2: our model
    cols = num + fpv + ftip
    q75 = df.date.quantile(0.75)
    es_start = q75 - min(pd.Timedelta(days=183), (q75 - df.date.min()) / 4)
    pre, te = df[df.date < q75], df[df.date >= q75].copy()
    fp, es = pre[pre.date < es_start], pre[pre.date >= es_start].copy()
    recency = 0.5 ** (((es_start - fp.date).dt.days / 365.25).values / 3.0)
    Xf, Xe, Xt = T.features(fp, cols, rel), T.features(es, cols, rel), T.features(te, cols, rel)
    bst, k, _ = R3.fit_weighted(Xf, fp.p_mkt.values.astype(float), fp.race_id, Xe, es.won.values, es.race_id.values,
                                recency, rounds=6000)
    es["p_a"] = V1.race_softmax(bst.predict(Xe, num_iteration=k, raw_score=True), es.race_id.values)
    te["p_a"] = V1.race_softmax(bst.predict(Xt, num_iteration=k, raw_score=True), te.race_id.values)
    t = te[te.p_bsp.notna()].copy()
    t["dband"] = band(t.drift)
    print(f"## Part 2: our model (F2, {k} rounds), {t.race_id.nunique():,} scored races with BSP from {t.date.min():%Y-%m-%d}\n")
    print("| drift | runners | wins | A/E vs our model | A/E vs BSP | A/E vs GRV's SP |\n|---|---|---|---|---|---|")
    for name in NAMES + [np.nan]:
        m = (t.dband == name) if isinstance(name, str) else t.dband.isna()
        g = t[m.values]
        if len(g) < 200:
            continue
        w = g.won.sum()
        print(f"| {name if isinstance(name, str) else 'nothing matched before the off'} | {len(g):,} | {int(w):,} | "
              f"{w / g.p_a.sum():.3f} | {w / g.p_bsp.sum():.3f} | {w / g.p_sp.sum():.3f} |")

    # the 1.3x rule at GRV's SP, split by drift
    e_ok, t_ok = es.p_sp.notna().values, te.p_sp.notna().values
    wts, _ = V1.blend(["p_a", "p_sp"], es[e_ok])
    t2 = te[t_ok].copy()
    t2["p_blend"] = V1.blend(["p_a", "p_sp"], t2, wts)[1]
    t2["dband"] = band(t2.drift)
    h = (t2.date < t2.date.quantile(0.5)).values
    price = t2.start_price.astype(float).values
    m, o, u = R9.horse_bets(t2, t2.p_blend.values, t2.p_sp.values, price, 0.0, 1.3, (2, 15))
    print(f"\n## The 1.3x rule at GRV's SP (our price $2-$15, Kelly x75 cap 4; blend {wts[0]:.2f} / {wts[1]:.2f}), "
          f"split by the dog's drift on Betfair\n")
    print("| drift | half | bets | winners | A/E | flat ROI | Kelly ROI | units won |\n|---|---|---|---|---|---|---|---|")
    groups = [(n, (t2.dband == n).values) for n in NAMES] + [("no Betfair pre-play price", t2.dband.isna().values),
                                                             ("all bets", np.ones(len(t2), bool))]
    for name, g in groups:
        for hn, hm in (("1st", h), ("2nd", ~h)):
            sel = m & g & hm
            r = R9.summary(t2, sel, o, u, price)
            if r["n"]:
                print(f"| {name} | {hn} | {r['n']:,} | {r['w']:,} | {r['ae']:.3f} | {r['flat']:+.1%} | {r['kroi']:+.1%} | "
                      f"{r['kunits']:+,.0f} |")
    # the guard: drop every bet that drifted past each cap
    print("\n| guard: no bet when drift is at least | half | bets | winners | A/E | flat ROI | Kelly ROI | units won |\n"
          "|---|---|---|---|---|---|---|---|")
    for cap in (1.3, 1.6, 2.2, 3.5, np.inf):
        keep = ~(t2.drift >= cap).values
        for hn, hm in (("1st", h), ("2nd", ~h)):
            r = R9.summary(t2, m & keep & hm, o, u, price)
            if r["n"]:
                cname = "no guard" if not np.isfinite(cap) else f"{cap:g}x"
                print(f"| {cname} | {hn} | {r['n']:,} | {r['w']:,} | {r['ae']:.3f} | {r['flat']:+.1%} | {r['kroi']:+.1%} | "
                      f"{r['kunits']:+,.0f} |")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 13")
