"""Weather at every NRL game since 2009 from Open-Meteo's historical archive (once, cached).

Founder approved weather on 21 Oct 2026. Open-Meteo's free API is for non-commercial use under CC BY 4.0
(credit: "Weather data by Open-Meteo.com"); this is private research. BOM is not used: its terms forbid
scraping. Each town is geocoded once (Open-Meteo's own geocoder), then a town's games are fetched in
windows of up to 13 days (a request over two weeks counts as more than one call), one request every
PAUSE seconds, well inside the free limit of 10,000 calls a day.

Per game (all times UTC, hours from the archive's hourly series):
  rain_pre3   mm in the 3 hours before kick-off      rain_game   mm in the 2 hours from kick-off
  rain_24     mm in the 24 hours before kick-off     temp, humidity, dew_point at kick-off
  wind, gusts mean km/h over the 2 hours from kick-off
Roofed grounds keep their rows but are flagged (roof) and should be read as dry and still.

Writes nrl/cache/weather/weather.parquet, towns.csv (the coordinates used) and raw.jsonl.gz.
Usage: python nrl/weather/pull.py nrl/weather/games.csv
"""
import gzip
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import requests

PAUSE = float(os.environ.get('PAUSE', '1'))
OUT = 'nrl/cache/weather'
GEO = 'https://geocoding-api.open-meteo.com/v1/search'
# SOURCE=forecast reads Open-Meteo's archive of past FORECASTS (short-range, stitched from each model run; about
# 2022 on) instead of what happened: the test of whether weather still helps when only a forecast is known
# Tested 21 Oct 2026: SOURCE=forecast returned rain IDENTICAL to the archive (correlation 1.00), so it is not
# a forecast test. SOURCE=previous reads the Previous Runs archive: the forecast as it stood LEAD days earlier.
SOURCE = os.environ.get('SOURCE', 'actual')
LEAD = int(os.environ.get('LEAD_DAYS', '1'))
ARCHIVE = {'forecast': 'https://historical-forecast-api.open-meteo.com/v1/forecast',
           'previous': 'https://previous-runs-api.open-meteo.com/v1/forecast'}.get(
    SOURCE, 'https://archive-api.open-meteo.com/v1/archive')
FIRST = os.environ.get('FIRST_DATE', '')
HOURLY = 'temperature_2m,relative_humidity_2m,dew_point_2m,precipitation,wind_speed_10m,wind_gusts_10m'
CC = {'Australia': 'AU', 'New Zealand': 'NZ', 'United States of America': 'US'}
# the geocoder's first pick was wrong for these (Mudgeeraba QLD; Redcliffe WA): coordinates set by hand
OVERRIDE = {('Mudgee', 'Australia'): (-32.5943, 149.5871, 'Mudgee', 'New South Wales'),
            ('Redcliffe', 'Australia'): (-27.2307, 153.1029, 'Redcliffe', 'Queensland')}
ONLY = [t for t in os.environ.get('ONLY_TOWNS', '').split(',') if t]   # refetch just these towns

s = requests.Session()
s.headers['User-Agent'] = 'fk-model NRL research'


def get(url, params):
    for attempt in range(4):
        try:
            r = s.get(url, params=params, timeout=60)
            time.sleep(PAUSE)
            if r.status_code == 200:
                return r.json()
            print(f'  HTTP {r.status_code}: {r.text[:200]}')
            if r.status_code == 429:
                time.sleep(60)
        except requests.RequestException as e:
            print(f'  {e}')
        time.sleep(PAUSE * 2 ** attempt)
    return None


def geocode(town, country):
    if (town, country) in OVERRIDE:
        lat, lon, name, admin = OVERRIDE[(town, country)]
        return dict(town=town, country=country, lat=lat, lon=lon, found=name, admin=admin, population=None)
    res = (get(GEO, {'name': town, 'count': 10, 'language': 'en', 'format': 'json'}) or {}).get('results', [])
    res = [r for r in res if r.get('country_code') == CC.get(country)]
    if not res:
        return None
    best = max(res, key=lambda r: (r.get('feature_code', '').startswith('PPL'), r.get('population') or 0))
    return dict(town=town, country=country, lat=best['latitude'], lon=best['longitude'], found=best.get('name'),
                admin=best.get('admin1'), population=best.get('population'))


def summarise(hours, ko):
    h = hours
    pre3 = h[(h.t >= ko - pd.Timedelta(hours=3)) & (h.t < ko)]
    pre24 = h[(h.t >= ko - pd.Timedelta(hours=24)) & (h.t < ko)]
    game = h[(h.t >= ko) & (h.t < ko + pd.Timedelta(hours=2))]
    at = h.iloc[(h.t - ko).abs().argsort()[:1]]
    return dict(rain_pre3=pre3.precipitation.sum(), rain_24=pre24.precipitation.sum(),
                rain_game=game.precipitation.sum(), temp=at.temperature_2m.iloc[0],
                humidity=at.relative_humidity_2m.iloc[0], dew_point=at.dew_point_2m.iloc[0],
                wind=game.wind_speed_10m.mean(), gusts=game.wind_gusts_10m.mean())


def main(games_csv):
    os.makedirs(OUT, exist_ok=True)
    g = pd.read_csv(games_csv)
    g['ko'] = pd.to_datetime(g.kick_off_utc, utc=True)
    if ONLY:
        g = g[g.town.isin(ONLY)]
    if FIRST:
        g = g[g.ko >= pd.Timestamp(FIRST, tz='UTC')]
    towns = []
    for (t, c), _ in g.groupby(['town', 'country']):
        x = geocode(t, c)
        if x is None:
            sys.exit(f'could not geocode {t}, {c}')
        towns.append(x)
    towns = pd.DataFrame(towns)
    if os.path.exists(f'{OUT}/towns.csv') and (ONLY or SOURCE != 'actual'):
        old = pd.read_csv(f'{OUT}/towns.csv')
        towns = pd.concat([old[~old.town.isin(towns.town)], towns], ignore_index=True)
    towns.to_csv(f'{OUT}/towns.csv', index=False)
    print(towns.to_string())
    where = {(r.town, r.country): (r.lat, r.lon) for r in towns.itertuples()}
    rows, calls = [], 0
    stem = {'actual': '', 'forecast': '_forecast'}.get(SOURCE, f'_previous_day{LEAD}')
    with gzip.open(f'{OUT}/raw{stem}.jsonl.gz', 'wt') as raw:
        for (t, c), grp in g.sort_values('ko').groupby(['town', 'country']):
            lat, lon = where[(t, c)]
            grp = grp.sort_values('ko')
            i = 0
            while i < len(grp):
                start = grp.ko.iloc[i] - pd.Timedelta(days=1)
                j = i
                while j + 1 < len(grp) and (grp.ko.iloc[j + 1] - start).days <= 12:
                    j += 1
                end = grp.ko.iloc[j] + pd.Timedelta(hours=3)
                hourly = HOURLY if SOURCE != 'previous' else ','.join(f'{v}_previous_day{LEAD}' for v in HOURLY.split(','))
                body = get(ARCHIVE, {'latitude': lat, 'longitude': lon, 'start_date': start.strftime('%Y-%m-%d'),
                                     'end_date': end.strftime('%Y-%m-%d'), 'hourly': hourly, 'timezone': 'GMT'})
                if body and SOURCE == 'previous' and 'hourly' in body:
                    body['hourly'] = {k.replace(f'_previous_day{LEAD}', ''): v for k, v in body['hourly'].items()}
                calls += 1
                raw.write(json.dumps({'town': t, 'country': c, 'start': str(start), 'end': str(end), 'body': body}) + '\n')
                if body and 'hourly' in body:
                    h = pd.DataFrame(body['hourly'])
                    h['t'] = pd.to_datetime(h.time, utc=True)
                    for r in grp.iloc[i:j + 1].itertuples():
                        rows.append(dict(match_id=r.match_id, roof=r.roof, **summarise(h, r.ko)))
                i = j + 1
    w = pd.DataFrame(rows)
    if ONLY and SOURCE == 'actual' and os.path.exists(f'{OUT}/weather.parquet'):
        old = pd.read_parquet(f'{OUT}/weather.parquet')
        w = pd.concat([old[~old.match_id.isin(w.match_id)], w], ignore_index=True)
    w.to_parquet(f'{OUT}/weather{stem}.parquet', index=False)
    print(f'{len(w):,} of {len(g):,} games with weather, {calls:,} archive requests; '
          f'rain in the game window in {(w.rain_game > 0.5).mean():.0%} of games (over 0.5 mm)')


if __name__ == '__main__':
    main(sys.argv[1])
