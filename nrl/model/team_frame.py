"""One row per team per game, every feature known before kick-off.

Built from the Rugby League Project mirror (nrl/data/mirror.py). Three families of features:

  ratings   points ratings updated game by game AFTER each game is used: an attack and a defence
            rating per team and a league scoring level, so the expected score for each side, the
            margin and the total come from one system. A season's start pulls every rating part-way
            back to average. Every rating a row carries is the value BEFORE that game.
  lineup    who took the field (RLP holds who played, not who was named on Tuesday). For each team:
            how many of its regulars are missing and whether any spine player (fullback, five-eighth,
            halfback, hooker) is, measured two ways:
              *_named  this game's 17 (the "teams named" model; optimistic, since late changes are
                       folded in)
              *_open   the previous game's 17 (what was knowable before Tuesday's lists)
  schedule  home, days since the team's last game, finals, round number

Usage: python -m nrl.model.team_frame nrl/cache   -> nrl/cache/team_frame.parquet
"""
import sys

import numpy as np
import pandas as pd

SPINE = {'FB', 'FE', 'HB', 'HK'}
STARTING = {'FB', 'W', 'C', 'FE', 'HB', 'FR', 'HK', '2R', 'L'}

# rating-system settings, tuned on 2003-2018 only (nrl/docs/TEAM_STEP1.md)
K_RATING = 0.04         # share of each game's surprise added to the ratings
SEASON_CARRY = 0.5      # share of a rating carried into the next season
K_LEAGUE = 0.01         # how fast the league scoring level follows actual totals
HOME_START = 3.0        # home advantage in points, updated slowly
K_HOME = 0.005


def load(cache):
    m = pd.read_parquet(f'{cache}/matches.parquet')
    pm = pd.read_parquet(f'{cache}/player_matches.parquet')
    m = m.dropna(subset=['home_team_score', 'away_team_score']).copy()
    m['kick_off'] = pd.to_datetime(m['date'].dt.strftime('%Y-%m-%d') + ' ' + m['time_24hr'].fillna('15:00:00'))
    m = m.sort_values(['kick_off', 'match_id']).reset_index(drop=True)
    m['is_final'] = ~m['round'].astype(str).str.startswith('Round')
    m['round_no'] = pd.to_numeric(m['round'].astype(str).str.extract(r'Round (\d+)')[0], errors='coerce')
    return m, pm[pm.match_id.isin(m.match_id)].copy()


def ratings(m):
    """Pre-game expected points for each side. Returns columns aligned to m's rows."""
    att, dfn = {}, {}
    league = 40.0
    home_adv = HOME_START
    season = None
    out = np.zeros((len(m), 5))
    for i, g in enumerate(m.itertuples(index=False)):
        if g.season != season:
            season = g.season
            att = {t: v * SEASON_CARRY for t, v in att.items()}
            dfn = {t: v * SEASON_CARRY for t, v in dfn.items()}
        h, a = g.home_team, g.away_team
        ah, aa, dh, da = att.get(h, 0.0), att.get(a, 0.0), dfn.get(h, 0.0), dfn.get(a, 0.0)
        exp_h = league / 2 + ah + da + home_adv / 2
        exp_a = league / 2 + aa + dh - home_adv / 2
        out[i] = (exp_h, exp_a, league, home_adv, (ah - dh) - (aa - da))
        # only now does the game's result touch the ratings
        sh, sa = g.home_team_score, g.away_team_score
        eh, ea = sh - exp_h, sa - exp_a
        att[h], dfn[a] = ah + K_RATING * eh, da + K_RATING * eh
        att[a], dfn[h] = aa + K_RATING * ea, dh + K_RATING * ea
        league += K_LEAGUE * ((sh + sa) - league)
        home_adv += K_HOME * ((sh - sa) - (exp_h - exp_a))
    return pd.DataFrame(out, columns=['exp_home', 'exp_away', 'league_total', 'home_adv', 'rating_diff'])


def lineup_features(m, pm, decay=0.8, regulars=17):
    """Missing regulars per team-game, from this game's 17 and from the previous game's 17.

    A player's selection weight for a team is an exponentially weighted share of that team's recent
    games he played in, computed from games BEFORE the one being described.
    """
    order = dict(zip(m.match_id, range(len(m))))
    pm = pm.assign(i=pm.match_id.map(order)).sort_values('i')
    rows = []
    weights = {}      # team -> {player: weight}
    spine_of = {}     # team -> {player: share of his recent games in a spine jersey}
    last_17 = {}      # team -> set of players in its previous game
    for i, grp in pm.groupby('i', sort=True):
        for team, tg in grp.groupby('team'):
            w = weights.get(team, {})
            top = sorted(w.items(), key=lambda kv: -kv[1])[:regulars]
            reg = {p for p, _ in top}
            spine_regs = {p for p, _ in top if spine_of.get(team, {}).get(p, 0) > 0.5}
            for tag, played in (('named', set(tg.player_id)), ('open', last_17.get(team, set()))):
                missing = [p for p in reg if p not in played]
                rows.append(dict(i=i, team=team, tag=tag,
                                 missing_regulars=len(missing) if reg else np.nan,
                                 missing_weight=sum(w[p] for p in missing) if reg else np.nan,
                                 spine_missing=sum(p not in played for p in spine_regs) if reg else np.nan))
            # update AFTER describing the game
            played = set(tg.player_id)
            for p in set(w) | played:
                w[p] = decay * w.get(p, 0.0) + (1 - decay) * (p in played)
            weights[team] = w
            sp = spine_of.setdefault(team, {})
            for p, pos in zip(tg.player_id, tg.position):
                sp[p] = 0.7 * sp.get(p, 0.0) + 0.3 * (pos in SPINE)
            last_17[team] = played
    lf = pd.DataFrame(rows).pivot_table(index=['i', 'team'], columns='tag',
                                        values=['missing_regulars', 'missing_weight', 'spine_missing'])
    lf.columns = [f'{a}_{b}' for a, b in lf.columns]
    return lf.reset_index()


CACHE = 'nrl/cache'


def build(m, pm):
    r = ratings(m)
    m = pd.concat([m.reset_index(drop=True), r], axis=1)
    m['i'] = np.arange(len(m))
    home = pd.DataFrame(dict(i=m.i, match_id=m.match_id, season=m.season, kick_off=m.kick_off, round_no=m.round_no,
                             is_final=m.is_final, venue_id=m.venue_id, team=m.home_team, opp=m.away_team, home=1,
                             exp_for=m.exp_home, exp_against=m.exp_away, score_for=m.home_team_score,
                             score_against=m.away_team_score, league_total=m.league_total, home_adv=m.home_adv,
                             rating_diff=m.rating_diff))
    away = pd.DataFrame(dict(i=m.i, match_id=m.match_id, season=m.season, kick_off=m.kick_off, round_no=m.round_no,
                             is_final=m.is_final, venue_id=m.venue_id, team=m.away_team, opp=m.home_team, home=0,
                             exp_for=m.exp_away, exp_against=m.exp_home, score_for=m.away_team_score,
                             score_against=m.home_team_score, league_total=m.league_total, home_adv=m.home_adv,
                             rating_diff=-m.rating_diff))
    tg = pd.concat([home, away], ignore_index=True)
    tries = pm.groupby(['match_id', 'team']).tries.sum().rename('tries_for').reset_index()
    tg = tg.merge(tries, on=['match_id', 'team'], how='left')
    tg['exp_margin'] = tg.exp_for - tg.exp_against
    tg['exp_total'] = tg.exp_for + tg.exp_against
    tg['margin'] = tg.score_for - tg.score_against
    tg['total'] = tg.score_for + tg.score_against
    tg = tg.sort_values(['team', 'kick_off'])
    tg['rest_days'] = tg.groupby('team').kick_off.diff().dt.days.clip(upper=21)
    lf = lineup_features(m, pm)
    try:
        ps = pd.read_parquet(f'{CACHE}/player_strength.parquet')
        tg = tg.merge(ps, on=['match_id', 'team'], how='left')
        o = ps.rename(columns={'team': 'opp', 'strength_named': 'opp_strength_named', 'strength_open': 'opp_strength_open'})
        tg = tg.merge(o, on=['match_id', 'opp'], how='left')
        for t in ('named', 'open'):
            tg[f'strength_diff_{t}'] = tg[f'strength_{t}'] - tg[f'opp_strength_{t}']
    except FileNotFoundError:
        print('no player_strength.parquet yet: run nrl.model.player_ratings first')
    tg = tg.merge(lf, on=['i', 'team'], how='left')
    opp = tg[['i', 'team'] + [c for c in tg.columns if c.startswith(('missing_', 'spine_')) or c == 'rest_days']]
    opp = opp.rename(columns={c: 'opp_' + c for c in opp.columns if c not in ('i', 'team')}).rename(columns={'team': 'opp'})
    tg = tg.merge(opp, on=['i', 'opp'], how='left')
    return tg.sort_values(['i', 'home'], ascending=[True, False]).reset_index(drop=True)


FEATURES_OPEN = ['exp_margin', 'exp_total', 'league_total', 'rest_days', 'opp_rest_days',
                 'missing_weight_open', 'opp_missing_weight_open', 'spine_missing_open', 'opp_spine_missing_open',
                 'strength_diff_open', 'is_final']
FEATURES_NAMED = [c.replace('_open', '_named') for c in FEATURES_OPEN]


def main(cache):
    global CACHE
    CACHE = cache
    m, pm = load(cache)
    tg = build(m, pm)
    tg.to_parquet(f'{cache}/team_frame.parquet', index=False)
    print(f'team_frame: {len(tg):,} team-games, seasons {tg.season.min()}-{tg.season.max()}')


if __name__ == '__main__':
    main(sys.argv[1])
