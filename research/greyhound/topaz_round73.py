"""Round 73: the best model at every bookmaker's first price (17 Nov 2026, founder: "Keep going, find more winning
bets")

Tests 89 and 90 closed three doors: fitting harder, averaging fits and betting smaller edges at TAB's open each add no
money to Test 88's fit at the 2-point margin. Test 81 found the other bookmakers' first prices added little to the
card's blend at its low ratios; it has never been run on Test 88's fit or its margin rule. The other books open a
median 1.6 hours after TAB (Test 81), so their first prices are a second, separate chance to bet. Stated before the run,
on Test 88's fit (corr_r70), February 2025 on, bets with a corrected BSP:

  - the books: the runners each priced, and how long after TAB's first price each opens
  - the 2-point margin, fair price under $15, a quarter of Kelly at ONE scale (TAB's 2-point bets' mean stake is one
    unit), at TAB's first price, at each bookmaker's first price, at the best first price of the other bookmakers,
    and at the best first price of all of them, TAB's included
  - a second chance: TAB's open's 2-point bets as they are, plus, on dogs TAB's open did not bet, the best first price
    of the other bookmakers where it clears a margin of 1.5, 2, 3 or 5 points; each dog is bet once; the extra bets
    alone and the two together
  - by half, and by three months for TAB's open, the extra bets at 2 points and the two together

The model's chance is read from TAB's opening book, and by the time the other books open the market may have moved
while the model has not; the corrected BSP judges whatever that costs. The best first price needs an account with every
book and a bet placed as each opens, and bookmakers limit accounts that win. Those are the founder's to weigh.

    python research/greyhound/topaz_round73.py DIR LABEL    (as round 67)

Counts, sums and rates only: no race, dog or price is printed (bookmakers are named).
"""
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import gbm_v0                     # noqa: E402
import topaz_round58 as R58       # noqa: E402
import topaz_round62 as R62       # noqa: E402
import topaz_round63 as R63       # noqa: E402
import topaz_round67 as R67       # noqa: E402
import topaz_round68 as R68       # noqa: E402
import topaz_round72 as R72       # noqa: E402

MARGIN = 0.02
SECOND_MARGINS = (0.015, 0.02, 0.03, 0.05)


def at_price(t: pd.DataFrame, price) -> pd.DataFrame:
    """t with its price replaced: the margin rule and the price paid read t.price, and the deduction stays TAB's."""
    return t.assign(price=np.asarray(price, float))


def raw_kelly(p: np.ndarray, paid: np.ndarray, frac: float = R67.KELLY, cap: float = R67.CAP) -> np.ndarray:
    """A quarter of Kelly on every dog with an edge at the price paid, capped, before any scaling."""
    with np.errstate(divide="ignore", invalid="ignore"):
        f = frac * (paid * p - 1) / (paid - 1)
    return np.where(np.isfinite(f), np.clip(f, 0, cap), 0.0)


def second_chance(m1: np.ndarray, paid1: np.ndarray, u1: np.ndarray,
                  m2: np.ndarray, paid2: np.ndarray, u2: np.ndarray) -> tuple:
    """The first chance's bets as they are, plus the second chance's bets on dogs the first did not bet, so no dog is
    bet twice: (mask, price paid, stake, the extra bets' mask)."""
    extra = m2 & ~m1
    m = m1 | extra
    paid = np.where(m1, paid1, np.where(extra, paid2, np.nan))
    u = np.where(m1, u1, np.where(extra, u2, 0.0))
    return m, paid, u, extra


def kelly_row(t: pd.DataFrame, tq: pd.DataFrame, m: np.ndarray, paid: np.ndarray, u: np.ndarray) -> str:
    """bets | units staked | corrected BSP per unit staked (SE) | corrected BSP units | realised units | luck (SD) |
    deepest fall, realised | losing months"""
    s = R68.staked(tq, m, paid, u)
    if not s["n"]:
        return "0 | | | | | | |"
    fall, lose, nmon = R68.deepest_fall(t, m & tq.p_bsp.notna().values, paid, u)
    return (f"{s['n']:,} | {s['staked']:,.0f} | {s['per']:+.1%} ({s['se']:.1%}) | {s['units']:+,.1f} | "
            f"{s['real']:+,.1f} | {s['luck']:,.1f} | {fall:,.1f} | {lose} of {nmon}")


def main(d, label):
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 73, the best model at every bookmaker's first price\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    x, _, _, _ = R62.field(d, t0)
    if not R67.read_saved(x, "r70", "c_f"):
        print("Test 88's fit (corr_r70) is not in the walk cache: nothing to test")
        return 1
    bw = R63.load_books(bdir)
    n0 = len(x)
    x = x.assign(_dn=gbm_v0.norm_name(x.dog_name.fillna(""))).merge(
        bw.drop(columns=[c for c in bw if c in x and c not in ("date", "_dn")]), on=["date", "_dn"],
        how="left").drop(columns="_dn")
    assert len(x) == n0, "the book prices duplicated runners"
    t = x[x.is_ran.astype(bool).values].reset_index(drop=True)
    t["q_bsp"], _ = R58.corrected_bsp(t)
    tq = t.assign(p_bsp=t.q_bsp)
    books = R63.books_of(t)
    since = R63.R36.in_period(t, R63.SINCE, None)
    print(f"Runners that ran at TAB's first price: {len(t):,} in {t.race_id.nunique():,} races. "
          f"{(time.monotonic() - t0) / 60:.0f} minutes in.\n")

    tab_t = t["Tab_t"] if "Tab_t" in t else pd.Series(np.nan, index=t.index)
    print("## 1. The books, since February 2025\n\n| book | runners it priced | median hours after TAB's first price |\n"
          "|---|---|---|")
    for b in books:
        has = t[f"{b}_first"].notna().values & since
        lag = ((t[f"{b}_t"] - tab_t) / 3600)[has]
        print(f"| {b} | {has.sum() / max(since.sum(), 1):.0%} | {lag.median():.1f} |")
    others = [b for b in books if not any(e in b.lower() for e in R63.EXCHANGES)]
    tab = t.price.where(t.price > 1)
    best_other = pd.concat([t[f"{b}_first"] for b in others], axis=1).max(axis=1) if others else tab * np.nan
    best_all = pd.concat([tab, best_other], axis=1).max(axis=1)
    print(f"\n(the other bookmakers: {', '.join(others) or 'none'}; an exchange pays commission rather than TAB's "
          "deduction, so it is left out of the prices below)\n")

    pm = R67.model_chance(t, "c_f")
    tab_paid = R68.paid_price(t)
    m_tab = R68.margin_bets(t, pm, MARGIN)
    u_tab_raw = raw_kelly(pm, tab_paid)
    scale = u_tab_raw[m_tab & since].mean()
    if not np.isfinite(scale) or scale <= 0:
        print("No 2-point bets at TAB's first price since February 2025: nothing to test")
        return 1
    u_tab = u_tab_raw / scale
    m_tab &= u_tab > 0

    def at(price) -> tuple:
        tp = at_price(t, price)
        paid = R68.paid_price(tp)
        u = raw_kelly(pm, paid) / scale
        return paid, u, tp

    prices = {"TAB's first price": tab.values,
              **{f"{b}{chr(39) if b.endswith('s') else chr(39) + 's'} first price": t[f"{b}_first"].values
                 for b in others},
              "the best first price of the other bookmakers": best_other.values,
              "the best first price of all, TAB's included": best_all.values}
    periods = [("Feb 2025 on", R63.SINCE, None)] + R63.HALVES
    head = ("bets | units staked | corrected BSP per unit staked (SE) | corrected BSP units | realised units | "
            "luck in the realised units (SD) | deepest fall, realised | losing months")
    print("## 2. The 2-point margin, fair price under $15, a quarter of Kelly at one scale, at each price\n")
    print(f"| price | period | {head} |\n|" + "---|" * 10)
    for pname, pr in prices.items():
        paid, u, tp = at(pr)
        m = R68.margin_bets(tp, pm, MARGIN) & (u > 0)
        for lab, lo, hi in periods:
            per = R63.R36.in_period(t, lo, hi)
            print(f"| {pname} | {lab} | " + kelly_row(t, tq, m & per, paid, u) + " |")

    paid_o, u_o, to = at(best_other.values)
    print(f"\n## 3. A second chance: TAB's open's 2-point bets, plus the best first price of the other bookmakers on "
          f"dogs TAB's open did not bet ({(time.monotonic() - t0) / 60:.0f} minutes in)\n")
    print(f"| second chance's margin | which | period | {head} |\n|" + "---|" * 11)
    keep = {}
    for dm in SECOND_MARGINS:
        m_o = R68.margin_bets(to, pm, dm) & (u_o > 0)
        m, paid, u, extra = second_chance(m_tab, tab_paid, u_tab, m_o, paid_o, u_o)
        keep[dm] = (m, paid, u, extra)
        for lab, lo, hi in periods:
            per = R63.R36.in_period(t, lo, hi)
            print(f"| {R72.points(dm)} | the extra bets alone | {lab} | " + kelly_row(t, tq, extra & per, paid, u)
                  + " |")
            print(f"| {R72.points(dm)} | TAB's open and the extra together | {lab} | "
                  + kelly_row(t, tq, m & per, paid, u) + " |")

    print("\n## 4. By three months, a quarter of Kelly at one scale: corrected BSP units / realised units\n")
    m2, paid2, u2, extra2 = keep[MARGIN]
    cols = [("TAB's open, 2 points", m_tab, tab_paid, u_tab), ("the extra bets at 2 points", extra2, paid2, u2),
            ("the two together", m2, paid2, u2)]
    print("| three months | " + " | ".join(c[0] for c in cols) + " |\n|" + "---|" * (len(cols) + 1))
    for bname, lo, hi in R68.blocks(R63.SINCE, None):
        per = R63.R36.in_period(t, lo, hi)
        cells = []
        for _, m, paid, u in cols:
            s = R68.staked(tq, m & per, paid, u)
            cells.append(f"{s['units']:+,.1f} / {s['real']:+,.1f}" if s["n"] else "no BSP yet")
        print(f"| {bname} | " + " | ".join(cells) + " |")
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 73")
