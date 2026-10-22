"""Coordinates of every BBL/WBBL ground, from the Wikipedia article NAMED for it (never a search hit).

A search for each venue name matched the Sydney Cricket Ground for "Brisbane Cricket Ground", Newlands
(Cape Town) for the WACA and The Oval (London) for Ballarat's Eastern Oval. So each Cricsheet venue name
maps to an article title by hand here, the API returns that article's coordinates (following redirects:
"Perth Stadium" is now "Optus Stadium"), and tests/test_collect.py checks every ground is in Australia
unless listed in OVERSEAS. A venue with no title, or a title with no coordinates, is reported, not guessed.

Usage: python -m bbl.collect.coords <out csv> <t20_matches.parquet> [fixtures csv]
"""
import sys
import time

import pandas as pd
import requests

from bbl.collect.wiki import API, UA

# Cricsheet's venue name, before any comma -> the Wikipedia article for that ground
TITLES = {
    'Adelaide Oval': 'Adelaide Oval', 'Adelaide Oval No. 2': 'Adelaide Oval', 'Allan Border Field': 'Allan Border Field',
    'Aurora Stadium': 'York Park', 'University of Tasmania Stadium': 'York Park', 'Invermay Park': 'York Park',
    'UTAS Stadium': 'York Park', 'Bankstown Oval': 'Bankstown Oval', 'Bellerive Oval': 'Bellerive Oval',
    'Blundstone Arena': 'Bellerive Oval', 'Blacktown International Sportspark': 'Blacktown International Sportspark',
    'Brisbane Cricket Ground': 'The Gabba', 'The Gabba': 'The Gabba', 'Gabba': 'The Gabba',
    'Camberwell Sports Ground': 'Camberwell Sports Ground', 'Carrara Oval': 'Carrara Stadium',
    'Metricon Stadium': 'Carrara Stadium', 'People First Stadium': 'Carrara Stadium', 'Casey Fields No 4': 'Casey Fields',
    'Casey Fields No. 4': 'Casey Fields', "Cazaly's Stadium": 'Cazalys Stadium', 'Cricket Central': 'Cricket Central',
    'Docklands Stadium': 'Docklands Stadium', 'Marvel Stadium': 'Docklands Stadium', 'Drummoyne Oval': 'Drummoyne Oval',
    'Eastern Oval': 'Eastern Oval', 'GMHBA Stadium': 'Kardinia Park (stadium)', 'Simonds Stadium': 'Kardinia Park (stadium)',
    'Kardinia Park': 'Kardinia Park (stadium)', 'Geelong Cricket Ground': 'Kardinia Park (stadium)',
    'Gliderol Stadium': 'Glenelg Oval', 'Great Barrier Reef Arena': 'Harrup Park', 'Harrup Park': 'Harrup Park',
    'Ray Mitchell Oval': 'Harrup Park', 'Howell Oval': 'Howell Oval', 'Hurstville Oval': 'Hurstville Oval',
    'International Sports Stadium': 'C.ex Coffs International Stadium', 'Junction Oval': 'Junction Oval',
    'Jubilee Park': 'Jubilee Park, Ringwood', 'Karen Rolton Oval': 'Karen Rolton Oval',
    'Latrobe Recreation Ground': 'Latrobe Recreation Ground', 'Lavington Sports Oval': 'Lavington Sports Ground',
    'Lilac Hill Park': 'Lilac Hill Park', 'Manuka Oval': 'Manuka Oval', 'Melbourne Cricket Ground': 'Melbourne Cricket Ground',
    'North Dalton Park': 'North Dalton Park', 'North Sydney Oval': 'North Sydney Oval', 'North Sydney Oval No.2': 'North Sydney Oval',
    'Nuriootpa Centennial Park': 'Nuriootpa', 'Perth Stadium': 'Perth Stadium', 'Optus Stadium': 'Perth Stadium',
    'Queen Elizabeth II Oval': 'Queen Elizabeth Oval', 'Stadium Australia': 'Stadium Australia',
    'Sydney Cricket Ground': 'Sydney Cricket Ground', 'Sydney Showground Stadium': 'Sydney Showground Stadium',
    'ENGIE Stadium': 'Sydney Showground Stadium', 'Ted Summerton Reserve': 'Ted Summerton Reserve',
    'Traeger Park': 'Traeger Park', 'University Oval': 'University Oval, Hobart', 'W.A.C.A. Ground': 'WACA Ground',
    'WACA Ground': 'WACA Ground', 'Western Australia Cricket Association Ground': 'WACA Ground',
    'Waverley Oval': 'Waverley Oval', 'West Park Oval': 'West Park Oval',
    'M. A. Chidambaram Stadium': 'M. A. Chidambaram Stadium', 'MA Chidambaram Stadium': 'M. A. Chidambaram Stadium',
    # Wikipedia's names, sponsor names included (the same ground under its naming-rights title)
    'ANZ Stadium': 'Stadium Australia', 'Adelaide Oval No.2': 'Adelaide Oval', 'Albrecht Oval': 'Albrecht Oval',
    'BBellerive Oval': 'Bellerive Oval', 'Ninja Stadium': 'Bellerive Oval', 'Blacktown ISP Oval': 'Blacktown International Sportspark',
    'C.ex Coffs International Stadium': 'C.ex Coffs International Stadium', 'Coffs Harbour International Stadium': 'C.ex Coffs International Stadium',
    'Carrara Stadium': 'Carrara Stadium', 'Heritage Bank Stadium': 'Carrara Stadium', 'Casey Fields': 'Casey Fields',
    'Casey Fields No.4': 'Casey Fields', 'Cazalys Stadium': 'Cazalys Stadium', 'CitiPower Centre': 'Junction Oval',
    'Engie Stadium': 'Sydney Showground Stadium', 'Spotless Stadium': 'Sydney Showground Stadium', 'Etihad Stadium': 'Docklands Stadium',
    'Kardinia Stadium': 'Kardinia Park (stadium)', 'Kingston Twin Ovals': 'Kingston Twin Ovals', 'Lavington Sports Ground': 'Lavington Sports Ground',
    'Lilac Hill': 'Lilac Hill Park', 'Marrara Cricket Ground': 'Marrara Cricket Ground',
    'Melbourne Cricket Ground Melbourne': 'Melbourne Cricket Ground', 'North Sydney Oval No. 1': 'North Sydney Oval',
    'North Sydney Oval No. 2': 'North Sydney Oval', 'Queen Elizabeth Oval': 'Queen Elizabeth Oval', 'Robertson Oval': 'Robertson Oval',
    'TIO Traeger Park': 'Traeger Park', 'The WACA': 'WACA Ground', 'Toorak Park': 'Toorak Park', 'West Park': 'West Park Oval',
    'York Park': 'York Park', 'Aquinas College': 'Aquinas College, Perth',
}
# grounds outside Australia that BBL/WBBL has used (BBL|16 opens in Chennai, 12 Dec 2026)
OVERSEAS = {'M. A. Chidambaram Stadium'}
AUSTRALIA = dict(lat=(-44.0, -10.0), lon=(112.0, 154.5))


def head(v):
    return str(v).split(',')[0].strip()


def fetch(titles):
    """{requested title: (resolved title, lat, lon)} following normalisation and redirects."""
    out = {}
    titles = sorted(set(titles))
    for k in range(0, len(titles), 20):
        batch = titles[k:k + 20]
        r = requests.get(API, params=dict(action='query', prop='coordinates', titles='|'.join(batch), redirects=1,
                                          format='json', formatversion=2), headers={'User-Agent': UA}, timeout=60)
        r.raise_for_status()
        q = r.json()['query']
        step = {x['from']: x['to'] for x in q.get('normalized', []) + q.get('redirects', [])}
        pages = {p['title']: p for p in q['pages']}
        for t in batch:
            res = t
            while res in step:
                res = step[res]
            cc = (pages.get(res, {}).get('coordinates') or [{}])[0]
            out[t] = (res, cc.get('lat'), cc.get('lon'))
        time.sleep(2)
    return out


def check(df):
    """Rows whose coordinates are missing or outside Australia (unless an allowed overseas ground)."""
    inside = df.lat.between(*AUSTRALIA['lat']) & df.lon.between(*AUSTRALIA['lon'])
    return df[df.lat.isna() | (~inside & ~df.title.isin(OVERSEAS))]


def main(out, matches, fixtures=None):
    m = pd.read_parquet(matches)
    names = set(m[m.competition.isin(['Big Bash League', "Women's Big Bash League"])].venue.dropna())
    if fixtures:
        names |= set(pd.read_csv(fixtures).venue_full.dropna())
    rows = [dict(venue=v, title=TITLES.get(head(v))) for v in sorted(names)]
    got = fetch([r['title'] for r in rows if r['title']])
    for r in rows:
        res, lat, lon = got.get(r['title'], (None, None, None))
        r.update(resolved=res, lat=lat, lon=lon)
    df = pd.DataFrame(rows)
    df.to_csv(out, index=False)
    bad = check(df)
    print(f'{len(df)} venue names, {df.lat.notna().sum()} with coordinates')
    if len(bad):
        print('NOT PLACED (no title, no coordinates, or outside Australia):')
        print(bad.to_string(index=False))


if __name__ == '__main__':
    main(*sys.argv[1:])
