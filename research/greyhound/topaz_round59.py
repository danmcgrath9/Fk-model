"""Round 59: the threshold and the stake, re-judged by BSP corrected for its first-tip lean (16 Nov 2026, founder:
"Well keep testing and lets get a fucking good model")

Test 76: BSP over-rates GRV's first tip (A/E 0.965, then 0.963), and since February 2025 most of the card's bets are
first tips. Corrected out of sample, BSP rates the card's bets at +40.8% a bet flat, not +46.1%, and the thin-edged
candidates below the card's line lower still. Two of the founder's open decisions rest on BSP's figures: the threshold
(Test 63 valued the bets 1.2x adds at +14% a unit) and the stake (Test 64's 10,000 replays drew each dog's win from
BSP's chance). Stated before the run, on round 58's field and corrected BSP, the held blend without Isolynx (the card):

  1. Test 63 again: the card's rule at 1.3x and 1.2x and the bets 1.2x adds, on the card's stake and on Kelly on the
     model (x75, cap 4), in each period: bets, winners, BSP's and the corrected BSP's expected winners, units staked,
     realised units, and both judges' units and return per unit
  2. Test 64's replays again, 10,000 of the same bets since February 2025 for each stake (the card's, Kelly on the
     model, one unit flat), each dog winning with BSP's chance and then with the corrected chance: the median, the 5th
     and 95th percentile of units won, the chance of being behind, and the median and 95th percentile worst drawdown

    python research/greyhound/topaz_round59.py DIR LABEL    (as round 51)

Counts, sums and rates only: no race, dog or price is printed.
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round36 as R36       # noqa: E402
import topaz_round43 as R43       # noqa: E402
import topaz_round45 as R45       # noqa: E402
import topaz_round46 as R46       # noqa: E402
import topaz_round57 as R57       # noqa: E402
import topaz_round58 as R58       # noqa: E402

JUDGES = {"BSP": "p_bsp", "BSP corrected": "q_bsp"}


def both(t, x, paid, u) -> dict:
    """R45.judged under each judge, on the bets that have a corrected chance (so both judge the same bets)."""
    y = x & t.q_bsp.notna().values
    out = {}
    for name, c in JUDGES.items():
        out[name] = R45.judged(t.assign(p_bsp=t[c]), y, paid, u)
    return out


def threshold_table(t) -> None:
    print("| period | stake | bets | bets judged | winners | BSP's expected | corrected expected | units staked | "
          "realised units | BSP's units | per unit | corrected units | per unit |\n|" + "---|" * 13)
    for pname, lo, hi in R43.PERIODS:
        p = R36.in_period(t, lo, hi)
        for stake in R45.STAKES:
            m13, paid, u13 = R45.bets(t, "pb6", 1.3, stake)
            m12, _, u12 = R45.bets(t, "pb6", 1.2, stake)
            for lab, x, u in (("1.3x", m13 & p, u13), ("1.2x", m12 & p, u12), ("1.2x, not 1.3x", m12 & ~m13 & p, u12)):
                j = both(t, x, paid, u)
                a, b = j["BSP"], j["BSP corrected"]
                if not a["n"]:
                    print(f"| {pname} | {stake}, {lab} | {int(x.sum())} | 0 |" + " |" * 9)
                    continue
                print(f"| {pname} | {stake}, {lab} | {int(x.sum()):,} | {a['n']:,} | {a['w']:,} | {a['e']:,.1f} | "
                      f"{b['e']:,.1f} | {a['staked']:,.0f} | {a['real']:+,.1f} | {a['bsp']:+,.1f} | "
                      f"{a['bsp'] / a['staked']:+.1%} | {b['bsp']:+,.1f} | {b['bsp'] / b['staked']:+.1%} |")


def replay_table(t) -> None:
    since = R36.in_period(t, "2025-02-01", None) & t.q_bsp.notna().values
    print(f"| stake | judge | bets | median units won | 5th percentile | 95th percentile | chance of being behind | "
          f"median worst drawdown | 95th percentile worst drawdown | as a share of a {R46.BANK:.0f}-unit bank |\n|"
          + "---|" * 10)
    for stake in R46.STAKES:
        m, paid, u = R46.stake_bets(t, stake)
        for name, c in JUDGES.items():
            s = R46.replays(t.assign(p_bsp=t[c]), m & since, paid, u)
            print(f"| {stake} | {name} | {s['n']:,} | {s['med']:+,.1f} | {s['p5']:+,.1f} | {s['p95']:+,.1f} | "
                  f"{s['behind']:.1%} | {s['dd50']:,.1f} | {s['dd95']:,.1f} | {s['dd95'] / R46.BANK:.0%} |")


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 59, the threshold and the stake, re-judged by the corrected BSP\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    if not os.environ.get("WALK_CACHE_USE", "").strip() or not os.environ.get("WALK_ISO_USE", "").strip():
        print("Both saved walks must be named (WALK_CACHE_USE and WALK_ISO_USE): nothing to test")
        return 1
    t, _ = R57.field(d, t0)
    t["q_bsp"], _ = R58.corrected_bsp(t)
    t["pb6"] = t.h_p_x_bet
    print(f"\nField at TAB's first price from May 2023: {t.race_id.nunique():,} races, {len(t):,} runners that ran. "
          f"{(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    print("## 1. Test 63 again: the threshold and the stake, both judges (on the bets with a corrected chance)\n")
    threshold_table(t)
    print(f"\n## 2. Test 64 again: {R46.REPLAYS:,} replays of the same bets since February 2025\n")
    replay_table(t)
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 59")
