"""Round 75: how fast is fast enough at TAB's open (18 Nov 2026, founder: "Wait so how would we bet this at the open")

Every bet so far is judged at TAB's FIRST price. Betting it means seeing TAB's open, pricing the race and placing the
bet, and TAB's first price stood a median of 59 minutes, with 22% changed inside five minutes (Test 50). Stated before
the run, February 2025 on, bets with a corrected BSP, the bet decided at TAB's open and placed k = 0, 5, 15, 30 and 60
minutes after the race's market opened, at TAB's price then, with TAB's deduction for the dogs scratched after then:

  - Test 88's fit (corr_r70), the 2-point margin, fair price under $15, a quarter of Kelly at one scale (the open's
    2-point bets' mean stake from February 2025 is one unit): the bet placed only if the price then still clears the
    2-point margin, at the quarter Kelly stake for that price; and, beside it, the open's bets placed at whatever the
    price is then, at the open's stakes
  - the corrected blend (round 62's c_q), 1.1x, fair price $2 to $15, flat: the bet placed only if TAB's price then is
    still at least 1.1x the fair price
  - for each: the share of the open's bets still on, what became of the price (the same, shorter, longer, gone), and
    the bets, units staked, the corrected BSP's return per unit staked (SE) and units, and the realised units, by half

    python research/greyhound/topaz_round75.py DIR LABEL    (as round 73; the walk cache holds corr_r70 and corr_r62)

Counts, sums and rates only: no race, dog or price is printed.
"""
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import gbm_v0                     # noqa: E402
import topaz_round33 as R33       # noqa: E402
import topaz_round58 as R58       # noqa: E402
import topaz_round62 as R62       # noqa: E402
import topaz_round63 as R63       # noqa: E402
import topaz_round67 as R67       # noqa: E402
import topaz_round68 as R68       # noqa: E402
import topaz_round73 as R73       # noqa: E402

TIMES = (0, 5, 15, 30, 60)
MARGIN = 0.02
RATIO = 1.1


def prices_at(t: pd.DataFrame, fr: pd.DataFrame, k: int) -> tuple:
    """TAB's price and deduction for each runner of t that ran, k minutes after its race's market opened (NaN where
    the runner had no price then, or the race had started)."""
    f = fr[(fr.k == k) & fr.ran].drop_duplicates(["date", "_dn"], keep=False)[["date", "_dn", "price", "ded"]]
    m = t[["date"]].assign(_dn=gbm_v0.norm_name(t.dog_name.fillna(""))).merge(f, on=["date", "_dn"], how="left")
    return m.price.values.astype(float), m.ded.fillna(0).values.astype(float)


def what_became(open_price: np.ndarray, later: np.ndarray, m: np.ndarray) -> dict:
    """Of the bets in m: the price k minutes on the same, shorter, longer, or gone (no price then)."""
    o, p = open_price[m], later[m]
    gone = ~np.isfinite(p)
    with np.errstate(invalid="ignore"):
        return {"same": float(np.mean(~gone & np.isclose(p, o))), "shorter": float(np.mean(~gone & (p < o - 1e-9))),
                "longer": float(np.mean(~gone & (p > o + 1e-9))), "gone": float(np.mean(gone))}


def main(d, label):
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 75, how fast is fast enough at TAB's open\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    x, _, _, _ = R62.field(d, t0)
    if not R67.read_saved(x, "r70", "c_f"):
        print("Test 88's fit (corr_r70) is not in the walk cache: nothing to test")
        return 1
    has_cb = R63.read_corrections(x)
    t = x[x.is_ran.astype(bool).values].reset_index(drop=True)
    t["q_bsp"], _ = R58.corrected_bsp(t)
    tq = t.assign(p_bsp=t.q_bsp)
    since = R63.R36.in_period(t, R63.SINCE, None)
    fr = R33.load(bdir, times=TIMES)
    print(f"Runners that ran at TAB's first price: {len(t):,} in {t.race_id.nunique():,} races. The corrected blend "
          f"{'is' if has_cb else 'is NOT'} in the walk cache. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")

    pm = R67.model_chance(t, "c_f")
    paid0 = R68.paid_price(t)
    m88 = R68.margin_bets(t, pm, MARGIN)
    raw0 = R73.raw_kelly(pm, paid0)
    scale = raw0[m88 & since].mean()
    u0 = raw0 / scale
    m88 &= u0 > 0
    mcb = R63.bets(t, "c_q", t.price.values, RATIO)[0] if has_cb else np.zeros(len(t), bool)
    open_price = t.price.values.astype(float)
    periods = [("Feb 2025 on", R63.SINCE, None)] + R63.HALVES
    head = ("bets | of the open's bets | units staked | corrected BSP per unit staked (SE) | corrected BSP units | "
            "realised units")
    fates = []
    print(f"| model and rule | minutes after TAB's open | period | {head} |\n|" + "---|" * 9)
    for k in TIMES:
        pk, dk = prices_at(t, fr, k) if k else (open_price, t.ded.fillna(0).values.astype(float))
        tk = t.assign(price=pk, ded=dk)
        paidk = R68.paid_price(tk)
        uk = R73.raw_kelly(pm, paidk) / scale
        still88 = m88 & R68.margin_bets(tk, pm, MARGIN) & (uk > 0)
        blind = m88 & np.isfinite(pk) & (pk > 1)
        rows = [("Test 88's fit, 2 points, quarter Kelly, placed only if it still clears", still88, paidk, uk, m88),
                ("Test 88's fit, 2 points, the open's bets at whatever the price is", blind, paidk, u0, m88)]
        if has_cb:
            stillcb = mcb & R63.bets(tk, "c_q", pk, RATIO)[0]
            rows.append(("the corrected blend, 1.1x, flat, placed only if it still clears", stillcb, paidk,
                         np.ones(len(t)), mcb))
        for nm, m, paid, u, base in rows:
            for lab, lo, hi in periods:
                per = R63.R36.in_period(t, lo, hi)
                s = R68.staked(tq, m & per, paid, u)
                nb = R68.staked(tq, base & per, paid0, u0 if "88" in nm else np.ones(len(t)))
                if not s["n"]:
                    print(f"| {nm} | {k} | {lab} | 0 | | | | | |")
                    continue
                print(f"| {nm} | {k} | {lab} | {s['n']:,} | {s['n'] / max(nb['n'], 1):.0%} | {s['staked']:,.0f} | "
                      f"{s['per']:+.1%} ({s['se']:.1%}) | {s['units']:+,.1f} | {s['real']:+,.1f} |")
        if k:
            fates.append((k, what_became(open_price, pk, m88 & since),
                          what_became(open_price, pk, mcb & since) if has_cb else None))

    print("\n## What became of TAB's first price on the open's bets, February 2025 on\n")
    print("| minutes after TAB's open | bets | the same | shorter | longer | gone (no price, or the race started) |\n"
          "|---|---|---|---|---|---|")
    for k, a, b in fates:
        for nm, f in (("Test 88's fit, 2 points", a), ("the corrected blend, 1.1x", b)):
            if f is None:
                continue
            print(f"| {k} | {nm} | {f['same']:.0%} | {f['shorter']:.0%} | {f['longer']:.0%} | {f['gone']:.0%} |")
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 75")
