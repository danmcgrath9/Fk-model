"""Pull the Champion Data match-centre JSON for one or more NRL seasons, once.

The founder approved this pull for private research (21 Oct 2026) after being told the feed has no
published terms or licence. One request at a time, PAUSE seconds apart, identified by User-Agent.
For each season: the premiership and finals fixtures, then one file per completed game.

Writes, per season:
  <out>/cd_raw_<season>.jsonl.gz  one line per game: {"comp_id", "comp_name", "fixture": <fixture row>,
                                  "match": <the match JSON as served>}
  <out>/cd_missing_<season>.txt   games that failed after retries (empty when complete)

Usage: python nrl/data/pull_cd.py --seasons 2014-2026 --out nrl/cache/cd
"""
import argparse
import gzip
import json
import os
import re
import sys
import time

import requests

BASE = 'https://mc.championdata.com/data'
UA = os.environ.get('NRL_UA', 'fk-model NRL research')
PAUSE = float(os.environ.get('PAUSE', '3'))
NAME = re.compile(r'(\d{4}) (Telstra )?NRL (Premiership|Finals)')

session = requests.Session()
session.headers['User-Agent'] = UA


def get_json(url):
    for attempt in range(4):
        try:
            r = session.get(url, timeout=60)
            time.sleep(PAUSE)
            if r.status_code == 200:
                return r.json()
            print(f'  {url}: HTTP {r.status_code}')
            if r.status_code in (403, 404):
                return None
        except (requests.RequestException, ValueError) as e:
            print(f'  {url}: {e}')
            time.sleep(PAUSE)
        time.sleep(PAUSE * 2 ** attempt)
    return None


def seasons_arg(s):
    a, _, b = s.partition('-')
    return list(range(int(a), int(b or a) + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seasons', required=True, help='e.g. 2014-2026 or 2025')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    comps = (get_json(f'{BASE}/competitions.json') or {}).get('competitionDetails', {}).get('competition', [])
    if not comps:
        sys.exit('could not read the competitions list')
    for season in seasons_arg(args.seasons):
        mine = [c for c in comps if (m := NAME.fullmatch(str(c.get('name', '')).strip())) and int(m.group(1)) == season]
        if not mine:
            print(f'{season}: no NRL premiership or finals competition listed')
            continue
        dest = os.path.join(args.out, f'cd_raw_{season}.jsonl.gz')
        missing, n = [], 0
        with gzip.open(dest + '.part', 'wt') as fh:
            for c in sorted(mine, key=lambda c: c['id']):
                fix = ((get_json(f'{BASE}/{c["id"]}/fixture.json') or {}).get('fixture') or {}).get('match') or []
                done = [m for m in fix if m.get('matchStatus') == 'complete']
                print(f'{season} {c["name"]} ({c["id"]}): {len(fix)} games, {len(done)} complete')
                for m in done:
                    body = get_json(f'{BASE}/{c["id"]}/{m["matchId"]}.json')
                    if body is None:
                        missing.append(f'{c["id"]} {m["matchId"]}')
                        continue
                    fh.write(json.dumps({'comp_id': c['id'], 'comp_name': c['name'], 'fixture': m, 'match': body}) + '\n')
                    n += 1
        os.replace(dest + '.part', dest)
        with open(os.path.join(args.out, f'cd_missing_{season}.txt'), 'w') as fh:
            fh.write(''.join(x + '\n' for x in missing))
        print(f'{season}: {n} games written, {len(missing)} missing')


if __name__ == '__main__':
    sys.exit(main())
