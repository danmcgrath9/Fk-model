"""Melbourne metro track ratings against the rain before them (28 Oct 2026, founder: "how much rain in the 3 days leading
up to it and how much its been watered and how the track ended up, then I can send you the forecast for Flemington for
Saturday and you can guess the rating off its history"). DB only plus Open-Meteo's free historical weather; no credits.

Sources:
- How the track ended up: every stored past run (entries' raw pastEvents) gives each race's official going ("Good 4",
  "Soft 6"...) by date and track, years back. Per meeting: the first race's rating, the last race's, and the wettest.
- Watering and Form King's own rain figures: fk.meetings raw (irrigation / rainfall "Xmm last 24 hours, Ymm last 7 days",
  penetrometer, rail, the rating at the time it was pulled), only for the meetings we have stored (Jul 2025 on).
- Rain by day: Open-Meteo archive (ERA5 reanalysis, daily precipitation_sum and FAO evapotranspiration at the track),
  race day and each of the three days before. Reanalysis rain is a grid estimate, not the course gauge.

    python scripts/track_weather.py [VIC|ALL|TRACK ...]   (default VIC: every Victorian track in the past runs)
Tracks without a fixed course location are found with Open-Meteo's geocoder (the town, filtered to the state), and the
coordinates used are printed so a wrong match can be seen.
"""
from __future__ import annotations

import collections
import datetime as dt
import json
import os
import re
import statistics
import sys
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

import psycopg

COORDS = {  # course centres
    "flemington": (-37.7895, 144.9120), "caulfield": (-37.8810, 145.0390),
    "moonee valley": (-37.7660, 144.9300), "sandown": (-37.9480, 145.1700),
}
ARGS = sys.argv[1:] or ["VIC"]
STATE = ARGS[0].upper() if ARGS[0].upper() in ("VIC", "NSW", "QLD", "SA", "WA", "TAS", "ACT", "NT", "ALL") else None
TRACKS: list[str] = [] if STATE else [t.lower() for t in ARGS]
STATE_NAME = {"VIC": "Victoria", "NSW": "New South Wales", "QLD": "Queensland", "SA": "South Australia",
              "WA": "Western Australia", "TAS": "Tasmania", "ACT": "Australian Capital Territory", "NT": "Northern Territory"}
MEL = ZoneInfo("Australia/Melbourne")


def day(d) -> str:
    if d is None:
        return ""
    if re.fullmatch(r"\d+(\.\d+)?", str(d)):
        v = float(d); v = v / 1000 if v > 1e11 else v
        return dt.datetime.fromtimestamp(v, MEL).date().isoformat()
    return str(d)[:10]


def going_num(g: str | None) -> int | None:
    """'Good 4' -> 4, 'Soft 5' -> 5, 'Heavy 10' -> 10; 'Dead' alone -> 4, 'Slow' alone -> 6 (pre-2014 words)."""
    if not g:
        return None
    m = re.search(r"(\d+)", g)
    if m:
        return int(m.group(1))
    w = g.strip().lower()
    return {"firm": 2, "fast": 2, "good": 3, "dead": 4, "slow": 6, "soft": 6, "heavy": 8}.get(w)


def which_track(name: str | None) -> str | None:
    n = (name or "").lower().strip()
    if STATE:
        return n or None
    return next((t for t in TRACKS if t in n), None)


def geocode(track: str, state: str | None) -> tuple[float, float] | None:
    name = re.sub(r"\b(synthetic|poly|hillside|lakeside|racecourse|turf club|park)\b", "", track, flags=re.I).strip() or track
    url = "https://geocoding-api.open-meteo.com/v1/search?count=10&country=AU&name=" + urllib.parse.quote(name)
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            res = json.load(r).get("results") or []
    except Exception:
        return None
    want = STATE_NAME.get(state or "", "")
    res = [x for x in res if not want or x.get("admin1") == want] or ([] if want else res)
    return (res[0]["latitude"], res[0]["longitude"]) if res else None


def mm(text: str | None, which: str) -> float | None:
    """'52mm last 24 hours, 58.6mm last 7 days' -> 52.0 (which='24') or 58.6 (which='7'); 'nil' -> 0."""
    if text is None:
        return None
    for part in str(text).split(","):
        if (which == "24" and "24" in part) or (which == "7" and "7 day" in part):
            if "nil" in part.lower():
                return 0.0
            m = re.search(r"([\d.]+)\s*mm", part)
            return float(m.group(1)) if m else None
    return None


q_runs = """select distinct p->>'raceId', p->>'date', coalesce(p->'track'->>'name', p->>'track'), p->>'going',
                   p->>'raceNumber', p->>'startTime', coalesce((p->>'trial')::boolean, false), p->>'state'
            from fk.entries e, jsonb_array_elements(coalesce(e.raw->'pastEvents', '[]'::jsonb)) p"""
q_meet = "select meeting_date, track, raw from fk.meetings"
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    runs = c.execute(q_runs).fetchall()
    meets = c.execute(q_meet).fetchall()

# meetings from past runs: date, track -> {race key: going}
M: dict[tuple[str, str], dict[str, tuple]] = collections.defaultdict(dict)
have_rn = have_st = 0
TSTATE: dict[str, str] = {}
for rid, d, trk, g, rn, st, trial, stt in runs:
    t = which_track(trk)
    if not t or trial or not g:
        continue
    if STATE and STATE != "ALL" and (stt or "").upper() != STATE:
        continue
    TSTATE[t] = (stt or "").upper()
    have_rn += rn is not None; have_st += st is not None
    order = float(rn) if rn and re.fullmatch(r"\d+", str(rn)) else (float(st) if st and re.fullmatch(r"\d+(\.\d+)?", str(st)) else None)
    M[(day(d), t)][rid] = (order, g)
print(f"past-run races kept: {sum(len(v) for v in M.values())}; with raceNumber {have_rn}, with startTime {have_st}")

# stored meetings (watering etc.)
FK = {}
for md, trk, raw in meets:
    t = which_track(trk)
    if not t or not raw:
        continue
    FK[(str(md), t)] = {"fk_going": raw.get("going"), "fk_going_n": raw.get("goingNumber"),
                        "irr24": mm(raw.get("irrigation"), "24"), "irr7": mm(raw.get("irrigation"), "7"),
                        "rain24": mm(raw.get("rainfall"), "24"), "rain7": mm(raw.get("rainfall"), "7"),
                        "pen": raw.get("penetrometer"), "rail": raw.get("railPosition")}

dates = sorted(d for d, _ in M if d)
if not dates:
    print("no meetings found"); sys.exit(0)
lo = (dt.date.fromisoformat(dates[0]) - dt.timedelta(days=4)).isoformat()
hi = min(dates[-1], (dt.date.today() - dt.timedelta(days=6)).isoformat())
W: dict[str, dict[str, tuple]] = {}
if STATE:
    TRACKS = sorted({t for _, t in M})
for t in TRACKS:
    if t in COORDS:
        la, lo_ = COORDS[t]
    else:
        g = geocode(t, TSTATE.get(t))
        if not g:
            print(f"weather {t}: no location found"); W[t] = {}; continue
        la, lo_ = g; COORDS[t] = g
    url = (f"https://archive-api.open-meteo.com/v1/archive?latitude={la}&longitude={lo_}&start_date={lo}&end_date={hi}"
           "&daily=precipitation_sum,et0_fao_evapotranspiration,temperature_2m_max&timezone=Australia%2FMelbourne")
    try:
        with urllib.request.urlopen(url, timeout=120) as r:
            d = json.load(r)["daily"]
        W[t] = {k: (p, e, tx) for k, p, e, tx in zip(d["time"], d["precipitation_sum"], d["et0_fao_evapotranspiration"], d["temperature_2m_max"])}
        print(f"weather {t}: {la:.3f},{lo_:.3f}, {len(W[t])} days")
    except Exception as ex:  # a weather failure leaves the ratings and watering table intact
        print(f"weather {t}: FAILED {ex}"); W[t] = {}

rows = []
for (d, t), races in sorted(M.items()):
    if not d:
        continue
    gs = [g for _, g in sorted(races.values(), key=lambda x: (x[0] is None, x[0] or 0))]
    nums = [going_num(g) for g in gs if going_num(g) is not None]
    if not nums:
        continue
    ordered = all(o is not None for o, _ in races.values())
    w = W.get(t, {})
    dd = dt.date.fromisoformat(d)
    rain = [w.get((dd - dt.timedelta(days=k)).isoformat(), (None, None, None))[0] for k in range(4)]   # race day, -1, -2, -3
    et0 = [w.get((dd - dt.timedelta(days=k)).isoformat(), (None, None, None))[1] for k in range(1, 4)]
    tmax = w.get(d, (None, None, None))[2]
    f = FK.get((d, t), {})
    rows.append({"date": d, "track": t, "races": len(nums), "first": nums[0] if ordered else None,
                 "last": nums[-1] if ordered else None, "wettest": max(nums), "mode": collections.Counter(nums).most_common(1)[0][0],
                 "first_txt": gs[0] if ordered else "", "last_txt": gs[-1] if ordered else "",
                 "rain_day": rain[0], "rain_d1": rain[1], "rain_d2": rain[2], "rain_d3": rain[3],
                 "rain_3d": None if None in rain[1:] else round(sum(rain[1:]), 1),
                 "et0_3d": None if None in et0 else round(sum(et0), 1), "tmax": tmax, **f})

cols = ["date", "track", "races", "first_txt", "last_txt", "first", "last", "wettest", "mode", "rain_d3", "rain_d2", "rain_d1",
        "rain_day", "rain_3d", "et0_3d", "tmax", "fk_going", "irr24", "irr7", "rain24", "rain7", "pen", "rail"]
print("\nCSV-BEGIN")
print(",".join(cols))
for r in rows:
    print(",".join("" if r.get(k) is None else str(r.get(k)).replace(",", ";") for k in cols))
print("CSV-END\n")

# summary per track: the first race's rating by the rain over the three days before plus race day
def band(x):
    return "<2" if x < 2 else "2-10" if x < 10 else "10-20" if x < 20 else "20+"
print("| track | meetings | under 2mm: usual start | 2-10mm | 10-20mm | 20mm+ | upgraded / downgraded in the day |\n|---|---|---|---|---|---|---|")
for t in TRACKS:
    rs = [r for r in rows if r["track"] == t and r["rain_3d"] is not None and r["rain_day"] is not None and r["first"] is not None]
    if len(rs) < 5:
        continue
    cell = []
    for b in ("<2", "2-10", "10-20", "20+"):
        g = [r["first"] for r in rs if band(r["rain_3d"] + r["rain_day"]) == b]
        cell.append(f"{statistics.median(g):g} (n={len(g)}, {min(g)}-{max(g)})" if g else "-")
    up = sum(r["last"] < r["first"] for r in rs); dn = sum(r["last"] > r["first"] for r in rs)
    print(f"| {t} | {len(rs)} | " + " | ".join(cell) + f" | {up} / {dn} |")
