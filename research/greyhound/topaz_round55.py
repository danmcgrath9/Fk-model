"""Round 55: where is TAB's opening price wrong? A calibration scan by group (16 Nov 2026, founder: "Well keep testing
and lets get a fucking good model"; "we will win long term on opening")

Test 71 found a lean in TAB's first price by checking its calibration across one group: in a mixed race it under-rates
the dogs with a tracked run (A/E 1.041, z +3.1, then 1.018). An edge at TAB's open has to come from where its price
is wrong, so this scans other groups the same way. Stated before the run, on round 50's prices (both saved walks read by
name), every race with nothing scratched after the open and a BSP on every runner:

  - for each group value: runners, winners, and winners against the chances given (A/E and z) for TAB's first book in
    each half (May 2023 to January 2025, and since February 2025), and since February 2025 for ours with Isolynx, the
    card's blend, the blend with Isolynx at 0.54 / 0.67 and BSP
  - the groups: GRV's tip (first tip, second to fourth, not tipped, no tips record), GRV's best bet, box, starts before
    the race, days since the last run, the class step, the trainer's runs, age, TAB's own order (favourite, second,
    third, fourth and longer), the field at the bet, distance and grade
  - a lean counts only if TAB's first book has |z| of 2 or more in BOTH halves with the same sign. Chances sum to one
    in each race, so a lean in one value is always balanced by the others in its group

    python research/greyhound/topaz_round55.py DIR LABEL    (as round 51)

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
import topaz_round53 as R53       # noqa: E402

HALVES = [("May 2023 to Jan 2025", "2023-05-01", "2025-02-01"), ("Feb 2025 on", "2025-02-01", None)]
SINCE_MODELS = {"ours, with Isolynx": "p_i_bet", "the card's blend": "h_p_x_bet", "blend with Isolynx": "h_p_i_bet",
                "BSP": "p_bsp"}
Z = 2.0


def col(t: pd.DataFrame, name: str) -> pd.Series:
    return t[name].astype(float) if name in t else pd.Series(np.nan, index=t.index)


def groups(t: pd.DataFrame) -> dict:
    """Each group: (a label per runner, the order its values print in). Missing values are 'unknown'."""
    tip = col(t, "tip_rank")
    tip_lab = pd.Series(np.select([tip == 1, tip.between(2, 4), tip == 0], ["first tip", "second to fourth tip",
                                                                            "not tipped"], "no tips record"),
                        index=t.index)
    bb = col(t, "is_best_bet")
    bb_lab = pd.Series(np.where(bb.isna(), "unknown", np.where(bb > 0, "best bet", "not")), index=t.index)
    order = t.groupby("race_id").p_book.rank(ascending=False, method="first")
    box = col(t, "box").astype("Int64").astype(str)
    out = {
        "GRV's tip": (tip_lab, ["first tip", "second to fourth tip", "not tipped", "no tips record"]),
        "GRV's best bet": (bb_lab, ["best bet", "not", "unknown"]),
        "box": (box, sorted(box.unique(), key=lambda b: (not b.isdigit(), b))),
        "starts before the race": R47.cut(col(t, "runs"), [0, 1, 4, 11, 10_000],
                                          ["first start", "1 to 3", "4 to 10", "11 or more"]),
        "days since the last run": R47.cut(col(t, "days_since"), [0, 8, 15, 29, 61, 100_000],
                                           ["under 8", "8 to 14", "15 to 28", "29 to 60", "61 or more"]),
        "class step": (pd.Series(np.select([col(t, "class_step") > 0, col(t, "class_step") < 0,
                                            col(t, "class_step") == 0], ["dropping in class", "rising in class",
                                                                         "same class"], "unknown"), index=t.index),
                       ["dropping in class", "same class", "rising in class", "unknown"]),
        "the trainer's runs": R47.cut(col(t, "trainer_runs"), [0, 50, 300, 1_000, 10_000_000],
                                      ["under 50", "50 to 299", "300 to 999", "1,000 or more"]),
        "age": R47.cut(col(t, "age_days") / 365.25, [0, 2, 3, 4, 100],
                       ["under 2 years", "2 to 3", "3 to 4", "4 and over"]),
        "TAB's order": R47.cut(order, [1, 2, 3, 4, 100], ["favourite", "second", "third", "fourth and longer"]),
        "the field at the bet": R47.cut(t.groupby("race_id").race_id.transform("size").astype(float), [0, 7, 8, 99],
                                        ["6 or fewer", "7", "8"]),
        "distance": R47.cut(col(t, "distance"), [0, 350, 450, 550, 10_000],
                            ["under 350 m", "350 to 449 m", "450 to 549 m", "550 m and over"]),
        "grade": R47.cut(col(t, "race_class"), [0, 4.5, 5.5, 7.5, 9],
                         ["grade 4 or better", "grade 5", "grade 6, 7, novice", "maiden"]),
    }
    return {k: (pd.Series(v, index=t.index).astype(str), o) for k, (v, o) in out.items()}


def fmt(s: dict) -> str:
    return "" if not s["n"] or np.isnan(s["ae"]) else f"{s['ae']:.3f} ({s['z']:+.1f})"


def lean(a: dict, b: dict, z: float = Z) -> str:
    """'wins more than TAB says' when TAB's first book under-rates the value in both halves (z at least z), 'wins less
    than TAB says' when it over-rates it in both (z at most -z), '' otherwise."""
    if not a["n"] or not b["n"] or np.isnan(a["z"]) or np.isnan(b["z"]):
        return ""
    if a["z"] >= z and b["z"] >= z:
        return "wins more than TAB says"
    if a["z"] <= -z and b["z"] <= -z:
        return "wins less than TAB says"
    return ""


def scan(t: pd.DataFrame, gs: dict) -> list:
    halves = [R36.in_period(t, lo, hi) for _, lo, hi in HALVES]
    won = t.won.values
    print("| group | value | runners | winners | TAB's first book, " + HALVES[0][0] + " | TAB's first book, "
          + HALVES[1][0] + " | " + " | ".join(f"{k}, {HALVES[1][0]}" for k in SINCE_MODELS) + " | lean in both "
          "halves |\n|" + "---|" * (7 + len(SINCE_MODELS)))
    found = []
    for gname, (lab, order) in gs.items():
        for v in order:
            g = (lab == v).values
            if not g.any():
                continue
            a = R53.ae(won[g & halves[0]], t.p_book.values[g & halves[0]])
            b = R53.ae(won[g & halves[1]], t.p_book.values[g & halves[1]])
            since = [R53.ae(won[g & halves[1]], t[c].values[g & halves[1]]) for c in SINCE_MODELS.values()]
            flag = lean(a, b)
            if flag:
                found.append((gname, v, flag))
            print(f"| {gname} | {v} | {int(g.sum()):,} | {int(won[g].sum()):,} | {fmt(a)} | {fmt(b)} | "
                  + " | ".join(fmt(s) for s in since) + f" | {flag} |")
    return found


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 55, where is TAB's opening price wrong? A calibration scan by group\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    if not os.environ.get("WALK_CACHE_USE", "").strip() or not os.environ.get("WALK_ISO_USE", "").strip():
        print("Both saved walks must be named (WALK_CACHE_USE and WALK_ISO_USE): nothing to test")
        return 1
    t = R53.prepare(d, t0)
    gs = groups(t)
    print(f"\nRaces with nothing scratched after the open and a BSP on every runner, from May 2023: "
          f"{t.race_id.nunique():,} races, {len(t):,} runners. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    print("Winners against the chances given, A/E (z):\n")
    found = scan(t, gs)
    print(f"\nLeans in TAB's first book in both halves (|z| {Z:g} or more, same sign): {len(found)}")
    for gname, v, flag in found:
        print(f"- {gname}, {v}: {flag}")
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 55")
