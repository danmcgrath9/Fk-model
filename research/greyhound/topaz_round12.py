"""Round 12: the old greyhound tales, how to back them, and where our price is closest to Betfair's (5 Nov 2026,
founder: "Keep testing things like I said, the ole greyhound tales on how to back them and how we can get the model
closer, look for data things").

    python research/greyhound/topaz_round12.py DIR LABEL     (BETFAIR_DIR, RACES_DIR as before; results only)

PART 1, THE TALES, no model: every race since 2020 where Betfair priced every runner. Each tale is a rule a punter can
apply before the race (the favourite tales use GRV's SP favourite, the market's favourite at the off). For each:
runners, wins, win %, actual wins against expected at BSP and at GRV's SP (both renormalised to a 100% book), and flat
1-unit ROI at BSP after 8% commission on winnings and at GRV's SP as paid, in two halves by date. A tale the market
already prices has A/E near 1 at BSP and loses at both prices. Then the favourite-longshot question at BSP: A/E and
ROI by BSP price band.

PART 2, OUR MODEL (round 8's F2, standard split, scored on the last quarter's races with BSP on every runner):
  a) each tale's A/E against our model beside BSP's: does the model know it?
  b) the gap to BSP by market: how much Betfair matched at BSP on the race (fifths), track, day or night, maiden or
     not, field size. Where our log loss is closest to Betfair's is where a model edge would show first;
  c) the gallops value rule (1.3x, our price $2-$15, Kelly x75 on the chance halfway to the market, cap 4) at three
     Betfair prices, each with 8% commission and its own Benter blend fitted on the early-stopping months: BSP, the
     best back price at the scheduled off, and the pre-play weighted average price taken; then BSP on the thinnest
     fifth of markets alone.

The Betfair column names are printed (Betfair's public file schema); no Topaz value is printed per runner.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_preview_test as PT   # noqa: E402
import topaz_round11 as R11       # noqa: E402
import topaz_round3 as R3         # noqa: E402
import topaz_round9 as R9         # noqa: E402
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402

COMM = 0.08
EXTRA = ["WIN_BSP_VOLUME", "BEST_AVAIL_BACK_AT_SCHEDULED_OFF", "WIN_PREPLAY_WEIGHTED_AVERAGE_PRICE_TAKEN"]
BANDS = [(1, 2), (2, 3), (3, 5), (5, 8), (8, 13), (13, 21), (21, 51), (51, 1001)]


def tale_columns(df: pd.DataFrame) -> pd.DataFrame:
    """The helper columns the tales need, each known before the race (earlier days only, or the race card)."""
    sp = df.start_price.where(df.start_price > 1)
    df["sp_fav"] = (sp.groupby(df.race_id).rank(method="min") == 1).astype(float).where(sp.notna())
    df["prev_won"] = T.prev_day_values(df, ["dog"], "won")
    df["prev_fav"] = T.prev_day_values(df, ["dog"], "sp_fav")
    df["won_last2"] = R11._prev_rolling(df, "won", 2, "mean", 2)
    df["prev_days_since"] = T.prev_day_values(df, ["dog"], "days_since")
    df["_one"] = 1.0
    df["track_runs"] = R11._prev_sum_count(df, ["dog", "track"], "_one")[1]
    tr = df.trainer_id if "trainer_id" in df else pd.Series(np.nan, index=df.index)
    df["trainer_runners"] = df.groupby([df.race_id, tr.fillna(-1)]).race_id.transform("size").where(tr.notna())
    st = pd.to_datetime(df.start_time, utc=True, errors="coerce") if "start_time" in df else pd.Series(pd.NaT, index=df.index)
    df["hour"] = st.dt.tz_convert("Australia/Melbourne").dt.hour if st.notna().any() else np.nan
    g = df.grade.astype(str).str.upper() if "grade" in df else pd.Series("", index=df.index)
    df["maiden"] = g.str.contains("MAIDEN|MDN", regex=True).astype(float)
    return df.drop(columns="_one")


def tales(df: pd.DataFrame) -> list:
    """(name, mask) for every tale, on the columns tale_columns adds and the model's race-card columns."""
    b, fav = df.box, df.sp_fav == 1
    out = [("box 1", b == 1), ("box 2", b == 2), ("box 8", b == 8),
           ("SP favourite", fav), ("SP favourite in box 1", fav & (b == 1)), ("SP favourite in box 7-8", fav & (b >= 7)),
           ("SP favourite, 6 or fewer runners", fav & (df.field <= 6)),
           ("won last start", df.prev_won == 1), ("won its last two", df.won_last2 == 1),
           ("beaten favourite last start", (df.prev_fav == 1) & (df.prev_won == 0)),
           ("first up after 28+ days", df.days_since >= 28),
           ("second up after a 28+ day spell", (df.prev_days_since >= 28) & (df.days_since < 28)),
           ("backing up within 4 days", df.days_since <= 4),
           ("dropping in grade", df.class_step > 0), ("rising in grade", df.class_step < 0),
           ("up 50m+ in trip", df.dist_change >= 50), ("down 50m+ in trip", df.dist_change <= -50),
           ("debut", df.runs == 0), ("first time at the track (not debut)", (df.track_runs == 0) & (df.runs > 0)),
           ("vacant box beside it", df.vacant_any == 1), ("box 1, box 2 vacant", (b == 1) & (df.vacant_right == 1)),
           ("weight up 1kg+ since last start", df.weight_change >= 1),
           ("weight down 1kg+ since last start", df.weight_change <= -1),
           ("trainer has 2+ in the race", df.trainer_runners >= 2),
           ("under 2 years old", df.age_days < 730.5), ("over 4 years old", df.age_days > 1461)]
    if "trainer_id_won_28D" in df and df.trainer_id_won_28D.notna().any():
        out.append(("hot trainer (top tenth, 28-day strike rate)",
                    df.trainer_id_won_28D >= df.trainer_id_won_28D.quantile(0.9)))
    for v, n in df.sex.value_counts().items():
        if v and n >= 0.05 * len(df):
            out.append((f"sex recorded as {v}", df.sex == v))
    out += [("maiden race", df.maiden == 1), ("night race (6pm on)", df.hour >= 18), ("day race (before 6pm)", df.hour < 18)]
    if "tip_rank" in df and df.tip_rank.notna().mean() > 0.01:
        out.append(("GRV's first tip", df.tip_rank == 1))
    if "is_best_bet" in df and pd.to_numeric(df.is_best_bet, errors="coerce").notna().mean() > 0.01:
        out.append(("GRV's best bet", pd.to_numeric(df.is_best_bet, errors="coerce") == 1))
    return [(n, m.fillna(False).values.astype(bool)) for n, m in out]


def flat_roi(won, price, comm=0.0) -> float:
    """Mean profit of 1 unit on each runner at `price`, commission taken off winnings."""
    won, price = np.asarray(won), np.asarray(price, dtype=float)
    return float(np.where(won == 1, (price - 1) * (1 - comm), -1.0).mean()) if len(won) else np.nan


def tale_row(g: pd.DataFrame) -> dict:
    w = g.won.sum()
    return dict(n=len(g), w=int(w), ae_bsp=w / g.p_bsp.sum(), roi_bsp=flat_roi(g.won, g.bsp, COMM),
                ae_sp=w / g.p_sp.sum(), roi_sp=flat_roi(g.won, g.start_price))


def add_betfair_extra(df: pd.DataFrame) -> tuple[pd.DataFrame, list]:
    """Betfair's other price and volume columns, matched as add_bsp matches BSP (date + normalised dog name)."""
    bdir = os.environ.get("BETFAIR_DIR", "")
    if not bdir or not os.path.isdir(bdir):
        return df, []
    import gbm_v0
    bf = gbm_v0.load(bdir)
    print(f"Betfair file columns: {', '.join(bf.columns)}\n")
    have = [c for c in EXTRA if c in bf]
    for c in have:
        bf[c] = pd.to_numeric(bf[c], errors="coerce")
    bf = bf[(bf.STATE_CODE == "VIC") & (bf.WIN_BSP > 1)][["date", "dog"] + have].drop_duplicates(["date", "dog"], keep=False)
    df["_dn"] = gbm_v0.norm_name(df.dog_name)
    df = df.merge(bf.rename(columns={"dog": "_dn"}), on=["date", "_dn"], how="left").drop(columns="_dn")
    return df, have


def gap_by(t: pd.DataFrame, key: pd.Series, name: str, order=None):
    """Winner log loss of our model less BSP's, races grouped by `key` (constant within a race)."""
    print(f"\n| {name} | races | our log loss | BSP | gap to BSP |\n|---|---|---|---|---|")
    keys = order if order is not None else sorted(key.dropna().unique(), key=str)
    for k in keys:
        m = (key == k).values
        races = t.race_id[m].nunique()
        if races < 200:
            continue
        lo, lb = V1.ll(t.p_a.values[m], t.won.values[m]), V1.ll(t.p_bsp.values[m], t.won.values[m])
        print(f"| {k} | {races:,} | {lo:.4f} | {lb:.4f} | {lo - lb:+.4f} |")


def rule_rows(t2, es2, h, pcol, price_col, label):
    """The 1.3x $2-$15 rule at one price: Benter blend on the early-stopping months, both halves."""
    w, _ = V1.blend(["p_a", pcol], es2)
    t2 = t2.assign(p_blend=V1.blend(["p_a", pcol], t2, w)[1])
    price = t2[price_col].astype(float).values
    for hn, hm in (("1st", h), ("2nd", ~h)):
        sub = t2[hm]
        m, o, u = R9.horse_bets(sub, sub.p_blend.values, sub[pcol].values, price[hm], COMM, 1.3, (2, 15))
        r = R9.summary(sub, m, o, u, price[hm])
        if r["n"]:
            print(f"| {label} | {w[0]:.2f} / {w[1]:.2f} | {hn} | {r['n']:,} | {r['w']:,} | {r['ae']:.3f} | {r['flat']:+.1%} | "
                  f"{r['staked']:,.0f} | {r['kroi']:+.1%} | {r['kunits']:+,.0f} | {r['dd']:,.0f} |")
        else:
            print(f"| {label} | {w[0]:.2f} / {w[1]:.2f} | {hn} | 0 | | | | | | | |")


def main(d, label):
    df, num, rel, bsp_note = W.build(d)
    if "is_best_bet" not in df and "isBestBet" in df:
        df["is_best_bet"] = df.isBestBet
    df, fpv, _ = PT.preview_features(df)
    ftip = []
    if os.environ.get("RACES_DIR") and os.path.isdir(os.environ["RACES_DIR"]):
        from greyhound.races import load_races, tip_features
        df, ftip = tip_features(df, load_races(os.environ["RACES_DIR"]))
    print(f"# {label}: round 12, the old tales and where we are closest to Betfair\n\n{bsp_note}\n")
    df, have = add_betfair_extra(df)
    df = tale_columns(df).copy()

    # PART 1: the tales on every race Betfair priced in full
    a = df[df.p_bsp.notna() & df.p_sp.notna()]
    half = (a.date < a.date.quantile(0.5)).values
    print(f"## Part 1: the tales, {a.race_id.nunique():,} races from {a.date.min():%Y-%m-%d}, halves split at "
          f"{a.date.quantile(0.5):%Y-%m-%d}\n")
    print("| tale | runners | win % | A/E at BSP (1st / 2nd) | flat ROI at BSP, 8% comm (1st / 2nd) | "
          "A/E at GRV's SP (1st / 2nd) | flat ROI at GRV's SP (1st / 2nd) |\n|---|---|---|---|---|---|---|")
    for name, m in tales(a):
        if m.sum() < 500:
            continue
        r1, r2 = tale_row(a[m & half]), tale_row(a[m & ~half])
        n, w = r1["n"] + r2["n"], r1["w"] + r2["w"]
        print(f"| {name} | {n:,} | {w / n:.1%} | {r1['ae_bsp']:.3f} / {r2['ae_bsp']:.3f} | {r1['roi_bsp']:+.1%} / {r2['roi_bsp']:+.1%} | "
              f"{r1['ae_sp']:.3f} / {r2['ae_sp']:.3f} | {r1['roi_sp']:+.1%} / {r2['roi_sp']:+.1%} |")
    print("\n| BSP | runners | win % | A/E at BSP (1st / 2nd) | flat ROI at BSP, 8% comm (1st / 2nd) |\n|---|---|---|---|---|")
    for lo, hi in BANDS:
        m = ((a.bsp >= lo) & (a.bsp < hi)).values
        r1, r2 = tale_row(a[m & half]), tale_row(a[m & ~half])
        n, w = r1["n"] + r2["n"], r1["w"] + r2["w"]
        bname = f"${lo}-${hi}" if hi < 1000 else f"${lo}+"
        print(f"| {bname} | {n:,} | {w / n:.1%} | {r1['ae_bsp']:.3f} / {r2['ae_bsp']:.3f} | "
              f"{r1['roi_bsp']:+.1%} / {r2['roi_bsp']:+.1%} |")

    # PART 2: our model on the standard split
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
    print(f"\n## Part 2: our model (F2, {k} rounds), {t.race_id.nunique():,} scored races with BSP from {t.date.min():%Y-%m-%d}; "
          f"log loss {V1.ll(t.p_a.values, t.won.values):.4f}, BSP {V1.ll(t.p_bsp.values, t.won.values):.4f}\n")
    print("| tale | runners | wins | A/E vs our model | A/E vs BSP | A/E vs GRV's SP |\n|---|---|---|---|---|---|")
    for name, m in tales(t):
        if m.sum() < 300:
            continue
        g = t[m]
        w = g.won.sum()
        print(f"| {name} | {len(g):,} | {int(w):,} | {w / g.p_a.sum():.3f} | {w / g.p_bsp.sum():.3f} | {w / g.p_sp.sum():.3f} |")

    if "WIN_BSP_VOLUME" in have:
        vol = t.groupby("race_id").WIN_BSP_VOLUME.transform("sum")
        qs = vol.groupby(t.race_id).first().quantile([0.2, 0.4, 0.6, 0.8]).values
        names = ["thinnest fifth", "second fifth", "middle fifth", "fourth fifth", "deepest fifth"]
        t["vol5"] = pd.cut(vol, [-np.inf, *qs, np.inf], labels=names).astype(str)
        print("\nBSP volume per race, fifth boundaries: " + ", ".join(f"{q:,.0f}" for q in qs))
        gap_by(t, t.vol5, "Betfair BSP volume on the race", names)
    gap_by(t, t.track.astype(str), "track")
    gap_by(t, pd.Series(np.where(t.hour >= 18, "night (6pm on)", np.where(t.hour < 18, "day", "unknown")), index=t.index),
           "time of day")
    gap_by(t, pd.Series(np.where(t.maiden == 1, "maiden", "not maiden"), index=t.index), "grade")
    gap_by(t, pd.Series(np.where(t.field <= 6, "6 or fewer", np.where(t.field == 7, "7", "8+")), index=t.index),
           "field size", ["6 or fewer", "7", "8+"])

    print("\n## The 1.3x rule, our price $2-$15, Kelly x75 cap 4, 8% commission, at each Betfair price\n")
    print("| price | blend weights (ours / market) | half | bets | winners | A/E | flat ROI | units staked | Kelly ROI | "
          "units won | worst drawdown |\n|---|---|---|---|---|---|---|---|---|---|---|")
    e = es[es.p_bsp.notna()].copy()
    for col, pname in (("bsp", "BSP"), ("BEST_AVAIL_BACK_AT_SCHEDULED_OFF", "best back at the scheduled off"),
                       ("WIN_PREPLAY_WEIGHTED_AVERAGE_PRICE_TAKEN", "pre-play weighted average")):
        if col != "bsp" and col not in have:
            continue
        pc = f"p_{col}"
        for x in (t, e):
            inv = (1 / x[col].where(x[col] > 1))
            full = inv.notna().groupby(x.race_id).transform("all")
            x[pc] = (inv / inv.groupby(x.race_id).transform("sum")).where(full)
        t2, e2 = t[t[pc].notna()], e[e[pc].notna()]
        h = (t2.date < t2.date.quantile(0.5)).values
        rule_rows(t2, e2, h, pc, col, pname)
    if "vol5" in t:
        t2 = t[t.vol5 == "thinnest fifth"]
        h = (t2.date < t2.date.quantile(0.5)).values
        rule_rows(t2, e, h, "p_bsp", "bsp", "BSP, thinnest fifth of markets")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 12")
