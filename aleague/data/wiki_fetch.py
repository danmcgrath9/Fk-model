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
# Wikimedia's User-Agent policy asks for a way to reach the operator; the repository URL is one
UA = (os.environ.get('ALEAGUE_UA', '').strip() or 'fk-model A-League research') + \
    ' (https://github.com/danmcgrath9/Fk-model) python-requests'
PAUSE = float(os.environ.get('WIKI_PAUSE', '5'))


def call(session, params):
    """One API request, waiting out 429s and replication lag."""
    for attempt in range(6):
        r = session.get(API, params=params, timeout=60)
        if r.status_code == 429 or 'maxlag' in r.text[:200]:
            wait = int(r.headers.get('Retry-After', 0) or 0) or 30 * (attempt + 1)
            print(f'  {r.status_code}: waiting {wait} s (attempt {attempt + 1})')
            time.sleep(wait)
            continue
        r.raise_for_status()
        time.sleep(PAUSE)
        return r.json()
    r.raise_for_status()
    raise RuntimeError(f'Wikipedia kept refusing after 6 attempts ({r.status_code})')


def fetch(session, titles):
    """{title: wikitext} for up to 50 titles, following redirects and the API's continuation
    (a batch whose content is too large comes back in parts)."""
    params = {'action': 'query', 'prop': 'revisions', 'rvprop': 'content', 'rvslots': 'main', 'redirects': 1,
              'format': 'json', 'formatversion': 2, 'maxlag': 5, 'titles': '|'.join(titles)}
    out = {}
    while True:
        j = call(session, params)
        for p in j.get('query', {}).get('pages', []):
            if p.get('missing') or not p.get('revisions'):
                continue
            out[p['title']] = p['revisions'][0]['slots']['main']['content']
        if 'continue' not in j:
            return out
        params = {**params, **j['continue']}


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
    seasons = args.seasons.split(',')
    # before 2021-22 the league was "A-League"; ask for both names in one request
    names = [f'{x} A-League Men' for x in seasons] + [f'{x} A-League' for x in seasons]
    leagues = {}
    for i in range(0, len(names), 10):
        leagues.update(fetch(s, names[i:i + 10]))
    for season in seasons:
        hit = [(t, b) for t, b in leagues.items() if t.startswith(season + ' ')]
        if not hit:
            log.append(f'{season}: league page missing'); continue
        title, text = hit[0]
        league = title
        open(os.path.join(args.out, safe(title) + '.wiki'), 'w').write(text)
        clubs = sorted(set(re.findall(r'\[\[(' + re.escape(season) + r' [^\]|]+? season)', text)))
        log.append(f'{league}: {len(text):,} chars, {len(clubs)} club season pages linked')
        for i in range(0, len(clubs), 20):
            for t, body in fetch(s, clubs[i:i + 20]).items():
                open(os.path.join(args.out, safe(t) + '.wiki'), 'w').write(body)
                n = len(re.findall(r'\{\{\s*[Ff]ootball ?box', body))
                log.append(f'  {t}: {len(body):,} chars, {n} footballboxes')
    text = '\n'.join(log)
    open(os.path.join(args.out, 'fetch_log.txt'), 'w').write(text + '\n')
    print(text)


if __name__ == '__main__':
    main()
