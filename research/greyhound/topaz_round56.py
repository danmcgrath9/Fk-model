"""Round 56: what does the card's blend get wrong? The calibration scan, both halves, every forecast (16 Nov 2026,
founder: "Well keep testing and lets get a fucking good model"; "we will win long term on opening")

Test 73: TAB's first book, normalised to chances, has a strong favourite-longshot bias (favourites at A/E 1.15, fourth
and longer at 0.83), and most of the leans its scan found line up with that order. The card's blend already removes it.
The question worth answering is what the card's blend gets wrong. Stated before the run, on round 50's prices (both
saved walks read by name), every race with nothing scratched after the open and a BSP on every runner:

  - five forecasts: TAB's first book after its favourite-longshot bias (TAB's chances alone refitted with one power on
    Test 51's window, December 2023 to June 2024, and held), the card's blend, the blend with Isolynx (both at
    0.54 / 0.67), ours with Isolynx, and BSP
  - runner-level groups only: GRV's tip, GRV's best bet, box, starts before the race, days since the last run, the class
    step, the trainer's runs, age, TAB's order, the weight change, and the early-speed order within the race
  - for each value and forecast, winners against the chances given (A/E and z) in each half (May 2023 to January 2025,
    and since February 2025); a lean counts only with |z| of 2 or more in both halves and the same sign
  - a lean the card's blend has and BSP does not is one the card might use, and one BSP's verdict can see

    python research/greyhound/topaz_round56.py DIR LABEL    (as round 51)

Counts, sums and rates only: no race, dog or price is printed.
"""
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round36 as R36       # noqa: E402
import topaz_round47 as R47       # noqa: E402
import topaz_round51 as R51       # noqa: E402
import topaz_round53 as R53       # noqa: E402
import topaz_round55 as R55       # noqa: E402

MODELS = {"TAB after its favourite bias": "p_tab_fl", "the card's blend": "h_p_x_bet",
          "blend with Isolynx": "h_p_i_bet", "ours with Isolynx": "p_i_bet", "BSP": "p_bsp"}
RACE_LEVEL = ("the field at the bet", "distance", "grade")


def runner_groups(t: pd.DataFrame) -> dict:
    """Round 55's groups less the race-level ones, plus the weight change and the early-speed order in the race."""
    g = {k: v for k, v in R55.groups(t).items() if k not in RACE_LEVEL}
    wc = R55.col(t, "weight_change")
    g["the weight change"] = (pd.Series(np.select([wc <= -0.5, wc >= 0.5, wc.notna()],
                                                  ["down 0.5 kg or more", "up 0.5 kg or more", "within 0.5 kg"],
                                                  "unknown"), index=t.index),
                              ["down 0.5 kg or more", "within 0.5 kg", "up 0.5 kg or more", "unknown"])
    early = R55.col(t, "style_early")
    rank = early.groupby(t.race_id.values).rank(method="first")          # lower style_early is more early speed
    lab, order = R47.cut(rank, [1, 2, 3, 4, 100], ["most early speed", "second", "third", "fourth and later"])
    g["the early-speed order"] = (pd.Series(lab, index=t.index).astype(str), order)
    return g


def scan(t: pd.DataFrame, gs: dict, models: dict = None) -> list:
    """One row per group value: A/E (z) per forecast per half; returns (group, value, forecast, direction) leans."""
    models = MODELS if models is None else models
    halves = [R36.in_period(t, lo, hi) for _, lo, hi in R55.HALVES]
    won = t.won.values
    print("| group | value | runners | winners | " + " | ".join(models) + " | leans in both halves |\n|"
          + "---|" * (5 + len(models)))
    found = []
    for gname, (lab, order) in gs.items():
        for v in order:
            g = (lab == v).values
            if not g.any():
                continue
            cells, leans = [], []
            for name, c in models.items():
                a = R53.ae(won[g & halves[0]], t[c].values[g & halves[0]])
                b = R53.ae(won[g & halves[1]], t[c].values[g & halves[1]])
                cells.append(f"{R55.fmt(a)} / {R55.fmt(b)}")
                flag = R55.lean(a, b)
                if flag:
                    leans.append(name)
                    found.append((gname, v, name, flag.replace("TAB", "it")))
            print(f"| {gname} | {v} | {int(g.sum()):,} | {int(won[g].sum()):,} | " + " | ".join(cells) + " | "
                  + ", ".join(leans) + " |")
    return found


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 56, what does the card's blend get wrong? The calibration scan, both halves\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    if not os.environ.get("WALK_CACHE_USE", "").strip() or not os.environ.get("WALK_ISO_USE", "").strip():
        print("Both saved walks must be named (WALK_CACHE_USE and WALK_ISO_USE): nothing to test")
        return 1
    t = R53.prepare(d, t0)
    w = R51.fit_weights(t, ["p_book"], *R51.FIT)
    t["p_tab_fl"] = R51.apply_weights(t, ["p_book"], w)
    print(f"\nRaces with nothing scratched after the open and a BSP on every runner, from May 2023: "
          f"{t.race_id.nunique():,} races, {len(t):,} runners. TAB's first book after its favourite bias: its chances "
          f"to the power {w[0]:.3f}, renormalised (fitted on Dec 2023 to Jun 2024). "
          f"{(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    print("Winners against the chances given, A/E (z), May 2023 to Jan 2025 / since Feb 2025:\n")
    found = scan(t, runner_groups(t))
    print(f"\nLeans in both halves (|z| {R55.Z:g} or more, same sign): {len(found)}\n")
    by = {}
    for gname, v, name, flag in found:
        by.setdefault((gname, v), {})[name] = flag
    for (gname, v), m in by.items():
        card = m.get("the card's blend", "")
        note = (" (BSP too)" if "BSP" in m else " (not BSP)") if card else ""
        print(f"- {gname}, {v}: " + "; ".join(f"{k} ({f})" for k, f in m.items()) + note)
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 56")
