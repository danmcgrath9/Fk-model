"""What does each candidate A-League Men data source hold, and what do its terms say? One look each.

Step 1 of prompts/aleague.md: list every source before building anything. Each source gets its
robots.txt and its terms page recorded, and the ones whose terms do not forbid it get ONE sample
(a single file or one or two pages, PAUSE seconds apart) so the inventory says what came back, not
what a blog claims. Nothing here is a bulk pull.

  football-data.co.uk   one CSV of A-League results and odds (the site offers it as a download)
  FBref                 season list, one season's fixtures, one match report (player table columns)
  ESPN                  one scoreboard and one match summary from its public JSON (player stats keys)
  Open-Meteo            one day of hourly weather at Sydney (archive API)
  FotMob, Sofascore, KeepUp, Ultimate A-League, Transfermarkt, API-Football: robots and terms only

Writes <out>/INVENTORY.md plus every response body, and appends the report to the run page.
Usage: python aleague/data/inventory.py --out aleague/cache/inventory
"""
import argparse
import io
import json
import os
import re
import time

import pandas as pd
import requests

UA = os.environ.get('ALEAGUE_UA', 'fk-model A-League research')
PAUSE = float(os.environ.get('PAUSE', '8'))

ROBOTS = ['www.football-data.co.uk', 'fbref.com', 'site.api.espn.com', 'www.espn.com.au', 'archive-api.open-meteo.com',
          'www.fotmob.com', 'www.sofascore.com', 'keepup.com.au', 'www.ultimatealeague.com', 'www.transfermarkt.com',
          'www.api-football.com']
TERMS = {
    'football-data.co.uk': 'https://www.football-data.co.uk/disclaimer.php',
    'Sports Reference (FBref) terms': 'https://www.sports-reference.com/termsofuse.html',
    'Sports Reference bot policy': 'https://www.sports-reference.com/bot-traffic.html',
    'Sports Reference data use': 'https://www.sports-reference.com/data_use.html',
    'ESPN (Disney) terms': 'https://disneytermsofuse.com/english/',
    'Open-Meteo terms': 'https://open-meteo.com/en/terms',
    'FotMob terms': 'https://www.fotmob.com/terms',
    'Sofascore terms': 'https://www.sofascore.com/terms-and-conditions',
    'KeepUp terms': 'https://keepup.com.au/terms-of-use',
    'Ultimate A-League home': 'https://www.ultimatealeague.com/',
    'Transfermarkt terms': 'https://www.transfermarkt.com/intern/anb',
    'API-Football terms': 'https://www.api-football.com/terms',
}
# lines in a terms page worth a human reading
TERMS_WORDS = re.compile(r'scrap|crawl|robot|automat|spider|harvest|data min|commercial|redistribut|bulk|'
                         r'personal use|non-commercial|bet|gambl', re.I)

FBREF = {
    'season list': 'https://fbref.com/en/comps/65/history/A-League-Men-Seasons',
    'fixtures 2025-26': 'https://fbref.com/en/comps/65/2025-2026/schedule/2025-2026-A-League-Men-Scores-and-Fixtures',
    'fixtures 2016-17': 'https://fbref.com/en/comps/65/2016-2017/schedule/2016-2017-A-League-Men-Scores-and-Fixtures',
}
ESPN = 'https://site.api.espn.com/apis/site/v2/sports/soccer/aus.1'


class Fetcher:
    def __init__(self, out):
        self.out = out
        self.s = requests.Session()
        self.s.headers['User-Agent'] = UA
        self.last = {}

    def get(self, url, name, **kw):
        host = re.sub(r'^https?://([^/]+).*', r'\1', url)
        wait = PAUSE - (time.time() - self.last.get(host, 0))
        if wait > 0:
            time.sleep(wait)
        try:
            r = self.s.get(url, timeout=45, **kw)
        except requests.RequestException as e:
            self.last[host] = time.time()
            print(f'{name}: FAILED {type(e).__name__}: {e}')
            return None
        self.last[host] = time.time()
        print(f'{name}: HTTP {r.status_code}, {len(r.content):,} bytes')
        with open(os.path.join(self.out, re.sub(r'[^A-Za-z0-9.-]+', '_', name)), 'wb') as fh:
            fh.write(r.content)
        return r


def robots_section(f):
    out = ['## robots.txt at pull time', '']
    for h in ROBOTS:
        r = f.get(f'https://{h}/robots.txt', f'robots {h}.txt')
        if r is None:
            out.append(f'**{h}**: no answer'); continue
        lines = [l for l in r.text.splitlines() if l.strip() and not l.startswith('#')]
        rel = [l for l in lines if re.match(r'(user-agent|disallow|allow|crawl-delay)', l.strip(), re.I)]
        out += [f'**{h}** (HTTP {r.status_code}, {len(lines)} lines; first 25 rules):', '```', *rel[:25], '```']
    return out + ['']


def terms_section(f):
    out = ['## Terms pages: lines that mention scraping, automated access, commercial use or betting', '']
    for name, url in TERMS.items():
        r = f.get(url, f'terms {name}.html')
        if r is None or r.status_code != 200:
            out.append(f'**{name}** ({url}): HTTP {getattr(r, "status_code", "no answer")}, not read'); out.append('')
            continue
        text = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', r.text, flags=re.S | re.I)
        text = re.sub(r'<[^>]+>', '\n', text)
        hits = []
        for line in (re.sub(r'\s+', ' ', l).strip() for l in text.splitlines()):
            if 20 < len(line) < 600 and TERMS_WORDS.search(line) and line not in hits:
                hits.append(line)
        out += [f'**{name}** ({url}): {len(hits)} relevant lines', *[f'> {h}' for h in hits[:12]], '']
    return out


def football_data(f):
    out = ['## football-data.co.uk: A-League results and odds', '']
    r = f.get('https://www.football-data.co.uk/new/AUS.csv', 'football-data AUS.csv')
    if r is None or r.status_code != 200:
        return out + [f'No file (HTTP {getattr(r, "status_code", "no answer")}).', '']
    df = pd.read_csv(io.BytesIO(r.content), encoding_errors='replace')
    out.append(f'{len(df):,} rows, {len(df.columns)} columns: `{", ".join(df.columns)}`')
    if 'Season' in df:
        counts = df.groupby('Season').size()
        out.append('Games per season: ' + ', '.join(f'{s} {n}' for s, n in counts.items()))
    odds = [c for c in df.columns if re.search(r'(H|D|A)$|Over|Under|AH', c) and c not in ('HG', 'AG')]
    filled = {c: f'{df[c].notna().mean():.0%}' for c in odds}
    out.append('Odds columns and how often each is filled: ' + ', '.join(f'{c} {v}' for c, v in filled.items()))
    out += ['', 'Last three rows:', '', df.tail(3).to_markdown(index=False), '']
    return out


def fbref(f):
    out = ['## FBref (A-League Men, comp 65)', '']
    report_url = None
    for name, url in FBREF.items():
        r = f.get(url, f'fbref {name}.html')
        if r is None or r.status_code != 200:
            out.append(f'- {name}: HTTP {getattr(r, "status_code", "no answer")}'); continue
        if name == 'season list':
            seasons = sorted(set(re.findall(r'/en/comps/65/(\d{4}-\d{4})/', r.text)))
            out.append(f'- season list: {len(seasons)} seasons, {seasons[:1]} to {seasons[-1:]}')
        else:
            reports = list(dict.fromkeys(re.findall(r'href="(/en/matches/[0-9a-f]{8}/[^"]+)"', r.text)))
            has_xg = 'data-stat="home_xg"' in r.text
            out.append(f'- {name}: {len(reports)} match report links; team xG column on fixtures: {has_xg}')
            if reports:
                report_url = report_url or ('https://fbref.com' + reports[0])
                if name == 'fixtures 2016-17':
                    report_url_old = 'https://fbref.com' + reports[0]
                    out += match_report(f, report_url_old, '2016-17')
    if report_url:
        out += match_report(f, report_url, '2025-26')
    return out + ['']


def match_report(f, url, label):
    r = f.get(url, f'fbref match report {label}.html')
    if r is None or r.status_code != 200:
        return [f'- match report {label}: HTTP {getattr(r, "status_code", "no answer")}']
    tables = sorted(set(re.findall(r'id="(stats_[0-9a-f]{8}_[a-z_]+)"', r.text)))
    stats = sorted(set(re.findall(r'data-stat="([a-z_0-9]+)"', r.text)))
    lineup = 'id="a"' in r.text or 'class="lineup"' in r.text
    return [f'- match report {label} ({url}): player tables {tables or "none"}; lineup block: {lineup}',
            f'  - columns seen: `{", ".join(stats)}`']


def espn(f):
    out = ['## ESPN public JSON (league aus.1)', '']
    first_event = None
    for d in ('20120114', '20160109', '20200111', '20260110'):
        r = f.get(f'{ESPN}/scoreboard?dates={d}', f'espn scoreboard {d}.json')
        if r is None or r.status_code != 200:
            out.append(f'- scoreboard {d}: HTTP {getattr(r, "status_code", "no answer")}'); continue
        evs = r.json().get('events', [])
        out.append(f'- scoreboard {d}: {len(evs)} games')
        if evs and d == '20260110':
            first_event = evs[0]['id']
        if evs and d == '20160109':
            old_event = evs[0]['id']
            out += espn_summary(f, old_event, '2016')
    if first_event:
        out += espn_summary(f, first_event, '2026')
    return out + ['']


def espn_summary(f, event, label):
    r = f.get(f'{ESPN}/summary?event={event}', f'espn summary {label}.json')
    if r is None or r.status_code != 200:
        return [f'- summary {label}: HTTP {getattr(r, "status_code", "no answer")}']
    j = r.json()
    rosters = j.get('rosters') or []
    players = [p for t in rosters for p in t.get('roster', [])]
    stat_names = sorted({s.get('name') for p in players for s in p.get('stats', [])})
    flags = sorted({k for p in players for k in p.keys()})
    team_stats = sorted({s.get('name') for t in (j.get('boxscore') or {}).get('teams', []) for s in t.get('statistics', [])})
    return [f'- summary {label} (event {event}): top-level keys `{", ".join(sorted(j.keys()))}`',
            f'  - {len(players)} players in rosters; player fields `{", ".join(flags)}`',
            f'  - player stats `{", ".join(stat_names)}`',
            f'  - team stats `{", ".join(team_stats)}`',
            f'  - game info: venue {bool((j.get("gameInfo") or {}).get("venue"))}, '
            f'attendance {(j.get("gameInfo") or {}).get("attendance")}, odds block {bool(j.get("odds") or j.get("pickcenter"))}']


def open_meteo(f):
    r = f.get('https://archive-api.open-meteo.com/v1/archive?latitude=-33.89&longitude=151.22&start_date=2026-01-10'
              '&end_date=2026-01-10&hourly=temperature_2m,precipitation,wind_speed_10m&timezone=Australia%2FSydney',
              'open-meteo sydney 2026-01-10.json')
    if r is None or r.status_code != 200:
        return ['## Open-Meteo', '', f'HTTP {getattr(r, "status_code", "no answer")}', '']
    h = r.json().get('hourly', {})
    return ['## Open-Meteo archive', '',
            f'Sydney 10 Jan 2026: {len(h.get("time", []))} hourly rows, fields {", ".join(k for k in h if k != "time")}; '
            f'rain that day {sum(x or 0 for x in h.get("precipitation", [])):.1f} mm', '']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    f = Fetcher(args.out)
    report = ['# A-League Men data inventory: what came back', '', f'User-Agent: `{UA}`; {PAUSE:.0f} s between calls to one host.', '']
    for part in (football_data, fbref, espn, open_meteo, terms_section, robots_section):
        try:
            report += part(f)
        except Exception as e:  # one source failing must not hide the others
            report += [f'## {part.__name__}: FAILED {type(e).__name__}: {e}', '']
    text = '\n'.join(report)
    open(os.path.join(args.out, 'INVENTORY.md'), 'w').write(text)
    print(text)
    summ = os.environ.get('GITHUB_STEP_SUMMARY')
    if summ:
        open(summ, 'a').write(text + '\n')


if __name__ == '__main__':
    main()
