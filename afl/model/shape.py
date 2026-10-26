"""Two more gaps:

  goal-kicking   for goals: shots (goals + behinds) per game over the last 10 and 20, and goal-kicking accuracy over
                 the last 30 shots, shrunk toward the league's. A forward with many shots and poor accuracy is due more
                 goals than his goals alone say; one kicking above his usual accuracy is due fewer.
  range          for every stat: the player's best and worst of his last 10 and how often he cleared his own average
                 (his ceiling and floor), which bears on the milestone prices (25+, 30+) more than on his average.
"""
import numpy as np
import pandas as pd


def goal_kicking(m, prior_shots=20, prior_accuracy=0.55):
    m = m.sort_values(['player_id', 'dt']).copy()
    g = m.groupby('player_id', sort=False)
    m['shots'] = m.G + m.B
    for n in (10, 20):
        m[f'shots_l{n}'] = g.shots.transform(lambda x, n=n: x.shift(1).rolling(n, min_periods=1).mean())
    gs = g.G.transform(lambda x: x.shift(1).rolling(30, min_periods=1).sum())
    ss = g.shots.transform(lambda x: x.shift(1).rolling(30, min_periods=1).sum())
    # shrunk toward a fixed 55% (about the league's long-run rate), so no later season leaks into an earlier row
    m['accuracy30'] = (gs + prior_shots * prior_accuracy) / (ss + prior_shots)
    m['behinds_l10'] = g.B.transform(lambda x: x.shift(1).rolling(10, min_periods=1).mean())
    return m.drop(columns=['shots'])


def player_range(m, stat):
    m = m.sort_values(['player_id', 'dt']).copy()
    g = m.groupby('player_id', sort=False)[stat]
    m[f'{stat}_max10'] = g.transform(lambda x: x.shift(1).rolling(10, min_periods=3).max())
    m[f'{stat}_min10'] = g.transform(lambda x: x.shift(1).rolling(10, min_periods=3).min())
    q = g.transform(lambda x: x.shift(1).rolling(10, min_periods=3).quantile(0.8))
    m[f'{stat}_q80_10'] = q
    return m


def groups(stat):
    out = {'range': [f'{stat}_max10', f'{stat}_min10', f'{stat}_q80_10']}
    if stat == 'G':
        out['goal-kicking'] = ['shots_l10', 'shots_l20', 'accuracy30', 'behinds_l10']
    return out


def add(m, stat):
    m = player_range(m, stat)
    if stat == 'G':
        m = goal_kicking(m)
    return m
