"""Round 38: can the blend at TAB's open get better? (15 Nov 2026, founder: "Well keep testing and lets get a fucking
good model")

Test 55 found the card's rule at TAB's first price, with ours blended with TAB's opening book and the weights held at
Test 51's (0.54 ours, 0.67 TAB), bets about once a week since February 2025 and the closing market agrees with the
bets. The blend has used two inputs. Here it is given everything the field at the bet holds, and each blend is fitted
on the same window Test 51 used (December 2023 to June 2024, races with nothing scratched after the open) and HELD,
so February 2025 on is out of sample for every one of them:

  A. ours + TAB's first book (Test 51, the baseline: should reproduce about 0.54 / 0.67)
  B. ours + the winners twin (the walk's second model, fitted on wins) + TAB
  C. ours + TAB + Sportsbet's first book + Ladbrokes' first book
  D. all five
and the baseline refitted each month on up to the 6, 12 and 24 months before (Test 54's refit used 6; every window starts
six months in and grows), to see whether an adaptive blend can keep the bets.

A book's chances are over the field at the bet: where Sportsbet or Ladbrokes did not price a runner (often a dog
scratched later), TAB's chance stands in, and the book's own chances share what TAB gives the runners it did price;
ours and the twin are scaled by TAB's book share of the dogs scratched later, as in round 33.

    python research/greyhound/topaz_round38.py DIR LABEL    (as round 37; WALK_CACHE_USE names the saved walk)

Printed: the weights; log loss by period on clean races; and the card's rule at 1.3x at TAB's first price after the
deduction by period for every blend, with A/E, z, flat and Kelly returns, months in profit and BSP against the price
paid. Counts, sums and rates only: no race, dog or price is printed.
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
import topaz_round37 as R37       # noqa: E402
import topaz_v1 as V1             # noqa: E402

FIT_FROM, FIT_TO = "2023-12-01", "2024-07-01"     # Test 51's early-stopping months
BLENDS = {"A. ours + TAB": ["p_x_bet", "p_book"],
          "B. ours + twin + TAB": ["p_x_bet", "p_b_bet", "p_book"],
          "C. ours + TAB + Sportsbet + Ladbrokes": ["p_x_bet", "p_book", "p_sb", "p_lb"],
          "D. all five": ["p_x_bet", "p_b_bet", "p_book", "p_sb", "p_lb"]}
WINDOWS = (6, 12, 24)
NAMES = {"p_x_bet": "ours", "p_b_bet": "twin", "p_book": "TAB", "p_sb": "Sportsbet", "p_lb": "Ladbrokes"}


def book_chance(x: pd.DataFrame, col: str) -> pd.Series:
    """A book's chances over the field at the bet: its own first prices normalised over the runners it priced, scaled
    to the share TAB's book gives those runners; TAB's chance for the runners it did not price. Sums to 1 a race."""
    inv = (1 / x[col]).where(x[col] > 1)
    have = inv.notna()
    own = inv / inv.groupby(x.race_id.values).transform("sum")
    cover = x.p_book.where(have, 0.0).groupby(x.race_id.values).transform("sum")
    return (own * cover).where(have, x.p_book)


def inputs(x: pd.DataFrame) -> pd.DataFrame:
    """The twin over the field at the bet (as ours is) and the two other books' chances."""
    x = x.copy()
    ran = x.is_ran.astype(bool).values
    x["p_b_bet"] = np.where(ran, x.p_b * (1 - x.s_later.fillna(0)), x.p_book)
    x["p_sb"] = book_chance(x, "sportsbet_first")
    x["p_lb"] = book_chance(x, "ladbrokes_first")
    return x


def held(x: pd.DataFrame, cols: list):
    """Weights fitted on Test 51's window (clean races), and the blend over every row with them."""
    w = x[(x.date >= FIT_FROM) & (x.date < FIT_TO) & (x.n_later == 0) & x[cols].notna().all(axis=1)]
    wb, _ = V1.blend(cols, w)
    ok = x[cols].notna().all(axis=1).values
    out = pd.Series(np.nan, index=x.index)
    out[ok] = V1.blend(cols, x[ok], wb)[1]
    return wb, out


def monthly(x: pd.DataFrame, cols: list, back: int) -> pd.Series:
    """The blend refitted each month on up to the `back` months before (clean races, 300 at least). Every window starts
    six months in, as Test 54's did, and grows to `back` months, so the windows price the same months."""
    out = pd.Series(np.nan, index=x.index)
    start = x.date.min().to_period("M")
    for M in pd.period_range(start + 6, x.date.max().to_period("M"), freq="M"):
        lo = max(M - back, start).start_time
        w = x[x.is_ran.astype(bool) & (x.n_later == 0) & (x.date >= lo) & (x.date < M.start_time)]
        cur = ((x.date >= M.start_time) & (x.date < (M + 1).start_time)).values
        if w.race_id.nunique() < 300 or not cur.any():
            continue
        wb, _ = V1.blend(cols, w)
        out[cur] = V1.blend(cols, x[cur], wb)[1]
    return out


def ll_table(t: pd.DataFrame, cols: dict) -> None:
    clean = t[(t.n_later == 0).values]
    full = np.ones(len(clean), bool)
    for c in list(cols.values()) + ["p_bsp"]:
        if c in clean:
            full &= clean[c].notna().groupby(clean.race_id).transform("all").values
    w = clean[full & (clean.won == 1).values]
    names = list(cols) + (["BSP"] if "p_bsp" in w else [])
    print("| period | races | " + " | ".join(names) + " |\n|" + "---|" * (len(names) + 2))
    for pname, a, b in R36.PERIODS:
        g = w[R36.in_period(w, a, b)]
        if g.empty:
            continue
        vals = [f"{-np.log(g[c].clip(1e-9)).mean():.4f}" for c in cols.values()]
        if "p_bsp" in g:
            vals.append(f"{-np.log(g.p_bsp.clip(1e-9)).mean():.4f}")
        print(f"| {pname} | {g.race_id.nunique():,} | " + " | ".join(vals) + " |")


def rule_table(t: pd.DataFrame, cols: dict, title: str) -> None:
    print(f"\n{title}\n\n| period | blend | bets | winners | A/E vs the price taken | z | flat ROI | Kelly ROI | units won "
          "| months in profit | BSP under the price paid | mean log(price paid / BSP) |\n|---|---|---|---|---|---|---|---|---|---|---|---|")
    price = t.price.values.astype(float)
    for pname, a, b in R36.PERIODS:
        p = R36.in_period(t, a, b)
        for name, col in cols.items():
            m, paid, u = R37.rule(t.assign(_pb=t[col].fillna(0)), "_pb", 1.3)
            x = m & p & t[col].notna().values
            s = R9.summary(t, x, paid, u, price)
            if not s["n"]:
                print(f"| {pname} | {name} | 0 | | | | | | | | | |")
                continue
            _, under, lr = R37.clv(t, x, paid)
            print(f"| {pname} | {name} | {s['n']:,} | {s['w']:,} | {s['ae']:.3f} | "
                  f"{R37.z_at_price(t.won.values[x], price[x]):+.1f} | {s['flat']:+.1%} | {s['kroi']:+.1%} | "
                  f"{s['kunits']:+,.0f} | {R37.months_in_profit(t, x, paid, u)} | "
                  f"{'' if np.isnan(under) else f'{under:.1%}'} | {'' if np.isnan(lr) else f'{lr:+.3f}'} |")


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 38, can the blend at TAB's open get better?\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    x, _ = R36.field_at_open(d, bdir, t0)
    if x is None:
        print("No Betwatch races: nothing to test")
        return 1
    x = inputs(x)
    print("| blend | weights, fitted on Dec 2023 to Jun 2024 and held |\n|---|---|")
    cols = {}
    for name, c in BLENDS.items():
        wb, x[f"pb_{name[0]}"] = held(x, c)
        cols[f"{name}, held"] = f"pb_{name[0]}"
        print(f"| {name} | " + ", ".join(f"{NAMES[n]} {v:.2f}" for n, v in zip(c, wb)) + " |")
    for k in WINDOWS:
        x[f"pm_{k}"] = monthly(x, BLENDS["A. ours + TAB"], k)
        cols[f"A, refitted monthly on {k} months"] = f"pm_{k}"
    t = R36.ran_rows(x)
    have = {c: t[c].notna().mean() for c in cols.values()}
    print(f"\nField at the bet: {t.race_id.nunique():,} races, {len(t):,} runners that ran, {t.date.min():%Y-%m-%d} to "
          f"{t.date.max():%Y-%m-%d}; Sportsbet priced {t.sportsbet_first.gt(1).mean():.0%} of them at its open, "
          f"Ladbrokes {t.ladbrokes_first.gt(1).mean():.0%}. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    print("## 1. Log loss on races with nothing scratched after the open, every input priced (lower is better)\n")
    ll_table(t, cols)
    print("\n## 2. The card's rule at 1.3x, TAB's first price, after TAB's deduction")
    rule_table(t, cols, "Every race:")
    rule_table(t[(t.n_later == 0).values].reset_index(drop=True), cols, "Races with nothing scratched after the open:")
    print(f"\n(coverage of each blend over the runners that ran: "
          + ", ".join(f"{k} {have[v]:.0%}" for k, v in cols.items()) + ")")
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 38")
