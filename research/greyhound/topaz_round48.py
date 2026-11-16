"""Round 48: the edge map's leads, on the Betwatch years before them (16 Nov 2026, founder: "Well keep testing and lets
get a fucking good model")

Test 65 mapped the held blend's edge from February 2025 slice by slice, judged by BSP, and found three leads where
both halves agreed and BSP was a fair judge, one weak slice, and two slices where BSP's own price was too short:

  leads:  TAB's first price 24 hours or more before the jump (48 or more: +50.4% a bet by BSP, 39 bets), six or fewer
          runners at the bet (+15.0%), 450 to 549 m (+12.7%)
  weak:   grade 5 (+3.6%)
  misses: maidens (27 winners where BSP expected 38.3) and races from 7pm (104 against 113.3)

Stated before the run, the same measures on the Betwatch years no test of these slices has looked at: May 2023 to
January 2025 (the held blend's two weights were fitted on December 2023 to June 2024, inside them, but the slices
never were). A lead holds if it is again above the rest by more than its standard error; a miss holds if BSP again
expects too many winners. Then the whole Test 65 map on the same years, for the record.

    python research/greyhound/topaz_round48.py DIR LABEL    (as round 47)

Counts, sums and rates only: no race, dog or price is printed (tracks are named).
"""
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round42 as R42       # noqa: E402
import topaz_round47 as R47       # noqa: E402

TO = R42.SINCE                    # the years before Test 65's window
SPLIT = "2024-05-01"
HALVES = ("May 2023 to Apr 2024", "May 2024 to Jan 2025")


def two(mask: np.ndarray, yes: str, no: str, index) -> tuple:
    return pd.Series(np.where(mask, yes, no), index=index), [yes, no]


def leads(t: pd.DataFrame) -> dict:
    """The slices Test 65 named, each against the rest, stated before the run."""
    j, cls, ix = t.to_jump, t.race_class if "race_class" in t else pd.Series(np.nan, index=t.index), t.index
    d = t.distance.astype(float)
    return {
        "every candidate": (pd.Series("all", index=ix), ["all"]),
        "TAB's first price to the jump": two((j >= 24).values, "24 hours or more", "under 24 hours", ix),
        "TAB's first price to the jump, 48": two((j >= 48).values, "48 hours or more", "under 48 hours", ix),
        "field at the bet": two((t.n_bet <= 6).values, "6 or fewer", "7 or 8", ix),
        "distance": two(((d >= 450) & (d < 550)).values, "450 to 549 m", "other distances", ix),
        "class": (pd.Series(np.select([cls.values == 5, cls.values == 8], ["grade 5", "maiden"], "other classes"),
                            index=ix), ["grade 5", "maiden", "other classes"]),
        "Melbourne hour of the race": two((t.start_hour >= 19).values, "7pm and later", "before 7pm", ix),
    }


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 48, the edge map's leads, on the Betwatch years before them\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    x = R47.field(d, bdir, t0)
    t = x[x.is_ran.astype(bool).values & (x.date < TO).values].reset_index(drop=True)
    print(f"Every race before February 2025 at TAB's first price: {t.race_id.nunique():,} races, {len(t):,} runners "
          f"that ran, {t.date.min():%b %Y} to {t.date.max():%b %Y}; TAB's first price time known for "
          f"{t.open_t.notna().mean():.1%}. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    print("## 1. The slices Test 65 named, each against the rest\n")
    R47.table(t, SPLIT, HALVES, leads(t))
    print("\n## 2. The whole map on the same years\n")
    R47.table(t, SPLIT, HALVES)
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 48")
