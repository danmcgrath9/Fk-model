"""Compare a saved odds snapshot with our prices and write a PAPER list. Paper only: nothing is sent anywhere.

Reads a JSON file in The Odds API v4 shape (a list of events, or a historical {"timestamp", "data"} wrapper;
each event has home_team, away_team, commence_time and bookmakers -> markets -> outcomes). Makes no network
call. Market keys are mapped to our quantities through MARKETS below; any key not listed is reported as
unmapped, never guessed. Cricket's prop keys on The Odds API are unknown until bbl/lines/probe.py has run:
add them here only from a real response.

A bet goes on the paper list when our chance x the book's price - 1 >= EDGE. EDGE is a placeholder
until recorded prices let it be chosen the way the threshold was chosen in the backtest.

Usage: python -m bbl.live.compare bbl/cache/parquet snapshot.json   (writes bbl/cache/paper/<snapshot>.csv)
"""
import json
import os
import sys

import numpy as np
import pandas as pd

EDGE = 0.05
SYDNEY = 'Australia/Sydney'
# The Odds API market key -> our quantity. h2h is a featured market on every sport. Nothing else is listed
# until the probe confirms it exists for cricket and what it settles on (e.g. whether 'totals' is match runs).
MARKETS = {'h2h': 'win'}


def team_name(s):
    """Book names to Cricsheet names: books may tag the women's sides."""
    for tag in (' Women', ' (W)', ' W'):
        if s.endswith(tag):
            return s[: -len(tag)]
    return s


def events(path):
    body = json.load(open(path))
    data = body.get('data', body) if isinstance(body, dict) else body
    return data if isinstance(data, list) else [data]


def outcomes(evs):
    rows = []
    for e in evs:
        for bk in e.get('bookmakers', []):
            for mk in bk.get('markets', []):
                for o in mk.get('outcomes', []):
                    rows.append(dict(event_id=e.get('id'), commence_time=e.get('commence_time'), home=team_name(e.get('home_team', '')),
                                     away=team_name(e.get('away_team', '')), book=bk.get('key'), market=mk.get('key'),
                                     name=o.get('name'), description=o.get('description'), point=o.get('point'), price=o.get('price'),
                                     last_update=mk.get('last_update') or bk.get('last_update')))
    return pd.DataFrame(rows)


def attach_games(o, games):
    o = o.copy()
    o['date'] = pd.to_datetime(o.commence_time, utc=True).dt.tz_convert(SYDNEY).dt.strftime('%Y-%m-%d')
    g = games.copy()
    g['pair'] = g.apply(lambda r: frozenset((r.team1, r.team2)), axis=1)
    o['pair'] = o.apply(lambda r: frozenset((r.home, r.away)), axis=1)
    return o.merge(g[['match_id', 'start_date', 'pair', 'team1', 'team2', 'p_team1']], left_on=['date', 'pair'],
                   right_on=['start_date', 'pair'], how='left')


def our_chance(o):
    """Our chance for each outcome; NaN for an outcome we do not price (a draw or tie line, an unknown name)."""
    p = pd.Series(np.nan, index=o.index)
    win = o.market.map(MARKETS) == 'win'
    side = o.name.fillna('').map(team_name)
    p[win & (side == o.team1)] = o.p_team1[win & (side == o.team1)]
    p[win & (side == o.team2)] = 1 - o.p_team1[win & (side == o.team2)]
    return p


def compare(d, snapshot):
    games = pd.read_parquet(os.path.join(d, 'prices_games.parquet'))
    o = attach_games(outcomes(events(snapshot)), games)
    unmapped = sorted(set(o.market) - set(MARKETS))
    unmatched = o[o.match_id.isna()][['home', 'away', 'date']].drop_duplicates()
    o = o[o.market.isin(MARKETS) & o.match_id.notna()].copy()
    o['our_p'] = our_chance(o)
    o['fair'] = 1 / o.our_p
    o['edge'] = o.our_p * o.price - 1
    paper = o[o.edge >= EDGE].sort_values('edge', ascending=False)
    return o, paper, unmapped, unmatched


def main(d, snapshot):
    o, paper, unmapped, unmatched = compare(d, snapshot)
    out = os.path.join(d, '..', 'paper')
    os.makedirs(out, exist_ok=True)
    stem = os.path.splitext(os.path.basename(snapshot))[0]
    o.to_csv(os.path.join(out, f'{stem}_all.csv'), index=False)
    paper.to_csv(os.path.join(out, f'{stem}_paper.csv'), index=False)
    print(f'PAPER ONLY. {len(o)} priced outcomes, {len(paper)} at an edge of {EDGE:.0%} or more.')
    if len(paper):
        print(paper[['date', 'home', 'away', 'book', 'market', 'name', 'price', 'fair', 'edge']].to_string(index=False))
    if unmapped:
        print('market keys not mapped (add only from a real response): ' + ', '.join(unmapped))
    if len(unmatched):
        print('events with no fixture priced: ' + '; '.join(f'{r.home} v {r.away} {r.date}' for r in unmatched.itertuples()))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
