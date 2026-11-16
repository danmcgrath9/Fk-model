"""Round 45: the card's rule at 1.2x and its stakes, judged two ways (16 Nov 2026, founder: "Well keep testing and lets
get a fucking good model")

Test 62: judged by BSP, which is fair to the held blend's bets from 1.1 to 1.5, the held blend's edge rises smoothly.
It is worth +4% a bet at 1.1 to 1.2, +14% at 1.2 to 1.3 and +35% at 1.3 to 1.5. The card bets from 1.3. The card's
Kelly stake is on half the model's chance and half TAB's book, so it stakes little or nothing under about 1.2x. Stated
before the run, for the held blend and the BSP correction shrunk halfway (Test 61), on every race from February 2025
at TAB's first price after TAB's deduction, realised and judged by BSP (price paid x BSP's chance - 1):

  - the card's rule at 1.3x and 1.2x, and the bets 1.2x adds (at 1.2x and not at 1.3x) on their own
  - two stakes: the card's (Kelly on half the model, half TAB's book), and Kelly on the model's own chance, with the
    card's multiplier (75) and cap (4 units)

    python research/greyhound/topaz_round45.py DIR LABEL    (as round 44; the corrections come from the walk cache)

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
import topaz_round43 as R43       # noqa: E402
import topaz_v1 as V1             # noqa: E402

MODELS = {"blend, held": "pb6", "correction on BSP, halfway": "ps"}
STAKES = ("the card's stake", "Kelly on the model")


def bets(t: pd.DataFrame, col: str, ratio: float, stake: str):
    """The card's rule at a ratio (our odds 2 to 15, TAB's first price at the ratio x our odds or over), with the
    price paid after TAB's deduction and the stake: the card's (Kelly on half the model, half TAB's book) or Kelly
    on the model's own chance, both x75 and capped at 4 units, and only where the stake is positive."""
    if stake == STAKES[0]:
        return R37.rule(t, col, ratio)
    p = t[col].values.astype(float)
    price = t.price.values.astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        fair = 1 / p
    m = np.isfinite(price) & (price > 1) & np.isfinite(fair) & (price >= ratio * fair) & (fair >= 2) & (fair < 15)
    # sized on TAB's price before any deduction, as the card is: a later scratching is not known when the bet is struck
    f = (p * price - 1) / np.maximum(price - 1, 1e-9)
    u = np.clip(R9.KELLY_X * np.nan_to_num(f), 0, R9.CAP)
    return m & (u > 0), 1 + (price - 1) * (1 - t.ded.fillna(0).values), u


def judged(t: pd.DataFrame, x: np.ndarray, paid: np.ndarray, u: np.ndarray) -> dict:
    """Bets in x with a BSP: stake, realised units, BSP's units, and BSP's expected winners against the actual."""
    y = x & t.p_bsp.notna().values
    n = int(y.sum())
    if not n:
        return dict(n=0)
    q, won, s = t.p_bsp.values[y], t.won.values[y].astype(float), u[y]
    real = (s * np.where(won == 1, paid[y] - 1, -1.0)).sum()
    bsp = (s * (paid[y] * q - 1)).sum()
    return dict(n=n, w=int(won.sum()), e=float(q.sum()), staked=float(s.sum()), real=float(real), bsp=float(bsp))


def table(t: pd.DataFrame) -> None:
    print("| period | model | stake | bets | bets with a BSP | winners | BSP's expected winners | units staked "
          "| realised units | realised per unit | BSP's units | BSP's return per unit |\n"
          "|---|---|---|---|---|---|---|---|---|---|---|---|")
    for pname, a, b in R43.PERIODS:
        p = R36.in_period(t, a, b)
        for name, col in MODELS.items():
            for stake in STAKES:
                m13, paid, u13 = bets(t, col, 1.3, stake)
                m12, _, u12 = bets(t, col, 1.2, stake)
                for lab, x, u in (("1.3x", m13 & p, u13), ("1.2x", m12 & p, u12),
                                  ("1.2x, not 1.3x", m12 & ~m13 & p, u12)):
                    s = judged(t, x, paid, u)
                    if not s["n"]:
                        print(f"| {pname} | {name} | {stake}, {lab} | {int(x.sum())} | 0 |" + " |" * 7)
                        continue
                    print(f"| {pname} | {name} | {stake}, {lab} | {int(x.sum()):,} | {s['n']:,} | {s['w']:,} | "
                          f"{s['e']:,.1f} | {s['staked']:,.0f} | {s['real']:+,.1f} | {s['real'] / s['staked']:+.1%} | "
                          f"{s['bsp']:+,.1f} | {s['bsp'] / s['staked']:+.1%} |")


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 45, the card's rule at 1.2x and its stakes, judged two ways\n")
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
    t = t[t.pq.notna().groupby(t.race_id.values).transform("all").values].reset_index(drop=True)
    t["ps"] = R43.halfway(t)
    print(f"Every race from February 2025 at TAB's first price: {t.race_id.nunique():,} races, {len(t):,} runners "
          f"that ran. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    table(t)
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 45")
