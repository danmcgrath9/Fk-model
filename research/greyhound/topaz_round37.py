"""Round 37: are the held blend's bets at TAB's open real? (13 Nov 2026, founder: "Well keep testing and get better")

Test 54 found the card's rule, with the blend held at Test 51's weights (0.54 ours, 0.67 TAB), still bets at TAB's first
price since February 2025: 99 bets, 31 winners against 19.3 expected at the prices taken, +40.9% flat after TAB's
deduction. Refitted each month the blend moved to about 0.35 ours and 0.88 TAB and stopped betting. The refitted blend
is fitted to log loss, so it is the better forecaster over the whole field; the held blend's bets are the dogs where ours
and TAB disagree most. Five checks, on round 36's field at the bet (read from the saved walk):

    python research/greyhound/topaz_round37.py DIR LABEL    (as round 36: BETWATCH_DIR, BETFAIR_DIR, RACES_DIR; the
                                                             weekly train's WALK_* settings, WALK_TO and WALK_CACHE_DIR
                                                             as round 36 ran them, so the saved walk is read)

  1. log loss by period on races with nothing scratched after the open: ours alone, TAB's first book, the two blends, BSP
  2. on the card's bets: how many won against how many each book expected (the sum of its chances for those dogs)
  3. the ratio from 1.1 to 1.5 at both blends: bets, A/E and z at the price taken, returns after the deduction, and BSP
     against the price paid (a real edge should grow with the ratio and beat BSP)
  4. since February 2025, the held blend's bets month by month
  5. since February 2025, the rule at TAB's first price over a grid of the two weights (how much the result rests on
     the exact weights; read as a sensitivity, not a choice)
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
import topaz_round36 as R36       # noqa: E402
import topaz_v1 as V1             # noqa: E402

RATIOS = (1.1, 1.2, 1.3, 1.5)
BLENDS = {"refitted monthly": "pb", "held at 0.54 / 0.67": "pb_fixed"}
GRID_OURS = (0.40, 0.47, 0.54, 0.61, 0.68)
GRID_TAB = (0.53, 0.60, 0.67, 0.74, 0.81)
RECENT = "2025-02-01"


def rule(t: pd.DataFrame, pb_col: str, ratio: float, price_col: str = "price"):
    """The card's rule at a ratio: mask, the price paid after TAB's deduction, Kelly units."""
    price = t[price_col].values.astype(float)
    m, o, u = R9.horse_bets(t, t[pb_col].values, t.p_book.values, price, 0.0, ratio, (2, 15))
    return m, 1 + (o - 1) * (1 - t.ded.fillna(0).values), u


def z_at_price(won: np.ndarray, price: np.ndarray) -> float:
    """Winners against the price taken's chances, in standard deviations."""
    p = 1 / price
    v = (p * (1 - p)).sum()
    return float((won.sum() - p.sum()) / np.sqrt(v)) if v > 0 else np.nan


def clv(t: pd.DataFrame, m: np.ndarray, paid: np.ndarray):
    """Bets with a BSP, the share where BSP came in under the price paid, the mean log(price paid / BSP)."""
    if "p_bsp" not in t:
        return 0, np.nan, np.nan
    x = m & t.p_bsp.notna().values
    if not x.any():
        return 0, np.nan, np.nan
    bsp = 1 / t.p_bsp.values[x]
    return int(x.sum()), float((bsp < paid[x]).mean()), float(np.log(paid[x] / bsp).mean())


def months_in_profit(t: pd.DataFrame, m: np.ndarray, paid: np.ndarray, u: np.ndarray) -> str:
    bym = pd.Series(np.where(t.won.values[m] == 1, paid[m] - 1, -1) * u[m]).groupby(
        pd.to_datetime(t.date.values[m]).to_period("M")).sum()
    return f"{(bym > 0).sum()} of {len(bym)}"


def log_loss(t: pd.DataFrame) -> None:
    clean = t[(t.n_later == 0).values]
    books = [("ours alone", "p_x_bet"), ("TAB's first book", "p_book"), ("blend refitted monthly", "pb"),
             ("blend held at 0.54 / 0.67", "pb_fixed"), ("BSP", "p_bsp")]
    books = [(n, c) for n, c in books if c in clean]
    full = np.ones(len(clean), bool)
    for _, c in books:
        full &= clean[c].notna().groupby(clean.race_id).transform("all").values
    w = clean[full & (clean.won == 1).values]
    print("| period | races | " + " | ".join(n for n, _ in books) + " |\n|" + "---|" * (len(books) + 2))
    for pname, a, b in R36.PERIODS:
        g = w[R36.in_period(w, a, b)]
        if g.empty:
            continue
        print(f"| {pname} | {g.race_id.nunique():,} | " +
              " | ".join(f"{-np.log(g[c].clip(1e-9)).mean():.4f}" for _, c in books) + " |")


def expected_winners(t: pd.DataFrame) -> None:
    """For the card's bets at TAB's first price: winners against the sum of each book's chances for those dogs."""
    books = [("the price taken", None), ("TAB's first book", "p_book"), ("ours alone", "p_x_bet"),
             ("blend refitted", "pb"), ("blend held", "pb_fixed"), ("BSP", "p_bsp")]
    books = [(n, c) for n, c in books if c is None or c in t]
    print("| period | blend the bets came from | bets | winners | expected by " + " | ".join(n for n, _ in books) +
          " |\n|" + "---|" * (len(books) + 4))
    for pname, a, b in R36.PERIODS:
        p = R36.in_period(t, a, b)
        for bn, bcol in BLENDS.items():
            m, _, _ = rule(t, bcol, 1.3)
            x = m & p
            if not x.any():
                print(f"| {pname} | {bn} | 0 | |" + " |" * len(books))
                continue
            cells = []
            for _, c in books:
                if c is None:
                    cells.append(f"{(1 / t.price.values[x]).sum():.1f}")
                    continue
                v = t[c].values[x]
                ok = ~np.isnan(v)
                cells.append(f"{np.nansum(v):.1f}" + ("" if ok.all() else f" (on {ok.sum():,})"))
            print(f"| {pname} | {bn} | {x.sum():,} | {int(t.won.values[x].sum()):,} | " + " | ".join(cells) + " |")


def ratio_sweep(t: pd.DataFrame, title: str) -> None:
    print(f"\n{title}\n\n| period | blend | ratio | bets | winners | A/E vs the price taken | z | flat ROI | Kelly ROI "
          "| units won | months in profit | bets with a BSP | BSP under the price paid | mean log(price paid / BSP) |"
          "\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    price = t.price.values.astype(float)
    for pname, a, b in R36.PERIODS:
        p = R36.in_period(t, a, b)
        for bn, bcol in BLENDS.items():
            for r in RATIOS:
                m, paid, u = rule(t, bcol, r)
                x = m & p
                s = R9.summary(t, x, paid, u, price)
                if not s["n"]:
                    print(f"| {pname} | {bn} | {r} | 0 | | | | | | | | | | |")
                    continue
                nb, under, lr = clv(t, x, paid)
                print(f"| {pname} | {bn} | {r} | {s['n']:,} | {s['w']:,} | {s['ae']:.3f} | "
                      f"{z_at_price(t.won.values[x], price[x]):+.1f} | {s['flat']:+.1%} | {s['kroi']:+.1%} | "
                      f"{s['kunits']:+,.0f} | {months_in_profit(t, x, paid, u)} | {nb:,} | "
                      f"{'' if np.isnan(under) else f'{under:.1%}'} | {'' if np.isnan(lr) else f'{lr:+.3f}'} |")


def recent_by_month(t: pd.DataFrame) -> None:
    m, paid, u = rule(t, "pb_fixed", 1.3)
    x = m & (t.date >= RECENT).values
    print("| month | bets | winners | expected at the price taken | flat return | Kelly units won |\n"
          "|---|---|---|---|---|---|")
    g = pd.DataFrame({"month": pd.to_datetime(t.date.values[x]).to_period("M"), "won": t.won.values[x],
                      "p": 1 / t.price.values[x], "flat": np.where(t.won.values[x] == 1, paid[x] - 1, -1.0),
                      "k": np.where(t.won.values[x] == 1, paid[x] - 1, -1.0) * u[x]})
    for mo, h in g.groupby("month"):
        print(f"| {mo} | {len(h)} | {int(h.won.sum())} | {h.p.sum():.1f} | {h.flat.mean():+.1%} | {h.k.sum():+.1f} |")
    print(f"| all | {len(g)} | {int(g.won.sum())} | {g.p.sum():.1f} | {g.flat.mean():+.1%} | {g.k.sum():+.1f} |")


def weight_grid(x: pd.DataFrame) -> None:
    """The rule at TAB's first price since February 2025 over a grid of the two weights: bets, A/E, flat ROI."""
    print("| ours \\ TAB | " + " | ".join(f"{w:.2f}" for w in GRID_TAB) + " |\n|" + "---|" * (len(GRID_TAB) + 1))
    xr = x[(x.date >= RECENT).values].reset_index(drop=True)
    for wa in GRID_OURS:
        cells = []
        for wt in GRID_TAB:
            xr["g"] = V1.blend(["p_x_bet", "p_book"], xr, np.array([wa, wt]))[1]
            t = R36.ran_rows(xr.assign(pb=xr.g))
            m, paid, u = rule(t, "pb", 1.3)
            s = R9.summary(t, m, paid, u, t.price.values.astype(float))
            cells.append("0" if not s["n"] else f"{s['n']}, {s['ae']:.2f}, {s['flat']:+.0%}")
        print(f"| {wa:.2f} | " + " | ".join(cells) + " |")


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 37, are the held blend's bets at TAB's open real?\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    x, _ = R36.field_at_open(d, bdir, t0)
    if x is None:
        print("No Betwatch races: nothing to test")
        return 1
    t = R36.ran_rows(x)
    print(f"Field at the bet: {t.race_id.nunique():,} races, {len(t):,} runners that ran, {t.date.min():%Y-%m-%d} to "
          f"{t.date.max():%Y-%m-%d}. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    print("## 1. Log loss on races with nothing scratched after the open, where every book prices every runner "
          "(lower is better)\n")
    log_loss(t)
    print("\n## 2. The card's bets (1.3x, TAB's first price): winners against each book's expected winners\n")
    expected_winners(t)
    print("\n## 3. The ratio, at TAB's first price, after TAB's deduction")
    ratio_sweep(t, "Every race:")
    ratio_sweep(t[(t.n_later == 0).values].reset_index(drop=True), "Races with nothing scratched after the open:")
    print("\n## 4. Since February 2025, the held blend's bets (1.3x, TAB's first price) month by month\n")
    recent_by_month(t)
    print("\n## 5. Since February 2025, the rule at TAB's first price over the two weights (bets, A/E vs the price "
          "taken, flat ROI after the deduction)\n")
    weight_grid(x)
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 37")
