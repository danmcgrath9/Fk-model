"""Round 46: what each stake would have cost at its worst (16 Nov 2026, founder: "Well keep testing and lets get a
fucking good model")

Test 63: at the card's 1.3x, Kelly on the held blend's own chance stakes three times the card's units on the same 98
bets since February 2025, and makes about two and a half times the units, realised and judged by BSP. Every extra
unit is worth about +40% by BSP. How much to stake is the founder's call on risk, and that needs the risk. Stated
before the run, on the held blend at 1.3x, every race from February 2025 at TAB's first price after TAB's deduction:

  1. as it happened, for three stakes: the card's (Kelly on half the model, half TAB's book, x75, cap 4 units), Kelly
     on the model's own chance (x75, cap 4), and one unit flat. For each: units staked and won, realised and by BSP,
     the worst drawdown in units and as a share of a 75-unit bank (a unit is 1/75 of the bank, so the cap is 5.3%),
     the longest losing run, months in profit and the worst month
  2. what BSP says could have happened: 10,000 replays of the same bets, at the same prices and stakes, each dog
     winning with BSP's chance (Test 62: BSP is fair to the held blend's bets, 293 winners against 292.5 from 1.1 to
     1.5). For each stake: the median, the 5th and the 95th percentile of units won, the chance of being behind after
     the 22 months, and the median and the 95th percentile of the worst drawdown

Half of any stake halves every unit figure, so it needs no rows of its own.

    python research/greyhound/topaz_round46.py DIR LABEL    (as round 45; the corrections are not needed)

Counts, sums and rates only: no race, dog or price is printed.
"""
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round33 as R33       # noqa: E402
import topaz_round36 as R36       # noqa: E402
import topaz_round41 as R41       # noqa: E402
import topaz_round42 as R42       # noqa: E402
import topaz_round43 as R43       # noqa: E402
import topaz_round45 as R45       # noqa: E402
import topaz_v1 as V1             # noqa: E402

BANK = 75.0                       # Kelly x75: a unit is 1/75 of the bank
REPLAYS = 10_000
STAKES = ("the card's stake", "Kelly on the model", "one unit flat")


def stake_bets(t: pd.DataFrame, stake: str):
    """The card's rule at 1.3x on the held blend under a stake: mask, price paid, units."""
    if stake == STAKES[2]:
        m, paid, _ = R45.bets(t, "pb6", 1.3, STAKES[0])
        return m, paid, np.ones(len(t))
    return R45.bets(t, "pb6", 1.3, stake)


def path(won: np.ndarray, paid: np.ndarray, u: np.ndarray):
    """Units won bet by bet (in date order), and the worst drawdown from a running peak (from 0)."""
    r = u * np.where(won == 1, paid - 1, -1.0)
    cum = np.cumsum(r, axis=-1)
    peak = np.maximum.accumulate(np.concatenate([np.zeros(cum.shape[:-1] + (1,)), cum], axis=-1), axis=-1)[..., 1:]
    return cum, (peak - cum).max(axis=-1).clip(min=0)


def longest_losing_run(won: np.ndarray) -> int:
    run = worst = 0
    for w in won:
        run = 0 if w else run + 1
        worst = max(worst, run)
    return worst


def as_it_happened(t: pd.DataFrame, x: np.ndarray, paid: np.ndarray, u: np.ndarray) -> dict:
    idx = np.flatnonzero(x)
    idx = idx[np.argsort(t.date.values[idx], kind="stable")]
    won, pd_, uu = t.won.values[idx].astype(float), paid[idx], u[idx]
    cum, dd = path(won, pd_, uu)
    r = uu * np.where(won == 1, pd_ - 1, -1.0)
    bym = pd.Series(r).groupby(pd.to_datetime(t.date.values[idx]).to_period("M")).sum()
    q = t.p_bsp.values[idx]
    has = ~np.isnan(q)
    return dict(n=len(idx), staked=float(uu.sum()), won=float(r.sum()),
                bsp=float((uu[has] * (pd_[has] * q[has] - 1)).sum()), nb=int(has.sum()), dd=float(dd),
                run=longest_losing_run(won), months=f"{(bym > 0).sum()} of {len(bym)}", worst=float(bym.min()),
                top=float(uu.max()))


def replays(t: pd.DataFrame, x: np.ndarray, paid: np.ndarray, u: np.ndarray, seed: int = 1) -> dict:
    """The same bets replayed REPLAYS times, each dog winning with BSP's chance (bets with no BSP left out)."""
    idx = np.flatnonzero(x & t.p_bsp.notna().values)
    idx = idx[np.argsort(t.date.values[idx], kind="stable")]
    q = t.p_bsp.values[idx].astype(float)
    rng = np.random.default_rng(seed)
    won = (rng.random((REPLAYS, len(idx))) < q).astype(float)
    cum, dd = path(won, paid[idx], u[idx])
    end = cum[:, -1]
    return dict(n=len(idx), med=float(np.median(end)), p5=float(np.percentile(end, 5)),
                p95=float(np.percentile(end, 95)), behind=float((end < 0).mean()), dd50=float(np.median(dd)),
                dd95=float(np.percentile(dd, 95)))


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 46, what each stake would have cost at its worst\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    a, _ = R41.ours(d, t0)
    fr = R33.load(bdir, times=(0,))
    x = R33.at_time(a, fr, 0)
    x["pb6"] = V1.blend(["p_x_bet", "p_book"], x, np.asarray(R41.FIXED))[1]
    ok = pd.Series((x.price > 1).values).groupby(x.race_id.values).transform("all").values
    x = x[ok].reset_index(drop=True)
    t = x[x.is_ran.astype(bool).values & (x.date >= R42.SINCE).values].reset_index(drop=True)
    print(f"Every race from February 2025 at TAB's first price: {t.race_id.nunique():,} races, {len(t):,} runners "
          f"that ran. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    print("## 1. As it happened, the held blend at 1.3x\n")
    print("| period | stake | bets | units staked | biggest stake | units won | per unit staked | BSP's units "
          "| worst drawdown, units | as a share of a 75-unit bank | longest losing run | months in profit "
          "| worst month, units |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for pname, lo, hi in R43.PERIODS:
        p = R36.in_period(t, lo, hi)
        for stake in STAKES:
            m, paid, u = stake_bets(t, stake)
            s = as_it_happened(t, m & p, paid, u)
            print(f"| {pname} | {stake} | {s['n']:,} | {s['staked']:,.0f} | {s['top']:.1f} | {s['won']:+,.1f} | "
                  f"{s['won'] / s['staked']:+.1%} | {s['bsp']:+,.1f} | {s['dd']:,.1f} | {s['dd'] / BANK:.0%} | "
                  f"{s['run']} | {s['months']} | {s['worst']:+,.1f} |")
    print(f"\n## 2. {REPLAYS:,} replays of the same bets, each dog winning with BSP's chance, February 2025 on\n")
    print("| stake | bets with a BSP | median units won | 5th percentile | 95th percentile | chance of being behind "
          "| median worst drawdown | 95th percentile worst drawdown | as a share of a 75-unit bank |\n"
          "|---|---|---|---|---|---|---|---|---|")
    for stake in STAKES:
        m, paid, u = stake_bets(t, stake)
        s = replays(t, m, paid, u)
        print(f"| {stake} | {s['n']:,} | {s['med']:+,.1f} | {s['p5']:+,.1f} | {s['p95']:+,.1f} | {s['behind']:.1%} | "
              f"{s['dd50']:,.1f} | {s['dd95']:,.1f} | {s['dd95'] / BANK:.0%} |")
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 46")
