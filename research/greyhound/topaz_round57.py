"""Round 57: the card's bets by the blend's leans, and the blend with terms for them (16 Nov 2026, founder: "Well keep
testing and lets get a fucking good model")

Test 74: the card's blend has two leans in both halves. GRV's first tip wins less than it says (A/E 0.943, then 0.962),
which ours and BSP share and TAB's first price does not. Box 1 wins less than it says (0.955, then 0.959), which TAB's
first book has and BSP and ours with Isolynx do not. A third, dogs up 0.5 kg or more, is in every forecast since
February 2025, BSP included. Stated before the run, on round 50's prices (both saved walks read by name):

  1. the card's bets at 1.3x and the candidates from 1.1x, split by first tip or not, box 1 or not, and up 0.5 kg or
     more or not: bets, winners, BSP's expected winners, realised flat ROI and BSP's return per bet, in each half
  2. the blend with a term for each of the three (each an input whose log is 1 for the group and 0 otherwise), fitted
     with the blend's two weights on Test 51's window and held, for ours without and with Isolynx; against the card and
     the same blends refitted without the terms
  3. judged as Test 72 was: log loss, calibration by the three groups (both halves), the card's rule at 1.3x, BSP's
     verdict and the card's stakes, and the same numbers of bets since February 2025

BSP shares the first-tip lean, so its verdict on first tips is a few points too kind; the realised results sit beside it.

    python research/greyhound/topaz_round57.py DIR LABEL    (as round 51)

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
import topaz_round43 as R43       # noqa: E402
import topaz_round44 as R44       # noqa: E402
import topaz_round50 as R50       # noqa: E402
import topaz_round51 as R51       # noqa: E402
import topaz_round52 as R52       # noqa: E402
import topaz_round55 as R55       # noqa: E402
import topaz_round56 as R56       # noqa: E402

TERMS = {"first tip": "t_tip1", "box 1": "t_box1", "up 0.5 kg or more": "t_wup"}
PERIODS = [("May 2023 to Jan 2025", "2023-05-01", "2025-02-01"), ("Feb 2025 on", "2025-02-01", None)]
BLENDS = {"no Isolynx, 0.54 / 0.67 (the card)": "h_p_x_bet", "no Isolynx, refitted": "r_p_x_bet",
          "no Isolynx, refitted with the terms": "k_p_x_bet", "with Isolynx, 0.54 / 0.67": "h_p_i_bet",
          "with Isolynx, refitted": "r_p_i_bet", "with Isolynx, refitted with the terms": "k_p_i_bet"}


def term_columns(t: pd.DataFrame) -> pd.DataFrame:
    """The three terms as chance-like inputs: e for the group, 1 otherwise (a missing value is not the group)."""
    t = t.copy()
    t["t_tip1"] = np.where(R55.col(t, "tip_rank").values == 1, np.e, 1.0)
    t["t_box1"] = np.where(R55.col(t, "box").values == 1, np.e, 1.0)
    t["t_wup"] = np.where(R55.col(t, "weight_change").values >= 0.5, np.e, 1.0)
    return t


def field(d: str, t0: float):
    df = R51.named_walks(d, t0)
    fr = R33.load(os.environ["BETWATCH_DIR"], times=(0,))
    x = R33.at_time(df, fr, 0)
    ran = x.is_ran.astype(bool).values
    x["p_i_bet"] = np.where(ran, x.p_i * (1 - x.s_later.fillna(0)), x.p_book)
    ok = pd.Series((x.price > 1).values).groupby(x.race_id.values).transform("all").values
    x = term_columns(x[ok].reset_index(drop=True))
    weights = {}
    for name, c in R51.OURS.items():
        x[f"h_{c}"] = R51.apply_weights(x, [c, "p_book"], R50.FIXED)
        w2 = R51.fit_weights(x, [c, "p_book"], *R51.FIT)
        x[f"r_{c}"] = R51.apply_weights(x, [c, "p_book"], w2)
        cols = [c, "p_book"] + list(TERMS.values())
        w5 = R51.fit_weights(x, cols, *R51.FIT)
        x[f"k_{c}"] = R51.apply_weights(x, cols, w5)
        weights[name] = (w2, w5)
    return x[x.is_ran.astype(bool).values].reset_index(drop=True), weights


def split_bets(t: pd.DataFrame, col: str) -> None:
    """The blend's bets at 1.3x and candidates from 1.1x, split by each group, in each half."""
    groups = {"first tip": R55.col(t, "tip_rank").values == 1, "box 1": R55.col(t, "box").values == 1,
              "up 0.5 kg or more": R55.col(t, "weight_change").values >= 0.5}
    m13, paid, _ = R37.rule(t, col, 1.3)
    m11 = R43.flat_candidates(t, col, 1.1)[0]
    print("| period | rule | group | in it | bets | " + R44.HEAD + " |\n|" + "---|" * 13)
    for pname, lo, hi in PERIODS:
        p = R36.in_period(t, lo, hi)
        for rname, m in (("1.3x, the card's rule", m13), ("flat from 1.1x", m11)):
            for gname, g in groups.items():
                for inside in (True, False):
                    x = m & p & (g if inside else ~g)
                    print(f"| {pname} | {rname} | {gname} | {'yes' if inside else 'no'} | {int(x.sum()):,} | "
                          + " | ".join(R44.cells(R44.judged(t, x, paid))) + " |")


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 57, the card's bets by the blend's leans, and the blend with terms for them\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    if not os.environ.get("WALK_CACHE_USE", "").strip() or not os.environ.get("WALK_ISO_USE", "").strip():
        print("Both saved walks must be named (WALK_CACHE_USE and WALK_ISO_USE): nothing to test")
        return 1
    t, weights = field(d, t0)
    print("\n## 1. The weights, fitted on Dec 2023 to Jun 2024 and held (each term as the factor on a dog's chance)\n")
    print("| ours | blend | ours | TAB | " + " | ".join(TERMS) + " |\n|" + "---|" * (4 + len(TERMS)))
    for name, (w2, w5) in weights.items():
        print(f"| {name} | refitted | {w2[0]:.2f} | {w2[1]:.2f} |" + " |" * len(TERMS))
        print(f"| {name} | refitted with the terms | {w5[0]:.2f} | {w5[1]:.2f} | "
              + " | ".join(f"x{np.exp(v):.3f}" for v in w5[2:]) + " |")
    clean = t[(t.n_later == 0).values]
    full = clean.p_bsp.notna().groupby(clean.race_id.values).transform("all").to_numpy(copy=True)
    clean = clean[full].reset_index(drop=True)
    print(f"\nField at TAB's first price from May 2023: {t.race_id.nunique():,} races, {len(t):,} runners that ran. "
          f"{(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    print("## 2. The card's bets, split by the leans\n")
    split_bets(t, "h_p_x_bet")
    print("\n## 3. Log loss on the winners (lower is better)\n")
    R51.ll_table(t, BLENDS, R50.PERIODS)
    print("\nCalibration by the three groups, A/E (z), May 2023 to Jan 2025 / since Feb 2025:\n")
    gs = R56.runner_groups(clean)
    sub = {k: gs[k] for k in ("GRV's tip", "box", "the weight change")}
    R56.scan(clean, sub, {**BLENDS, "BSP": "p_bsp"})
    print("\n## 4. The bets\n")
    R51.judge(t, BLENDS, R50.PERIODS)
    print("\n## 5. The best N candidates by edge since February 2025, judged by BSP, flat\n")
    R52.ladder(t, {"since Feb 2025": R36.in_period(t, R52.SINCE, None)}, R52.NS, BLENDS)
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 57")
