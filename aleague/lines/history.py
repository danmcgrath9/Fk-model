"""Plan and pull A-League Men team-market history from The Odds API, inside a credit budget.

Not run yet: it waits for the ODDS_API_KEY secret and for the probe (probe.py) to confirm which markets
and books exist. `--plan` prints what a pull would cost without spending anything.

What to buy, and why this shape. A historical odds call returns every game listed at one moment, for
10 credits x markets x regions (au only here). So the unit of cost is a SNAPSHOT TIME, not a game, and
the cheapest useful history is a few snapshots per round:
  open   the first snapshot after a round's lines appear (the probe measures how many days before)
  named  shortly after team news (A-League sides are named about an hour before kick-off, so for
         this sport "teams named" and "close" are nearly the same moment; one snapshot per kick-off
         time, 10 minutes before)
  close  5 minutes before each kick-off time (the closing line: the benchmark the house standard asks
         for). Games sharing a kick-off time share a snapshot
Matches come from aleague-history's matches.parquet (kick-off times in UTC).

Costs from the real fixture lists (--plan), 2020-21 to 2025-26, 3 markets (30 credits a snapshot):
  close at every kick-off: about 5,600 a season, 33,840 for all six (over the 20,000 budget)
  close once per match day (--close day): run --plan; it is the affordable way to cover six seasons
--plan prints the exact figure before anything is bought.

Usage:
  python -m aleague.lines.history --plan --tables aleague/cache/tables --seasons 2023,2024,2025,2026
  python -m aleague.lines.history --pull ... --max-credits 5000 --out aleague/cache/odds
"""
import argparse
import datetime as dt
import json
import os
import sys

import pandas as pd

SPORT = 'soccer_australia_aleague'
BASE = 'https://api.the-odds-api.com/v4'


def snapshots(matches, seasons, open_days=5.0, close_minutes=5, close='kickoff'):
    """(time, kind) pairs: one 'open' per round-week, then one 'close' per distinct kick-off time
    (close='kickoff'), or one per Sydney match day before its first kick-off (close='day': cheaper, and
    a day's later games are priced some hours before their own kick-off)."""
    m = matches[matches.season.isin(seasons) & matches.kickoff_utc.notna()].copy()
    m['ko'] = pd.to_datetime(m.kickoff_utc, utc=True)
    local = m.ko.dt.tz_convert('Australia/Sydney').dt.tz_localize(None)
    m['week'] = local.dt.to_period('W-SUN')
    m['day'] = local.dt.date
    out = []
    for _, w in m.groupby('week'):
        first = w.ko.min()
        out.append((first - pd.Timedelta(days=open_days), 'open'))
        if close == 'day':
            for _, d in w.groupby('day'):
                out.append((d.ko.min() - pd.Timedelta(minutes=close_minutes), 'close'))
        else:
            for ko in sorted(w.ko.unique()):
                out.append((pd.Timestamp(ko) - pd.Timedelta(minutes=close_minutes), 'close'))
    return sorted(set(out))


def plan(matches, seasons, markets, close='kickoff'):
    snaps = snapshots(matches, seasons, close=close)
    per = 10 * len(markets)
    df = pd.DataFrame(snaps, columns=['at', 'kind'])
    df['season'] = [matches[(pd.to_datetime(matches.kickoff_utc, utc=True) - t).abs() < pd.Timedelta(days=8)].season.max()
                    for t in df['at']]
    by = df.groupby('season').kind.value_counts().unstack(fill_value=0)
    by['credits'] = (by.sum(axis=1)) * per
    return df, by


def pull(snaps, markets, key, max_credits, out):
    import requests
    os.makedirs(out, exist_ok=True)
    spent, start_used = 0, None
    for t, kind in snaps:
        cost = 10 * len(markets)
        if spent + cost > max_credits:
            print(f'stopping: next call would pass {max_credits} credits (spent {spent})'); break
        name = os.path.join(out, f'{t:%Y%m%dT%H%M}_{kind}.json')
        if os.path.exists(name):
            continue  # never buy a snapshot twice
        r = requests.get(f'{BASE}/historical/sports/{SPORT}/odds', timeout=60,
                         params=dict(apiKey=key, regions='au', markets=','.join(markets), oddsFormat='decimal',
                                     date=t.strftime('%Y-%m-%dT%H:%M:%SZ')))
        used = int(float(r.headers.get('x-requests-used', 0) or 0))
        start_used = used - int(float(r.headers.get('x-requests-last', 0) or 0)) if start_used is None else start_used
        spent = used - start_used
        print(f'{t} {kind}: HTTP {r.status_code}, spent {spent}, remaining {r.headers.get("x-requests-remaining")}')
        if r.status_code != 200:
            print(r.text[:300]); break
        json.dump(r.json(), open(name, 'w'))
    return spent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tables', default='aleague/cache/tables')
    ap.add_argument('--seasons', default='2023,2024,2025,2026')
    ap.add_argument('--markets', default='h2h,spreads,totals')
    ap.add_argument('--close', default='kickoff', choices=['kickoff', 'day'])
    ap.add_argument('--plan', action='store_true')
    ap.add_argument('--pull', action='store_true')
    ap.add_argument('--max-credits', type=int, default=0)
    ap.add_argument('--out', default='aleague/cache/odds')
    a = ap.parse_args()
    m = pd.read_parquet(os.path.join(a.tables, 'matches.parquet'))
    seasons = [int(s) for s in a.seasons.split(',')]
    markets = a.markets.split(',')
    snaps, by = plan(m, seasons, markets, a.close)
    print(by.to_string())
    print(f'total: {len(snaps)} snapshots, {by.credits.sum():,} credits at {10 * len(markets)} a snapshot')
    if a.pull:
        key = os.environ.get('ODDS_API_KEY')
        if not key:
            sys.exit('ODDS_API_KEY is not set')
        if a.max_credits <= 0:
            sys.exit('--max-credits is required for a pull')
        pull(list(zip(snaps['at'], snaps['kind'])), markets, key, a.max_credits, a.out)


if __name__ == '__main__':
    main()
