"""Round 54: the blend with a term for the tracked dogs (16 Nov 2026, founder: "Well keep testing and lets get a fucking
good model")

Test 71: in a race where some runners have a tracked run before it and some do not, TAB's first price under-rates the
tracked dogs and over-rates the rest (A/E 1.041 and 0.957 from May 2023 to January 2025, 1.018 and 0.973 since). Ours
without Isolynx and the card's blend share the lean. Ours with Isolynx does not (0.999 and 1.001, then 1.011 and 0.984),
but the blend with it keeps about half of TAB's lean, then most of it, because TAB carries 0.67 of it. Stated before
the run, on round 50's prices (both saved walks read by name):

  - a third input in the blend: 1 for a runner with a tracked run before the race, 0 for one without, so its weight
    shifts chance toward the tracked dogs in a mixed race and changes nothing in a race where every runner is tracked
    or none is
  - fitted with the two weights on Test 51's window (December 2023 to June 2024, races with nothing scratched after the
    open) and held, for ours without and with Isolynx; against the same blends refitted without the term (Test 69) and
    the two at 0.54 / 0.67
  - judged by log loss by period and by race make-up, calibration in the mixed races (Test 71's table), the card's rule
    at 1.3x, BSP's verdict flat from 1.1x and 1.3x and on the card's stakes, and at the same numbers of bets as Test 70
    (since February 2025, and in each half at half the counts). BSP leans the same way slightly (1.013 and 0.985, then
    1.008 and 0.989), so its verdict may under-credit the tracked dogs a little; the realised results sit beside it

    python research/greyhound/topaz_round54.py DIR LABEL    (as round 51)

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
import topaz_round50 as R50       # noqa: E402
import topaz_round51 as R51       # noqa: E402
import topaz_round52 as R52       # noqa: E402
import topaz_round53 as R53       # noqa: E402


def tracked_term(iso_runs: pd.Series) -> np.ndarray:
    """The blend's third input, as a chance-like column: its log is 1 for a runner with a tracked run before the race
    and 0 for one without (a missing count is no tracked run)."""
    return np.where(iso_runs.fillna(0).values > 0, np.e, 1.0)


def field(d: str, t0: float):
    """Round 52's field with the six blends; (runners that ran, the weights fitted)."""
    df = R51.named_walks(d, t0)
    fr = R33.load(os.environ["BETWATCH_DIR"], times=(0,))
    x = R33.at_time(df, fr, 0)
    ran = x.is_ran.astype(bool).values
    x["p_i_bet"] = np.where(ran, x.p_i * (1 - x.s_later.fillna(0)), x.p_book)
    ok = pd.Series((x.price > 1).values).groupby(x.race_id.values).transform("all").values
    x = x[ok].reset_index(drop=True)
    x["trk"] = tracked_term(x.iso_runs)
    weights = {}
    for name, c in R51.OURS.items():
        x[f"h_{c}"] = R51.apply_weights(x, [c, "p_book"], R50.FIXED)
        w2 = R51.fit_weights(x, [c, "p_book"], *R51.FIT)
        x[f"r_{c}"] = R51.apply_weights(x, [c, "p_book"], w2)
        w3 = R51.fit_weights(x, [c, "p_book", "trk"], *R51.FIT)
        x[f"k_{c}"] = R51.apply_weights(x, [c, "p_book", "trk"], w3)
        weights[name] = (w2, w3)
    return x[x.is_ran.astype(bool).values].reset_index(drop=True), weights


BLENDS = {"no Isolynx, 0.54 / 0.67 (the card)": "h_p_x_bet", "with Isolynx, 0.54 / 0.67": "h_p_i_bet",
          "no Isolynx, refitted": "r_p_x_bet", "with Isolynx, refitted": "r_p_i_bet",
          "no Isolynx, refitted with the term": "k_p_x_bet", "with Isolynx, refitted with the term": "k_p_i_bet"}


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 54, the blend with a term for the tracked dogs\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    if not os.environ.get("WALK_CACHE_USE", "").strip() or not os.environ.get("WALK_ISO_USE", "").strip():
        print("Both saved walks must be named (WALK_CACHE_USE and WALK_ISO_USE): nothing to test")
        return 1
    t, weights = field(d, t0)
    if "iso_runs" not in t:
        print("No tracked-run count (iso_runs): nothing to test")
        return 1
    print("\n## 1. The weights, fitted on Dec 2023 to Jun 2024 and held\n\n| ours | blend | ours | TAB | the term "
          "| a tracked dog's chance in a mixed race, times |\n|---|---|---|---|---|---|")
    for name, (w2, w3) in weights.items():
        print(f"| {name} | refitted | {w2[0]:.2f} | {w2[1]:.2f} | | |")
        print(f"| {name} | refitted with the term | {w3[0]:.2f} | {w3[1]:.2f} | {w3[2]:+.3f} | {np.exp(w3[2]):.3f} |")
    clean = t[(t.n_later == 0).values]
    full = clean.p_bsp.notna().groupby(clean.race_id.values).transform("all").to_numpy(copy=True)
    clean = clean[full].reset_index(drop=True)
    print(f"\nField at TAB's first price from May 2023: {t.race_id.nunique():,} races, {len(t):,} runners that ran; "
          f"{clean.race_id.nunique():,} races with nothing scratched after the open and a BSP on every runner. "
          f"{(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    models = {"TAB's first book": "p_book", **BLENDS, "BSP": "p_bsp"}
    mk = R53.make_up(clean)
    print("## 2. Log loss on the winners (lower is better)\n")
    R51.ll_table(t, BLENDS, R50.PERIODS)
    print("\nBy race make-up:\n")
    R53.ll_make_up(clean, mk, models)
    print("\n## 3. Winners against the chances given (the mixed-race rows are the ones that move)\n")
    R53.calibration(clean, mk, models)
    print("\n## 4. The bets\n")
    R51.judge(t, BLENDS, R50.PERIODS)
    print("\n## 5. The best N candidates by edge, judged by BSP, flat\n")
    since = R36.in_period(t, R52.SINCE, None)
    R52.ladder(t, {"since Feb 2025": since}, R52.NS, BLENDS)
    print()
    R52.ladder(t, {h: R36.in_period(t, lo, hi) for h, lo, hi in R52.HALVES}, tuple(n // 2 for n in R52.NS), BLENDS)
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 54")
