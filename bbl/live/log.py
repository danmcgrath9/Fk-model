"""Price every fixture in the next few days and append the prices to the prediction log. Paper only.

The log is the model's track record before any odds exist: every price is stamped with the time it was made and
the code version, made before the game, and never edited afterwards (bbl/live/score.py scores it once results
are in). A game priced on several days keeps every row; the score uses the last one made before the game's day.

Usage: python -m bbl.live.log <parquet dir> <fixtures csv> <squads csv> <log dir> [days ahead, default 3]
"""
import datetime as dt
import os
import sys
from zoneinfo import ZoneInfo

import pandas as pd

from bbl.live import price

SYDNEY = ZoneInfo('Australia/Sydney')
PLAYER_COLS = ['player', 'team', 'p_bat', 'mu_runs', 'r_runs', 'mu_6s', 'r_6s', 'p_bowl', 'mu_wkts', 'r_wkts', 'top_batter']


def window(fixtures, held_ids, days, today=None):
    today = today or dt.datetime.now(SYDNEY).date()
    f = fixtures.copy()
    f['d'] = pd.to_datetime(f.date).dt.date
    f = f[(f.d >= today) & (f.d <= today + dt.timedelta(days=days))]
    return f[~f.cricinfo_id.astype(str).isin(held_ids)].drop(columns='d').reset_index(drop=True)


def append(path, rows):
    if rows.empty:
        return 0
    old = pd.read_parquet(path) if os.path.exists(path) else pd.DataFrame()
    pd.concat([old, rows], ignore_index=True).to_parquet(path, index=False)
    return len(rows)


def main(d, fixtures_csv, squads_csv, log_dir, days='3'):
    os.makedirs(log_dir, exist_ok=True)
    held = set(pd.read_parquet(os.path.join(d, 't20_matches.parquet'), columns=['match_id']).match_id)
    fx = window(pd.read_csv(fixtures_csv, dtype=str), held, int(days))
    if fx.empty:
        print('nothing to price in the window')
        return
    squads = pd.read_csv(squads_csv, dtype=str) if squads_csv and os.path.exists(squads_csv) else None
    games, players, notes = price.price(d, fx[['date', 'team1', 'team2', 'venue', 'gender', 'comp']], None, squads)
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    ver = os.environ.get('GITHUB_SHA', 'local')[:7]
    # price.future_rows names fixture k 'F{k:03d}_{date}', in the order given: map back to the Cricinfo id
    key = {f'F{k:03d}_{r.date}': r.cricinfo_id for k, r in enumerate(fx.itertuples())}
    games = games.assign(cricinfo_id=games.match_id.map(key), logged_at=stamp, code=ver)
    players = players.assign(cricinfo_id=players.match_id.map(key), logged_at=stamp, code=ver)
    keep = ['cricinfo_id', 'logged_at', 'code', 'start_date', 'competition', 'team1', 'team2', 'venue', 'p_team1',
            'first_inns_runs_mu', 'first_inns_runs_sd', 'match_runs_mu', 'match_runs_sd']
    n1 = append(os.path.join(log_dir, 'prediction_log_games.parquet'), games[[c for c in keep if c in games]])
    n2 = append(os.path.join(log_dir, 'prediction_log_players.parquet'),
                players[['cricinfo_id', 'logged_at', 'code'] + [c for c in PLAYER_COLS if c in players]])
    print(f'logged {n1} games and {n2} player rows at {stamp} (code {ver})')
    for n in notes:
        print(' -', n)


if __name__ == '__main__':
    main(*sys.argv[1:])
