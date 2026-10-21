"""What does The Odds API actually hold for A-League Men? A small, capped probe before any bulk pull.

Answers, each from a real response:
  1. sport key: is soccer_australia_aleague listed, and is it in season now
  2. markets now: for the next few games, which market keys each Australian book posts today
     (the event-markets endpoint, 1 credit a game), so no prop is assumed to exist
  3. coverage: on one date in each season 2020-21 to 2025-26, does the archive list A-League games
  4. team markets: head-to-head (three-way), line and total for a round in three seasons, which books
  5. props and extra markets in the archive: the keys found in step 2, on one 2025-26 game
  6. opening: on one 2025-26 game, how many days before kick-off head-to-head prices first appear

Costs (the-odds-api.com/liveapi/guides/v4): events list 0 live, 1 historical (0 if empty); event
markets 1; odds and event odds 10 x markets x regions (live is 1 per market per region). The probe
stops before any call that would take it past MAX_CREDITS, reading the provider's own
x-requests-used header after every call, and spends in priority order so a cut-off loses the least.

Env: ODDS_API_KEY (GitHub secret; never printed), MAX_CREDITS (default 300), OUT (default aleague/cache/odds_probe)
"""
import datetime as dt
import json
import os
import sys

import requests

BASE = 'https://api.the-odds-api.com/v4'
SPORT = 'soccer_australia_aleague'
KEY = os.environ.get('ODDS_API_KEY', '')
MAX_CREDITS = int(os.environ.get('MAX_CREDITS', '300'))
OUT = os.environ.get('OUT', 'aleague/cache/odds_probe')

# One mid-season date per season (00:00 UTC Thursday = 11am Sydney, before a weekend round), plus the
# July 2020 hub restart of 2019-20 to find where the archive starts.
COVERAGE_DATES = ['2020-07-16T00:00:00Z', '2021-02-11T00:00:00Z', '2022-01-13T00:00:00Z', '2023-01-12T00:00:00Z',
                  '2024-01-11T00:00:00Z', '2025-01-09T00:00:00Z', '2026-01-08T00:00:00Z']
# Team markets for a whole round: one early, one middle, one recent season
ROUND_DATES = ['2021-02-11T00:00:00Z', '2023-11-09T00:00:00Z', '2025-11-13T00:00:00Z']
# Anything a soccer book might post, in case today's markets list comes back empty or the endpoint is missing.
# Only used for the archive check if step 2 found nothing; each key costs 10.
FALLBACK_KEYS = ['btts', 'player_goal_scorer_anytime']
SOCCER_TEAM_KEYS = {'h2h', 'spreads', 'totals'}


class Budget:
    def __init__(self):
        self.start = None
        self.used = None
        self.calls = []

    @property
    def spent(self):
        return 0 if self.start is None else self.used - self.start

    def can(self, cost):
        return self.spent + cost <= MAX_CREDITS

    def note(self, resp, label):
        used = resp.headers.get('x-requests-used')
        if used is not None:
            used = int(float(used))
            last = int(float(resp.headers.get('x-requests-last', 0) or 0))
            if self.start is None:
                self.start = used - last
            self.used = used
        self.calls.append(dict(label=label, status=resp.status_code, cost=resp.headers.get('x-requests-last'),
                               remaining=resp.headers.get('x-requests-remaining')))


budget = Budget()


def get(path, params, label, cost):
    if not budget.can(cost):
        print(f'SKIPPED {label}: would pass the {MAX_CREDITS}-credit cap (spent {budget.spent})')
        return None
    r = requests.get(f'{BASE}{path}', params={**params, 'apiKey': KEY}, timeout=60)
    budget.note(r, label)
    # never echo the URL: it carries the key
    print(f'{label}: HTTP {r.status_code}, cost {r.headers.get("x-requests-last")}, '
          f'remaining {r.headers.get("x-requests-remaining")}')
    if r.status_code != 200:
        print(f'  body: {r.text[:300]}')
        return None
    body = r.json()
    with open(os.path.join(OUT, label.replace(' ', '_').replace(':', '') + '.json'), 'w') as fh:
        json.dump(body, fh)
    return body


def market_rows(bookmakers, market):
    """(book, outcomes, players) for one market across a list of bookmakers."""
    rows = []
    for bk in bookmakers or []:
        for mk in bk.get('markets', []):
            if mk.get('key') != market:
                continue
            outs = mk.get('outcomes', [])
            players = {o.get('description') for o in outs if o.get('description')}
            rows.append((bk.get('key'), len(outs), len(players)))
    return rows


def main():
    if not KEY:
        sys.exit('ODDS_API_KEY is not set')
    os.makedirs(OUT, exist_ok=True)
    report = ['# The Odds API probe: A-League Men', '']

    # 1. sport key (free)
    sports = get('/sports', {'all': 'true'}, 'sports list', 0)
    soccer_au = [s for s in (sports or []) if s.get('key', '').startswith('soccer_australia')]
    report.append('Australian soccer keys listed: ' + (', '.join(f'`{s["key"]}` ({s.get("title")}, active {s.get("active")})'
                                                         for s in soccer_au) or 'NONE'))
    report.append('')

    # 2. markets each AU book posts now (events list is free live; markets 1 a game)
    upcoming = get(f'/sports/{SPORT}/events', {}, 'events now', 0) or []
    upcoming = sorted(upcoming, key=lambda x: x['commence_time'])[:3]
    found_keys = set()
    report += ['## Markets Australian books post today (next games)', '',
               '| game | kick-off (UTC) | book | market keys |', '|---|---|---|---|']
    for g in upcoming:
        mk = get(f'/sports/{SPORT}/events/{g["id"]}/markets', {'regions': 'au'}, f'markets now {g["id"][:8]}', 1)
        books = (mk or {}).get('bookmakers', [])
        if not books:
            report.append(f'| {g["away_team"]} at {g["home_team"]} | {g["commence_time"]} | none | |')
        for bk in books:
            keys = sorted(m['key'] for m in bk.get('markets', []))
            found_keys.update(keys)
            report.append(f'| {g["away_team"]} at {g["home_team"]} | {g["commence_time"]} | {bk["key"]} | {", ".join(keys)} |')
    report += ['', 'All keys seen today: ' + (', '.join(f'`{k}`' for k in sorted(found_keys)) or 'none'), '']

    # 3. archive coverage by season (1 each, 0 if empty)
    report += ['## Archive coverage, one date per season', '', '| date | games listed | first game |', '|---|---|---|']
    games_by_date = {}
    for d in COVERAGE_DATES:
        ev = get(f'/historical/sports/{SPORT}/events', {'date': d}, f'events {d[:10]}', 1)
        games = sorted((ev or {}).get('data') or [], key=lambda x: x['commence_time'])
        games_by_date[d] = games
        first = f'{games[0]["away_team"]} at {games[0]["home_team"]}, {games[0]["commence_time"]}' if games else ''
        report.append(f'| {d[:10]} | {len(games)} | {first} |')
    report.append('')

    # 4. team markets for a round, three seasons (30 each)
    report += ['## Team markets (head-to-head, line, total), whole-round snapshots', '',
               '| snapshot | games | books per game | books | h2h outcomes | line points seen | total points seen |',
               '|---|---|---|---|---|---|---|']
    for d in ROUND_DATES:
        snap = get(f'/historical/sports/{SPORT}/odds', {'date': d, 'regions': 'au', 'markets': 'h2h,spreads,totals',
                                                        'oddsFormat': 'decimal'}, f'team markets {d[:10]}', 30)
        data = (snap or {}).get('data') or []
        books = sorted({b['key'] for x in data for b in x.get('bookmakers', [])})
        h2h_outs = sorted({len(m['outcomes']) for x in data for b in x.get('bookmakers', []) for m in b['markets']
                           if m['key'] == 'h2h'})
        spreads = sorted({o.get('point') for x in data for b in x.get('bookmakers', []) for m in b['markets']
                          if m['key'] == 'spreads' for o in m['outcomes']}, key=lambda p: (p is None, p))
        totals = sorted({o.get('point') for x in data for b in x.get('bookmakers', []) for m in b['markets']
                         if m['key'] == 'totals' for o in m['outcomes']}, key=lambda p: (p is None, p))
        report.append(f'| {(snap or {}).get("timestamp", d)} | {len(data)} | '
                      f'{", ".join(str(len(x.get("bookmakers", []))) for x in data)} | {", ".join(books)} | '
                      f'{h2h_outs} | {spreads[:12]} | {totals[:12]} |')
    report.append('')

    # 5 and 6 on one 2025-26 game
    pool = games_by_date.get('2026-01-08T00:00:00Z') or games_by_date.get('2025-01-09T00:00:00Z') or []
    if pool:
        g = pool[0]
        start = dt.datetime.fromisoformat(g['commence_time'].replace('Z', '+00:00'))
        report += [f'## One archived game: {g["away_team"]} at {g["home_team"]}, kick-off {g["commence_time"]}', '']

        # 5. the extra keys found today, in the archive, 3 hours before kick-off (10 per key)
        extra = sorted(found_keys - SOCCER_TEAM_KEYS) or FALLBACK_KEYS
        affordable = max(0, (MAX_CREDITS - budget.spent - 40) // 10)  # keep 40 for step 6
        keys = extra[:affordable]
        if len(keys) < len(extra):
            report.append(f'Not checked in the archive for lack of budget: {", ".join(extra[len(keys):])}')
        t = (start - dt.timedelta(hours=3)).strftime('%Y-%m-%dT%H:%M:%SZ')
        if keys:
            snap = get(f'/historical/sports/{SPORT}/events/{g["id"]}/odds',
                       {'date': t, 'regions': 'au', 'markets': ','.join(keys), 'oddsFormat': 'decimal'},
                       'extra markets archive', 10 * len(keys))
            report += ['', f'Snapshot {(snap or {}).get("timestamp", "none")}, 3 hours before kick-off:', '',
                       '| market | books (outcomes, players each) |', '|---|---|']
            for k in keys:
                rows = market_rows(((snap or {}).get('data') or {}).get('bookmakers'), k)
                report.append(f'| {k} | {", ".join(f"{b} ({o}, {p})" for b, o, p in rows) or "none"} |')
            report.append('')

        # 6. when do head-to-head prices first appear (10 each)
        report += ['| days before kick-off | snapshot | books with head-to-head |', '|---|---|---|']
        for days in (10, 7, 4, 2):
            t = (start - dt.timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%SZ')
            snap = get(f'/historical/sports/{SPORT}/events/{g["id"]}/odds',
                       {'date': t, 'regions': 'au', 'markets': 'h2h', 'oddsFormat': 'decimal'}, f'opening -{days}d', 10)
            rows = market_rows(((snap or {}).get('data') or {}).get('bookmakers'), 'h2h')
            report.append(f'| {days} | {(snap or {}).get("timestamp", "no snapshot")} | '
                          f'{", ".join(b for b, _, _ in rows) or "none"} |')
        report.append('')

    report += [f'**Credits spent this probe: {budget.spent}** (cap {MAX_CREDITS}); remaining on the plan: '
               f'{budget.calls[-1]["remaining"] if budget.calls else "unknown"}.', '']
    text = '\n'.join(report)
    open(os.path.join(OUT, 'PROBE.md'), 'w').write(text)
    print(text)
    summ = os.environ.get('GITHUB_STEP_SUMMARY')
    if summ:
        open(summ, 'a').write(text + '\n')


if __name__ == '__main__':
    main()
