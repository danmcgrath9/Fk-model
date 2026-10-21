"""Team model: margin and total per game, from pre-game information, scored against Squiggle's models.

Two predictions per game, because the market moves between them:
  open   what was knowable when books open the round (Sunday/Monday): last week's 22, less anyone
         subbed off injured in it. No team news.
  named  the 22 that actually took the field (teams are named Thursday; late changes before the bounce).
The gap between the two is the value of team and injury news; once real opening and closing lines
exist (afl/README.md), the test is whether "named" beats the opening line by more than the market
moved.

Lineup strength = the sum of each selected player's recent rating (AFL Player Ratings from Fryzigg,
rolling, shifted one game; SuperCoach where ratings are missing). Plus results-only ratings (Elo),
rolling team stat differentials, rest, travel, ground.

Split by season: fit 2013-2022, choose on 2023, score 2024 and 2025 once (Fryzigg ratings end at 2025;
2026 is scored as well with SuperCoach standing in, and said so).

Usage: python -m afl.model.team afl/cache afl/docs/TEAM_STEP1.md
"""
import glob
import sys
import warnings

import numpy as np
import pandas as pd
from scipy import stats

from afl.model.frame import _key

warnings.filterwarnings('ignore')
FIT, TUNE, TESTS = (2013, 2022), 2023, (2024, 2025, 2026)

# home state of each club, and the state of each ground, for travel
CLUB_STATE = {'Adelaide': 'SA', 'Port Adelaide': 'SA', 'Brisbane': 'QLD', 'Gold Coast': 'QLD', 'Sydney': 'NSW', 'GWS': 'NSW',
              'West Coast': 'WA', 'Fremantle': 'WA', 'Geelong': 'VIC', 'Carlton': 'VIC', 'Collingwood': 'VIC', 'Essendon': 'VIC',
              'Hawthorn': 'VIC', 'Melbourne': 'VIC', 'North Melbourne': 'VIC', 'Richmond': 'VIC', 'St Kilda': 'VIC',
              'Western Bulldogs': 'VIC'}
VENUE_STATE = {'M.C.G.': 'VIC', 'Docklands': 'VIC', 'Kardinia Park': 'VIC', 'Eureka Stadium': 'VIC', 'Adelaide Oval': 'SA',
               'Football Park': 'SA', 'Norwood Oval': 'SA', 'Barossa Park': 'SA', 'Gabba': 'QLD', 'Carrara': 'QLD',
               'Riverway Stadium': 'QLD', "Cazaly's Stadium": 'QLD', 'S.C.G.': 'NSW', 'Stadium Australia': 'NSW',
               'Sydney Showground': 'NSW', 'Blacktown': 'NSW', 'Manuka Oval': 'ACT', 'Subiaco': 'WA', 'Perth Stadium': 'WA',
               'Hands Oval': 'WA', 'York Park': 'TAS', 'Bellerive Oval': 'TAS', 'Marrara Oval': 'NT', 'Traeger Park': 'NT',
               'Wellington': 'NZ', 'Jiangwan Stadium': 'CN', 'Summit Sports Park': 'SA'}
FRYZIGG_TEAM = {'Brisbane Lions': 'Brisbane', 'Greater Western Sydney': 'GWS', 'Footscray': 'Western Bulldogs'}
SQUIGGLE_TEAM = {'Brisbane Lions': 'Brisbane', 'Greater Western Sydney': 'GWS'}


def player_ratings(cache, m):
    """Attach Fryzigg's AFL Player Ratings (rating points) to the frame's player-games."""
    fz = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f'{cache}/fryzigg_*.parquet'))], ignore_index=True)
    fz['date'] = pd.to_datetime(fz.match_date).dt.strftime('%Y-%m-%d')
    fz['team'] = fz.player_team.replace(FRYZIGG_TEAM)
    fz['key'] = (fz.player_first_name.fillna('') + ' ' + fz.player_last_name.fillna('')).map(_key)
    fz = fz.drop_duplicates(['date', 'team', 'key'])
    m = m.copy()
    m['key'] = m.Player.map(_key)
    m = m.merge(fz[['date', 'team', 'key', 'rating_points', 'match_weather_type', 'match_weather_temp_c']],
                on=['date', 'team', 'key'], how='left')
    p = m.sort_values('dt').groupby('player_id')
    m['rp_pg'] = p.rating_points.transform(lambda s: s.shift(1).rolling(10, min_periods=1).mean())
    return m


def lineup_strength(m):
    """Per game and team: strength of the 22 that played (named) and of the 22 expected at the open."""
    m = m.copy()
    # one scale for both measures: SuperCoach per game where no rating history exists
    m['val_sc'] = m.SC_pg
    m['val_rp'] = m.rp_pg
    rows = []
    by_game = {k: v for k, v in m.groupby('game')}
    for team, g in m.sort_values('dt').groupby('team', sort=False):
        games = g.drop_duplicates('game').sort_values('dt').game.tolist()
        by = {k: v for k, v in g.groupby('game')}
        prev = None
        for gm in games:
            cur = by[gm]
            named_sc = cur.val_sc.nlargest(22).sum()
            named_rp = cur.val_rp.nlargest(22).sum(min_count=1)
            if prev is None:
                open_sc, open_rp, n_out = np.nan, np.nan, np.nan
            else:
                was = by[prev]
                # expected at the open: last week's side less anyone subbed off injured; values as of this game
                keep_ids = was[was.subbed_off != 1].player_id
                vals = by_game[gm][by_game[gm].player_id.isin(keep_ids)]
                # players from last week who did not play this week still count at the open: use their last value
                missing = was[(was.subbed_off != 1) & ~was.player_id.isin(cur.player_id)]
                open_sc = pd.concat([vals.val_sc, missing.val_sc]).nlargest(22).sum()
                open_rp = pd.concat([vals.val_rp, missing.val_rp]).nlargest(22).sum(min_count=1)
                n_out = float(len(missing))
            rows.append((gm, team, named_sc, named_rp, open_sc, open_rp, n_out))
            prev = gm
    return pd.DataFrame(rows, columns=['game', 'team', 'named_sc', 'named_rp', 'open_sc', 'open_rp', 'n_changes'])


def team_games(m):
    g = (m.groupby(['game', 'dt', 'season', 'Round', 'round_no', 'finals', 'venue', 'team', 'opp', 'is_home'], as_index=False, dropna=False)
          .agg(score_for=('score_for', 'first'), score_against=('score_against', 'first'), I50=('I50', 'sum'), CP=('CP', 'sum'),
               CL=('CL', 'sum'), MG=('MG', 'sum'), T=('T', 'sum'), D=('D', 'sum'),
               weather=('match_weather_type', 'first'), temp=('match_weather_temp_c', 'first')))
    opp = g[['game', 'team', 'I50', 'CP', 'CL', 'MG', 'T', 'D']].rename(columns={'team': 'opp'})
    g = g.merge(opp, on=['game', 'opp'], suffixes=('', '_opp'))
    for c in ['I50', 'CP', 'CL', 'MG', 'T', 'D']:
        g[f'{c}_diff'] = g[c] - g[f'{c}_opp']
    g['margin'] = g.score_for - g.score_against
    g = g.sort_values('dt')
    t = g.groupby('team')
    for c in ['margin', 'score_for', 'score_against', 'I50_diff', 'CP_diff', 'CL_diff', 'MG_diff', 'T_diff']:
        g[f'{c}_f6'] = t[c].transform(lambda s: s.shift(1).rolling(6, min_periods=2).mean())
    g['rest'] = t.dt.diff().dt.days.clip(upper=21)
    g['interstate'] = (g.team.map(CLUB_STATE) != g.venue.map(VENUE_STATE)).astype(float)
    return g


def build_games(cache):
    m = pd.read_parquet(f'{cache}/frame.parquet')
    m = player_ratings(cache, m)
    ls = lineup_strength(m)
    tg = team_games(m).merge(ls, on=['game', 'team'], how='left')
    elo = m.drop_duplicates(['game', 'team'])[['game', 'team', 'exp_margin']]
    tg = tg.merge(elo, on=['game', 'team'], how='left')
    home = tg[tg.is_home == 1].copy()
    away = tg[tg.is_home == 0].copy()
    feats = ['score_for_f6', 'score_against_f6', 'margin_f6', 'I50_diff_f6', 'CP_diff_f6', 'CL_diff_f6', 'MG_diff_f6', 'T_diff_f6',
             'rest', 'interstate', 'named_sc', 'named_rp', 'open_sc', 'open_rp', 'n_changes']
    gm = home.merge(away[['game'] + feats + ['team']], on='game', suffixes=('_h', '_a'))
    gm = gm.rename(columns={'team_h': 'home', 'team_a': 'away', 'margin': 'home_margin'})
    gm['total'] = gm.score_for + gm.score_against
    gm['elo_margin'] = gm.exp_margin
    for c in ['score_for_f6', 'margin_f6', 'I50_diff_f6', 'CP_diff_f6', 'CL_diff_f6', 'MG_diff_f6', 'T_diff_f6', 'rest', 'interstate',
              'named_sc', 'open_sc', 'named_rp', 'open_rp']:
        gm[f'd_{c}'] = gm[f'{c}_h'] - gm[f'{c}_a']
    gm['sum_attack'] = gm.score_for_f6_h + gm.score_for_f6_a
    gm['sum_defence'] = gm.score_against_f6_h + gm.score_against_f6_a
    gm['wet'] = gm.weather.astype('string').str.contains('RAIN|WET|SHOWER|STORM', case=False, na=False).astype(float)
    gm['date'] = gm.dt.dt.strftime('%Y-%m-%d')
    return gm.sort_values('dt').reset_index(drop=True)


def ridge(X, y, lam):
    Xc = np.column_stack([np.ones(len(X)), X])
    I = np.eye(Xc.shape[1]); I[0, 0] = 0
    return np.linalg.solve(Xc.T @ Xc + lam * I, Xc.T @ y)


def predict_ridge(b, X):
    return np.column_stack([np.ones(len(X)), X]) @ b


def fill(df, cols, ref):
    return df[cols].fillna(ref[cols].mean())


MARGIN_OPEN = ['elo_margin', 'd_margin_f6', 'd_I50_diff_f6', 'd_CP_diff_f6', 'd_CL_diff_f6', 'd_MG_diff_f6', 'd_rest', 'd_interstate', 'd_open_sc']
MARGIN_NAMED = ['elo_margin', 'd_margin_f6', 'd_I50_diff_f6', 'd_CP_diff_f6', 'd_CL_diff_f6', 'd_MG_diff_f6', 'd_rest', 'd_interstate', 'd_named_sc']
TOTAL = ['sum_attack', 'sum_defence', 'wet', 'finals']


def squiggle(cache):
    tips = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f'{cache}/squiggle_tips_*.parquet'))], ignore_index=True)
    tips['date'] = pd.to_datetime(tips.date).dt.strftime('%Y-%m-%d')
    for c in ('hteam', 'ateam'):
        tips[c] = tips[c].replace(SQUIGGLE_TEAM)
    return tips


def bits(p_home, home_margin):
    """Squiggle's bits: 1 + log2(p) for the side that won, 1 + 0.5*log2(p(1-p)) for a draw."""
    p = np.clip(p_home, 1e-6, 1 - 1e-6)
    return np.where(home_margin > 0, 1 + np.log2(p), np.where(home_margin < 0, 1 + np.log2(1 - p), 1 + 0.5 * np.log2(p * (1 - p))))


def run(cache, out_md):
    gm = build_games(cache)
    gm.to_parquet(f'{cache}/team_games.parquet', index=False)
    fit = gm[gm.season.between(*FIT) & gm.elo_margin.notna()]
    tune = gm[gm.season == TUNE]
    res = {}
    # choose lambda and the strength measure on the tuning season
    choices = {}
    for name, cols in (('open', MARGIN_OPEN), ('named', MARGIN_NAMED)):
        best = None
        for lam in (1, 10, 100, 1000):
            b = ridge(fill(fit, cols, fit).to_numpy(), fit.home_margin.to_numpy(), lam)
            mae = np.abs(predict_ridge(b, fill(tune, cols, fit).to_numpy()) - tune.home_margin).mean()
            if best is None or mae < best[0]:
                best = (mae, lam, b)
        choices[name] = best
    sd = np.std(fit.home_margin - predict_ridge(choices['named'][2], fill(fit, MARGIN_NAMED, fit).to_numpy()))
    bt = ridge(fill(fit, TOTAL, fit).to_numpy(), fit.total.to_numpy(), 10)

    tips = squiggle(cache)
    rows = []
    for season in TESTS:
        te = gm[gm.season == season].copy()
        te['m_open'] = predict_ridge(choices['open'][2], fill(te, MARGIN_OPEN, fit).to_numpy())
        te['m_named'] = predict_ridge(choices['named'][2], fill(te, MARGIN_NAMED, fit).to_numpy())
        te['m_elo'] = te.elo_margin
        te['t_hat'] = predict_ridge(bt, fill(te, TOTAL, fit).to_numpy())
        for k in ('m_open', 'm_named', 'm_elo'):
            te[k.replace('m_', 'p_')] = stats.norm.cdf(te[k] / sd)
        res[season] = te
        for k, lab in (('open', 'ours, at the open (no team news)'), ('named', 'ours, teams named'), ('elo', 'results-only rating')):
            rows.append(dict(season=season, model=lab, games=len(te), tips=((te[f'm_{k}'] > 0) == (te.home_margin > 0)).mean(),
                             mae=(te[f'm_{k}'] - te.home_margin).abs().mean(), bits=bits(te[f'p_{k}'], te.home_margin).mean()))
        # Squiggle's models on the same games (matched on date and teams)
        sq = tips[tips.year == season].merge(te[['date', 'home', 'away', 'home_margin']], left_on=['date', 'hteam', 'ateam'],
                                              right_on=['date', 'home', 'away'])
        for src, s in sq.groupby('source'):
            if len(s) < 0.9 * len(te):
                continue
            hm = pd.to_numeric(s.hmargin, errors='coerce')
            pc = pd.to_numeric(s.hconfidence, errors='coerce') / 100
            rows.append(dict(season=season, model=src, games=len(s), tips=((hm > 0) == (s.home_margin > 0)).mean(),
                             mae=(hm - s.home_margin).abs().mean(), bits=bits(pc, s.home_margin).mean()))
    r = pd.DataFrame(rows)
    rep = ['# AFL team model, step 1: margin and total, against Squiggle\'s models', '',
           f'Fitted {FIT[0]}-{FIT[1]}, choices made on {TUNE}, then {", ".join(map(str, TESTS))} scored once. '
           '"Punters" is Squiggle\'s reading of the betting market. 2026 has no Fryzigg player ratings yet, so its lineup '
           'strength is SuperCoach-based throughout (as it is for every season in this first cut).', '',
           f'Win chance = normal around the predicted margin, spread {sd:.1f} points (fitted on the training seasons).', '']
    for season in TESTS:
        t = r[r.season == season].sort_values('bits', ascending=False)
        rep += [f'## {season}', '', '| rank | model | games | tips correct | margin miss (pts) | bits per game |', '|---|---|---|---|---|---|']
        for i, x in enumerate(t.itertuples(), 1):
            star = '**' if x.model.startswith('ours') or x.model in ('Punters', 'Wheelo Ratings') else ''
            rep.append(f'| {i} | {star}{x.model}{star} | {x.games} | {x.tips:.1%} | {x.mae:.1f} | {x.bits:.3f} |')
        rep.append('')
    allte = pd.concat(res.values())
    rep += ['## Team news: how much the named 22 moves the prediction', '',
            '| change in our margin, open to named | games | open margin miss | named margin miss |', '|---|---|---|---|']
    allte['move'] = (allte.m_named - allte.m_open).abs()
    for lo, hi in ((0, 1), (1, 3), (3, 6), (6, 100)):
        g = allte[(allte.move >= lo) & (allte.move < hi)]
        rep.append(f'| {lo} to {hi} pts | {len(g)} | {(g.m_open - g.home_margin).abs().mean():.1f} | {(g.m_named - g.home_margin).abs().mean():.1f} |')
    rep += ['', '## Totals', '', '| season | total miss (pts), ours | always the training average |', '|---|---|---|']
    for season, te in res.items():
        rep.append(f'| {season} | {(te.t_hat - te.total).abs().mean():.1f} | {(fit.total.mean() - te.total).abs().mean():.1f} |')
    open(out_md, 'w').write('\n'.join(rep) + '\n')
    print('\n'.join(rep))
    allte.to_parquet(f'{cache}/team_test_predictions.parquet', index=False)


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else 'afl/cache', sys.argv[2] if len(sys.argv) > 2 else 'afl/docs/TEAM_STEP1.md')
