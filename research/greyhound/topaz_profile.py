"""Profile of the Topaz bulk runs, and a first look at our ratings on real form (4 Nov 2026, the first full pull).

    python research/greyhound/topaz_profile.py DIR LABEL     (DIR: the pull's runs_<STATE>_<YYYY-MM>.json.gz files)

Prints totals, rates and test results only, never a row: the workflow's mode=run keeps this report and throws the
data away, because GRV's data is personal use and this repository is public.

1. What the history holds, year by year: meetings, races, runners, tracks, and how often a runner has its own time,
   a first split and a starting price.
2. The starting price (startPrice) against results: the book's size, and A/E by price band on races where every
   runner is priced and there is exactly one winner. This says whether GRV's SP is a usable market price.
3. Our ratings on real form, point in time (greyhound/ratings.py): on the later half of the period, how often the
   runner ranked first by each rating wins, against the field-size share and against the SP favourite.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from greyhound.ratings import dog_form, elo, load_topaz, run_ratings   # noqa: E402


def main(d, label):
    runs = load_topaz(d)
    runs["year"] = runs.date.dt.year
    print(f"# {label}: Topaz profile\n\n{runs.race_id.nunique():,} races, {len(runs):,} runners, "
          f"{runs.dog.nunique():,} dogs, {runs.track.nunique()} tracks, {runs.date.min():%Y-%m-%d} to "
          f"{runs.date.max():%Y-%m-%d}\n")

    print("## 1. The history by year\n")
    print("| year | meetings | races | runners | tracks | own time | first split | start price | runners a race |")
    print("|---|---|---|---|---|---|---|---|---|")
    for y, g in runs.groupby("year"):
        print(f"| {y} | {g.meeting_id.nunique():,} | {g.race_id.nunique():,} | {len(g):,} | {g.track.nunique()} | "
              f"{g.time.notna().mean():.0%} | {g.split.notna().mean():.0%} | "
              f"{(g.start_price > 1).mean() if 'start_price' in g else float('nan'):.0%} | "
              f"{len(g) / g.race_id.nunique():.1f} |")

    print("\n## 2. Starting price against results\n")
    g = runs.groupby("race_id")
    ok = (g.start_price.transform(lambda s: (s > 1).all()) & (g.finish.transform(lambda s: (s == 1).sum()) == 1)
          & (g.dog.transform("size") >= 4))
    s = runs[ok].copy()
    s["won"] = (s.finish == 1).astype(int)
    book = (1 / s.start_price).groupby(s.race_id).sum()
    s["p_sp"] = (1 / s.start_price) / s.race_id.map(book)
    ll = -np.log(s.p_sp[s.won == 1].clip(1e-9)).sum() / s.race_id.nunique()
    print(f"{s.race_id.nunique():,} races priced throughout with one winner; book size median {book.median():.3f} "
          f"(1.000 = no margin); winner log loss of the SP chances {ll:.4f}\n")
    print("| SP band | runners | winners | A/E (on the raw SP) | A/E (on the book-adjusted chance) |")
    print("|---|---|---|---|---|")
    bands = [(1, 2), (2, 3), (3, 5), (5, 8), (8, 13), (13, 21), (21, 51), (51, 1e9)]
    for lo, hi in bands:
        b = s[(s.start_price >= lo) & (s.start_price < hi)]
        if len(b):
            print(f"| ${lo:g}-{'' if hi > 1e8 else f'${hi:g}'} | {len(b):,} | {b.won.sum():,} | "
                  f"{b.won.sum() / (1 / b.start_price).sum():.3f} | {b.won.sum() / b.p_sp.sum():.3f} |")

    print("\n## 3. Our ratings on real form (point in time)\n")
    rated = run_ratings(runs)
    form = dog_form(runs, rated)
    e = elo(runs)
    x = pd.concat([runs[["race_id", "date", "finish", "start_price"]], form, e.rename("elo")], axis=1)
    x = x[x.date >= x.date.quantile(0.5)]
    x["won"] = (x.finish == 1).astype(int)
    one = x.groupby("race_id").won.transform("sum") == 1
    x = x[one]
    field = x.groupby("race_id").race_id.transform("size")
    print(f"scored on the later half: {x.race_id.nunique():,} races from {x.date.min():%Y-%m-%d}; a random runner "
          f"wins {(1 / field).mean():.1%} of the time\n")
    print("| ranked first by | races where it is known | top-ranked runner wins | SP of those winners (median) |")
    print("|---|---|---|---|")
    for col, asc, name in (("time_rating_mean5", False, "time rating, mean of last 5"),
                           ("time_rating_best5", False, "time rating, best of last 5"),
                           ("split_rating_mean5", False, "first-split rating, mean of last 5"),
                           ("elo", False, "Elo (who beat whom)"),
                           ("finish_mean5", True, "mean finish, last 5"),
                           ("start_price", True, "SP favourite")):
        if col not in x:
            continue
        known = x.groupby("race_id")[col].transform(lambda v: v.notna().mean() >= 0.75)
        y = x[known & x[col].notna()]
        r = y.groupby("race_id")[col].rank(ascending=asc, method="first")
        top = y[r == 1]
        print(f"| {name} | {top.race_id.nunique():,} | {top.won.mean():.1%} | "
              f"{top.start_price[top.won == 1].median():.2f} |")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz")
