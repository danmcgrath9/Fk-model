"""One row per player per game for the try-scorer model, every feature known once teams are named.

Try-scorer bets are struck after the Tuesday lists, so a player's position and jersey for the game are
known (late changes aside: RLP records who took the field). Everything else comes from earlier games:

  player   exponentially weighted try rates (fast and slow), career games and tries, games and tries
           in this position group, previous game's position
  team     the team model's expected points for and against (teams-named ratings), team and opponent
           player strength, the team's recent tries per game
  opponent tries the opponent has conceded per game, overall and to this position group

Usage: python -m nrl.model.player_frame nrl/cache  -> nrl/cache/player_frame.parquet
"""
import sys

import numpy as np
import pandas as pd

from nrl.model.team_frame import history

GROUP = {'W': 'edge', 'C': 'edge', 'FB': 'edge', 'FE': 'half', 'HB': 'half', 'HK': 'middle', 'L': 'middle',
         '2R': 'back_row', 'FR': 'middle', 'B': 'bench'}
FEATURES = ['position_code', 'jersey', 'starter', 'try_ew_fast', 'try_ew_slow', 'career_games', 'career_rate',
            'group_games', 'group_rate', 'same_position_as_last', 'exp_for', 'exp_against', 'exp_margin',
            'strength_named', 'opp_strength_named', 'team_tries_ew', 'opp_conceded_ew', 'opp_conceded_group_ew',
            'home', 'league_total', 'is_final']
POSITIONS = ['W', 'C', 'FB', 'FE', 'HB', 'HK', 'L', '2R', 'FR', 'B']
# Champion Data (2014 on): a player's recent attacking involvement, from earlier games only; NaN before 2014
CD_STATS = {'lineBreaks': 'cd_line_breaks', 'tackleBreaks': 'cd_tackle_breaks', 'runMetres': 'cd_run_metres',
            'tryAssists': 'cd_try_assists', 'possessions': 'cd_possessions'}
CD_FEATURES = [f'{v}_ew' for v in CD_STATS.values()]


def cd_features(cache):
    """Per (RLP match_id, RLP player_id): exponentially weighted Champion Data stats BEFORE that game."""
    try:
        cp = pd.read_parquet(f'{cache}/cd_player_games.parquet')
        links = pd.read_parquet(f'{cache}/cd_links.parquet')
        gl = pd.read_parquet(f'{cache}/cd_game_link.parquet')
    except FileNotFoundError:
        return None
    cp = cp[cp.took_field].merge(gl, on='cd_match_id')
    to_rlp = dict(zip(links.cd_player_id, links.player_id))
    cp['player_id'] = cp.playerId.map(to_rlp).fillna(-cp.playerId).astype('int64')
    cp = cp.sort_values('utc_start')
    out = cp[['match_id', 'player_id']].copy()
    for src, name in CD_STATS.items():
        out[f'{name}_ew'] = ew(None, cp.player_id, cp[src].astype(float), 0.15)
    return out.drop_duplicates(['match_id', 'player_id'])


def ew(series_by_key, keys, values, alpha):
    """Exponentially weighted mean of values per key, BEFORE each row (rows must be in time order)."""
    state, out = {}, np.empty(len(values))
    for i, (k, v) in enumerate(zip(keys, values)):
        s = state.get(k)
        out[i] = np.nan if s is None else s
        state[k] = v if s is None else alpha * v + (1 - alpha) * s
    return out


def build(cache):
    tf = pd.read_parquet(f'{cache}/team_frame.parquet')
    pm = history(cache)[1]
    order = tf[['match_id', 'i', 'kick_off', 'season']].drop_duplicates('match_id')
    p = pm.merge(order, on='match_id').sort_values(['i', 'team', 'number']).reset_index(drop=True)
    p['jersey'] = pd.to_numeric(p.number, errors='coerce')
    p['starter'] = (p.jersey <= 13).astype(float)
    p['position'] = p.position.astype(str)
    p['group'] = p.position.map(GROUP).fillna('bench')
    p['position_code'] = p.position.map({k: j for j, k in enumerate(POSITIONS)}).astype(float)
    p['tries'] = p.tries.astype(float)
    p['scored'] = (p.tries > 0).astype(float)

    # player history: counts before this game
    g = p.groupby('player_id')
    p['career_games'] = g.cumcount()
    p['career_tries'] = g.tries.cumsum() - p.tries
    p['career_rate'] = (p.career_tries + 0.15 * 5) / (p.career_games + 5)
    gg = p.groupby(['player_id', 'group'])
    p['group_games'] = gg.cumcount()
    p['group_rate'] = ((gg.tries.cumsum() - p.tries) + 0.15 * 5) / (p.group_games + 5)
    p['try_ew_fast'] = ew(None, p.player_id, p.tries, 0.25)
    p['try_ew_slow'] = ew(None, p.player_id, p.tries, 0.08)
    p['same_position_as_last'] = (p.position == g.position.shift(1)).astype(float)

    # team side, teams-named ratings from the team frame
    cols = ['match_id', 'team', 'opp', 'home', 'exp_for', 'exp_against', 'exp_margin', 'strength_named',
            'opp_strength_named', 'league_total', 'is_final', 'tries_for']
    t = tf[cols].copy()
    t = t.merge(order[['match_id', 'i']], on='match_id').sort_values('i')
    t['team_tries_ew'] = ew(None, t.team, t.tries_for.fillna(0), 0.1)
    t['opp_conceded_ew'] = ew(None, t.opp, t.tries_for.fillna(0), 0.1)   # tries the opp let in, before this game
    p = p.merge(t.drop(columns=['i', 'tries_for']), on=['match_id', 'team'], how='left')

    # tries the opponent concedes to this position group, per game, before this game
    conc = p.groupby(['i', 'match_id', 'opp', 'group']).tries.sum().reset_index().sort_values('i')
    conc['opp_conceded_group_ew'] = ew(None, list(zip(conc.opp, conc.group)), conc.tries, 0.1)
    p = p.merge(conc[['match_id', 'opp', 'group', 'opp_conceded_group_ew']], on=['match_id', 'opp', 'group'], how='left')
    for c in ('home', 'is_final'):
        p[c] = p[c].astype(float)
    cf = cd_features(cache)
    if cf is not None:
        p = p.merge(cf, on=['match_id', 'player_id'], how='left')
    else:
        for c in CD_FEATURES:
            p[c] = np.nan
    return p.sort_values(['i', 'team', 'jersey']).reset_index(drop=True)


def main(cache):
    p = build(cache)
    p.to_parquet(f'{cache}/player_frame.parquet', index=False)
    print(f'player_frame: {len(p):,} player-games, seasons {p.season.min()}-{p.season.max()}')


if __name__ == '__main__':
    main(sys.argv[1])
