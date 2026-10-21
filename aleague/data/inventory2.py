"""Second inventory look (step 1 continued): two leads found after the first run.

  aussportsbetting.com   publishes historical results-and-odds spreadsheets for Australian leagues
                         as free downloads; does it have one for the A-League, what is in it, what
                         do its terms say
  Ultimate A-League      robots.txt allows its match pages; what do they hold (line-ups, substitutions,
                         cards) and does it publish terms anywhere

One page or file at a time, PAUSE seconds apart; nothing bulk. Writes <out>/INVENTORY2.md and every body.
Usage: python aleague/data/inventory2.py --out aleague/cache/inventory2
"""
import argparse
import io
import os
import re
import time

import pandas as pd
import requests

UA = (os.environ.get('ALEAGUE_UA', '').strip() or 'fk-model A-League research') + ' (https://github.com/danmcgrath9/Fk-model)'
PAUSE = float(os.environ.get('PAUSE', '8'))
TERMS_WORDS = re.compile(r'scrap|crawl|robot|automat|spider|harvest|commercial|redistribut|copyright|'
                         r'personal use|permission|reproduc|download', re.I)


class F:
    def __init__(self, out):
        self.out, self.s, self.t = out, requests.Session(), 0.0
        self.s.headers['User-Agent'] = UA

    def get(self, url, name):
        time.sleep(max(0.0, PAUSE - (time.time() - self.t)))
        try:
            r = self.s.get(url, timeout=60)
        except requests.RequestException as e:
            self.t = time.time()
            print(f'{name}: FAILED {e}')
            return None
        self.t = time.time()
        print(f'{name}: HTTP {r.status_code}, {len(r.content):,} bytes, {r.headers.get("content-type")}')
        open(os.path.join(self.out, re.sub(r'[^A-Za-z0-9.-]+', '_', name)), 'wb').write(r.content)
        return r


def text_of(html):
    t = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', html, flags=re.S | re.I)
    t = re.sub(r'<[^>]+>', '\n', t)
    return [re.sub(r'\s+', ' ', l).strip() for l in t.splitlines() if l.strip()]


def terms_lines(r):
    if r is None or r.status_code != 200:
        return [f'HTTP {getattr(r, "status_code", "no answer")}']
    hits = []
    for line in text_of(r.text):
        if 15 < len(line) < 700 and TERMS_WORDS.search(line) and line not in hits:
            hits.append(line)
    return [f'> {h}' for h in hits[:15]] or ['(no lines about scraping, copying or reuse)']


def links(r, pat):
    return sorted(set(re.findall(pat, r.text))) if r is not None and r.status_code == 200 else []


def aussportsbetting(f):
    out = ['## aussportsbetting.com', '']
    base = 'https://www.aussportsbetting.com'
    idx = f.get(f'{base}/data/', 'asb data index.html')
    files = links(idx, r'href="([^"]+\.xlsx?)"')
    pages = links(idx, r'href="(https://www\.aussportsbetting\.com/data/[^"]+)"')
    out += [f'- data index: {len(files)} spreadsheet links; data pages: {len(pages)}',
            '  - ' + ', '.join(files[:30]), '  - pages: ' + ', '.join(p.rsplit('/data/', 1)[-1] for p in pages[:40])]
    for name, url in (('terms', f'{base}/terms-and-conditions/'), ('robots', f'{base}/robots.txt')):
        r = f.get(url, f'asb {name}')
        out += [f'- {name} ({url}):'] + ([f'  ```', *r.text.splitlines()[:20], '  ```'] if name == 'robots' and r is not None
                                         else terms_lines(r))
    # the A-League page and its file, if there is one
    league_pages = [p for p in pages if re.search(r'a-?league|soccer|football', p, re.I) and 'afl' not in p.lower()]
    cand = [x for x in files if re.search(r'a-?league|aleague|soccer', x, re.I)]
    for p in league_pages[:2]:
        r = f.get(p, 'asb ' + p.rstrip('/').rsplit('/', 1)[-1] + '.html')
        cand += [x for x in links(r, r'href="([^"]+\.xlsx?)"') if x not in cand]
        out += [f'- page {p}:'] + terms_lines(r)[:6]
    for x in cand[:2]:
        url = x if x.startswith('http') else base + x
        r = f.get(url, 'asb ' + url.rsplit('/', 1)[-1])
        if r is None or r.status_code != 200:
            continue
        try:
            sheets = pd.read_excel(io.BytesIO(r.content), sheet_name=None, header=None)
        except Exception as e:  # noqa: BLE001
            out.append(f'- {url}: could not read ({e})'); continue
        for sname, df in sheets.items():
            hdr = next((i for i in range(min(5, len(df))) if df.iloc[i].astype(str).str.contains('Date').any()), 0)
            d = pd.read_excel(io.BytesIO(r.content), sheet_name=sname, header=hdr)
            dates = pd.to_datetime(d.get('Date'), errors='coerce')
            out += [f'- {url} sheet "{sname}": {len(d):,} rows, dates {dates.min()} to {dates.max()}',
                    f'  - columns: `{", ".join(map(str, d.columns))}`',
                    '  - filled share of odds columns: ' + ', '.join(
                        f'{c} {d[c].notna().mean():.0%}' for c in d.columns if re.search(r'odds|line|total|open|close|min|max', str(c), re.I))]
    return out + ['']


def ultimate(f):
    out = ['## Ultimate A-League', '']
    base = 'https://www.ultimatealeague.com'
    home = f.get(base + '/', 'ual home.html')
    nav = links(home, r'href="(/[^"#?]+)"')
    out.append('- site sections: ' + ', '.join(nav[:60]))
    legal = [n for n in nav if re.search(r'legal|terms|privacy|about|contact|copyright', n, re.I)]
    for n in legal[:3]:
        out += [f'- {n}:'] + terms_lines(f.get(base + n, 'ual ' + n.strip('/').replace('/', '_') + '.html'))
    if not legal:
        out += ['- no legal/terms link on the home page; trying /legal/ once (robots asks crawlers to skip it, '
                'this is a single read of the terms, not a crawl)']
        out += terms_lines(f.get(base + '/legal/', 'ual legal.html'))
    # one season and one match, to see what a match page carries
    season = [n for n in nav if re.search(r'season|20\d\d', n)][:1]
    if season:
        s = f.get(base + season[0], 'ual season.html')
        matches = [m for m in links(s, r'href="(/[^"]*match[^"]*)"')][:1]
        out.append(f'- season page {season[0]}: {len(links(s, r"href=\"(/[^\"]*match[^\"]*)\""))} match links')
        if matches:
            m = f.get(base + matches[0], 'ual match.html')
            lines = text_of(m.text) if m is not None and m.status_code == 200 else []
            out += [f'- match page {matches[0]} (first 60 text lines):', '```', *lines[:60], '```']
    return out + ['']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    f = F(args.out)
    report = ['# A-League Men data inventory, second look', '']
    for part in (aussportsbetting, ultimate):
        try:
            report += part(f)
        except Exception as e:  # noqa: BLE001
            report += [f'## {part.__name__}: FAILED {type(e).__name__}: {e}', '']
    text = '\n'.join(report)
    open(os.path.join(args.out, 'INVENTORY2.md'), 'w').write(text)
    print(text)
    s = os.environ.get('GITHUB_STEP_SUMMARY')
    if s:
        open(s, 'a').write(text + '\n')


if __name__ == '__main__':
    main()
