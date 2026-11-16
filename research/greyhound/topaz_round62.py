"""Round 62: the blend corrected for its own mistakes (17 Nov 2026, founder: "We HAVE to be able to beat Victoria, I can
guarantee you we have more knowlege than TAB"; "Do research, you have all the information")

Test 79 (round 61): TAB's first price is wrong in 71 cells of every input in both halves, and the card's blend corrects
almost all of them: it shares only five, all of them Isolynx speeds, which the blend with Isolynx halves. So ours knows
more than TAB's opening price. But the card's blend is wrong in 74 cells of its own where TAB is right, mostly trusting a
dog's recent ratings and past market support too much and its poor recent finishes too little, and it over-rates GRV's
first tips with no tracking history by about 9%. Those errors make false edges against TAB, and the card cannot tell
them from the real ones. The blend with Isolynx has 35. Stated before the run:

  - round 41's correction (a gradient-boosted race softmax that starts from a blend and learns only where it is wrong,
    over every input ours has plus ours, TAB's first book, the gap between them, TAB's book, the share scratched after
    the open and the field), now started from the blend with Isolynx (0.54 / 0.67), walked forward exactly as round 41
    (refitted every two months from November 2024, rounds chosen on the three months before each refit)
  - on two labels: the winners, and BSP corrected for its first-tip and weight leans (the correction's factors fitted on
    May 2023 to January 2025 and applied to every race, so the label carries no information from after January 2025)
  - judged from February 2025, against the card's blend and the blend with Isolynx: log loss, how many of Test 79's
    cells each still gets wrong in both halves (February 2025 to January 2026, and since), the card's rule at 1.3x and
    BSP's verdict by the corrected BSP (Test 76), and the same numbers of bets
  - the corrections' inputs by their share of its gain: what the blend gets wrong
  - the corrections are saved to the walk cache (corr_r62) for the rounds after

    python research/greyhound/topaz_round62.py DIR LABEL    (as round 51)

Counts, sums and rates only: no race, dog or price is printed. The corrections' inputs are named.
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
import topaz_round36 as R36       # noqa: E402
import topaz_round41 as R41       # noqa: E402
import topaz_round50 as R50       # noqa: E402
import topaz_round51 as R51       # noqa: E402
import topaz_round52 as R52       # noqa: E402
import topaz_round57 as R57       # noqa: E402
import topaz_round58 as R58       # noqa: E402
import topaz_round61 as R61       # noqa: E402
import topaz_theories as T        # noqa: E402

TAG = "r62"
SINCE = "2025-02-01"
PERIODS = [("Feb 2025 to Jan 2026", "2025-02-01", "2026-02-01"), ("Feb 2026 on", "2026-02-01", None),
           ("Feb 2025 on", "2025-02-01", None)]
LABEL_FIT = ("2023-05-01", "2025-02-01")
BLENDS = {"the card's blend": "h_p_x_bet", "blend with Isolynx": "h_p_i_bet",
          "with Isolynx, corrected on the winners": "c_w", "with Isolynx, corrected on BSP corrected": "c_q"}


def bsp_label(R: pd.DataFrame, lo: str, hi: str):
    """BSP corrected for its first-tip and weight leans, with factors fitted on [lo, hi) and applied to every race with
    a BSP on every runner that ran; (the label over R's rows, which rows have it, the factors)."""
    full = R.p_bsp.notna().groupby(R.race_id.values).transform("all").to_numpy(copy=True)
    w = R51.fit_weights(R[full], R58.COLS, lo, hi)
    q = np.zeros(len(R))
    q[full] = R51.apply_weights(R[full], R58.COLS, w).values
    return q, full, w


def field(d: str, t0: float):
    """The field at TAB's first price with both blends, the inputs aligned, and the runners that ran (R, XR) with the
    blend with Isolynx as the offset and ours with Isolynx as ours."""
    df, num, rel = R51.named_walks(d, t0, with_inputs=True)
    df = df.reset_index(drop=True)
    df["_row"] = np.arange(len(df))
    X = T.features(df, num, rel)
    fr = R33.load(os.environ["BETWATCH_DIR"], times=(0,))
    x = R33.at_time(df, fr, 0)
    ran = x.is_ran.astype(bool).values
    x["p_i_bet"] = np.where(ran, x.p_i * (1 - x.s_later.fillna(0)), x.p_book)
    ok = pd.Series((x.price > 1).values).groupby(x.race_id.values).transform("all").values
    x = R57.term_columns(x[ok].reset_index(drop=True))
    for c in R51.OURS.values():
        x[f"h_{c}"] = R51.apply_weights(x, [c, "p_book"], R50.FIXED)
    xi = x.assign(p_x_bet=x.p_i_bet, pb6=x.h_p_i_bet)
    R, XR = R41.ran_field(xi, X)
    return x, R, XR, num


def corrections(x: pd.DataFrame, R: pd.DataFrame, XR: pd.DataFrame, t0: float) -> pd.DataFrame:
    """Both corrections over x (c_w, c_q), read from the walk cache when a run saved them, else walked and saved."""
    d = os.environ.get("WALK_CACHE_DIR", "")
    f = Path(d) / f"corr_{TAG}.csv.gz" if d else None
    flog = Path(d) / f"corr_{TAG}.json" if d else None
    ran = x.is_ran.astype(bool).values
    x["c_w"], x["c_q"] = x.h_p_i_bet, x.h_p_i_bet          # a dog scratched after the open keeps the blend's chance
    if f is not None and f.exists() and flog.exists():
        c = pd.read_csv(f, dtype={"race_id": "int64", "dog": str})
        k = pd.DataFrame({"race_id": x.race_id.values[ran].astype("int64"), "dog": x.dog.values[ran].astype(str)})
        mg = k.merge(c.drop_duplicates(["race_id", "dog"]), on=["race_id", "dog"], how="left")
        x.loc[ran, "c_w"], x.loc[ran, "c_q"] = mg.c_w.values, mg.c_q.values
        for line in json.loads(flog.read_text()):
            print(line)
        print("(corrections read from the walk cache)\n")
        return x
    q, full, w = bsp_label(R, *LABEL_FIT)
    lines = [f"BSP corrected for the label: power {w[0]:.3f}, first tip x{np.exp(w[1]):.3f}, up 0.5 kg or more "
             f"x{np.exp(w[2]):.3f} (fitted on May 2023 to Jan 2025)"]
    print(lines[-1] + "\n")
    for name, col, y, use in (("corrected on the winners", "c_w", R.won.values.astype(float), np.ones(len(R), bool)),
                              ("corrected on BSP corrected", "c_q", q, full)):
        p, log, share = R41.walk_correction(R, XR, y, use)
        lines.append(f"**{name}**: " + "; ".join(log))
        lines.append(f"its inputs by share of gain: " + ", ".join(f"{k} {v:.1%}" for k, v in share.head(20).items()))
        print(lines[-2] + "\n\n" + lines[-1])
        print(f"({(time.monotonic() - t0) / 60:.0f} minutes in)\n")
        x.loc[R["index"].values, col] = p * R.s_ran.values
    if f is not None:
        f.parent.mkdir(parents=True, exist_ok=True)
        x.loc[ran, ["race_id", "dog", "c_w", "c_q"]].to_csv(f, index=False, float_format="%.9g")
        flog.write_text(json.dumps(lines))
    return x


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 62, the blend corrected for its own mistakes\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    if not os.environ.get("WALK_CACHE_USE", "").strip() or not os.environ.get("WALK_ISO_USE", "").strip():
        print("Both saved walks must be named (WALK_CACHE_USE and WALK_ISO_USE): nothing to test")
        return 1
    x, R, XR, num = field(d, t0)
    print(f"\nRunners that ran at TAB's first price: {len(R):,} in {R.race_id.nunique():,} races. "
          f"{(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    print("## 1. The corrections, walked forward from November 2024\n")
    x = corrections(x, R, XR, t0)
    t = x[x.is_ran.astype(bool).values].reset_index(drop=True)
    t["q_bsp"], _ = R58.corrected_bsp(t)
    since = R36.in_period(t, SINCE, None)
    print("## 2. Log loss on the winners (lower is better)\n")
    R51.ll_table(t, BLENDS, PERIODS)
    print("\n## 3. How many of the cells of every input each still gets wrong, Feb 2025 to Jan 2026 / since Feb 2026\n")
    clean = t[(t.n_later == 0).values & t.q_bsp.notna().groupby(t.race_id.values).transform("all").values]
    clean = clean.reset_index(drop=True)
    w = R51.fit_weights(clean, ["p_book"], *R51.FIT)
    clean["p_tab_fl"] = R51.apply_weights(clean, ["p_book"], w)
    models = {"TAB after its favourite bias": "p_tab_fl", **BLENDS, "BSP corrected": "q_bsp"}
    old = R61.SPLIT
    R61.SPLIT = "2026-02-01"
    try:
        labels = R61.labelled(clean, list(dict.fromkeys(num + ["sex"])))
        res = R61.scan(clean, labels, R36.in_period(clean, SINCE, None), models)
    finally:
        R61.SPLIT = old
    print(f"{len(res):,} cells. Wrong in both halves: " + ", ".join(f"{m} {int((res[m + '|pass'] != 0).sum())}"
                                                                    for m in models) + "\n")
    best = "with Isolynx, corrected on BSP corrected"
    R61.show(res, res[res[best + "|pass"] != 0].sort_values(best + "|minz", ascending=False), models,
             f"**Where the blend {best} is still wrong:**")
    tq = t.assign(p_bsp=t.q_bsp)
    print("## 4. The bets, BSP's verdict by the corrected BSP\n")
    R51.judge(tq, BLENDS, PERIODS)
    print("\n## 5. The best N candidates by edge since February 2025, judged by the corrected BSP, flat\n")
    R52.ladder(tq, {"since Feb 2025": since}, R52.NS, BLENDS)
    print()
    R52.ladder(tq, {h: R36.in_period(tq, lo, hi) for h, lo, hi in R52.HALVES}, tuple(n // 2 for n in R52.NS), BLENDS)
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 62")
