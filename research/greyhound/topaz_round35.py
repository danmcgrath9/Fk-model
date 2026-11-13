"""Round 35: the Betwatch field at TAB's open, month by month, against who actually ran (13 Nov 2026).

Round 34 made 723 of the card rule's bets from May 2023 to March 2025 and 10 from March 2025 to November 2026. A rule
that stops betting is a sign the data changed, not the dogs. Round 33 builds the field at the bet from Betwatch alone:
a runner with TAB prices and no scratching time counts as a runner. A dog that did not run but carries no scratching
time (an emergency that got no start, or a scratching Betwatch did not time) then sits in TAB's opening book, takes a
share of it from the dogs that ran, and brings no deduction. That makes TAB's price look long against ours.

    python research/greyhound/topaz_round35.py DIR LABEL      (DIR: the Topaz runs; BETWATCH_DIR: the Betwatch files)

No model. Per month, from the Betwatch files and Topaz's runs (scratched rows kept):
  - Betwatch runners listed a race, with TAB prices, with a scratching time, flagged emergency (and of those, with TAB
    prices and with a scratching time)
  - round 33's field at the open: its size, TAB's book over it, races with a dog scratched after the open, the deduction
  - "phantoms": runners in that field with no scratching time whom Topaz does not have running (scratched in Topaz, or
    not in the race at all), and their share of TAB's opening book
  - hours from TAB's first price to the jump
Counts and medians only: no race, dog or price is printed.
"""
import gzip
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import gbm_v0                     # noqa: E402
import topaz_round32 as R32       # noqa: E402


def topaz_status(d: str) -> pd.DataFrame:
    """One row per Topaz runner, scratched ones included: date, normalised dog name, race, whether it ran."""
    rows = []
    for f in sorted(Path(d).glob("runs_*_*.json.gz")):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for r in json.load(fh):
                rows.append((r.get("meetingDate"), r.get("dogName"), r.get("raceId"), bool(r.get("scratched"))))
    t = pd.DataFrame(rows, columns=["date", "dog", "race_id", "scratched"])
    t["date"] = pd.to_datetime(t.date.astype(str).str[:10], errors="coerce")
    t["_dn"] = gbm_v0.norm_name(t.dog.fillna(""))
    return t.drop(columns="dog").drop_duplicates(["date", "_dn", "race_id"])


def race_audit(r: dict) -> list:
    """One row per Betwatch runner: what Betwatch says of it, and whether it is in round 33's field at the open."""
    start = R32.ts(r.get("start"))
    runners = []
    for ru in r.get("runners", []):
        fl = sorted(((float(p), R32.ts(t)) for p, t in ((ru.get("books") or {}).get("Tab") or {}).get("flucs") or []
                     if p and float(p) > 1 and not np.isnan(R32.ts(t))), key=lambda f: f[1])
        if not np.isnan(start):
            fl = [f for f in fl if f[1] <= start]
        st = R32.ts(ru.get("scratched")) if ru.get("scratched") else np.inf
        runners.append((ru, fl, np.inf if np.isnan(st) else st, bool(ru.get("scratched"))))
    firsts = [fl[0][1] for _, fl, _, _ in runners if fl]
    open_t = min(firsts) if firsts else np.nan
    field = [(ru, fl, st) for ru, fl, st, _ in runners if fl and not st <= open_t]
    book = sum(1 / fl[0][0] for _, fl, _ in field) if field else np.nan
    later = [(fl, st) for _, fl, st in field if np.isfinite(st)]
    cents = 0
    for fl, st in later:
        ps = R32.price_at(fl, st)
        cents += R32.table_cents(fl[0][0] if np.isnan(ps) else ps)
    rows = []
    for ru, fl, st, flagged in runners:
        in_field = bool(fl) and not st <= open_t
        rows.append({"bw_race": r.get("id"), "date": r.get("date"), "dog_raw": ru.get("name"),
                     "has_tab": bool(fl), "scr_flag": flagged, "scr_time": np.isfinite(st),
                     "emergency": bool(ru.get("emergency")), "in_field": in_field, "later": in_field and np.isfinite(st),
                     "share": (1 / fl[0][0]) / book if in_field else np.nan, "book": book,
                     "lead_h": (start - open_t) / 3600 if not np.isnan(start) and firsts else np.nan,
                     "n_later": len(later), "ded": min(R32.MAX_CENTS, cents) / 100})
    return rows


def load(bdir: str) -> pd.DataFrame:
    rows = []
    for f in sorted(Path(bdir).glob("betwatch_VIC_G_*.json.gz")):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for r in json.load(fh).get("races", []):
                rows.extend(race_audit(r))
    a = pd.DataFrame(rows)
    a["date"] = pd.to_datetime(a.date, errors="coerce")
    a["_dn"] = gbm_v0.norm_name(a.dog_raw.fillna(""))
    return a.drop(columns="dog_raw")


def mark_topaz(a: pd.DataFrame, t: pd.DataFrame) -> pd.DataFrame:
    """Each Betwatch runner's Topaz status: ran, scratched, or not found that day under that name. A name found in more
    than one Topaz race that day is ambiguous and left unmarked."""
    u = t.drop_duplicates(["date", "_dn"], keep=False)
    a = a.merge(u[["date", "_dn", "race_id", "scratched"]], on=["date", "_dn"], how="left")
    found_day = a.date.isin(t.date.unique())
    a["tz"] = np.where(a.race_id.isna(), np.where(found_day, "not found", "no Topaz day"),
                       np.where(a.scratched.fillna(False).astype(bool), "scratched", "ran"))
    return a


def monthly(a: pd.DataFrame) -> None:
    a = a.assign(month=a.date.dt.to_period("M"))
    races = a.drop_duplicates("bw_race")
    f = a[a.in_field]
    ph = f[~f.later & f.tz.isin(["scratched", "not found"])]
    ph_race = ph.groupby("bw_race").share.sum()
    print("| month | races | runners listed a race | with TAB prices | with a scratching time | flagged scratched, no "
          "time | emergencies a race | emergencies with TAB prices | emergencies with a time | field at the open "
          "| TAB's book there (median) | races with a scratching after the open | deduction there (median) | "
          "phantoms a race | races with a phantom | phantoms' share of the book there (median) | phantoms that are "
          "emergencies | hours from the open to the jump (median) |")
    print("|" + "---|" * 18)
    for m, g in a.groupby("month"):
        rg, fg = races[races.month == m], f[f.month == m]
        pg = ph[ph.month == m]
        nr = rg.bw_race.nunique()
        later_r = rg[rg.n_later > 0]
        sh = ph_race[ph_race.index.isin(pg.bw_race.unique())]
        em = g[g.emergency]
        print(f"| {m} | {nr:,} | {len(g) / nr:.2f} | {g.has_tab.mean():.1%} | {g.scr_time.mean():.1%} | "
              f"{(g.scr_flag & ~g.scr_time).sum():,} | {len(em) / nr:.2f} | "
              f"{em.has_tab.mean() if len(em) else np.nan:.1%} | {em.scr_time.mean() if len(em) else np.nan:.1%} | "
              f"{len(fg) / nr:.2f} | {rg.book.median():.1%} | {len(later_r) / nr:.1%} | "
              f"{later_r.ded.median() if len(later_r) else np.nan:.0%} | {len(pg) / nr:.2f} | "
              f"{pg.bw_race.nunique() / nr:.1%} | {sh.median() if len(sh) else np.nan:.1%} | "
              f"{pg.emergency.mean() if len(pg) else np.nan:.0%} | {rg.lead_h.median():.1f} |")


def topaz_side(a: pd.DataFrame) -> None:
    """How the field at the open matches Topaz, by year: of its runners with no scratching time, how many ran."""
    f = a[a.in_field & ~a.later].assign(year=a.date.dt.year)
    print("\n| year | field-at-open runners with no scratching time | ran in Topaz | scratched in Topaz | not found that "
          "day | no Topaz that day | name in two races that day |\n|---|---|---|---|---|---|---|")
    for y, g in f.groupby("year"):
        c = g.tz.value_counts()
        n = len(g)
        print(f"| {y} | {n:,} | {c.get('ran', 0) / n:.1%} | {c.get('scratched', 0) / n:.1%} | "
              f"{c.get('not found', 0) / n:.1%} | {c.get('no Topaz day', 0) / n:.1%} | {g.tz.isna().mean():.1%} |")


def main(d, label):
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 35, the Betwatch field at TAB's open against who ran\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to audit")
        return 1
    a = load(bdir)
    t = topaz_status(d)
    a = mark_topaz(a, t)
    print(f"Betwatch: {a.bw_race.nunique():,} races, {len(a):,} runners listed, {a.date.min():%Y-%m-%d} to "
          f"{a.date.max():%Y-%m-%d}. Topaz: {len(t):,} runners, {t.scratched.mean():.1%} of them scratched.\n")
    print("A phantom is a runner in round 33's field at the open (TAB prices, no scratching time before the open) that "
          "has no scratching time at all and that Topaz does not have running.\n")
    monthly(a)
    topaz_side(a)
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 35")
