"""Round 52: the blends compared at the same number of bets, and where Isolynx's gain lands (16 Nov 2026, founder:
"Well keep testing and lets get a fucking good model")

Test 69: refitting the blend for ours with Isolynx forecasts no better, and each weighting picks a different point on
one trade-off, more bets or better bets. Comparing blends by the bets each makes at 1.3x mixes that trade-off with how
good the model is. Stated before the run, on round 50's prices (both saved walks read by name, as round 51):

  1. the four blends of Test 69 (with and without Isolynx, at 0.54 / 0.67 and refitted on Test 51's window), each with
     its candidates in the card's band (our odds 2 to 15) that have a BSP, ranked by edge (TAB's first price x the
     blend's chance), and the best 50, 100, 200, 400, 800 and 1,600 since February 2025 judged by BSP, flat, after
     TAB's deduction. A better model gives better bets at every count. The counts are set over the whole period, which
     is a look ahead, but the same look ahead for every blend
  2. the same in each half (to January 2026, and since) at half the counts
  3. the same split by the race (at one of the tracks Isolynx covers or not) and by the runner (a tracked run before the
     race or not), at 25, 50, 100, 200 and 400
  4. log loss of ours and of each blend, split the same two ways, from May 2023 to January 2025 and since February 2025

    python research/greyhound/topaz_round52.py DIR LABEL    (as round 51)

Counts, sums and rates only: no race, dog or price is printed (tracks are named by group only).
"""
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round18 as R18       # noqa: E402
import topaz_round33 as R33       # noqa: E402
import topaz_round36 as R36       # noqa: E402
import topaz_round42 as R42       # noqa: E402
import topaz_round44 as R44       # noqa: E402
import topaz_round50 as R50       # noqa: E402
import topaz_round51 as R51       # noqa: E402

NS = (50, 100, 200, 400, 800, 1600)
SPLIT_NS = (25, 50, 100, 200, 400)
SINCE = "2025-02-01"
HALVES = [("Feb 2025 to Jan 2026", "2025-02-01", "2026-02-01"), ("Feb 2026 on", "2026-02-01", None)]
LL_PERIODS = [("May 2023 to Jan 2025", "2023-05-01", "2025-02-01"), ("Feb 2025 on", "2025-02-01", None)]
BLENDS = {"no Isolynx, 0.54 / 0.67 (the card)": "h_p_x_bet", "with Isolynx, 0.54 / 0.67": "h_p_i_bet",
          "no Isolynx, refitted": "r_p_x_bet", "with Isolynx, refitted": "r_p_i_bet"}


def top_n(t: pd.DataFrame, col: str, mask: np.ndarray, n: int):
    """The n candidates in the card's band with a BSP and the highest edge under this blend, within mask: (the bets,
    the price paid, the edge of the last one in). None when fewer than n are there."""
    m, e, paid = R42.candidates(t.assign(_pb=t[col].fillna(0)), "_pb")
    idx = np.flatnonzero(m & mask & t.p_bsp.notna().values & np.isfinite(e))
    if len(idx) < n:
        return None, paid, np.nan
    pick = idx[np.argsort(-e[idx], kind="stable")][:n]
    x = np.zeros(len(t), bool)
    x[pick] = True
    return x, paid, float(e[pick[-1]])


def ladder(t: pd.DataFrame, groups: dict, ns: tuple) -> None:
    print("| group | blend | best | edge of the last one in | " + R44.HEAD + " |\n|" + "---|" * 12)
    for gname, g in groups.items():
        for n in ns:
            for name, col in BLENDS.items():
                x, paid, edge = top_n(t, col, g, n)
                if x is None:
                    print(f"| {gname} | {name} | {n} | fewer candidates |" + " |" * 8)
                    continue
                print(f"| {gname} | {name} | {n} | {edge:.2f} | " + " | ".join(R44.cells(R44.judged(t, x, paid)))
                      + " |")


def splits(t: pd.DataFrame) -> dict:
    """Race at a tracked track or not; runner with a tracked run before the race or not."""
    tracked = t.track.astype(str).str.upper().isin(R18.TRACKED).values
    runs = t.iso_runs.fillna(0).values if "iso_runs" in t else np.full(len(t), np.nan)
    return {"at a tracked track": tracked, "at the other tracks": ~tracked,
            "runner with a tracked run before": runs > 0, "runner with none": runs == 0}


def ll_split(t: pd.DataFrame, groups: dict) -> None:
    clean = t[(t.n_later == 0).values]
    full = clean.p_bsp.notna().groupby(clean.race_id.values).transform("all").to_numpy(copy=True)
    w = clean[full & (clean.won == 1).values]
    gw = {k: v[(t.n_later == 0).values][full & (clean.won == 1).values] for k, v in groups.items()}
    cols = {"TAB's first book": "p_book", "ours, no Isolynx": "p_x_bet", "ours, with Isolynx": "p_i_bet", **BLENDS,
            "BSP": "p_bsp"}
    print("Log loss on the winners (a runner group is the group the winner is in):\n\n| period | group | winners | "
          + " | ".join(cols) + " |\n|" + "---|" * (len(cols) + 3))
    for pname, lo, hi in LL_PERIODS:
        p = R36.in_period(w, lo, hi)
        for gname, g in gw.items():
            s = w[p & g]
            if len(s):
                print(f"| {pname} | {gname} | {len(s):,} | " + " | ".join(f"{R50.ll(s, c):.4f}" for c in cols.values())
                      + " |")


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 52, the blends at the same number of bets, and where Isolynx's gain lands\n")
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
    x = x[ok].reset_index(drop=True)
    print("\n| blend | fitted on | ours | TAB |\n|---|---|---|---|")
    for name, c in R51.OURS.items():
        x[f"h_{c}"] = R51.apply_weights(x, [c, "p_book"], R50.FIXED)
        wb = R51.fit_weights(x, [c, "p_book"], *R51.FIT)
        x[f"r_{c}"] = R51.apply_weights(x, [c, "p_book"], wb)
        print(f"| {name} | Test 51, held | {R50.FIXED[0]:.2f} | {R50.FIXED[1]:.2f} |\n"
              f"| {name} | Dec 2023 to Jun 2024 | {wb[0]:.2f} | {wb[1]:.2f} |")
    t = x[x.is_ran.astype(bool).values].reset_index(drop=True)
    g = splits(t)
    tr = g["at a tracked track"]
    print(f"\nField at TAB's first price from May 2023: {t.race_id.nunique():,} races, {len(t):,} runners that ran; "
          f"{t.race_id[tr].nunique():,} races at a tracked track; a tracked run before the race for "
          f"{g['runner with a tracked run before'].mean():.0%} of runners "
          f"({g['runner with a tracked run before'][tr].mean():.0%} at a tracked track). "
          f"{(time.monotonic() - t0) / 60:.0f} minutes in.\n")

    since = R36.in_period(t, SINCE, None)
    print("## 1. The best N candidates by edge since February 2025, judged by BSP, flat\n")
    ladder(t, {"every race": since}, NS)
    print("\n## 2. In each half, at half the counts\n")
    ladder(t, {h: R36.in_period(t, lo, hi) for h, lo, hi in HALVES}, tuple(n // 2 for n in NS))
    print("\n## 3. Split by the race and by the runner, since February 2025\n")
    ladder(t, {k: v & since for k, v in g.items()}, SPLIT_NS)
    print("\n## 4. Where the forecasting gain is\n")
    ll_split(t, g)
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 52")
