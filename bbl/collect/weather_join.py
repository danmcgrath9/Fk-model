"""Weather at each BBL/WBBL game, from the held NASA POWER hourly files: at the start and through the game.

The local start time (Wikipedia, match_context.parquet) is turned into UTC with the ground's own time zone
(Australian states differ, Queensland has no daylight saving, Chennai is India), then the POWER hours from the
start to three hours after are read: temperature, dew point, humidity, rain and wind at 2 m. The dew signal is
the dew-point depression (temperature minus dew point): the smaller it is late in the game, the likelier dew.
A game without a start time or without weather for its ground gets blanks, never a guess.

Usage: python -m bbl.collect.weather_join <power dir> <venue_coords.csv> <parquet dir>   (writes match_weather.parquet)
"""
import glob
import json
import os
import sys
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

PARAMS = ['T2M', 'T2MDEW', 'RH2M', 'PRECTOTCORR', 'WS2M']
GAME_HOURS = 3


def zone(lat, lon):
    """The ground's time zone from its position (state borders, close enough for every ground BBL has used)."""
    if lat > 0:
        return 'Asia/Kolkata' if 60 < lon < 100 else 'UTC'
    if lon < 129:
        return 'Australia/Perth'
    if lon < 138:
        return 'Australia/Darwin' if lat > -26 else 'Australia/Adelaide'
    if lon < 141 and lat <= -26:
        return 'Australia/Adelaide'
    if lat > -29 and lon >= 138:
        return 'Australia/Brisbane'
    return 'Australia/Hobart' if lat < -39.5 else 'Australia/Sydney'


def load_power(power_dir):
    """{(lat, lon): DataFrame indexed by UTC hour} from every held file."""
    out = {}
    for f in glob.glob(os.path.join(power_dir, '*.json')):
        lat, lon, _ = os.path.basename(f)[:-5].split('_')
        p = json.load(open(f)).get('properties', {}).get('parameter', {})
        if not p:
            continue
        df = pd.DataFrame({k: pd.Series(v) for k, v in p.items() if k in PARAMS})
        df.index = pd.to_datetime(df.index, format='%Y%m%d%H', utc=True)
        df = df.replace(-999.0, np.nan)
        key = (round(float(lat), 4), round(float(lon), 4))
        out[key] = pd.concat([out[key], df]).sort_index() if key in out else df
    return {k: v[~v.index.duplicated()] for k, v in out.items()}


def start_utc(date, local_time, tz):
    if not isinstance(local_time, str) or ':' not in local_time:
        return None
    h, mnt = local_time.strip()[:5].split(':')[:2]
    t = pd.Timestamp(f'{date} {int(h):02d}:{int(mnt[:2]):02d}').tz_localize(ZoneInfo(tz))
    return t.tz_convert('UTC')


def main(power_dir, coords, d):
    m = pd.read_parquet(os.path.join(d, 't20_matches.parquet'), columns=['match_id', 'start_date', 'venue'])
    ctx = pd.read_parquet(os.path.join(d, 'match_context.parquet'))
    c = pd.read_csv(coords).dropna(subset=['lat', 'lon'])
    x = m.merge(ctx[['match_id', 'local_time']], on='match_id').merge(c[['venue', 'lat', 'lon']], on='venue', how='left')
    wx = load_power(power_dir)
    rows = []
    for r in x.itertuples():
        row = dict(match_id=r.match_id)
        if pd.notna(r.lat):
            tz = zone(r.lat, r.lon)
            t0 = start_utc(r.start_date, r.local_time, tz)
            series = wx.get((round(r.lat, 4), round(r.lon, 4)))
            row['tz'] = tz
            if t0 is not None and series is not None:
                t0h = t0.floor('h')
                w = series.loc[t0h: t0h + pd.Timedelta(hours=GAME_HOURS)]
                if len(w):
                    row.update(temp_start=w.T2M.iloc[0], dew_start=w.T2MDEW.iloc[0], rh_start=w.RH2M.iloc[0],
                               temp_end=w.T2M.iloc[-1], dew_end=w.T2MDEW.iloc[-1], rh_end=w.RH2M.iloc[-1],
                               dew_gap_end=w.T2M.iloc[-1] - w.T2MDEW.iloc[-1], rain_mm=w.PRECTOTCORR.sum(),
                               wind_mean=w.WS2M.mean(), start_utc=t0)
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_parquet(os.path.join(d, 'match_weather.parquet'), index=False)
    print(f'match_weather: {len(out)} games, {out.temp_start.notna().sum() if "temp_start" in out else 0} with weather')


if __name__ == '__main__':
    main(*sys.argv[1:])
