"""Rain and evaporation at a course for the week before a meeting and the forecast to race day (31 Oct 2026, founder:
"Check the weather for Tuesday, I'm pretty sure they'll all be soft"). Open-Meteo forecast API (no key), daily totals in
Melbourne time, past 7 days plus forecast. Reads only: no credits.

    python scripts/track_forecast.py RACEDATE TRACK [TRACK ...]
"""
from __future__ import annotations
import datetime as dt, json, sys, time, urllib.request

COORDS = {"echuca": (-36.13, 144.75), "mildura": (-34.21, 142.13), "wangaratta": (-36.36, 146.31),
          "ballarat": (-37.56, 143.85), "flemington": (-37.7895, 144.9120), "mansfield": (-37.05, 146.08),
          "mornington": (-38.23, 145.06), "kyneton": (-37.25, 144.46),
          "cranbourne": (-38.10, 145.28), "warrnambool": (-38.37, 142.50), "benalla": (-36.55, 145.98), "sale": (-38.11, 147.07),
          "geelong": (-38.17, 144.35), "bendigo": (-36.73, 144.27), "pakenham": (-38.08, 145.49), "caulfield": (-37.88, 145.04),
          "moonee valley": (-37.77, 144.93), "sandown": (-37.95, 145.16), "seymour": (-37.03, 145.14), "swan hill": (-35.34, 143.55),
          "hamilton": (-37.74, 142.02), "ararat": (-37.28, 142.93), "stawell": (-37.06, 142.78), "donald": (-36.37, 142.98),
          "yarra valley": (-37.66, 145.53), "kilmore": (-37.30, 144.95), "wodonga": (-36.12, 146.88), "horsham": (-36.71, 142.20),
          "moe": (-38.17, 146.27), "traralgon": (-38.19, 146.54), "bairnsdale": (-37.83, 147.61), "colac": (-38.34, 143.59),
          "terang": (-38.24, 142.92), "camperdown": (-38.23, 143.15), "penshurst": (-37.87, 142.29), "casterton": (-37.59, 141.40),
          "edenhope": (-37.04, 141.30), "st arnaud": (-36.62, 143.26), "wycheproof": (-36.08, 143.23), "mortlake": (-38.08, 142.80),
          "healesville": (-37.65, 145.52), "avoca": (-37.09, 143.47), "murtoa": (-36.62, 142.47), "nhill": (-36.33, 141.65),
          "werribee": (-37.90, 144.66), "tatura": (-36.44, 145.23), "wangaratta": (-36.36, 146.31),
          "dunkeld": (-37.65, 142.34), "yea": (-37.21, 145.43)}
race = dt.date.fromisoformat(sys.argv[1])
for t in sys.argv[2:]:
    la, lo = COORDS[t.lower()]
    days = (race - dt.date.today()).days + 1
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={la}&longitude={lo}&past_days=7&forecast_days={max(days, 1) + 1}"
           "&daily=precipitation_sum,precipitation_probability_max,et0_fao_evapotranspiration,temperature_2m_max"
           "&timezone=Australia%2FMelbourne")
    for a in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                d = json.load(r)["daily"]; break
        except Exception as ex:
            if a == 3: print(f"## {t}: FAILED {ex}"); d = None
            time.sleep(5 * (a + 1))
    if not d: continue
    print(f"\n## {t} ({la}, {lo}), race day {race}")
    print("| day | rain mm | chance | evaporation mm | max C |\n|---|---|---|---|---|")
    for i, day in enumerate(d["time"]):
        if day > race.isoformat(): break
        mark = " (forecast)" if day >= dt.date.today().isoformat() else ""
        print(f"| {day}{mark} | {d['precipitation_sum'][i]} | {d['precipitation_probability_max'][i]}% | "
              f"{d['et0_fao_evapotranspiration'][i]} | {d['temperature_2m_max'][i]} |")
