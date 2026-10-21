"""Pull NRL.com's round team-list and late-mail articles once (private, non-commercial research).

Only men's NRL round articles are kept (no NRLW, Toyota Cup, trials, State of Origin, fantasy or
predictions), from the URL list the probe built (urls.txt). Before 2020 the articles are prose written
when the lists were named, so they keep Tuesday's 19-22; from 2020 the page shows the match-day 18 and
adds nothing over who played, but is kept for the record. One request every PAUSE seconds.

Writes nrl/cache/teamlists/<season>.jsonl.gz: one line per article {"url", "status", "html"}.
Usage: python nrl/teamlists/pull.py <urls.txt> [seasons, e.g. 2009-2026]
"""
import gzip
import json
import os
import re
import sys
import time

import requests

UA = os.environ.get('NRL_UA', 'fk-model NRL research')
PAUSE = float(os.environ.get('PAUSE', '3'))
OUT = 'nrl/cache/teamlists'
KEEP = re.compile(r'(team-?lists?|late-mail)', re.I)
DROP = re.compile(r'toyota|nrlw|women|trial|pre-season|preseason|all-stars|origin|world-club|charity|nines|fantasy|'
                  r'predict|nsw-cup|qld-cup|intrust|hostplus|under-20|u20|holden-cup|jersey-flegg|country|city|test|'
                  r'pacific|kangaroos|knock-on|harvey-norman|tips|topic', re.I)


def wanted(url):
    return bool(KEEP.search(url)) and not DROP.search(url) and re.search(r'/news/20\d\d/', url)


def main(urls_file, seasons='2009-2026'):
    a, _, b = seasons.partition('-')
    years = range(int(a), int(b or a) + 1)
    urls = [u.strip() for u in open(urls_file) if wanted(u.strip())]
    os.makedirs(OUT, exist_ok=True)
    s = requests.Session()
    s.headers['User-Agent'] = UA
    for y in years:
        mine = [u for u in urls if f'/news/{y}/' in u]
        if not mine:
            continue
        n = 0
        with gzip.open(os.path.join(OUT, f'{y}.jsonl.gz'), 'wt') as fh:
            for u in mine:
                try:
                    r = s.get(u, timeout=60)
                    fh.write(json.dumps({'url': u, 'status': r.status_code, 'html': r.text if r.status_code == 200 else ''}) + '\n')
                    n += r.status_code == 200
                except requests.RequestException as e:
                    fh.write(json.dumps({'url': u, 'status': str(e), 'html': ''}) + '\n')
                time.sleep(PAUSE)
        print(f'{y}: {n} of {len(mine)} articles')


if __name__ == '__main__':
    main(*sys.argv[1:])
