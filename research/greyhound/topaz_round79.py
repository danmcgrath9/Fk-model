"""Round 79: the best model with only what is known on a live morning (18 Nov 2026, founder: "Port the best model into the
morning program")

Test 88's fit reads the market's history on each dog's earlier runs. Part of that history is how far BSP closed from
TAB's open (dog_mv_*, trainer_mv*, the backed and drifted rates, the trainer's last 90 days), and Betfair publishes
its BSP files about a month after the racing. On a live morning those inputs would be a month stale while the model was
trained on them fresh: the live model would not be the one tested. TAB's own moves and the other books' opening prices
come from Betwatch every night, and GRV's starting price from Topaz the day after, so they are known.

Stated before the run: Test 88's fit walked again (Test 83's inputs, learning rate 0.04, up to 4,000 rounds, the same
refits) without the BSP-based history, beside Test 88's fit (corr_r70), February 2025 on: the inputs dropped, the
distance to BSP, the 2-point margin flat and at a quarter of Kelly on one scale, by half and by three months. Saved as
corr_r79 (column c_v).

    python research/greyhound/topaz_round79.py DIR LABEL    (as round 70)

Counts, sums and rates only: no race, dog or price is printed. The model's inputs are named.
"""
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round58 as R58       # noqa: E402
import topaz_round63 as R63       # noqa: E402
import topaz_round64 as R64       # noqa: E402
import topaz_round67 as R67       # noqa: E402
import topaz_round68 as R68       # noqa: E402
import topaz_round70 as R70       # noqa: E402
import topaz_round73 as R73       # noqa: E402
import topaz_v1 as V1             # noqa: E402

TAG = "r79"
BSP_BASED = r"^(dog_mv|trainer_mv)|^mh_(steam|drift)5$|^mh_tr90_"
OLD, NEW = "Test 88's fit", "known on the morning"


def live_inputs(inputs: list) -> tuple:
    """(the inputs known on a live morning, the BSP-based ones dropped)."""
    drop = [c for c in inputs if re.search(BSP_BASED, c)]
    return [c for c in inputs if c not in drop], drop


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 79, the best model with only what is known on a live morning\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    x, R, XR, q, use, off_tab, tab, inputs = R67.build(d, t0)
    if not R67.read_saved(x, "r70", "c_f"):
        print("Test 88's fit (corr_r70) is not in the walk cache: nothing to compare")
        return 1
    keep, drop = live_inputs(inputs)
    print(f"Inputs: {len(inputs)}; known on the morning: {len(keep)}; dropped as BSP-based: {len(drop)} "
          f"({', '.join(drop)}). {(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    race, dates = R.race_id.values, R.date.values.astype("datetime64[ns]")
    ran = x.is_ran.astype(bool).values
    p, log, share = R70.walk_faster(R.assign(off=off_tab), XR[keep], q, use)
    print("## 1. The walk\n\n" + "; ".join(log) + "\n")
    print("Its inputs by share of gain: " + ", ".join(f"{k} {v:.1%}" for k, v in share.head(20).items()) + "\n")

    t = x[ran].reset_index(drop=True)
    clean = (R.n_later.fillna(0).values == 0)
    pf_r = R70.on_runners(R, t, "c_f")
    ok = use & clean & (dates >= np.datetime64(R64.SPLIT)) & np.isfinite(p) & np.isfinite(pf_r)
    tab_d = R64.distance(tab[ok], q[ok], race[ok])
    print(f"## 2. Distance to BSP, Feb 2025 on, clean races ({int(ok.sum()):,} runners)\n\n| model | distance to BSP "
          "(thousandths) | of TAB's distance closed | winners' log loss |\n|---|---|---|---|")
    for nm, v in ((OLD, pf_r), (NEW, p)):
        dd = R64.distance(v[ok], q[ok], race[ok])
        print(f"| {nm} | {dd:.2f} | {1 - dd / tab_d:+.1%} | {V1.ll(v[ok], R.won.values[ok]):.4f} |")

    s_tab = pd.Series(R.p_book.values).groupby(race).transform("sum").values
    x["c_v"] = x.p_book
    x.loc[R["index"].values, "c_v"] = p * s_tab
    cdir = os.environ.get("WALK_CACHE_DIR", "")
    if cdir:
        Path(cdir).mkdir(parents=True, exist_ok=True)
        x.loc[ran, ["race_id", "dog", "c_v"]].to_csv(Path(cdir) / f"corr_{TAG}.csv.gz", index=False,
                                                     float_format="%.9g")
    t["c_v"], t["c_f"] = x.c_v.values[ran], x.c_f.values[ran]
    t["q_bsp"], _ = R58.corrected_bsp(t)
    tq = t.assign(p_bsp=t.q_bsp)
    paid = R68.paid_price(t)
    models = {OLD: R67.model_chance(t, "c_f"), NEW: R67.model_chance(t, "c_v")}
    periods = [("Feb 2025 on", R63.SINCE, None)] + R63.HALVES
    print("\n## 3. The 2-point margin, fair price under $15, flat\n")
    print("| period | model | bets | a month | A/E | realised flat ROI | realised units | corrected BSP per bet (SE) | "
          "corrected BSP units |\n|" + "---|" * 9)
    for pname, lo, hi in periods:
        per = R63.R36.in_period(t, lo, hi)
        for mname, pm in models.items():
            print(f"| {pname} | {mname} | " + R67.cells(t, tq, R68.margin_bets(t, pm, 0.02) & per, paid,
                                                        R67.months_in(t, per)) + " |")
    since = R63.R36.in_period(t, R63.SINCE, None)
    scale = R73.raw_kelly(models[OLD], paid)[R68.margin_bets(t, models[OLD], 0.02) & since].mean()
    rules = {}
    print(f"\n## 4. The 2-point margin, a quarter of Kelly at one scale ({(time.monotonic() - t0) / 60:.0f} minutes in)\n")
    print("| model | period | bets | units staked | corrected BSP per unit staked (SE) | corrected BSP units | "
          "realised units | luck in the realised units (SD) | deepest fall, realised | losing months |\n|" + "---|" * 10)
    for mname, pm in models.items():
        u = R73.raw_kelly(pm, paid) / scale
        m = R68.margin_bets(t, pm, 0.02) & (u > 0)
        rules[mname] = (m, u)
        for pname, lo, hi in periods:
            per = R63.R36.in_period(t, lo, hi)
            print(f"| {mname} | {pname} | " + R73.kelly_row(t, tq, m & per, paid, u) + " |")
    print("\n## 5. By three months, a quarter of Kelly: corrected BSP units / realised units\n")
    print("| three months | " + " | ".join(models) + " |\n|" + "---|" * (len(models) + 1))
    for bname, lo, hi in R68.blocks(R63.SINCE, None):
        per = R63.R36.in_period(t, lo, hi)
        cells = []
        for mname in models:
            m, u = rules[mname]
            s = R68.staked(tq, m & per, paid, u)
            cells.append(f"{s['units']:+,.1f} / {s['real']:+,.1f}" if s["n"] else "no BSP yet")
        print(f"| {bname} | " + " | ".join(cells) + " |")
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 79")
