"""No run-metres or tackles feature may see its own game: change a game's stats, rebuild, compare.

Needs nrl/cache with the Champion Data tables (nrl/build.sh); skipped without them.
"""
import os
import shutil

import numpy as np
import pandas as pd
import pytest

from nrl.model import counts

CACHE = os.path.join(os.path.dirname(__file__), '..', 'cache')
pytestmark = pytest.mark.skipif(not os.path.exists(os.path.join(CACHE, 'cd_player_games.parquet')), reason='no cd data')
HISTORY = ['games', 'ew_fast', 'ew_slow', 'last10', 'last3', 'group_games', 'group_avg', 'opp_conc', 'exp_margin',
           'exp_total', 'prev_starter']


@pytest.mark.parametrize('stat', ['tackles', 'runMetres'])
def test_a_games_own_stats_never_reach_its_features(tmp_path, stat):
    for f in ('cd_player_games.parquet', 'cd_game_link.parquet', 'team_frame.parquet', 'teams.parquet'):
        shutil.copy(os.path.join(CACHE, f), tmp_path / f)
    before = counts.frame(str(tmp_path), stat)
    target = before[before.season == 2023].cd_match_id.unique()[40]
    cp = pd.read_parquet(tmp_path / 'cd_player_games.parquet')
    cp.loc[cp.cd_match_id == target, stat] = cp.loc[cp.cd_match_id == target, stat] * 3 + 50
    cp.to_parquet(tmp_path / 'cd_player_games.parquet', index=False)
    after = counts.frame(str(tmp_path), stat)
    k = ['cd_match_id', 'playerId']
    b = before[before.cd_match_id == target].sort_values(k)[HISTORY].reset_index(drop=True)
    a = after[after.cd_match_id == target].sort_values(k)[HISTORY].reset_index(drop=True)
    pd.testing.assert_frame_equal(b, a)
    players = set(before[before.cd_match_id == target].playerId)
    t0 = before[before.cd_match_id == target].kick_off.iloc[0]
    nb = before[before.playerId.isin(players) & (before.kick_off > t0)].groupby('playerId').head(1).sort_values(k)
    na = after.set_index(k).loc[list(zip(nb.cd_match_id, nb.playerId))]
    assert not np.allclose(nb.ew_fast.to_numpy(), na.ew_fast.to_numpy())
