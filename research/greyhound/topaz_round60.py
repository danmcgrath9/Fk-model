"""Round 60: where does the first-tip edge live? Mapped by BSP corrected for its first-tip lean (16 Nov 2026, founder:
"Well keep testing and lets get a fucking good model"; "we will win long term on opening")

Tests 75 to 77: since February 2025 the card's edge is GRV's first tip priced long at TAB's open (85 of its 98 bets), and
the fair judge of a first-tip bet is BSP corrected for its first-tip lean. Stated before the run, on round 58's field and
corrected BSP, the card's blend (held, no Isolynx), every candidate in the card's band (our odds 2 to 15) with an edge
of 1.1 or over that is GRV's first tip, flat, at TAB's first price after TAB's deduction:

  - one row per slice value: candidates, the corrected BSP's return per bet with its standard error in each half (May
    2023 to January 2025, and since February 2025), the realised flat ROI in each half, and the card's bets at 1.3x
    since February 2025
  - the slices: GRV's best bet, TAB's order of the dog, our odds, the edge, TAB's book at its first price, the hours
    from TAB's first price to the jump, track, box, grade, the field at the bet, and the dog's starts
  - a slice is strong if its corrected return per bet is at least two standard errors above all first-tip candidates'
    in BOTH halves, and weak if at least two below in both; anything else is not a finding

It is a map, not a rule: a slice that is strong here is tested forward before it reaches the card.

    python research/greyhound/topaz_round60.py DIR LABEL    (as round 51)

Counts, sums and rates only: no race, dog or price is printed (tracks are named).
"""
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round36 as R36       # noqa: E402
import topaz_round37 as R37       # noqa: E402
import topaz_round42 as R42       # noqa: E402
import topaz_round44 as R44       # noqa: E402
import topaz_round47 as R47       # noqa: E402
import topaz_round55 as R55       # noqa: E402
import topaz_round57 as R57       # noqa: E402
import topaz_round58 as R58       # noqa: E402

HALVES = [("to Jan 2025", "2023-05-01", "2025-02-01"), ("since Feb 2025", "2025-02-01", None)]
TOP_TRACKS = 10


def slices(t: pd.DataFrame) -> dict:
    """Each slice: (a label per runner, the order its values print in)."""
    counts = t.track.value_counts()
    top = list(counts.index[:TOP_TRACKS])
    bb = R55.col(t, "is_best_bet")
    order = t.groupby("race_id").p_book.rank(ascending=False, method="first")
    box = R55.col(t, "box").astype("Int64").astype(str)
    edge = t.price * t.pb6
    out = {
        "GRV's best bet": (pd.Series(np.where(bb.isna(), "unknown", np.where(bb > 0, "best bet", "not")), index=t.index),
                           ["best bet", "not", "unknown"]),
        "TAB's order": R47.cut(order, [1, 2, 3, 100], ["favourite", "second", "third or longer"]),
        "our odds": R47.cut(1 / t.pb6, [2, 3, 5, 8, 15], ["2 to 3", "3 to 5", "5 to 8", "8 to 15"]),
        "the edge": R47.cut(edge, [1.1, 1.2, 1.3, 1.5, 100], ["1.1 to 1.2", "1.2 to 1.3", "1.3 to 1.5", "1.5 and over"]),
        "TAB's book at its first price": R47.cut(t.tab_book * 100, [0, 125, 135, 145, 1000],
                                                 ["under 125%", "125 to 135%", "135 to 145%", "145% and over"]),
        "hours from TAB's first price to the jump": R47.cut(t.to_jump, [0, 6, 12, 24, 10_000],
                                                            ["under 6", "6 to 12", "12 to 24", "24 and over"]),
        "track": (t.track.where(t.track.isin(top), "other tracks"), top + ["other tracks"]),
        "box": (box, sorted(box.unique(), key=lambda b: (not b.isdigit(), b))),
        "grade": R47.cut(R55.col(t, "race_class"), [0, 4.5, 5.5, 7.5, 9],
                         ["grade 4 or better", "grade 5", "grade 6, 7, novice", "maiden"]),
        "the field at the bet": R47.cut(t.n_bet.astype(float), [0, 7, 8, 99], ["6 or fewer", "7", "8"]),
        "starts before the race": R47.cut(R55.col(t, "runs"), [0, 4, 11, 31, 10_000],
                                          ["under 4", "4 to 10", "11 to 30", "31 or more"]),
    }
    return {k: (pd.Series(v, index=t.index).astype(str), o) for k, (v, o) in out.items()}


def verdict(a: dict, base: dict) -> str:
    """'strong' or 'weak' in one half: at least two standard errors above or below all first-tip candidates."""
    if not a.get("n") or a["n"] < 2 or np.isnan(a["se"]) or not base.get("n"):
        return ""
    if a["bsp"] - base["bsp"] >= 2 * a["se"]:
        return "strong"
    if a["bsp"] - base["bsp"] <= -2 * a["se"]:
        return "weak"
    return ""


def fmt(a: dict, key: str = "bsp") -> str:
    if not a.get("n"):
        return ""
    return f"{a[key]:+.1%}" + (f" ({a['se']:.1%})" if key == "bsp" and a["n"] > 1 else "")


def table(t: pd.DataFrame, cand: np.ndarray, card13: np.ndarray, paid: np.ndarray, sl: dict) -> list:
    tq = t.assign(p_bsp=t.q_bsp)
    halves = [R36.in_period(t, lo, hi) for _, lo, hi in HALVES]
    base = [R44.judged(tq, cand & h, paid) for h in halves]
    print("| slice | value | candidates | corrected BSP per bet, " + HALVES[0][0] + " | " + HALVES[1][0]
          + " | realised flat ROI, " + HALVES[0][0] + " | " + HALVES[1][0] + " | the card's bets since Feb 2025 | "
          "verdict |\n|" + "---|" * 9)
    print(f"| all first tips | | {int(cand.sum()):,} | {fmt(base[0])} | {fmt(base[1])} | {fmt(base[0], 'flat')} | "
          f"{fmt(base[1], 'flat')} | {int((card13 & halves[1]).sum())} | |")
    found = []
    for name, (lab, order) in sl.items():
        for v in order:
            g = (lab == v).values & cand
            if not g.any():
                continue
            a = [R44.judged(tq, g & h, paid) for h in halves]
            vs = [verdict(a[i], base[i]) for i in range(2)]
            out = vs[0] if vs[0] and vs[0] == vs[1] else ""
            if out:
                found.append((name, v, out))
            print(f"| {name} | {v} | {int(g.sum()):,} | {fmt(a[0])} | {fmt(a[1])} | {fmt(a[0], 'flat')} | "
                  f"{fmt(a[1], 'flat')} | {int((card13 & halves[1] & (lab == v).values).sum())} | {out} |")
    return found


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 60, where does the first-tip edge live? Mapped by the corrected BSP\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    if not os.environ.get("WALK_CACHE_USE", "").strip() or not os.environ.get("WALK_ISO_USE", "").strip():
        print("Both saved walks must be named (WALK_CACHE_USE and WALK_ISO_USE): nothing to test")
        return 1
    t, _ = R57.field(d, t0)
    t["q_bsp"], _ = R58.corrected_bsp(t)
    t["pb6"] = t.h_p_x_bet
    t["tab_book"] = (1 / t.price).groupby(t.race_id.values).transform("sum")
    t["n_bet"] = t.groupby("race_id").race_id.transform("size")
    ot = R47.open_times(bdir)
    t = t.merge(ot, on="bw_race", how="left")
    t["to_jump"] = (t.start_t - t.open_t) / 3600
    tip1 = R55.col(t, "tip_rank").values == 1
    m, e, paid = R42.candidates(t, "pb6")
    cand = m & (e >= 1.1) & tip1
    card13 = R37.rule(t, "pb6", 1.3)[0] & tip1
    print(f"\nField at TAB's first price from May 2023: {t.race_id.nunique():,} races, {len(t):,} runners that ran; "
          f"{int(cand.sum()):,} first-tip candidates from 1.1x; TAB's first price time known for "
          f"{t.open_t.notna().mean():.1%}. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    print("Corrected BSP's return per bet (its standard error), realised flat ROI, flat after TAB's deduction:\n")
    found = table(t, cand, card13, paid, slices(t))
    print(f"\nStrong or weak in both halves: {len(found)}")
    for name, v, out in found:
        print(f"- {name}, {v}: {out}")
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 60")
