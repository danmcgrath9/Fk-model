"""No try-scorer feature may see its own game: change a game's tries, rebuild, compare that game's rows.

Position and jersey for the game ARE allowed (they are on Tuesday's team list); tries and results are not.
Needs nrl/cache (team_frame.parquet and player_matches.parquet); skipped without it.
"""
import os
import shutil

import numpy as np
import pandas as pd
import pytest

from nrl.model import player_frame

CACHE = os.path.join(os.path.dirname(__file__), '..', 'cache')
pytestmark = pytest.mark.skipif(not os.path.exists(os.path.join(CACHE, 'team_frame.parquet')), reason='no nrl/cache')
HISTORY = [f for f in player_frame.FEATURES if f not in ('position_code', 'jersey', 'starter')]


def test_a_games_own_tries_never_reach_its_features(tmp_path):
    for f in ('team_frame.parquet', 'player_matches.parquet', 'matches.parquet'):
        shutil.copy(os.path.join(CACHE, f), tmp_path / f)
    before = player_frame.build(str(tmp_path))
    target = before[before.season == 2022].match_id.unique()[50]
    pm = pd.read_parquet(tmp_path / 'player_matches.parquet')
    pm.loc[pm.match_id == target, 'tries'] = pm.loc[pm.match_id == target, 'tries'] + 2
    pm.to_parquet(tmp_path / 'player_matches.parquet', index=False)
    tf = pd.read_parquet(tmp_path / 'team_frame.parquet')
    tf.loc[tf.match_id == target, 'tries_for'] = tf.loc[tf.match_id == target, 'tries_for'] + 34
    tf.to_parquet(tmp_path / 'team_frame.parquet', index=False)
    after = player_frame.build(str(tmp_path))
    key = ['match_id', 'player_id']
    b = before[before.match_id == target].sort_values(key)[HISTORY].reset_index(drop=True)
    a = after[after.match_id == target].sort_values(key)[HISTORY].reset_index(drop=True)
    pd.testing.assert_frame_equal(b, a)
    # and it does reach those players' next game
    players = set(before[before.match_id == target].player_id)
    nxt = before[before.player_id.isin(players) & (before.i > before[before.match_id == target].i.iloc[0])] \
        .groupby('player_id').head(1).set_index('player_id').sort_index()
    nxt_after = after.set_index(['match_id', 'player_id']).loc[list(zip(nxt.match_id, nxt.index))]
    assert not np.allclose(nxt.try_ew_fast.to_numpy(), nxt_after.try_ew_fast.to_numpy())
