"""No team feature may see its own game. Change one game's result and line-up, rebuild, compare.

Needs nrl/cache from nrl/data/mirror.py; skipped without it (the data is not in the repo).
"""
import os

import numpy as np
import pandas as pd
import pytest

from nrl.model import player_ratings, team_frame

CACHE = os.path.join(os.path.dirname(__file__), '..', 'cache')
pytestmark = pytest.mark.skipif(not os.path.exists(os.path.join(CACHE, 'matches.parquet')), reason='no nrl/cache')
FEATS = ['exp_for', 'exp_against', 'league_total', 'home_adv', 'rating_diff', 'rest_days',
         'missing_weight_named', 'missing_weight_open', 'spine_missing_named', 'spine_missing_open']


@pytest.fixture(scope='module')
def data():
    m, pm = team_frame.load(CACHE)
    keep = m.season.between(2018, 2021)
    m = m[keep].reset_index(drop=True)
    return m, pm[pm.match_id.isin(m.match_id)].copy()


def test_a_games_own_result_never_reaches_its_features(data):
    m, pm = data
    target = m[m.season == 2020].match_id.iloc[60]
    before = team_frame.build(m, pm)
    m2, pm2 = m.copy(), pm.copy()
    rows = m2.match_id == target
    m2.loc[rows, 'home_team_score'] += 40
    m2.loc[rows, 'away_team_score'] = 0
    pm2.loc[pm2.match_id == target, 'tries'] += 3
    after = team_frame.build(m2, pm2)
    b = before[before.match_id == target].sort_values('team')[FEATS].reset_index(drop=True)
    a = after[after.match_id == target].sort_values('team')[FEATS].reset_index(drop=True)
    pd.testing.assert_frame_equal(b, a)
    # the tamper did reach the teams' next games, so the test would notice a broken order
    teams = set(before[before.match_id == target].team)
    later = before[(before.kick_off > before[before.match_id == target].kick_off.iloc[0]) & before.team.isin(teams)]
    nxt = later.groupby('team').head(1).match_id
    moved = before[before.match_id.isin(nxt)].exp_for.to_numpy() != after[after.match_id.isin(nxt)].exp_for.to_numpy()
    assert moved.any()


def test_a_games_own_lineup_changes_only_the_named_measure(data):
    m, pm = data
    target = m[m.season == 2020].match_id.iloc[60]
    before = team_frame.build(m, pm)
    pm2 = pm.copy()
    # swap the home side's fullback for a player it has never used
    home = m.loc[m.match_id == target, 'home_team'].iloc[0]
    fb = (pm2.match_id == target) & (pm2.team == home) & (pm2.position == 'FB')
    pm2.loc[fb, 'player_id'] = -1
    after = team_frame.build(m, pm2)
    b = before[(before.match_id == target) & (before.team == home)].iloc[0]
    a = after[(after.match_id == target) & (after.team == home)].iloc[0]
    assert b.missing_weight_open == a.missing_weight_open
    assert a.missing_weight_named > b.missing_weight_named


def test_player_ratings_fit_only_on_earlier_games(data, tmp_path):
    m, pm = data
    # the ratings for a round must not move when that round's results change
    import shutil
    for f in ('matches.parquet', 'player_matches.parquet'):
        shutil.copy(os.path.join(CACHE, f), tmp_path / f)
    player_ratings.main(str(tmp_path))
    before = pd.read_parquet(tmp_path / 'player_strength.parquet')
    mm = pd.read_parquet(tmp_path / 'matches.parquet')
    target = m[m.season == 2020].match_id.iloc[60]
    mm.loc[mm.match_id == target, 'home_team_score'] += 40
    mm.to_parquet(tmp_path / 'matches.parquet', index=False)
    player_ratings.main(str(tmp_path))
    after = pd.read_parquet(tmp_path / 'player_strength.parquet')
    b = before[before.match_id == target].sort_values('team').reset_index(drop=True)
    a = after[after.match_id == target].sort_values('team').reset_index(drop=True)
    pd.testing.assert_frame_equal(b, a)
    later = before.match_id > target
    assert not np.allclose(before[later].strength_named.fillna(0), after[later].strength_named.fillna(0))
