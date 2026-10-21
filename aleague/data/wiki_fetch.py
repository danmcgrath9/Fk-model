"""Fetch the wikitext of A-League Men season pages and each club's season page from Wikipedia.

Why Wikipedia: the GitHub mirror of FBref results (worldfootballR_data) stops at May 2025, and FBref,
ESPN and FotMob forbid automated access. Wikipedia's text is CC BY-SA 4.0 (reuse allowed with
attribution) and its API is built for this: we identify ourselves in the User-Agent, batch up to 50
titles per request and pause between requests (https://www.mediawiki.org/wiki/API:Etiquette).

Each club season page carries every match as a {{footballbox}} with date, score, scorers and minute,
venue, attendance and referee; aleague/data/wiki_parse.py reads them.

Usage: python aleague/data/wiki_fetch.py --out aleague/cache/wiki [--seasons 2024–25,2025–26]
Writes <out>/<title>.wiki per page and <out>/fetch_log.txt.
"""
import argparse
import os
import re
import time

import requests

API = 'https://en.wikipedia.org/w/api.php'
UA = os.environ.get('ALEAGUE_UA', 'fk-model A-League research')
PAUSE = float(os.environ.get('WIKI_PAUSE', '3'))


def fetch(session, titles):
    """{title: wikitext} for up to 50 titles, following redirects."""
    r = session.get(API, params={'action': 'query', 'prop': 'revisions', 'rvprop': 'content', 'rvslots': 'main',
                                 'redirects': 1, 'format': 'json', 'formatversion': 2, 'titles': '|'.join(titles)},
                    timeout=60)
    r.raise_for_status()
    time.sleep(PAUSE)
    out = {}
    for p in r.json().get('query', {}).get('pages', []):
        if p.get('missing'):
            continue
        out[p['title']] = p['revisions'][0]['slots']['main']['content']
    return out


def safe(title):
    return re.sub(r'[^A-Za-z0-9.–-]+', '_', title)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--seasons', default=','.join(f'{y}–{str(y + 1)[2:]}' for y in range(2013, 2027)))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    s = requests.Session()
    s.headers['User-Agent'] = UA
    log = []
    for season in args.seasons.split(','):
        league = f'{season} A-League Men'
        got = fetch(s, [league])
        if not got:  # before 2021-22 the league was "A-League"
            league = f'{season} A-League'
            got = fetch(s, [league])
        if not got:
            log.append(f'{league}: missing'); continue
        title, text = next(iter(got.items()))
        open(os.path.join(args.out, safe(title) + '.wiki'), 'w').write(text)
        clubs = sorted(set(re.findall(r'\[\[(' + re.escape(season) + r' [^\]|]+? season)', text)))
        log.append(f'{league}: {len(text):,} chars, {len(clubs)} club season pages linked')
        for i in range(0, len(clubs), 50):
            for t, body in fetch(s, clubs[i:i + 50]).items():
                open(os.path.join(args.out, safe(t) + '.wiki'), 'w').write(body)
                n = len(re.findall(r'\{\{\s*[Ff]ootball ?box', body))
                log.append(f'  {t}: {len(body):,} chars, {n} footballboxes')
    text = '\n'.join(log)
    open(os.path.join(args.out, 'fetch_log.txt'), 'w').write(text + '\n')
    print(text)


if __name__ == '__main__':
    main()
