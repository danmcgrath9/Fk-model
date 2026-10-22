"""Wikipedia season pages (fixtures, start times, venues, squads) and ground coordinates, through the API.

Wikimedia's API policy: a User-Agent naming the client and a way to reach its owner, one request at a time,
honour throttling. Content is CC BY-SA: kept with its page title and revision id so it can be attributed.
Raw responses only: bbl/collect/parse_wiki.py turns them into tables, so a parsing fix never re-asks the site.

Usage: python -m bbl.collect.wiki <out dir> <t20_matches.parquet>
       python -m bbl.collect.wiki <out dir> --squads   (the separate season squads pages)
"""
import json
import os
import sys
import time

import pandas as pd
import requests

API = 'https://en.wikipedia.org/w/api.php'
UA = os.environ.get('WIKI_UA', 'fk-model-bbl/0.1 (github.com/danmcgrath9/Fk-model; research)')
PAUSE = 2.0


def season_titles():
    out = []
    for y in range(2011, 2027):
        s = f'{y}–{(y + 1) % 100:02d}'
        out.append(f'{s} Big Bash League season')
        if y >= 2015:
            out.append(f"{s} Women's Big Bash League season")
    return out


def get(params):
    for attempt in range(4):
        r = requests.get(API, params={**params, 'format': 'json', 'formatversion': 2, 'maxlag': 5},
                         headers={'User-Agent': UA}, timeout=60)
        if r.status_code == 200 and 'error' not in r.json():
            time.sleep(PAUSE)
            return r.json()
        wait = int(r.headers.get('Retry-After', 10 * (attempt + 1)))
        print(f'  HTTP {r.status_code}, waiting {wait}s')
        time.sleep(wait)
    r.raise_for_status()
    return r.json()


def squad_titles():
    """The separate '<season> squads' pages (most seasons have none; a missing page is recorded as missing)."""
    return [t + ' squads' for t in season_titles()]


def fetch_pages(titles, dest):
    os.makedirs(dest, exist_ok=True)
    for k in range(0, len(titles), 4):
        batch = titles[k:k + 4]
        body = get(dict(action='query', prop='revisions', rvprop='content|ids|timestamp', rvslots='main',
                        titles='|'.join(batch), redirects=1))
        for page in body['query']['pages']:
            with open(os.path.join(dest, page['title'].replace('/', '_') + '.json'), 'w') as fh:
                json.dump(page, fh)
            print(f'{page["title"]}: {"missing" if page.get("missing") else "held"}')


def main(out, matches):
    if matches == '--squads':
        fetch_pages(squad_titles(), os.path.join(out, 'squads'))
        return
    os.makedirs(os.path.join(out, 'pages'), exist_ok=True)
    titles = season_titles()
    for k in range(0, len(titles), 4):
        batch = titles[k:k + 4]
        body = get(dict(action='query', prop='revisions', rvprop='content|ids|timestamp', rvslots='main',
                        titles='|'.join(batch), redirects=1))
        for page in body['query']['pages']:
            name = page['title'].replace('/', '_')
            with open(os.path.join(out, 'pages', name + '.json'), 'w') as fh:
                json.dump(page, fh)
            rev = (page.get('revisions') or [{}])[0]
            print(f'{page["title"]}: {"missing" if page.get("missing") else str(len(rev.get("slots", {}).get("main", {}).get("content", ""))) + " chars, rev " + str(rev.get("revid"))}')
    # grounds: every venue name Cricsheet uses for a BBL or WBBL game, searched, then the top hit's coordinates
    m = pd.read_parquet(matches)
    venues = sorted(m[m.competition.isin(['Big Bash League', "Women's Big Bash League"])].venue.dropna().unique())
    found = []
    for v in venues:
        s = get(dict(action='query', list='search', srsearch=f'{v.split(",")[0]} cricket ground', srlimit=1))
        hit = (s['query']['search'] or [{}])[0].get('title')
        found.append(dict(venue=v, title=hit))
    hits = sorted({f['title'] for f in found if f['title']})
    coords = {}
    for k in range(0, len(hits), 20):
        c = get(dict(action='query', prop='coordinates', titles='|'.join(hits[k:k + 20]), redirects=1))
        for page in c['query']['pages']:
            cc = (page.get('coordinates') or [{}])[0]
            coords[page['title']] = (cc.get('lat'), cc.get('lon'))
    for f in found:
        f['lat'], f['lon'] = coords.get(f['title'], (None, None))
    pd.DataFrame(found).to_csv(os.path.join(out, 'venue_coords.csv'), index=False)
    print(f'{len(venues)} venue names, {sum(1 for f in found if f["lat"] is not None)} with coordinates')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
