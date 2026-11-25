"""How well was race-day rain forecast, 1 to 5 days ahead? (25 Nov 2026, founder: "test rain on race day. I suspect it's
the worst and most predictable of the lot"). Open-Meteo's Previous Runs API keeps what each forecast said N days before
the hour it was for, so the forecast we would have read on the Wednesday for a Saturday can be compared with what fell.
No credits, no Form King calls: reads the 28 Oct track_weather.py output on the experiments branch (each Victorian
meeting's official ratings and ERA5 rain) and the course coordinates it printed.

    python scripts/t_rain_forecast.py [EXPERIMENT_FILE]

Prints a CSV: per meeting from 2024 on, the forecast rain on race day and each of the three days before at leads of
1 to 5 days (hourly precipitation_previous_dayN summed by Melbourne day), beside the meeting's ERA5 rain and ratings.
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import io
import json
import re
import subprocess
import sys
import time
import urllib.request

SRC = sys.argv[1] if len(sys.argv) > 1 else "2026-10-28T0011Z-track_weather-40603886237.md"
LEADS = (1, 2, 3, 4, 5)
UA = {"User-Agent": "fk-model-weather/1.0 (github.com/danmcgrath9/Fk-model)"}


def get(url, tries=5):
    for a in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.load(r)
        except Exception as ex:
            if a == tries - 1:
                raise
            print(f"  (retry {a + 1}: {type(ex).__name__} {str(ex)[:100]})", file=sys.stderr)
            time.sleep((5, 15, 30, 60)[min(a, 3)])


subprocess.run(["git", "fetch", "-q", "--depth", "1", "origin", "experiments"], check=True)
text = subprocess.run(["git", "show", f"FETCH_HEAD:{SRC}"], capture_output=True, text=True, check=True).stdout
coords = {m.group(1): (float(m.group(2)), float(m.group(3)))
          for m in re.finditer(r"^weather (.+?): (-?[\d.]+),(-?[\d.]+),", text, re.M)}
a, b = text.find("CSV-BEGIN") + 9, text.find("CSV-END")
rows = [r for r in csv.DictReader(io.StringIO(text[a:b].strip())) if r["date"] >= "2024-01-10" and "synth" not in r["track"]]
print(f"meetings from 2024: {len(rows)}; tracks with coordinates: {len(coords)}", file=sys.stderr)

by_track = collections.defaultdict(list)
for r in rows:
    by_track[r["track"]].append(r)

out = io.StringIO()
cols = ["date", "track", "races", "first", "last", "wettest", "era5_d3", "era5_d2", "era5_d1", "era5_day", "om_day"]
for off in (3, 2, 1, 0):
    cols += [f"fc_{'day' if off == 0 else 'd' + str(off)}_lead{n}" for n in LEADS]
w = csv.writer(out)
w.writerow(cols)
missing = []
for track, rs in sorted(by_track.items()):
    if track not in coords:
        missing.append(track)
        continue
    la, lo = coords[track]
    dates = sorted({dt.date.fromisoformat(r["date"]) for r in rs})
    # one request per calendar year of this track's meetings (keeps each call's weight modest)
    daily = collections.defaultdict(lambda: collections.defaultdict(float))   # day -> var -> mm
    seen = collections.defaultdict(lambda: collections.defaultdict(int))
    for yr in sorted({d.year for d in dates}):
        ds = [d for d in dates if d.year == yr]
        start, end = min(ds) - dt.timedelta(days=4), max(ds)
        vars_ = ["precipitation"] + [f"precipitation_previous_day{n}" for n in LEADS]
        try:
            h = get("https://previous-runs-api.open-meteo.com/v1/forecast?"
                    f"latitude={la}&longitude={lo}&hourly={','.join(vars_)}"
                    f"&start_date={start}&end_date={end}&timezone=Australia%2FMelbourne")["hourly"]
        except Exception as ex:
            print(f"{track} {yr}: FAILED {ex}", file=sys.stderr)
            continue
        for i, t in enumerate(h["time"]):
            day = t[:10]
            for v in vars_:
                x = h[v][i]
                if x is not None:
                    daily[day][v] += x
                    seen[day][v] += 1
        time.sleep(1)
    val = lambda day, v: round(daily[day][v], 1) if seen[day][v] >= 20 else ""   # a day needs most of its hours
    for r in rs:
        d = dt.date.fromisoformat(r["date"])
        row = [r["date"], track, r["races"], r["first"], r["last"], r["wettest"],
               r["rain_d3"], r["rain_d2"], r["rain_d1"], r["rain_day"], val(str(d), "precipitation")]
        for off in (3, 2, 1, 0):
            day = str(d - dt.timedelta(days=off))
            row += [val(day, f"precipitation_previous_day{n}") for n in LEADS]
        w.writerow(row)
    print(f"{track}: {len(rs)} meetings", file=sys.stderr)

print(f"no coordinates: {', '.join(missing) or 'none'}")
print("CSV-BEGIN")
print(out.getvalue().strip())
print("CSV-END")
