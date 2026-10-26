"""No feature may see its own game. Change a game's stats and score, rebuild, compare that game's features.

Needs nbl/cache from nbl/data/mirror.py (or the nbl-history release); skipped without it.
"""
import os

import numpy as np
import pandas as pd
import pytest

from nbl.model import frame

CACHE = os.path.join(os.path.dirname(__file__), '..', 'cache')
pytestmark = pytest.mark.skipif(not os.path.exists(os.path.join(CACHE, 'box_player.parquet')), reason='no nbl/cache')


def _build(games, players):
    tg = frame.team_features(frame.team_box(players, games), games)
    return frame.add_player_features(players, tg), tg


@pytest.fixture(scope='module')
def base():
    results = pd.read_parquet(os.path.join(CACHE, 'results.parquet'))
    box = pd.read_parquet(os.path.join(CACHE, 'box_player.parquet'))
    games = frame.base_games(results)
    games = games[games.season.isin([2024, 2025])].reset_index(drop=True)
    players = frame.base_players(box, games)
    return games, players


def test_a_games_own_stats_never_reach_its_features(base):
    games, players = base
    target = games[games.season == 2025].game.iloc[60]
    before, tb = _build(games, players)
    g2, p2 = games.copy(), players.copy()
    rows = p2.game == target
    for c in frame.STATS + ['min', 'pra', 'eff']:
        p2.loc[rows, c] = p2.loc[rows, c] * 3 + 7
    g2.loc[g2.game == target, ['home_score', 'away_score']] = [150, 40]
    after, ta = _build(g2, p2)

    f = frame.PLAYER_FEATURES
    b = before[before.game == target].sort_values(['team', 'key'])[f].reset_index(drop=True)
    a = after[after.game == target].sort_values(['team', 'key'])[f].reset_index(drop=True)
    pd.testing.assert_frame_equal(b, a)
    tf = ['poss_ew', 'ortg_ew', 'drtg_ew', 'margin_ew', 'elo_margin', 'league_poss', 'league_pts']
    pd.testing.assert_frame_equal(tb[tb.game == target].sort_values('team')[tf].reset_index(drop=True),
                                  ta[ta.game == target].sort_values('team')[tf].reset_index(drop=True))
    bb, ba = frame.bottom_up(before), frame.bottom_up(after)
    pd.testing.assert_frame_equal(bb[bb.game == target].sort_values('team').reset_index(drop=True),
                                  ba[ba.game == target].sort_values('team').reset_index(drop=True))
    # and the tamper did reach later games, so the test would notice a broken shift
    later = before[before.tip > before[before.game == target].tip.iloc[0]].game.unique()[:40]
    bl = before[before.game.isin(later)].sort_values(['game', 'team', 'key'])
    al = after[after.game.isin(later)].sort_values(['game', 'team', 'key'])
    assert (bl.r_pts.to_numpy() != al.r_pts.to_numpy()).any()
    assert (bl.elo_margin.to_numpy() != al.elo_margin.to_numpy()).any()


def test_minutes_parse_both_source_formats():
    s = pd.Series(['27:09', '0', '40', '00:00', None])
    out = frame._minutes(s)
    assert out.iloc[0] == pytest.approx(27.15)
    assert list(out.iloc[1:4]) == [0.0, 40.0, 0.0]
    assert np.isnan(out.iloc[4])


def test_rate_is_shrunk_toward_the_league_and_uses_earlier_games_only():
    lr = {2025: {c: 0.5 for c in frame.RATE_COLS}}
    day = pd.Timestamp('2025-10-01')
    rows = []
    for i, (mins, pts) in enumerate([(20.0, 20.0), (20.0, 0.0)]):
        rows.append(dict(game=f'g{i}', key='a b', season=2025, day=day + pd.Timedelta(days=7 * i), tip=day + pd.Timedelta(days=7 * i),
                         team='T', min=mins, played=1.0, starter=1.0, pra=pts,
                         **{c: (pts if c == 'pts' else 0.0) for c in frame.RATE_COLS}))
    h = frame.player_history(pd.DataFrame(rows), lr).set_index('game')
    assert h.loc['g0', 'r_pts'] == pytest.approx(0.5)                                  # nothing yet: the league rate
    prior = frame.RATE_MEMORY['pts'][1]
    assert h.loc['g1', 'r_pts'] == pytest.approx((20 + prior * 0.5) / (20 + prior))   # game 0 only
    assert h.loc['g1', 'min_last'] == 20.0


def test_squad_context_values_missing_players_at_their_usual_minutes():
    rows = []
    for gm, day, ids in [('g1', '2025-10-01', ['a', 'b', 'c']), ('g2', '2025-10-08', ['a', 'b', 'd'])]:
        for k in ids:
            rows.append(dict(game=gm, tip=pd.Timestamp(day), team='T', key=k, min_ew={'a': 30.0, 'b': 25.0, 'c': 20.0, 'd': 5.0}[k]))
    out = frame.squad_context(pd.DataFrame(rows)).set_index('game')
    assert np.isnan(out.loc['g1', 'min_out'])
    assert out.loc['g2', 'min_out'] == 20.0      # c (usually 20 minutes) did not dress for g2
    assert out.loc['g2', 'min_in'] == 5.0


def test_expected_squads_copy_the_teams_latest_squad_and_stay_empty():
    tip1, tip2 = pd.Timestamp('2026-10-10', tz='UTC'), pd.Timestamp('2026-10-20', tz='UTC')
    cols = ['game', 'season', 'tip', 'day', 'finals', 'round_no', 'venue', 'team', 'opp', 'is_home', 'key', 'player', 'pos',
            'starter', 'min', 'played'] + frame.STATS + ['pra', 'eff']
    rows = []
    for gm, tip, keys in (('g0', tip1 - pd.Timedelta(days=5), ['a', 'z']), ('g1', tip1, ['a', 'b'])):
        for k in keys:
            r = {c: 1.0 for c in cols}
            r.update(game=gm, season=2026, tip=tip, day=tip.tz_localize(None), venue='V', team='T', opp='O', key=k, player=k, pos='G')
            rows.append(r)
    players = pd.DataFrame(rows)[cols]
    games = pd.DataFrame([dict(game='g2', season=2026, tip=tip2, day=tip2.tz_localize(None), finals=0.0, round_no=5.0, venue='V',
                               home='O', away='T', scheduled=True)])
    out = frame.expected_squads(players, games)
    t = out[out.team == 'T']
    assert sorted(t.key) == ['a', 'b']                     # the latest squad (g1), not g0's
    assert t.is_home.eq(0.0).all() and t.opp.eq('O').all()
    assert t[['min', 'played', 'pts']].isna().all().all()  # nothing about the game itself
    assert out[out.team == 'O'].empty                      # a team with no past games gets no squad
