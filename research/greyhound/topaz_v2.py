"""Greyhound model v2: v1 plus run style and the speed map (4 Nov 2026, founder: "So we can do maps etc").

    python research/greyhound/topaz_v2.py DIR LABEL      (as topaz_v1.py)

Every feature is from the dog's EARLIER runs, never the race itself:
- RUN STYLE, from past runs' in-running positions (pir) and run line and jump codes: how often it led at the first
  point, its mean early and late position against the field, how many places it makes up, and how often each run-line
  and jump code was recorded for it (codes seen on at least 1% of runs; their meanings are GRV's, the model only needs
  them consistent);
- THE MAP for this race, from those styles and v1's early-speed ratings against the boxes: the dog's rank in the field
  by early speed, the gap to the next fastest, how many quicker beginners are drawn inside it, the early speed of the
  dogs either side, how many dogs in the race usually lead, and the dog's rail habit against its box.
Then the same models and scoring as v1, with v1 beside v2 on the same races so the gain from the map is measured.
"""
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import topaz_v1 as V1   # noqa: E402


def pir_positions(s: pd.Series) -> tuple[pd.Series, pd.Series]:
    """First and last in-running position from GRV's pir text: digits, with or without separators ("4321", "4-3-2").
    NaN when absent."""
    t = s.fillna("").astype(str)
    parts = t.str.findall(r"\d+")
    first = parts.map(lambda p: float(p[0]) if p else np.nan) if len(t) else pd.Series(dtype=float)
    last = parts.map(lambda p: float(p[-1]) if p else np.nan) if len(t) else pd.Series(dtype=float)
    # one run of single digits with no separators is one position per character
    joined = t.str.fullmatch(r"\d{2,}")
    first = first.where(~joined, t.str[0].where(joined).astype(float))
    last = last.where(~joined, t.str[-1].where(joined).astype(float))
    return first, last


def history_mean(df: pd.DataFrame, col: str, n: int = 10) -> np.ndarray:
    """Mean of `col` over the dog's last n runs on EARLIER days (the same end-of-previous-day rule as dog_form)."""
    x = df[["dog", "date", col]].copy()
    x["_i"] = np.arange(len(x))
    x = x.sort_values(["dog", "date", "_i"])
    roll = x.groupby("dog")[col].rolling(n, min_periods=1).mean().reset_index(level=0, drop=True)
    x["_m"] = roll
    day = x.groupby(["dog", "date"])._m.last().reset_index()
    day["prev"] = day.groupby("dog")._m.shift()
    m = df[["dog", "date"]].merge(day[["dog", "date", "prev"]], on=["dog", "date"], how="left")
    return m.prev.values


def add_map(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    first, last = pir_positions(df.get("pir", pd.Series(np.nan, index=df.index)))
    field = df.field.astype(float)
    df["_early"] = (first - 1) / (field - 1).clip(lower=1)           # 0 = led at the first point, 1 = last
    df["_late"] = (last - 1) / (field - 1).clip(lower=1)
    df["_led"] = (first == 1).astype(float).where(first.notna())
    df["_gain"] = (first - last).where(first.notna() & last.notna())
    feats = []
    for c, name in (("_early", "style_early"), ("_late", "style_late"), ("_led", "style_led_rate"),
                    ("_gain", "style_gain")):
        df[name] = history_mean(df, c)
        feats.append(name)
    for code_col, prefix in (("run_line", "line"), ("jump", "jump")):
        if code_col not in df:
            continue
        codes = df[code_col].fillna("").astype(str).str.strip()
        share = codes[codes != ""].value_counts(normalize=True)
        for code in share[share >= 0.01].index[:8]:
            col = f"{prefix}_{re.sub(r'[^A-Za-z0-9]+', '_', code)}"
            df["_c"] = (codes == code).astype(float).where(codes != "")
            df[col] = history_mean(df, "_c")
            feats.append(col)
    # the map: this race's field, from the history above and v1's early-speed rating
    sp = df.split_rating_mean5
    g = df.groupby("race_id")
    df["map_speed_rank"] = g.split_rating_mean5.rank(ascending=False, method="min")
    srt = g.split_rating_mean5.transform(lambda s: s.sort_values(ascending=False).iloc[1] if s.notna().sum() > 1 else np.nan)
    top = g.split_rating_mean5.transform("max")
    df["map_gap_to_next"] = np.where(sp == top, sp - srt, sp - top)
    df["map_quicker_inside"] = _quicker_inside(df)
    df = df.sort_values(["race_id", "box"])
    nb = df.groupby("race_id").split_rating_mean5
    df["map_left_speed"] = nb.shift(1)
    df["map_right_speed"] = nb.shift(-1)
    df = df.sort_values(["date", "race_id", "box"])
    df["map_leaders_in_race"] = df.groupby("race_id").style_led_rate.transform(lambda s: (s >= 0.4).sum())
    df["map_rail_vs_box"] = df.get("line_R", pd.Series(np.nan, index=df.index)) * df.box
    feats += ["map_speed_rank", "map_gap_to_next", "map_quicker_inside", "map_left_speed", "map_right_speed",
              "map_leaders_in_race", "map_rail_vs_box"]
    return df.drop(columns=[c for c in ("_early", "_late", "_led", "_gain", "_c") if c in df]), feats


def _quicker_inside(df: pd.DataFrame) -> np.ndarray:
    """For each runner: how many dogs drawn INSIDE it (lower box) have a higher early-speed rating."""
    out = np.full(len(df), np.nan)
    pos = {i: k for k, i in enumerate(df.index)}
    for _, grp in df.groupby("race_id", sort=False):
        b, s = grp.box.values, grp.split_rating_mean5.values
        for j, idx in enumerate(grp.index):
            if np.isnan(s[j]):
                continue
            out[pos[idx]] = np.sum((b < b[j]) & (s > s[j]))
    return out


def main(d, label):
    df = V1.build(d)
    m = re.search(r"since=(\d{4}-\d{2}-\d{2})", label)
    if m:
        df = df[df.date >= m.group(1)].reset_index(drop=True)
    df, map_feats = add_map(df)
    df = df.reset_index(drop=True)
    print(f"map features: {', '.join(map_feats)}")
    V1.run_scored(df, label + " (v1 features, the same races)")
    V1.NUM = V1.NUM + [f for f in map_feats if f not in V1.NUM]
    V1.REL = V1.REL + [f for f in ("style_early", "style_led_rate", "style_gain") if f in map_feats]
    V1.run_scored(df, label + " (v2: v1 + run style and the map)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz v2")
