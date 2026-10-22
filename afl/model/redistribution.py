"""Who inherits the ball when a teammate is out (docs/RESEARCH_BEST_MODEL.md, rank 5).

The model already sees the team's outs as totals (outs_D, outs_CCL) and each player's share of the named side's usual
disposals. This adds, per stat:
  gone_{s}       usual {s} of players who played the team's previous game and not this one
  inherit_{s}    gone_{s} x the player's share of the named side's usual {s}: a share-weighted guess at what comes his way
  inherit_ccl    the team's missing centre clearances x the player's share of the named side's centre clearances
  wowy_{s}       his own record in past games where a key midfielder was out (2+ usual centre clearances missing),
                 relative to his record at the time, shrunk toward 1 when there are few such games
All from games before this one.
"""
import numpy as np
import pandas as pd


def team_index(m):
    tg = m[['team', 'game', 'dt']].drop_duplicates().sort_values('dt')
    tg['tidx'] = tg.groupby('team').cumcount()
    return m.merge(tg[['team', 'game', 'tidx']], on=['team', 'game'], how='left')


def outs(m, col):
    """Per team-game: sum of `col` (as of each missing player's last game) over players in the previous game, not this."""
    p = m[['team', 'tidx', 'player_id', col]].copy()
    nxt = p.assign(tidx=p.tidx + 1)
    here = m[['team', 'tidx', 'player_id']].assign(here=1)
    gone = nxt.merge(here, on=['team', 'tidx', 'player_id'], how='left')
    gone = gone[gone.here.isna()]
    played = m[['team', 'tidx']].drop_duplicates()
    s = gone.groupby(['team', 'tidx'])[col].sum().rename(f'outs_{col}')
    return played.merge(s.reset_index(), on=['team', 'tidx'], how='left').fillna({f'outs_{col}': 0.0})


def add(m, stat, shrink=4):
    m = team_index(m)
    o = outs(m, f'{stat}_l10').rename(columns={f'outs_{stat}_l10': f'gone_{stat}'})
    m = m.merge(o, on=['team', 'tidx'], how='left')
    m.loc[m.tidx == 0, f'gone_{stat}'] = np.nan
    pool = m.groupby(['game', 'team'])[f'{stat}_l10'].transform('sum')
    m[f'inherit_{stat}'] = m[f'gone_{stat}'] * m[f'{stat}_l10'] / pool.replace(0, np.nan)
    m['inherit_ccl'] = m.outs_CCL * m.CCL_pg / m.groupby(['game', 'team']).CCL_pg.transform('sum').replace(0, np.nan)
    # with or without you: his stat in past games with a key midfielder out, against his record at the time
    m = m.sort_values(['player_id', 'dt'])
    key_out = (m.outs_CCL >= 2).astype(float)
    g = m.groupby('player_id', sort=False)
    val = m[stat] * key_out
    s = val.groupby(m.player_id).transform(lambda x: x.shift(1).expanding().sum())
    n = key_out.groupby(m.player_id).transform(lambda x: x.shift(1).expanding().sum())
    overall = g[stat].transform(lambda x: x.shift(1).expanding().mean())
    rel = (s / n.replace(0, np.nan)) / overall.replace(0, np.nan)
    w = n / (n + shrink)
    m[f'wowy_{stat}'] = (w * rel + (1 - w)).where(n > 0, 1.0) * key_out.where(key_out > 0, np.nan)
    return m.drop(columns=['tidx'])


def columns(stat):
    return [f'gone_{stat}', f'inherit_{stat}', 'inherit_ccl', f'wowy_{stat}']
