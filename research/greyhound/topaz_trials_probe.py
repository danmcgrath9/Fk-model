"""Where are the trials? (6 Nov 2026, founder: "First starters for dogs has trial form though and times ... Do we not have
those already?")

    python research/greyhound/topaz_trials_probe.py DIR LABEL    (TOPAZ_API_KEY; ISOLYNX_DIR when the pull is restored)

Counts only, never a dog, a name or a time:
  1. GRV's /trialresult feed (Test 13: 14,238 trial runs in 13 years) on the last 14 days, a call a day: trials a day,
     tracks, and how many of the dogs that debuted in those days had a trial in the feed beforehand (back 120 days)
  2. /dog/{id}/form for up to 25 of those debutants: rows by race type, so we know whether the form lists trials the
     feed leaves out
  3. Isolynx: tracked runs whose race is not in the bulk runs (a trial or a non-TAB race), and the words of their race
     names that say so
"""
import collections
import gzip
import json
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from greyhound.topaz import TopazClient, TopazError  # noqa: E402


def bulk_runs(d: Path, months: int = 60) -> pd.DataFrame:
    rows = []
    for f in sorted(Path(d).glob("runs_VIC_*.json.gz"))[-months:]:
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for r in json.load(fh):
                rows.append({"race": r.get("raceId"), "dog": r.get("dogId"), "date": str(r.get("meetingDate"))[:10],
                             "scratched": r.get("scratched")})
    t = pd.DataFrame(rows)
    t["date"] = pd.to_datetime(t.date, errors="coerce")
    return t[t.scratched != True]  # noqa: E712


def main(d, label):
    print(f"# {label}: where are the trials\n")
    runs = bulk_runs(Path(d))
    first = runs.sort_values("date").groupby("dog").date.min()
    end = runs.date.max()
    days = pd.date_range(end - pd.Timedelta(days=13), end)
    debut = first[first >= days[0]]
    print(f"Bulk runs to {end:%Y-%m-%d}; {len(debut):,} dogs debuted in the last 14 days\n")
    client = TopazClient(max_per_minute=60)

    # 1. the trial feed
    per_day, tracks, dogs_trialled = [], collections.Counter(), set()
    look = pd.date_range(days[0] - pd.Timedelta(days=120), end)
    for i, day in enumerate(look):
        try:
            rows = client.trial_results(day.year, day.month, day.day)
        except TopazError as e:
            print(f"trial feed refused on {day:%Y-%m-%d}: {str(e)[:120]}")
            rows = []
        vic = [r for r in rows if str(r.get("owningAuthorityCode", "VIC")).upper() == "VIC"]
        if day >= days[0]:
            per_day.append((f"{day:%Y-%m-%d}", len(rows), len(vic)))
            tracks.update(str(r.get("trackCode")) for r in vic)
        dogs_trialled.update(r.get("dogId") for r in vic)
    print("| day | trials in the feed | of them VIC |\n|---|---|---|")
    for day, n, v in per_day:
        print(f"| {day} | {n:,} | {v:,} |")
    had = sum(1 for dog in debut.index if dog in dogs_trialled)
    print(f"\nVIC trials in the last 14 days by track: {', '.join(f'{t} {n}' for t, n in tracks.most_common())}")
    print(f"Debutants of the last 14 days with a trial in the feed in the 120 days before: {had:,} of {len(debut):,}\n")

    # 2. the dog's form
    kinds, with_trial, asked = collections.Counter(), 0, 0
    for dog in list(debut.index)[:25]:
        try:
            form = client._get(f"dog/{int(dog)}/form") or []
        except TopazError as e:
            print(f"/dog/{{id}}/form refused: {str(e)[:120]}")
            break
        asked += 1
        rows = form if isinstance(form, list) else form.get("form", []) if isinstance(form, dict) else []
        k = collections.Counter(str(r.get("raceType") or r.get("raceTypeCode") or "?") for r in rows if isinstance(r, dict))
        kinds.update(k)
        with_trial += any("trial" in t.lower() for t in k)
    print(f"/dog/{{id}}/form for {asked} debutants: rows by race type {dict(kinds.most_common(12))}; "
          f"{with_trial} of {asked} list a trial\n")

    # 3. Isolynx
    iso = os.environ.get("ISOLYNX_DIR", "")
    if iso and os.path.isdir(iso):
        races = set(runs.race.dropna().astype("int64"))
        allrace = set()
        for f in sorted(Path(d).glob("runs_VIC_*.json.gz")):
            with gzip.open(f, "rt", encoding="utf-8") as fh:
                allrace.update(r.get("raceId") for r in json.load(fh))
        n = unmatched = 0
        words = collections.Counter()
        for f in sorted(Path(iso).glob("isolynx_dogs_*.json.gz")):
            with gzip.open(f, "rt", encoding="utf-8") as fh:
                for g in json.load(fh):
                    for r in g.get("runs") or []:
                        n += 1
                        if r.get("raceId") not in allrace:
                            unmatched += 1
                            words.update(w.upper() for w in str(r.get("raceName") or "").split() if w.isalpha())
        print(f"Isolynx: {n:,} tracked runs, {unmatched:,} in a race the bulk runs do not hold "
              f"({len(races):,} races in the last 60 months of bulk runs)")
        print(f"Commonest words in those races' names: {', '.join(f'{w} {c}' for w, c in words.most_common(15))}")
    else:
        print("Isolynx: no ISOLYNX_DIR")
    print(f"\n{client.calls} calls")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "trials probe")
