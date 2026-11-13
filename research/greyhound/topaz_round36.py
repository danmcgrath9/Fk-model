"""Round 36: the card's rule at TAB's open, month by month and by the three Betwatch periods (13 Nov 2026).

Round 34 made 723 of the 1.3x rule's bets at TAB's first price from May 2023 to March 2025 and 10 from March 2025 to
November 2026. Round 35 found Betwatch's open moves in three periods:
  - to August 2023: TAB's first price about 22 hours before the jump, a dog scratched after it in about 40% of races;
  - September 2023 to January 2025: about 9 hours before, a scratching after it in only 6-10% of races;
  - February 2025 on: about 10.5 hours before, a scratching after it in 41-55% of races.
Did the bets stop because TAB's opening prices moved, or because the blend refitted each month gave ours less weight?

    python research/greyhound/topaz_round36.py DIR LABEL    (BETWATCH_DIR; the weekly train's WALK_* settings;
                                                             WALK_REFIT_EVERY, 6 by default; WALK_TO, a date: races on
                                                             or after it are left out, so the walk can be cached;
                                                             WALK_CACHE_DIR: the saved walk)

Ours, the field at the bet and TAB's deduction are round 34's (topaz_walk.walk_cached, topaz_round33.at_time). Printed:
  1. month by month: the field at the bet, the blend's weights that month (refitted on the six months before, on races
     with nothing scratched after the open), how often TAB's first price is 1.3x ours alone and 1.3x the blend, and the
     card's rule at TAB's first price
  2. the card's rule by period, at TAB's first price and the best first price of three, with the blend refitted each
     month and with it held at Test 51's weights (0.54 ours, 0.67 TAB): if the bets come back with the weights held,
     the blend moved; if not, the prices did
  3. the same by period on races with nothing scratched after the open, and BSP against the price paid
"""
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import gbm_v0                     # noqa: E402
import topaz_round9 as R9         # noqa: E402
import topaz_round12 as R12       # noqa: E402
import topaz_round18 as R18       # noqa: E402
import topaz_round29 as R29       # noqa: E402
import topaz_round30 as R30       # noqa: E402
import topaz_round31 as R31       # noqa: E402
import topaz_round33 as R33       # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402

BLEND_MONTHS = 6
FIXED = (0.54, 0.67)              # Test 51's weights, fitted on the early-stopping months (Dec 2023 to Jun 2024)
PERIODS = [("to Aug 2023 (open ~22 h out)", None, "2023-09-01"),
           ("Sep 2023 to Jan 2025 (open ~9 h out, few later scratchings)", "2023-09-01", "2025-02-01"),
           ("Feb 2025 on (open ~10.5 h out)", "2025-02-01", None)]
PRICES = {"TAB's first price": "price", "best first price of three": "best_first"}


def monthly_blend(x: pd.DataFrame, months) -> tuple:
    """The blended chance for every row of the field at the bet, refitted each month on the BLEND_MONTHS before on
    races with nothing scratched after the bet; and the weights by month."""
    out, ws = pd.Series(np.nan, index=x.index), {}
    for M in months:
        w = x[x.is_ran & (x.n_later == 0) & (x.date >= (M - BLEND_MONTHS).start_time) & (x.date < M.start_time)]
        cur = ((x.date >= M.start_time) & (x.date < (M + 1).start_time)).values
        if w.race_id.nunique() < 300 or not cur.any():
            continue
        wb, _ = V1.blend(["p_x_bet", "p_book"], w)
        out[cur] = V1.blend(["p_x_bet", "p_book"], x[cur], wb)[1]
        ws[M] = wb
    return out, ws


def fixed_blend(x: pd.DataFrame, w=FIXED) -> pd.Series:
    return pd.Series(V1.blend(["p_x_bet", "p_book"], x, np.asarray(w))[1], index=x.index)


def card(t: pd.DataFrame, pb_col: str, price_col: str):
    """The card's rule on t: mask, the price paid after TAB's deduction, Kelly units."""
    price = t[price_col].values.astype(float)
    m, o, u = R9.horse_bets(t, t[pb_col].values, t.p_book.values, price, 0.0, 1.3, (2, 15))
    return m, 1 + (o - 1) * (1 - t.ded.fillna(0).values), u


def in_period(t: pd.DataFrame, a, b) -> np.ndarray:
    m = np.ones(len(t), bool)
    if a:
        m &= (t.date >= a).values
    if b:
        m &= (t.date < b).values
    return m


def row(t, m, paid, u, price):
    r = R9.summary(t, m, paid, u, price)
    if not r["n"]:
        return "0 | | | | | | |"
    x = m
    bym = pd.Series(np.where(t.won.values[x] == 1, paid[x] - 1, -1) * u[x]).groupby(
        pd.to_datetime(t.date.values[x]).to_period("M")).sum()
    return (f"{r['n']:,} | {r['w']:,} | {r['ae']:.3f} | {r['flat']:+.1%} | {r['kroi']:+.1%} | {r['kunits']:+,.0f} | "
            f"{(bym > 0).sum()} of {len(bym)} |")


def by_month(t: pd.DataFrame, ws: dict) -> None:
    print("| month | races | with a scratching after the open | blend weights (ours / TAB) | TAB's first price 1.3x ours "
          "alone | 1.3x the blend | card's bets | winners | flat return |\n|---|---|---|---|---|---|---|---|---|")
    m, paid, u = card(t, "pb", "price")
    ours_alone = (t.price.values >= 1.3 / np.clip(t.p_x_bet.values, 1e-9, 1))
    blend_x = (t.price.values >= 1.3 / np.clip(t.pb.values, 1e-9, 1))
    for M, g in t.groupby(t.date.dt.to_period("M")):
        i = t.index.isin(g.index)
        races = g.drop_duplicates("race_id")
        w = ws.get(M)
        mi = m & i
        ret = np.where(t.won.values[mi] == 1, paid[mi] - 1, -1).mean() if mi.any() else np.nan
        print(f"| {M} | {len(races):,} | {races.n_later.gt(0).mean():.1%} | "
              f"{'' if w is None else f'{w[0]:.2f} / {w[1]:.2f}'} | {ours_alone[i].mean():.2%} | {blend_x[i].mean():.2%} | "
              f"{mi.sum():,} | {int(t.won.values[mi].sum()):,} | {'' if np.isnan(ret) else f'{ret:+.1%}'} |")


def by_period(t: pd.DataFrame, title: str) -> None:
    print(f"\n{title}\n\n| period | price | blend | bets | winners | A/E vs the price taken | flat ROI | Kelly ROI | "
          "units won | months in profit |\n|---|---|---|---|---|---|---|---|---|---|")
    for pname, a, b in PERIODS:
        p = in_period(t, a, b)
        for prn, pcol in PRICES.items():
            for bn, bcol in (("refitted monthly", "pb"), ("held at 0.54 / 0.67", "pb_fixed")):
                m, paid, u = card(t, bcol, pcol)
                print(f"| {pname} | {prn} | {bn} | {row(t, m & p, paid, u, t[pcol].values.astype(float))}")


def bsp_table(t: pd.DataFrame) -> None:
    print("\nBSP against the price paid after TAB's deduction, the card's rule at TAB's first price, blend refitted "
          "monthly:\n\n| period | bets with a BSP | BSP under the price paid | mean log(price paid / BSP) | A/E vs BSP |"
          "\n|---|---|---|---|---|")
    m, paid, u = card(t, "pb", "price")
    for pname, a, b in PERIODS:
        x = m & in_period(t, a, b) & t.p_bsp.notna().values if "p_bsp" in t else np.zeros(len(t), bool)
        if not x.any():
            print(f"| {pname} | 0 | | | |")
            continue
        bsp = 1 / t.p_bsp.values[x]
        lr = np.log(paid[x] / bsp)
        print(f"| {pname} | {x.sum():,} | {(bsp < paid[x]).sum():,} ({(bsp < paid[x]).mean():.1%}) | {lr.mean():+.3f} | "
              f"{t.won.values[x].sum() / t.p_bsp.values[x].sum():.3f} |")


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 36, the card's rule at TAB's open by month and by Betwatch period\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    fr = R33.load(bdir, times=(0,))
    bw = R30.load_betwatch(bdir)
    if fr.empty or bw.empty:
        print("No Betwatch races: nothing to test")
        return 1
    df, num, rel, note = W.build_full(d)
    df, _, _ = R18.check_features(df, os.environ.get("ISOLYNX_DIR", ""))
    df = R12.tale_columns(df)
    bfd = os.environ.get("BETFAIR_DIR", "")
    if bfd and os.path.isdir(bfd):
        df = R29.betfair_extras(df, bfd)
    to = os.environ.get("WALK_TO", "").strip()
    if to:
        df = df[df.date < to].reset_index(drop=True)
    every = max(1, int(os.environ.get("WALK_REFIT_EVERY", "6") or 6))
    first_pred = bw.date.min().to_period("M")
    print(f"{note}\nOurs refitted every {every} months from {first_pred} on every race before, {W.ROUNDS_A} rounds; "
          f"{len(num)} inputs{f'; races before {to} only' if to else ''}.\n")
    df, log = W.walk_cached(df, num, rel, first_pred, t0, every)
    print("Refits: " + "; ".join(f"{m}: {s}" for m, s in log if "priced by" not in s) + "\n")
    df = df[df.p_a.notna()].copy()
    df["p_x"] = df.p_a
    x = R33.at_time(df, fr, 0)
    sb = bw[["date", "_dn", "sportsbet_first", "ladbrokes_first"]]
    x = x.assign(_dn=gbm_v0.norm_name(x.dog_name.fillna(""))).merge(sb, on=["date", "_dn"], how="left")
    x = x.drop(columns="_dn")
    x["tab_first"] = x.price
    x["best_first"] = R31.best_first(x)
    months = pd.period_range(first_pred + BLEND_MONTHS, x.date.max().to_period("M"), freq="M")
    x["pb"], ws = monthly_blend(x, months)
    x["pb_fixed"] = fixed_blend(x)
    ok = pd.Series((x.pb.notna() & (x.price > 1)).values)
    whole = ok.groupby(x.race_id.values).transform("all").values
    t = x[whole & x.is_ran.values].reset_index(drop=True)
    print(f"Field at the bet: {t.race_id.nunique():,} races, {len(t):,} runners that ran, {t.date.min():%Y-%m-%d} to "
          f"{t.date.max():%Y-%m-%d}. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    print("## 1. Month by month (TAB's first price)\n")
    by_month(t, ws)
    print("\n## 2. The card's rule by period, after TAB's deduction")
    by_period(t, "Every race:")
    by_period(t[(t.n_later == 0).values].reset_index(drop=True), "Races with nothing scratched after the open:")
    bsp_table(t)
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 36")
