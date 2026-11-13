"""Rain and evaporation at a course for the week before a meeting and the forecast to race day (31 Oct 2026, founder:
"Check the weather for Tuesday, I'm pretty sure they'll all be soft"). Open-Meteo forecast API (no key), daily totals in
Melbourne time, past 7 days plus forecast. Reads only: no credits.

    python scripts/track_forecast.py RACEDATE TRACK [TRACK ...] [--fallback]

THE WEATHER NEVER GIVES UP (13 Nov 2026, founder: "Weather should never time out", after Kyneton's read failed four times
on SSL handshake timeouts from GitHub's runner and the meeting was priced with "Rain Nonemm"). Three sources, tried in
order until one answers, each with its own retries:
  1. api.open-meteo.com forecast (past 7 days + forecast; the normal source)
  2. historical-forecast-api.open-meteo.com for the past days + api.met.no locationforecast for the days ahead
     (two different hosts, so one host's outage cannot take the reading down)
The table is the same shape whichever source answered (rain_before() in price_run.py reads it); a column a source does not
have is "-". The heading names the source. --fallback skips source 1 (to test the fallback).
"""
from __future__ import annotations
import datetime as dt, json, sys, time, urllib.request
from zoneinfo import ZoneInfo

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
MEL = ZoneInfo("Australia/Melbourne")
UA = {"User-Agent": "fk-model-weather/1.0 (github.com/danmcgrath9/Fk-model)"}   # api.met.no refuses a request without one


def get(url, tries=5):
    """JSON from url, or raises after tries attempts (backoff 5, 10, 20, 30 s; a 30 s timeout each)."""
    for a in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.load(r)
        except Exception as ex:
            if a == tries - 1:
                raise
            print(f"  (retry {a + 1}: {type(ex).__name__} {str(ex)[:80]})", file=sys.stderr)
            time.sleep((5, 10, 20, 30)[min(a, 3)])


def open_meteo(la, lo, race):
    days = (race - dt.date.today()).days + 1
    d = get(f"https://api.open-meteo.com/v1/forecast?latitude={la}&longitude={lo}&past_days=7&forecast_days={max(days, 1) + 1}"
            "&daily=precipitation_sum,precipitation_probability_max,et0_fao_evapotranspiration,temperature_2m_max"
            "&timezone=Australia%2FMelbourne")["daily"]
    return "Open-Meteo", [(day, d["precipitation_sum"][i], d["precipitation_probability_max"][i],
                           d["et0_fao_evapotranspiration"][i], d["temperature_2m_max"][i]) for i, day in enumerate(d["time"])]


def fallback(la, lo, race):
    """Past days from Open-Meteo's historical-forecast host, the days ahead from MET Norway (hourly, summed by Melbourne day)."""
    today = dt.date.today(); rows = {}
    past = get(f"https://historical-forecast-api.open-meteo.com/v1/forecast?latitude={la}&longitude={lo}"
               f"&start_date={today - dt.timedelta(days=7)}&end_date={today - dt.timedelta(days=1)}"
               "&daily=precipitation_sum,et0_fao_evapotranspiration,temperature_2m_max&timezone=Australia%2FMelbourne")["daily"]
    for i, day in enumerate(past["time"]):
        rows[day] = [past["precipitation_sum"][i], "-", past["et0_fao_evapotranspiration"][i], past["temperature_2m_max"][i]]
    if race >= today:
        ts = get(f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={la:.2f}&lon={lo:.2f}")["properties"]["timeseries"]
        covered = {}   # Melbourne day -> [rain mm, max C]; next_1_hours where it exists, else next_6_hours blocks
        last_end = None
        for t in ts:
            at = dt.datetime.fromisoformat(t["time"].replace("Z", "+00:00"))
            if last_end and at < last_end:
                continue
            dd = t["data"]; amt, hrs = None, 1
            if "next_1_hours" in dd:
                amt = dd["next_1_hours"]["details"].get("precipitation_amount")
            elif "next_6_hours" in dd:
                amt, hrs = dd["next_6_hours"]["details"].get("precipitation_amount"), 6
            day = str(at.astimezone(MEL).date())
            c = covered.setdefault(day, [0.0, None])
            if amt is not None:
                c[0] += amt; last_end = at + dt.timedelta(hours=hrs)
            tmp = dd.get("instant", {}).get("details", {}).get("air_temperature")
            if tmp is not None:
                c[1] = tmp if c[1] is None else max(c[1], tmp)
        for day, (mm, mx) in covered.items():
            if day >= str(today):
                rows[day] = [round(mm, 1), "-", "-", mx if mx is not None else "-"]
    return "Open-Meteo history + MET Norway forecast (fallback)", [(k, *v) for k, v in sorted(rows.items())]


race = dt.date.fromisoformat(sys.argv[1])
fb_only = "--fallback" in sys.argv
for t in (a for a in sys.argv[2:] if not a.startswith("--")):
    la, lo = COORDS[t.lower()]
    src, rows, errs = None, None, []
    for f in ((fallback,) if fb_only else (open_meteo, fallback)):
        try:
            src, rows = f(la, lo, race); break
        except Exception as ex:
            errs.append(f"{f.__name__}: {type(ex).__name__} {str(ex)[:120]}")
    if not rows:
        print(f"## {t}: FAILED every source ({'; '.join(errs)})"); continue
    print(f"\n## {t} ({la}, {lo}), race day {race}" + (f" [{src}]" if src != "Open-Meteo" else ""))
    print("| day | rain mm | chance | evaporation mm | max C |\n|---|---|---|---|---|")
    for day, rain, ch, et0, mx in rows:
        if day > race.isoformat(): break
        mark = " (forecast)" if day >= dt.date.today().isoformat() else ""
        print(f"| {day}{mark} | {rain} | {ch if ch == '-' else f'{ch}%'} | {et0} | {mx} |")
