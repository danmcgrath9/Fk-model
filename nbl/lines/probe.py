"""What does The Odds API actually hold for the NBL? A small, capped probe before any bulk pull.

Answers, each from a real response:
  1. coverage: on one Friday evening per season, 2020-21 to 2026-27, does the archive list NBL games,
     and does it hold head-to-head prices for them (which Australian books)
  2. team markets: head-to-head, line and total on a 2024-25 and a 2026-27 Friday
  3. props: points, rebounds, assists, threes and points+rebounds+assists on one 2025-26 game and one
     2026-27 game: which books, how many players each
  4. opening: on the 2026-27 game, how many days before the tip team markets and player points first appear
  5. half markets: first- and second-half totals and the first-half line on that game

Costs (the-odds-api.com/liveapi/guides/v4): /sports 0; historical events 1 (0 if empty); historical
odds and historical event odds 10 x markets x regions. The probe stops before any call that would take
it past MAX_CREDITS, reading the provider's own x-requests-used header after every call. Planned total
about 290 credits.

Env: ODDS_API_KEY (GitHub secret; never printed), MAX_CREDITS (default 300), OUT (default nbl/cache/odds_probe)
"""
import datetime as dt
import json
import os
import sys

import requests

BASE = 'https://api.the-odds-api.com/v4'
SPORT = 'basketball_nbl'
KEY = os.environ.get('ODDS_API_KEY', '')
MAX_CREDITS = int(os.environ.get('MAX_CREDITS', '300'))
OUT = os.environ.get('OUT', 'nbl/cache/odds_probe')

# Fridays at 08:00 UTC (6pm or 7pm in Melbourne), one per season. 2020-21 started in January 2021.
# The last two carry the full checks; the older ones only ask "are games and head-to-head prices held".
DATES = ['2021-02-12T08:00:00Z', '2021-12-10T08:00:00Z', '2022-11-11T08:00:00Z', '2023-11-10T08:00:00Z',
         '2024-11-08T08:00:00Z', '2025-11-07T08:00:00Z', '2026-10-16T08:00:00Z']
FULL_TEAM = {'2024-11-08', '2026-10-16'}
PROP_DATES = ('2025-11-07', '2026-10-16')
PROPS = ['player_points', 'player_rebounds', 'player_assists', 'player_threes', 'player_points_rebounds_assists']


class Budget:
    def __init__(self):
        self.start = None
        self.used = None
        self.calls = []

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


def market_books(games, market):
    """Book keys that price `market` in a list of games (historical odds 'data')."""
    return sorted({b['key'] for g in games for b in g.get('bookmakers', [])
                   for m in b.get('markets', []) if m.get('key') == market})


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


def first_game(d):
    ev = get(f'/historical/sports/{SPORT}/events', {'date': d}, f'events {d[:10]}', 1)
    games = (ev or {}).get('data') or []
    return games, (sorted(games, key=lambda x: x['commence_time'])[0] if games else None)


def main():
    if not KEY:
        sys.exit('ODDS_API_KEY is not set')
    os.makedirs(OUT, exist_ok=True)
    report = ['# The Odds API probe: NBL', '']

    sports = get('/sports', {'all': 'true'}, 'sports list', 0)
    nbl = [s for s in (sports or []) if s.get('key') == SPORT]
    report.append(f'Sport key `{SPORT}` listed: {"yes" if nbl else "NO"}' + (f' ({nbl[0].get("title")}, active {nbl[0].get("active")})' if nbl else ''))
    report.append('')

    # 1 and 2: coverage and team markets per date
    report += ['## Team markets, one Friday per season (snapshot 08:00 UTC)', '',
               '| date | games listed | snapshot | h2h books | line books | total books |', '|---|---|---|---|---|---|']
    picks = {}
    for d in DATES:
        games, g = first_game(d)
        if g:
            picks[d[:10]] = g
        if not games:
            report.append(f'| {d[:10]} | 0 | | | | |')
            continue
        full = d[:10] in FULL_TEAM
        mk = 'h2h,spreads,totals' if full else 'h2h'
        snap = get(f'/historical/sports/{SPORT}/odds', {'date': d, 'regions': 'au', 'markets': mk, 'oddsFormat': 'decimal'},
                   f'team {d[:10]}', 30 if full else 10)
        data = (snap or {}).get('data') or []
        cells = [', '.join(market_books(data, m)) or 'none' for m in ('h2h', 'spreads', 'totals')]
        if not full:
            cells[1] = cells[2] = 'not asked'
        report.append(f'| {d[:10]} | {len(games)} | {(snap or {}).get("timestamp", "")} | ' + ' | '.join(cells) + ' |')
    report.append('')

    # 3: props on one game in 2025-26 and one in 2026-27
    report += ['## Player props, first game after each snapshot', '', '| date | game | market | books (players each) | sample over |',
               '|---|---|---|---|---|']
    for day in PROP_DATES:
        g = picks.get(day)
        if not g:
            report.append(f'| {day} | no game listed | | | |')
            continue
        d = f'{day}T08:00:00Z'
        snap = get(f'/historical/sports/{SPORT}/events/{g["id"]}/odds',
                   {'date': d, 'regions': 'au', 'markets': ','.join(PROPS), 'oddsFormat': 'decimal'},
                   f'props {day}', 10 * len(PROPS))
        for mkt in PROPS:
            rows = summarise_props(snap, mkt)
            s = next((x[2] for x in rows if x[2]), None)
            sample = f'{s["description"]} {s["point"]} @ {s["price"]}' if s else ''
            report.append(f'| {day} | {g["away_team"]} at {g["home_team"]} | {mkt} | '
                          f'{", ".join(f"{b} ({n})" for b, n, _ in rows) or "none"} | {sample} |')
    report.append('')

    # 4: when do lines open? step back from the tip on the 2026-27 game
    g = picks.get('2026-10-16')
    if g:
        start = dt.datetime.fromisoformat(g['commence_time'].replace('Z', '+00:00'))
        report += [f'## When lines first appear: {g["away_team"]} at {g["home_team"]}, tip {g["commence_time"]}', '',
                   '| days before the tip | h2h books | player_points books (players each) |', '|---|---|---|']
        for days in (4, 2, 1):
            t = (start - dt.timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%SZ')
            team = get(f'/historical/sports/{SPORT}/events/{g["id"]}/odds',
                       {'date': t, 'regions': 'au', 'markets': 'h2h', 'oddsFormat': 'decimal'}, f'open h2h -{days}d', 10)
            tb = sorted({b['key'] for b in ((team or {}).get('data') or {}).get('bookmakers', [])})
            pp = 'not asked'
            if days <= 2:
                snap = get(f'/historical/sports/{SPORT}/events/{g["id"]}/odds',
                           {'date': t, 'regions': 'au', 'markets': 'player_points', 'oddsFormat': 'decimal'},
                           f'open points -{days}d', 10)
                pp = ', '.join(f'{b} ({n})' for b, n, _ in summarise_props(snap, 'player_points')) or 'none'
            report.append(f'| {days} | {", ".join(tb) or "none"} | {pp} |')
        report.append('')

    # 5: half markets (Voulgaris angle, nbl/docs/RESEARCH.md): do AU books post NBL first- and second-half lines?
    g = picks.get('2026-10-16')
    if g:
        half = ['totals_h1', 'totals_h2', 'spreads_h1']
        snap = get(f'/historical/sports/{SPORT}/events/{g["id"]}/odds',
                   {'date': '2026-10-16T08:00:00Z', 'regions': 'au', 'markets': ','.join(half), 'oddsFormat': 'decimal'},
                   'half markets 2026-10-16', 10 * len(half))
        data = (snap or {}).get('data') or {}
        report += ['## Half markets, same 2026 game', '', '| market | books | sample |', '|---|---|---|']
        for mk in half:
            books = [(b['key'], m) for b in data.get('bookmakers', []) for m in b.get('markets', []) if m.get('key') == mk]
            smp = books[0][1]['outcomes'][0] if books and books[0][1].get('outcomes') else None
            report.append(f'| {mk} | {", ".join(b for b, _ in books) or "none"} | '
                          f'{(smp.get("name", "") + " " + str(smp.get("point", "")) + " @ " + str(smp.get("price", ""))) if smp else ""} |')
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
