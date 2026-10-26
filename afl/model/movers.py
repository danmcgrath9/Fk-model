"""Players who have changed clubs: is a recent mover projected badly, and does he lift against his old club?

Per player-game, from games before it:
  club_games       games played for his current club so far
  new_club         1 in his first 16 games at a club, after 20+ games elsewhere (a traded or delisted-and-picked-up
                   player settling into a new role)
  vs_former_club   1 when the opponent is a club he played 20+ games for
  role_shift       his disposals per game at this club so far against his last 10 at his old club (how much the move
                   changed his role), shrunk toward 1 over his first few games
The player's form features already follow him across clubs (they are keyed by player); these ask whether the move
itself carries information the form does not.
"""
import numpy as np
import pandas as pd


def add(m, stat, shrink=4):
    m = m.sort_values(['player_id', 'dt']).copy()
    g = m.groupby('player_id', sort=False)
    m['club_games'] = m.groupby(['player_id', 'team'], sort=False).cumcount()
    games_before = g.cumcount()
    elsewhere = games_before - m.club_games
    m['new_club'] = ((m.club_games < 16) & (elsewhere >= 20)).astype(float)
    # clubs he had played 20+ games for before this game (excluding his current one)
    seen = {}
    vs = np.zeros(len(m))
    for i, (pid, team, opp) in enumerate(zip(m.player_id.to_numpy(), m.team.to_numpy(), m.opp.to_numpy())):
        c = seen.setdefault(pid, {})
        vs[i] = 1.0 if (opp != team and c.get(opp, 0) >= 20) else 0.0
        c[team] = c.get(team, 0) + 1
    m['vs_former_club'] = vs
    # role shift: per-game {stat} at this club so far, against his last-10 average when he arrived
    pc = m.groupby(['player_id', 'team'], sort=False)[stat]
    at_club = pc.transform(lambda x: x.shift(1).expanding().mean())
    l10 = m[f'{stat}_l10'] if f'{stat}_l10' in m else g[stat].transform(lambda x: x.shift(1).rolling(10, min_periods=1).mean())
    arrival = l10.where(m.club_games == 0).groupby([m.player_id, m.team]).transform('first')
    w = m.club_games / (m.club_games + shrink)
    rel = (at_club / arrival.replace(0, np.nan))
    m[f'role_shift_{stat}'] = (w * rel + (1 - w)).where((elsewhere >= 20) & (m.club_games > 0), 1.0)
    return m


def columns(stat):
    return ['club_games', 'new_club', 'vs_former_club', f'role_shift_{stat}']
