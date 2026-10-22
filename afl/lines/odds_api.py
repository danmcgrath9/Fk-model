"""The Odds API: historical AFL lines, pulled once, capped, resumable.

Endpoints and costs from the provider's v4 docs (the-odds-api.com/liveapi/guides/v4):
  GET /v4/historical/sports/{sport}/events?date=           1 credit (0 if empty)
  GET /v4/historical/sports/{sport}/events/{id}/odds?date=  10 x markets x regions (props: from 2023-05-03)
  GET /v4/historical/sports/{sport}/odds?date=              10 x markets x regions (featured markets, all games at once)
Snapshots every 5 minutes; a date returns the closest snapshot at or before it. Every response is saved under
afl/cache/lines/raw/, and a call whose file exists is never made again. A plan is priced in credits before it runs
(--dry-run needs no key), and the run stops before any call that would pass MAX_CREDITS.

Usage:
  python -m afl.lines.odds_api --dry-run                       # price the default plan, no calls
  python -m afl.lines.odds_api --seasons 2025 --max-credits 5000
"""
import argparse
import datetime as dt
import json
import os
import sys

import pandas as pd

BASE = 'https://api.the-odds-api.com/v4'
SPORT = 'aussierules_afl'
PROPS = ['player_disposals', 'player_marks_over', 'player_tackles_over', 'player_goals_scored_over']
TEAM_MARKETS = ['h2h', 'spreads', 'totals']
# hours before the bounce at which each game's props are snapshotted; the earliest one with lines is the opener
OFFSETS_H = [120, 72, 48, 30, 12, 3, 0.25]
RAW = 'afl/cache/lines/raw'
PROPS_START = dt.datetime(2023, 5, 3, 6, tzinfo=dt.timezone.utc)


def iso(t):
    return t.astimezone(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


class Client:
    def __init__(self, key, max_credits, dry_run=False):
        self.key, self.max, self.dry = key, max_credits, dry_run
        self.start_used = None
        self.used = None
        self.planned = 0

    @property
    def spent(self):
        return self.planned if self.dry else (0 if self.start_used is None else self.used - self.start_used)

    def get(self, path, params, cost, cache_file):
        if os.path.exists(cache_file):
            with open(cache_file) as fh:
                return json.load(fh)
        if self.spent + cost > self.max:
            raise BudgetExceeded(f'stopping: next call ({cost}) would pass {self.max} credits (spent {self.spent})')
        if self.dry:
            self.planned += cost
            return None
        import requests
        r = requests.get(f'{BASE}{path}', params={**params, 'apiKey': self.key}, timeout=60)
        used = r.headers.get('x-requests-used')
        if used is not None:
            used = int(float(used))
            if self.start_used is None:
                self.start_used = used - int(float(r.headers.get('x-requests-last', 0) or 0))
            self.used = used
        if r.status_code != 200:
            # never echo the URL: it carries the key
            print(f'HTTP {r.status_code} for {os.path.basename(cache_file)}: {r.text[:200]}', flush=True)
            return None
        body = r.json()
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, 'w') as fh:
            json.dump(body, fh)
        return body


class BudgetExceeded(Exception):
    pass


def fixture(cache):
    """Our own fixture (dates and teams), used to plan calls and to price a dry run."""
    f = pd.read_parquet(f'{cache}/frame.parquet', columns=['game', 'season', 'date', 'team', 'opp', 'is_home'])
    g = f[f.is_home == 1].drop_duplicates('game')
    return g.rename(columns={'team': 'home', 'opp': 'away'})[['game', 'season', 'date', 'home', 'away']]


def round_weeks(fx, seasons):
    """One events call per Monday of each week that has games: lists that week's events with their ids."""
    d = pd.to_datetime(fx[fx.season.isin(seasons)].date)
    mondays = sorted({(x - pd.Timedelta(days=x.weekday())).normalize() for x in d})
    return [dt.datetime(m.year, m.month, m.day, 0, tzinfo=dt.timezone.utc) for m in mondays]


def plan_and_pull(client, cache, seasons, props=True, team=True, offsets=None, prop_markets=None):
    global OFFSETS_H, PROPS
    OFFSETS_H = offsets or OFFSETS_H
    PROPS = prop_markets or PROPS
    fx = fixture(cache)
    events = {}
    for monday in round_weeks(fx, seasons):
        if monday < PROPS_START - dt.timedelta(days=7) and not team:
            continue
        body = client.get(f'/historical/sports/{SPORT}/events',
                          {'date': iso(monday), 'commenceTimeFrom': iso(monday), 'commenceTimeTo': iso(monday + dt.timedelta(days=7))},
                          1, f'{RAW}/events/{monday:%Y-%m-%d}.json')
        for e in (body or {}).get('data', []):
            events[e['id']] = e
    if client.dry:
        # no event ids without calling: price from our own fixture, one "event" per game
        games = fx[fx.season.isin(seasons)]
        n_props = sum(1 for d in pd.to_datetime(games.date) if d.tz_localize('UTC') >= PROPS_START) if props else 0
        client.planned += n_props * len(OFFSETS_H) * 10 * len(PROPS)
        if team:
            client.planned += len(games) * len(OFFSETS_H) * 10 * len(TEAM_MARKETS)
        return client.spent
    for eid, e in sorted(events.items(), key=lambda kv: kv[1]['commence_time']):
        start = dt.datetime.fromisoformat(e['commence_time'].replace('Z', '+00:00'))
        for h in OFFSETS_H:
            t = start - dt.timedelta(hours=h)
            markets = (PROPS if (props and t >= PROPS_START) else []) + (TEAM_MARKETS if team else [])
            if not markets:
                continue
            client.get(f'/historical/sports/{SPORT}/events/{eid}/odds',
                       {'date': iso(t), 'regions': 'au', 'markets': ','.join(markets), 'oddsFormat': 'decimal'},
                       10 * len(markets), f'{RAW}/odds/{eid}/{h:g}h.json')
    return client.spent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cache', default='afl/cache')
    ap.add_argument('--seasons', default='2023,2024,2025,2026')
    ap.add_argument('--max-credits', type=int, default=int(os.environ.get('MAX_CREDITS', '1000')))
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--no-team', action='store_true')
    ap.add_argument('--no-props', action='store_true')
    ap.add_argument('--offsets', help='hours before the bounce, comma separated (default 120,72,48,30,12,3,0.25)')
    ap.add_argument('--markets', help='prop markets, comma separated (default all four)')
    a = ap.parse_args()
    seasons = [int(s) for s in a.seasons.split(',')]
    key = os.environ.get('ODDS_API_KEY', '')
    if not key and not a.dry_run:
        sys.exit('ODDS_API_KEY is not set')
    c = Client(key, a.max_credits if not a.dry_run else 10 ** 9, a.dry_run)
    try:
        spent = plan_and_pull(c, a.cache, seasons, props=not a.no_props, team=not a.no_team,
                              offsets=[float(x) for x in a.offsets.split(',')] if a.offsets else None,
                              prop_markets=a.markets.split(',') if a.markets else None)
        print(f'{"planned" if a.dry_run else "spent"}: {spent:,} credits for seasons {seasons}')
    except BudgetExceeded as e:
        print(e)


if __name__ == '__main__':
    main()
