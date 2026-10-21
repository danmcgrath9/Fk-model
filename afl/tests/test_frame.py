"""No feature may see its own game. Change a game's stats, rebuild, compare that game's features.

Needs afl/cache from afl/data/mirror.py; skipped without it (the data is not in the repo).
"""
import os

import numpy as np
import pandas as pd
import pytest

from afl.model import frame

CACHE = os.path.join(os.path.dirname(__file__), '..', 'cache')
pytestmark = pytest.mark.skipif(not os.path.exists(os.path.join(CACHE, 'afltables.parquet')), reason='no afl/cache')


@pytest.fixture(scope='module')
def base():
    at = pd.read_parquet(os.path.join(CACHE, 'afltables.parquet'))
    fw = pd.read_parquet(os.path.join(CACHE, 'footywire.parquet'))
    at, fw = at[at.Season.isin([2024, 2025])], fw[fw.Season.isin([2024, 2025])]
    return frame.base_table(at, fw)


def test_a_games_own_stats_never_reach_its_features(base):
    target = base[base.season == 2025].game.unique()[100]
    before = frame.add_features(base)
    tampered = base.copy()
    rows = tampered.game == target
    for c in ['D', 'TOG', 'K', 'HB', 'CCL', 'CL', 'CP', 'UP', 'SC', 'G', 'margin', 'score_for', 'score_against']:
        tampered.loc[rows, c] = tampered.loc[rows, c] * 3 + 7
    after = frame.add_features(tampered)
    f = frame.FEATURES
    b = before[before.game == target].sort_values('player_id')[f].reset_index(drop=True)
    a = after[after.game == target].sort_values('player_id')[f].reset_index(drop=True)
    pd.testing.assert_frame_equal(b, a)
    # and the tamper did reach the next game, so the test would notice a broken shift
    later = sorted(base[(base.game > target)].game.unique())[:60]
    moved = (before[before.game.isin(later)].D_l3.fillna(-1).to_numpy() != after[after.game.isin(later)].D_l3.fillna(-1).to_numpy())
    assert moved.any()


def test_outs_value_the_missing_player_at_his_usual_figures():
    rows = []
    for gm, day, ids in [('g1', '2025-03-01', [1, 2, 3]), ('g2', '2025-03-08', [1, 2, 4])]:
        for pid in ids:
            rows.append(dict(game=gm, dt=pd.Timestamp(day), team='A', player_id=pid, D_l10=10.0 * pid, CCL_pg=float(pid)))
    out = frame.outs_and_ins(pd.DataFrame(rows)).set_index('game')
    assert np.isnan(out.loc['g1', 'outs_D'])
    assert out.loc['g2', 'outs_D'] == 30.0       # player 3 (usual 30) missed g2
    assert out.loc['g2', 'outs_CCL'] == 3.0
    assert out.loc['g2', 'n_ins'] == 1.0          # player 4 came in


def test_elo_expected_margin_is_pregame():
    g = pd.DataFrame({'season': [2025] * 3, 'home': ['A', 'A', 'B'], 'away': ['B', 'B', 'A'], 'margin_home': [40, 40, -10]})
    e = frame.elo(g)
    assert e.iloc[0] == frame.ELO_HGA                       # first meeting knows nothing but home ground
    assert e.iloc[1] == pytest.approx(frame.ELO_HGA + 2 * frame.ELO_K * (40 - frame.ELO_HGA))   # moved only by game 1
