"""Ground shape and size, measured rather than typed in: what each ground has done to each stat, overall and for each
position, in its recent games.

AFL grounds differ a lot (Kardinia Park is long and narrow, the SCG and Gabba short and wide, Docklands has a roof),
and the model so far sees only one ground measure: total disposals there against the league (venue_rel). This adds,
per stat, from games before this one:
  venue_{s}_rel        the ground's total {s} per game over its last 20 games, against the league's last 60
  venue_pos_{s}_rel    the same for players of this position group at this ground (a long ground may help forwards'
                       marks and hurt defenders', which an overall figure averages away)
  games_at_venue       how many times the player has played there (familiarity)
Measured effects stand in for dimensions, which would have to be typed from memory and could be wrong.
"""
import numpy as np
import pandas as pd


def add(m, stat, window=20):
    m = m.copy()
    if 'pos' not in m:
        from afl.model.extra import position
        m['pos'] = position(m)
    # the ground overall
    g = m.groupby(['game', 'dt', 'venue'], as_index=False)[stat].sum(min_count=1).sort_values('dt')
    g['ven'] = g.groupby('venue')[stat].transform(lambda x: x.shift(1).rolling(window, min_periods=5).mean())
    g['lg'] = g[stat].shift(1).rolling(60, min_periods=20).mean()
    g[f'venue_{stat}_rel'] = g.ven / g.lg
    m = m.merge(g[['game', f'venue_{stat}_rel']], on='game', how='left')
    # the ground by position: average per player of that position, per game
    p = m.groupby(['game', 'dt', 'venue', 'pos'], as_index=False)[stat].mean().sort_values('dt')
    p['ven'] = p.groupby(['venue', 'pos'])[stat].transform(lambda x: x.shift(1).rolling(window, min_periods=5).mean())
    p['lg'] = p.groupby('pos')[stat].transform(lambda x: x.shift(1).rolling(60, min_periods=20).mean())
    p[f'venue_pos_{stat}_rel'] = p.ven / p.lg
    m = m.merge(p[['game', 'pos', f'venue_pos_{stat}_rel']], on=['game', 'pos'], how='left')
    m = m.sort_values(['player_id', 'dt'])
    m['games_at_venue'] = m.groupby(['player_id', 'venue']).cumcount()
    return m


def columns(stat):
    return [f'venue_{stat}_rel', f'venue_pos_{stat}_rel', 'games_at_venue']
