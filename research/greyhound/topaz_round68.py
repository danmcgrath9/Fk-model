"""Round 68: the card with its favourites (17 Nov 2026, founder: "Keep going, find more winning bets")

Test 85 found that the favourites the card has always skipped (the model's fair price under $2) make money at TAB's
first price: from 5% expected value, 494 bets in 22 months, +49 units by the corrected BSP, both halves positive. It
also found that from $2 to $15 the model gets about seven points less than it expects, because the same error in its
chance moves the expected value more on a longer price, and that a quarter of Kelly earns more for each unit staked.
Stated before the run, with both saved models (Test 83's, and its inputs walked at up to 4,000 rounds), no new walk:

  - the favourites in detail: by the model's expected value (0%, 3%, 5%, 10% and over), under $1.50 and $1.50 to $2,
    from February 2025 and by half
  - one rule for every price: bet when the model's chance is at least d points over the chance the price paid needs
    (1 / the price paid), d from 1 to 5 points, fair price under $15
  - the card with its favourites: the card's ratio rule ($2 to $15, 1.1x, 1.2x and 1.3x) plus the favourites at 0%
    or 5% expected value, flat, from February 2025, by half and by three months
  - staked by a quarter of Kelly, with what flat has had all along: a standard error, by half, the deepest fall from
    a high point (realised) and the losing months
  - the same in races with nothing scratched after TAB's open

    python research/greyhound/topaz_round68.py DIR LABEL    (as round 67)

Counts, sums and rates only: no race, dog or price is printed.
"""
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round44 as R44       # noqa: E402
import topaz_round58 as R58       # noqa: E402
import topaz_round62 as R62       # noqa: E402
import topaz_round63 as R63       # noqa: E402
import topaz_round65 as R65       # noqa: E402
import topaz_round67 as R67       # noqa: E402

FAV_EVS = (0.0, 0.03, 0.05, 0.10)
FAV_BANDS = [("under $1.50", 0.0, 1.5), ("$1.50 to $2", 1.5, 2.0), ("under $2", 0.0, 2.0)]
MARGINS = (0.01, 0.02, 0.03, 0.04, 0.05)
CARD = (2.0, 15.0)


def paid_price(t: pd.DataFrame) -> np.ndarray:
    """TAB's first price after its deduction, the same as the card's rule and round 67 pay."""
    pr = t.price.values.astype(float)
    return 1 + (pr - 1) * (1 - t.ded.fillna(0).values)


def margin_bets(t: pd.DataFrame, p: np.ndarray, d: float, band: tuple = (0.0, 15.0)) -> np.ndarray:
    """Bets where the model's chance is at least d over the chance the price paid needs (1 / price paid), with the
    model's fair price in the band."""
    pr = t.price.values.astype(float)
    paid = paid_price(t)
    with np.errstate(divide="ignore", invalid="ignore"):
        fair = 1 / p
        need = 1 / paid
    return (np.isfinite(pr) & (pr > 1) & np.isfinite(p) & (p - need >= d - 1e-12)
            & (fair >= band[0]) & (fair < band[1]))


def card_with_favourites(t: pd.DataFrame, col: str, p: np.ndarray, ratio: float, fav_ev) -> tuple:
    """The card's ratio rule in its band, plus the favourites (fair price under $2) at fav_ev expected value or more
    (None: none). A dog is one bet whichever rule takes it: (mask, of them favourites, price paid)."""
    m, paid = R63.bets(t, col, t.price.values, ratio)
    f = np.zeros(len(t), bool)
    if fav_ev is not None:
        f, _, _ = R67.value_bets(t, p, fav_ev, np.inf, (0.0, 2.0))
        f = f & ~m
    return m | f, f, paid


def staked(tq: pd.DataFrame, m: np.ndarray, paid: np.ndarray, u: np.ndarray) -> dict:
    """Stakes u on the bets in m that have a BSP: units staked, the corrected BSP's units and return per unit staked
    with its standard error (over the bets, as round 44's flat one), realised units and the luck in them (the
    standard deviation of the realised units if BSP's chances were the truth)."""
    y = m & tq.p_bsp.notna().values
    if not y.any():
        return dict(n=0)
    s = u[y]
    q = tq.p_bsp.values[y].astype(float)
    v = paid[y] * q - 1
    won = tq.won.values[y].astype(float)
    real = np.where(won == 1, paid[y] - 1, -1.0)
    tot = s.sum()
    kb = (s * v).sum() / tot
    return dict(n=int(y.sum()), staked=float(tot), units=float((s * v).sum()), per=float(kb),
                se=float(np.sqrt((s ** 2 * (v - kb) ** 2).sum()) / tot),
                real=float((s * real).sum()), luck=float(np.sqrt((s ** 2 * paid[y] ** 2 * q * (1 - q)).sum())))


def deepest_fall(t: pd.DataFrame, m: np.ndarray, paid: np.ndarray, u: np.ndarray) -> tuple:
    """Realised, in date order: the deepest fall from a high point (units) and the losing months of the months bet."""
    idx = np.where(m)[0]
    if not len(idx):
        return 0.0, 0, 0
    order = idx[np.lexsort((t.race_id.values[idx], t.date.values[idx]))]
    won = t.won.values[order].astype(float)
    r = u[order] * np.where(won == 1, paid[order] - 1, -1.0)
    cum = np.cumsum(r)
    fall = float(np.max(np.maximum.accumulate(np.concatenate([[0.0], cum]))[1:] - cum))
    mon = pd.Series(r).groupby(pd.to_datetime(t.date.values[order]).to_period("M")).sum()
    return max(fall, 0.0), int((mon < 0).sum()), int(len(mon))


def flat_row(t, tq, m, paid, months) -> str:
    return R67.cells(t, tq, m, paid, months)


def blocks(start: str, end) -> list:
    """Three-month periods from start: (label, lo, hi)."""
    out, lo = [], pd.Timestamp(start)
    last = pd.Timestamp(end) if end else pd.Timestamp.today().normalize() + pd.Timedelta(days=1)
    while lo < last:
        hi = lo + pd.DateOffset(months=3)
        lab = f"{lo:%b %Y} to {(hi - pd.Timedelta(days=1)):%b %Y}" if hi <= last else f"{lo:%b %Y} on"
        out.append((lab, f"{lo:%Y-%m-%d}", f"{hi:%Y-%m-%d}" if hi <= last else None))
        lo = hi
    return out


def main(d, label):
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 68, the card with its favourites\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    x, R, _, _ = R62.field(d, t0)
    if not R67.read_saved(x, R65.TAG, "c_m") or not R67.read_saved(x, R67.TAG, "c_l"):
        print("Test 83's model (corr_r65) and the longer fit (corr_r67) must both be in the walk cache: nothing to test")
        return 1
    ran = x.is_ran.astype(bool).values
    t = x[ran].reset_index(drop=True)
    t["q_bsp"], _ = R58.corrected_bsp(t)
    tq = t.assign(p_bsp=t.q_bsp)
    print(f"Runners that ran at TAB's first price: {len(t):,} in {t.race_id.nunique():,} races; both models read "
          f"from the walk cache. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")

    since = [("Feb 2025 on", R63.SINCE, None)]
    periods = since + R63.HALVES
    cols = {"Test 83's model": "c_m", "the longer fit": "c_l"}
    chance = {n: R67.model_chance(t, c) for n, c in cols.items()}
    paid = paid_price(t)
    head = ("bets | a month | A/E | realised flat ROI | realised units | corrected BSP per bet (SE) | "
            "corrected BSP units")

    print("## 1. The favourites (the model's fair price under $2), flat\n")
    print(f"| period | model | fair price | expected value | {head} |\n|" + "---|" * 11)
    for pname, lo, hi in periods:
        per = R63.R36.in_period(t, lo, hi)
        mo = R67.months_in(t, per)
        for mname, p in chance.items():
            for bname, b0, b1 in (FAV_BANDS if pname == since[0][0] else FAV_BANDS[-1:]):
                for e in FAV_EVS:
                    m, pd_, _ = R67.value_bets(t, p, e, np.inf, (b0, b1))
                    print(f"| {pname} | {mname} | {bname} | {e:.0%} or more | "
                          + flat_row(t, tq, m & per, pd_, mo) + " |")

    print("\n## 2. One rule for every price: the model's chance at least d points over the chance the price paid "
          "needs, fair price under $15, flat\n")
    print(f"| period | model | d | {head} |\n|" + "---|" * 10)
    for pname, lo, hi in periods:
        per = R63.R36.in_period(t, lo, hi)
        mo = R67.months_in(t, per)
        for mname, p in chance.items():
            for dd in MARGINS:
                print(f"| {pname} | {mname} | {dd * 100:.0f} point{'' if dd == 0.01 else 's'} | "
                      + flat_row(t, tq, margin_bets(t, p, dd) & per, paid, mo) + " |")

    rules = [("1.1x", 1.1, None), ("1.1x + favourites from 0%", 1.1, 0.0), ("1.1x + favourites from 5%", 1.1, 0.05),
             ("1.2x", 1.2, None), ("1.2x + favourites from 5%", 1.2, 0.05), ("1.3x + favourites from 5%", 1.3, 0.05)]
    print(f"\n## 3. The card with its favourites, flat ({(time.monotonic() - t0) / 60:.0f} minutes in)\n")
    print(f"| period | model | rule | of them favourites | {head} |\n|" + "---|" * 11)
    for pname, lo, hi in periods:
        per = R63.R36.in_period(t, lo, hi)
        mo = R67.months_in(t, per)
        for mname, col in cols.items():
            for rname, ratio, fe in rules:
                m, f, pd_ = card_with_favourites(t, col, chance[mname], ratio, fe)
                print(f"| {pname} | {mname} | {rname} | {int((f & per).sum()):,} | "
                      + flat_row(t, tq, m & per, pd_, mo) + " |")

    pl = chance["the longer fit"]
    m11, _, pd11 = card_with_favourites(t, "c_l", pl, 1.1, None)
    m11f, _, _ = card_with_favourites(t, "c_l", pl, 1.1, 0.05)
    k11 = R67.kelly_stakes(pl, pd11, m11 & R63.R36.in_period(t, R63.SINCE, None))
    k11f = R67.kelly_stakes(pl, pd11, m11f & R63.R36.in_period(t, R63.SINCE, None))
    one = np.ones(len(t))
    print("\n## 4. By three months, the longer fit: corrected BSP units / realised units\n")
    print("| three months | 1.1x, flat | 1.1x + favourites from 5%, flat | 1.1x + favourites from 5%, quarter Kelly |"
          "\n|---|---|---|---|")
    for bname, lo, hi in blocks(R63.SINCE, None):
        per = R63.R36.in_period(t, lo, hi)
        cells = []
        for m, u in ((m11, one), (m11f, one), (m11f, k11f)):
            s = staked(tq, m & per, pd11, u)
            cells.append(f"{s['units']:+,.1f} / {s['real']:+,.1f}" if s["n"] else "")
        print(f"| {bname} | " + " | ".join(cells) + " |")

    print("\n## 5. Flat against a quarter of Kelly, the longer fit (stakes scaled to a mean of one unit from Feb 2025)"
          "\n")
    print("| rule | period | staking | bets | units staked | corrected BSP per unit staked (SE) | corrected BSP units | "
          "realised units | luck in the realised units (SD) | largest stake | deepest fall, realised | losing months |"
          "\n|" + "---|" * 12)
    for rname, m, k in (("1.1x", m11, k11), ("1.1x + favourites from 5%", m11f, k11f)):
        for pname, lo, hi in periods:
            per = R63.R36.in_period(t, lo, hi)
            for sname, u in (("flat", one), ("quarter Kelly", k)):
                mm = m & per
                s = staked(tq, mm, pd11, u)
                if not s["n"]:
                    continue
                fall, lose, nmon = deepest_fall(t, mm, pd11, u)
                print(f"| {rname} | {pname} | {sname} | {s['n']:,} | {s['staked']:,.0f} | {s['per']:+.1%} "
                      f"({s['se']:.1%}) | {s['units']:+,.1f} | {s['real']:+,.1f} | {s['luck']:,.1f} | "
                      f"{u[mm].max():.1f} | {fall:,.1f} | {lose} of {nmon} |")

    c = t[(t.n_later.fillna(0) == 0).values].reset_index(drop=True)
    cq = c.assign(p_bsp=c.q_bsp)
    pc = R67.model_chance(c, "c_l")
    per = R63.R36.in_period(c, R63.SINCE, None)
    mo = R67.months_in(c, per)
    print("\n## 6. Races with nothing scratched after TAB's open, the longer fit, flat, Feb 2025 on\n")
    print(f"| rule | of them favourites | {head} |\n|" + "---|" * 9)
    for rname, ratio, fe in rules:
        m, f, pd_ = card_with_favourites(c, "c_l", pc, ratio, fe)
        print(f"| {rname} | {int((f & per).sum()):,} | " + flat_row(c, cq, m & per, pd_, mo) + " |")
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 68")
