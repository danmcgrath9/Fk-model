"""Round 42: does the correction know where its edge is? (16 Nov 2026, founder: "Well keep testing and lets get a
fucking good model")

Test 59: a correction fitted on top of the held blend is the best forecaster we have at TAB's open (1.5686 to 1.5629
since February 2025, on BSP), yet at the card's 1.3x rule it makes three times the bets at a much lower A/E. The 1.3x
threshold was set long before the correction existed, so that does not yet say whether its best bets are better or
worse. Three ways to see it without choosing a threshold for it, on every race from February 2025 at TAB's first price:

  1. the edge ladder: every candidate (our odds 2 to 15) by how far TAB's first price sits over the model's chance
     (price x chance), with the chance the model claims (its chances over TAB's) beside the A/E it got. A model that
     knows its edge gets about what it claims, and does better the higher the ladder goes
  2. the top bets by edge: each model's 100, 200 and 400 biggest edges, so all three are compared on as many bets
  3. at 1.3x, the bets the held blend and each correction share and the ones only one of them makes

The corrections are round 41's, recomputed the same way (or read back from the walk cache, where the first run saves
them: race, dog and the two corrected chances only).

    python research/greyhound/topaz_round42.py DIR LABEL    (as round 41; WALK_CACHE_USE names the six-month walk)

Counts, sums and rates only: no race, dog or price is printed.
"""
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round33 as R33       # noqa: E402
import topaz_round37 as R37       # noqa: E402
import topaz_round41 as R41       # noqa: E402
import topaz_v1 as V1             # noqa: E402

SINCE = "2025-02-01"
BAND = (2, 15)                    # the card's band on our odds
LADDER = [0.0, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5, np.inf]
TOP = (100, 200, 400)
CORR_TAG = "r41"                  # the cached corrections: corr_r41.csv.gz and corr_r41.json in WALK_CACHE_DIR
MODELS = {"blend, held": "pb6", "correction on the winners": "pw", "correction on BSP": "pq"}


def candidates(t: pd.DataFrame, col: str):
    """Every runner the card's band admits for this model: mask, edge (TAB's first price x the model's chance) and the
    price paid after TAB's deduction."""
    p = t[col].values.astype(float)
    price = t.price.values.astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        fair = 1 / p
    m = np.isfinite(price) & (price > 1) & np.isfinite(fair) & (fair >= BAND[0]) & (fair < BAND[1])
    paid = 1 + (price - 1) * (1 - t.ded.fillna(0).values)
    return m, price * p, paid


def stats(t: pd.DataFrame, x: np.ndarray, col: str, paid: np.ndarray) -> dict:
    """Bets, winners, the A/E the model claims and the one it got (both against the price taken), z, flat ROI after
    the deduction, and the closing line."""
    n = int(x.sum())
    if not n:
        return dict(n=0)
    won = t.won.values[x].astype(float)
    price = t.price.values[x].astype(float)
    implied = (1 / price).sum()
    _, under, lr = R37.clv(t, x, paid)
    return dict(n=n, w=int(won.sum()), claim=float(t[col].values[x].sum() / implied), ae=float(won.sum() / implied),
                z=R37.z_at_price(won, price), flat=float(np.where(won == 1, paid[x] - 1, -1.0).mean()),
                under=under, lr=lr)


def row(s: dict) -> str:
    if not s["n"]:
        return "0" + " |" * 7
    under = "" if np.isnan(s["under"]) else f"{s['under']:.1%}"
    lr = "" if np.isnan(s["lr"]) else f"{s['lr']:+.3f}"
    return (f"{s['n']:,} | {s['w']:,} | {s['claim']:.3f} | {s['ae']:.3f} | {s['z']:+.1f} | {s['flat']:+.1%} | "
            f"{under} | {lr}")


HEAD = ("| bets | winners | A/E it claims | A/E it got | z | flat ROI | BSP under the price paid | "
        "mean log(price paid / BSP) |")


def ladder(t: pd.DataFrame, models: dict) -> None:
    print("| model | edge (TAB's first price x its chance) " + HEAD + "\n|---|---|---|---|---|---|---|---|---|---|")
    for name, col in models.items():
        m, e, paid = candidates(t, col)
        for lo, hi in zip(LADDER[:-1], LADDER[1:]):
            x = m & (e >= lo) & (e < hi)
            band = f"under {hi}" if lo == 0 else (f"{lo} and over" if np.isinf(hi) else f"{lo} to {hi}")
            print(f"| {name} | {band} | " + row(stats(t, x, col, paid)) + " |")


def top(t: pd.DataFrame, col: str, k: int) -> tuple:
    """The k candidates with the biggest edges, as a mask (ties broken by row order), and the paid prices."""
    m, e, paid = candidates(t, col)
    idx = np.flatnonzero(m)
    pick = idx[np.argsort(-e[idx], kind="stable")[:k]]
    x = np.zeros(len(t), bool)
    x[pick] = True
    return x, paid, float(e[pick].min()) if len(pick) else np.nan


def top_table(t: pd.DataFrame, models: dict) -> None:
    print("| model | top bets | smallest edge among them " + HEAD + "\n|---|---|---|---|---|---|---|---|---|---|---|")
    for k in TOP:
        for name, col in models.items():
            x, paid, emin = top(t, col, k)
            print(f"| {name} | {k} | {emin:.2f} | " + row(stats(t, x, col, paid)) + " |")


def split(t: pd.DataFrame, a: str, b: str, names: tuple) -> None:
    """At 1.3x: the bets both make and the ones only one makes (flat, so a shared dog counts once at one price)."""
    ma, paid, _ = R37.rule(t, a, 1.3)
    mb = R37.rule(t, b, 1.3)[0]
    print("| bets made by | " + HEAD.lstrip("| ") + "\n|---|---|---|---|---|---|---|---|---|")
    for lab, x, col in (("both", ma & mb, a), (f"only the {names[0]}", ma & ~mb, a), (f"only the {names[1]}", mb & ~ma, b)):
        print(f"| {lab} | " + row(stats(t, x, col, paid)) + " |")


def corrections(x: pd.DataFrame, R: pd.DataFrame, XR: pd.DataFrame, t0: float) -> pd.DataFrame:
    """Round 41's two corrections over x (pw, pq), read from the walk cache when a run saved them, else walked here and
    saved there."""
    d = os.environ.get("WALK_CACHE_DIR", "")
    f = Path(d) / f"corr_{CORR_TAG}.csv.gz" if d else None
    flog = Path(d) / f"corr_{CORR_TAG}.json" if d else None
    if f is not None and f.exists() and flog.exists():
        c = pd.read_csv(f, dtype={"race_id": "int64", "dog": str})
        ran = x.is_ran.astype(bool).values
        k = pd.DataFrame({"race_id": x.race_id.values[ran].astype("int64"), "dog": x.dog.values[ran].astype(str)})
        mg = k.merge(c.drop_duplicates(["race_id", "dog"]), on=["race_id", "dog"], how="left")
        x["pw"], x["pq"] = x.pb6, x.pb6           # a dog scratched after the open keeps the blend's chance
        x.loc[ran, "pw"], x.loc[ran, "pq"] = mg.pw.values, mg.pq.values
        for line in json.loads(flog.read_text()):
            print(line)
        print(f"(corrections read from the walk cache: {int(x.pw[ran].notna().sum()):,} of {int(ran.sum()):,} runners "
              "that ran)\n")
        return x
    q, full = R41.bsp_label(R)
    every = np.ones(len(R), bool)
    lines = []
    for name, col, y, use in (("correction on the winners", "pw", R.won.values.astype(float), every),
                              ("correction on BSP", "pq", q, full)):
        p, log, share = R41.walk_correction(R, XR, y, use)
        lines.append(f"**{name}**: " + "; ".join(log))
        print(lines[-1])
        print(f"({(time.monotonic() - t0) / 60:.0f} minutes in)\n")
        x[col] = x.pb6
        x.loc[R["index"].values, col] = p * R.s_ran.values
    if f is not None:
        f.parent.mkdir(parents=True, exist_ok=True)
        x.loc[x.is_ran.astype(bool).values, ["race_id", "dog", "pw", "pq"]].to_csv(f, index=False, float_format="%.9g")
        flog.write_text(json.dumps(lines))
    return x


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 42, does the correction know where its edge is?\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    a, X = R41.ours(d, t0)
    fr = R33.load(bdir, times=(0,))
    x = R33.at_time(a, fr, 0)
    x["pb6"] = V1.blend(["p_x_bet", "p_book"], x, np.asarray(R41.FIXED))[1]
    ok = pd.Series((x.price > 1).values).groupby(x.race_id.values).transform("all").values
    x = x[ok].reset_index(drop=True)
    R, XR = R41.ran_field(x, X)
    x = corrections(x, R, XR, t0)
    ran = x.is_ran.astype(bool).values
    t = x[ran & (x.date >= SINCE).values & x.pw.notna().values & x.pq.notna().values].reset_index(drop=True)
    print(f"Every race from February 2025 at TAB's first price, priced by all three: {t.race_id.nunique():,} races, "
          f"{len(t):,} runners that ran. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    print("## 1. The edge ladder: every candidate in the card's band (our odds 2 to 15), flat at the price paid after "
          "TAB's deduction\n")
    ladder(t, MODELS)
    print("\n## 2. Each model's biggest edges, as many bets each\n")
    top_table(t, MODELS)
    print("\n## 3. The card's rule at 1.3x: the bets the held blend and each correction share\n")
    for name, col in list(MODELS.items())[1:]:
        print(f"Held blend and {name}:\n")
        split(t, "pb6", col, ("held blend", name))
        print()
    print(f"{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 42")
