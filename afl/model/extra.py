"""Extra pre-game inputs for the props: opponent by position, weather, returning players, dead rubbers, player-specific
history against the opponent and at the ground, interstate travel. Each is tested in afl/model/extra_test.py and kept
only where it improves the unseen seasons.

Position comes from the player's own recent role stats (shifted one game), not a list, so it exists for every season
including 2026 and follows role changes: ruck (hitouts), midfield (centre clearances / clearances), forward (goals,
marks inside 50), defence (rebounds, intercepts, spoils), else general.
"""
import numpy as np
import pandas as pd

from afl.model.team import CLUB_STATE, VENUE_STATE

POS = ['ruck', 'mid', 'fwd', 'def', 'gen']


def position(m):
    pos = np.full(len(m), 'gen', dtype=object)
    pos[(m.R50_pg + 0.5 * m.ITC_pg + 0.5 * m.OP_pg >= 3.5).to_numpy()] = 'def'
    pos[(m.G_pg + 0.5 * m.MI5_pg >= 1.0).to_numpy()] = 'fwd'
    pos[((m.CCL_pg >= 1.5) | (m.CL_pg >= 3.5)).to_numpy()] = 'mid'
    pos[(m.HO_pg >= 8).to_numpy()] = 'ruck'
    return pos


def opponent_by_position(m, stat, window=8):
    """What this opponent has conceded lately to players of this position, against the league for that position."""
    d = m[['game', 'dt', 'opp', 'pos', stat]].copy()
    per = d.groupby(['game', 'dt', 'opp', 'pos'], as_index=False)[stat].mean()        # 'opp' here = the defending team
    per = per.sort_values('dt')
    per['conc'] = per.groupby(['opp', 'pos'])[stat].transform(lambda x: x.shift(1).rolling(window, min_periods=3).mean())
    lg = d.groupby(['dt', 'pos'])[stat].mean().reset_index().sort_values('dt')
    lg['league'] = lg.groupby('pos')[stat].transform(lambda x: x.shift(1).rolling(60, min_periods=10).mean())
    per = per.merge(lg[['dt', 'pos', 'league']], on=['dt', 'pos'], how='left')
    per[f'{stat}_opp_pos_rel'] = per.conc / per.league
    return m.merge(per[['game', 'opp', 'pos', f'{stat}_opp_pos_rel']], on=['game', 'opp', 'pos'], how='left')


def returning(m):
    """Team games missed since the player's previous appearance for this team (0 = played last week)."""
    tg = m[['team', 'game', 'dt']].drop_duplicates().sort_values('dt')
    tg['tidx'] = tg.groupby('team').cumcount()
    m = m.merge(tg[['team', 'game', 'tidx']], on=['team', 'game'], how='left')
    m = m.sort_values(['player_id', 'dt'])
    prev = m.groupby(['player_id', 'team']).tidx.shift(1)
    m['games_missed'] = (m.tidx - prev - 1).clip(lower=0, upper=20)
    m['back_from_absence'] = (m.games_missed >= 2).astype(float)
    return m.drop(columns=['tidx'])


def dead_rubber(m):
    """Home-and-away games a team plays after it can no longer reach the top 8 on wins (the cruder, safe reading)."""
    g = m[~m.finals.astype(bool)].drop_duplicates(['game', 'team'])[['season', 'game', 'dt', 'team', 'margin']].sort_values('dt')
    g['win'] = (g.margin > 0).astype(float) + 0.5 * (g.margin == 0)
    g['wins_before'] = g.groupby(['season', 'team']).win.transform(lambda x: x.shift(1).fillna(0).cumsum())
    g['played'] = g.groupby(['season', 'team']).cumcount()
    total = g.groupby(['season', 'team']).game.transform('count')
    g['remaining'] = total - g.played
    rows = []
    for (season, dt_), day in g.groupby(['season', 'dt']):
        # ladder as it stood before this day: each team's latest wins_before up to now
        hist = g[(g.season == season) & (g.dt <= dt_)].sort_values('dt').groupby('team').tail(1)
        eighth = hist.wins_before.sort_values(ascending=False).iloc[7] if len(hist) >= 8 else 0
        for r in day.itertuples():
            rows.append((r.game, r.team, float(r.wins_before + r.remaining < eighth)))
    dr = pd.DataFrame(rows, columns=['game', 'team', 'dead_rubber'])
    return m.merge(dr, on=['game', 'team'], how='left')


def player_history(m, stat, key, name, shrink=3):
    """The player's average for this stat in past games against this opponent (key='opp') or at this ground
    (key='venue'), relative to his overall average at the time, shrunk toward 1 when there are few such games."""
    m = m.sort_values(['player_id', 'dt']).copy()
    g = m.groupby(['player_id', key], sort=False)[stat]
    s = g.transform(lambda x: x.shift(1).expanding().sum())
    n = g.transform(lambda x: x.shift(1).expanding().count())
    overall = m.groupby('player_id')[stat].transform(lambda x: x.shift(1).expanding().mean())
    rel = (s / n) / overall.replace(0, np.nan)
    w = n / (n + shrink)
    m[name] = (w * rel + (1 - w)).where(n > 0, 1.0)
    return m


def weather(m, cache):
    v = pd.read_parquet(f'{cache}/frame_values.parquet', columns=['game', 'match_weather_type', 'match_weather_temp_c']).drop_duplicates('game')
    m = m.merge(v, on='game', how='left')
    wt = m.match_weather_type.astype('string')
    known = wt.notna()
    m['wet'] = wt.str.contains('RAIN|THUNDER', na=False).astype(float).where(known)
    m['windy'] = wt.str.contains('WIND', na=False).astype(float).where(known)
    m['roof'] = wt.str.contains('ROOF', na=False).astype(float).where(known)
    m['temp'] = m.match_weather_temp_c
    return m.drop(columns=['match_weather_type', 'match_weather_temp_c'])


def add_extra(m, cache, stat):
    m = m.copy()
    m['pos'] = position(m)
    m = opponent_by_position(m, stat)
    m = returning(m)
    m = dead_rubber(m)
    m = player_history(m, stat, 'opp', f'{stat}_vs_opp')
    m = player_history(m, stat, 'venue', f'{stat}_at_venue')
    m = weather(m, cache)
    m['interstate'] = (m.team.map(CLUB_STATE) != m.venue.map(VENUE_STATE)).astype(float)
    for p in POS:
        m[f'pos_{p}'] = (m.pos == p).astype(float)
    return m


def extra_groups(stat):
    return {
        'opponent by position': [f'{stat}_opp_pos_rel'] + [f'pos_{p}' for p in POS],
        'weather': ['wet', 'windy', 'roof', 'temp'],
        'returning / dead rubber': ['games_missed', 'back_from_absence', 'dead_rubber'],
        'player vs this opponent': [f'{stat}_vs_opp'],
        'player at this ground': [f'{stat}_at_venue'],
        'interstate travel': ['interstate'],
    }
