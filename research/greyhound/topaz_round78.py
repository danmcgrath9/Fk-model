"""Round 78: does the running line make the best model more money? (18 Nov 2026, founder: "once the running line job is
ran, want to know if it increase profitablity")

Round 77 walked our own price again with the running line and today's draw against it (topaz_lines). That answers
whether our own price gets sharper. The money is made by Test 88's fit, which reads ours against TAB's opening book and
the market's history. This round walks Test 88's fit again (Test 83's inputs, learning rate 0.04, up to 4,000 rounds,
the same refits) with two changes, stated before the run:

  - ours with Isolynx is round 77's walk, ours with the lines (WALK_LINES_USE names it), so lp_ours and the gap to
    TAB read the sharper price
  - the running-line inputs are inputs to the correction too, so it can learn where TAB's opening book misprices a
    wide runner drawn inside, a squeezed dog or a slow beginner with a clash

Beside Test 88's fit (corr_r70), February 2025 on:
  - its inputs by share of gain, and the running-line inputs' total share
  - the distance to BSP and the winners' log loss on clean races
  - the margin rule at 1.5 and 2 points, fair price under $15, flat, by half
  - the 2-point margin at a quarter of Kelly on one scale (Test 88's 2-point bets' mean stake is one unit), by half and
    by three months, with the luck, the deepest fall and the losing months

Saved as corr_r78 (column c_h) in the walk cache.

    python research/greyhound/topaz_round78.py DIR LABEL    (as round 77, plus WALK_LINES_USE=<round 77's walk>)

Counts, sums and rates only: no race, dog or price is printed. The model's inputs are named.
"""
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_lines as L           # noqa: E402
import topaz_round50 as R50       # noqa: E402
import topaz_round58 as R58       # noqa: E402
import topaz_round63 as R63       # noqa: E402
import topaz_round64 as R64       # noqa: E402
import topaz_round67 as R67       # noqa: E402
import topaz_round68 as R68       # noqa: E402
import topaz_round70 as R70       # noqa: E402
import topaz_round73 as R73       # noqa: E402
import topaz_v1 as V1             # noqa: E402

TAG = "r78"
OLD, NEW = "Test 88's fit", "with the running line"


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir, iso_dir = os.environ.get("BETWATCH_DIR", ""), os.environ.get("ISOLYNX_DIR", "")
    lines_use = os.environ.get("WALK_LINES_USE", "").strip()
    print(f"# {label}: round 78, does the running line make the best model more money\n")
    if not bdir or not os.path.isdir(bdir) or not iso_dir or not os.path.isdir(iso_dir):
        print("Betwatch (BETWATCH_DIR) and Isolynx (ISOLYNX_DIR) are both needed: nothing to test")
        return 1
    if not lines_use:
        print("Round 77's walk must be named (WALK_LINES_USE): nothing to test")
        return 1
    from greyhound.isolynx import table
    orig, memo = R50.base, {}

    def base_lines(dd):
        """Round 50's base with the running-line inputs added, and named as inputs, so the correction reads them."""
        if "v" not in memo:
            df, num, rel, note = orig(dd)
            df, feats, lnote = L.add_lines(df, table(iso_dir))
            memo["v"] = (df, list(dict.fromkeys(list(num) + feats)), rel, note, feats, lnote)
        df, num, rel, note, _, _ = memo["v"]
        return df.copy(), list(num), list(rel), note

    R50.base = base_lines
    iso_use = os.environ.get("WALK_ISO_USE", "")
    os.environ["WALK_ISO_USE"] = lines_use              # ours with Isolynx is round 77's, ours with the lines
    try:
        x, R, XR, q, use, off_tab, tab, inputs = R67.build(d, t0)
    finally:
        R50.base = orig
        os.environ["WALK_ISO_USE"] = iso_use
    feats, lnote = memo["v"][4], memo["v"][5]
    line_in = [c for c in inputs if c in feats]
    print(f"{lnote}\n\nThe correction's inputs: {len(inputs)}, of them the running line's: {len(line_in)}. "
          f"{(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    if not R67.read_saved(x, "r70", "c_f"):
        print("Test 88's fit (corr_r70) is not in the walk cache: nothing to compare")
        return 1
    race, dates = R.race_id.values, R.date.values.astype("datetime64[ns]")
    ran = x.is_ran.astype(bool).values

    print(f"## 1. Test 83's inputs and the running line, walked at a learning rate of {R70.LEARNING_RATE}, up to "
          f"{R70.WALK_ROUNDS:,} rounds a refit\n")
    p, log, share = R70.walk_faster(R.assign(off=off_tab), XR[inputs], q, use)
    print("; ".join(log) + "\n")
    print("Its inputs by share of gain: " + ", ".join(f"{k} {v:.1%}" for k, v in share.head(25).items()) + "\n")
    ls = share.reindex(line_in).fillna(0).sort_values(ascending=False)
    print(f"The running line's inputs: {ls.sum():.1%} of the gain; the largest: "
          + ", ".join(f"{k} {v:.1%}" for k, v in ls.head(12).items()) + "\n")

    t = x[ran].reset_index(drop=True)
    clean = (R.n_later.fillna(0).values == 0)
    ok = use & clean & (dates >= np.datetime64(R64.SPLIT)) & np.isfinite(p)
    pf_r = R70.on_runners(R, t, "c_f")
    ok2 = ok & np.isfinite(pf_r)
    tab_d = R64.distance(tab[ok2], q[ok2], race[ok2])
    print(f"## 2. Distance to BSP, Feb 2025 on, clean races ({int(ok2.sum()):,} runners)\n\n| model | distance to BSP "
          "(thousandths) | of TAB's distance closed | winners' log loss |\n|---|---|---|---|")
    for nm, v in ((OLD, pf_r), (NEW, p)):
        dd = R64.distance(v[ok2], q[ok2], race[ok2])
        print(f"| {nm} | {dd:.2f} | {1 - dd / tab_d:+.1%} | {V1.ll(v[ok2], R.won.values[ok2]):.4f} |")

    s_tab = pd.Series(R.p_book.values).groupby(race).transform("sum").values
    x["c_h"] = x.p_book
    x.loc[R["index"].values, "c_h"] = p * s_tab
    cdir = os.environ.get("WALK_CACHE_DIR", "")
    if cdir:
        Path(cdir).mkdir(parents=True, exist_ok=True)
        x.loc[ran, ["race_id", "dog", "c_h"]].to_csv(Path(cdir) / f"corr_{TAG}.csv.gz", index=False,
                                                     float_format="%.9g")
    t["c_h"] = x.c_h.values[ran]
    t["c_f"] = x.c_f.values[ran]
    t["q_bsp"], _ = R58.corrected_bsp(t)
    tq = t.assign(p_bsp=t.q_bsp)
    paid = R68.paid_price(t)
    models = {OLD: R67.model_chance(t, "c_f"), NEW: R67.model_chance(t, "c_h")}
    periods = [("Feb 2025 on", R63.SINCE, None)] + R63.HALVES
    print("\n## 3. The margin rule, fair price under $15, flat\n")
    print("| period | model | margin | bets | a month | A/E | realised flat ROI | realised units | corrected BSP per bet "
          "(SE) | corrected BSP units |\n|" + "---|" * 10)
    for pname, lo, hi in periods:
        per = R63.R36.in_period(t, lo, hi)
        mo = R67.months_in(t, per)
        for mname, pm in models.items():
            for dm in (0.02, 0.015):
                print(f"| {pname} | {mname} | {dm * 100:g} points | "
                      + R67.cells(t, tq, R68.margin_bets(t, pm, dm) & per, paid, mo) + " |")

    since = R63.R36.in_period(t, R63.SINCE, None)
    m88 = R68.margin_bets(t, models[OLD], 0.02)
    scale = R73.raw_kelly(models[OLD], paid)[m88 & since].mean()
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
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 78")
