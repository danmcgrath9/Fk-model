"""What does The Odds API actually hold for AFL? A small, capped probe before any bulk pull.

Answers, each from a real response:
  1. coverage: on dates through 2023-2026, does the archive list AFL games?
  2. disposals: for one game per date, which Australian books post disposal lines, for how many players
  3. other props: goals, marks, tackles on one 2025 game
  4. opening: on one 2025 game, how many days before the bounce do disposal lines first appear
  5. team markets: head-to-head, line and total for a 2025 round

Costs (the-odds-api.com/liveapi/guides/v4): historical events 1 (0 if empty); historical odds and
historical event odds 10 x markets x regions. The probe stops before any call that would take it past
MAX_CREDITS, reading the provider's own x-requests-used header after every call.

Env: ODDS_API_KEY (GitHub secret; never printed), MAX_CREDITS (default 300), OUT (default afl/cache/odds_probe)
"""
import datetime as dt
import json
import os
import sys

import requests

BASE = 'https://api.the-odds-api.com/v4'
SPORT = 'aussierules_afl'
KEY = os.environ.get('ODDS_API_KEY', '')
MAX_CREDITS = int(os.environ.get('MAX_CREDITS', '300'))
OUT = os.environ.get('OUT', 'afl/cache/odds_probe')

# Thursday 08:00 UTC = 6pm in Melbourne, after teams are named, early and late in each season
DATES = ['2023-05-11T08:00:00Z', '2023-08-10T08:00:00Z', '2024-05-09T08:00:00Z', '2024-08-08T08:00:00Z',
         '2025-05-08T08:00:00Z', '2025-08-07T08:00:00Z', '2026-05-07T08:00:00Z', '2026-08-06T08:00:00Z']
OTHER_PROPS = ['player_goals_scored_over', 'player_marks_over', 'player_tackles_over', 'player_disposals_over']


class Budget:
    def __init__(self):
        self.start = None
        self.used = None
        self.calls = []

    def can(self, cost):
        spent = 0 if self.start is None else self.used - self.start
        return spent + cost <= MAX_CREDITS

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

    @property
    def spent(self):
        return 0 if self.start is None else self.used - self.start


budget = Budget()


def get(path, params, label, cost):
    if not budget.can(cost):
        print(f'SKIPPED {label}: would pass the {MAX_CREDITS}-credit cap (spent {budget.spent})')
        return None
    r = requests.get(f'{BASE}{path}', params={**params, 'apiKey': KEY}, timeout=60)
    budget.note(r, label)
    # never echo the URL: it carries the key
    print(f'{label}: HTTP {r.status_code}, cost {r.headers.get("x-requests-last")}, remaining {r.headers.get("x-requests-remaining")}')
    if r.status_code != 200:
        print(f'  body: {r.text[:300]}')
        return None
    body = r.json()
    with open(os.path.join(OUT, label.replace(' ', '_').replace(':', '') + '.json'), 'w') as fh:
        json.dump(body, fh)
    return body


def summarise_props(snap, market):
    """Books, players and a sample line for one market in one event snapshot."""
    data = (snap or {}).get('data') or {}
    rows = []
    for bk in data.get('bookmakers', []):
        for mk in bk.get('markets', []):
            if mk.get('key') != market:
                continue
            players = {o.get('description') for o in mk.get('outcomes', [])}
            sample = next((o for o in mk.get('outcomes', []) if o.get('name') == 'Over'), None)
            rows.append((bk.get('key'), len(players), sample))
    return rows


def main():
    if not KEY:
        sys.exit('ODDS_API_KEY is not set')
    os.makedirs(OUT, exist_ok=True)
    report = ['# The Odds API probe: AFL', '']

    sports = get('/sports', {'all': 'true'}, 'sports list', 0)
    afl = [s for s in (sports or []) if s.get('key') == SPORT]
    report.append(f'Sport key `{SPORT}` listed: {"yes" if afl else "NO"}' + (f' ({afl[0].get("title")})' if afl else ''))
    report.append('')

    # 1 and 2: coverage and disposals per date
    report += ['## Disposal lines, one game per date (snapshot Thursday 6pm Melbourne)', '',
               '| date | games listed | game | snapshot | books with disposal lines (players each) | sample over |',
               '|---|---|---|---|---|---|']
    first_2025 = None
    for d in DATES:
        ev = get(f'/historical/sports/{SPORT}/events', {'date': d}, f'events {d[:10]}', 1)
        games = (ev or {}).get('data') or []
        if not games:
            report.append(f'| {d[:10]} | 0 | | | | |')
            continue
        g = sorted(games, key=lambda x: x['commence_time'])[0]
        if d.startswith('2025-08'):
            first_2025 = g
        snap = get(f'/historical/sports/{SPORT}/events/{g["id"]}/odds',
                   {'date': d, 'regions': 'au', 'markets': 'player_disposals', 'oddsFormat': 'decimal'},
                   f'disposals {d[:10]}', 10)
        rows = summarise_props(snap, 'player_disposals')
        books = ', '.join(f'{b} ({n})' for b, n, _ in rows) or 'none'
        s = next((x[2] for x in rows if x[2]), None)
        sample = f'{s["description"]} {s["point"]} @ {s["price"]}' if s else ''
        report.append(f'| {d[:10]} | {len(games)} | {g["away_team"]} at {g["home_team"]} | {(snap or {}).get("timestamp", "")} | {books} | {sample} |')
    report.append('')

    if first_2025:
        g, d = first_2025, '2025-08-07T08:00:00Z'
        # 3: other prop markets on the same game
        snap = get(f'/historical/sports/{SPORT}/events/{g["id"]}/odds',
                   {'date': d, 'regions': 'au', 'markets': ','.join(OTHER_PROPS), 'oddsFormat': 'decimal'},
                   'other props 2025-08-07', 10 * len(OTHER_PROPS))
        report += ['## Other prop markets, same 2025 game', '', '| market | books (players each) |', '|---|---|']
        for mkt in OTHER_PROPS:
            rows = summarise_props(snap, mkt)
            report.append(f'| {mkt} | {", ".join(f"{b} ({n})" for b, n, _ in rows) or "none"} |')
        report.append('')

        # 4: when do disposal lines open? step back from the bounce
        start = dt.datetime.fromisoformat(g['commence_time'].replace('Z', '+00:00'))
        report += [f'## When disposal lines first appear: {g["away_team"]} at {g["home_team"]}, bounce {g["commence_time"]}', '',
                   '| days before the bounce | snapshot | books with lines (players each) |', '|---|---|---|']
        for days in (5, 4, 3, 2, 1):
            t = (start - dt.timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%SZ')
            snap = get(f'/historical/sports/{SPORT}/events/{g["id"]}/odds',
                       {'date': t, 'regions': 'au', 'markets': 'player_disposals', 'oddsFormat': 'decimal'},
                       f'opening -{days}d', 10)
            rows = summarise_props(snap, 'player_disposals')
            report.append(f'| {days} | {(snap or {}).get("timestamp", "no snapshot")} | {", ".join(f"{b} ({n})" for b, n, _ in rows) or "none"} |')
        report.append('')

        # 5: team markets for the round
        snap = get(f'/historical/sports/{SPORT}/odds', {'date': d, 'regions': 'au', 'markets': 'h2h,spreads,totals',
                                                        'oddsFormat': 'decimal'}, 'team markets 2025-08-07', 30)
        data = (snap or {}).get('data') or []
        report += ['## Team markets, 2025-08-07 snapshot', '',
                   f'{len(data)} games; books per game: ' + ', '.join(str(len(x.get('bookmakers', []))) for x in data), '']
        if data:
            keys = sorted({b['key'] for x in data for b in x.get('bookmakers', [])})
            report.append('Books: ' + ', '.join(keys))
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
