"""Round 39: is round 38's other-books blend a look ahead? (16 Nov 2026)

Round 38 blended ours with TAB's, Sportsbet's and Ladbrokes' FIRST prices and bet at TAB's first price: about ten times
the bets of ours + TAB since February 2025, A/E 1.44. But "Sportsbet's first price" is the first one Betwatch recorded
for Sportsbet that day, whenever that was. If Ladbrokes or Sportsbet opens after TAB, its first price did not exist when
TAB's first price was there to take, and the blend reads the future. So:

  1. when each book opens against TAB, race by race and by period;
  2. the bet at TAB's first price with the other books' prices standing at that moment (no look ahead: a book not open
     yet gives no price, and TAB's chance stands in), against round 38's version with their first prices whenever;
  3. the bet once all three books are open: the field then, TAB's price then, the other books' prices then, and TAB's
     deduction for the dogs scratched after that moment.
Every blend is fitted on Test 51's window (Dec 2023 to Jun 2024, clean races) and held, as in round 38.

    python research/greyhound/topaz_round39.py DIR LABEL    (as round 38; WALK_CACHE_USE names the saved walk)

Counts, medians and rates only: no race, dog or price is printed.
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
import gbm_v0                     # noqa: E402
import topaz_round12 as R12       # noqa: E402
import topaz_round18 as R18       # noqa: E402
import topaz_round29 as R29       # noqa: E402
import topaz_round32 as R32       # noqa: E402
import topaz_round36 as R36       # noqa: E402
import topaz_round37 as R37       # noqa: E402
import topaz_round38 as R38       # noqa: E402
import topaz_round9 as R9         # noqa: E402
import topaz_walk as W            # noqa: E402

BOOKS = (("Tab", "tab"), ("Sportsbet", "sb"), ("Ladbrokes", "lb"))
EXTRA = ["sb", "lb", "sb_first", "lb_first", "lag_sb", "lag_lb", "lag_all", "to_jump"]
CORE = ["race_id", "bw_race", "date", "price", "p_book", "p_x_bet", "won", "is_ran", "s_later", "n_later", "ded"]


def flucs(ru: dict, book: str, start: float) -> list:
    fl = sorted(((float(p), R32.ts(t)) for p, t in (((ru.get("books") or {}).get(book) or {}).get("flucs") or [])
                 if p and float(p) > 1 and not np.isnan(R32.ts(t))), key=lambda f: f[1])
    return [f for f in fl if f[1] <= start] if not np.isnan(start) else fl


def race_rows(r: dict) -> list:
    """The race at two bet times, one row per runner in TAB's market then: at TAB's first price ("tab_open", each
    runner's first TAB price, as round 33), and once all three books are open ("all_open", TAB's price standing then).
    Each row carries the other books' prices standing at the bet time, their first prices whenever they came (round
    38's), and the race's lags: hours from TAB's open to Sportsbet's, Ladbrokes' and the last of the three."""
    start = R32.ts(r.get("start"))
    runners = []
    for ru in r.get("runners", []):
        fl = {k: flucs(ru, b, start) for b, k in BOOKS}
        st = R32.ts(ru.get("scratched")) if ru.get("scratched") else np.inf
        runners.append((ru, fl, np.inf if np.isnan(st) else st))
    opens = {k: min((fl[k][0][1] for _, fl, _ in runners if fl[k]), default=np.nan) for _, k in BOOKS}
    if np.isnan(opens["tab"]):
        return []
    lag = {k: (opens[k] - opens["tab"]) / 3600 for k in ("sb", "lb")}
    all_t = max(opens.values()) if not any(np.isnan(v) for v in opens.values()) else np.nan
    rows = []
    for when, bt in (("tab_open", opens["tab"]), ("all_open", all_t)):
        if np.isnan(bt) or (not np.isnan(start) and bt >= start):
            continue
        field = []
        for ru, fl, st in runners:
            if st <= bt or not fl["tab"]:
                continue
            p = fl["tab"][0][0] if when == "tab_open" else R32.price_at(fl["tab"], bt)
            if np.isnan(p):
                continue
            field.append((ru, fl, st, p))
        if not field:
            continue
        book = sum(1 / p for *_, p in field)
        later = [(fl, st, p) for _, fl, st, p in field if np.isfinite(st)]
        s = sum((1 / p) / book for _, _, p in later)
        cents = 0
        for fl, st, p in later:
            ps = R32.price_at(fl["tab"], st)
            cents += R32.table_cents(p if np.isnan(ps) else ps)
        ded = min(R32.MAX_CENTS, cents) / 100
        for ru, fl, st, p in field:
            rows.append({"bw_race": r.get("id"), "date": r.get("date"), "dog_raw": ru.get("name"), "when": when,
                         "price": p, "p_book": (1 / p) / book, "ran": not np.isfinite(st), "s_later": s,
                         "n_later": len(later), "ded": ded,
                         "sb": R32.price_at(fl["sb"], bt) if fl["sb"] else np.nan,
                         "lb": R32.price_at(fl["lb"], bt) if fl["lb"] else np.nan,
                         "sb_first": fl["sb"][0][0] if fl["sb"] else np.nan,
                         "lb_first": fl["lb"][0][0] if fl["lb"] else np.nan,
                         "lag_sb": lag["sb"], "lag_lb": lag["lb"],
                         "lag_all": (all_t - opens["tab"]) / 3600 if not np.isnan(all_t) else np.nan,
                         "to_jump": (start - bt) / 3600 if not np.isnan(start) else np.nan})
    return rows


def load(bdir: str) -> pd.DataFrame:
    rows = []
    for f in sorted(Path(bdir).glob("betwatch_VIC_G_*.json.gz")):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for r in json.load(fh).get("races", []):
                rows.extend(race_rows(r))
    fr = pd.DataFrame(rows)
    if fr.empty:
        return fr
    fr["date"] = pd.to_datetime(fr.date, errors="coerce")
    fr["_dn"] = gbm_v0.norm_name(fr.dog_raw)
    return fr.drop(columns="dog_raw")


def at_time(t: pd.DataFrame, fr: pd.DataFrame, when: str) -> pd.DataFrame:
    """topaz_round33.at_time with the other books carried: the races in t as they stood at `when`."""
    f = fr[fr.when == when]
    ran = f[f.ran].drop_duplicates(["date", "_dn"], keep=False)
    x = t.assign(_dn=gbm_v0.norm_name(t.dog_name)).merge(
        ran[["date", "_dn", "bw_race", "price", "p_book", "s_later", "n_later", "ded"] + EXTRA], on=["date", "_dn"],
        how="inner")
    n_x, n_t = x.groupby("race_id").size(), t.groupby("race_id").size()
    whole = n_x.index[(n_x == n_t.reindex(n_x.index)).values]
    one = x.groupby("race_id").bw_race.nunique()
    x = x[x.race_id.isin(whole.intersection(one.index[(one == 1).values]))].copy()
    x["p_x_bet"] = x.p_x * (1 - x.s_later)
    x["is_ran"] = True
    first = x.drop_duplicates("bw_race").set_index("bw_race")
    later = f[~f.ran & f.bw_race.isin(first.index)].copy()
    later["race_id"], later["p_x_bet"], later["won"], later["is_ran"] = later.bw_race.map(first.race_id), later.p_book, 0, False
    later["date"] = later.bw_race.map(first.date)
    keep = [c for c in x.columns if c in CORE + EXTRA or c in ("p_bsp", "p_b")]
    return pd.concat([x[keep], later[[c for c in CORE + EXTRA if c in later]]], ignore_index=True)


def ours(d: str, t0: float) -> pd.DataFrame:
    """Ours walked forward (read from the named walk), as round 36 builds it."""
    df, num, rel, note = W.build_full(d)
    df, _, _ = R18.check_features(df, os.environ.get("ISOLYNX_DIR", ""))
    df = R12.tale_columns(df)
    bfd = os.environ.get("BETFAIR_DIR", "")
    if bfd and os.path.isdir(bfd):
        df = R29.betfair_extras(df, bfd)
    to = os.environ.get("WALK_TO", "").strip()
    if to:
        df = df[df.date < to].reset_index(drop=True)
    every = max(1, int(os.environ.get("WALK_REFIT_EVERY", "6") or 6))
    df, log = W.walk_cached(df, num, rel, pd.Period("2022-11", "M"), t0, every)
    print(f"{note}\nRefits: " + "; ".join(f"{m}: {s}" for m, s in log if "priced by" not in s) + "\n")
    df = df[df.p_a.notna()].copy()
    df["p_x"] = df.p_a
    return df


def timing(fr: pd.DataFrame) -> None:
    """When each book opens against TAB, race by race."""
    r = fr[fr.when == "tab_open"].drop_duplicates("bw_race")
    f = fr[fr.when == "tab_open"]
    print("| period | races | Sportsbet open, hours after TAB's (median) | Ladbrokes (median) | Sportsbet at or before "
          "TAB | Ladbrokes at or before TAB | all three open, hours after TAB's (median) | races with all three "
          "open before the jump | TAB's field priced by Sportsbet at TAB's open | by Ladbrokes |\n|" + "---|" * 10)
    for pname, a, b in R36.PERIODS:
        g, h = r[R36.in_period(r, a, b)], f[R36.in_period(f, a, b)]
        if g.empty:
            continue
        print(f"| {pname} | {len(g):,} | {g.lag_sb.median():+.1f} | {g.lag_lb.median():+.1f} | {(g.lag_sb <= 0).mean():.0%} "
              f"| {(g.lag_lb <= 0).mean():.0%} | {g.lag_all.median():.1f} | "
              f"{fr[(fr.when == 'all_open') & fr.bw_race.isin(g.bw_race)].bw_race.nunique() / len(g):.0%} | "
              f"{h.sb.gt(1).mean():.0%} | {h.lb.gt(1).mean():.0%} |")


def blends(x: pd.DataFrame, sb: str, lb: str, tag: str, cols: dict, wts: list) -> pd.DataFrame:
    x = x.copy()
    x["p_sb"] = R38.book_chance(x, sb)
    x["p_lb"] = R38.book_chance(x, lb)
    for name, c in (("A. ours + TAB", ["p_x_bet", "p_book"]),
                    ("C. ours + TAB + Sportsbet + Ladbrokes", ["p_x_bet", "p_book", "p_sb", "p_lb"])):
        if name.startswith("A") and sb != "sb":
            continue                                   # A does not read the other books: once a time is enough
        wb, out = R38.held(x, c)
        key = f"{tag}: {name}"
        x[f"pb_{len(cols)}"] = out
        cols[key] = f"pb_{len(cols)}"
        wts.append((key, ", ".join(f"{R38.NAMES[n]} {v:.2f}" for n, v in zip(c, wb))))
    return x


def whole_races(x: pd.DataFrame) -> pd.DataFrame:
    """The runners that ran, in races where every dog in TAB's field at the bet has a TAB price."""
    ok = pd.Series((x.price > 1).values)
    whole = ok.groupby(x.race_id.values).transform("all").values
    return x[whole & x.is_ran.astype(bool).values].reset_index(drop=True)


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 39, is the other-books blend a look ahead?\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    fr = load(bdir)
    if fr.empty:
        print("No Betwatch races: nothing to test")
        return 1
    df = ours(d, t0)
    fr = fr[fr.date >= df.date.min()]
    print("## 1. When each book opens against TAB's first price (race by race; a negative lag is before TAB)\n")
    timing(fr)
    cols, wts, frames = {}, [], {}
    x0 = at_time(df, fr, "tab_open")
    x0 = blends(x0, "sb_first", "lb_first", "at TAB's open, the other books' first prices whenever (round 38)", cols, wts)
    x0 = blends(x0, "sb", "lb", "at TAB's open, the other books' prices standing then", cols, wts)
    x1 = at_time(df, fr, "all_open")
    x1 = blends(x1, "sb", "lb", "once all three are open, every price then", cols, wts)
    print("\n| blend | weights, fitted on Dec 2023 to Jun 2024 and held |\n|---|---|")
    for k, w in wts:
        print(f"| {k} | {w} |")
    t0x, t1x = whole_races(x0), whole_races(x1)
    print(f"\nAt TAB's open: {t0x.race_id.nunique():,} races, {len(t0x):,} runners that ran. Once all three are open: "
          f"{t1x.race_id.nunique():,} races, {len(t1x):,} runners; median {t1x.drop_duplicates('race_id').to_jump.median():.1f} "
          f"hours to the jump then, against {t0x.drop_duplicates('race_id').to_jump.median():.1f} at TAB's open. "
          f"{(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    c0 = {k: v for k, v in cols.items() if k.startswith("at TAB")}
    c1 = {k: v for k, v in cols.items() if k.startswith("once")}
    print("## 2. Log loss on races with nothing scratched after the bet (lower is better)\n\nAt TAB's open:\n")
    R38.ll_table(t0x, c0)
    print("\nOnce all three are open:\n")
    R38.ll_table(t1x, c1)
    print("\n## 3. The card's rule at 1.3x on TAB's price at the bet, after TAB's deduction")
    R38.rule_table(t0x, c0, "At TAB's first price, every race:")
    R38.rule_table(t0x[(t0x.n_later == 0).values].reset_index(drop=True), c0,
                   "At TAB's first price, races with nothing scratched after it:")
    R38.rule_table(t1x, c1, "At TAB's price once all three are open, every race:")
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 39")
