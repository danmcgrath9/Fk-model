"""Round 58: a judge without the first-tip lean (16 Nov 2026, founder: "Well keep testing and lets get a fucking good
model")

Test 75: the card's edge since February 2025 is GRV's first tip priced long at TAB's open (85 of its 98 bets). The blend
with terms for its leans (first tip, box 1, a weight rise) forecasts better than any blend so far, but BSP rates its
bets lower at every count while the realised results mostly rate them higher. BSP over-rates GRV's first tip (A/E
0.965, then 0.963) and dogs up 0.5 kg or more (0.950, then 0.907), so it is a biased judge of exactly the bets the terms
move. Stated before the run, on round 57's field:

  - BSP corrected: BSP's chances with a term for the first tip and one for a weight rise of 0.5 kg or more (each an
    input whose log is 1 for the group), fitted on one half (May 2023 to January 2025, or since February 2025) on races
    with nothing scratched after the open, and applied to the other half; races without a BSP on every runner get no
    corrected chance
  - its calibration by the two groups, against BSP's, out of the half it was fitted on
  - the card's bets split by first tip, and the six blends of round 57 at 1.3x, on the card's stakes and at the same
    numbers of bets, re-judged by the corrected BSP

    python research/greyhound/topaz_round58.py DIR LABEL    (as round 51)

Counts, sums and rates only: no race, dog or price is printed.
"""
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round36 as R36       # noqa: E402
import topaz_round50 as R50       # noqa: E402
import topaz_round51 as R51       # noqa: E402
import topaz_round52 as R52       # noqa: E402
import topaz_round56 as R56       # noqa: E402
import topaz_round57 as R57       # noqa: E402

HALVES = [("May 2023 to Jan 2025", "2023-05-01", "2025-02-01"), ("Feb 2025 on", "2025-02-01", "2100-01-01")]
COLS = ["p_bsp", "t_tip1", "t_wup"]


def corrected_bsp(t: pd.DataFrame):
    """BSP's chances corrected for its first-tip and weight-rise leans, fitted on one half and applied to the other
    (races with a BSP on every runner only). Returns (the corrected chances, {fitted on: weights})."""
    full = t.p_bsp.notna().groupby(t.race_id.values).transform("all").to_numpy(copy=True)
    x = t[full]
    q = pd.Series(np.nan, index=t.index)
    weights = {}
    for (fname, flo, fhi), (_, alo, ahi) in ((HALVES[0], HALVES[1]), (HALVES[1], HALVES[0])):
        w = R51.fit_weights(x, COLS, flo, fhi)
        weights[fname] = w
        app = R36.in_period(x, alo, ahi)
        if app.any():
            q.loc[x.index[app]] = R51.apply_weights(x[app], COLS, w).values
    return q, weights


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 58, a judge without the first-tip lean\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    if not os.environ.get("WALK_CACHE_USE", "").strip() or not os.environ.get("WALK_ISO_USE", "").strip():
        print("Both saved walks must be named (WALK_CACHE_USE and WALK_ISO_USE): nothing to test")
        return 1
    t, _ = R57.field(d, t0)
    t["q_bsp"], weights = corrected_bsp(t)
    print("\n## 1. The correction, fitted on one half and applied to the other\n\n| fitted on | BSP's power | "
          "first tip | up 0.5 kg or more |\n|---|---|---|---|")
    for fname, w in weights.items():
        print(f"| {fname} | {w[0]:.3f} | x{np.exp(w[1]):.3f} | x{np.exp(w[2]):.3f} |")
    have = t.q_bsp.notna()
    print(f"\nField at TAB's first price from May 2023: {t.race_id.nunique():,} races, {len(t):,} runners that ran; "
          f"a corrected BSP for {have.mean():.1%} of them. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    clean = t[(t.n_later == 0).values & t.q_bsp.notna().groupby(t.race_id.values).transform("all").values]
    gs = R56.runner_groups(clean)
    print("Calibration, A/E (z), May 2023 to Jan 2025 / since Feb 2025 (each half judged by the fit on the other):\n")
    R56.scan(clean, {k: gs[k] for k in ("GRV's tip", "the weight change")},
             {"BSP": "p_bsp", "BSP corrected": "q_bsp", "the card's blend": "h_p_x_bet"})
    tq = t.assign(p_bsp=t.q_bsp)
    for title, tt in (("by BSP", t), ("by the corrected BSP", tq)):
        print(f"\n## 2. The card's bets split by GRV's first tip, {title}\n")
        R57.split_bets(tt, "h_p_x_bet")
    print("\n## 3. The six blends, judged by the corrected BSP (the realised results are the same as Test 75's)\n")
    R51.judge(tq, R57.BLENDS, R50.PERIODS)
    print("\n## 4. The best N candidates by edge, judged by the corrected BSP, flat\n")
    R52.ladder(tq, {"since Feb 2025": R36.in_period(tq, R52.SINCE, None)}, R52.NS, R57.BLENDS)
    print()
    R52.ladder(tq, {h: R36.in_period(tq, lo, hi) for h, lo, hi in R52.HALVES}, tuple(n // 2 for n in R52.NS),
               R57.BLENDS)
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 58")
