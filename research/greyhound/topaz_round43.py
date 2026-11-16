"""Round 43: the rule at 1.1x, 1.2x and 1.3x, and the BSP correction shrunk halfway (16 Nov 2026, founder: "Well keep
testing and lets get a fucking good model")

Test 60: the card's +47% at 1.3x sits on one rung of 84 bets that beat even what the held blend claimed for it. From
1.1 up, both the held blend (1,144 bets, about +7.5% flat) and the correction on BSP (1,394 bets, about +6.2%) make as
many flat units as the card from twelve to fourteen times the bets. The correction overclaims its biggest edges. 1.1
was read off that ladder, so it is a lead. Here, stated before the run, on every race from February 2025 at TAB's
first price after TAB's deduction, by period:

  A. the card's rule (its band, its stakes: Kelly on half ours, half TAB's book) at 1.1x, 1.2x and 1.3x, with Kelly
     units, months in profit, the worst drawdown and the longest losing run
  B. flat, every candidate in the band whose edge (TAB's first price x the model's chance) is at the ratio or over
  C. the edge ladder for the one fix for the overclaiming: the BSP correction shrunk halfway back to the held blend
     (the geometric mean of the two over the runners that ran, a dog scratched after the open keeping the blend's
     chance)

for three models: the held blend, the correction on BSP, and that correction shrunk halfway. The corrections are read
back from the walk cache (round 42 saved them).

    python research/greyhound/topaz_round43.py DIR LABEL    (as round 42)

Counts, sums and rates only: no race, dog or price is printed.
"""
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round9 as R9         # noqa: E402
import topaz_round33 as R33       # noqa: E402
import topaz_round36 as R36       # noqa: E402
import topaz_round37 as R37       # noqa: E402
import topaz_round41 as R41       # noqa: E402
import topaz_round42 as R42       # noqa: E402
import topaz_v1 as V1             # noqa: E402

RATIOS = (1.1, 1.2, 1.3)
PERIODS = [("Feb 2025 to Jan 2026", "2025-02-01", "2026-02-01"), ("Feb 2026 on", "2026-02-01", None),
           ("Feb 2025 on", "2025-02-01", None)]
MODELS = {"blend, held": "pb6", "correction on BSP": "pq", "correction on BSP, halfway to the held blend": "ps"}


def halfway(t: pd.DataFrame, a: str = "pb6", b: str = "pq") -> np.ndarray:
    """The geometric mean of two models' chances, renormalised within each race to the share a holds there (t holds
    the runners that ran, so that share is what is left after the dogs scratched later)."""
    g = t.race_id.values
    geo = pd.Series(np.sqrt(t[a].values * t[b].values))
    share = t[a].groupby(g).transform("sum").values
    return (geo / geo.groupby(g).transform("sum").values).values * share


def flat_candidates(t: pd.DataFrame, col: str, ratio: float):
    """Every candidate in the card's band with an edge at the ratio or over, staked one unit each."""
    m, e, paid = R42.candidates(t, col)
    return m & (e >= ratio), paid, np.ones(len(t))


def rule_rows(t: pd.DataFrame, models: dict, flat: bool) -> None:
    price = t.price.values.astype(float)
    if flat:
        print("| period | model | ratio | bets | winners | A/E vs the price taken | z | flat ROI | flat units "
              "| months in profit | BSP under the price paid | mean log(price paid / BSP) |\n"
              "|---|---|---|---|---|---|---|---|---|---|---|---|")
    else:
        print("| period | model | ratio | bets | winners | A/E vs the price taken | z | flat ROI | Kelly ROI | Kelly units "
              "| months in profit | worst drawdown, Kelly units | longest losing run | BSP under the price paid "
              "| mean log(price paid / BSP) |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for pname, a, b in PERIODS:
        p = R36.in_period(t, a, b)
        for name, col in models.items():
            for r in RATIOS:
                m, paid, u = flat_candidates(t, col, r) if flat else R37.rule(t, col, r)
                x = m & p
                s = R9.summary(t, x, paid, u, price)
                if not s["n"]:
                    print(f"| {pname} | {name} | {r}x | 0 |" + " |" * (8 if flat else 11))
                    continue
                _, under, lr = R37.clv(t, x, paid)
                cells = [pname, name, f"{r}x", f"{s['n']:,}", f"{s['w']:,}", f"{s['ae']:.3f}",
                         f"{R37.z_at_price(t.won.values[x], price[x]):+.1f}", f"{s['flat']:+.1%}"]
                if flat:
                    cells += [f"{s['flat'] * s['n']:+,.0f}", R37.months_in_profit(t, x, paid, u)]
                else:
                    cells += [f"{s['kroi']:+.1%}", f"{s['kunits']:+,.0f}", R37.months_in_profit(t, x, paid, u),
                              f"{s['dd']:,.0f}", str(s["run"])]
                cells += ["" if np.isnan(under) else f"{under:.1%}", "" if np.isnan(lr) else f"{lr:+.3f}"]
                print("| " + " | ".join(cells) + " |")


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 43, the rule at 1.1x, 1.2x and 1.3x, and the BSP correction shrunk halfway\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    a, X = R41.ours(d, t0)
    fr = R33.load(bdir, times=(0,))
    x = R33.at_time(a, fr, 0)
    x["pb6"] = V1.blend(["p_x_bet", "p_book"], x, np.asarray(R41.FIXED))[1]
    ok = pd.Series((x.price > 1).values).groupby(x.race_id.values).transform("all").values
    x = x[ok].reset_index(drop=True)
    R, XR = R41.ran_field(x, X)
    x = R42.corrections(x, R, XR, t0)
    ran = x.is_ran.astype(bool).values
    t = x[ran & (x.date >= R42.SINCE).values].reset_index(drop=True)
    whole = t.pq.notna().groupby(t.race_id.values).transform("all").values
    t = t[whole].reset_index(drop=True)
    t["ps"] = halfway(t)
    print(f"Every race from February 2025 at TAB's first price, priced by all three: {t.race_id.nunique():,} races, "
          f"{len(t):,} runners that ran. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    print("## A. The card's rule (its band, its Kelly stakes) at 1.1x, 1.2x and 1.3x\n")
    rule_rows(t, MODELS, flat=False)
    print("\n## B. Flat, every candidate in the band with an edge at the ratio or over\n")
    rule_rows(t, MODELS, flat=True)
    print("\n## C. The edge ladder for the BSP correction shrunk halfway (Feb 2025 on)\n")
    R42.ladder(t, {"correction on BSP, halfway to the held blend": "ps"})
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 43")
