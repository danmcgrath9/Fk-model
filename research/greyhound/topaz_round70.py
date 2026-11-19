"""Round 70: the longer fit, let run further (17 Nov 2026, founder: "Keep going, find more winning bets")

Test 87 found the best card so far: the longer fit (Test 83's inputs walked at up to 4,000 rounds a refit) at a 2-point
margin, staked by a quarter of Kelly, +365 units by the corrected BSP over 21 months. Walked at up to 4,000 rounds its
refits still stopped at or near the cap (three at 4,000, ten within 100 of it), so the fit wanted more. Twice the
rounds would cost about four times the time to choose them, so this round doubles the learning rate instead, which
reaches as far in the same number of rounds. Stated before the run:

  - Test 83's inputs walked forward again at a learning rate of 0.04 (was 0.02), up to 4,000 rounds a refit, saved
    as corr_r70; its distance to BSP beside the longer fit's on the same clean races
  - the margin rule (1.5, 2 and 2.5 points, fair price under $15) for both, flat, from February 2025 and by half
  - the 2-point margin staked by a quarter of Kelly for both, by half and by three months, with the standard error,
    the luck, the deepest fall and the losing months

    python research/greyhound/topaz_round70.py DIR LABEL    (as round 67)

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
import topaz_round41 as R41       # noqa: E402
import topaz_round58 as R58       # noqa: E402
import topaz_round63 as R63       # noqa: E402
import topaz_round64 as R64       # noqa: E402
import topaz_round65 as R65       # noqa: E402
import topaz_round67 as R67       # noqa: E402
import topaz_round68 as R68       # noqa: E402
import topaz_v1 as V1             # noqa: E402

TAG = "r70"
LEARNING_RATE = 0.04
WALK_ROUNDS = 4000
MARGINS = (0.015, 0.02, 0.025)


def walk_faster(R: pd.DataFrame, X: pd.DataFrame, q: np.ndarray, use: np.ndarray, models: list | None = None):
    """Round 41's walk at LEARNING_RATE and up to WALK_ROUNDS a refit; the module's settings are put back after.
    `models`, when a list, collects each refit's (month, booster) (round 80)."""
    old_rounds, old_params = R41.MAX_ROUNDS, R41.PARAMS
    R41.MAX_ROUNDS, R41.PARAMS = WALK_ROUNDS, dict(R41.PARAMS, learning_rate=LEARNING_RATE)
    try:
        if models is None:
            return R41.walk_correction(R, X, q, use)
        return R41.walk_correction(R, X, q, use, models=models)
    finally:
        R41.MAX_ROUNDS, R41.PARAMS = old_rounds, old_params


def on_runners(R: pd.DataFrame, t: pd.DataFrame, col: str) -> np.ndarray:
    """A saved model's chance over the runners that ran (t), lined up on R's rows by race and dog."""
    pm = R64.ran_share(t[col].values.astype(float), t.race_id.values)
    k = pd.DataFrame({"race_id": t.race_id.values.astype("int64"), "dog": t.dog.values.astype(str), "pm": pm})
    rk = pd.DataFrame({"race_id": R.race_id.values.astype("int64"), "dog": R.dog.values.astype(str)})
    return rk.merge(k.drop_duplicates(["race_id", "dog"]), on=["race_id", "dog"], how="left").pm.values


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 70, the longer fit, let run further\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    if not os.environ.get("WALK_CACHE_USE", "").strip() or not os.environ.get("WALK_ISO_USE", "").strip():
        print("Both saved walks must be named (WALK_CACHE_USE and WALK_ISO_USE): nothing to test")
        return 1
    x, R, XR, q, use, off_tab, tab, inputs = R67.build(d, t0)
    if not R67.read_saved(x, R67.TAG, "c_l"):
        print("The longer fit (corr_r67) is not in the walk cache: nothing to test")
        return 1
    race, dates = R.race_id.values, R.date.values.astype("datetime64[ns]")
    ran = x.is_ran.astype(bool).values
    print(f"Runners that ran at TAB's first price: {len(R):,} in {R.race_id.nunique():,} races; the longer fit read "
          f"from the walk cache. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")

    print(f"## 1. Test 83's inputs walked at a learning rate of {LEARNING_RATE}, up to {WALK_ROUNDS:,} rounds a "
          "refit\n")
    p, log, share = walk_faster(R.assign(off=off_tab), XR[inputs], q, use)
    print("; ".join(log) + "\n")
    print("Its inputs by share of gain: " + ", ".join(f"{k} {v:.1%}" for k, v in share.head(20).items()) + "\n")
    t = x[ran].reset_index(drop=True)
    clean = (R.n_later.fillna(0).values == 0)
    ok = use & clean & (dates >= np.datetime64(R64.SPLIT)) & np.isfinite(p)
    pl_r = on_runners(R, t, "c_l")
    ok2 = ok & np.isfinite(pl_r)
    tab_d = R64.distance(tab[ok2], q[ok2], race[ok2])
    dd = R64.distance(p[ok2], q[ok2], race[ok2])
    dl = R64.distance(pl_r[ok2], q[ok2], race[ok2])
    print(f"Distance to BSP, Feb 2025 on, clean races: {dd:.2f} thousandths ({1 - dd / tab_d:+.1%} of TAB's closed), "
          f"winners' log loss {V1.ll(p[ok2], R.won.values[ok2]):.4f}; the longer fit on the same races {dl:.2f} "
          f"({1 - dl / tab_d:+.1%}), {V1.ll(pl_r[ok2], R.won.values[ok2]):.4f}\n")
    s_tab = pd.Series(R.p_book.values).groupby(race).transform("sum").values
    x["c_f"] = x.p_book
    x.loc[R["index"].values, "c_f"] = p * s_tab
    cdir = os.environ.get("WALK_CACHE_DIR", "")
    if cdir:
        Path(cdir).mkdir(parents=True, exist_ok=True)
        x.loc[ran, ["race_id", "dog", "c_f"]].to_csv(Path(cdir) / f"corr_{TAG}.csv.gz", index=False,
                                                     float_format="%.9g")
    t["c_f"] = x.c_f.values[ran]
    t["q_bsp"], _ = R58.corrected_bsp(t)
    tq = t.assign(p_bsp=t.q_bsp)
    paid = R68.paid_price(t)
    models = {"the longer fit": R67.model_chance(t, "c_l"), f"learning rate {LEARNING_RATE}": R67.model_chance(t, "c_f")}
    periods = [("Feb 2025 on", R63.SINCE, None)] + R63.HALVES

    print("## 2. The margin rule, fair price under $15, flat\n")
    print("| period | model | margin | bets | a month | A/E | realised flat ROI | realised units | corrected BSP per bet "
          "(SE) | corrected BSP units |\n|" + "---|" * 10)
    for pname, lo, hi in periods:
        per = R63.R36.in_period(t, lo, hi)
        mo = R67.months_in(t, per)
        for mname, pm in models.items():
            for dm in MARGINS:
                print(f"| {pname} | {mname} | {dm * 100:g} points | "
                      + R67.cells(t, tq, R68.margin_bets(t, pm, dm) & per, paid, mo) + " |")

    since = R63.R36.in_period(t, R63.SINCE, None)
    one = np.ones(len(t))
    m2 = {n: R68.margin_bets(t, pm, 0.02) for n, pm in models.items()}
    kel = {n: R67.kelly_stakes(pm, paid, m2[n] & since) for n, pm in models.items()}
    print(f"\n## 3. The 2-point margin, flat against a quarter of Kelly (stakes scaled to a mean of one unit from Feb "
          f"2025; bets with a corrected BSP) ({(time.monotonic() - t0) / 60:.0f} minutes in)\n")
    print("| model | period | staking | bets | units staked | corrected BSP per unit staked (SE) | corrected BSP units | "
          "realised units | luck in the realised units (SD) | largest stake | deepest fall, realised | losing months |"
          "\n|" + "---|" * 12)
    has = tq.p_bsp.notna().values
    for mname in models:
        for pname, lo, hi in periods:
            per = R63.R36.in_period(t, lo, hi)
            for sname, u in (("flat", one), ("quarter Kelly", kel[mname])):
                mm = m2[mname] & per
                s = R68.staked(tq, mm, paid, u)
                if not s["n"]:
                    continue
                fall, lose, nmon = R68.deepest_fall(t, mm & has, paid, u)
                print(f"| {mname} | {pname} | {sname} | {s['n']:,} | {s['staked']:,.0f} | {s['per']:+.1%} "
                      f"({s['se']:.1%}) | {s['units']:+,.1f} | {s['real']:+,.1f} | {s['luck']:,.1f} | "
                      f"{u[mm].max():.1f} | {fall:,.1f} | {lose} of {nmon} |")

    print("\n## 4. By three months, the 2-point margin, quarter Kelly: corrected BSP units / realised units\n")
    print("| three months | " + " | ".join(models) + " |\n|" + "---|" * (len(models) + 1))
    for bname, lo, hi in R68.blocks(R63.SINCE, None):
        per = R63.R36.in_period(t, lo, hi)
        cells = []
        for mname in models:
            s = R68.staked(tq, m2[mname] & per, paid, kel[mname])
            cells.append(f"{s['units']:+,.1f} / {s['real']:+,.1f}" if s["n"] else "no BSP yet")
        print(f"| {bname} | " + " | ".join(cells) + " |")
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 70")
