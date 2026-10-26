"""More gaps:

  supply          a team's inside-50s per game over its last 8, the opponent's inside-50s conceded, and the team's
                  marks inside 50: the chances a forward gets
  tackle chances  how much ball the player's team usually concedes (opposition disposals and handballs against it):
                  more opposition ball is more to tackle
  momentum        last game's margin, and the team's results over its last 3 and 6 (a side on a slide, or bouncing back)
  travel load     interstate trips in the team's last 3 games, and whether last week was interstate too
"""
import numpy as np
import pandas as pd

from afl.model.team import CLUB_STATE, VENUE_STATE


def add(m):
    m = m.copy()
    s = lambda c: (c, lambda x: x.sum(min_count=1))
    tg = m.groupby(['game', 'dt', 'team', 'opp', 'venue'], as_index=False).agg(I50=s('I50'), MI5=s('MI5'), D=s('D'), HB=s('HB'),
                                                                            margin=('margin', 'first')).sort_values('dt')
    opp = tg[['game', 'team', 'I50', 'D', 'HB']].rename(columns={'team': 'opp', 'I50': 'I50_against', 'D': 'D_against', 'HB': 'HB_against'})
    tg = tg.merge(opp, on=['game', 'opp'], how='left')
    t = tg.groupby('team')
    roll = lambda c, n=8: t[c].transform(lambda x: x.shift(1).rolling(n, min_periods=3).mean())
    tg['team_I50_l8'] = roll('I50')
    tg['team_MI5_l8'] = roll('MI5')
    tg['team_I50_conc_l8'] = roll('I50_against')
    tg['team_D_conc_l8'] = roll('D_against')
    tg['team_HB_conc_l8'] = roll('HB_against')
    tg['last_margin'] = t.margin.shift(1)
    win = (tg.margin > 0).astype(float).where(tg.margin.notna())
    tg['form3'] = win.groupby(tg.team).transform(lambda x: x.shift(1).rolling(3, min_periods=1).mean())
    tg['form6'] = win.groupby(tg.team).transform(lambda x: x.shift(1).rolling(6, min_periods=1).mean())
    inter = (tg.team.map(CLUB_STATE) != tg.venue.map(VENUE_STATE)).astype(float)
    tg['trips3'] = inter.groupby(tg.team).transform(lambda x: x.shift(1).rolling(3, min_periods=1).sum())
    tg['back_to_back_trip'] = inter * inter.groupby(tg.team).shift(1)
    cols = ['team_I50_l8', 'team_MI5_l8', 'team_I50_conc_l8', 'team_D_conc_l8', 'team_HB_conc_l8', 'last_margin', 'form3',
            'form6', 'trips3', 'back_to_back_trip']
    m = m.merge(tg[['game', 'team'] + cols], on=['game', 'team'], how='left')
    # the opponent's inside-50s conceded, seen from this team's side
    oc = tg[['game', 'team', 'team_I50_conc_l8']].rename(columns={'team': 'opp', 'team_I50_conc_l8': 'opp_I50_conc_l8'})
    return m.merge(oc, on=['game', 'opp'], how='left')


def groups():
    return {
        'supply': ['team_I50_l8', 'team_MI5_l8', 'opp_I50_conc_l8'],
        'tackle chances': ['team_D_conc_l8', 'team_HB_conc_l8'],
        'momentum': ['last_margin', 'form3', 'form6'],
        'travel load': ['trips3', 'back_to_back_trip'],
    }
