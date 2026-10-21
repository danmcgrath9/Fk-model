"""No feature may see its own game. Change a game's balls and result, rebuild, compare that game's features.

Runs on a made-up league (tests/synth.py), so it needs no data; the same check on the real pull runs in
the bbl-frame workflow when bbl/cache/parquet is present.
"""
import os

import numpy as np
import pandas as pd
import pytest

from bbl.model import frame
from bbl.tests import synth

CACHE = os.path.join(os.path.dirname(__file__), '..', 'cache', 'parquet')


def tamper(dl, inn, m, target):
    dl, inn, m = dl.copy(), inn.copy(), m.copy()
    rows = dl.match_id == target
    dl.loc[rows, 'runs_batter'] = 6
    dl.loc[rows, 'runs_total'] = 6 + dl.loc[rows, 'runs_extras']
    dl.loc[rows & (dl.seq == 1), ['player_out', 'wicket_kind', 'n_wickets']] = [None, None, 0]
    inn.loc[inn.match_id == target, 'runs'] += 200
    r = m.match_id == target
    m.loc[r, 'winner'] = np.where(m.loc[r, 'winner'] == m.loc[r, 'team1'], m.loc[r, 'team2'], m.loc[r, 'team1'])
    m.loc[r, 'result'] = 'win'
    return dl, inn, m


def check(m, pl, dl, inn, target, later_n=5):
    g0, t0 = frame.build_from(m, pl, dl, inn)
    d2, i2, m2 = tamper(dl, inn, m, target)
    g1, t1 = frame.build_from(m2, pl, d2, i2)
    key = ['match_id', 'team', 'pid']
    pf = frame.PLAYER + [c for c in frame.TEAM_NAMED if c in g0.columns]
    a = g0[g0.match_id == target].sort_values(key)[pf].reset_index(drop=True)
    b = g1[g1.match_id == target].sort_values(key)[pf].reset_index(drop=True)
    pd.testing.assert_frame_equal(a, b)
    tf = frame.TEAM_NAMED
    a = t0[t0.match_id == target].sort_values('team')[tf].reset_index(drop=True)
    b = t1[t1.match_id == target].sort_values('team')[tf].reset_index(drop=True)
    pd.testing.assert_frame_equal(a, b)
    # and the tamper reached later games, so the test would notice a broken shift
    later = sorted(m.loc[m.start_date > m.loc[m.match_id == target, 'start_date'].iloc[0], 'match_id'])[:later_n]
    x0 = g0[g0.match_id.isin(later)].sort_values(key).pre_runs_pg.fillna(-1).to_numpy()
    x1 = g1[g1.match_id.isin(later)].sort_values(key).pre_runs_pg.fillna(-1).to_numpy()
    assert (x0 != x1).any()
    y0 = t0[t0.match_id.isin(later)].sort_values(['match_id', 'team']).elo_pre.to_numpy()
    y1 = t1[t1.match_id.isin(later)].sort_values(['match_id', 'team']).elo_pre.to_numpy()
    assert (y0 != y1).any()


def test_a_games_own_result_never_reaches_its_features():
    m, pl, dl, inn = synth.league()
    check(m, pl, dl, inn, 'm012')


def test_batting_position_and_counts():
    m, pl, dl, inn = synth.league(n_matches=2)
    g, t = frame.build_from(m, pl, dl, inn)
    first = dl[(dl.match_id == 'm000') & (dl.innings == 1)].iloc[0]
    row = g[(g.match_id == 'm000') & (g.player == first.batter)].iloc[0]
    assert row.bat_pos == 1
    assert g[(g.match_id == 'm000') & (g.player == first.non_striker)].bat_pos.iloc[0] == 2
    # a player's runs add up to the innings' runs less extras
    for (mid, team), x in g.groupby(['match_id', 'team']):
        i = inn[(inn.match_id == mid) & (inn.team == team)].iloc[0]
        extras = dl[(dl.match_id == mid) & (dl.team == team)].runs_extras.sum()
        assert x.bat_runs.fillna(0).sum() == i.runs - extras
    assert set(g.did_bat.unique()) <= {0, 1}
    assert t.groupby('match_id').size().eq(2).all()


def test_first_game_knows_nothing():
    m, pl, dl, inn = synth.league(n_matches=3)
    g, t = frame.build_from(m, pl, dl, inn)
    first = g[g.match_id == 'm000']
    assert first.pre_runs_pg.isna().all() and (first.pre_games == 0).all()
    assert (t[t.match_id == 'm000'].elo_pre == 1500).all()
    assert t[t.match_id == 'm000'].xi_runs_open.isna().all()     # no previous XI: at the open knows nothing of the side


def test_venue_names_collapse():
    assert frame.canon_venue('Brisbane Cricket Ground, Woolloongabba, Brisbane') == 'Gabba'
    assert frame.canon_venue('Western Australia Cricket Association Ground') == frame.canon_venue('W.A.C.A. Ground')
    assert frame.canon_venue('Simonds Stadium, South Geelong, Victoria') == frame.canon_venue('GMHBA Stadium, South Geelong, Victoria')
    assert frame.season_split('2019/20') == 'fit' and frame.season_split('2022/23') == 'choose'
    assert frame.season_split('2024/25') == 'confirm' and frame.season_split('2025/26') == 'final'


@pytest.mark.skipif(not os.path.exists(os.path.join(CACHE, 't20_matches.parquet')), reason='no bbl/cache/parquet')
def test_real_bbl_venues_and_teams():
    m = frame.match_table(pd.read_parquet(os.path.join(CACHE, 't20_matches.parquet')))
    b = m[m.comp == 'BBL']
    assert b.venue_c.nunique() <= 22
    assert len(set(b.team1) | set(b.team2)) == 8


def add_future(m, pl, n=2):
    """Append n unplayed games for the last game's two sides, with that game's XIs."""
    last = m.iloc[-1]
    fm, fp = [], []
    for k in range(n):
        mid = f'f{k}'
        fm.append(dict(match_id=mid, competition='Big Bash League', season=last.season,
                       start_date=(pd.Timestamp(last.start_date) + pd.Timedelta(days=3 + k)).strftime('%Y-%m-%d'),
                       gender='male', team1=last.team1, team2=last.team2, venue=last.venue, toss_winner=None,
                       toss_decision=None, bat_first=None, winner=None, result=None, method=None, future=True))
        fp.append(pl[pl.match_id == last.match_id].assign(match_id=mid))
    return pd.concat([m.assign(future=False), pd.DataFrame(fm)], ignore_index=True), pd.concat([pl] + fp, ignore_index=True)


def test_unplayed_games_are_not_observations():
    m, pl, dl, inn = synth.league(n_matches=12)
    g0, t0 = frame.build_from(m, pl, dl, inn)
    m2, pl2 = add_future(m, pl)
    g1, t1 = frame.build_from(m2, pl2, dl, inn)
    # the played games are untouched
    key = ['match_id', 'team', 'pid']
    cols = frame.PLAYER + ['elo_pre', 'venue_first_runs']
    a = g0.sort_values(key)[cols].reset_index(drop=True)
    b = g1[~g1.match_id.str.startswith('f')].sort_values(key)[cols].reset_index(drop=True)
    pd.testing.assert_frame_equal(a, b)
    # and the second unplayed game sees the same form as the first: the first was not counted as a game
    f0 = g1[g1.match_id == 'f0'].sort_values(['team', 'pid'])
    f1 = g1[g1.match_id == 'f1'].sort_values(['team', 'pid'])
    for c in ['pre_' + x for x in frame.PLAYER_STATE] + ['pre_comp_runs_pg', 'pre_comp_games']:
        np.testing.assert_allclose(f0[c].to_numpy(float), f1[c].to_numpy(float), equal_nan=True, err_msg=c)
    assert t1[t1.match_id == 'f1'].elo_pre.tolist() == t1[t1.match_id == 'f0'].elo_pre.tolist()
    # the ground's history reaches an unplayed game (the made-up league's 10-over innings never count as full,
    # so check the ground's game count rather than its average)
    assert (t1[t1.match_id == 'f0'].venue_games > 0).all()
    assert t1[t1.match_id == 'f1'].venue_games.tolist() == t1[t1.match_id == 'f0'].venue_games.tolist()


@pytest.mark.skipif(not os.path.exists(os.path.join(CACHE, 't20_deliveries.parquet')), reason='no bbl/cache/parquet')
def test_real_data_a_bbl_games_own_result_never_reaches_its_features():
    """The tamper test on the real pull: every T20 match from June 2024 to February 2025, a mid-season BBL game."""
    m = pd.read_parquet(os.path.join(CACHE, 't20_matches.parquet'))
    m = m[(m.start_date >= '2024-06-01') & (m.start_date <= '2025-02-15')]
    ids = set(m.match_id)
    pl = pd.read_parquet(os.path.join(CACHE, 't20_players.parquet'))
    dl = pd.read_parquet(os.path.join(CACHE, 't20_deliveries.parquet'))
    inn = pd.read_parquet(os.path.join(CACHE, 't20_innings.parquet'))
    pl, dl, inn = pl[pl.match_id.isin(ids)], dl[dl.match_id.isin(ids)], inn[inn.match_id.isin(ids)]
    bbl = m[(m.competition == frame.BBL) & (m.season == '2024/25')].sort_values('start_date')
    check(m, pl, dl, inn, bbl.match_id.iloc[len(bbl) // 2], later_n=40)


def test_list_order_never_reaches_a_feature():
    """Cricsheet lists each XI in the order it batted in that game. Shuffling it must move no feature."""
    m, pl, dl, inn = synth.league(n_matches=12)
    g0, _ = frame.build_from(m, pl, dl, inn)
    rng = np.random.default_rng(3)
    pl2 = pl.copy()
    pl2['list_order'] = pl2.groupby(['match_id', 'team']).list_order.transform(lambda s: rng.permutation(s.to_numpy()))
    g1, _ = frame.build_from(m, pl2, dl, inn)
    from bbl.model import props
    feats = sorted(set(frame.PLAYER + props.BAT + props.BOWL + props.CTX) & set(g0.columns))
    assert 'list_order' not in feats
    key = ['match_id', 'team', 'pid']
    pd.testing.assert_frame_equal(g0.sort_values(key)[feats].reset_index(drop=True), g1.sort_values(key)[feats].reset_index(drop=True))
