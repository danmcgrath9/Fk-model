"""Round 61: what does TAB's opening price get wrong? Every input, one at a time (16 Nov 2026, founder: "We HAVE to be
able to beat Victoria, I can guarantee you we have more knowlege than TAB"; "Do research, you have all the information")

Tests 71 to 74 found leans in TAB's first price by checking its calibration across a handful of groups, and Test 75
found the card's edge is one of them (GRV's first tip, priced long at TAB's open). This round runs the same check over
every input ours has. Stated before the run, on round 58's field, every race with nothing scratched after the open and
a BSP on every runner, from May 2023:

  - each input that varies within a race is cut two ways: the dog's order on it within its race (highest, 2nd, 3rd,
    4th or lower, missing), and the fifth of all runners it falls in (missing apart); an input with five values or
    fewer is cut by its values; inputs that do not vary within most races are skipped (their A/E is 1 by construction)
  - in each cell, winners against the chances given (A/E and z) in each half (May 2023 to January 2025, and since
    February 2025) for four forecasts: TAB's first book after its favourite-longshot bias (one power, fitted on Test
    51's window), the card's blend, the blend with Isolynx, and BSP corrected for its first-tip and weight leans (Test
    76)
  - a cell counts for a forecast only with |z| of 2 or more in both halves and the same sign; at about a thousand cells,
    about one passes for each forecast by chance
  - reported: where TAB's first price is wrong; where the card's blend is wrong; where both are wrong the same way,
    which is knowledge the card does not use yet; and the same scan inside GRV's first tips, where the card's bets are

    python research/greyhound/topaz_round61.py DIR LABEL    (as round 51)

Counts, sums and rates only: no race, dog or price is printed (inputs are named).
"""
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round33 as R33       # noqa: E402
import topaz_round50 as R50       # noqa: E402
import topaz_round51 as R51       # noqa: E402
import topaz_round55 as R55       # noqa: E402
import topaz_round57 as R57       # noqa: E402
import topaz_round58 as R58       # noqa: E402

MODELS = {"TAB after its favourite bias": "p_tab_fl", "the card's blend": "h_p_x_bet", "blend with Isolynx": "h_p_i_bet",
          "BSP corrected": "q_bsp"}
SPLIT = "2025-02-01"
Z = 2.0
TOP = 40
VARIES = 0.5


def cuts(t: pd.DataFrame, f: str) -> dict:
    """The ways one input is cut: {name: a label per runner}. Empty when it does not vary within most races."""
    v = pd.to_numeric(t[f], errors="coerce").astype(float)
    if v.nunique(dropna=True) <= 1:
        return {}
    within = v.groupby(t.race_id.values).transform("nunique")
    if (within > 1).mean() < VARIES:
        return {}
    if v.nunique(dropna=True) <= 5:
        return {"value": pd.Series(np.where(v.isna(), "missing", v.map(lambda x: f"{x:g}")), index=t.index)}
    r = v.groupby(t.race_id.values).rank(ascending=False, method="min")
    order = pd.Series(np.select([v.isna(), r == 1, r == 2, r == 3], ["missing", "highest in the race", "2nd", "3rd"],
                                "4th or lower"), index=t.index)
    q = pd.qcut(v, 5, labels=False, duplicates="drop")
    fifth = pd.Series(np.where(q.isna(), "missing", "fifth " + (q.fillna(-1).astype(int) + 1).astype(str)), index=t.index)
    return {"order in the race": order, "fifth of all runners": fifth}


def cell_table(t: pd.DataFrame, lab: pd.Series, half: np.ndarray, models: dict) -> pd.DataFrame:
    """One row per label: runners, and per forecast and half the A/E and z (keys 'forecast|half|ae' and '|z')."""
    base = pd.DataFrame({"lab": lab.values, "h": half, "w": t.won.values.astype(float)})
    out = pd.DataFrame({"n": base.groupby("lab").size()})
    for name, c in models.items():
        p = t[c].values.astype(float)
        g = base.assign(p=p, v=p * (1 - p)).groupby(["lab", "h"])[["w", "p", "v"]].sum().unstack("h")
        for h in (0, 1):
            if ("w", h) in g.columns:
                w_, p_, v_ = (g[(k, h)].reindex(out.index) for k in ("w", "p", "v"))
            else:
                w_ = p_ = v_ = pd.Series(np.nan, index=out.index)
            out[f"{name}|{h}|ae"] = (w_ / p_).where(p_ > 0)
            out[f"{name}|{h}|z"] = ((w_ - p_) / np.sqrt(v_)).where(v_ > 0)
    return out


def labelled(t: pd.DataFrame, inputs: list, cats=("sex",)) -> list:
    """(input, cut, a label per runner) for every input, cut on the whole field."""
    out = []
    for f in inputs:
        if f not in t:
            continue
        if f in cats:
            lab = t[f].astype(object).where(t[f].notna(), "missing").astype(str)
            if lab.nunique() > 1:
                out.append((f, "value", lab))
            continue
        for how, lab in cuts(t, f).items():
            out.append((f, how, lab))
    return out


def scan(t: pd.DataFrame, labels: list, mask: np.ndarray = None, models: dict = None) -> pd.DataFrame:
    """Every cell of every input (within mask), with a pass flag (+1, -1 or 0) and the smaller |z| per forecast."""
    models = MODELS if models is None else models
    m = np.ones(len(t), bool) if mask is None else mask
    tt = t[m]
    half = np.where(tt.date.values < np.datetime64(SPLIT), 0, 1)
    rows = []
    for f, how, lab in labels:
        c = cell_table(tt, lab[m], half, models)
        c.insert(0, "input", f)
        c.insert(1, "cut", how)
        rows.append(c.reset_index().rename(columns={"lab": "value"}))
    if not rows:
        return pd.DataFrame()
    res = pd.concat(rows, ignore_index=True)
    for name in models:
        z0, z1 = res[f"{name}|0|z"], res[f"{name}|1|z"]
        res[f"{name}|pass"] = np.where((z0 >= Z) & (z1 >= Z), 1, np.where((z0 <= -Z) & (z1 <= -Z), -1, 0))
        res[f"{name}|minz"] = np.minimum(z0.abs(), z1.abs())
    return res


def cell(r, name) -> str:
    a0, a1 = r[f"{name}|0|ae"], r[f"{name}|1|ae"]
    if pd.isna(a0) or pd.isna(a1):
        return ""
    return f"{a0:.3f} ({r[f'{name}|0|z']:+.1f}) / {a1:.3f} ({r[f'{name}|1|z']:+.1f})"


def show(res: pd.DataFrame, rows: pd.DataFrame, models: dict, title: str) -> None:
    print(f"{title}\n\n| input | cut | value | runners | " + " | ".join(models) + " |\n|" + "---|" * (4 + len(models)))
    for _, r in rows.head(TOP).iterrows():
        print(f"| {r['input']} | {r['cut']} | {r['value']} | {int(r['n']):,} | "
              + " | ".join(cell(r, m) for m in models) + " |")
    if len(rows) > TOP:
        print(f"\n({len(rows) - TOP} more not shown)")
    print()


def report(res: pd.DataFrame, models: dict) -> None:
    tab, card = "TAB after its favourite bias", "the card's blend"
    n = len(res)
    print(f"{n:,} cells. Passing in both halves: " + ", ".join(f"{m} {int((res[m + '|pass'] != 0).sum())}"
                                                             for m in models) + "\n")
    srt = lambda x, m: x.sort_values(m + "|minz", ascending=False)          # noqa: E731
    show(res, srt(res[res[tab + "|pass"] != 0], tab), models,
         "**Where TAB's first price is wrong** (A/E (z), May 2023 to Jan 2025 / since Feb 2025; over 1 wins more than "
         "it says):")
    show(res, srt(res[res[card + "|pass"] != 0], card), models, "**Where the card's blend is wrong:**")
    both = res[(res[tab + "|pass"] != 0) & (res[tab + "|pass"] == res[card + "|pass"])]
    show(res, srt(both, card), models, "**Where both are wrong the same way** (knowledge the card does not use yet):")


def field(d: str, t0: float):
    """Round 57's field with the walk's input list; clean races only, with TAB after its bias and BSP corrected."""
    df, num = R51.named_walks(d, t0, with_inputs=True)
    fr = R33.load(os.environ["BETWATCH_DIR"], times=(0,))
    x = R33.at_time(df, fr, 0)
    ran = x.is_ran.astype(bool).values
    x["p_i_bet"] = np.where(ran, x.p_i * (1 - x.s_later.fillna(0)), x.p_book)
    ok = pd.Series((x.price > 1).values).groupby(x.race_id.values).transform("all").values
    x = R57.term_columns(x[ok].reset_index(drop=True))
    for c in R51.OURS.values():
        x[f"h_{c}"] = R51.apply_weights(x, [c, "p_book"], R50.FIXED)
    t = x[x.is_ran.astype(bool).values].reset_index(drop=True)
    t["q_bsp"], _ = R58.corrected_bsp(t)
    clean = t[(t.n_later == 0).values & t.q_bsp.notna().groupby(t.race_id.values).transform("all").values]
    clean = clean.reset_index(drop=True)
    w = R51.fit_weights(clean, ["p_book"], *R51.FIT)
    clean["p_tab_fl"] = R51.apply_weights(clean, ["p_book"], w)
    return clean, num, float(w[0])


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 61, what does TAB's opening price get wrong? Every input, one at a time\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    if not os.environ.get("WALK_CACHE_USE", "").strip() or not os.environ.get("WALK_ISO_USE", "").strip():
        print("Both saved walks must be named (WALK_CACHE_USE and WALK_ISO_USE): nothing to test")
        return 1
    t, num, power = field(d, t0)
    inputs = list(dict.fromkeys(num + ["sex"]))
    print(f"\nRaces with nothing scratched after the open and a BSP on every runner, from May 2023: "
          f"{t.race_id.nunique():,} races, {len(t):,} runners; {len(inputs)} inputs; TAB's first book after its "
          f"favourite bias is its chances to the power {power:.3f}. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    labels = labelled(t, inputs)
    print(f"{len(labels)} cuts of {len({f for f, _, _ in labels})} inputs that vary within a race.\n")
    print("## 1. Every runner\n")
    report(scan(t, labels), MODELS)
    tip1 = R55.col(t, "tip_rank").values == 1
    print(f"## 2. Inside GRV's first tips ({int(tip1.sum()):,} runners; each input cut on the whole field)\n")
    report(scan(t, labels, tip1), MODELS)
    print(f"{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 61")
