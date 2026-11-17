"""Round 72: the fits averaged, and more bets at the same Kelly (17 Nov 2026, founder: "Keep going, find more winning
bets")

Round 71 walked Test 83's inputs two more ways beside Test 88's fit (learning rate 0.04, up to 4,000 rounds, 15
leaves; corr_r70): twice the rounds (8,000, corr_r71a) and bigger trees (31 leaves, corr_r71b). Each landed level with
Test 88's fit on bets, but averaging two fits sat closer to BSP than either alone. This round reads the saved fits (no
new walk) and, stated before the run:

  - the distance to BSP, February 2025 on, clean races, of each fit, each pair averaged and all of them averaged
  - the 2-point margin, flat, for Test 88's fit and the fits averaged, by half
  - a quarter of Kelly at ONE scale (the 2-point margin's mean stake is one unit) with the margin lowered to 1.5, 1,
    0.5 and 0 points, so a lower margin adds its own small stakes rather than shrinking the others: bets, units
    staked, corrected BSP units and per unit staked (SE), realised units, the luck, the deepest fall and the losing
    months, for Test 88's fit and the fits averaged, by half; and the 1-point margin with the fair-price cap at $40
  - by three months for the margins that hold

    python research/greyhound/topaz_round72.py DIR LABEL    (as round 67; WALK_ALSO names the second saved walk)

Counts, sums and rates only: no race, dog or price is printed.
"""
import itertools
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round58 as R58       # noqa: E402
import topaz_round62 as R62       # noqa: E402
import topaz_round63 as R63       # noqa: E402
import topaz_round64 as R64       # noqa: E402
import topaz_round67 as R67       # noqa: E402
import topaz_round68 as R68       # noqa: E402
import topaz_v1 as V1             # noqa: E402

# (saved tag, its column, the name it is printed by, the column it is read into)
FITS = [("r70", "c_f", "Test 88's fit", "c_f"),
        ("r71a", "c_g", "twice the rounds", "c_a"),
        ("r71b", "c_g", "bigger trees", "c_b")]
BASE = "Test 88's fit"
AVERAGED = "the fits averaged"
KELLY_MARGINS = (0.02, 0.015, 0.01, 0.005, 0.0)


def read_fits(x: pd.DataFrame) -> dict:
    """Each saved fit in FITS that the walk cache holds, read into its own column: {name: column}."""
    got = {}
    for tag, col, name, into in FITS:
        if R67.read_saved(x, tag, col):
            x[into] = x[col].values
            if into != col:
                x.drop(columns=[col], inplace=True)
            got[name] = into
    return got


def fixed_kelly(p: np.ndarray, paid: np.ndarray, ref: np.ndarray, frac: float = R67.KELLY,
                cap: float = R67.CAP) -> np.ndarray:
    """A quarter of Kelly on every dog with an edge, capped, divided by ONE scale: the mean stake over the reference
    bets (ref) is one unit. A lower margin then adds its own stakes and leaves the others as they were."""
    with np.errstate(divide="ignore", invalid="ignore"):
        f = frac * (paid * p - 1) / (paid - 1)
    f = np.where(np.isfinite(f), np.clip(f, 0, cap), 0.0)
    s = f[ref].mean() if ref.any() else 0.0
    return f / s if s > 0 else f


def points(d: float) -> str:
    v = f"{d * 100:g}"
    return f"{v} point" + ("" if v == "1" else "s")


def main(d, label):
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 72, the fits averaged, and more bets at the same Kelly\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    x, R, _, _ = R62.field(d, t0)
    fits = read_fits(x)
    if BASE not in fits:
        print("Test 88's fit (corr_r70) is not in the walk cache: nothing to test")
        return 1
    missing = [n for _, _, n, _ in FITS if n not in fits]
    print("Fits read from the walk cache: " + ", ".join(fits)
          + (f"; not in it: {', '.join(missing)}" if missing else "") + "\n")
    ran = x.is_ran.astype(bool).values
    t = x[ran].reset_index(drop=True)
    t["q_bsp"], _ = R58.corrected_bsp(t)
    tq = t.assign(p_bsp=t.q_bsp)
    print(f"Runners that ran at TAB's first price: {len(t):,} in {t.race_id.nunique():,} races. "
          f"{(time.monotonic() - t0) / 60:.0f} minutes in.\n")

    # Distance to BSP over R (the runners that ran, races together), the label as round 65's walk was judged by
    race, dates = R.race_id.values, R.date.values.astype("datetime64[ns]")
    q, full, _ = R62.bsp_label(R, *R62.LABEL_FIT)
    rk = pd.DataFrame({"race_id": R.race_id.values.astype("int64"), "dog": R.dog.values.astype(str)})
    chance = {}
    for name, col in fits.items():
        pm = R64.ran_share(t[col].values.astype(float), t.race_id.values)
        k = pd.DataFrame({"race_id": t.race_id.values.astype("int64"), "dog": t.dog.values.astype(str), "pm": pm})
        chance[name] = rk.merge(k.drop_duplicates(["race_id", "dog"]), on=["race_id", "dog"], how="left").pm.values
    tab = R64.ran_share(R.p_book.values, race)
    clean = (R.n_later.fillna(0).values == 0)
    ok = full.astype(bool) & clean & (dates >= np.datetime64(R64.SPLIT))
    for v in chance.values():
        ok &= np.isfinite(v)
    tab_d = R64.distance(tab[ok], q[ok], race[ok])
    combos = [(n, chance[n]) for n in fits]
    for k in range(2, len(fits) + 1):
        for c in itertools.combinations(fits, k):
            nm = AVERAGED if k == len(fits) else " and ".join(c) + " averaged"
            combos.append((nm, np.mean([chance[n] for n in c], axis=0)))
    print(f"## 1. Distance to BSP, Feb 2025 on, clean races ({int(ok.sum()):,} runners in "
          f"{pd.unique(race[ok]).size:,} races; TAB's first price {tab_d:.2f} thousandths)\n")
    print("| model | distance to BSP (thousandths) | of TAB's distance closed | winners' log loss |\n|---|---|---|---|")
    won = R.won.values
    for nm, v in combos:
        dd = R64.distance(v[ok], q[ok], race[ok])
        print(f"| {nm} | {dd:.2f} | {1 - dd / tab_d:+.1%} | {V1.ll(v[ok], won[ok]):.4f} |")

    paid = R68.paid_price(t)
    pr = {n: R67.model_chance(t, c) for n, c in fits.items()}
    models = {BASE: pr[BASE]}
    if len(fits) > 1:
        models[AVERAGED] = np.mean([pr[n] for n in fits], axis=0)
    periods = [("Feb 2025 on", R63.SINCE, None)] + R63.HALVES
    head = ("bets | a month | A/E | realised flat ROI | realised units | corrected BSP per bet (SE) | "
            "corrected BSP units")
    print(f"\n## 2. The 2-point margin and 1.5 points, fair price under $15, flat\n\n| period | model | margin | {head} |\n|"
          + "---|" * 10)
    for pname, lo, hi in periods:
        per = R63.R36.in_period(t, lo, hi)
        mo = R67.months_in(t, per)
        for mname, pm in models.items():
            for dm in (0.02, 0.015):
                print(f"| {pname} | {mname} | {points(dm)} | "
                      + R67.cells(t, tq, R68.margin_bets(t, pm, dm) & per, paid, mo) + " |")

    since = R63.R36.in_period(t, R63.SINCE, None)
    has = tq.p_bsp.notna().values
    print(f"\n## 3. A quarter of Kelly at one scale (the 2-point margin's mean stake from Feb 2025 is one unit), the margin "
          f"lowered; bets with a corrected BSP ({(time.monotonic() - t0) / 60:.0f} minutes in)\n")
    print("| model | margin, fair price cap | period | bets | units staked | corrected BSP per unit staked (SE) | "
          "corrected BSP units | realised units | luck in the realised units (SD) | largest stake | "
          "deepest fall, realised | losing months |\n|" + "---|" * 12)
    rules = {}
    for mname, pm in models.items():
        u = fixed_kelly(pm, paid, R68.margin_bets(t, pm, 0.02) & since)
        rows = [(f"{points(dm)}, under $15", R68.margin_bets(t, pm, dm)) for dm in KELLY_MARGINS]
        rows.append(("1 point, under $40", R68.margin_bets(t, pm, 0.01, (0.0, 40.0))))
        for rname, m in rows:
            m = m & (u > 0)
            rules[(mname, rname)] = (m, u)
            for pname, lo, hi in periods:
                mm = m & R63.R36.in_period(t, lo, hi)
                s = R68.staked(tq, mm, paid, u)
                if not s["n"]:
                    continue
                fall, lose, nmon = R68.deepest_fall(t, mm & has, paid, u)
                print(f"| {mname} | {rname} | {pname} | {s['n']:,} | {s['staked']:,.0f} | {s['per']:+.1%} "
                      f"({s['se']:.1%}) | {s['units']:+,.1f} | {s['real']:+,.1f} | {s['luck']:,.1f} | "
                      f"{u[mm].max():.1f} | {fall:,.1f} | {lose} of {nmon} |")

    cols = [(m, r) for m in models for r in ("2 points, under $15", "1 point, under $15", "0 points, under $15")]
    print("\n## 4. By three months, a quarter of Kelly at one scale: corrected BSP units / realised units\n")
    print("| three months | " + " | ".join(f"{m}, {r.split(',')[0]}" for m, r in cols) + " |\n|"
          + "---|" * (len(cols) + 1))
    for bname, lo, hi in R68.blocks(R63.SINCE, None):
        per = R63.R36.in_period(t, lo, hi)
        cells = []
        for key in cols:
            m, u = rules[key]
            s = R68.staked(tq, m & per, paid, u)
            cells.append(f"{s['units']:+,.1f} / {s['real']:+,.1f}" if s["n"] else "no BSP yet")
        print(f"| {bname} | " + " | ".join(cells) + " |")
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 72")
