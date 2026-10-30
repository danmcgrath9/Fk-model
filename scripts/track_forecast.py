"""Rain and evaporation at a course for the week before a meeting and the forecast to race day (31 Oct 2026, founder:
"Check the weather for Tuesday, I'm pretty sure they'll all be soft"). Open-Meteo forecast API (no key), daily totals in
Melbourne time, past 7 days plus forecast. Reads only: no credits.

    python scripts/track_forecast.py RACEDATE TRACK [TRACK ...]
"""
from __future__ import annotations
import datetime as dt, json, sys, time, urllib.request

COORDS = {"echuca": (-36.13, 144.75), "mildura": (-34.21, 142.13), "wangaratta": (-36.36, 146.31),
          "ballarat": (-37.56, 143.85), "flemington": (-37.7895, 144.9120), "mansfield": (-37.05, 146.08),
          "mornington": (-38.23, 145.06)}
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
