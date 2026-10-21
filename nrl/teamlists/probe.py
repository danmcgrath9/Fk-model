"""Where are NRL.com's team-list articles, and can we read them? A small probe before any pull.

NRL.com's terms allow downloading for private, non-commercial use (nrl/docs/INVENTORY.md); its
robots.txt allows everything and points at a sitemap. This walks the sitemap (at most MAX_SITEMAPS
files), collects every article URL that looks like a team list or late mail, and saves ONE sample
article per season so the parser can be written against real pages. One request every PAUSE seconds.

Writes nrl/cache/teamlists_probe/: urls.txt, sample_<season>.html, PROBE.md
"""
import gzip
import os
import re
import time
from collections import defaultdict

import requests

UA = os.environ.get('NRL_UA', 'fk-model NRL research')
PAUSE = float(os.environ.get('PAUSE', '3'))
MAX_SITEMAPS = int(os.environ.get('MAX_SITEMAPS', '400'))
OUT = 'nrl/cache/teamlists_probe'
ROOT = 'https://www.nrl.com/sitemap/sitemap.xml'
LIST = re.compile(r'team-?lists?|late-mail|teams-for-round|named-teams', re.I)

s = requests.Session()
s.headers['User-Agent'] = UA


def get(url):
    try:
        r = s.get(url, timeout=60)
    except requests.RequestException as e:
        print(f'{url}: {e}')
        r = None
    time.sleep(PAUSE)
    return r


def main():
    os.makedirs(OUT, exist_ok=True)
    report = ['# NRL.com team-list probe', '']
    queue, seen, found, fetched = [ROOT], set(), set(), 0
    kinds = defaultdict(int)
    while queue and fetched < MAX_SITEMAPS:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        r = get(url)
        fetched += 1
        if r is None or r.status_code != 200:
            report.append(f'- {url}: {getattr(r, "status_code", "error")}')
            continue
        body = gzip.decompress(r.content).decode('utf-8', 'replace') if r.content[:2] == b'\x1f\x8b' else r.text
        locs = re.findall(r'<loc>\s*([^<\s]+)\s*</loc>', body)
        if '<sitemapindex' in body:
            kinds['index'] += 1
            # newest first is the order NRL.com uses; keep every child, prefer ones that look like news
            news = [l for l in locs if re.search(r'news|article|20\d\d', l, re.I)]
            queue = news + [l for l in locs if l not in news] + queue
            if fetched <= 3:
                report.append(f'- index {url}: {len(locs)} children, e.g. {locs[:5]}')
        else:
            kinds['urlset'] += 1
            hits = [l for l in locs if LIST.search(l)]
            report.append(f'- {url}: {len(locs):,} URLs, {len(hits)} team-list-like')
            found.update(hits)
    report.append(f'\nFetched {fetched} sitemap files ({dict(kinds)}); {len(found)} team-list-like URLs.\n')
    by_season = defaultdict(list)
    for u in sorted(found):
        m = re.search(r'/news/(20\d\d)/', u)
        by_season[m.group(1) if m else 'undated'].append(u)
    report += ['| season | URLs | examples |', '|---|---|---|']
    for k in sorted(by_season):
        report.append(f'| {k} | {len(by_season[k])} | {"<br>".join(by_season[k][:3])} |')
    open(os.path.join(OUT, 'urls.txt'), 'w').write('\n'.join(sorted(found)) + '\n')
    for season, urls in sorted(by_season.items()):
        pick = next((u for u in urls if re.search(r'nrl-team-lists-round-\d+/?$', u)), urls[0])
        r = get(pick)
        if r is not None and r.status_code == 200:
            open(os.path.join(OUT, f'sample_{season}.html'), 'w').write(r.text)
            names = len(re.findall(r'team-list-profile__name', r.text))
            report.append(f'- sample {season}: {pick} ({len(r.text):,} bytes, {names} player-name blocks)')
    text = '\n'.join(report)
    open(os.path.join(OUT, 'PROBE.md'), 'w').write(text)
    print(text)
    summ = os.environ.get('GITHUB_STEP_SUMMARY')
    if summ:
        open(summ, 'a').write(text + '\n')


if __name__ == '__main__':
    main()
