"""NBL data layer: one row per player per game and one row per team per game, every feature known
before the tip.

Known before the tip means: each player's own past games, who dressed for this game (the game-day
squad of 12 is announced before the tip; from 2018-19 the box score lists players who dressed and did
not play at 0:00), the teams' past games, the venue, the date and the schedule. Nothing from the game
itself. Every rolling figure is built from earlier games only, and nbl/tests/test_frame.py changes a
game's stats and checks that game's features do not move.

Two versions of "who is playing":
  named  the players who dressed for the game (before 2018-19 only those who played are listed,
         so the named squad is slightly optimistic in 2015-16 to 2017-18)
  open   the players who dressed for the team's previous game: what was knowable when books open,
         with no team news

Built from nblR's copy (nbl/data/mirror.py): results.parquet, box_player.parquet, box_team.parquet.

Usage: python -m nbl.model.frame nbl/cache   (writes nbl/cache/players.parquet and teams.parquet)
"""
import math
import re
import sys
import unicodedata

import numpy as np
import pandas as pd

FIRST_SEASON = 2015          # box scores start in 2015-16
STATS = ['pts', 'reb', 'ast', 'fg3m', 'fg3a', 'fga', 'fgm', 'fta', 'ftm', 'oreb', 'tov', 'stl', 'blk', 'pf']
PROPS = ['pts', 'reb', 'ast', 'fg3m', 'pra']
RATE_COLS = ['pts', 'reb', 'ast', 'fg3m', 'fg3a', 'fga', 'fta', 'oreb', 'tov', 'stl', 'blk', 'eff']
DECAY = 0.92                 # weight kept per later game played, in a player's rate and minutes history
PRIOR_MIN = 60.0             # minutes of league-average play mixed into every rate (shrinkage)
TEAM_DECAY = 0.90            # weight kept per later game, in team pace and defence
ELO_K, ELO_HCA, ELO_CARRY, ELO_CAP = 0.04, 3.0, 0.6, 30.0   # per point of error, home court, share kept over summer, error cap
# (chosen on 2016-17 to 2022-23 by margin miss; nbl/docs/TEAM_STEP1.md)

# cities, for travel (the NBL criss-crosses Australia and New Zealand)
CITY = {'Adelaide 36ers': (-34.93, 138.60), 'Brisbane Bullets': (-27.47, 153.03), 'Cairns Taipans': (-16.92, 145.77),
        'Illawarra Hawks': (-34.42, 150.89), 'Melbourne United': (-37.81, 144.96), 'New Zealand Breakers': (-36.85, 174.76),
        'Perth Wildcats': (-31.95, 115.86), 'South East Melbourne Phoenix': (-37.81, 144.96), 'Sydney Kings': (-33.87, 151.21),
        'Tasmania JackJumpers': (-42.88, 147.33), 'Townsville Crocodiles': (-19.26, 146.82)}


def _ascii(s):
    return unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().lower()


def name_key(first, family):
    s = _ascii(f'{first or ""} {family or ""}')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z ]', '', s.replace('-', ' '))).strip()


def season_year(s):
    return int(str(s)[:4])


def km(a, b):
    (la1, lo1), (la2, lo2) = a, b
    p = math.pi / 180
    h = math.sin((la2 - la1) * p / 2) ** 2 + math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))


def base_games(results):
    """Completed games from 2015-16: one row per game, both source shapes (numbers before 2025-26, text ids after)."""
    r = results.copy()
    r['season'] = r.season.map(season_year)
    r = r[(r.season >= FIRST_SEASON) & (r.match_status == 'COMPLETE')].copy()
    r['tip'] = pd.to_datetime(r.match_time_utc, utc=True, format='mixed')
    r['home_score'] = pd.to_numeric(r.home_score_string, errors='coerce')
    r['away_score'] = pd.to_numeric(r.away_score_string, errors='coerce')
    rn = r.round_number.astype(str)
    # finals: FINALS before 2025-26; from 2025-26 the type is blank and the round names the series
    r['finals'] = ((r.match_type == 'FINALS') | ~rn.str.fullmatch(r'\d+')).astype(float)
    r['round_no'] = pd.to_numeric(rn, errors='coerce')
    r['ot'] = pd.to_numeric(r.extra_periods_used, errors='coerce').fillna(0)
    g = r.rename(columns={'match_id': 'game', 'home_team_name': 'home', 'away_team_name': 'away', 'venue_name': 'venue'})
    g = g[['game', 'season', 'tip', 'round_number', 'round_no', 'finals', 'venue', 'home', 'away', 'home_score', 'away_score', 'ot']]
    g = g[g.home_score.notna() & g.away_score.notna()]
    # Australian date of the game (for rest days and back-to-backs)
    g['day'] = (g.tip + pd.Timedelta(hours=10)).dt.normalize().dt.tz_localize(None)
    return g.sort_values(['tip', 'game']).reset_index(drop=True)


def _minutes(s):
    """'27:09' (minutes:seconds) or, in some early rows, whole minutes ('0', '40')."""
    s = s.astype('string').str.strip()
    x = s.str.extract(r'^(\d+):(\d+)$')
    mmss = pd.to_numeric(x[0]) + pd.to_numeric(x[1]) / 60
    whole = pd.to_numeric(s.where(s.str.fullmatch(r'\d+', na=False)), errors='coerce')
    return mmss.fillna(whole).astype(float)


def base_players(box, games):
    """One row per player per game: who dressed, minutes and the counting stats, team from home/away."""
    b = box.drop(columns=['season']).copy()
    b = b.merge(games[['game', 'home', 'away']], left_on='match_id', right_on='game', how='inner')
    b['team'] = np.where(b.home_away == 1, b.home, b.away)
    b['opp'] = np.where(b.home_away == 1, b.away, b.home)
    b['is_home'] = (b.home_away == 1).astype(float)
    b['key'] = [name_key(f, l) for f, l in zip(b.first_name, b.family_name)]
    b['player'] = (b.first_name.fillna('') + ' ' + b.family_name.fillna('')).str.strip()
    b['min'] = _minutes(b.minutes)
    num = {'pts': 'points', 'reb': 'rebounds_total', 'ast': 'assists', 'fg3m': 'three_pointers_made',
           'fg3a': 'three_pointers_attempted', 'fga': 'field_goals_attempted', 'fta': 'free_throws_attempted',
           'fgm': 'field_goals_made', 'ftm': 'free_throws_made',
           'oreb': 'rebounds_offensive', 'tov': 'turnovers', 'stl': 'steals', 'blk': 'blocks', 'pf': 'fouls_personal'}
    for k, c in num.items():
        b[k] = pd.to_numeric(b[c], errors='coerce')
    b['starter'] = pd.to_numeric(b.starter, errors='coerce').fillna(0)
    b['pos'] = b.playing_position.astype('string').str.upper().str[:1].fillna('?')
    b = b[b['min'].notna() & (b.key != '')]
    b['played'] = (b['min'] > 0).astype(float)
    # a player who played has every counting stat; a missing one in a played row is a source gap
    b.loc[b.played == 1, STATS] = b.loc[b.played == 1, STATS].fillna(0)
    b['pra'] = b.pts + b.reb + b.ast
    # the NBL's own efficiency rating: what a player put up less his misses and turnovers
    b['eff'] = b.pts + b.reb + b.ast + b.stl + b.blk - (b.fga - b.fgm) - (b.fta - b.ftm) - b.tov
    b = b.drop_duplicates(['game', 'team', 'key'])
    b = b.merge(games[['game', 'season', 'tip', 'day', 'finals', 'round_no', 'venue']], on='game')
    keep = ['game', 'season', 'tip', 'day', 'finals', 'round_no', 'venue', 'team', 'opp', 'is_home', 'key', 'player', 'pos',
            'starter', 'min', 'played'] + STATS + ['pra', 'eff']
    return b[keep].sort_values(['tip', 'game', 'team', 'key']).reset_index(drop=True)


def team_box(players, games):
    """One row per team per game: points, possessions, and what it allowed."""
    t = players[players.played == 1].groupby(['game', 'team'], as_index=False)[STATS + ['min']].sum()
    t['poss'] = t.fga - t.oreb + t.tov + 0.44 * t.fta
    side = []
    for home in (True, False):
        s = games[['game', 'season', 'tip', 'day', 'finals', 'venue', 'ot', 'home', 'away', 'home_score', 'away_score']].copy()
        s['team'] = s.home if home else s.away
        s['opp'] = s.away if home else s.home
        s['is_home'] = float(home)
        s['score'] = s.home_score if home else s.away_score
        s['opp_score'] = s.away_score if home else s.home_score
        side.append(s)
    tg = pd.concat(side, ignore_index=True).drop(columns=['home', 'away', 'home_score', 'away_score'])
    tg = tg.merge(t, on=['game', 'team'], how='left')
    opp = t.rename(columns={c: f'{c}_allowed' for c in STATS + ['poss', 'min']}).rename(columns={'team': 'opp'})
    tg = tg.merge(opp, on=['game', 'opp'], how='left')
    tg['margin'] = tg.score - tg.opp_score
    return tg.sort_values(['tip', 'game', 'team']).reset_index(drop=True)


def elo(games):
    """Pre-game expected home margin from results only; ratings regress toward zero each summer."""
    r, last, out = {}, None, []
    for g in games.itertuples():
        if g.season != last:
            r = {t: ELO_CARRY * v for t, v in r.items()}
            last = g.season
        rh, ra = r.get(g.home, 0.0), r.get(g.away, 0.0)
        exp = rh - ra + ELO_HCA
        out.append(exp)
        err = float(np.clip((g.home_score - g.away_score) - exp, -ELO_CAP, ELO_CAP))
        r[g.home] = rh + ELO_K * err
        r[g.away] = ra - ELO_K * err
    return pd.Series(out, index=games.index)


def team_features(tg, games):
    """Pre-game team context: pace, scoring and defence (decayed, shifted), rest and travel."""
    tg = tg.copy().sort_values(['tip', 'game'])
    per = 100.0 / tg.poss.replace(0, np.nan)
    tg['ortg'] = tg.score * per
    tg['drtg'] = tg.opp_score * per
    for c in ['pts', 'reb', 'ast', 'fg3m', 'oreb']:
        tg[f'{c}_allowed_pp'] = tg[f'{c}_allowed'] / tg.poss_allowed.replace(0, np.nan)
    tg['reb_chances'] = tg.fga - tg.oreb + tg.fga_allowed - tg.oreb_allowed     # missed-shot proxies on both ends
    cols = ['poss', 'ortg', 'drtg', 'margin', 'pts_allowed_pp', 'reb_allowed_pp', 'ast_allowed_pp', 'fg3m_allowed_pp', 'score', 'opp_score']
    out = {f'{c}_ew': [] for c in cols}
    state, idx = {}, []
    for row in tg.itertuples():
        s = state.setdefault(row.team, {'w': 0.0, **{c: 0.0 for c in cols}})
        for c in cols:
            out[f'{c}_ew'].append(s[c] / s['w'] if s['w'] > 0 else np.nan)
        idx.append(row.Index)
        # carry most of last season into the next (rosters turn over, but not completely)
        vals = {c: getattr(row, c) for c in cols}
        if all(pd.notna(v) for v in vals.values()):
            for c in cols:
                s[c] = TEAM_DECAY * s[c] + vals[c]
            s['w'] = TEAM_DECAY * s['w'] + 1.0
    for k, v in out.items():
        tg.loc[idx, k] = v
    g = tg.groupby('team', sort=False)
    tg['games_prior'] = g.cumcount()
    tg['days_rest'] = g.day.diff().dt.days.clip(upper=14)
    tg['b2b'] = (tg.days_rest <= 1).astype(float)
    # travel: distance from where the team last played (home city, or the opponent's when away)
    tg['city'] = [CITY[t] if h == 1 else CITY.get(o) for t, o, h in zip(tg.team, tg.opp, tg.is_home)]
    prev = tg.groupby('team', sort=False).city.shift(1)
    tg['travel_km'] = [km(a, b) if isinstance(a, tuple) and isinstance(b, tuple) else 0.0 for a, b in zip(prev, tg.city)]
    tg = tg.drop(columns=['city'])
    # league environment from earlier games only: points per possession and possessions per game
    pp = {f'g_{c}': (f'{c}_allowed_pp', 'mean') for c in ['pts', 'reb', 'ast', 'fg3m']}
    lg = tg.groupby(['game', 'tip'], as_index=False).agg(game_poss=('poss', 'mean'), game_pts=('score', 'sum'), **pp).sort_values('tip')
    lg['league_poss'] = lg.game_poss.shift(1).rolling(60, min_periods=15).mean()
    lg['league_pts'] = lg.game_pts.shift(1).rolling(60, min_periods=15).mean()
    for c in ['pts', 'reb', 'ast', 'fg3m']:
        lg[f'league_{c}_pp'] = lg[f'g_{c}'].shift(1).rolling(60, min_periods=15).mean()
    tg = tg.merge(lg[['game', 'league_poss', 'league_pts'] + [f'league_{c}_pp' for c in ['pts', 'reb', 'ast', 'fg3m']]],
                  on='game', how='left')
    ge = games.copy()
    ge['elo_home'] = elo(ge)
    tg = tg.merge(ge[['game', 'home', 'elo_home']], on='game', how='left')
    tg['elo_margin'] = np.where(tg.team == tg.home, tg.elo_home, -tg.elo_home)
    tg = tg.drop(columns=['home', 'elo_home'])
    return tg.sort_values(['tip', 'game', 'team']).reset_index(drop=True)


def player_history(p, league_rate):
    """Each player's decayed minutes and per-minute rates from earlier games only, shrunk to the league.

    One pass in time order per player. Rates count played games; minutes count played games; the DNP
    rate counts games he dressed for (2018-19 on). A season break keeps the history (decay continues).
    """
    p = p.sort_values(['tip', 'game']).copy()
    n = len(p)
    rate_cols = RATE_COLS
    out = {f'r_{c}': np.full(n, np.nan) for c in rate_cols}
    for c in ['min_ew', 'min_last', 'min_l3', 'start_ew', 'start_last', 'dnp_l5', 'games_prior', 'games_season', 'days_since',
              'min_ew_season', 'pra_l10', 'pts_l10', 'reb_l10', 'ast_l10', 'fg3m_l10', 'pts_l5', 'reb_l5', 'ast_l5',
              'fg3m_l5', 'pra_l5', 'min_sd', 'prev_team_same']:
        out[c] = np.full(n, np.nan)
    rows = p[['key', 'season', 'day', 'team', 'min', 'played', 'starter'] + rate_cols + ['pra']].to_numpy(object)
    pos = {c: i for i, c in enumerate(['key', 'season', 'day', 'team', 'min', 'played', 'starter'] + rate_cols + ['pra'])}
    order = np.argsort(p.key.to_numpy(), kind='stable')
    keys = p.key.to_numpy()[order]
    starts = np.r_[0, np.flatnonzero(keys[1:] != keys[:-1]) + 1, len(keys)]
    for a, b in zip(starts[:-1], starts[1:]):
        idxs = order[a:b]          # this player's rows, in time order (stable sort kept tip order)
        sw = smin = sstart = 0.0
        sst = {c: 0.0 for c in rate_cols}
        hist_min, hist_dress, recent = [], [], {c: [] for c in ['pts', 'reb', 'ast', 'fg3m', 'pra']}
        last_day = last_season = last_team = None
        season_games = 0
        sw_s = smin_s = 0.0
        for i in idxs:
            r = rows[i]
            season = r[pos['season']]
            if season != last_season:
                season_games, sw_s, smin_s = 0, 0.0, 0.0
            lr = league_rate.get(season, league_rate[min(league_rate)])
            for c in rate_cols:
                out[f'r_{c}'][i] = (sst[c] + PRIOR_MIN * lr[c]) / (smin + PRIOR_MIN)
            out['min_ew'][i] = smin / sw if sw > 0 else np.nan
            out['min_ew_season'][i] = smin_s / sw_s if sw_s > 0 else np.nan
            out['start_ew'][i] = sstart / sw if sw > 0 else np.nan
            out['min_last'][i] = hist_min[-1] if hist_min else np.nan
            out['min_l3'][i] = np.mean(hist_min[-3:]) if hist_min else np.nan
            out['min_sd'][i] = np.std(hist_min[-10:]) if len(hist_min) >= 3 else np.nan
            out['start_last'][i] = hist_dress[-1][1] if hist_dress else np.nan
            out['dnp_l5'][i] = np.mean([1 - d[0] for d in hist_dress[-5:]]) if hist_dress else np.nan
            out['games_prior'][i] = len(hist_min)
            out['games_season'][i] = season_games
            out['days_since'][i] = (r[pos['day']] - last_day).days if last_day is not None else np.nan
            out['prev_team_same'][i] = float(last_team == r[pos['team']]) if last_team is not None else np.nan
            for c in recent:
                h = recent[c]
                out[f'{c}_l10'][i] = np.mean(h[-10:]) if h else np.nan
                out[f'{c}_l5'][i] = np.mean(h[-5:]) if h else np.nan
            # now fold this game in, for the games after it
            played = r[pos['played']] == 1
            hist_dress.append((float(played), float(r[pos['starter']])))
            if played:
                m = float(r[pos['min']])
                sw = DECAY * sw + 1.0
                smin = DECAY * smin + m
                sstart = DECAY * sstart + float(r[pos['starter']])
                for c in rate_cols:
                    sst[c] = DECAY * sst[c] + float(r[pos[c]])
                sw_s = DECAY * sw_s + 1.0
                smin_s = DECAY * smin_s + m
                hist_min.append(m)
                for c in recent:
                    recent[c].append(float(r[pos[c]]))
                season_games += 1
            last_day, last_season, last_team = r[pos['day']], season, r[pos['team']]
    for k, v in out.items():
        p[k] = v
    return p


def league_rates(players):
    """Per-minute league rates by season, from the season BEFORE (the first season uses its own; it is
    only ever a warm-up season and never scored)."""
    pl = players[players.played == 1]
    by = pl.groupby('season')[RATE_COLS + ['min']].sum()
    rates = by.div(by['min'], axis=0).drop(columns='min')
    out = {}
    for s in sorted(rates.index):
        src = s - 1 if s - 1 in rates.index else s
        out[s] = rates.loc[src].to_dict()
    return out


def squad_context(p):
    """Per team-game: minutes freed by players who dressed last game and not this one (named), and
    the expected-minutes pool of each version of the squad."""
    rows = []
    p = p.sort_values(['tip', 'game'])
    for team, g in p.groupby('team', sort=False):
        order = g.drop_duplicates('game').game.tolist()
        by = {k: v for k, v in g.groupby('game', sort=False)}
        prev = None
        for gm in order:
            cur = by[gm]
            pool = cur.min_ew.fillna(0).sum()
            if prev is None:
                rows.append((gm, team, pool, np.nan, np.nan, np.nan))
            else:
                was = by[prev]
                out = was[~was.key.isin(cur.key)]
                ins = cur[~cur.key.isin(was.key)]
                rows.append((gm, team, pool, out.min_ew.fillna(0).sum(), ins.min_ew.fillna(0).sum(), float(len(out))))
            prev = gm
    return pd.DataFrame(rows, columns=['game', 'team', 'squad_min_pool', 'min_out', 'min_in', 'n_out'])


def lineup_values(p, lr):
    """Per team-game, the squad's value above league average: each player's efficiency per minute above
    the league's, times the minutes he would get if the team's 200 were shared by usual minutes.
      named  the players who dressed for this game
      open   the players who dressed for the team's previous game (no team news), at their latest values
    """
    p = p.sort_values(['tip', 'game']).copy()
    p['val'] = p.r_eff - p.season.map(lambda s: lr[s]['eff'])
    rows = []
    for team, g in p.groupby('team', sort=False):
        by = {k: v for k, v in g.groupby('game', sort=False)}
        order = g.drop_duplicates('game').game.tolist()
        latest = {}          # key -> (val, min_ew) as of his latest game
        prev = None
        for gm in order:
            cur = by[gm]
            for r in cur.itertuples():
                latest[r.key] = (r.val, r.min_ew)

            def strength(pairs):
                pairs = [(v, m) for v, m in pairs if pd.notna(v) and pd.notna(m) and m > 0]
                pool = sum(m for _, m in pairs)
                return sum(v * 200.0 * m / pool for v, m in pairs) if pool > 0 else np.nan

            named = strength(zip(cur.val, cur.min_ew))
            open_ = strength(latest[k] for k in by[prev].key) if prev is not None else np.nan
            rows.append((gm, team, named, open_))
            prev = gm
    return pd.DataFrame(rows, columns=['game', 'team', 'named_val', 'open_val'])


def add_player_features(players, tg):
    lr = league_rates(players)
    p = player_history(players, lr)
    p = p.merge(squad_context(p), on=['game', 'team'], how='left')
    # the player's share of his squad's usual minutes, scaled to the 200 a team plays
    p['min_share'] = p.min_ew / p.squad_min_pool.replace(0, np.nan)
    p['min_scaled'] = 200.0 * p.min_share
    tcols = ['game', 'team', 'poss_ew', 'ortg_ew', 'drtg_ew', 'margin_ew', 'days_rest', 'b2b', 'travel_km', 'elo_margin',
             'league_poss', 'league_pts']
    p = p.merge(tg[tcols], on=['game', 'team'], how='left')
    opp = tg[['game', 'team', 'poss_ew', 'drtg_ew', 'ortg_ew', 'pts_allowed_pp_ew', 'reb_allowed_pp_ew', 'ast_allowed_pp_ew',
              'fg3m_allowed_pp_ew']].rename(columns={'team': 'opp', 'poss_ew': 'opp_poss_ew', 'drtg_ew': 'opp_drtg_ew',
                                                     'ortg_ew': 'opp_ortg_ew'})
    p = p.merge(opp, on=['game', 'opp'], how='left')
    p['exp_poss'] = (p.poss_ew + p.opp_poss_ew) / 2
    p['pace_rel'] = p.exp_poss / p.league_poss
    lgc = tg[['game', 'team'] + [f'league_{c}_pp' for c in ['pts', 'reb', 'ast', 'fg3m']]]
    p = p.merge(lgc, on=['game', 'team'], how='left')
    for c in ['pts', 'reb', 'ast', 'fg3m']:
        # what the opponent has allowed per possession lately, against the league in earlier games
        p[f'opp_{c}_rel'] = p[f'{c}_allowed_pp_ew'] / p[f'league_{c}_pp']
    p['exp_blowout'] = p.elo_margin.abs()
    return p.sort_values(['tip', 'game', 'team', 'key']).reset_index(drop=True)


PLAYER_FEATURES = ['r_pts', 'r_reb', 'r_ast', 'r_fg3m', 'r_fg3a', 'r_fga', 'r_fta', 'r_oreb', 'r_tov',
                   'min_ew', 'min_ew_season', 'min_last', 'min_l3', 'min_sd', 'start_ew', 'start_last', 'dnp_l5',
                   'games_prior', 'games_season', 'days_since', 'prev_team_same',
                   'pts_l10', 'reb_l10', 'ast_l10', 'fg3m_l10', 'pra_l10', 'pts_l5', 'reb_l5', 'ast_l5', 'fg3m_l5', 'pra_l5',
                   'squad_min_pool', 'min_out', 'min_in', 'n_out', 'min_share', 'min_scaled',
                   'poss_ew', 'opp_poss_ew', 'exp_poss', 'pace_rel', 'ortg_ew', 'drtg_ew', 'opp_drtg_ew', 'opp_ortg_ew',
                   'opp_pts_rel', 'opp_reb_rel', 'opp_ast_rel', 'opp_fg3m_rel', 'elo_margin', 'exp_blowout', 'is_home',
                   'days_rest', 'b2b', 'travel_km', 'finals']


def build(cache):
    results = pd.read_parquet(f'{cache}/results.parquet')
    box = pd.read_parquet(f'{cache}/box_player.parquet')
    games = base_games(results)
    players = base_players(box, games)
    tg = team_features(team_box(players, games), games)
    p = add_player_features(players, tg)
    tg = tg.merge(lineup_values(p, league_rates(players)), on=['game', 'team'], how='left')
    return games, p, tg


if __name__ == '__main__':
    cache = sys.argv[1] if len(sys.argv) > 1 else 'nbl/cache'
    games, p, tg = build(cache)
    p.to_parquet(f'{cache}/players.parquet', index=False)
    tg.to_parquet(f'{cache}/teams.parquet', index=False)
    print(f'{len(p):,} player-games ({int(p.played.sum()):,} played), {p.game.nunique():,} games, seasons {p.season.min()}-{p.season.max()}')
    print(f'{len(tg):,} team-games; possessions missing for {tg.poss.isna().mean():.1%}')
