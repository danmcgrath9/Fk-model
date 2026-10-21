"""Read each NRL data source's robots.txt and terms BEFORE we pull anything from it.

Runs on a GitHub runner (the build session cannot reach these sites). For every source it
records: robots.txt, the lines of its terms page that mention copying, scraping, commercial use
or permission, and, for the two feeds we might rely on, a tiny sample so we know what they hold:

  Champion Data match centre (what nrlR reads): the competitions list, one fixture, one match.
    Three requests, 3 seconds apart, and only if robots.txt does not disallow /data/.
  AusSportsBetting historical NRL odds: the download page only (its terms and the file link).
    The file itself is NOT downloaded here; that waits until the founder has read the terms.

Writes nrl/cache/sources/SOURCES.md and the raw pages beside it.
"""
import json
import os
import re
import time
import urllib.robotparser

import requests

OUT = os.environ.get('OUT', 'nrl/cache/sources')
UA = os.environ.get('NRL_UA', 'fk-model NRL research')
PAUSE = 3

SITES = {
    'Rugby League Project': ('https://www.rugbyleagueproject.org',
                             ['/', '/about.html', '/terms.html', '/copyright.html']),
    'Champion Data match centre': ('https://mc.championdata.com', ['/']),
    'Champion Data': ('https://www.championdata.com',
                      ['/terms-of-use/', '/terms-and-conditions/', '/terms/', '/privacy-policy/']),
    'NRL.com': ('https://www.nrl.com', ['/terms-of-use/', '/terms-and-conditions/', '/terms/']),
    'Zero Tackle': ('https://www.zerotackle.com', ['/terms-of-use/', '/terms-and-conditions/', '/terms/']),
    'AusSportsBetting': ('https://www.aussportsbetting.com',
                         ['/data/historical-nrl-results-and-odds-data/', '/data/', '/terms-of-use/',
                          '/terms-and-conditions/', '/disclaimer/']),
    'BOM': ('http://www.bom.gov.au', ['/other/copyright.shtml', '/other/disclaimer.shtml']),
    'Open-Meteo': ('https://open-meteo.com', ['/en/terms', '/en/pricing', '/en/licence']),
}
KEYWORDS = re.compile(r'scrap|crawl|spider|robot|automat|copy|reproduc|commercial|permission|licen[cs]e|'
                      r'redistribut|personal use|non-commercial|download|terms|prohibit|creative commons',
                      re.I)

session = requests.Session()
session.headers['User-Agent'] = UA
report = []


def text_of(html):
    html = re.sub(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>', ' ', html)
    txt = re.sub(r'(?s)<[^>]+>', '\n', html)
    txt = re.sub(r'&nbsp;|&#160;', ' ', txt)
    lines = [re.sub(r'\s+', ' ', l).strip() for l in txt.split('\n')]
    return [l for l in lines if len(l) > 2]


def fetch(url):
    try:
        r = session.get(url, timeout=30)
        time.sleep(PAUSE)
        return r
    except requests.RequestException as e:
        time.sleep(PAUSE)
        return e


def slug(url):
    return re.sub(r'[^A-Za-z0-9]+', '_', url).strip('_')[:120]


def check_site(name, base, paths):
    report.extend([f'## {name}', ''])
    rp = urllib.robotparser.RobotFileParser()
    r = fetch(base + '/robots.txt')
    if isinstance(r, requests.Response) and r.status_code == 200:
        rp.parse(r.text.splitlines())
        open(os.path.join(OUT, slug(base) + '_robots.txt'), 'w').write(r.text)
        lines = [l for l in r.text.splitlines() if l.strip() and not l.startswith('#')][:25]
        report += ['robots.txt (first lines):', '```', *lines, '```']
    else:
        rp = None
        report.append(f'robots.txt: {getattr(r, "status_code", r)}')
    for p in paths:
        url = base + p
        r = fetch(url)
        if not isinstance(r, requests.Response):
            report.append(f'- `{p}`: error {r}')
            continue
        report.append(f'- `{p}`: HTTP {r.status_code}, final URL {r.url}')
        if r.status_code != 200 or 'html' not in r.headers.get('content-type', ''):
            continue
        open(os.path.join(OUT, slug(url) + '.html'), 'w').write(r.text)
        hits = [l for l in text_of(r.text) if KEYWORDS.search(l) and len(l) < 1200]
        links = sorted(set(re.findall(r'href="([^"]*(?:term|copyright|licen|\.xlsx?|\.csv)[^"]*)"', r.text, re.I)))
        if hits:
            report += ['  lines about terms or reuse:', '', *[f'  > {l}' for l in hits[:40]], '']
        if links:
            report.append('  links: ' + ', '.join(f'`{l}`' for l in links[:20]))
    report.append('')
    return rp


def champion_data_sample(rp):
    report.extend(['## Champion Data match-centre feed: what it holds (3-request sample)', ''])
    base = 'https://mc.championdata.com/data'
    if rp is not None and not rp.can_fetch(UA, base + '/competitions.json'):
        report += ['robots.txt disallows /data/: NOT sampled.', '']
        return
    r = fetch(base + '/competitions.json')
    if not isinstance(r, requests.Response) or r.status_code != 200:
        report += [f'competitions.json: {getattr(r, "status_code", r)}', '']
        return
    comps = r.json().get('competitionDetails', {}).get('competition', [])
    json.dump(comps, open(os.path.join(OUT, 'cd_competitions.json'), 'w'))
    nrl = [c for c in comps if re.search(r'NRL|Premiership|Rugby League', str(c.get('name', '')), re.I)]
    report += [f'{len(comps)} competitions listed; {len(nrl)} look like rugby league:', '',
               '| id | name | season |', '|---|---|---|']
    for c in sorted(nrl, key=lambda c: str(c.get('season', '')))[:80]:
        report.append(f'| {c.get("id")} | {c.get("name")} | {c.get("season")} |')
    report.append('')
    men = [c for c in nrl if re.search(r'^NRL|Telstra Premiership|NRL Premiership', str(c.get('name', '')))
           and not re.search(r'NRLW|Women|State of Origin|Cup|Pre', str(c.get('name', '')), re.I)]
    if not men:
        report += ['no men\'s NRL premiership found in the list; fixture not sampled', '']
        return
    latest = max(men, key=lambda c: str(c.get('season', '')))
    r = fetch(f'{base}/{latest["id"]}/fixture.json')
    if not isinstance(r, requests.Response) or r.status_code != 200:
        report += [f'fixture for {latest["id"]}: {getattr(r, "status_code", r)}', '']
        return
    matches = (r.json().get('fixture') or {}).get('match') or []
    json.dump(matches, open(os.path.join(OUT, 'cd_fixture_sample.json'), 'w'))
    done = [m for m in matches if m.get('matchStatus') == 'complete']
    report += [f'fixture {latest["id"]} ({latest.get("name")} {latest.get("season")}): {len(matches)} matches, '
               f'{len(done)} complete. Fixture fields: {", ".join(sorted(matches[0].keys())) if matches else "none"}', '']
    if not done:
        return
    mid = done[-1]['matchId']
    r = fetch(f'{base}/{latest["id"]}/{mid}.json')
    if not isinstance(r, requests.Response) or r.status_code != 200:
        report += [f'match {mid}: {getattr(r, "status_code", r)}', '']
        return
    body = r.json()
    json.dump(body, open(os.path.join(OUT, 'cd_match_sample.json'), 'w'))

    def keys(o, depth=0, prefix=''):
        out = []
        if isinstance(o, dict) and depth < 4:
            for k, v in o.items():
                out.append(f'{prefix}{k} ({type(v).__name__}{", " + str(len(v)) if isinstance(v, list) else ""})')
                sub = v[0] if isinstance(v, list) and v else v
                out += keys(sub, depth + 1, prefix + '  ')
        return out
    report += [f'match {mid}: structure (first four levels)', '```', *keys(body)[:150], '```', '']


def main():
    os.makedirs(OUT, exist_ok=True)
    report.extend(['# NRL sources: robots.txt, terms, and what the feeds hold', '',
                   f'User-Agent: `{UA}`; {PAUSE} s between requests.', ''])
    robots = {}
    for name, (base, paths) in SITES.items():
        robots[name] = check_site(name, base, paths)
    champion_data_sample(robots.get('Champion Data match centre'))
    text = '\n'.join(report)
    open(os.path.join(OUT, 'SOURCES.md'), 'w').write(text)
    print(text)
    summ = os.environ.get('GITHUB_STEP_SUMMARY')
    if summ:
        open(summ, 'a').write(text + '\n')


if __name__ == '__main__':
    main()
