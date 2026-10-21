"""What does The Odds API actually hold for NRL? A small, capped probe before any bulk pull.

Answers, each from a real response, most important first (the cap may stop the tail):
  1. sport key, and which seasons the archive lists NRL games for (one events call per season)
  2. which markets exist per game: the event-markets endpoint (1 credit) where the archive serves it,
     otherwise a request for the candidate try-scorer keys on one 2025 game
  3. try-scorer lines on one game per season 2023-2026: which AU books, how many players
  4. every prop market found, on one 2025 game
  5. when lines open: head-to-head and anytime try scorer on one 2025 game, from six days out
     to two hours before kick-off (team lists are named on the Tuesday)
  6. team markets: h2h, line and total for a whole 2025 round; h2h on one 2020 game (how far back)

Costs (the-odds-api.com/liveapi/guides/v4): historical events 1 (0 if empty); historical odds and
historical event odds 10 x markets x regions. Every call is checked against MAX_CREDITS at its
worst-case cost first, and the spend is read from the provider's x-requests-used header after it.

Env: ODDS_API_KEY (GitHub secret; never printed), MAX_CREDITS (default 300), OUT (default nrl/cache/odds_probe)
"""
import datetime as dt
import json
import os
import sys

import requests

BASE = 'https://api.the-odds-api.com/v4'
KEY = os.environ.get('ODDS_API_KEY', '')
MAX_CREDITS = int(os.environ.get('MAX_CREDITS', '300'))
OUT = os.environ.get('OUT', 'nrl/cache/odds_probe')

# Wednesday 08:00 UTC = 6pm Sydney: after Tuesday's team lists, before the round starts.
SEASON_DATES = ['2020-07-15T08:00:00Z', '2021-06-16T08:00:00Z', '2022-06-15T08:00:00Z', '2023-06-14T08:00:00Z',
                '2024-06-12T08:00:00Z', '2025-06-11T08:00:00Z', '2026-06-10T08:00:00Z']
PROP_SEASONS = ['2023-06-14T08:00:00Z', '2024-06-12T08:00:00Z', '2025-06-11T08:00:00Z', '2026-06-10T08:00:00Z']
REF_DATE = '2025-06-11T08:00:00Z'
# Candidate keys, tried only if the markets endpoint cannot tell us; a key that does not exist costs nothing.
CANDIDATE_PROPS = ['player_try_scorer_anytime', 'player_try_scorer_first', 'player_try_scorer_last',
                   'player_try_scorer_over']
TRY_KEY = 'player_try_scorer_anytime'


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
    print(f'{label}: HTTP {r.status_code}, cost {r.headers.get("x-requests-last")}, remaining {r.headers.get("x-requests-remaining")}')
    if r.status_code != 200:
        print(f'  body: {r.text[:300]}')
        return None
    body = r.json()
    with open(os.path.join(OUT, label.replace(' ', '_').replace(':', '') + '.json'), 'w') as fh:
        json.dump(body, fh)
    return body


def market_rows(snap, market):
    """(book, players, sample outcome) for one market in one event snapshot."""
    data = (snap or {}).get('data') or {}
    rows = []
    for bk in data.get('bookmakers', []):
        for mk in bk.get('markets', []):
            if mk.get('key') != market:
                continue
            outs = mk.get('outcomes', [])
            players = {o.get('description') or o.get('name') for o in outs}
            rows.append((bk.get('key'), len(players), outs[0] if outs else None))
    return rows


def markets_in(snap):
    data = (snap or {}).get('data') or {}
    return sorted({mk.get('key') for bk in data.get('bookmakers', []) for mk in bk.get('markets', [])})


def fmt_books(rows):
    return ', '.join(f'{b} ({n})' for b, n, _ in rows) or 'none'


def fmt_sample(rows):
    s = next((x[2] for x in rows if x[2]), None)
    if not s:
        return ''
    who = s.get('description') or ''
    return f'{who} {s.get("name", "")} {s.get("point", "")} @ {s.get("price")}'.replace('  ', ' ').strip()


def first_game(sport, date):
    ev = get(f'/historical/sports/{sport}/events', {'date': date}, f'events {date[:10]}', 1)
    games = (ev or {}).get('data') or []
    return games, (sorted(games, key=lambda x: x['commence_time'])[0] if games else None)


def main():
    if not KEY:
        sys.exit('ODDS_API_KEY is not set')
    os.makedirs(OUT, exist_ok=True)
    report = ['# The Odds API probe: NRL', '']

    # 1. sport key and seasons
    sports = get('/sports', {'all': 'true'}, 'sports list', 0) or []
    league = [s for s in sports if 'rugbyleague' in s.get('key', '') or 'NRL' in s.get('title', '')]
    report.append('Rugby league keys listed: ' + (', '.join(f'`{s["key"]}` ({s.get("title")}, active {s.get("active")})'
                                                           for s in league) or 'NONE'))
    sport = next((s['key'] for s in league if s['key'] == 'rugbyleague_nrl'), None) or \
        next((s['key'] for s in league if 'nrl' in s['key'] and 'state' not in s['key']), None)
    if not sport:
        report.append('No NRL key found; stopping.')
        return finish(report)
    report += [f'Using `{sport}`.', '', '## Games the archive lists, one Wednesday 6pm Sydney per season', '',
               '| date | games listed | first game | kick-off |', '|---|---|---|---|']
    games_by_date = {}
    for d in SEASON_DATES:
        games, g = first_game(sport, d)
        games_by_date[d] = (games, g)
        report.append(f'| {d[:10]} | {len(games)} | {g["away_team"] + " at " + g["home_team"] if g else ""} | '
                      f'{g["commence_time"] if g else ""} |')
    report.append('')

    ref_games, ref = games_by_date.get(REF_DATE, ([], None))

    # 2. which markets exist
    found = []
    report += ['## Which markets exist per game', '']
    for d in PROP_SEASONS:
        g = games_by_date.get(d, ([], None))[1]
        if not g:
            continue
        mk = get(f'/historical/sports/{sport}/events/{g["id"]}/markets', {'date': d, 'regions': 'au'},
                 f'markets {d[:10]}', 10)
        books = ((mk or {}).get('data') or {}).get('bookmakers', [])
        if mk is None:
            report.append(f'- {d[:10]}: the historical markets endpoint did not answer (see log)')
            continue
        keys = sorted({m.get('key') for b in books for m in b.get('markets', [])})
        found = sorted(set(found) | set(keys))
        report.append(f'- {d[:10]} {g["away_team"]} at {g["home_team"]}: {len(books)} books; markets: '
                      + (', '.join(f'`{k}`' for k in keys) or 'none'))
    report.append('')
    props = [k for k in found if k.startswith('player_')]
    if not found and ref:
        # the markets endpoint did not help: ask for the candidates directly on the reference game
        snap = get(f'/historical/sports/{sport}/events/{ref["id"]}/odds',
                   {'date': REF_DATE, 'regions': 'au', 'markets': ','.join(CANDIDATE_PROPS), 'oddsFormat': 'decimal'},
                   'candidate props 2025', 10 * len(CANDIDATE_PROPS))
        props = markets_in(snap)
        report += ['Markets endpoint unavailable; candidate keys requested on the 2025 game. Returned: '
                   + (', '.join(f'`{k}`' for k in props) or 'none'), '']
    try_key = TRY_KEY if TRY_KEY in props or not props else next((k for k in props if 'anytime' in k), props[0])

    # 3. anytime try scorer per season
    report += [f'## `{try_key}` on one game per season (Wednesday 6pm Sydney snapshot)', '',
               '| date | game | snapshot | books (players each) | sample |', '|---|---|---|---|---|']
    for d in PROP_SEASONS:
        g = games_by_date.get(d, ([], None))[1]
        if not g:
            report.append(f'| {d[:10]} | no game | | | |')
            continue
        snap = get(f'/historical/sports/{sport}/events/{g["id"]}/odds',
                   {'date': d, 'regions': 'au', 'markets': try_key, 'oddsFormat': 'decimal'}, f'try {d[:10]}', 10)
        rows = market_rows(snap, try_key)
        report.append(f'| {d[:10]} | {g["away_team"]} at {g["home_team"]} | {(snap or {}).get("timestamp", "")} | '
                      f'{fmt_books(rows)} | {fmt_sample(rows)} |')
    report.append('')

    # 4. every prop market found, on the 2025 game
    others = [k for k in props if k != try_key][:6]
    if ref and others:
        snap = get(f'/historical/sports/{sport}/events/{ref["id"]}/odds',
                   {'date': REF_DATE, 'regions': 'au', 'markets': ','.join(others), 'oddsFormat': 'decimal'},
                   'other props 2025', 10 * len(others))
        report += [f'## Other prop markets, {ref["away_team"]} at {ref["home_team"]}', '',
                   '| market | books (players each) | sample |', '|---|---|---|']
        for k in others:
            rows = market_rows(snap, k)
            report.append(f'| `{k}` | {fmt_books(rows)} | {fmt_sample(rows)} |')
        report.append('')

    # 5. when do lines open
    if ref:
        start = dt.datetime.fromisoformat(ref['commence_time'].replace('Z', '+00:00'))
        report += [f'## When lines appear: {ref["away_team"]} at {ref["home_team"]}, kick-off {ref["commence_time"]}', '',
                   '| before kick-off | snapshot | h2h books | try-scorer books (players each) |', '|---|---|---|---|']
        for label, delta in (('6 days', dt.timedelta(days=6)), ('4 days', dt.timedelta(days=4)),
                             ('3 days', dt.timedelta(days=3)), ('2 days', dt.timedelta(days=2)),
                             ('1 day', dt.timedelta(days=1)), ('2 hours', dt.timedelta(hours=2))):
            t = (start - delta).strftime('%Y-%m-%dT%H:%M:%SZ')
            snap = get(f'/historical/sports/{sport}/events/{ref["id"]}/odds',
                       {'date': t, 'regions': 'au', 'markets': f'h2h,{try_key}', 'oddsFormat': 'decimal'},
                       f'opening {label}', 20)
            h2h = market_rows(snap, 'h2h')
            report.append(f'| {label} | {(snap or {}).get("timestamp", "no snapshot")} | {len(h2h)} | '
                          f'{fmt_books(market_rows(snap, try_key))} |')
        report.append('')

    # 6. team markets
    snap = get(f'/historical/sports/{sport}/odds', {'date': REF_DATE, 'regions': 'au', 'markets': 'h2h,spreads,totals',
                                                    'oddsFormat': 'decimal'}, 'team markets 2025', 30)
    data = (snap or {}).get('data') or []
    if snap is not None:
        report += ['## Team markets, whole round, 2025-06-11 snapshot', '',
                   f'{len(data)} games. Per game: ' + '; '.join(
                       f'{x["home_team"]}: {len(x.get("bookmakers", []))} books, '
                       + '/'.join(sorted({m["key"] for b in x.get("bookmakers", []) for m in b.get("markets", [])}))
                       for x in data), '']
        if data:
            report += ['Books: ' + ', '.join(sorted({b['key'] for x in data for b in x.get('bookmakers', [])})), '']
    g2020 = games_by_date.get(SEASON_DATES[0], ([], None))[1]
    if g2020:
        snap = get(f'/historical/sports/{sport}/events/{g2020["id"]}/odds',
                   {'date': SEASON_DATES[0], 'regions': 'au', 'markets': 'h2h', 'oddsFormat': 'decimal'}, 'h2h 2020', 10)
        report += [f'2020 check, {g2020["away_team"]} at {g2020["home_team"]}: h2h from '
                   f'{fmt_books(market_rows(snap, "h2h"))}', '']
    return finish(report)


def finish(report):
    report += [f'**Credits spent this probe: {budget.spent}** (cap {MAX_CREDITS}); remaining on the plan: '
               f'{budget.calls[-1]["remaining"] if budget.calls else "unknown"}.', '',
               '| call | HTTP | credits |', '|---|---|---|',
               *[f'| {c["label"]} | {c["status"]} | {c["cost"]} |' for c in budget.calls], '']
    text = '\n'.join(report)
    open(os.path.join(OUT, 'PROBE.md'), 'w').write(text)
    print(text)
    summ = os.environ.get('GITHUB_STEP_SUMMARY')
    if summ:
        open(summ, 'a').write(text + '\n')


if __name__ == '__main__':
    main()
