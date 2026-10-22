"""NASA POWER hourly weather at every BBL/WBBL ground, for the summers it was used.

NASA POWER: no restrictions on use (credit "NASA Langley Research Center POWER Project"). Hourly
temperature, dew point, humidity, rain and wind at 2 m, in UTC, one request per ground per summer
(October to February), one at a time. Raw JSON only; nothing is re-asked once held.

Resumable: a ground-summer already in <out dir> is skipped, and the run stops after BUDGET_MIN minutes so
what it has can be uploaded; the next run carries on.

Usage: python -m bbl.collect.power <out dir> <venue_coords.csv> <t20_matches.parquet> [fixtures.csv]
"""
import json
import os
import sys
import time

import pandas as pd
import requests

API = 'https://power.larc.nasa.gov/api/temporal/hourly/point'
PARAMS = 'T2M,T2MDEW,RH2M,PRECTOTCORR,WS2M'
UA = 'fk-model-bbl/0.1 (github.com/danmcgrath9/Fk-model; research)'
PAUSE = 1.0
BUDGET_MIN = float(os.environ.get('POWER_BUDGET_MIN', '200'))


def main(out, coords, matches, fixtures=None):
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    c = pd.read_csv(coords).dropna(subset=['lat', 'lon'])
    m = pd.read_parquet(matches)
    m = m[m.competition.isin(['Big Bash League', "Women's Big Bash League"])][['venue', 'start_date']]
    if fixtures:   # fixtures Cricsheet does not hold yet (the coming season) by their Wikipedia venue name
        f = pd.read_csv(fixtures)
        m = pd.concat([m, f[['venue_full', 'date']].rename(columns={'venue_full': 'venue', 'date': 'start_date'}).dropna()])
    m = m.merge(c[['venue', 'lat', 'lon']], on='venue')
    m['summer'] = pd.to_datetime(m.start_date).map(lambda d: d.year if d.month >= 7 else d.year - 1)
    need = m.groupby(['lat', 'lon']).summer.unique()
    # the coming season too: every ground used in the last three summers
    recent = m[m.summer >= m.summer.max() - 2].groupby(['lat', 'lon']).size().index
    jobs = sorted({(lat, lon, int(s)) for (lat, lon), ss in need.items() for s in ss} |
                  {(lat, lon, int(m.summer.max()) + 1) for lat, lon in recent})
    print(f'{len(jobs)} ground-summers to fetch')
    done = 0
    for lat, lon, s in jobs:
        dest = os.path.join(out, f'{lat:.4f}_{lon:.4f}_{s}.json')
        if os.path.exists(dest):
            continue
        if (time.time() - t0) / 60 > BUDGET_MIN:
            print(f'time budget of {BUDGET_MIN:.0f} min reached: stopping; the next run carries on')
            break
        end = min(pd.Timestamp(f'{s + 1}-02-28'), pd.Timestamp.utcnow().tz_localize(None) - pd.Timedelta(days=7))
        if end < pd.Timestamp(f'{s}-10-01'):
            continue
        params = dict(parameters=PARAMS, community='RE', latitude=f'{lat:.4f}', longitude=f'{lon:.4f}',
                      start=f'{s}1001', end=end.strftime('%Y%m%d'), format='JSON', **{'time-standard': 'UTC'})
        for attempt in range(4):
            r = requests.get(API, params=params, headers={'User-Agent': UA}, timeout=120)
            if r.status_code == 200:
                break
            print(f'  {lat},{lon} {s}: HTTP {r.status_code} {r.text[:200]}')
            time.sleep(15 * (attempt + 1))
        if r.status_code != 200:
            continue
        with open(dest, 'w') as fh:
            fh.write(r.text)
        done += 1
        time.sleep(PAUSE)
    print(f'fetched {done}; held {len(os.listdir(out))} files')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
