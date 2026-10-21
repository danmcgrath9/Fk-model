"""Copy uselessnrlstats' cleaned Rugby League Project data into parquet files.

uselessnrlstats keeps RLP's NRL history, already cleaned, on GitHub (match and per-player
match data, 1908 to the last time they refreshed). We read their copy with one git clone
instead of scraping RLP. Seasons before 1998 (the first NRL season) are dropped: the
competition, the rules and the try value all differ too much to teach 2027.

Writes, one row per:
  <out>/matches.parquet         game: season, round, date, kick-off, venue, crowd, scores, penalties
  <out>/player_matches.parquet  player per game: team, jersey, position, tries, goals, field goals,
                                sin bins, send offs, points
  <out>/players.parquet, teams.parquet, venues.parquet, ladders.parquet  reference tables
  <out>/mirror_source.txt       the commit we copied, so a later run can say what changed

Usage: python nrl/data/mirror.py --out nrl/cache [--src /path/to/existing/uselessnrlstats]
"""
import argparse
import os
import subprocess
import sys
import tempfile

import pandas as pd

MIRROR = 'https://github.com/uselessnrlstats/uselessnrlstats.git'
FIRST_SEASON = 1998
TABLES = {'match_data': 'matches', 'player_match_data': 'player_matches', 'player_data': 'players',
          'team_data': 'teams', 'venue_data': 'venues', 'ladder_round_data': 'ladders'}


def clone(dest):
    subprocess.run(['git', 'clone', '--depth', '1', '-q', MIRROR, dest], check=True)
    return subprocess.run(['git', '-C', dest, 'log', '-1', '--format=%H %cd'], check=True,
                          capture_output=True, text=True).stdout.strip()


def to_strings(df):
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].astype('string')
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--src', help='an existing clone of uselessnrlstats (skips the download)')
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    src = args.src
    if src:
        head = subprocess.run(['git', '-C', src, 'log', '-1', '--format=%H %cd'], capture_output=True,
                              text=True).stdout.strip()
    else:
        src = os.path.join(tempfile.mkdtemp(), 'uselessnrlstats')
        head = clone(src)
    print(f'uselessnrlstats at {head}')
    raw = os.path.join(src, 'cleaned_data', 'nrl')

    frames = {name: pd.read_csv(os.path.join(raw, f + '.csv'), low_memory=False) for f, name in TABLES.items()}
    m = frames['matches']
    m['date'] = pd.to_datetime(m['date'])
    m['season'] = m['date'].dt.year
    m = m[m.season >= FIRST_SEASON].reset_index(drop=True)
    frames['matches'] = m
    pm = frames['player_matches']
    frames['player_matches'] = pm[pm.match_id.isin(m.match_id)].reset_index(drop=True)
    if 'ladders' in frames and 'competition_year' in frames['ladders']:
        lad = frames['ladders']
        yr = lad.competition_year.astype(str).str.extract(r'(\d{4})')[0].astype(float)
        frames['ladders'] = lad[yr >= FIRST_SEASON].reset_index(drop=True)

    for name, df in frames.items():
        to_strings(df).to_parquet(os.path.join(args.out, name + '.parquet'), index=False)
    with open(os.path.join(args.out, 'mirror_source.txt'), 'w') as fh:
        fh.write(f'{MIRROR} {head}\n')

    pm = frames['player_matches']
    print(f'matches: {len(m):,} games, seasons {m.season.min()}-{m.season.max()}, last game {m.date.max().date()}')
    print(f'player_matches: {len(pm):,} player-games')
    by = m.groupby('season').size()
    print('games per season: ' + ', '.join(f'{s} {n}' for s, n in by.items()))


if __name__ == '__main__':
    sys.exit(main())
