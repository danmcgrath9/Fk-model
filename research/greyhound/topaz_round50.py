"""Round 50: Isolynx in ours, walked forward, at TAB's open (16 Nov 2026, founder: "Well keep testing and lets get a
fucking good model")

Test 67: since mid-2024 TAB's first book has caught up with ours. It was 0.11 to 0.12 worse than BSP in 2023 and 0.08
to 0.10 since, while ours stayed 0.075 to 0.115 from BSP throughout, and the edge stepped down with it. So the lever is ours,
and it needs information it does not have. The biggest single step any test has found is Isolynx tracking and the
checks (Test 35: 0.0039 closer to BSP, "the biggest single step since GRV's rating"), which was decided for the win
model and has never been walked forward. Stated before the run:

  - ours, refitted every six months from November 2022 as the saved walk is, with Isolynx's 15 tracking inputs and
    the 4 check inputs added (ISOLYNX_DIR; the pull runs to 6 Nov 2026), and nothing else changed
  - against the saved walk (WALK_CACHE_USE), on the same races at TAB's first price from May 2023: log loss of ours
    alone, of each blended with TAB's first book at Test 51's held weights (0.54 / 0.67; fitted for the walk without
    Isolynx, so they favour it, if anything), TAB's first book and BSP, by period; the card's rule at 1.3x; and
    BSP's verdict flat from 1.1x and 1.3x and on the card's stakes
  - the walk with Isolynx is saved to the walk cache for later rounds

    python research/greyhound/topaz_round50.py DIR LABEL    (isolynx=yes; WALK_CACHE_USE names the saved walk)

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
import topaz_round37 as R37       # noqa: E402
import topaz_round38 as R38       # noqa: E402
import topaz_round43 as R43       # noqa: E402
import topaz_round44 as R44       # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402

FIRST = "2022-11"
FIXED = (0.54, 0.67)
BW_FROM = "2023-05-01"
PERIODS = [("May 2023 to Jan 2025", "2023-05-01", "2025-02-01"), ("Feb 2025 to Jan 2026", "2025-02-01", "2026-02-01"),
           ("Feb 2026 on", "2026-02-01", None), ("Feb 2025 on", "2025-02-01", None)]


def base(d: str):
    """As round 40's base, with the Isolynx check inputs kept as inputs (round 40 dropped the list)."""
    df, num, rel, note = W.build_full(d)
    df, chk, share = R18.check_features(df, os.environ.get("ISOLYNX_DIR", ""))
    num = list(dict.fromkeys(list(num) + list(chk)))
    df = R12.tale_columns(df)
    bfd = os.environ.get("BETFAIR_DIR", "")
    if bfd and os.path.isdir(bfd):
        df = R29.betfair_extras(df, bfd)
    to = os.environ.get("WALK_TO", "").strip()
    if to:
        df = df[df.date < to].reset_index(drop=True)
    iso = [c for c in num if c.startswith("iso_") or c in chk]
    return df, num, rel, note + f"\nIsolynx inputs in ours: {len(iso)} ({len(chk)} of them the checks)"


def two_walks(d: str, t0: float) -> pd.DataFrame:
    df, num, rel, note = base(d)
    print(note)
    a, log_a = W.walk_cached(df.copy(), num, rel, pd.Period(FIRST, "M"), t0, 6)
    print("Saved walk, no Isolynx: " + "; ".join(f"{m}: {s}" for m, s in log_a if "priced by" not in s))
    use = os.environ.pop("WALK_CACHE_USE", None)
    try:
        b, log_b = W.walk_cached(df.copy(), num, rel, pd.Period(FIRST, "M"), t0, 6)
    finally:
        if use:
            os.environ["WALK_CACHE_USE"] = use
    print("With Isolynx: " + "; ".join(f"{m}: {s}" for m, s in log_b if "priced by" not in s) + "\n")
    out = a.copy()
    out["p_i"] = b.p_a.values
    out = out[(out.date >= BW_FROM) & out.p_a.notna() & out.p_i.notna()].copy()
    out["p_x"] = out.p_a
    return out


def ll(g: pd.DataFrame, col: str) -> float:
    return float(-np.log(g[col].clip(1e-9)).mean())


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 50, Isolynx in ours, walked forward, at TAB's open\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    if not os.path.isdir(os.environ.get("ISOLYNX_DIR", "")):
        print("No Isolynx pull (ISOLYNX_DIR): nothing to test")
        return 1
    df = two_walks(d, t0)
    fr = R33.load(bdir, times=(0,))
    x = R33.at_time(df, fr, 0)
    ran = x.is_ran.astype(bool).values
    x["p_i_bet"] = np.where(ran, x.p_i * (1 - x.s_later.fillna(0)), x.p_book)
    x["pb6"] = V1.blend(["p_x_bet", "p_book"], x, np.asarray(FIXED))[1]
    x["pbi"] = V1.blend(["p_i_bet", "p_book"], x, np.asarray(FIXED))[1]
    ok = pd.Series((x.price > 1).values).groupby(x.race_id.values).transform("all").values
    t = x[ok & ran].reset_index(drop=True)
    print(f"Field at TAB's first price from May 2023: {t.race_id.nunique():,} races, {len(t):,} runners that ran. "
          f"{(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    print("## 1. Log loss, winners only, races with nothing scratched after the open and a BSP on every runner\n")
    clean = t[(t.n_later == 0).values]
    full = clean.p_bsp.notna().groupby(clean.race_id.values).transform("all").values
    w = clean[full & (clean.won == 1).values]
    print("| period | races | ours, no Isolynx | ours, with Isolynx | TAB's first book | blend, no Isolynx "
          "| blend, with Isolynx | BSP |\n|---|---|---|---|---|---|---|---|")
    for pname, lo, hi in PERIODS:
        g = w[R36.in_period(w, lo, hi)]
        if len(g):
            print(f"| {pname} | {g.race_id.nunique():,} | {ll(g, 'p_x_bet'):.4f} | {ll(g, 'p_i_bet'):.4f} | "
                  f"{ll(g, 'p_book'):.4f} | {ll(g, 'pb6'):.4f} | {ll(g, 'pbi'):.4f} | {ll(g, 'p_bsp'):.4f} |")
    cols = {"blend, no Isolynx": "pb6", "blend, with Isolynx": "pbi"}
    old = R36.PERIODS
    R36.PERIODS = PERIODS
    try:
        print("\n## 2. The card's rule at 1.3x, TAB's first price, after TAB's deduction")
        R38.rule_table(t, cols, "Every race:")
    finally:
        R36.PERIODS = old
    print("\n## 3. BSP's verdict, flat\n")
    print("| period | blend | rule | " + R44.HEAD + " |\n|---|---|---|---|---|---|---|---|---|---|---|")
    for pname, lo, hi in PERIODS:
        p = R36.in_period(t, lo, hi)
        for name, col in cols.items():
            for r in (1.1, 1.3):
                m, paid, _ = R43.flat_candidates(t, col, r)
                print(f"| {pname} | {name} | flat, {r}x | " + " | ".join(R44.cells(R44.judged(t, m & p, paid)))
                      + " |")
    print("\nThe card's rule at 1.3x on its own Kelly stakes, by BSP:\n")
    old = R43.PERIODS
    R43.PERIODS = PERIODS[:]
    try:
        R44.card(t, cols)
    finally:
        R43.PERIODS = old
    rec = (t.date >= "2025-02-01").values
    m0, m1 = R37.rule(t, "pb6", 1.3)[0] & rec, R37.rule(t, "pbi", 1.3)[0] & rec
    print(f"\nSince February 2025 the two blends make {int(m0.sum())} and {int(m1.sum())} bets, "
          f"{int((m0 & m1).sum())} of them the same dog.")
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 50")
