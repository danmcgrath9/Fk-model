"""Round 44: the closing line as the judge (16 Nov 2026, founder: "Well keep testing and lets get a fucking good
model")

Test 61: at 22 months the realised results cannot rank the models. A rung of 235 bets has a standard error of about
13 points of flat ROI, and every model's ladder swings that much from rung to rung. The closing line rises smoothly
with the edge for every model. BSP is the best forecaster in every test (log loss 1.5065 since February 2025, against
the held blend's 1.5686), so the price paid against BSP's chance is a far less noisy measure of what each bet was
worth than whether it won:

    BSP's return = price paid after TAB's deduction x BSP's chance - 1

Stated before the run, on every race from February 2025 at TAB's first price, for bets with a BSP:

  1. is BSP a fair judge out here? In each rung of each model's edge ladder, BSP's expected winners (the sum of its
     chances) against the actual winners, with z. If BSP is fair in the tail, they agree
  2. the edge ladder judged by BSP: BSP's return per bet with its standard error, and in units, beside the realised
     flat ROI, for the held blend, both corrections and the BSP correction shrunk halfway (Test 61)
  3. the rules judged by BSP, by period: flat at 1.0x, 1.1x, 1.2x and 1.3x, and the card's rule (its Kelly stakes) at
     1.3x, for the held blend, the BSP correction and the shrunk correction

    python research/greyhound/topaz_round44.py DIR LABEL    (as round 43; the corrections come from the walk cache)

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
import topaz_round41 as R41       # noqa: E402
import topaz_round42 as R42       # noqa: E402
import topaz_round43 as R43       # noqa: E402
import topaz_v1 as V1             # noqa: E402

LADDER_MODELS = {"blend, held": "pb6", "correction on the winners": "pw", "correction on BSP": "pq",
                 "correction on BSP, halfway": "ps"}
RULE_MODELS = {"blend, held": "pb6", "correction on BSP": "pq", "correction on BSP, halfway": "ps"}
RATIOS = (1.0, 1.1, 1.2, 1.3)


def judged(t: pd.DataFrame, x: np.ndarray, paid: np.ndarray, u: np.ndarray = None) -> dict:
    """The bets in x that have a BSP: winners, BSP's expected winners and z, the realised flat ROI, and BSP's return
    per bet (mean of price paid x BSP's chance - 1) with its standard error, flat and, given stakes u, staked."""
    y = x & t.p_bsp.notna().values
    n = int(y.sum())
    if not n:
        return dict(n=0)
    q = t.p_bsp.values[y].astype(float)
    won = t.won.values[y].astype(float)
    v = paid[y] * q - 1
    var = (q * (1 - q)).sum()
    out = dict(n=n, w=int(won.sum()), e=float(q.sum()),
               z=float((won.sum() - q.sum()) / np.sqrt(var)) if var > 0 else np.nan,
               flat=float(np.where(won == 1, paid[y] - 1, -1.0).mean()), bsp=float(v.mean()),
               se=float(v.std(ddof=1) / np.sqrt(n)) if n > 1 else np.nan, units=float(v.sum()))
    if u is not None:
        s = u[y]
        out.update(kbsp=float((s * v).sum() / s.sum()) if s.sum() > 0 else np.nan, kunits=float((s * v).sum()),
                   kreal=float((s * np.where(won == 1, paid[y] - 1, -1.0)).sum()))
    return out


def cells(s: dict) -> list:
    if not s["n"]:
        return ["0"] + [""] * 7
    return [f"{s['n']:,}", f"{s['w']:,}", f"{s['e']:,.1f}", f"{s['z']:+.1f}", f"{s['flat']:+.1%}",
            f"{s['bsp']:+.1%}", f"{s['se']:.1%}", f"{s['units']:+,.1f}"]


HEAD = ("bets with a BSP | winners | BSP's expected winners | z | realised flat ROI | BSP's return per bet | "
        "its standard error | BSP's return, units")


def ladder(t: pd.DataFrame, models: dict) -> None:
    print("| model | edge | " + HEAD + " |\n|---|---|---|---|---|---|---|---|---|---|")
    for name, col in models.items():
        m, e, paid = R42.candidates(t, col)
        for lo, hi in zip(R42.LADDER[:-1], R42.LADDER[1:]):
            band = f"under {hi}" if lo == 0 else (f"{lo} and over" if np.isinf(hi) else f"{lo} to {hi}")
            print(f"| {name} | {band} | " + " | ".join(cells(judged(t, m & (e >= lo) & (e < hi), paid))) + " |")


def rules(t: pd.DataFrame, models: dict) -> None:
    print("| period | model | rule | " + HEAD + " |\n|---|---|---|---|---|---|---|---|---|---|---|")
    for pname, a, b in R43.PERIODS:
        p = R36.in_period(t, a, b)
        for name, col in models.items():
            for r in RATIOS:
                m, paid, _ = R43.flat_candidates(t, col, r)
                print(f"| {pname} | {name} | flat, {r}x | " + " | ".join(cells(judged(t, m & p, paid))) + " |")


def card(t: pd.DataFrame, models: dict) -> None:
    print("| period | model | bets with a BSP | Kelly units staked | realised Kelly units | BSP's return, Kelly units "
          "| BSP's return per unit staked |\n|---|---|---|---|---|---|---|")
    for pname, a, b in R43.PERIODS:
        p = R36.in_period(t, a, b)
        for name, col in models.items():
            m, paid, u = R37.rule(t, col, 1.3)
            s = judged(t, m & p, paid, u)
            if not s["n"]:
                print(f"| {pname} | {name} | 0 | | | | |")
                continue
            staked = float(u[m & p & t.p_bsp.notna().values].sum())
            print(f"| {pname} | {name} | {s['n']:,} | {staked:,.0f} | {s['kreal']:+,.1f} | {s['kunits']:+,.1f} | "
                  f"{s['kbsp']:+.1%} |")


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 44, the closing line as the judge\n")
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
          f"that ran, {int(t.p_bsp.notna().sum()):,} with a BSP. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    print("## 1 and 2. The edge ladder judged by BSP, February 2025 on (flat at the price paid after TAB's deduction)\n")
    ladder(t, LADDER_MODELS)
    print("\n## 3. The rules judged by BSP, by period\n")
    rules(t, RULE_MODELS)
    print("\nThe card's rule at 1.3x, on its own Kelly stakes:\n")
    card(t, RULE_MODELS)
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 44")
