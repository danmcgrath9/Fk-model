"""Round 67: more bets from the best model (17 Nov 2026, founder: "Keep going, find more winning bets")

Test 83's model (everything + the market's history, walked from TAB's opening book) makes 67 bets a month at 1.1x,
+15.5% a bet by the corrected BSP, but only inside the card's fair-price band ($2 to $15) and by the card's ratio rule.
Test 84 found the open is where the edge is, so more bets have to come from the open. Stated before the run:

  - the model's own expected value at TAB's first price, after TAB's deduction: price paid x the model's chance - 1,
    with the model's chance over the runners that ran (Test 83's model, read from the walk cache as round 65 saved it)
  - bets by that expected value (0%, 5%, 10%, 15%, 20%, 30% and over) in four bands of the model's own fair price:
    under $2, $2 to $15 (the card's band), $15 to $30 and $30 and over; flat, realised and by the corrected BSP, from
    February 2025 and by half
  - staking: the same bets staked by a quarter of Kelly on the model's chance, scaled so the mean stake is one unit,
    beside flat; realised and by the corrected BSP
  - a longer fit: Test 83's inputs walked forward again with up to 4,000 rounds a refit (its walk kept the 2,000 cap at
    10 of 13 refits), its distance to BSP and the same bets beside Test 83's

    python research/greyhound/topaz_round67.py DIR LABEL    (as round 65)

Counts, sums and rates only: no race, dog or price is printed. The models' inputs are named.
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
import topaz_round41 as R41       # noqa: E402
import topaz_round44 as R44       # noqa: E402
import topaz_round58 as R58       # noqa: E402
import topaz_round62 as R62       # noqa: E402
import topaz_round63 as R63       # noqa: E402
import topaz_round64 as R64       # noqa: E402
import topaz_round65 as R65       # noqa: E402
import topaz_v1 as V1             # noqa: E402

TAG = "r67"
WALK_ROUNDS = 4000
EVS = (0.0, 0.05, 0.10, 0.15, 0.20, 0.30)
BANDS = [("under $2", 0.0, 2.0), ("$2 to $15", 2.0, 15.0), ("$15 to $30", 15.0, 30.0), ("$30 and over", 30.0, np.inf)]
KELLY = 0.25
CAP = 0.05                        # a quarter Kelly never more than 5% of the bank on one dog, before scaling


def model_chance(t: pd.DataFrame, col: str) -> np.ndarray:
    """The model's chance over the runners that ran: its column divided by the race's sum of TAB's book (the column
    was saved as the chance times that sum, so the card's ratio rule reads it like TAB's book)."""
    s = pd.Series(t.p_book.values.astype(float)).groupby(t.race_id.values).transform("sum").values
    with np.errstate(divide="ignore", invalid="ignore"):
        return t[col].values.astype(float) / s


def value_bets(t: pd.DataFrame, p: np.ndarray, lo_ev: float, hi_ev: float, band: tuple) -> tuple:
    """Bets whose expected value at TAB's first price after the deduction is in [lo_ev, hi_ev) and whose fair price
    (1 / the model's chance) is in the band: (mask, price paid, expected value)."""
    pr = t.price.values.astype(float)
    paid = 1 + (pr - 1) * (1 - t.ded.fillna(0).values)
    with np.errstate(divide="ignore", invalid="ignore"):
        fair = 1 / p
        ev = paid * p - 1
    m = (np.isfinite(pr) & (pr > 1) & np.isfinite(ev) & (ev >= lo_ev) & (ev < hi_ev)
         & (fair >= band[0]) & (fair < band[1]))
    return m, paid, ev


def kelly_stakes(p: np.ndarray, paid: np.ndarray, m: np.ndarray, frac: float = KELLY, cap: float = CAP) -> np.ndarray:
    """Fractional Kelly on the model's chance, capped, scaled so the mean stake over the bets in m is one unit
    (so staked units read beside flat units). Zero outside m."""
    with np.errstate(divide="ignore", invalid="ignore"):
        f = frac * (paid * p - 1) / (paid - 1)
    f = np.where(m & np.isfinite(f), np.clip(f, 0, cap), 0.0)
    s = f[m].mean() if m.any() else 0.0
    return f / s if s > 0 else f


def build(d: str, t0: float):
    """Round 65's field and inputs: (x, R, XR, q, use, off_tab, tab, inputs)."""
    bdir = os.environ["BETWATCH_DIR"]
    x, R, XR, num = R62.field(d, t0)
    race = R.race_id.values
    q, full, _ = R62.bsp_label(R, *R62.LABEL_FIT)
    tab = R64.ran_share(R.p_book.values, race)
    off_tab = np.log(np.clip(tab, 1e-12, None))
    mv = R64.moves(R, q, full, tab)
    day = R65.run_market(R, R65.tab_and_books(bdir), mv)
    XR = pd.concat([XR.reset_index(drop=True), R64.move_history(R, mv),
                    R65.dog_history(R, day).reset_index(drop=True), R65.trainer_history(R, mv, day.steam.values)],
                   axis=1)
    groups = R64.group_columns([c for c in XR.columns if not c.startswith("mh_")])
    every = [c for g in groups.values() for c in g]
    parts = {p: [c for c in XR.columns if re.search(pat, c)] for p, pat in R65.PARTS.items()}
    hist = groups[R64.NEW] + [c for v in parts.values() for c in v]
    no_hist = [c for c in every if c not in groups[R64.NEW]]
    return x, R, XR, q, full.astype(bool), off_tab, tab, R64.BASE + no_hist + hist


def read_saved(x: pd.DataFrame, tag: str, col: str) -> bool:
    """A model's column saved by an earlier round (corr_<tag>.csv.gz in the walk cache) onto the runners that ran."""
    cdir = os.environ.get("WALK_CACHE_DIR", "")
    f = Path(cdir) / f"corr_{tag}.csv.gz" if cdir else None
    if f is None or not f.exists():
        return False
    c = pd.read_csv(f, dtype={"race_id": "int64", "dog": str}).drop_duplicates(["race_id", "dog"])
    if col not in c:
        return False
    ran = x.is_ran.astype(bool).values
    k = pd.DataFrame({"race_id": x.race_id.values[ran].astype("int64"), "dog": x.dog.values[ran].astype(str)})
    x[col] = x.p_book
    x.loc[ran, col] = k.merge(c[["race_id", "dog", col]], on=["race_id", "dog"], how="left")[col].values
    return True


def cells(t: pd.DataFrame, tq: pd.DataFrame, m: np.ndarray, paid: np.ndarray, months: float) -> str:
    """bets | a month | A/E | realised flat ROI | realised units | corrected BSP per bet (SE) | corrected BSP units"""
    n = int(m.sum())
    if not n:
        return "0 | 0 | | | | | "
    j = R44.judged(tq, m, paid)
    won = t.won.values[m].astype(float)
    real = np.where(won == 1, paid[m] - 1, -1.0)
    if not j["n"]:
        return f"{n:,} | {n / months:.1f} | | {real.mean():+.1%} | {real.sum():+,.1f} | | "
    return (f"{n:,} | {n / months:.1f} | {j['w'] / j['e']:.3f} | {real.mean():+.1%} | {real.sum():+,.1f} | "
            f"{j['bsp']:+.1%} ({j['se']:.1%}) | {j['units']:+,.1f}")


def months_in(t: pd.DataFrame, per: np.ndarray) -> float:
    return max(t.date[per].dt.to_period("M").nunique(), 1) if per.any() else 1


def ev_table(t: pd.DataFrame, tq: pd.DataFrame, models: dict, periods: list) -> None:
    print("| period | model | fair price | expected value | bets | a month | A/E | realised flat ROI | realised units | "
          "corrected BSP per bet (SE) | corrected BSP units |\n|" + "---|" * 11)
    edges = list(EVS) + [np.inf]
    for pname, lo, hi in periods:
        per = R63.R36.in_period(t, lo, hi)
        mo = months_in(t, per)
        for mname, p in models.items():
            for bname, b0, b1 in BANDS:
                for i, e in enumerate(EVS):
                    m, paid, _ = value_bets(t, p, e, edges[i + 1], (b0, b1))
                    print(f"| {pname} | {mname} | {bname} | {e:.0%} to {edges[i + 1]:.0%} | "
                          .replace("to inf%", "and over") + cells(t, tq, m & per, paid, mo) + " |")


def cumulative_table(t: pd.DataFrame, tq: pd.DataFrame, models: dict, periods: list, bands: list) -> None:
    print("| period | model | fair price | expected value | bets | a month | A/E | realised flat ROI | realised units | "
          "corrected BSP per bet (SE) | corrected BSP units |\n|" + "---|" * 11)
    for pname, lo, hi in periods:
        per = R63.R36.in_period(t, lo, hi)
        mo = months_in(t, per)
        for mname, p in models.items():
            for bname, b0, b1 in bands:
                for e in EVS:
                    m, paid, _ = value_bets(t, p, e, np.inf, (b0, b1))
                    print(f"| {pname} | {mname} | {bname} | {e:.0%} or more | " + cells(t, tq, m & per, paid, mo) + " |")


def staking_table(t: pd.DataFrame, tq: pd.DataFrame, models: dict, band: tuple, since: tuple) -> None:
    print("| model | expected value | bets | flat: realised units | flat: corrected BSP units | quarter Kelly: realised "
          "units | quarter Kelly: corrected BSP units | largest stake (units) |\n|" + "---|" * 8)
    per = R63.R36.in_period(t, since[1], since[2])
    for mname, p in models.items():
        for e in (0.0, 0.05, 0.10, 0.20):
            m, paid, _ = value_bets(t, p, e, np.inf, band)
            m = m & per
            if not m.any():
                continue
            u = kelly_stakes(p, paid, m)
            j = R44.judged(tq, m, paid, u)
            won = t.won.values[m].astype(float)
            real = np.where(won == 1, paid[m] - 1, -1.0)
            print(f"| {mname} | {e:.0%} or more | {int(m.sum()):,} | {real.sum():+,.1f} | {j['units']:+,.1f} | "
                  f"{(u[m] * real).sum():+,.1f} | {j['kunits']:+,.1f} | {u[m].max():.1f} |")


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 67, more bets from the best model\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    if not os.environ.get("WALK_CACHE_USE", "").strip() or not os.environ.get("WALK_ISO_USE", "").strip():
        print("Both saved walks must be named (WALK_CACHE_USE and WALK_ISO_USE): nothing to test")
        return 1
    x, R, XR, q, use, off_tab, tab, inputs = build(d, t0)
    race, dates = R.race_id.values, R.date.values.astype("datetime64[ns]")
    if not read_saved(x, R65.TAG, "c_m"):
        print("Test 83's model (corr_r65) is not in the walk cache: nothing to test")
        return 1
    ran = x.is_ran.astype(bool).values
    print(f"Runners that ran at TAB's first price: {len(R):,} in {R.race_id.nunique():,} races; Test 83's model read "
          f"from the walk cache. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")

    t = x[ran].reset_index(drop=True)
    t["q_bsp"], _ = R58.corrected_bsp(t)
    tq = t.assign(p_bsp=t.q_bsp)
    since = [("Feb 2025 on", R63.SINCE, None)]
    halves = R63.HALVES
    models = {"Test 83's model": model_chance(t, "c_m")}
    card = (2.0, 15.0)

    print("## 1. Test 83's bets by their expected value at TAB's first price, Feb 2025 on, each slice on its own\n")
    ev_table(t, tq, models, since)
    print("\n## 2. The same, each threshold and above\n")
    cumulative_table(t, tq, models, since + halves, [("$2 to $15", 2.0, 15.0), ("$2 and over", 2.0, np.inf),
                                                     ("any", 0.0, np.inf)])
    print("\n## 3. Staked by a quarter of Kelly, scaled to a mean stake of one unit, the card's band, Feb 2025 on\n")
    staking_table(t, tq, models, card, since[0])
    print(f"\n({(time.monotonic() - t0) / 60:.0f} minutes in)\n")

    print(f"## 4. Test 83's inputs walked again with up to {WALK_ROUNDS:,} rounds a refit\n")
    old = R41.MAX_ROUNDS
    R41.MAX_ROUNDS = WALK_ROUNDS
    try:
        p, log, share = R41.walk_correction(R.assign(off=off_tab), XR[inputs], q, use)
    finally:
        R41.MAX_ROUNDS = old
    print("; ".join(log) + "\n")
    print("Its inputs by share of gain: " + ", ".join(f"{k} {v:.1%}" for k, v in share.head(20).items()) + "\n")
    clean = (R.n_later.fillna(0).values == 0)
    test = use & clean & (dates >= np.datetime64(R64.SPLIT))
    ok = test & np.isfinite(p)
    tab_d = R64.distance(tab[ok], q[ok], race[ok])
    dd = R64.distance(p[ok], q[ok], race[ok])
    pm = R64.ran_share(t.c_m.values.astype(float), t.race_id.values)
    k = pd.DataFrame({"race_id": t.race_id.values.astype("int64"), "dog": t.dog.values.astype(str), "pm": pm})
    rk = pd.DataFrame({"race_id": race.astype("int64"), "dog": R.dog.values.astype(str)})
    pm_r = rk.merge(k.drop_duplicates(["race_id", "dog"]), on=["race_id", "dog"], how="left").pm.values
    ok2 = ok & np.isfinite(pm_r)
    d83 = R64.distance(pm_r[ok2], q[ok2], race[ok2])
    print(f"Distance to BSP, Feb 2025 on, clean races: {dd:.2f} thousandths ({1 - dd / tab_d:+.1%} of TAB's closed), "
          f"winners' log loss {V1.ll(p[ok], R.won.values[ok]):.4f}; Test 83's model on the same races "
          f"{d83:.2f} ({1 - d83 / R64.distance(tab[ok2], q[ok2], race[ok2]):+.1%}), "
          f"{V1.ll(pm_r[ok2], R.won.values[ok2]):.4f}\n")
    s_tab = pd.Series(R.p_book.values).groupby(race).transform("sum").values
    x["c_l"] = x.p_book
    x.loc[R["index"].values, "c_l"] = p * s_tab
    cdir = os.environ.get("WALK_CACHE_DIR", "")
    if cdir:
        Path(cdir).mkdir(parents=True, exist_ok=True)
        x.loc[ran, ["race_id", "dog", "c_l"]].to_csv(Path(cdir) / f"corr_{TAG}.csv.gz", index=False,
                                                     float_format="%.9g")
    t["c_l"] = x.c_l.values[ran]
    models[f"up to {WALK_ROUNDS:,} rounds"] = model_chance(t, "c_l")

    print("## 5. Both models by the card's ratio rule at TAB's first price, flat\n")
    blends = {"Test 83's model": "c_m", f"up to {WALK_ROUNDS:,} rounds": "c_l"}
    R63.table(t, blends, {"TAB's first price": t.price.values}, since + halves)
    print("\n## 6. Both models by expected value, each threshold and above\n")
    cumulative_table(t, tq, models, since + halves, [("$2 to $15", 2.0, 15.0), ("any", 0.0, np.inf)])
    c = t[(t.n_later.fillna(0) == 0).values].reset_index(drop=True)
    cq = c.assign(p_bsp=c.q_bsp)
    print("\n## 7. Races with nothing scratched after the open, each threshold and above, Feb 2025 on\n")
    cumulative_table(c, cq, {n: model_chance(c, col) for n, col in blends.items()}, since,
                     [("$2 to $15", 2.0, 15.0), ("any", 0.0, np.inf)])
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 67")
