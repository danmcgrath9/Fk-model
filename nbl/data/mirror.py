"""Copy nblR's pre-scraped NBL history into parquet files.

nblR's author keeps the NBL's results, box scores, play-by-play and shot locations as files on GitHub
releases (JaseZiv/nblr_data, refreshed through the season), so we read his copy instead of asking the
NBL's own site or its stats provider. One download per file, nothing else.

Writes to <out>:
  results.parquet      every game since 1979: teams, scores, venue, round, type, tip time (UTC)
  box_team.parquet     one row per team per game, 2015-16 on
  box_player.parquet   one row per player per game, 2015-16 on (game-day squad, including 0:00 rows
                       for players who dressed and did not play)
  shots.parquet        shot locations, 2015-16 and 2017-18 to 2024-25
  pbp.parquet          play-by-play (read from pbp.csv.gz, which the workflow writes with R, because
                       the .rds holds types pyreadr cannot read)
  seasons.parquet      season to competition id

Usage: python nbl/data/mirror.py --out nbl/cache [--raw dir-with-rds-files]
"""
import argparse
import os
import sys

import pandas as pd
import pyreadr
import requests

BASE = 'https://github.com/JaseZiv/nblr_data/releases/download'
FILES = {  # our name: (release tag, file)
    'seasons': ('league', 'seasons.rds'),
    'results': ('match_results', 'results_wide.rds'),
    'box_team': ('box_team', 'box_team.rds'),
    'box_player': ('box_player', 'box_player.rds'),
    'shots': ('shots', 'shots.rds'),
    'pbp': ('pbp', 'pbp.rds'),
}


def fetch(tag, name, dest):
    path = os.path.join(dest, name)
    if os.path.exists(path):
        return path
    r = requests.get(f'{BASE}/{tag}/{name}', timeout=600)
    r.raise_for_status()
    open(path, 'wb').write(r.content)
    return path


def tidy(df):
    # R factors and mixed columns arrive as objects; parquet wants one type per column
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].astype('string')
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--raw', help='directory for the downloaded .rds files (default <out>/raw)')
    args = ap.parse_args()
    raw = args.raw or os.path.join(args.out, 'raw')
    os.makedirs(args.out, exist_ok=True)
    os.makedirs(raw, exist_ok=True)

    for name, (tag, fname) in FILES.items():
        path = fetch(tag, fname, raw)
        if name == 'pbp':
            csv = os.path.join(raw, 'pbp.csv.gz')
            if not os.path.exists(csv):
                print('pbp: pbp.csv.gz not found (the workflow writes it with R); skipped')
                continue
            df = pd.read_csv(csv, low_memory=False)
        else:
            df = pyreadr.read_r(path)[None]
        df = tidy(df)
        df.to_parquet(os.path.join(args.out, f'{name}.parquet'), index=False)
        seasons = df['season'].dropna().astype(str) if 'season' in df.columns else pd.Series(dtype=str)
        span = f', seasons {seasons.min()} to {seasons.max()}' if len(seasons) else ''
        print(f'{name}: {len(df):,} rows, {df.shape[1]} columns{span}')


if __name__ == '__main__':
    sys.exit(main())
