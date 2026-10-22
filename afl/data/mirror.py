"""Copy fitzRoy's pre-scraped AFL Tables and Footywire history into parquet files.

fitzRoy's author keeps both sites' per-game player stats on GitHub (jimmyday12/fitzRoy_data,
refreshed weekly in season), so we read his copy instead of scraping either site. One git
clone, nothing else. Seasons before 2012 are dropped: the game, the stats kept and the
interchange rules all differ too much to teach 2027.

Writes:
  <out>/afltables.parquet   one row per player per game, every season from 2012 (results,
                            venue, scores, AFL Tables stats, Brownlow votes, substitute flag)
  <out>/footywire.parquet   one row per player per game from 2012 (advanced stats:
                            metres gained, score involvements, intercepts, centre clearances,
                            time on ground, SuperCoach, AFL Fantasy)

Usage: python afl/data/mirror.py --out afl/cache [--src /path/to/existing/fitzRoy_data]
"""
import argparse
import os
import subprocess
import sys
import tempfile

import pandas as pd
import pyreadr

MIRROR = 'https://github.com/jimmyday12/fitzRoy_data.git'
FIRST_SEASON = 2012


def clone(dest):
    subprocess.run(['git', 'clone', '--depth', '1', MIRROR, dest], check=True)
    head = subprocess.run(['git', '-C', dest, 'log', '-1', '--format=%H %cd'], check=True,
                          capture_output=True, text=True).stdout.strip()
    print(f'fitzRoy_data at {head}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--src', help='an existing clone of fitzRoy_data (skips the download)')
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    src = args.src
    if not src:
        src = os.path.join(tempfile.mkdtemp(), 'fitzRoy_data')
        clone(src)
    raw = os.path.join(src, 'data-raw')

    at = pyreadr.read_r(os.path.join(raw, 'afl_tables_playerstats', 'afldata.rda'))['afldata']
    at = at[at.Season >= FIRST_SEASON].reset_index(drop=True)
    fw = pyreadr.read_r(os.path.join(raw, 'player_stats', 'player_stats.rda'))['player_stats']
    fw = fw[fw.Season >= FIRST_SEASON].reset_index(drop=True)

    # R factors and mixed columns arrive as objects; parquet wants one type per column
    for df in (at, fw):
        for c in df.columns:
            if df[c].dtype == object:
                df[c] = df[c].astype('string')

    at.to_parquet(os.path.join(args.out, 'afltables.parquet'), index=False)
    fw.to_parquet(os.path.join(args.out, 'footywire.parquet'), index=False)
    for name, df in (('afltables', at), ('footywire', fw)):
        print(f'{name}: {len(df):,} rows, seasons {int(df.Season.min())}-{int(df.Season.max())}, '
              f'last game {df.Date.max()}')


if __name__ == '__main__':
    sys.exit(main())
