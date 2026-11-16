"""Round 51: the blend refitted for ours with Isolynx (16 Nov 2026, founder: "Well keep testing and lets get a fucking
good model")

Test 68: Isolynx makes ours closer to BSP in every period (0.0057 of log loss since February 2025, from 0.0079 behind
TAB's first book to 0.0022 behind), and the blend with TAB 0.0027 closer. The card's bets at 1.3x come out the same by
BSP. Those bets were made on the blend at the held weights, 0.54 ours and 0.67 TAB, which Test 51 fitted on December
2023 to June 2024 for ours WITHOUT Isolynx. A better ours deserves more weight and the held weights never give it any.
Stated before the run:

  - both saved walks read by name, so the prices are round 50's exactly: without Isolynx (WALK_CACHE_USE,
    47fecb2b5fac8c3c) and with it (WALK_ISO_USE, 3175ebcbfe9eb070)
  - each blended with TAB's first book at weights fitted on Test 51's window, December 2023 to June 2024, on races with
    nothing scratched after the open, as round 38's held blend was, and held from there. The refit for the walk without
    Isolynx is the check that the fit is the one Test 51 made: it should come back near 0.54 / 0.67
  - for those blends and the two at 0.54 / 0.67 (round 50's): log loss by period, the card's rule at 1.3x, BSP's
    verdict flat from 1.1x and 1.3x, and the card's Kelly stakes by BSP
  - a second fit on February 2025 to January 2026, judged on February 2026 on only: the most recent year out of sample

    python research/greyhound/topaz_round51.py DIR LABEL    (as round 50, with WALK_ISO_USE naming its saved walk)

Counts, sums and rates only: no race, dog or price is printed.
"""
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round33 as R33       # noqa: E402
import topaz_round36 as R36       # noqa: E402
import topaz_round37 as R37       # noqa: E402
import topaz_round38 as R38       # noqa: E402
import topaz_round43 as R43       # noqa: E402
import topaz_round44 as R44       # noqa: E402
import topaz_round50 as R50       # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402

FIT = ("2023-12-01", "2024-07-01")         # Test 51's window, as round 38's held()
RECENT_FIT = ("2025-02-01", "2026-02-01")  # the year before the last period
RECENT = [("Feb 2026 on", "2026-02-01", None)]
OURS = {"no Isolynx": "p_x_bet", "with Isolynx": "p_i_bet"}


def fit_weights(x: pd.DataFrame, cols: list, lo: str, hi: str) -> np.ndarray:
    """The blend's weights fitted on [lo, hi), races with nothing scratched after the open, every input priced."""
    w = x[(x.date >= lo).values & (x.date < hi).values & (x.n_later == 0).values & x[cols].notna().all(axis=1).values]
    return np.asarray(V1.blend(cols, w)[0])


def apply_weights(x: pd.DataFrame, cols: list, wb) -> pd.Series:
    """The blend at weights wb over every row with its inputs priced (NaN elsewhere)."""
    ok = x[cols].notna().all(axis=1).values
    out = pd.Series(np.nan, index=x.index)
    out[ok] = V1.blend(cols, x[ok], np.asarray(wb))[1]
    return out


def named_walks(d: str, t0: float) -> pd.DataFrame:
    """Round 50's runners with both saved walks' prices, read by name (no refit)."""
    df, num, rel, note = R50.base(d)
    print(note)
    a, log_a = W.walk_cached(df.copy(), num, rel, pd.Period(R50.FIRST, "M"), t0, 6)
    use = os.environ["WALK_CACHE_USE"]
    os.environ["WALK_CACHE_USE"] = os.environ["WALK_ISO_USE"]
    try:
        b, log_b = W.walk_cached(df.copy(), num, rel, pd.Period(R50.FIRST, "M"), t0, 6)
    finally:
        os.environ["WALK_CACHE_USE"] = use
    for name, lg in (("No Isolynx", log_a), ("With Isolynx", log_b)):
        print(f"{name}: " + "; ".join(s for m, s in lg if m == "cache"))
    out = a.copy()
    out["p_i"] = b.p_a.values
    out = out[(out.date >= R50.BW_FROM) & out.p_a.notna() & out.p_i.notna()].copy()
    out["p_x"] = out.p_a
    return out


def ll_table(t: pd.DataFrame, cols: dict, periods: list) -> None:
    clean = t[(t.n_later == 0).values]
    full = clean.p_bsp.notna().groupby(clean.race_id.values).transform("all").to_numpy(copy=True)
    for c in cols.values():
        full = full & clean[c].notna().groupby(clean.race_id.values).transform("all").to_numpy()
    w = clean[full & (clean.won == 1).values]
    print("| period | races | TAB's first book | " + " | ".join(cols) + " | BSP |\n|" + "---|" * (len(cols) + 4))
    for pname, lo, hi in periods:
        g = w[R36.in_period(w, lo, hi)]
        if len(g):
            print(f"| {pname} | {g.race_id.nunique():,} | {R50.ll(g, 'p_book'):.4f} | "
                  + " | ".join(f"{R50.ll(g, c):.4f}" for c in cols.values()) + f" | {R50.ll(g, 'p_bsp'):.4f} |")


def judge(t: pd.DataFrame, cols: dict, periods: list) -> None:
    """The card's rule at 1.3x, BSP's verdict flat from 1.1x and 1.3x, and the card's Kelly stakes by BSP."""
    old36, old43 = R36.PERIODS, R43.PERIODS
    R36.PERIODS, R43.PERIODS = periods, periods[:]
    try:
        R38.rule_table(t, cols, "The card's rule at 1.3x, TAB's first price, after TAB's deduction, every race:")
        print("\nBSP's verdict, flat:\n\n| period | blend | rule | " + R44.HEAD + " |\n|---|---|---|---|---|---|---|---|"
              "---|---|---|")
        for pname, lo, hi in periods:
            p = R36.in_period(t, lo, hi)
            for name, col in cols.items():
                for r in (1.1, 1.3):
                    m, paid, _ = R43.flat_candidates(t.assign(_pb=t[col].fillna(0)), "_pb", r)
                    m = m & t[col].notna().values
                    print(f"| {pname} | {name} | {r}x | " + " | ".join(R44.cells(R44.judged(t, m & p, paid))) + " |")
        print("\nThe card's rule at 1.3x on its own Kelly stakes, by BSP:\n")
        R44.card(t, cols)
    finally:
        R36.PERIODS, R43.PERIODS = old36, old43


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 51, the blend refitted for ours with Isolynx\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    if not os.environ.get("WALK_CACHE_USE", "").strip() or not os.environ.get("WALK_ISO_USE", "").strip():
        print("Both saved walks must be named (WALK_CACHE_USE and WALK_ISO_USE): nothing to test")
        return 1
    df = named_walks(d, t0)
    fr = R33.load(bdir, times=(0,))
    x = R33.at_time(df, fr, 0)
    ran = x.is_ran.astype(bool).values
    x["p_i_bet"] = np.where(ran, x.p_i * (1 - x.s_later.fillna(0)), x.p_book)
    ok = pd.Series((x.price > 1).values).groupby(x.race_id.values).transform("all").values
    x = x[ok].reset_index(drop=True)

    print("\n## 1. The weights\n\n| blend | fitted on | ours | TAB |\n|---|---|---|---|")
    print(f"| both | Test 51, held | {R50.FIXED[0]:.2f} | {R50.FIXED[1]:.2f} |")
    cols, recent = {}, {}
    for name, c in OURS.items():
        x[f"h_{c}"] = apply_weights(x, [c, "p_book"], R50.FIXED)
        cols[f"{name}, 0.54 / 0.67"] = f"h_{c}"
    for name, c in OURS.items():
        wb = fit_weights(x, [c, "p_book"], *FIT)
        x[f"r_{c}"] = apply_weights(x, [c, "p_book"], wb)
        cols[f"{name}, refitted"] = f"r_{c}"
        print(f"| {name} | Dec 2023 to Jun 2024 | {wb[0]:.2f} | {wb[1]:.2f} |")
    for name, c in OURS.items():
        wb = fit_weights(x, [c, "p_book"], *RECENT_FIT)
        x[f"y_{c}"] = apply_weights(x, [c, "p_book"], wb)
        recent[f"{name}, fitted Feb 2025 to Jan 2026"] = f"y_{c}"
        print(f"| {name} | Feb 2025 to Jan 2026 | {wb[0]:.2f} | {wb[1]:.2f} |")

    t = x[x.is_ran.astype(bool).values].reset_index(drop=True)
    print(f"\nField at TAB's first price from May 2023: {t.race_id.nunique():,} races, {len(t):,} runners that ran. "
          f"{(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    print("## 2. Log loss, winners only, races with nothing scratched after the open and a BSP on every runner\n")
    ll_table(t, cols, R50.PERIODS)
    print("\n## 3. The bets\n")
    judge(t, cols, R50.PERIODS)
    rec = (t.date >= "2025-02-01").values
    m0 = R37.rule(t.assign(_pb=t["h_p_x_bet"].fillna(0)), "_pb", 1.3)[0] & rec
    m1 = R37.rule(t.assign(_pb=t["r_p_i_bet"].fillna(0)), "_pb", 1.3)[0] & rec
    print(f"\nSince February 2025 the held blend without Isolynx and the refitted blend with it make {int(m0.sum())} and "
          f"{int(m1.sum())} bets, {int((m0 & m1).sum())} of them the same dog.")

    print("\n## 4. Fitted on February 2025 to January 2026, judged on February 2026 on\n")
    both = {"no Isolynx, 0.54 / 0.67": "h_p_x_bet", "with Isolynx, 0.54 / 0.67": "h_p_i_bet", **recent}
    ll_table(t, both, RECENT)
    print()
    judge(t, both, RECENT)
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 51")
