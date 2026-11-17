"""Round 69: the margin rule, taken apart and staked (17 Nov 2026, founder: "Keep going, find more winning bets")

Test 86 found the best rule so far: bet when the model's chance is at least 2 points over the chance TAB's first price
(after the deduction) needs. With the longer fit it makes 2,430 bets in 22 months, +12.9% a bet by the corrected BSP
and +305 units, ahead of the card's 1.1x in both halves; and a quarter of Kelly beat flat in both halves on the card's
rules. Stated before the run, the longer fit (corr_r67) and Test 83's model (corr_r65) read from the walk cache:

  - where the 2-point margin's bets sit: by the model's fair price (under $2, $2 to $4, $4 to $8, $8 to $15)
  - the margin around 2 points (1.5, 2, 2.5) and the fair-price cap at 2 points ($10, $15, $20)
  - a margin that grows with the price's own spread: the model's chance at least k x sqrt(need x (1 - need)) over the
    chance needed, k from 0.03 to 0.08
  - the 2-point margin staked by a quarter of Kelly against flat, by half, with the standard error, the luck, the
    deepest fall and the losing months, beside the card's 1.1x and the card with its favourites staked the same way
  - by three months, and in races with nothing scratched after TAB's open

    python research/greyhound/topaz_round69.py DIR LABEL    (as round 67)

Counts, sums and rates only: no race, dog or price is printed.
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round58 as R58       # noqa: E402
import topaz_round62 as R62       # noqa: E402
import topaz_round63 as R63       # noqa: E402
import topaz_round65 as R65       # noqa: E402
import topaz_round67 as R67       # noqa: E402
import topaz_round68 as R68       # noqa: E402

PRICE_BANDS = [("under $2", 0.0, 2.0), ("$2 to $4", 2.0, 4.0), ("$4 to $8", 4.0, 8.0), ("$8 to $15", 8.0, 15.0)]
MARGINS = (0.015, 0.02, 0.025)
CAPS = (10.0, 15.0, 20.0)
SPREADS = (0.03, 0.04, 0.05, 0.06, 0.08)


def spread_bets(t, p: np.ndarray, k: float, band: tuple = (0.0, 15.0)) -> np.ndarray:
    """Bets where the model's chance is at least k x sqrt(need x (1 - need)) over the chance the price paid needs
    (need = 1 / price paid), with the model's fair price in the band."""
    pr = t.price.values.astype(float)
    paid = R68.paid_price(t)
    with np.errstate(divide="ignore", invalid="ignore"):
        fair = 1 / p
        need = 1 / paid
        gap = (p - need) / np.sqrt(need * (1 - need))
    return (np.isfinite(pr) & (pr > 1) & np.isfinite(gap) & (gap >= k - 1e-12)
            & (fair >= band[0]) & (fair < band[1]))


def points(d: float) -> str:
    v = f"{d * 100:g}"
    return f"{v} point" + ("" if v == "1" else "s")


def main(d, label):
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 69, the margin rule, taken apart and staked\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    x, R, _, _ = R62.field(d, t0)
    if not R67.read_saved(x, R65.TAG, "c_m") or not R67.read_saved(x, R67.TAG, "c_l"):
        print("Test 83's model (corr_r65) and the longer fit (corr_r67) must both be in the walk cache: nothing to test")
        return 1
    ran = x.is_ran.astype(bool).values
    t = x[ran].reset_index(drop=True)
    t["q_bsp"], _ = R58.corrected_bsp(t)
    tq = t.assign(p_bsp=t.q_bsp)
    print(f"Runners that ran at TAB's first price: {len(t):,} in {t.race_id.nunique():,} races; both models read "
          f"from the walk cache. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")

    periods = [("Feb 2025 on", R63.SINCE, None)] + R63.HALVES
    paid = R68.paid_price(t)
    pl = R67.model_chance(t, "c_l")
    pm = R67.model_chance(t, "c_m")
    head = ("bets | a month | A/E | realised flat ROI | realised units | corrected BSP per bet (SE) | "
            "corrected BSP units")

    def table(title, rows):
        print(f"{title}\n\n| period | model | rule | {head} |\n|" + "---|" * 10)
        for pname, lo, hi in periods:
            per = R63.R36.in_period(t, lo, hi)
            mo = R67.months_in(t, per)
            for mname, rname, m in rows:
                print(f"| {pname} | {mname} | {rname} | " + R67.cells(t, tq, m & per, paid, mo) + " |")
        print()

    m2 = R68.margin_bets(t, pl, 0.02)
    with np.errstate(divide="ignore"):
        fair = 1 / pl
    table("## 1. Where the 2-point margin's bets sit, the longer fit, by its fair price, flat",
          [("the longer fit", f"2 points, {b}", m2 & (fair >= b0) & (fair < b1)) for b, b0, b1 in PRICE_BANDS])
    table("## 2. The margin around 2 points, and the fair-price cap at 2 points, flat",
          [(mn, f"{points(dd)}, under $15", R68.margin_bets(t, p, dd)) for mn, p in
           (("the longer fit", pl), ("Test 83's model", pm)) for dd in MARGINS]
          + [("the longer fit", f"2 points, under ${c:.0f}", R68.margin_bets(t, pl, 0.02, (0.0, c))) for c in CAPS
             if c != 15.0])
    table("## 3. A margin that grows with the price's spread, k x sqrt(need x (1 - need)), under $15, flat",
          [("the longer fit", f"k {k:g}", spread_bets(t, pl, k)) for k in SPREADS])

    since = R63.R36.in_period(t, R63.SINCE, None)
    m11, _, _ = R68.card_with_favourites(t, "c_l", pl, 1.1, None)
    m11f, _, _ = R68.card_with_favourites(t, "c_l", pl, 1.1, 0.05)
    rules = [("1.1x", m11), ("1.1x + favourites from 5%", m11f), ("2 points", m2)]
    one = np.ones(len(t))
    kel = {r: R67.kelly_stakes(pl, paid, m & since) for r, m in rules}
    print(f"## 4. Flat against a quarter of Kelly, the longer fit (stakes scaled to a mean of one unit from Feb 2025; "
          f"bets with a corrected BSP) ({(time.monotonic() - t0) / 60:.0f} minutes in)\n")
    print("| rule | period | staking | bets | units staked | corrected BSP per unit staked (SE) | corrected BSP units | "
          "realised units | luck in the realised units (SD) | largest stake | deepest fall, realised | losing months |"
          "\n|" + "---|" * 12)
    for rname, m in rules:
        for pname, lo, hi in periods:
            per = R63.R36.in_period(t, lo, hi)
            for sname, u in (("flat", one), ("quarter Kelly", kel[rname])):
                mm = m & per
                s = R68.staked(tq, mm, paid, u)
                if not s["n"]:
                    continue
                fall, lose, nmon = R68.deepest_fall(t, mm & tq.p_bsp.notna().values, paid, u)
                print(f"| {rname} | {pname} | {sname} | {s['n']:,} | {s['staked']:,.0f} | {s['per']:+.1%} "
                      f"({s['se']:.1%}) | {s['units']:+,.1f} | {s['real']:+,.1f} | {s['luck']:,.1f} | "
                      f"{u[mm].max():.1f} | {fall:,.1f} | {lose} of {nmon} |")

    print("\n## 5. By three months, the longer fit: corrected BSP units / realised units (bets with a corrected BSP)\n")
    cols = [("1.1x, flat", m11, one), ("2 points, flat", m2, one), ("2 points, quarter Kelly", m2, kel["2 points"])]
    print("| three months | " + " | ".join(c[0] for c in cols) + " |\n|" + "---|" * (len(cols) + 1))
    for bname, lo, hi in R68.blocks(R63.SINCE, None):
        per = R63.R36.in_period(t, lo, hi)
        cells = []
        for _, m, u in cols:
            s = R68.staked(tq, m & per, paid, u)
            cells.append(f"{s['units']:+,.1f} / {s['real']:+,.1f}" if s["n"] else "no BSP yet")
        print(f"| {bname} | " + " | ".join(cells) + " |")

    c = t[(t.n_later.fillna(0) == 0).values].reset_index(drop=True)
    cq = c.assign(p_bsp=c.q_bsp)
    pc = R67.model_chance(c, "c_l")
    cpaid = R68.paid_price(c)
    per = R63.R36.in_period(c, R63.SINCE, None)
    mo = R67.months_in(c, per)
    print("\n## 6. Races with nothing scratched after TAB's open, the longer fit, flat, Feb 2025 on\n")
    print(f"| rule | {head} |\n|" + "---|" * 8)
    m, _, _ = R68.card_with_favourites(c, "c_l", pc, 1.1, None)
    print("| 1.1x | " + R67.cells(c, cq, m & per, cpaid, mo) + " |")
    for dd in MARGINS:
        print(f"| {points(dd)} | " + R67.cells(c, cq, R68.margin_bets(c, pc, dd) & per, cpaid, mo) + " |")
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 69")
