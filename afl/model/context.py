"""Game context the model has not used yet, from AFL Tables fields we already hold (all known before the bounce:
start times are fixtured, umpire panels and coaches are announced in the week):

  game time        night (start 6pm or later, local), twilight (4pm to 6pm), day of week. Dew at night is said to make
                   the ball slippery, which would cut marks and lift handballs and ground balls.
  umpire crew      the field umpires' recent games: total tackles and free kicks per game against the league. Crews differ
                   in how readily they pay holding the ball, which is a tackle the stats count either way, and in frees.
  coach            games the team has had under its current coach, and a new-coach flag (first 15 games): a new coach
                   brings a new game plan, which old form does not show.
  ruck matchup     the named side's best ruckman (hitouts per game over his last 10) against the opposition's, so a
                   midfielder fed by a dominant ruck is seen as such.
  opposition style the opponent's recent kicks per handball and share of uncontested possession (a chain-handball side
                   gives up a different game from a long-kicking one).
"""
import numpy as np
import pandas as pd

from afl.model.frame import TEAM


def game_info(cache):
    a = pd.read_parquet(f'{cache}/afltables.parquet', columns=['Date', 'Home.team', 'Away.team', 'Local.start.time',
                                                              'Umpire.1', 'Umpire.2', 'Umpire.3', 'Umpire.4', 'Playing.for', 'Coach'])
    a['date'] = pd.to_datetime(a.Date).dt.strftime('%Y-%m-%d')
    a['game'] = a.date + '|' + a['Home.team'].replace(TEAM) + '|' + a['Away.team'].replace(TEAM)
    a['team'] = a['Playing.for'].replace(TEAM)
    g = a.drop_duplicates('game')[['game', 'Local.start.time', 'Umpire.1', 'Umpire.2', 'Umpire.3', 'Umpire.4']]
    c = a.drop_duplicates(['game', 'team'])[['game', 'team', 'Coach']]
    return g, c


def add(m, cache, stat):
    m = m.copy()
    g, c = game_info(cache)
    m = m.merge(g, on='game', how='left').merge(c, on=['game', 'team'], how='left')
    t = m['Local.start.time']
    m['night'] = (t >= 1800).astype(float).where(t.notna())
    m['twilight'] = ((t >= 1600) & (t < 1800)).astype(float).where(t.notna())
    m['weekday'] = m.dt.dt.weekday.astype(float)

    # umpire crew: each field umpire's last 15 games, the game's total tackles and frees against the league
    tg = m.groupby(['game', 'dt'], as_index=False).agg(T=('T', lambda s: s.sum(min_count=1)), FF=('FF', lambda s: s.sum(min_count=1)))
    tg = tg.merge(g[['game', 'Umpire.1', 'Umpire.2', 'Umpire.3', 'Umpire.4']], on='game', how='left').sort_values('dt')
    tg['lgT'] = tg['T'].shift(1).rolling(60, min_periods=20).mean()
    tg['lgF'] = tg['FF'].shift(1).rolling(60, min_periods=20).mean()
    long = tg.melt(id_vars=['game', 'dt', 'T', 'FF'], value_vars=['Umpire.1', 'Umpire.2', 'Umpire.3', 'Umpire.4'], value_name='ump').dropna(subset=['ump'])
    long = long.sort_values('dt')
    for col in ('T', 'FF'):
        long[f'u_{col}'] = long.groupby('ump')[col].transform(lambda x: x.shift(1).rolling(15, min_periods=5).mean())
    crew = long.groupby('game')[['u_T', 'u_FF']].mean().reset_index()
    tg = tg.merge(crew, on='game', how='left')
    tg['ump_T_rel'] = tg.u_T / tg.lgT
    tg['ump_FF_rel'] = tg.u_FF / tg.lgF
    m = m.merge(tg[['game', 'ump_T_rel', 'ump_FF_rel']], on='game', how='left')

    # coach: games under the current coach, new-coach flag
    tc = m.drop_duplicates(['game', 'team'])[['game', 'dt', 'team', 'Coach']].sort_values('dt')
    tc['coach_games'] = tc.groupby(['team', 'Coach']).cumcount()
    tc['new_coach'] = (tc.coach_games < 15).astype(float)
    # a team's first coach in our data would look "new"; only flag a coach who followed another at the same club
    first = tc.groupby('team').Coach.transform('first')
    tc.loc[tc.Coach == first, 'new_coach'] = 0.0
    m = m.merge(tc[['game', 'team', 'coach_games', 'new_coach']], on=['game', 'team'], how='left')

    # ruck matchup: best named ruck per side by hitouts per game over his last 10
    r = m.groupby(['game', 'team'], as_index=False).HO_pg.max().rename(columns={'HO_pg': 'own_ruck_HO'})
    m = m.merge(r, on=['game', 'team'], how='left')
    m = m.merge(r.rename(columns={'team': 'opp', 'own_ruck_HO': 'opp_ruck_HO'}), on=['game', 'opp'], how='left')
    m['ruck_edge'] = m.own_ruck_HO - m.opp_ruck_HO

    # opposition style: their own recent kicks per handball and uncontested share
    st = m.groupby(['game', 'dt', 'team'], as_index=False).agg(K=('K', lambda s: s.sum(min_count=1)), HB=('HB', lambda s: s.sum(min_count=1)),
                                                               UP=('UP', lambda s: s.sum(min_count=1)), CP=('CP', lambda s: s.sum(min_count=1))).sort_values('dt')
    for col in ('K', 'HB', 'UP', 'CP'):
        st[f'{col}8'] = st.groupby('team')[col].transform(lambda x: x.shift(1).rolling(8, min_periods=3).mean())
    st['opp_kick_ratio'] = st.K8 / st.HB8
    st['opp_up_share'] = st.UP8 / (st.UP8 + st.CP8)
    m = m.merge(st[['game', 'team', 'opp_kick_ratio', 'opp_up_share']].rename(columns={'team': 'opp'}), on=['game', 'opp'], how='left')
    return m.drop(columns=['Local.start.time', 'Umpire.1', 'Umpire.2', 'Umpire.3', 'Umpire.4', 'Coach'])


def groups():
    return {
        'game time': ['night', 'twilight', 'weekday'],
        'umpire crew': ['ump_T_rel', 'ump_FF_rel'],
        'coach': ['coach_games', 'new_coach'],
        'ruck matchup': ['own_ruck_HO', 'opp_ruck_HO', 'ruck_edge'],
        'opposition style': ['opp_kick_ratio', 'opp_up_share'],
    }
