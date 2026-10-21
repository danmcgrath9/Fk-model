"""A match's own result must never reach the numbers used to price it.

Runs on a synthetic league (always) and on the real tables when aleague/cache/tables exists.
"""
import datetime as dt
import os

import numpy as np
import pandas as pd
import pytest

from aleague.data.team_games import build as build_team_games
from aleague.model.team import rolling_predictions

TEAMS = ['A', 'B', 'C', 'D', 'E', 'F']
REAL = os.path.join(os.path.dirname(__file__), '..', 'cache', 'tables', 'matches.parquet')


def synthetic(seasons=(2020, 2021), seed=1):
    rng = np.random.default_rng(seed)
    rows = []
    for s in seasons:
        day = dt.date(s - 1, 10, 1)
        for rnd in range(15):
            order = rng.permutation(TEAMS)
            for i in range(0, 6, 2):
                h, a = order[i], order[i + 1]
                hg, ag = rng.poisson(1.6), rng.poisson(1.2)
                rows.append(dict(match_id=f'{day}_{h}_{a}', season=s, date=day, home=h, away=a, neutral=False,
                                 stage='Regular season', home_goals=hg, away_goals=ag,
                                 home_goals_90=float(hg), away_goals_90=float(ag)))
            day += dt.timedelta(days=7)
    return pd.DataFrame(rows)


def change_result(m, match_id):
    m = m.copy()
    i = m.index[m.match_id == match_id][0]
    m.loc[i, ['home_goals', 'home_goals_90']] = m.loc[i, 'home_goals_90'] + 6
    return m


def check_model(m, target_season):
    base = rolling_predictions(m, [target_season])
    victim = base.iloc[len(base) // 2]
    moved = rolling_predictions(change_result(m, victim.match_id), [target_season])
    cols = ['lam_home', 'lam_away', 'p_home', 'p_draw', 'p_away', 'p_over25', 'p_btts']
    same_day_or_before = base.date <= victim.date
    # the changed match, and everything on or before its day, is priced exactly as before
    pd.testing.assert_frame_equal(base.loc[same_day_or_before, cols], moved.loc[same_day_or_before, cols])
    # and the test can see a leak: later matches involving the team do move
    later = (base.date > victim.date) & ((base.home == victim.home) | (base.away == victim.home))
    assert later.any() and (base.loc[later, 'lam_home'] - moved.loc[later, 'lam_home']).abs().max() > 1e-6


def check_team_games(m):
    t0 = build_team_games(m)
    victim = m[m.home_goals_90.notna()].iloc[len(m) // 2]
    t1 = build_team_games(change_result(m, victim.match_id))
    feats = ['gf_last5', 'ga_last5', 'gf_ewm', 'ga_ewm', 'rest_days', 'long_trip', 'season_game']
    own = t0.match_id == victim.match_id
    pd.testing.assert_frame_equal(t0.loc[own, feats], t1.loc[own, feats])
    # the targets do change, and the team's next match's features do
    assert (t0.loc[own, 'y_gf'].to_numpy() != t1.loc[own, 'y_gf'].to_numpy()).any()
    nxt = t0[(t0.team == victim.home) & (t0.date > victim.date)].index[0]
    assert t0.loc[nxt, 'gf_last5'] != t1.loc[nxt, 'gf_last5']


def test_model_synthetic():
    check_model(synthetic(), 2021)


def test_team_games_synthetic():
    check_team_games(synthetic())


@pytest.mark.skipif(not os.path.exists(REAL), reason='real tables not downloaded')
def test_model_real():
    m = pd.read_parquet(REAL)
    counts = m[m.home_goals_90.notna()].groupby('season').size()
    check_model(m, int(counts[counts >= 100].index.max()))  # the latest complete season


@pytest.mark.skipif(not os.path.exists(REAL), reason='real tables not downloaded')
def test_team_games_real():
    check_team_games(pd.read_parquet(REAL))
