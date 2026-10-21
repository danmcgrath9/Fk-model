"""One row per player per game and one row per team per game, every feature known before the start.

Built from the Cricsheet tables (bbl/data/cricsheet.py) for EVERY T20 match in the file, both
genders, so a player's form includes the IPL, The Hundred, internationals and the rest. BBL and
WBBL rows are flagged and carry the season split; the other leagues are history only.

Known before the start means: each player's own past games, both XIs (named at the toss), the
toss, the teams' past results and the venue's past scoring. Nothing from the game itself. A
player's form is an exponentially weighted figure of his PAST games: every one is computed from
the state after his previous game, and tests/test_frame.py changes a game's balls and result and
checks that the game's own features do not move.

Two versions of the team context, matching the two moments we could bet:
  at the open   (FEATURES_OPEN):  no team news, so the XI is taken to be the team's last XI
  teams named   (FEATURES_NAMED): the XI that played, the toss, and who is in and out since last game
Super overs are left out of every player and team figure (a super over is not part of a player's
innings for the usual prop rules; checked per book later).

Usage: python -m bbl.model.frame bbl/cache/parquet  (writes player_frame.parquet, team_frame.parquet)
"""
import os
import sys

import numpy as np
import pandas as pd

BBL = 'Big Bash League'
WBBL = "Women's Big Bash League"
# a season is chosen and tested in order: fit on the oldest, choose on the next, confirm, then one final look
SPLIT = [('fit', '2021/22'), ('choose', '2023/24'), ('confirm', '2024/25'), ('final', '2025/26')]
BOWLER_WICKETS = {'bowled', 'caught', 'lbw', 'stumped', 'caught and bowled', 'hit wicket'}
NOT_DISMISSALS = {'retired hurt', 'retired not out'}
HALFLIFE = 8           # games: a player's form weights his last 8 games as much as everything before them
VENUE_HALFLIFE = 15    # games at the ground
ELO_K, ELO_CARRY = 24.0, 0.7   # rating points per win, share of the gap kept into a new season

# one name per ground: Cricsheet writes a venue with and without its city, and grounds get renamed
VENUE_ALIAS = {
    'W.A.C.A. Ground': 'WACA', 'Western Australia Cricket Association Ground': 'WACA',
    'Simonds Stadium': 'Kardinia Park', 'GMHBA Stadium': 'Kardinia Park',
    'Aurora Stadium': 'York Park', 'University of Tasmania Stadium': 'York Park',
    'Brisbane Cricket Ground': 'Gabba', 'Optus Stadium': 'Perth Stadium', 'Marvel Stadium': 'Docklands Stadium',
    'Metricon Stadium': 'Carrara Oval', 'Blundstone Arena': 'Bellerive Oval', 'Spotless Stadium': 'Sydney Showground Stadium',
    'GIANTS Stadium': 'Sydney Showground Stadium', 'ENGIE Stadium': 'Sydney Showground Stadium',
    'UTAS Stadium': 'York Park', 'Junction Oval': 'Junction Oval',
}


def canon_venue(v):
    if v is None or pd.isna(v):
        return None
    head = str(v).split(',')[0].strip()
    return VENUE_ALIAS.get(head, head)


def season_split(season):
    for name, last in SPLIT:
        if season <= last:
            return name
    return 'future'


# ---------------------------------------------------------------- per-game facts (the game itself)

def batting(dl):
    """One row per batter per innings: runs, balls faced, 4s, 6s, dismissal, position."""
    d = dl[~dl.super_over].copy()
    d['ball_idx'] = np.arange(len(d))
    faced = d.wides == 0
    d['four'] = (d.runs_batter == 4) & ~d.non_boundary
    d['six'] = (d.runs_batter == 6) & ~d.non_boundary
    b = (d.assign(faced=faced).groupby(['match_id', 'innings', 'batter'], sort=False)
         .agg(bat_runs=('runs_batter', 'sum'), bat_balls=('faced', 'sum'), bat_4s=('four', 'sum'), bat_6s=('six', 'sum'))
         .reset_index().rename(columns={'batter': 'player'}))
    # position: the order each player first appears at either end; on the same ball the striker comes first
    ends = pd.concat([d[['match_id', 'innings', 'batter']].rename(columns={'batter': 'player'}).assign(order=d.ball_idx * 2),
                      d[['match_id', 'innings', 'non_striker']].rename(columns={'non_striker': 'player'}).assign(order=d.ball_idx * 2 + 1)])
    first = ends.groupby(['match_id', 'innings', 'player']).order.min().reset_index()
    first = first.sort_values(['match_id', 'innings', 'order'])
    first['bat_pos'] = first.groupby(['match_id', 'innings']).cumcount() + 1
    outs = pd.concat([d.loc[d.player_out.notna(), ['match_id', 'innings', 'player_out', 'wicket_kind']],
                      d.loc[d.player_out_2.notna(), ['match_id', 'innings', 'player_out_2', 'wicket_kind_2']]
                      .rename(columns={'player_out_2': 'player_out', 'wicket_kind_2': 'wicket_kind'})])
    outs = outs[~outs.wicket_kind.isin(NOT_DISMISSALS)].drop_duplicates(['match_id', 'innings', 'player_out'])
    outs = outs.rename(columns={'player_out': 'player', 'wicket_kind': 'how_out'})
    b = first[['match_id', 'innings', 'player', 'bat_pos']].merge(b, on=['match_id', 'innings', 'player'], how='left')
    b[['bat_runs', 'bat_balls', 'bat_4s', 'bat_6s']] = b[['bat_runs', 'bat_balls', 'bat_4s', 'bat_6s']].fillna(0)
    b = b.merge(outs, on=['match_id', 'innings', 'player'], how='left')
    b['bat_out'] = b.how_out.notna().astype(int)
    return b


def bowling(dl):
    """One row per bowler per match: legal balls, runs conceded, wickets, dots."""
    d = dl[~dl.super_over]
    w1 = d.wicket_kind.isin(BOWLER_WICKETS).astype(int)
    w2 = d.wicket_kind_2.isin(BOWLER_WICKETS).astype(int)
    return (d.assign(conceded=d.runs_batter + d.wides + d.noballs, wk=w1 + w2,
                     dot=(d.legal & (d.runs_total == 0)).astype(int), lg=d.legal.astype(int))
            .groupby(['match_id', 'bowler'], sort=False)
            .agg(bowl_balls=('lg', 'sum'), bowl_runs=('conceded', 'sum'), bowl_wkts=('wk', 'sum'), bowl_dots=('dot', 'sum'))
            .reset_index().rename(columns={'bowler': 'player'}))


def catches(dl):
    d = dl[~dl.super_over]
    c = d.loc[d.wicket_kind == 'caught', ['match_id', 'fielders']].dropna()
    c = c.assign(player=c.fielders.str.split(';')).explode('player')
    cb = d.loc[d.wicket_kind == 'caught and bowled', ['match_id', 'bowler']].rename(columns={'bowler': 'player'})
    return pd.concat([c[['match_id', 'player']], cb]).groupby(['match_id', 'player']).size().rename('catches').reset_index()


def match_table(m):
    m = m.copy()
    m['venue_c'] = m.venue.map(canon_venue)
    m['comp'] = np.select([m.competition == BBL, m.competition == WBBL], ['BBL', 'WBBL'], 'other')
    m['split'] = np.where(m.comp != 'other', m.season.astype(str).map(season_split), None)
    m['dt'] = pd.to_datetime(m.start_date)
    return m.sort_values(['dt', 'match_id']).reset_index(drop=True)


def player_games(m, pl, dl):
    """The XI of every match with what each player did in it (NaN batting when he did not bat)."""
    bat = batting(dl)
    inn_team = dl[~dl.super_over].drop_duplicates(['match_id', 'innings'])[['match_id', 'innings', 'team']]
    bat = bat.merge(inn_team, on=['match_id', 'innings'])
    bat = bat.drop(columns='innings').drop_duplicates(['match_id', 'team', 'player'])
    if 'future' not in m:
        m = m.assign(future=False)
    g = pl.merge(m[['match_id', 'dt', 'season', 'comp', 'competition', 'split', 'gender', 'team1', 'team2', 'venue_c',
                    'toss_winner', 'toss_decision', 'bat_first', 'future']], on='match_id')
    g['opp'] = np.where(g.team == g.team1, g.team2, g.team1)
    g = g.merge(bat, on=['match_id', 'team', 'player'], how='left')
    g = g.merge(bowling(dl), on=['match_id', 'player'], how='left').merge(catches(dl), on=['match_id', 'player'], how='left')
    g['did_bat'] = g.bat_pos.notna().astype(int)
    for c in ['bowl_balls', 'bowl_runs', 'bowl_wkts', 'bowl_dots', 'catches']:
        g[c] = g[c].fillna(0)
    g['did_bowl'] = (g.bowl_balls > 0).astype(int)
    fut = g.future.fillna(False).astype(bool)
    g.loc[fut, ['did_bat', 'did_bowl', 'bowl_balls', 'bowl_runs', 'bowl_wkts', 'bowl_dots', 'catches']] = np.nan
    g['pid'] = g.player_id.fillna('name:' + g.player)
    g['team_key'] = g.team + '|' + g.gender
    g['opp_key'] = g.opp + '|' + g.gender
    return g.drop(columns=['team1', 'team2']).sort_values(['dt', 'match_id', 'team', 'list_order']).reset_index(drop=True)


# ---------------------------------------------------------------- pre-game features

PLAYER_STATE = ['runs_pg', 'balls_pg', 'sixes_pg', 'fours_pg', 'bat_rate', 'pos_ewm', 'sr', 'out_per_ball',
                'bowl_balls_pg', 'bowl_rate', 'econ', 'wkts_per_ball', 'catches_pg']


def player_state(g):
    """Each player's form AFTER each of his games (ewm over his games, half-life HALFLIFE games).

    A row's own pre-game features are the previous row's state, so nothing here may be used for
    the game it was computed on. Per-ball rates are ratios of weighted sums, so a 2-ball cameo
    weighs 2 balls and not one innings.
    """
    g = g.sort_values(['dt', 'match_id']).copy()
    p = g.groupby('pid', sort=False)

    batted = g.did_bat == 1
    # league-adjusted figures when bbl.model.leagues has put them on a common scale (build_from(..., factors=...))
    adj = 'adj_bat_runs' in g
    runs_col = g.adj_bat_runs if adj else g.bat_runs
    six_col = g.adj_bat_6s if adj else g.bat_6s
    four_col = g.adj_bat_4s if adj else g.bat_4s
    out_col = g.adj_bat_out if adj else g.bat_out
    bat_runs = runs_col.where(batted)
    bat_balls = g.bat_balls.where(batted)
    s = pd.DataFrame(index=g.index)
    s['pid'], s['dt'], s['match_id'] = g.pid, g.dt, g.match_id
    tmp = g.assign(_runs0=runs_col.fillna(0), _balls0=g.bat_balls.fillna(0), _6=six_col.fillna(0), _4=four_col.fillna(0),
                   _rb=bat_runs, _bb=bat_balls, _ob=out_col.where(batted), _pos=g.bat_pos,
                   _br=g.adj_bowl_runs if adj else g.bowl_runs, _bw=g.adj_bowl_wkts if adj else g.bowl_wkts)
    # a game not yet played is not an observation: blank every outcome so the weighted averages skip it
    future = g.future.fillna(False).astype(bool) if 'future' in g else pd.Series(False, index=g.index)
    obs = ['_runs0', '_balls0', '_6', '_4', '_rb', '_bb', '_ob', '_pos', 'did_bat', 'did_bowl', 'bowl_balls', '_br',
           '_bw', 'catches']
    tmp[obs] = tmp[obs].astype(float).where(~future)
    p = tmp.groupby('pid', sort=False)

    def ewm(col):
        return p[col].transform(lambda x: x.ewm(halflife=HALFLIFE, ignore_na=True).mean())

    s['runs_pg'] = ewm('_runs0')
    s['balls_pg'] = ewm('_balls0')
    s['sixes_pg'] = ewm('_6')
    s['fours_pg'] = ewm('_4')
    s['bat_rate'] = ewm('did_bat')
    s['pos_ewm'] = ewm('_pos')
    s['sr'] = ewm('_rb') / ewm('_bb').replace(0, np.nan)
    s['out_per_ball'] = ewm('_ob') / ewm('_bb').replace(0, np.nan)
    s['bowl_balls_pg'] = ewm('bowl_balls')
    s['bowl_rate'] = ewm('did_bowl')
    s['econ'] = ewm('_br') / ewm('bowl_balls').replace(0, np.nan)
    s['wkts_per_ball'] = ewm('_bw') / ewm('bowl_balls').replace(0, np.nan)
    s['catches_pg'] = ewm('catches')
    s['games'] = p.cumcount() + 1
    return s


def add_player_features(g, state):
    g = g.sort_values(['dt', 'match_id']).copy()
    prev = state.groupby('pid', sort=False)[PLAYER_STATE + ['games', 'dt']].shift(1)
    for c in PLAYER_STATE:
        g[f'pre_{c}'] = prev[c]
    g['pre_games'] = prev.games.fillna(0)
    # expected batting position: his usual position ranked within this XI, from past games only. NOT Cricsheet's
    # list order, which is the order the XI actually batted in this game (98% of the time) and so leaks the game.
    # ties (no history, or the same usual position) break on the player id, never on row order: rows are
    # sorted by list order, so a row-order tie-break would let the batting order back in
    order = g.assign(_p=g.pre_pos_ewm.fillna(99.0)).sort_values(['match_id', 'team', '_p', 'pid'])
    g['exp_pos'] = (order.groupby(['match_id', 'team']).cumcount() + 1).reindex(g.index)
    g['days_rest'] = (g.dt - prev.dt).dt.days.clip(upper=365)
    # the same competition only (BBL form for a BBL game): games at this level, and his ewm runs in it
    future = g.future.fillna(False).astype(bool) if 'future' in g else pd.Series(False, index=g.index)
    cp = g.assign(_r=g.bat_runs.fillna(0).where(~future), _n=(~future).astype(int)).groupby(['pid', 'comp'], sort=False)
    g['pre_comp_games'] = cp._n.transform(lambda s: s.shift(1).cumsum()).fillna(0)
    g['pre_comp_runs_pg'] = cp._r.transform(lambda s: s.shift(1).ewm(halflife=HALFLIFE, ignore_na=True).mean())
    return g


def asof_state(state, keys):
    """For each (pid, dt) in keys, the player's latest state from a game strictly before dt."""
    st = state.sort_values('dt')
    k = keys.reset_index().sort_values('dt')
    out = pd.merge_asof(k, st[['pid', 'dt'] + PLAYER_STATE + ['games']], on='dt', by='pid', allow_exact_matches=False)
    return out.set_index('index').sort_index()


def lineup_strength(xi):
    """Team aggregates from a set of players' pre-game state: expected batter runs, sixes and bowling quality."""
    x = xi.copy()
    x['runs_pg'] = x.runs_pg.fillna(0)
    x['sixes_pg'] = x.sixes_pg.fillna(0)
    bb = x.bowl_balls_pg.fillna(0)
    agg = x.assign(_bb=bb, _econ_w=bb * x.econ.fillna(0), _wk_w=bb * x.wkts_per_ball.fillna(0),
                   _new=x.games.isna().astype(int))
    a = agg.groupby(['match_id', 'team_key']).agg(xi_runs=('runs_pg', 'sum'), xi_sixes=('sixes_pg', 'sum'),
                                                  _bb=('_bb', 'sum'), _ew=('_econ_w', 'sum'), _ww=('_wk_w', 'sum'),
                                                  xi_debutants=('_new', 'sum'), xi_n=('pid', 'size'))
    a['xi_econ'] = a._ew / a._bb.replace(0, np.nan)
    a['xi_wkts'] = a._ww / a._bb.replace(0, np.nan) * 120
    return a.drop(columns=['_bb', '_ew', '_ww'])


def team_games(m, inn):
    """One row per team per match: runs and wickets for and against, result, and full-length flag."""
    reg = inn[~inn.super_over]
    t = []
    for side, other in (('team1', 'team2'), ('team2', 'team1')):
        mm = m if 'future' in m else m.assign(future=False)
        x = mm[['match_id', 'dt', 'season', 'comp', 'split', 'gender', 'venue_c', 'toss_winner', 'toss_decision', 'bat_first',
                'winner', 'result', 'method', 'future', side, other]].rename(columns={side: 'team', other: 'opp'})
        t.append(x)
    t = pd.concat(t, ignore_index=True)
    f = reg[['match_id', 'team', 'innings', 'runs', 'wickets', 'legal_balls']]
    t = t.merge(f.rename(columns={'innings': 'bat_inn'}), on=['match_id', 'team'], how='left')
    t = t.merge(f.rename(columns={'team': 'opp', 'innings': 'opp_inn', 'runs': 'opp_runs', 'wickets': 'opp_wickets',
                                  'legal_balls': 'opp_legal_balls'}), on=['match_id', 'opp'], how='left')
    t['team_key'] = t.team + '|' + t.gender
    t['opp_key'] = t.opp + '|' + t.gender
    t['batted_first'] = (t.team == t.bat_first).astype(int)
    t['won_toss'] = (t.team == t.toss_winner).astype(int)
    t['won'] = np.select([t.result == 'win', t.result == 'tie'], [(t.winner == t.team).astype(float), 0.5], np.nan)
    first_runs = np.where(t.batted_first == 1, t.runs, t.opp_runs)
    first_balls = np.where(t.batted_first == 1, t.legal_balls, t.opp_legal_balls)
    first_wkts = np.where(t.batted_first == 1, t.wickets, t.opp_wickets)
    t['first_inns_runs'] = first_runs
    # a first innings is complete when it ran its 120 balls or lost 10 wickets, and no rain rule was used
    t['full_first_inns'] = ((first_balls >= 120) | (first_wkts >= 10)) & t.method.isna() & (t.result != 'no result')
    t['match_runs'] = t.runs + t.opp_runs
    t['margin_runs'] = t.runs - t.opp_runs   # crude: a chase stops when it wins; the team model handles that
    return t.sort_values(['dt', 'match_id', 'team']).reset_index(drop=True)


def elo(t):
    """Pre-game win ratings per team_key (logistic, 400-point scale), regressed at each new season."""
    rating, seen_season, pre = {}, {}, {}
    games = t.drop_duplicates('match_id').sort_values(['dt', 'match_id'])
    for g in games.itertuples():
        a, b = g.team_key, g.opp_key
        for k in (a, b):
            if k in seen_season and seen_season[k] != g.season:
                rating[k] = 1500 + ELO_CARRY * (rating[k] - 1500)
            seen_season[k] = g.season
        ra, rb = rating.get(a, 1500.0), rating.get(b, 1500.0)
        pre[(g.match_id, a)], pre[(g.match_id, b)] = ra, rb
        if not np.isnan(g.won):
            ea = 1 / (1 + 10 ** ((rb - ra) / 400))
            rating[a] = ra + ELO_K * (g.won - ea)
            rating[b] = rb - ELO_K * (g.won - ea)
    return pd.Series([pre[(r.match_id, r.team_key)] for r in t.itertuples()], index=t.index)


def venue_features(t):
    """Per ground and gender, from games before this one: first-innings runs and how often batting first won."""
    # one row per match, so a game not yet played (no toss, no innings) still gets its ground's history
    g = t.sort_values(['dt', 'match_id']).drop_duplicates('match_id').copy()
    bf = t[t.batted_first == 1].set_index('match_id')
    g['bf_won'] = g.match_id.map(bf.won)
    g['vkey'] = g.venue_c + '|' + g.gender
    full = g.first_inns_runs.where(g.full_first_inns.fillna(False).astype(bool))
    g['venue_first_runs'] = full.groupby(g.vkey).transform(lambda s: s.shift(1).ewm(halflife=VENUE_HALFLIFE, ignore_na=True).mean())
    # batting first's win rate, shrunk to a half with 10 games of prior weight (a game with no result counts a half)
    w = g.bf_won.where(g.bf_won.notna() | g.first_inns_runs.isna(), 0.5).fillna(0.5)
    played = g.first_inns_runs.notna().astype(float)
    wins = (w * played).groupby(g.vkey).transform(lambda s: s.shift(1).cumsum()).fillna(0)
    n = played.groupby(g.vkey).transform(lambda s: s.shift(1).cumsum()).fillna(0)
    g['venue_bat_first_win'] = (wins + 5) / (n + 10)
    g['venue_games'] = n          # games played here before this one (an unplayed fixture is not one)
    return g[['match_id', 'venue_first_runs', 'venue_games', 'venue_bat_first_win']]


def build(d, league_adjust=False):
    m = match_table(pd.read_parquet(os.path.join(d, 't20_matches.parquet')))
    pl = pd.read_parquet(os.path.join(d, 't20_players.parquet'))
    dl = pd.read_parquet(os.path.join(d, 't20_deliveries.parquet'))
    inn = pd.read_parquet(os.path.join(d, 't20_innings.parquet'))
    factors = None
    if league_adjust:
        from bbl.model.leagues import league_factors
        factors = league_factors(m, dl, LEAGUE_CUTOFF)
    return build_from(m, pl, dl, inn, factors)


# League adjustment (bbl/model/leagues.py): factors estimated on matches before this date only, so the
# choose seasons (from 2022/23) never inform their own factors. None = off.
LEAGUE_CUTOFF = '2022-07-01'


def build_from(m, pl, dl, inn, factors=None):
    m = match_table(m) if 'venue_c' not in m else m
    g = player_games(m, pl, dl)
    if factors is not None:
        from bbl.model.leagues import apply_factors
        g = apply_factors(g, factors)
    state = player_state(g)
    g = add_player_features(g, state)
    t = team_games(m, inn)
    t['elo_pre'] = elo(t)
    opp = t[['match_id', 'team_key', 'elo_pre']].rename(columns={'team_key': 'opp_key', 'elo_pre': 'opp_elo_pre'})
    t = t.merge(opp, on=['match_id', 'opp_key'], how='left')
    t = t.merge(venue_features(t), on='match_id', how='left')

    # teams named: the XI that played, at their pre-game state
    named = asof_state(state, g[['match_id', 'team_key', 'pid', 'dt']])
    sn = lineup_strength(named).add_suffix('_named')
    # at the open: the team's previous XI, at their state as of this game's date
    games_by_team = t[['match_id', 'team_key', 'dt']].sort_values(['dt', 'match_id'])
    games_by_team['prev_match'] = games_by_team.groupby('team_key').match_id.shift(1)
    xi = g[['match_id', 'team_key', 'pid']]
    prev_xi = games_by_team.dropna(subset=['prev_match']).merge(
        xi.rename(columns={'match_id': 'prev_match'}), on=['prev_match', 'team_key'])
    opened = asof_state(state, prev_xi[['match_id', 'team_key', 'pid', 'dt']])
    so = lineup_strength(opened).add_suffix('_open')
    # who is in and out against the last XI
    cur = set(zip(xi.match_id, xi.team_key, xi.pid))
    prv = set(zip(prev_xi.match_id, prev_xi.team_key, prev_xi.pid))
    named_ix = named.set_index(['match_id', 'team_key', 'pid'])
    opened_ix = opened.set_index(['match_id', 'team_key', 'pid'])
    outs = opened_ix.loc[[k for k in opened_ix.index if k not in cur]]
    ins = named_ix.loc[[k for k in named_ix.index if k not in prv]]
    has_prev = set(zip(prev_xi.match_id, prev_xi.team_key))
    ins = ins[[k[:2] in has_prev for k in ins.index]]
    news = pd.DataFrame({
        'n_outs': outs.groupby(level=[0, 1]).size(), 'outs_runs': outs.runs_pg.fillna(0).groupby(level=[0, 1]).sum(),
        'outs_bowl_balls': outs.bowl_balls_pg.fillna(0).groupby(level=[0, 1]).sum(),
        'n_ins': ins.groupby(level=[0, 1]).size(), 'ins_runs': ins.runs_pg.fillna(0).groupby(level=[0, 1]).sum()})
    news.index.names = ['match_id', 'team_key']
    t = t.merge(sn, left_on=['match_id', 'team_key'], right_index=True, how='left')
    t = t.merge(so, left_on=['match_id', 'team_key'], right_index=True, how='left')
    t = t.merge(news, left_on=['match_id', 'team_key'], right_index=True, how='left')
    has = t.set_index(['match_id', 'team_key']).index.isin(list(has_prev))
    for c in ['n_outs', 'outs_runs', 'outs_bowl_balls', 'n_ins', 'ins_runs']:
        t[c] = np.where(has, t[c].fillna(0), np.nan)
    # the opponent's lineup, both versions
    oc = [c for c in t.columns if c.endswith('_named') or c.endswith('_open')]
    o = t[['match_id', 'team_key'] + oc].rename(columns={'team_key': 'opp_key', **{c: 'opp_' + c for c in oc}})
    t = t.merge(o, on=['match_id', 'opp_key'], how='left')
    # how often this team has played at this ground before (a home-ground signal that needs no fixture list)
    t = t.sort_values(['dt', 'match_id']).reset_index(drop=True)
    tv = t.groupby('team_key', sort=False)
    t['_played'] = (~t.future.fillna(False).astype(bool)).astype(int)
    t['team_prior_games'] = tv._played.transform(lambda s: s.shift(1).cumsum()).fillna(0)
    t['team_prior_at_venue'] = t.groupby(['team_key', 'venue_c'], sort=False)._played.transform(lambda s: s.shift(1).cumsum()).fillna(0)
    t = t.drop(columns='_played')
    t['venue_share'] = t.team_prior_at_venue / t.team_prior_games.replace(0, np.nan)
    t['days_rest'] = tv.dt.diff().dt.days.clip(upper=365)

    # player rows get their team's and opponent's context, both versions
    ctx = ['elo_pre', 'opp_elo_pre', 'venue_first_runs', 'venue_games', 'venue_bat_first_win', 'venue_share'] + oc + ['opp_' + c for c in oc]
    g = g.merge(t[['match_id', 'team_key'] + ctx], on=['match_id', 'team_key'], how='left')
    return g, t


TEAM_OPEN = ['elo_pre', 'opp_elo_pre', 'venue_first_runs', 'venue_games', 'venue_bat_first_win', 'venue_share', 'days_rest',
             'xi_runs_open', 'xi_sixes_open', 'xi_econ_open', 'xi_wkts_open', 'xi_debutants_open',
             'opp_xi_runs_open', 'opp_xi_sixes_open', 'opp_xi_econ_open', 'opp_xi_wkts_open']
TEAM_NAMED = TEAM_OPEN + ['won_toss', 'batted_first', 'xi_runs_named', 'xi_sixes_named', 'xi_econ_named', 'xi_wkts_named',
                          'xi_debutants_named', 'opp_xi_runs_named', 'opp_xi_sixes_named', 'opp_xi_econ_named',
                          'opp_xi_wkts_named', 'n_outs', 'outs_runs', 'outs_bowl_balls', 'n_ins', 'ins_runs']
PLAYER = ['pre_' + c for c in PLAYER_STATE] + ['pre_games', 'days_rest', 'pre_comp_games', 'pre_comp_runs_pg', 'exp_pos']
# Cricsheet's list order is the actual batting order of the game: never a feature (tests/test_frame.py checks)
NEVER_FEATURES = ['list_order']
# the game's own facts: never features
OUTCOMES = ['bat_runs', 'bat_balls', 'bat_4s', 'bat_6s', 'bat_out', 'how_out', 'bat_pos', 'did_bat', 'bowl_balls', 'bowl_runs',
            'bowl_wkts', 'bowl_dots', 'catches', 'did_bowl']


def main(d):
    g, t = build(d, league_adjust=os.environ.get('LEAGUE_ADJUST') == '1')
    g.to_parquet(os.path.join(d, 'player_frame.parquet'), index=False)
    t.to_parquet(os.path.join(d, 'team_frame.parquet'), index=False)
    for name, x in (('player_frame', g), ('team_frame', t)):
        print(f'{name}: {len(x):,} rows, {x.shape[1]} columns; BBL {int((x.comp == "BBL").sum()):,}, WBBL {int((x.comp == "WBBL").sum()):,}')


if __name__ == '__main__':
    main(sys.argv[1])
