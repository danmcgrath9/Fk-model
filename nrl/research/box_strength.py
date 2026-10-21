"""Line-up strength from box scores: the named 17's recent Champion Data stats, summed per side.

For every player, an exponentially weighted average of each stat over his EARLIER games (never this one);
for every team-game, the sum over the players who took the field, home minus away. 2014 on only.
Writes nrl/cache/box_strength.parquet: match_id (RLP id), and one *_diff column per stat.
"""
import sys

import numpy as np
import pandas as pd

from nrl.model.player_frame import ew

STATS = ['runMetres', 'postContactMetres', 'lineBreaks', 'tackleBreaks', 'tryAssists', 'offloads', 'tackles',
         'missedTackles', 'errors', 'penaltiesConceded', 'kickMetres']


def main(cache):
    cp = pd.read_parquet(f'{cache}/cd_player_games.parquet')
    cp = cp[cp.took_field].sort_values('utc_start').reset_index(drop=True)
    for s in STATS:
        cp[f'{s}_ew'] = ew(None, cp.playerId, cp[s].astype(float), 0.15)
        # a debutant counts as a typical player in his jersey: fill with the jersey's average so far
        cp[f'{s}_ew'] = cp[f'{s}_ew'].fillna(cp.groupby('jumperNumber')[f'{s}_ew'].transform('median'))
    side = cp.groupby(['cd_match_id', 'home'])[[f'{s}_ew' for s in STATS]].sum()
    h, a = side.xs(True, level='home'), side.xs(False, level='home')
    d = (h - a).add_suffix('_diff').reset_index()
    gl = pd.read_parquet(f'{cache}/cd_game_link.parquet')
    d = d.merge(gl, on='cd_match_id')
    d.drop(columns='cd_match_id').to_parquet(f'{cache}/box_strength.parquet', index=False)
    print(f'box_strength: {len(d):,} games')


if __name__ == '__main__':
    main(sys.argv[1])
