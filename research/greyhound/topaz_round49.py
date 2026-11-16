"""Round 49: the edge quarter by quarter (16 Nov 2026, founder: "Well keep testing and lets get a fucking good model")

Test 66: judged by BSP the held blend's candidates (edge 1.1 or over, flat) were worth +35.8% a bet from May 2023 to
April 2024, +14.2% to January 2025, +11.8% to January 2026 and +7.1% since. TAB's first price also moved from the
night before to the morning. Is the edge still falling, and is it TAB getting sharper or ours getting duller? Stated
before the run, quarter by quarter from April 2023 at TAB's first price:

  - log loss, winners only, on races with nothing scratched after the open and a BSP on every runner: TAB's first
    book, ours alone, the held blend and BSP, and each one's distance from BSP (the race mix changes from quarter to
    quarter, so the distances are the comparison, not the levels)
  - TAB's market: its mean book at its first price, the median hours from its first price to the jump, and the share
    of races it first priced the night before (6pm to midnight, Melbourne) and a day or more ahead
  - the held blend's candidates, flat: from 1.1x and from 1.3x, how many, worth what a bet by BSP, and the realised
    flat ROI

    python research/greyhound/topaz_round49.py DIR LABEL    (as round 48)

Counts, sums and rates only: no race, dog or price is printed.
"""
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round43 as R43       # noqa: E402
import topaz_round44 as R44       # noqa: E402
import topaz_round47 as R47       # noqa: E402

FORECASTS = {"tab": "p_book", "ours": "p_x_bet", "blend": "pb6", "bsp": "p_bsp"}   # TAB's first book, ours alone, the held blend, BSP


def ll(g: pd.DataFrame, col: str) -> float:
    return float(-np.log(g[col].clip(1e-9)).mean()) if len(g) else np.nan


def forecasts(t: pd.DataFrame) -> pd.DataFrame:
    """Per quarter: races and the winners' log loss of each forecast, on races with nothing scratched after the open
    and a BSP on every runner that ran."""
    clean = t[(t.n_later.fillna(0) == 0).values]
    full = clean.p_bsp.notna().groupby(clean.race_id.values).transform("all").values
    w = clean[full & (clean.won == 1).values]
    q = pd.to_datetime(w.date).dt.to_period("Q")
    rows = []
    for k, g in w.groupby(q.values):
        rows.append({"quarter": str(k), "races": g.race_id.nunique(), **{n: ll(g, c) for n, c in FORECASTS.items()}})
    return pd.DataFrame(rows)


def market(t: pd.DataFrame) -> pd.DataFrame:
    """Per quarter, one row per race: TAB's book, hours from its first price to the jump, night-before and day-ahead
    shares."""
    r = t.drop_duplicates("race_id")
    q = pd.to_datetime(r.date).dt.to_period("Q")
    g = r.groupby(q.values)
    return pd.DataFrame({"quarter": [str(k) for k in g.groups], "book": g.tab_book.mean().values,
                         "hours": g.to_jump.median().values,
                         "night": g.open_hour.apply(lambda h: (h >= 18).mean()).values,
                         "day": g.to_jump.apply(lambda h: (h >= 24).mean()).values})


def worth(t: pd.DataFrame, ratio: float) -> pd.DataFrame:
    m, paid, _ = R43.flat_candidates(t, "pb6", ratio)
    q = pd.to_datetime(t.date).dt.to_period("Q").astype(str).values
    rows = []
    for k in sorted(set(q)):
        s = R44.judged(t, m & (q == k), paid)
        rows.append({"quarter": k, "n": s.get("n", 0), "bsp": s.get("bsp", np.nan), "se": s.get("se", np.nan),
                     "flat": s.get("flat", np.nan)})
    return pd.DataFrame(rows)


def report(t: pd.DataFrame) -> None:
    f, mk, a, b = forecasts(t), market(t), worth(t, 1.1), worth(t, 1.3)
    print("## 1. Log loss by quarter, winners only, nothing scratched after the open (lower is better)\n")
    print("| quarter | races | TAB's first book | ours alone | blend, held | BSP | TAB's first book minus BSP "
          "| ours minus BSP | blend minus BSP |\n|---|---|---|---|---|---|---|---|---|")
    for _, r in f.iterrows():
        print(f"| {r.quarter} | {r.races:,} | {r.tab:.4f} | {r.ours:.4f} | {r.blend:.4f} | {r.bsp:.4f} | "
              f"{r.tab - r.bsp:+.4f} | {r.ours - r.bsp:+.4f} | {r.blend - r.bsp:+.4f} |")
    print("\n## 2. TAB's market and the held blend's candidates by quarter\n")
    print("| quarter | TAB's mean book | median hours from its first price to the jump | first priced 6pm to midnight "
          "| first priced a day or more ahead | from 1.1x: bets with a BSP | worth a bet by BSP | its standard error "
          "| realised flat ROI | from 1.3x: bets with a BSP | worth a bet by BSP | realised flat ROI |\n"
          "|---|---|---|---|---|---|---|---|---|---|---|---|")
    x = mk.merge(a, on="quarter", how="left").merge(b, on="quarter", how="left", suffixes=("", "3"))
    for _, r in x.iterrows():
        def pc(v):
            return "" if pd.isna(v) else f"{v:+.1%}"
        print(f"| {r.quarter} | {r.book:.1%} | {r.hours:.1f} | {r.night:.0%} | {r.day:.0%} | {int(r.n):,} | "
              f"{pc(r.bsp)} | {'' if pd.isna(r.se) else f'{r.se:.1%}'} | {pc(r.flat)} | {int(r.n3):,} | "
              f"{pc(r.bsp3)} | {pc(r.flat3)} |")


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 49, the edge quarter by quarter\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    x = R47.field(d, bdir, t0)
    t = x[x.is_ran.astype(bool).values].reset_index(drop=True)
    print(f"Every race at TAB's first price: {t.race_id.nunique():,} races, {len(t):,} runners that ran, "
          f"{t.date.min():%b %Y} to {t.date.max():%b %Y}. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    report(t)
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 49")
