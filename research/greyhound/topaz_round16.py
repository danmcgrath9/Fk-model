"""Round 16: the place book (6 Nov 2026; Test 29 found the place rule's profits in races whose place BSPs add up to well
under the places paid, seen only at the off).

    python research/greyhound/topaz_round16.py DIR LABEL     (BETFAIR_DIR; DIR is not read: no model, Betfair's files only)

Every race since 2020 in Betfair's free files with a place BSP on every runner that ran and 2 or 3 places paid:
  place book = (sum over the runners of 1 / place BSP) / places paid     (1 = fair; 0.77 = the 1.3x rule's races)

1. How often the place book settles under-round at BSP, and what backing every runner at place BSP (8% commission)
   returned in each band, both halves; the money matched at BSP in those races; the win book in the same races beside it.
2. The place prices traded before the off (last price taken, weighted average): do they know the result (a price traded
   in-play would), and does the book they show predict the BSP book?
3. The bet anyone could make: back every runner at place BSP in races whose book BEFORE the off is under a cap. The
   selection reads only prices traded before the off; the bet is struck at BSP, which nobody knows until the off and
   nobody needs to.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

COMM = 0.08
BANDS = [(0, 0.77), (0.77, 0.85), (0.85, 0.95), (0.95, 1.05), (1.05, np.inf)]
NAMES = ["under 0.77", "0.77-0.85", "0.85-0.95", "0.95-1.05", "1.05 and over"]
PRE = {"PLACE_LAST_PRICE_TAKEN": "last price traded", "PLACE_WEIGHTED_AVERAGE_PRICE_TAKEN": "weighted average traded"}
NUM = ["WIN_BSP", "PLACE_BSP", "PLACE_BSP_VOLUME", "PLACE_PREPLAY_VOLUME"] + list(PRE)


def races(df: pd.DataFrame) -> pd.DataFrame:
    """Runners that ran (a win BSP), in races with a place BSP on every one of them and 2 or 3 places paid; adds k
    (places paid), the place book at BSP, the win book at BSP, and each pre-off book where every runner traded."""
    df = df[df.WIN_BSP > 1].copy()
    g = df.groupby("WIN_MARKET_ID")
    df["k"] = g.placed.transform("sum")
    full = (df.PLACE_BSP > 1).groupby(df.WIN_MARKET_ID).transform("all")
    df = df[full & df.k.isin([2, 3])].copy()
    g = df.groupby("WIN_MARKET_ID")
    df["book_bsp"] = (1 / df.PLACE_BSP).groupby(df.WIN_MARKET_ID).transform("sum") / df.k
    df["win_book"] = (1 / df.WIN_BSP).groupby(df.WIN_MARKET_ID).transform("sum")
    for c in PRE:
        if c not in df:
            continue
        ok = (df[c] > 1).groupby(df.WIN_MARKET_ID).transform("all")
        df["book_" + c] = ((1 / df[c]).groupby(df.WIN_MARKET_ID).transform("sum") / df.k).where(ok)
    return df


def band(x: pd.Series) -> pd.Series:
    out = pd.Series(np.nan, index=x.index, dtype=object)
    for (lo, hi), name in zip(BANDS, NAMES):
        out[(x >= lo) & (x < hi)] = name
    return out


def flat_roi(placed, price, comm=COMM) -> float:
    placed, price = np.asarray(placed, float), np.asarray(price, float)
    return float(np.where(placed == 1, (price - 1) * (1 - comm), -1.0).mean())


def chance(df: pd.DataFrame, col: str) -> pd.Series:
    """A price's place chance, 1 / price rescaled so each race adds to its places."""
    inv = 1 / df[col]
    return inv / inv.groupby(df.WIN_MARKET_ID).transform("sum") * df.k


def bll(p, y) -> float:
    p = np.clip(np.asarray(p, float), 1e-9, 1 - 1e-9)
    y = np.asarray(y, float)
    return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())


def band_table(t: pd.DataFrame, col: str, half: np.ndarray, what: str):
    b = band(t[col])
    print(f"| {what} | races | share | runners | placed | flat ROI at place BSP (1st / 2nd) | "
          "median place BSP money per race | median win book |\n|---|---|---|---|---|---|---|---|")
    n_races = t.WIN_MARKET_ID.nunique()
    for name in NAMES:
        m = (b == name).values
        if not m.any():
            continue
        g = t[m]
        r = g.WIN_MARKET_ID.nunique()
        r1, r2 = flat_roi(g.placed[half[m]], g.PLACE_BSP[half[m]]), flat_roi(g.placed[~half[m]], g.PLACE_BSP[~half[m]])
        vol = g.groupby("WIN_MARKET_ID").PLACE_BSP_VOLUME.sum().median() if "PLACE_BSP_VOLUME" in g else np.nan
        print(f"| {name} | {r:,} | {r / n_races:.1%} | {m.sum():,} | {int(g.placed.sum()):,} | {r1:+.1%} / {r2:+.1%} | "
              f"${vol:,.0f} | {g.groupby('WIN_MARKET_ID').win_book.first().median():.3f} |")
    print()


def main(_d, label):
    import gbm_v0
    bdir = os.environ.get("BETFAIR_DIR", "")
    if not bdir or not os.path.isdir(bdir):
        print("No BETFAIR_DIR: nothing to test")
        return 1
    df = gbm_v0.load(bdir)
    for c in NUM:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if "PLACE_BSP" not in df:
        print("Betfair's files carry no place BSP: nothing to test")
        return 1
    print(f"# {label}: round 16, the place book\n")
    for scope, sub in (("VIC", df[df.STATE_CODE == "VIC"]), ("all of Australia", df)):
        t = races(sub)
        if t.empty:
            continue
        half = (t.date < t.date.quantile(0.5)).values
        print(f"## {scope}: {t.WIN_MARKET_ID.nunique():,} races from {t.date.min():%Y-%m-%d} with a place BSP on every "
              f"runner, halves split at {t.date.quantile(0.5):%Y-%m-%d} (2 places in "
              f"{(t.groupby('WIN_MARKET_ID').k.first() == 2).mean():.0%})\n")
        book = t.groupby("WIN_MARKET_ID").book_bsp.first()
        print(f"Place book at BSP: median {book.median():.3f}, 10th percentile {book.quantile(0.1):.3f}, 90th "
              f"{book.quantile(0.9):.3f}. Win book at BSP in the same races: median "
              f"{t.groupby('WIN_MARKET_ID').win_book.first().median():.3f}\n")
        band_table(t, "book_bsp", half, "place book at BSP")

        # the prices traded before the off: do they know the result?
        y = t.placed.values
        print("| place chance from | races where every runner traded | binary log loss | the same runners at place BSP | "
              "A/E |\n|---|---|---|---|---|")
        usable = []
        for c, what in PRE.items():
            bc = "book_" + c
            if bc not in t:
                continue
            m = t[bc].notna().values
            if m.sum() < 1000:
                continue
            g = t[m]
            p, pb = chance(g, c), chance(g, "PLACE_BSP")
            l, lb = bll(p, g.placed), bll(pb, g.placed)
            print(f"| {what} | {g.WIN_MARKET_ID.nunique():,} | {l:.4f} | {lb:.4f} | {g.placed.sum() / p.sum():.3f} |")
            if l > lb - 0.02:                      # within reach of BSP, not far below it: traded before the result
                usable.append((c, what))
        print("\n(a price traded after the dogs jumped would score far below BSP; those are not used below)\n")

        for c, what in usable:
            bc = "book_" + c
            g = t[t[bc].notna()]
            r = g.groupby("WIN_MARKET_ID")[[bc, "book_bsp"]].first()
            print(f"Book from the {what} against the book at BSP: correlation {r[bc].corr(r.book_bsp):.2f}; of the races "
                  f"under 0.77 at BSP, {(r[bc][r.book_bsp < 0.77] < 0.85).mean():.0%} were under 0.85 on the {what}\n")
            hb = (g.date < t.date.quantile(0.5)).values
            print(f"| back every runner at place BSP when the book on the {what} is under | half | races | bets | placed | "
                  "flat ROI | median place BSP money per race |\n|---|---|---|---|---|---|---|")
            for cap in (0.80, 0.85, 0.90, 0.95):
                sel = (g[bc] < cap).values
                for hn, hm in (("1st", hb), ("2nd", ~hb)):
                    s = g[sel & hm]
                    if s.empty:
                        print(f"| {cap:.2f} | {hn} | 0 | | | | |")
                        continue
                    vol = s.groupby("WIN_MARKET_ID").PLACE_BSP_VOLUME.sum().median()
                    print(f"| {cap:.2f} | {hn} | {s.WIN_MARKET_ID.nunique():,} | {len(s):,} | {int(s.placed.sum()):,} | "
                          f"{flat_roi(s.placed, s.PLACE_BSP):+.1%} | ${vol:,.0f} |")
            print()
        if usable:
            robust(t, "book_" + usable[0][0], usable[0][1])
    return 0


def robust(t: pd.DataFrame, bc: str, what: str):
    """Is the pre-off rule carried by a few big prices? Flat ROI with place BSP capped at $20 and without the five
    biggest returns, and the rule year by year."""
    print(f"| book on the {what} under | bets | flat ROI | place BSP capped at $20 | without the 5 biggest returns | "
          "biggest place BSP that placed |\n|---|---|---|---|---|---|")
    for cap in (0.85, 0.90):
        s = t[t[bc] < cap]
        if s.empty:
            continue
        ret = np.where(s.placed == 1, (s.PLACE_BSP - 1) * (1 - COMM), -1.0)
        capped = np.where(s.placed == 1, (np.minimum(s.PLACE_BSP, 20) - 1) * (1 - COMM), -1.0)
        trimmed = np.sort(ret)[:-5] if len(ret) > 5 else ret
        print(f"| {cap:.2f} | {len(s):,} | {ret.mean():+.1%} | {capped.mean():+.1%} | {trimmed.mean():+.1%} | "
              f"${s.PLACE_BSP[s.placed == 1].max():,.2f} |")
    print(f"\n| year, book on the {what} under 0.90 | races | bets | flat ROI | median place BSP money per race |\n"
          "|---|---|---|---|---|")
    s = t[t[bc] < 0.90]
    for y, g in s.groupby(s.date.dt.year):
        print(f"| {y} | {g.WIN_MARKET_ID.nunique():,} | {len(g):,} | {flat_roi(g.placed, g.PLACE_BSP):+.1%} | "
              f"${g.groupby('WIN_MARKET_ID').PLACE_BSP_VOLUME.sum().median():,.0f} |")
    print()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "", sys.argv[2] if len(sys.argv) > 2 else "topaz round 16")
