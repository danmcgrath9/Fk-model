"""One row per player per game, with features that were all known before that game.

Known before the bounce means: the player's own past games, the two final 22s (teams are
named Thursday night and final changes are made just before the bounce), the teams' past
results, the venue and the date. Nothing from the game itself. Every rolling figure is
shifted one game, and tests/test_frame.py checks that changing a game's stats leaves that
game's features untouched.

Built from the fitzRoy mirror (afl/data/mirror.py): AFL Tables for results, venues, ages and
the substitute flag; Footywire for the stat set (time on ground, metres gained, centre
clearances, SuperCoach and so on). Home-and-away and finals both kept; finals are flagged.

Usage: python -m afl.model.frame afl/cache  (writes afl/cache/frame.parquet)
"""
import re
import sys
import unicodedata

import numpy as np
import pandas as pd

TEAM = {'Brisbane Lions': 'Brisbane', 'Footscray': 'Western Bulldogs', 'Greater Western Sydney': 'GWS'}
STATS = ['D', 'K', 'HB', 'M', 'G', 'B', 'T', 'HO', 'GA', 'I50', 'CL', 'CG', 'R50', 'FF', 'FA', 'AF', 'SC', 'CP', 'UP',
         'ED', 'DE', 'CM', 'MI5', 'One.Percenters', 'BO', 'TOG', 'MG', 'SI', 'TO', 'ITC', 'T5', 'CCL', 'SCL']
ELO_K, ELO_HGA, ELO_CARRY = 0.08, 8.0, 0.7     # margin points per point of error, home ground, share kept over summer


def _ascii(s):
    return unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().lower()


def _key(name):
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z ]', '', _ascii(name))).strip()


def _surname(name):
    # Footywire shortens hyphenated surnames ("Luke D-Uniacke"): key on the last hyphen part
    return re.sub(r'[^a-z]', '', re.split(r'[ -]', _ascii(name).strip())[-1])


def join_sources(at, fw):
    """AFL Tables rows with Footywire's stats attached, matched on date, team and player name."""
    at = at.copy()
    at['team'] = at.Team.replace(TEAM)
    at['home_team'] = at['Home.team'].replace(TEAM)
    at['away_team'] = at['Away.team'].replace(TEAM)
    at['date'] = pd.to_datetime(at.Date).dt.strftime('%Y-%m-%d')
    at['key'] = at.Player.map(_key)
    at['sur'] = at.Surname.map(_surname)
    at['ini'] = at['First.name'].map(_key).str[:1]

    fw = fw.copy().rename(columns={'One.Percenters': 'One.Percenters'})
    fw['team'] = fw.Team
    fw['date'] = pd.to_datetime(fw.Date).dt.strftime('%Y-%m-%d')
    fw['key'] = fw.Player.map(_key)
    fw['sur'] = fw.Player.str.replace(r'[^\w \-]', '', regex=True).map(_surname)
    fw['ini'] = fw.key.str[:1]
    fw = fw.drop_duplicates(['date', 'team', 'key'])
    cols = [c for c in STATS if c in fw.columns]

    m = at.merge(fw[['date', 'team', 'key'] + cols], on=['date', 'team', 'key'], how='left', suffixes=('_at', ''))
    miss = m['D'].isna().to_numpy()
    fb = at.loc[miss, ['date', 'team', 'sur', 'ini']].reset_index()
    fw2 = fw.drop_duplicates(['date', 'team', 'sur', 'ini'], keep=False)
    fb = fb.merge(fw2[['date', 'team', 'sur', 'ini'] + cols], on=['date', 'team', 'sur', 'ini'], how='left').set_index('index')
    m.loc[miss, cols] = fb[cols].to_numpy()
    return m, cols


def base_table(at, fw):
    m, cols = join_sources(at, fw)
    home = m.team == m.home_team
    m['opp'] = np.where(home, m.away_team, m.home_team)
    m['is_home'] = home.astype(float)
    m['score_for'] = np.where(home, m['Home.score'], m['Away.score']).astype(float)
    m['score_against'] = np.where(home, m['Away.score'], m['Home.score']).astype(float)
    m['margin'] = m.score_for - m.score_against
    m['game'] = m.date + '|' + m.home_team + '|' + m.away_team
    m['finals'] = ~m.Round.astype(str).str.fullmatch(r'\d+')
    m['round_no'] = pd.to_numeric(m.Round, errors='coerce')
    m['season'] = m.Season.astype(int)
    m['player_id'] = pd.to_numeric(m.ID, errors='coerce')
    m['named_sub'] = (m.Substitute.astype('string') == 'On').astype(float)     # started on the bench as the named sub
    m['subbed_off'] = (m.Substitute.astype('string') == 'Off').astype(float)
    m['age'] = pd.to_numeric(m.Age, errors='coerce')
    m['dt'] = pd.to_datetime(m.date)
    m = m[m.player_id.notna() & m.D.notna()].copy()
    keep = ['season', 'Round', 'round_no', 'finals', 'date', 'dt', 'game', 'Venue', 'team', 'opp', 'is_home',
            'score_for', 'score_against', 'margin', 'player_id', 'Player', 'age', 'named_sub', 'subbed_off'] + cols
    return m[keep].rename(columns={'One.Percenters': 'OP', 'Venue': 'venue'}).sort_values(['dt', 'game', 'team']).reset_index(drop=True)


def elo(games):
    """Pre-game margin ratings: expected margin = rating gap + home ground; refit each game."""
    r, last_season, out = {}, None, []
    for g in games.itertuples():
        if g.season != last_season:
            r = {t: ELO_CARRY * v for t, v in r.items()}
            last_season = g.season
        rh, ra = r.get(g.home, 0.0), r.get(g.away, 0.0)
        exp = rh - ra + ELO_HGA
        out.append(exp)
        err = g.margin_home - exp
        r[g.home] = rh + ELO_K * err
        r[g.away] = ra - ELO_K * err
    return pd.Series(out, index=games.index)


def add_features(m):
    m = m.copy()
    p = m.groupby('player_id', sort=False)

    def roll(col, n, fn='mean'):
        return p[col].transform(lambda s: getattr(s.shift(1).rolling(n, min_periods=1), fn)())

    # form
    for n in (3, 5, 10, 20):
        m[f'D_l{n}'] = roll('D', n)
    m['D_med10'] = roll('D', 10, 'median')
    m['D_sd10'] = p.D.transform(lambda s: s.shift(1).rolling(10, min_periods=3).std())
    m['D_ewm'] = p.D.transform(lambda s: s.shift(1).ewm(halflife=5, min_periods=1).mean())
    m['D_last'] = p.D.shift(1)
    m['D_trend'] = m.D_l3 - m.D_l20
    sp = m.groupby(['player_id', 'season'], sort=False)
    m['D_season'] = sp.D.transform(lambda s: s.shift(1).expanding().mean())
    m['games_season'] = sp.cumcount()

    # time on ground and disposals per full game on the ground (rate), so a role or minutes change is visible
    for n in (3, 10):
        m[f'TOG_l{n}'] = roll('TOG', n)
    m['TOG_last'] = p.TOG.shift(1)
    m['tog_frac'] = m.TOG / 100.0
    for n in (5, 10, 20):
        num = p.D.transform(lambda s: s.shift(1).rolling(n, min_periods=1).sum())
        den = p.tog_frac.transform(lambda s: s.shift(1).rolling(n, min_periods=1).sum())
        m[f'rate_l{n}'] = num / den.replace(0, np.nan)
    m['was_named_sub_last'] = p.named_sub.shift(1)
    m['was_subbed_off_last'] = p.subbed_off.shift(1)

    # role: per-game averages over the last 10 games
    for c in ['CCL', 'CL', 'CP', 'UP', 'K', 'HB', 'I50', 'R50', 'ITC', 'OP', 'HO', 'G', 'MI5', 'T', 'MG', 'SC', 'CM', 'M']:
        m[f'{c}_pg'] = roll(c, 10)
    m['kick_share'] = m.K_pg / (m.K_pg + m.HB_pg).replace(0, np.nan)
    m['games_prior'] = p.cumcount()
    m['days_rest'] = p.dt.diff().dt.days.clip(upper=60)

    # team context from the named 22: the pool of usual disposals, and who is in or out since last game
    tg = m.groupby(['game', 'team'])
    m['team_pool_D'] = tg.D_l10.transform('sum')
    m['share_of_pool'] = m.D_l10 / m.team_pool_D
    m['team_CCL_pool'] = tg.CCL_pg.transform('sum')
    m['share_CCL_pool'] = m.CCL_pg / m.team_CCL_pool.replace(0, np.nan)
    m['n_mids'] = tg.CCL_pg.transform(lambda s: (s >= 1.5).sum())
    m = m.merge(outs_and_ins(m), on=['game', 'team'], how='left')

    # expected margin from results only (betting lines replace this once the odds pull lands)
    games = (m.drop_duplicates('game')[['game', 'dt', 'season', 'team', 'opp', 'is_home', 'margin']]
             .assign(home=lambda d: np.where(d.is_home == 1, d.team, d.opp),
                     away=lambda d: np.where(d.is_home == 1, d.opp, d.team),
                     margin_home=lambda d: np.where(d.is_home == 1, d.margin, -d.margin))
             .sort_values('dt'))
    games['elo_exp_home'] = elo(games)
    m = m.merge(games[['game', 'home', 'elo_exp_home']], on='game', how='left')
    m['exp_margin'] = np.where(m.team == m.home, m.elo_exp_home, -m.elo_exp_home)
    m['exp_blowout'] = m.exp_margin.abs()
    m = m.drop(columns=['home', 'elo_exp_home'])

    # opponent: disposals it has conceded lately, against the league at the time
    team_games = m.groupby(['game', 'dt', 'team', 'opp'], as_index=False).agg(D_for=('D', 'sum'), UP_for=('UP', 'sum'), T_for=('T', 'sum'))
    conc = team_games.rename(columns={'team': 'opp', 'opp': 'team', 'D_for': 'D_against', 'UP_for': 'UP_against', 'T_for': 'T_against'})
    tgm = team_games.merge(conc[['game', 'team', 'D_against', 'UP_against']], on=['game', 'team']).sort_values('dt')
    tgm['opp_conc_D_l8'] = tgm.groupby('team').D_against.transform(lambda s: s.shift(1).rolling(8, min_periods=3).mean())
    tgm['opp_conc_UP_l8'] = tgm.groupby('team').UP_against.transform(lambda s: s.shift(1).rolling(8, min_periods=3).mean())
    tgm['team_D_l8'] = tgm.groupby('team').D_for.transform(lambda s: s.shift(1).rolling(8, min_periods=3).mean())
    tgm['team_T_l8'] = tgm.groupby('team').T_for.transform(lambda s: s.shift(1).rolling(8, min_periods=3).mean())
    m = m.merge(tgm[['game', 'team', 'team_D_l8']], on=['game', 'team'], how='left')
    m = m.merge(tgm[['game', 'team', 'opp_conc_D_l8', 'opp_conc_UP_l8', 'team_T_l8']].rename(
        columns={'team': 'opp', 'team_T_l8': 'opp_T_l8'}), on=['game', 'opp'], how='left')

    # league and venue environment: totals in games before this one (rule changes like 2026's show up here)
    gt = (team_games.groupby(['game', 'dt'], as_index=False).D_for.sum().rename(columns={'D_for': 'game_D'})
          .merge(m.drop_duplicates('game')[['game', 'venue']], on='game').sort_values('dt'))
    gt['league_game_D'] = gt.game_D.shift(1).rolling(36, min_periods=9).mean()
    gt['venue_game_D'] = gt.groupby('venue').game_D.transform(lambda s: s.shift(1).rolling(20, min_periods=3).mean())
    gt['venue_rel'] = (gt.venue_game_D / gt.league_game_D).fillna(1.0)
    m = m.merge(gt[['game', 'league_game_D', 'venue_rel']], on='game', how='left')
    m['opp_conc_rel'] = m.opp_conc_D_l8 / (m.league_game_D / 2)
    return m


def outs_and_ins(m):
    """For each team in each game: usual disposals of players who played its previous game but not this one."""
    rows = []
    for team, g in m.groupby('team', sort=False):
        order = g.drop_duplicates('game').sort_values('dt').game.tolist()
        lineup = {k: grp for k, grp in g.groupby('game')}
        prev = None
        for gm in order:
            cur = lineup[gm]
            if prev is None:
                rows.append((gm, team, np.nan, np.nan, np.nan))
            else:
                was = lineup[prev]
                out = was[~was.player_id.isin(cur.player_id)]
                # an "out" is valued at his usual figures going into the game he missed
                rows.append((gm, team, out.D_l10.sum() if len(out) else 0.0, out.CCL_pg.sum() if len(out) else 0.0,
                             float((~cur.player_id.isin(was.player_id)).sum())))
            prev = gm
    return pd.DataFrame(rows, columns=['game', 'team', 'outs_D', 'outs_CCL', 'n_ins'])


FEATURES = ['D_l3', 'D_l5', 'D_l10', 'D_l20', 'D_med10', 'D_sd10', 'D_ewm', 'D_last', 'D_trend', 'D_season', 'games_season',
            'TOG_l3', 'TOG_l10', 'TOG_last', 'rate_l5', 'rate_l10', 'rate_l20', 'was_named_sub_last', 'was_subbed_off_last',
            'CCL_pg', 'CL_pg', 'CP_pg', 'UP_pg', 'K_pg', 'HB_pg', 'I50_pg', 'R50_pg', 'ITC_pg', 'OP_pg', 'HO_pg', 'G_pg',
            'MI5_pg', 'T_pg', 'MG_pg', 'SC_pg', 'CM_pg', 'M_pg', 'kick_share', 'games_prior', 'days_rest', 'age',
            'team_pool_D', 'share_of_pool', 'share_CCL_pool', 'n_mids', 'outs_D', 'outs_CCL', 'n_ins',
            'exp_margin', 'exp_blowout', 'is_home', 'team_D_l8', 'opp_conc_D_l8', 'opp_conc_UP_l8', 'opp_T_l8',
            'league_game_D', 'venue_rel', 'opp_conc_rel', 'named_sub', 'finals', 'round_no']


def build(cache):
    at = pd.read_parquet(f'{cache}/afltables.parquet')
    fw = pd.read_parquet(f'{cache}/footywire.parquet')
    m = add_features(base_table(at, fw))
    m['finals'] = m.finals.astype(float)
    return m


if __name__ == '__main__':
    cache = sys.argv[1] if len(sys.argv) > 1 else 'afl/cache'
    m = build(cache)
    m.to_parquet(f'{cache}/frame.parquet', index=False)
    print(f'{len(m):,} player-games, {m.game.nunique():,} games, seasons {m.season.min()}-{m.season.max()}')
    print('matched to Footywire stats:', f'{m.TOG.notna().mean():.1%}')
