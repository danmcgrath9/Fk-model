"""Round 53: does ours with Isolynx mark a dog down for having no tracking history? (16 Nov 2026, founder: "Well keep
testing and lets get a fucking good model")

Test 70: ours with Isolynx gives a winner with a tracked run before the race a much better chance (0.0296 of log loss
from May 2023 to January 2025, 0.0160 since), and a winner with none a worse one (0.0349 and 0.0185). A split by the
winner's group cannot tell a model that knows more about tracked dogs from one that marks a dog down for having no
tracking history. Calibration can. Stated before the run, on round 50's prices (both saved walks read by name), every
race with nothing scratched after the open and a BSP on every runner, from May 2023 to January 2025 and since February
2025:

  1. winners against the chances given (A/E, with z), for TAB's first book, ours without and with Isolynx, the two
     blends at 0.54 / 0.67 and BSP, by race make-up (every runner with a tracked run, some, none) and, in the mixed
     races, by the runner (a tracked run before or not)
  2. in the mixed races, the same for ours without and with Isolynx and BSP by each model's own odds (under 3, 3 to 6,
     6 to 12, 12 and over)
  3. log loss by race make-up

A model that knows more about the tracked dogs stays near A/E 1 for both kinds of runner. One that marks the untracked
down has A/E over 1 for them, and under 1 for the tracked dogs beside them, in the mixed races.

    python research/greyhound/topaz_round53.py DIR LABEL    (as round 51)

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
import topaz_round50 as R50       # noqa: E402
import topaz_round51 as R51       # noqa: E402

PERIODS = [("May 2023 to Jan 2025", "2023-05-01", "2025-02-01"), ("Feb 2025 on", "2025-02-01", None)]
MODELS = {"TAB's first book": "p_book", "ours, no Isolynx": "p_x_bet", "ours, with Isolynx": "p_i_bet",
          "blend, no Isolynx (the card)": "h_p_x_bet", "blend, with Isolynx": "h_p_i_bet", "BSP": "p_bsp"}
BAND_MODELS = {"ours, no Isolynx": "p_x_bet", "ours, with Isolynx": "p_i_bet", "BSP": "p_bsp"}
BANDS = [("under 3", 1 / 3, 1.01), ("3 to 6", 1 / 6, 1 / 3), ("6 to 12", 1 / 12, 1 / 6), ("12 and over", 0, 1 / 12)]


def ae(won: np.ndarray, p: np.ndarray) -> dict:
    """Winners against the chances given: runners, winners, expected, A/E and z."""
    p = np.asarray(p, float)
    won = np.asarray(won, float)
    e, var = p.sum(), (p * (1 - p)).sum()
    return dict(n=len(p), w=int(won.sum()), e=float(e), ae=float(won.sum() / e) if e > 0 else np.nan,
                z=float((won.sum() - e) / np.sqrt(var)) if var > 0 else np.nan)


def make_up(t: pd.DataFrame) -> pd.Series:
    """Each runner's race: 'every runner tracked', 'some tracked' or 'none tracked' (a tracked run before the race)."""
    tracked = (t.iso_runs.fillna(0) > 0).astype(float)
    share = tracked.groupby(t.race_id.values).transform("mean")
    return pd.Series(np.select([share >= 1, share <= 0], ["every runner tracked", "none tracked"], "some tracked"),
                     index=t.index)


def prepare(d: str, t0: float) -> pd.DataFrame:
    """Round 52's field: both walks, TAB's first price, the blends at 0.54 / 0.67; runners that ran, races with nothing
    scratched after the open and a BSP on every runner."""
    df = R51.named_walks(d, t0)
    fr = R33.load(os.environ["BETWATCH_DIR"], times=(0,))
    x = R33.at_time(df, fr, 0)
    ran = x.is_ran.astype(bool).values
    x["p_i_bet"] = np.where(ran, x.p_i * (1 - x.s_later.fillna(0)), x.p_book)
    ok = pd.Series((x.price > 1).values).groupby(x.race_id.values).transform("all").values
    x = x[ok].reset_index(drop=True)
    for c in R51.OURS.values():
        x[f"h_{c}"] = R51.apply_weights(x, [c, "p_book"], R50.FIXED)
    t = x[x.is_ran.astype(bool).values & (x.n_later == 0).values].reset_index(drop=True)
    full = t.p_bsp.notna().groupby(t.race_id.values).transform("all").to_numpy(copy=True)
    return t[full].reset_index(drop=True)


def calibration(t: pd.DataFrame, mk: pd.Series) -> None:
    tracked = (t.iso_runs.fillna(0) > 0).values
    cells = [("every runner tracked", "all", None), ("some tracked", "a tracked run before", True),
             ("some tracked", "none", False), ("none tracked", "all", None)]
    print("| period | race make-up | runners | model | runners | winners | expected | A/E | z |\n"
          "|---|---|---|---|---|---|---|---|---|")
    for pname, lo, hi in PERIODS:
        p = R36.in_period(t, lo, hi)
        for race, rname, flag in cells:
            g = p & (mk == race).values & (np.ones(len(t), bool) if flag is None else tracked == flag)
            if not g.any():
                continue
            for name, col in MODELS.items():
                s = ae(t.won.values[g], t[col].values[g])
                print(f"| {pname} | {race} | {rname} | {name} | {s['n']:,} | {s['w']:,} | {s['e']:,.1f} | "
                      f"{s['ae']:.3f} | {s['z']:+.1f} |")


def by_band(t: pd.DataFrame, mk: pd.Series) -> None:
    tracked = (t.iso_runs.fillna(0) > 0).values
    mixed = (mk == "some tracked").values
    print("| period | runners | model | its odds | runners | winners | expected | A/E | z |\n"
          "|---|---|---|---|---|---|---|---|---|")
    for pname, lo, hi in PERIODS:
        p = R36.in_period(t, lo, hi) & mixed
        for rname, flag in (("a tracked run before", True), ("none", False)):
            for name, col in BAND_MODELS.items():
                q = t[col].values.astype(float)
                for bname, a, b in BANDS:
                    g = p & (tracked == flag) & (q > a) & (q <= b)
                    if not g.any():
                        continue
                    s = ae(t.won.values[g], q[g])
                    print(f"| {pname} | {rname} | {name} | {bname} | {s['n']:,} | {s['w']:,} | {s['e']:,.1f} | "
                          f"{s['ae']:.3f} | {s['z']:+.1f} |")


def ll_make_up(t: pd.DataFrame, mk: pd.Series) -> None:
    w = (t.won == 1).values
    print("| period | race make-up | races | " + " | ".join(MODELS) + " |\n|" + "---|" * (len(MODELS) + 3))
    for pname, lo, hi in PERIODS:
        p = R36.in_period(t, lo, hi) & w
        for race in ("every runner tracked", "some tracked", "none tracked"):
            g = t[p & (mk == race).values]
            if len(g):
                print(f"| {pname} | {race} | {g.race_id.nunique():,} | "
                      + " | ".join(f"{R50.ll(g, c):.4f}" for c in MODELS.values()) + " |")


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 53, does ours with Isolynx mark a dog down for having no tracking history?\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    if not os.environ.get("WALK_CACHE_USE", "").strip() or not os.environ.get("WALK_ISO_USE", "").strip():
        print("Both saved walks must be named (WALK_CACHE_USE and WALK_ISO_USE): nothing to test")
        return 1
    t = prepare(d, t0)
    if "iso_runs" not in t:
        print("No tracked-run count (iso_runs): nothing to test")
        return 1
    mk = make_up(t)
    races = t.groupby("race_id").date.first()
    rmk = mk.groupby(t.race_id.values).first()
    print(f"\nRaces with nothing scratched after the open and a BSP on every runner, from May 2023: {len(races):,} "
          f"races, {len(t):,} runners; every runner tracked in {(rmk == 'every runner tracked').mean():.0%} of races, "
          f"some in {(rmk == 'some tracked').mean():.0%}, none in {(rmk == 'none tracked').mean():.0%}. "
          f"{(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    print("## 1. Winners against the chances given, by race make-up and runner\n")
    calibration(t, mk)
    print("\n## 2. In the mixed races, by each model's own odds\n")
    by_band(t, mk)
    print("\n## 3. Log loss by race make-up (lower is better)\n")
    ll_make_up(t, mk)
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 53")
