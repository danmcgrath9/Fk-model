"""Round 83: the dog that comes across, read from where dogs get to at the first point (19 Nov 2026, founder, on
Warragul race 3: "the 6 crossed it", "add that input and test it", and "the market drifted the 5 because of this ...
$3.50 out to $5")

Test 96's map counted a dog drawn outside as a crosser only when its early-speed RATING was quicker. At Warragul box 6
was slower than box 5 on that rating but had led at the first point more often (4 in 10 against 3 in 10), and it came
across. topaz_cross reads the threat from position instead: dogs drawn outside that are usually ahead at the first
point and run no wider (cx_out_first, cx_out_led, cx_out_pressure, the nearest outside dog's lead over it), and dogs
drawn inside that are ahead and run wider (cx_in_first). Six inputs, every one from runs on earlier days and today's
draw.

Stated before the run. Test 98's fit (the best model with what is known on a live morning: Test 83's inputs without
the BSP-based history, learning rate 0.04, up to 4,000 rounds, the same refits) walked again with the six crossing
inputs added, beside Test 98's saved walk (corr_r79), February 2025 on:

  - how many runners have a crosser, and the crossing inputs' share of the gain
  - the distance to BSP and the winners' log loss on clean races
  - by crossing group: actual wins against Test 98's chance, the new fit's, TAB's first book and the corrected BSP, and
    how far the market moved from TAB's first price to BSP (the founder's drift)
  - Test 98's bets with and without a crosser outside, and Test 98 skipping the dogs with one
  - the 2-point margin flat and at a quarter of Kelly on one scale, by half and by three months

Saved as corr_r83 (column c_x) in the walk cache.

    python research/greyhound/topaz_round83.py DIR LABEL    (as round 79, with ISOLYNX_DIR for the running line)

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
import topaz_cross as C           # noqa: E402
import topaz_lines as L           # noqa: E402
import topaz_round50 as R50       # noqa: E402
import topaz_round58 as R58       # noqa: E402
import topaz_round63 as R63       # noqa: E402
import topaz_round64 as R64       # noqa: E402
import topaz_round67 as R67       # noqa: E402
import topaz_round68 as R68       # noqa: E402
import topaz_round70 as R70       # noqa: E402
import topaz_round73 as R73       # noqa: E402
import topaz_round79 as R79       # noqa: E402
import topaz_v1 as V1             # noqa: E402

TAG = "r83"
OLD, NEW, SKIP = "Test 98's fit", "with the crossing inputs", "Test 98, skipping a dog with a crosser outside"


def groups(cx: pd.DataFrame) -> list:
    """(name, mask) for each crossing group, on rows of cx."""
    f = cx.cx_out_first.values
    has = np.isfinite(f)
    pr = cx.cx_out_pressure.values
    top = np.nanquantile(pr[has & (pr > 0)], 0.9) if np.any(has & (pr > 0)) else np.inf
    return [
        ("nothing drawn outside it is usually ahead of it and runs its line", has & (f == 0)),
        ("one dog drawn outside is usually ahead of it at the first point and runs no wider", has & (f == 1)),
        ("two or more such dogs", has & (f >= 2)),
        ("the dog drawn next outside has led more often", np.nan_to_num(cx.cx_nb_out_led.values, nan=-1) > 0),
        ("the dog drawn next outside is a tenth of the field or more ahead at the first point",
         np.nan_to_num(cx.cx_nb_out_first.values, nan=-1) >= 0.10),
        ("the crossers' pressure, the top tenth", has & (pr >= top)),
        ("a dog drawn inside is usually ahead of it and runs wider", np.nan_to_num(cx.cx_in_first.values) >= 1),
        ("no first-point history", ~has),
    ]


def ae_cells(won: np.ndarray, m: np.ndarray, chances: list) -> str:
    """runners | wins | A/E against each chance | SE of the last"""
    n = int(m.sum())
    if not n:
        return "0 | 0 |" + " |" * (len(chances) + 1)
    w = won[m].sum()
    cells = [f"{w / np.nansum(p[m]):.3f}" for p in chances]
    pl = chances[-1][m]
    se = np.sqrt(np.nansum(pl * (1 - pl))) / np.nansum(pl)
    return f"{n:,} | {int(w):,} | " + " | ".join(cells) + f" | {se:.3f}"


def drift(tab: np.ndarray, bsp: np.ndarray, m: np.ndarray) -> str:
    """How far the market moved from TAB's first book to the corrected BSP, as the price: the mean of
    log(TAB's chance / BSP's chance), shown as a price change (+ = drifted out), and the share that drifted."""
    ok = m & np.isfinite(tab) & np.isfinite(bsp) & (tab > 0) & (bsp > 0)
    if not ok.any():
        return " | "
    lr = np.log(tab[ok] / bsp[ok])
    return f"{np.exp(lr.mean()) - 1:+.1%} | {np.mean(lr > 0):.0%}"


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir, iso_dir = os.environ.get("BETWATCH_DIR", ""), os.environ.get("ISOLYNX_DIR", "")
    print(f"# {label}: round 83, the dog that comes across, read from the first point\n")
    if not bdir or not os.path.isdir(bdir) or not iso_dir or not os.path.isdir(iso_dir):
        print("Betwatch (BETWATCH_DIR) and Isolynx (ISOLYNX_DIR) are both needed: nothing to test")
        return 1
    from greyhound.isolynx import table
    orig, memo = R50.base, {}

    def base_cross(dd):
        """Round 50's base with the crossing inputs added and named as inputs (the running line only builds them)."""
        if "v" not in memo:
            df, num, rel, note = orig(dd)
            df, _, lnote = L.add_lines(df, table(iso_dir))
            cm = C.cross_map(df)
            for c in C.COLS:
                df[c] = cm[c].values
            memo["v"] = (df, list(dict.fromkeys(list(num) + C.COLS)), rel, note, lnote)
        df, num, rel, note, _ = memo["v"]
        return df.copy(), list(num), list(rel), note

    R50.base = base_cross
    try:
        x, R, XR, q, use, off_tab, tab, inputs = R67.build(d, t0)
    finally:
        R50.base = orig
    keep, drop = R79.live_inputs(inputs)
    cx_in = [c for c in keep if c in C.COLS]
    print(f"{memo['v'][4]}\n\nThe fit's inputs: {len(keep)} (dropped as BSP-based: {len(drop)}), of them the crossing "
          f"inputs: {len(cx_in)} ({', '.join(cx_in)}). {(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    if len(cx_in) != len(C.COLS):
        print("Not every crossing input reached the fit: nothing to test")
        return 1
    if not R67.read_saved(x, "r79", "c_v"):
        print("Test 98's fit (corr_r79) is not in the walk cache: nothing to compare")
        return 1
    has70 = R67.read_saved(x, "r70", "c_f")
    race, dates = R.race_id.values, R.date.values.astype("datetime64[ns]")
    ran = x.is_ran.astype(bool).values
    since_r = dates >= np.datetime64(R63.SINCE)
    cxr = XR[C.COLS].reset_index(drop=True)
    print("## 1. Runners with a crosser, February 2025 on\n\n| group | share of runners |\n|---|---|")
    for nm, m in groups(cxr):
        print(f"| {nm} | {np.mean(m[since_r]):.1%} |")

    print(f"\n## 2. Test 98's inputs and the crossing inputs, walked at a learning rate of {R70.LEARNING_RATE}, up to "
          f"{R70.WALK_ROUNDS:,} rounds a refit ({(time.monotonic() - t0) / 60:.0f} minutes in)\n")
    p, log, share = R70.walk_faster(R.assign(off=off_tab), XR[keep], q, use)
    print("; ".join(log) + "\n")
    print("Its inputs by share of gain: " + ", ".join(f"{k} {v:.1%}" for k, v in share.head(20).items()) + "\n")
    cs = share.reindex(C.COLS).fillna(0).sort_values(ascending=False)
    print(f"The crossing inputs: {cs.sum():.1%} of the gain (" + ", ".join(f"{k} {v:.2%}" for k, v in cs.items())
          + ")\n")

    t = x[ran].reset_index(drop=True)
    clean = (R.n_later.fillna(0).values == 0)
    pv_r = R70.on_runners(R, t, "c_v")
    ok = use & clean & (dates >= np.datetime64(R64.SPLIT)) & np.isfinite(p) & np.isfinite(pv_r)
    tab_d = R64.distance(tab[ok], q[ok], race[ok])
    print(f"## 3. Distance to BSP, Feb 2025 on, clean races ({int(ok.sum()):,} runners)\n\n| model | distance to BSP "
          "(thousandths) | of TAB's distance closed | winners' log loss |\n|---|---|---|---|")
    for nm, v in ((OLD, pv_r), (NEW, p)):
        dd = R64.distance(v[ok], q[ok], race[ok])
        print(f"| {nm} | {dd:.2f} | {1 - dd / tab_d:+.1%} | {V1.ll(v[ok], R.won.values[ok]):.4f} |")

    s_tab = pd.Series(R.p_book.values).groupby(race).transform("sum").values
    x["c_x"] = x.p_book
    x.loc[R["index"].values, "c_x"] = p * s_tab
    cdir = os.environ.get("WALK_CACHE_DIR", "")
    if cdir:
        Path(cdir).mkdir(parents=True, exist_ok=True)
        x.loc[ran, ["race_id", "dog", "c_x"]].to_csv(Path(cdir) / f"corr_{TAG}.csv.gz", index=False,
                                                     float_format="%.9g")
    to_t = np.full(len(x), -1)
    to_t[np.flatnonzero(ran)] = np.arange(int(ran.sum()))
    tpos = to_t[R["index"].values]
    cxt = pd.DataFrame(np.nan, index=np.arange(len(t)), columns=C.COLS)
    cxt.iloc[tpos] = cxr.values
    t["c_v"], t["c_x"] = x.c_v.values[ran], x.c_x.values[ran]
    t["q_bsp"], _ = R58.corrected_bsp(t)
    tq = t.assign(p_bsp=t.q_bsp)
    paid = R68.paid_price(t)
    since = R63.R36.in_period(t, R63.SINCE, None)
    pv, px = R67.model_chance(t, "c_v"), R67.model_chance(t, "c_x")
    ptab = R64.ran_share(t.p_book.values.astype(float), t.race_id.values)
    pbsp = t.q_bsp.values.astype(float)
    won = t.won.values.astype(float)
    have = since & np.isfinite(pbsp)

    print("\n## 4. By crossing group, February 2025 on, runners with a corrected BSP\n")
    print("| group | runners | wins | A/E vs Test 98's fit | A/E vs the new fit | A/E vs TAB's first book | A/E vs the "
          "corrected BSP | SE | TAB's first price to BSP (mean) | share drifted |\n|" + "---|" * 10)
    for nm, m in groups(cxt):
        print(f"| {nm} | " + ae_cells(won, m & have, [pv, px, ptab, pbsp]) + " | " + drift(ptab, pbsp, m & have)
              + " |")

    base = R67.model_chance(t, "c_f") if has70 else pv
    scale = R73.raw_kelly(base, paid)[R68.margin_bets(t, base, 0.02) & since].mean()
    crossed = np.nan_to_num(cxt.cx_out_first.values) >= 1
    rules = {}
    for nm, pm in ((OLD, pv), (NEW, px)):
        u = R73.raw_kelly(pm, paid) / scale
        rules[nm] = (R68.margin_bets(t, pm, 0.02) & (u > 0), u, R68.margin_bets(t, pm, 0.02))
    m98, u98, f98 = rules[OLD]
    rules[SKIP] = (m98 & ~crossed, u98, f98 & ~crossed)

    print("\n## 5. Test 98's bets with and without a crosser outside, a quarter of Kelly, February 2025 on\n")
    print("| Test 98's bets | A/E vs its own chance | A/E vs the corrected BSP | bets with a BSP | units staked | "
          "corrected BSP per unit staked (SE) | corrected BSP units | realised units | luck (SD) | deepest fall | "
          "losing months |\n|" + "---|" * 11)
    for nm, mk in (("with a crosser outside", m98 & crossed), ("without", m98 & ~crossed)):
        m = mk & since
        y = m & np.isfinite(pbsp)
        ae_own = won[y].sum() / pv[y].sum() if y.any() else np.nan
        ae_bsp = won[y].sum() / pbsp[y].sum() if y.any() else np.nan
        print(f"| {nm}: {int(m.sum()):,} | {ae_own:.3f} | {ae_bsp:.3f} | " + R73.kelly_row(t, tq, m, paid, u98) + " |")

    periods = [("Feb 2025 on", R63.SINCE, None)] + R63.HALVES
    print("\n## 6. The 2-point margin, fair price under $15, flat\n")
    print("| period | model | bets | a month | A/E | realised flat ROI | realised units | corrected BSP per bet (SE) | "
          "corrected BSP units |\n|" + "---|" * 9)
    for pname, lo, hi in periods:
        per = R63.R36.in_period(t, lo, hi)
        for mname, (_, _, fm) in rules.items():
            print(f"| {pname} | {mname} | " + R67.cells(t, tq, fm & per, paid, R67.months_in(t, per)) + " |")
    print(f"\n## 7. The 2-point margin, a quarter of Kelly at one scale ({scale:.4f})\n")
    print("| model | period | bets | units staked | corrected BSP per unit staked (SE) | corrected BSP units | "
          "realised units | luck in the realised units (SD) | deepest fall, realised | losing months |\n|" + "---|" * 10)
    for mname, (m, u, _) in rules.items():
        for pname, lo, hi in periods:
            per = R63.R36.in_period(t, lo, hi)
            print(f"| {mname} | {pname} | " + R73.kelly_row(t, tq, m & per, paid, u) + " |")
    print("\n## 8. By three months, a quarter of Kelly: corrected BSP units / realised units\n")
    print("| three months | " + " | ".join(rules) + " |\n|" + "---|" * (len(rules) + 1))
    for bname, lo, hi in R68.blocks(R63.SINCE, None):
        per = R63.R36.in_period(t, lo, hi)
        cells = []
        for m, u, _ in rules.values():
            s = R68.staked(tq, m & per, paid, u)
            cells.append(f"{s['units']:+,.1f} / {s['real']:+,.1f}" if s["n"] else "no BSP yet")
        print(f"| {bname} | " + " | ".join(cells) + " |")
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 83")
