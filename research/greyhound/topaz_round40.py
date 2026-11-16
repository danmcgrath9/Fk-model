"""Round 40: does refitting ours more often help at TAB's open? (16 Nov 2026, founder: "Well keep testing and lets get
a fucking good model")

Test 57 settled where the bet is: ours blended with TAB's first book, at TAB's first price, weights held. So the lever
is ours, and since February 2025 TAB's first book beats ours alone (Test 55: 1.5913 against 1.5992). Every walk so far
refits ours every six months; the live model retrains every week. If the half-year gap between refits is what costs
ours, a walk refitted every two months should close some of it. Two walks over the same races:

  - every six months: the saved walk (WALK_CACHE_USE), refits at 2024-11, 2025-05, 2025-11, 2026-05
  - every two months from November 2024: refitted here (13 refits; saved to the cache for later rounds)

and on the field at TAB's first price from November 2024, for each: log loss of ours alone, of the blend with TAB's
first book held at Test 51's weights (0.54 / 0.67), and the card's rule at 1.3x after TAB's deduction.

    python research/greyhound/topaz_round40.py DIR LABEL    (as round 39; WALK_CACHE_USE names the six-month walk)

Counts, sums and rates only: no race, dog or price is printed.
"""
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round12 as R12       # noqa: E402
import topaz_round18 as R18       # noqa: E402
import topaz_round29 as R29       # noqa: E402
import topaz_round33 as R33       # noqa: E402
import topaz_round36 as R36       # noqa: E402
import topaz_round38 as R38       # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402

FROM = "2024-11"
FIXED = (0.54, 0.67)
PERIODS = [("Nov 2024 to Jan 2025", "2024-11-01", "2025-02-01"), ("Feb 2025 to Jan 2026", "2025-02-01", "2026-02-01"),
           ("Feb 2026 on", "2026-02-01", None), ("Feb 2025 on", "2025-02-01", None)]


def base(d: str):
    df, num, rel, note = W.build_full(d)
    df, _, _ = R18.check_features(df, os.environ.get("ISOLYNX_DIR", ""))
    df = R12.tale_columns(df)
    bfd = os.environ.get("BETFAIR_DIR", "")
    if bfd and os.path.isdir(bfd):
        df = R29.betfair_extras(df, bfd)
    to = os.environ.get("WALK_TO", "").strip()
    if to:
        df = df[df.date < to].reset_index(drop=True)
    return df, num, rel, note


def two_walks(d: str, t0: float) -> pd.DataFrame:
    """Ours every six months (the named saved walk) and every two months from FROM, on the same rows."""
    df, num, rel, note = base(d)
    print(note)
    a, log_a = W.walk_cached(df.copy(), num, rel, pd.Period("2022-11", "M"), t0, 6)
    print("Every six months: " + "; ".join(f"{m}: {s}" for m, s in log_a if "priced by" not in s))
    use = os.environ.pop("WALK_CACHE_USE", None)
    try:
        b, log_b = W.walk_cached(df.copy(), num, rel, pd.Period(FROM, "M"), t0, 2)
    finally:
        if use:
            os.environ["WALK_CACHE_USE"] = use
    print("Every two months: " + "; ".join(f"{m}: {s}" for m, s in log_b if "priced by" not in s) + "\n")
    out = a.copy()
    out["p_a2"] = b.p_a.values
    out = out[(out.date >= pd.Period(FROM, "M").start_time) & out.p_a.notna() & out.p_a2.notna()].copy()
    out["p_x"] = out.p_a
    return out


def ll(g: pd.DataFrame, col: str) -> float:
    return float(-np.log(g[col].clip(1e-9)).mean())


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 40, does refitting ours more often help at TAB's open?\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    df = two_walks(d, t0)
    if not len(df):
        print("Neither walk priced anything from " + FROM)
        return 1
    fr = R33.load(bdir, times=(0,))
    x = R33.at_time(df, fr, 0)
    ran = x.is_ran.astype(bool).values
    x["p_x2_bet"] = np.where(ran, x.p_a2 * (1 - x.s_later.fillna(0)), x.p_book)
    x["pb6"] = V1.blend(["p_x_bet", "p_book"], x, np.asarray(FIXED))[1]
    x["pb2"] = V1.blend(["p_x2_bet", "p_book"], x, np.asarray(FIXED))[1]
    ok = pd.Series((x.price > 1).values).groupby(x.race_id.values).transform("all").values
    t = x[ok & ran].reset_index(drop=True)
    print(f"Field at TAB's first price from {FROM}: {t.race_id.nunique():,} races, {len(t):,} runners that ran. "
          f"{(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    print("## 1. Log loss on races with nothing scratched after the open (lower is better)\n")
    clean = t[(t.n_later == 0).values]
    full = clean.p_bsp.notna().groupby(clean.race_id).transform("all").values if "p_bsp" in clean else None
    w = clean[(full if full is not None else True) & (clean.won == 1).values]
    print("| period | races | ours, every six months | ours, every two months | TAB's first book | blend, six | blend, two "
          "| BSP |\n|---|---|---|---|---|---|---|---|")
    for pname, a, b in PERIODS:
        g = w[R36.in_period(w, a, b)]
        if g.empty:
            continue
        print(f"| {pname} | {g.race_id.nunique():,} | {ll(g, 'p_x_bet'):.4f} | {ll(g, 'p_x2_bet'):.4f} | "
              f"{ll(g, 'p_book'):.4f} | {ll(g, 'pb6'):.4f} | {ll(g, 'pb2'):.4f} | "
              f"{ll(g, 'p_bsp') if 'p_bsp' in g else float('nan'):.4f} |")
    old = R36.PERIODS
    R36.PERIODS = PERIODS
    try:
        cols = {"blend, ours every six months": "pb6", "blend, ours every two months": "pb2"}
        print("\n## 2. The card's rule at 1.3x, TAB's first price, after TAB's deduction")
        R38.rule_table(t, cols, "Every race:")
        R38.rule_table(t[(t.n_later == 0).values].reset_index(drop=True), cols, "Races with nothing scratched after the open:")
    finally:
        R36.PERIODS = old
    m6 = R38.R37.rule(t, "pb6", 1.3)[0]
    m2 = R38.R37.rule(t, "pb2", 1.3)[0]
    rec = (t.date >= "2025-02-01").values
    print(f"\nSince February 2025 the two make {int((m6 & rec).sum())} and {int((m2 & rec).sum())} bets, "
          f"{int((m6 & m2 & rec).sum())} of them the same dog.")
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 40")
