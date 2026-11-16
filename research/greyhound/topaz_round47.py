"""Round 47: where does the card's edge live? Judged by BSP (16 Nov 2026, founder: "Well keep testing and lets get a
fucking good model")

Tests 62 to 64: BSP is a fair judge of the held blend's bets from an edge of 1.1 to 1.5, and its judgement has a
fraction of the noise of the results, so the edge can be mapped slice by slice where 22 months of results could not.
Stated before the run, on the held blend, every race from February 2025 at TAB's first price after TAB's deduction,
for every candidate in the card's band (our odds 2 to 15) with an edge of 1.1 or over and of 1.3 or over (the card's
line), flat. Each slice gets BSP's return per bet (price paid x BSP's chance - 1) with its standard error, in each half
(to January 2026 and since), the realised flat ROI, and the winners against BSP's expected winners. The slices are:

  track, distance, class, box, our odds, the field at the bet, a dog scratched after the open or not, TAB's book at
  its first price, the hours from TAB's first price to the jump, the Melbourne hour TAB first priced the race, and the
  Melbourne hour of the race

It is a map, not a rule: a slice is a lead only if both halves agree, and a rule cut from it is tested forward on the
tracker before it reaches the card.

    python research/greyhound/topaz_round47.py DIR LABEL    (as round 46)

Counts, sums and rates only: no race, dog or price is printed (tracks are named).
"""
import gzip
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round32 as R32       # noqa: E402
import topaz_round33 as R33       # noqa: E402
import topaz_round41 as R41       # noqa: E402
import topaz_round42 as R42       # noqa: E402
import topaz_round43 as R43       # noqa: E402
import topaz_round44 as R44       # noqa: E402
import topaz_v1 as V1             # noqa: E402

MEL = "Australia/Melbourne"
TOP_TRACKS = 12
SPLIT = "2026-02-01"


def race_times(r: dict) -> dict:
    """For one Betwatch race: TAB's first price time and the start, as epoch seconds (NaN when missing)."""
    start = R32.ts(r.get("start"))
    firsts = []
    for ru in r.get("runners", []):
        fl = [R32.ts(t) for p, t in ((ru.get("books") or {}).get("Tab") or {}).get("flucs") or []
              if p and float(p) > 1 and not np.isnan(R32.ts(t)) and (np.isnan(start) or R32.ts(t) <= start)]
        if fl:
            firsts.append(min(fl))
    return {"bw_race": r.get("id"), "open_t": min(firsts) if firsts else np.nan, "start_t": start}


def open_times(d: str) -> pd.DataFrame:
    rows = []
    for f in sorted(Path(d).glob("betwatch_VIC_G_*.json.gz")):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            rows.extend(race_times(r) for r in json.load(fh).get("races", []))
    return pd.DataFrame(rows).drop_duplicates("bw_race")


def mel_hour(epoch: pd.Series) -> pd.Series:
    t = pd.to_datetime(epoch, unit="s", utc=True)
    return t.dt.tz_convert(MEL).dt.hour.where(epoch.notna())


def cut(v: pd.Series, edges: list, labels: list):
    """Bands as labels ('unknown' where the value is missing or outside them), with their print order."""
    res = pd.cut(v, edges, labels=labels, right=False).astype(object)
    return res.where(res.notna(), "unknown"), labels + ["unknown"]


def slices(t: pd.DataFrame) -> dict:
    """Each slice: (a label per runner, the order its values print in)."""
    counts = t.track.value_counts()
    top = list(counts.index[:TOP_TRACKS])
    cls = t.race_class if "race_class" in t else pd.Series(np.nan, index=t.index)
    box = t.box.astype("Int64").astype(str)
    out = {
        "track": (t.track.where(t.track.isin(top), "other tracks"), top + ["other tracks"]),
        "distance": cut(t.distance.astype(float), [0, 350, 450, 550, 10_000],
                        ["under 350 m", "350 to 449 m", "450 to 549 m", "550 m and over"]),
        "class": cut(cls.astype(float), [0, 4.5, 5.5, 7.5, 9],
                     ["grade 4 or better", "grade 5", "grade 6, 7, novice", "maiden"]),
        "box": (box, sorted(box.unique(), key=lambda b: (not b.isdigit(), b))),
        "our odds": cut(1 / t.pb6, [2, 3, 5, 8, 15], ["2 to 3", "3 to 5", "5 to 8", "8 to 15"]),
        "field at the bet": cut(t.n_bet.astype(float), [0, 7, 8, 99], ["6 or fewer", "7", "8"]),
        "scratched after the open": (pd.Series(np.where(t.n_later.fillna(0) > 0, "one or more", "none"), index=t.index),
                                     ["none", "one or more"]),
        "TAB's book at its first price": cut(t.tab_book * 100, [0, 115, 125, 135, 1000],
                                             ["under 115%", "115 to 125%", "125 to 135%", "135% and over"]),
        "hours from TAB's first price to the jump": cut(t.to_jump, [0, 6, 12, 24, 48, 10_000],
                                                        ["under 6", "6 to 12", "12 to 24", "24 to 48", "48 and over"]),
        "Melbourne hour TAB first priced it": cut(t.open_hour.astype(float), [0, 6, 12, 18, 24],
                                                  ["midnight to 6am", "6am to noon", "noon to 6pm", "6pm to midnight"]),
        "Melbourne hour of the race": cut(t.start_hour.astype(float), [0, 16, 19, 24],
                                          ["before 4pm", "4pm to 7pm", "7pm and later"]),
    }
    return {k: (pd.Series(v, index=t.index).astype(str), order) for k, (v, order) in out.items()}


def fmt(s: dict, key: str = "bsp") -> str:
    return "" if not s.get("n") else f"{s[key]:+.1%}"


def table(t: pd.DataFrame, split: str = SPLIT, halves=("to Jan 2026", "since Feb 2026"), cuts: dict = None) -> None:
    """One row per slice value (cuts: {name: (labels, order)}; default every slice), BSP's verdict and the result."""
    m11, paid, _ = R43.flat_candidates(t, "pb6", 1.1)
    m13 = R43.flat_candidates(t, "pb6", 1.3)[0]
    early = (t.date < split).values
    print("| slice | value | edge 1.1+: bets with a BSP | BSP's return per bet | its standard error | "
          f"{halves[0]} | {halves[1]} | realised flat ROI | winners | BSP's expected winners | edge 1.3+: bets with a "
          "BSP | BSP's return per bet | realised flat ROI |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for name, (lab, order) in (slices(t) if cuts is None else cuts).items():
        for v in order:
            g = (lab == v).values
            a = R44.judged(t, m11 & g, paid)
            if not a["n"]:
                continue
            e = R44.judged(t, m11 & g & early, paid)
            lt = R44.judged(t, m11 & g & ~early, paid)
            c = R44.judged(t, m13 & g, paid)
            print(f"| {name} | {v} | {a['n']:,} | {a['bsp']:+.1%} | {a['se']:.1%} | {fmt(e)} | {fmt(lt)} | "
                  f"{a['flat']:+.1%} | {a['w']:,} | {a['e']:,.1f} | {c.get('n', 0):,} | {fmt(c)} | "
                  f"{fmt(c, 'flat')} |")


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 47, where does the card's edge live? Judged by BSP\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    x = field(d, bdir, t0)
    t = x[x.is_ran.astype(bool).values & (x.date >= R42.SINCE).values].reset_index(drop=True)
    print(f"Every race from February 2025 at TAB's first price: {t.race_id.nunique():,} races, {len(t):,} runners "
          f"that ran; TAB's first price time known for {t.open_t.notna().mean():.1%}. "
          f"{(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    table(t)
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


def field(d: str, bdir: str, t0: float) -> pd.DataFrame:
    """The field at TAB's first price with the held blend, TAB's book, the field size and the open and start times."""
    a, _ = R41.ours(d, t0)
    fr = R33.load(bdir, times=(0,))
    x = R33.at_time(a, fr, 0)
    x["pb6"] = V1.blend(["p_x_bet", "p_book"], x, np.asarray(R41.FIXED))[1]
    ok = pd.Series((x.price > 1).values).groupby(x.race_id.values).transform("all").values
    x = x[ok].reset_index(drop=True)
    x["tab_book"] = (1 / x.price).groupby(x.race_id.values).transform("sum")
    x["n_bet"] = x.groupby("race_id").race_id.transform("size")
    ot = open_times(bdir)
    x = x.merge(ot, on="bw_race", how="left")
    x["to_jump"] = (x.start_t - x.open_t) / 3600
    x["open_hour"], x["start_hour"] = mel_hour(x.open_t), mel_hour(x.start_t)
    return x


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 47")
