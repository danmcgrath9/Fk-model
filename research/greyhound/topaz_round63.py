"""Round 63: more winning bets, at every bookmaker's first price (17 Nov 2026, founder: "All I care about is winning";
"Keep going, find more winning bets - mate need way more than this for amount of bets")

The card bets only at TAB's first price: 98 bets since February 2025, worth about +41% a bet by the corrected BSP (Test
76). Test 53 found the best first price of TAB, Sportsbet and Ladbrokes made 158 bets in eight months where TAB's alone
made 10, on a blend refitted monthly that the card no longer uses; it has never been run on the held blend or judged by
the corrected BSP. Test 57 found the other books open a median 1.6 hours after TAB, so their first prices are a later,
separate chance to bet, not an input. Stated before the run, on round 58's field and corrected BSP, from February 2025:

  - every bookmaker in the Betwatch files, each with its first price before the jump (the first price Betwatch saw);
    its coverage and how long after TAB's first price it opens
  - the card's rule (our odds 2 to 15, the price at the ratio x our odds or over) at 1.1x, 1.2x, 1.3x and 1.5x, flat,
    after TAB's deduction, at each book's first price and at the best first price of all the bookmakers (an exchange,
    if there is one, is shown on its own and left out of the best)
  - for the card's blend, the blend with Isolynx, and round 62's corrected blends when the walk cache holds them
  - bets, bets a month, winners, realised flat ROI and units, and the corrected BSP's return per bet with its standard
    error and its units; the best first price is also shown in each half

The best first price needs an account with every book and a bet placed as each one opens; bookmakers also limit
accounts that win. Those are the founder's to weigh; this round only says what the prices would have paid.

    python research/greyhound/topaz_round63.py DIR LABEL    (as round 51)

Counts, sums and rates only: no race, dog or price is printed (bookmakers are named).
"""
import gzip
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import gbm_v0                     # noqa: E402
import topaz_round32 as R32       # noqa: E402
import topaz_round33 as R33       # noqa: E402
import topaz_round36 as R36       # noqa: E402
import topaz_round44 as R44       # noqa: E402
import topaz_round50 as R50       # noqa: E402
import topaz_round51 as R51       # noqa: E402
import topaz_round57 as R57       # noqa: E402
import topaz_round58 as R58       # noqa: E402

SINCE = "2025-02-01"
HALVES = [("Feb 2025 to Jan 2026", "2025-02-01", "2026-02-01"), ("Feb 2026 on", "2026-02-01", None)]
RATIOS = (1.1, 1.2, 1.3, 1.5)
BAND = (2.0, 15.0)
EXCHANGES = ("betfair",)


def load_books(bdir: str) -> pd.DataFrame:
    """One row per runner (not scratched): date, normalised name, and for every book its first price before the jump
    (`<book>_first`) and when (`<book>_t`, epoch seconds)."""
    rows = []
    for f in sorted(Path(bdir).glob("betwatch_VIC_G_*.json.gz")):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for r in json.load(fh).get("races", []):
                start = R32.ts(r.get("start"))
                for ru in r.get("runners", []):
                    if ru.get("scratched"):
                        continue
                    row = {"date": r.get("date"), "dog_raw": ru.get("name")}
                    for bk, v in (ru.get("books") or {}).items():
                        fl = []
                        for p, t in (v or {}).get("flucs") or []:
                            try:
                                p = float(p)
                            except (TypeError, ValueError):
                                continue
                            ts = R32.ts(t)
                            if p > 1 and (np.isnan(start) or np.isnan(ts) or ts <= start):
                                fl.append((p, ts))
                        if fl:
                            row[f"{bk}_first"], row[f"{bk}_t"] = fl[0]
                    rows.append(row)
    bw = pd.DataFrame(rows)
    if bw.empty:
        return bw
    bw["date"] = pd.to_datetime(bw.date, errors="coerce")
    bw["_dn"] = gbm_v0.norm_name(bw.dog_raw.fillna(""))
    return bw.drop(columns="dog_raw").drop_duplicates(["date", "_dn"], keep=False)


def books_of(t: pd.DataFrame) -> list:
    return [c[:-6] for c in t.columns if c.endswith("_first") and c[:-6] and c[:-6].lower() != "tab"
            and f"{c[:-6]}_t" in t]


def bets(t: pd.DataFrame, col: str, price: np.ndarray, ratio: float):
    """The card's rule at a price: mask and the price paid after TAB's deduction."""
    p = t[col].values.astype(float)
    pr = np.asarray(price, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        fair = 1 / p
    m = np.isfinite(pr) & (pr > 1) & np.isfinite(fair) & (fair >= BAND[0]) & (fair < BAND[1]) & (pr >= ratio * fair)
    return m, 1 + (pr - 1) * (1 - t.ded.fillna(0).values)


def row(t: pd.DataFrame, tq: pd.DataFrame, x: np.ndarray, paid: np.ndarray, months: float) -> str:
    n = int(x.sum())
    if not n:
        return f"0 | 0 |" + " |" * 7
    won = t.won.values[x].astype(float)
    real = np.where(won == 1, paid[x] - 1, -1.0)
    j = R44.judged(tq, x, paid)
    if not j["n"]:
        return f"{n:,} | {n / months:.1f} | {int(won.sum()):,} | | {real.mean():+.1%} | {real.sum():+,.1f} | | | |"
    return (f"{n:,} | {n / months:.1f} | {int(won.sum()):,} | {j['e']:,.1f} | {real.mean():+.1%} | {real.sum():+,.1f} | "
            f"{j['bsp']:+.1%} | {j['se']:.1%} | {j['units']:+,.1f}")


def table(t: pd.DataFrame, blends: dict, prices: dict, periods: list) -> None:
    tq = t.assign(p_bsp=t.q_bsp)
    print("| period | price | blend | ratio | bets | bets a month | winners | corrected BSP's expected winners | "
          "realised flat ROI | realised units | corrected BSP per bet | its standard error | corrected BSP units |\n|"
          + "---|" * 13)
    for pname, lo, hi in periods:
        p = R36.in_period(t, lo, hi)
        months = max(t.date[p].dt.to_period("M").nunique(), 1) if p.any() else 1
        for pr_name, pr in prices.items():
            for bname, col in blends.items():
                for r in RATIOS:
                    m, paid = bets(t, col, pr, r)
                    print(f"| {pname} | {pr_name} | {bname} | {r}x | " + row(t, tq, m & p, paid, months) + " |")


def read_corrections(x: pd.DataFrame, tag: str = "r62") -> bool:
    """Round 62's corrected blends (c_w, c_q) from the walk cache, when a run saved them; never walks them here."""
    d = os.environ.get("WALK_CACHE_DIR", "")
    f = Path(d) / f"corr_{tag}.csv.gz" if d else None
    if f is None or not f.exists():
        return False
    c = pd.read_csv(f, dtype={"race_id": "int64", "dog": str})
    ran = x.is_ran.astype(bool).values
    k = pd.DataFrame({"race_id": x.race_id.values[ran].astype("int64"), "dog": x.dog.values[ran].astype(str)})
    mg = k.merge(c.drop_duplicates(["race_id", "dog"]), on=["race_id", "dog"], how="left")
    x["c_w"], x["c_q"] = x.h_p_i_bet, x.h_p_i_bet
    x.loc[ran, "c_w"], x.loc[ran, "c_q"] = mg.c_w.values, mg.c_q.values
    return True


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 63, more winning bets, at every bookmaker's first price\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    if not os.environ.get("WALK_CACHE_USE", "").strip() or not os.environ.get("WALK_ISO_USE", "").strip():
        print("Both saved walks must be named (WALK_CACHE_USE and WALK_ISO_USE): nothing to test")
        return 1
    df = R51.named_walks(d, t0)
    fr = R33.load(bdir, times=(0,))
    x = R33.at_time(df, fr, 0)
    ran = x.is_ran.astype(bool).values
    x["p_i_bet"] = np.where(ran, x.p_i * (1 - x.s_later.fillna(0)), x.p_book)
    ok = pd.Series((x.price > 1).values).groupby(x.race_id.values).transform("all").values
    x = R57.term_columns(x[ok].reset_index(drop=True))
    for c in R51.OURS.values():
        x[f"h_{c}"] = R51.apply_weights(x, [c, "p_book"], R50.FIXED)
    blends = {"the card's blend": "h_p_x_bet", "blend with Isolynx": "h_p_i_bet"}
    if read_corrections(x):
        blends["with Isolynx, corrected on BSP corrected"] = "c_q"
    bw = load_books(bdir)
    n0 = len(x)
    x = x.assign(_dn=gbm_v0.norm_name(x.dog_name.fillna(""))).merge(bw.drop(columns=[c for c in bw if c in x and c not in
                                                                                    ("date", "_dn")]),
                                                                    on=["date", "_dn"], how="left").drop(columns="_dn")
    assert len(x) == n0, "the book prices duplicated runners"
    t = x[x.is_ran.astype(bool).values].reset_index(drop=True)
    t["q_bsp"], _ = R58.corrected_bsp(t)
    books = books_of(t)
    since = R36.in_period(t, SINCE, None)
    tab_t = t["Tab_t"] if "Tab_t" in t else pd.Series(np.nan, index=t.index)
    print(f"\nField at TAB's first price from May 2023: {t.race_id.nunique():,} races, {len(t):,} runners that ran. "
          f"{(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    print("## 1. The books, since February 2025\n\n| book | runners it priced | median hours after TAB's first price |\n"
          "|---|---|---|")
    for b in books:
        has = t[f"{b}_first"].notna().values & since
        lag = ((t[f"{b}_t"] - tab_t) / 3600)[has]
        print(f"| {b} | {has.sum() / max(since.sum(), 1):.0%} | {lag.median():.1f} |")
    bookies = [b for b in books if not any(e in b.lower() for e in EXCHANGES)]
    best = pd.concat([t.price.where(t.price > 1)] + [t[f"{b}_first"] for b in bookies], axis=1).max(axis=1)
    prices = {"TAB's first price": t.price.values, **{f"{b}'s first price": t[f"{b}_first"].values for b in books},
              "the best first price of the bookmakers": best.values}
    print(f"\n(the best first price is TAB's and {', '.join(bookies) or 'no other book'}'s)\n")
    print("## 2. The card's rule at every price since February 2025, flat\n")
    table(t, blends, prices, [("Feb 2025 on", SINCE, None)])
    print("\n## 3. TAB's and the best first price in each half\n")
    table(t, blends, {k: prices[k] for k in ("TAB's first price", "the best first price of the bookmakers")}, HALVES)
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 63")
