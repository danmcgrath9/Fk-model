"""Round 71: the fit pushed further, two ways, and averaged (17 Nov 2026, founder: "Keep going, find more winning bets")

Test 88: Test 83's inputs walked at a learning rate of 0.04 (up to 4,000 rounds a refit) made +388.8 units by the
corrected BSP at the 2-point margin and a quarter of Kelly, against the longer fit's +365.0, and six of its thirteen
refits still stopped at or near the cap. Each step further has added about 20 units flat, so this round goes further
again. One script, run twice in parallel with different settings (environment, below), each stated before the run:

  - Test 83's inputs walked at R71_LR, up to R71_ROUNDS rounds a refit, R71_LEAVES leaves a tree, saved as
    corr_<R71_TAG> (column c_g); its distance to BSP beside Test 88's fit (corr_r70) and the two averaged
  - the 2-point margin (and 1.5 points), fair price under $15, flat, for all three, from February 2025 and by half
  - the 2-point margin staked by a quarter of Kelly for all three, by half and by three months

    R71_LR=0.04 R71_ROUNDS=8000 R71_LEAVES=15 R71_TAG=r71a python research/greyhound/topaz_round71.py DIR LABEL
    R71_LR=0.04 R71_ROUNDS=4000 R71_LEAVES=31 R71_TAG=r71b python research/greyhound/topaz_round71.py DIR LABEL

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
import topaz_round67 as R67       # noqa: E402
import topaz_round68 as R68       # noqa: E402
import topaz_round70 as R70       # noqa: E402
import topaz_v1 as V1             # noqa: E402

MARGINS = (0.015, 0.02)


def settings() -> dict:
    """The walk's settings from the environment: learning rate, the round cap, leaves a tree and the saved file's tag."""
    return dict(lr=float(os.environ.get("R71_LR", "0.04")), rounds=int(os.environ.get("R71_ROUNDS", "8000")),
                leaves=int(os.environ.get("R71_LEAVES", "15")), tag=os.environ.get("R71_TAG", "r71").strip() or "r71")


def walk_with(R: pd.DataFrame, X: pd.DataFrame, q: np.ndarray, use: np.ndarray, lr: float, rounds: int, leaves: int):
    """Round 41's walk at the given learning rate, round cap and leaves; the module's settings are put back after."""
    old_rounds, old_params = R41.MAX_ROUNDS, R41.PARAMS
    R41.MAX_ROUNDS, R41.PARAMS = rounds, dict(R41.PARAMS, learning_rate=lr, num_leaves=leaves)
    try:
        return R41.walk_correction(R, X, q, use)
    finally:
        R41.MAX_ROUNDS, R41.PARAMS = old_rounds, old_params


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    st = settings()
    name = f"learning rate {st['lr']:g}, {st['rounds']:,} rounds, {st['leaves']} leaves"
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 71, the fit pushed further ({name}), and averaged\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    if not os.environ.get("WALK_CACHE_USE", "").strip() or not os.environ.get("WALK_ISO_USE", "").strip():
        print("Both saved walks must be named (WALK_CACHE_USE and WALK_ISO_USE): nothing to test")
        return 1
    x, R, XR, q, use, off_tab, tab, inputs = R67.build(d, t0)
    if not R67.read_saved(x, R70.TAG, "c_f"):
        print("Test 88's fit (corr_r70) is not in the walk cache: nothing to test")
        return 1
    race, dates = R.race_id.values, R.date.values.astype("datetime64[ns]")
    ran = x.is_ran.astype(bool).values
    print(f"Runners that ran at TAB's first price: {len(R):,} in {R.race_id.nunique():,} races; Test 88's fit read "
          f"from the walk cache. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")

    print(f"## 1. Test 83's inputs walked at {name} a refit\n")
    p, log, share = walk_with(R.assign(off=off_tab), XR[inputs], q, use, st["lr"], st["rounds"], st["leaves"])
    print("; ".join(log) + "\n")
    print("Its inputs by share of gain: " + ", ".join(f"{k} {v:.1%}" for k, v in share.head(20).items()) + "\n")
    t = x[ran].reset_index(drop=True)
    clean = (R.n_later.fillna(0).values == 0)
    pf_r = R70.on_runners(R, t, "c_f")
    ok = use & clean & (dates >= np.datetime64(R64.SPLIT)) & np.isfinite(p) & np.isfinite(pf_r)
    tab_d = R64.distance(tab[ok], q[ok], race[ok])
    won = R.won.values[ok]
    for mname, pr in ((name, p), ("Test 88's fit", pf_r), ("the two averaged", (p + pf_r) / 2)):
        dd = R64.distance(pr[ok], q[ok], race[ok])
        print(f"Distance to BSP, Feb 2025 on, clean races, {mname}: {dd:.2f} thousandths ({1 - dd / tab_d:+.1%} of "
              f"TAB's closed), winners' log loss {V1.ll(pr[ok], won):.4f}")
    print()
    s_tab = pd.Series(R.p_book.values).groupby(race).transform("sum").values
    x["c_g"] = x.p_book
    x.loc[R["index"].values, "c_g"] = p * s_tab
    cdir = os.environ.get("WALK_CACHE_DIR", "")
    if cdir:
        Path(cdir).mkdir(parents=True, exist_ok=True)
        x.loc[ran, ["race_id", "dog", "c_g"]].to_csv(Path(cdir) / f"corr_{st['tag']}.csv.gz", index=False,
                                                     float_format="%.9g")
    t["c_g"] = x.c_g.values[ran]
    t["q_bsp"], _ = R58.corrected_bsp(t)
    tq = t.assign(p_bsp=t.q_bsp)
    paid = R68.paid_price(t)
    pf, pg = R67.model_chance(t, "c_f"), R67.model_chance(t, "c_g")
    models = {"Test 88's fit": pf, name: pg, "the two averaged": (pf + pg) / 2}
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
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 71")
