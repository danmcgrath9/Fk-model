"""Round 76: the order sheet with no TAB price in it (18 Nov 2026, founder: "whats our profit on back test without
tabs price")

An order sheet loaded into BetMatic before TAB opens fires within a couple of seconds of the open, at TAB's first
price, if that price is at or above the sheet's minimum (BetMatic's market-open bets, betmatic/API_NOTES.md). A sheet
built from our own price alone needs nothing from TAB: each dog's minimum is a multiple of our own fair price, known
the night before. Stated before the run, February 2025 on, bets with a corrected BSP, every bet at TAB's first price
after its deduction:

  - the sheet from our own price, with Isolynx and without (round 62's p_i_bet and p_x_bet: our chance over TAB's
    field at its first price): bet when TAB's first price is at least 1.1x, 1.2x, 1.3x, 1.5x or 2x our fair price,
    our fair price $2 to $15, flat; and the 2-point margin on our own chance, a quarter of Kelly
  - beside them, the two that need TAB's opening book: Test 88's fit at the 2-point margin, a quarter of Kelly, and
    the corrected blend (c_q) at 1.1x, flat
  - one Kelly scale for every quarter-Kelly row: Test 88's 2-point bets' mean stake from February 2025 is one unit
  - bets, bets a month, units staked, the corrected BSP's return per unit staked (SE) and units, realised units, the
    deepest fall and the losing months, by half

    python research/greyhound/topaz_round76.py DIR LABEL    (as round 75)

Counts, sums and rates only: no race, dog or price is printed.
"""
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round58 as R58       # noqa: E402
import topaz_round62 as R62       # noqa: E402
import topaz_round63 as R63       # noqa: E402
import topaz_round67 as R67       # noqa: E402
import topaz_round68 as R68       # noqa: E402
import topaz_round73 as R73       # noqa: E402

SHEET_RATIOS = (1.1, 1.2, 1.3, 1.5, 2.0)
OWN = {"ours with Isolynx": "p_i_bet", "ours without Isolynx": "p_x_bet"}


def row(t, tq, m, paid, u, months) -> str:
    """bets | a month | units staked | corrected BSP per unit staked (SE) | corrected BSP units | realised units |
    deepest fall, realised | losing months"""
    s = R68.staked(tq, m, paid, u)
    if not s["n"]:
        return "0 | | | | | | |"
    fall, lose, nmon = R68.deepest_fall(t, m & tq.p_bsp.notna().values, paid, u)
    return (f"{s['n']:,} | {s['n'] / months:.1f} | {s['staked']:,.0f} | {s['per']:+.1%} ({s['se']:.1%}) | "
            f"{s['units']:+,.1f} | {s['real']:+,.1f} | {fall:,.1f} | {lose} of {nmon}")


def main(d, label):
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 76, the order sheet with no TAB price in it\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    x, _, _, _ = R62.field(d, t0)
    has88 = R67.read_saved(x, "r70", "c_f")
    hascb = R63.read_corrections(x)
    t = x[x.is_ran.astype(bool).values].reset_index(drop=True)
    t["q_bsp"], _ = R58.corrected_bsp(t)
    tq = t.assign(p_bsp=t.q_bsp)
    since = R63.R36.in_period(t, R63.SINCE, None)
    paid = R68.paid_price(t)
    print(f"Runners that ran at TAB's first price: {len(t):,} in {t.race_id.nunique():,} races. Test 88's fit "
          f"{'in' if has88 else 'NOT in'} the walk cache; the corrected blend {'in' if hascb else 'NOT in'} it. "
          f"{(time.monotonic() - t0) / 60:.0f} minutes in.\n")

    scale = None
    if has88:
        p88 = R67.model_chance(t, "c_f")
        m88 = R68.margin_bets(t, p88, 0.02)
        raw = R73.raw_kelly(p88, paid)
        scale = raw[m88 & since].mean()
    flat = np.ones(len(t))
    rules = []
    for nm, col in OWN.items():
        if col not in t:
            continue
        p = t[col].values.astype(float)
        for r in SHEET_RATIOS:
            rules.append((f"the sheet: {nm}, {r:g}x, flat", R63.bets(t, col, t.price.values, r)[0], flat))
        if scale:
            u = R73.raw_kelly(p, paid) / scale
            rules.append((f"the sheet: {nm}, 2 points, quarter Kelly", R68.margin_bets(t, p, 0.02) & (u > 0), u))
    if has88:
        u = raw / scale
        rules.append(("needs TAB's book: Test 88's fit, 2 points, quarter Kelly", m88 & (u > 0), u))
    if hascb:
        rules.append(("needs TAB's book: the corrected blend, 1.1x, flat", R63.bets(t, "c_q", t.price.values, 1.1)[0],
                      flat))
    periods = [("Feb 2025 on", R63.SINCE, None)] + R63.HALVES
    print("| rule | period | bets | a month | units staked | corrected BSP per unit staked (SE) | corrected BSP units | "
          "realised units | deepest fall, realised | losing months |\n|" + "---|" * 10)
    for nm, m, u in rules:
        for lab, lo, hi in periods:
            per = R63.R36.in_period(t, lo, hi)
            print(f"| {nm} | {lab} | " + row(t, tq, m & per, paid, u, R67.months_in(t, per)) + " |")
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 76")
