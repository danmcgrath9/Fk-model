"""Our prices for games not yet played: win chance, totals, and every player's runs, sixes and wickets.

Inputs
  fixtures CSV: date (local, YYYY-MM-DD), team1, team2, venue, gender (male/female), comp (BBL/WBBL),
                optional bat_first (once the toss is known)
  XI CSV (optional): date, team, player, as a team sheet or bookmaker writes the name. A side without
                a named XI is priced on its last XI in the same competition: the 'at the open' price.
Every model is refitted on all club T20 history of the same gender before the first fixture, with the
choices fixed in bbl/model/team.py and bbl/model/props.py; nothing is tuned here.

Output (in the parquet dir): prices_games.parquet, prices_players.parquet, PRICES.md.
Fair odds only (1 / our chance). Nothing is sent anywhere: comparing with a book is bbl/live/compare.py.

Usage: python -m bbl.live.price bbl/cache/parquet fixtures.csv [--xi xi.csv] [--squads squads.csv]
"""
import os
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from bbl.live import names
from bbl.model import frame, props, team

RUN_LINES = [9.5, 14.5, 19.5, 24.5, 29.5, 34.5]
COUNT_LINES = [0.5, 1.5]
COMP_NAME = {'BBL': frame.BBL, 'WBBL': frame.WBBL}


def season_of(date):
    d = pd.Timestamp(date)
    return f'{d.year}/{(d.year + 1) % 100:02d}' if d.month >= 7 else f'{d.year - 1}/{d.year % 100:02d}'


def load(d):
    return (pd.read_parquet(os.path.join(d, f'{n}.parquet')) for n in ('t20_matches', 't20_players', 't20_deliveries', 't20_innings'))


def recent_pool(m, pl, team_name, gender, before, days=730):
    mm = m[(m.gender == gender) & (pd.to_datetime(m.start_date) < before) & (pd.to_datetime(m.start_date) >= before - pd.Timedelta(days=days))]
    x = pl[pl.match_id.isin(mm.match_id) & (pl.team == team_name)]
    return x.drop_duplicates('player')[['player', 'player_id']]


def last_xi(m, pl, team_name, gender, comp, before):
    mm = m[(m.gender == gender) & (m.competition == COMP_NAME[comp]) & (pd.to_datetime(m.start_date) < before)
           & ((m.team1 == team_name) | (m.team2 == team_name))]
    if mm.empty:
        return None
    last = mm.sort_values('start_date').iloc[-1].match_id
    return pl[(pl.match_id == last) & (pl.team == team_name)][['player', 'player_id']]


def squad_xi(m, pl, side, gender, comp, when, squads, last):
    """An at-the-open XI from the season's squad: last XI players still in the squad, then squad members with
    the most T20 games in the past year. Squad names (Wikipedia) are matched to Cricsheet's within everyone of
    that gender who played T20 in the past two years; an ambiguous or unknown name is left out and noted."""
    season = season_of(when.strftime('%Y-%m-%d'))
    sq = squads[(squads.season == season) & (squads.comp == comp) & (squads.club == side)] if squads is not None else None
    if sq is None or sq.empty:
        return last, f'last XI (no {season} squad for {side})'
    mm = m[(m.gender == gender) & (pd.to_datetime(m.start_date) < when) & (pd.to_datetime(m.start_date) >= when - pd.Timedelta(days=730))]
    pool = pl[pl.match_id.isin(mm.match_id)]
    recent = pool[pool.match_id.isin(mm[pd.to_datetime(mm.start_date) >= when - pd.Timedelta(days=365)].match_id)]
    games = recent.groupby('player').size()
    names_pool = pool.drop_duplicates('player')[['player', 'player_id']]
    club_pool = pool[pool.team == side].drop_duplicates('player').player
    matched, unknown = [], []
    for nm in sq.player:
        # the club's own recent players first (resolves most common surnames), then everyone of that gender
        who, how = names.match(nm, club_pool, team=side)
        if who is None:
            who, how = names.match(nm, names_pool.player, team=side)
        (matched if who else unknown).append(who or f'{nm} ({how})')
    keep = last[last.player.isin(matched)] if last is not None else pd.DataFrame(columns=['player', 'player_id'])
    extra = [p for p in sorted(set(matched) - set(keep.player), key=lambda p: -games.get(p, 0))]
    add = names_pool[names_pool.player.isin(extra[:max(0, 11 - len(keep))])]
    add = add.set_index('player').loc[[p for p in extra[:max(0, 11 - len(keep))]]].reset_index()
    xi = pd.concat([keep, add[['player', 'player_id']]], ignore_index=True).head(11)
    note = (f'squad XI: {len(keep)} kept from last XI, {len(add)} added from the {season} squad'
            + (f'; not matched: {", ".join(unknown)}' if unknown else ''))
    return xi, note


def future_rows(m, pl, fixtures, xis, squads=None):
    fm, fp, notes = [], [], []
    for k, f in enumerate(fixtures.itertuples()):
        mid = f'F{k:03d}_{f.date}'
        when = pd.Timestamp(f.date)
        fm.append(dict(match_id=mid, competition=COMP_NAME[f.comp], season=season_of(f.date), start_date=f.date, gender=f.gender,
                       match_type='T20', team_type='club', team1=f.team1, team2=f.team2, venue=f.venue, toss_winner=None,
                       toss_decision=None, bat_first=getattr(f, 'bat_first', None) if pd.notna(getattr(f, 'bat_first', None)) else None,
                       winner=None, result=None, method=None, future=True))
        for side in (f.team1, f.team2):
            named = xis[(xis.date == f.date) & (xis.team == side)] if xis is not None else pd.DataFrame()
            if len(named):
                pool = recent_pool(m, pl, side, f.gender, when)
                rows = []
                for nm in named.player:
                    who, how = names.match(nm, pool.player, team=side)
                    if who is None:
                        notes.append(f'{f.date} {side}: "{nm}" not matched ({how}); priced without him')
                        continue
                    rows.append(pool[pool.player == who].iloc[0])
                xi, src = pd.DataFrame(rows), 'named'
            else:
                xi, src = squad_xi(m, pl, side, f.gender, f.comp, when, squads, last_xi(m, pl, side, f.gender, f.comp, when))
                if xi is None or len(xi) == 0:
                    notes.append(f'{f.date} {side}: no previous {f.comp} XI and none named; cannot price')
                    continue
            notes.append(f'{f.date} {side}: {src}, {len(xi)} players')
            fp.append(xi.assign(match_id=mid, team=side, list_order=range(1, len(xi) + 1)))
    return pd.DataFrame(fm), (pd.concat(fp, ignore_index=True) if fp else pd.DataFrame()), notes


def win_chances(x, fut_ids):
    # before the toss: who chases is unknown, so never the 'after_toss' inputs here
    feats = team.win_features('named')
    rows = []
    for gender, g in x[x.match_id.isin(fut_ids)].groupby('gender'):
        train = x[(x.team_type == 'club') & (x.gender == gender) & x.won.isin([0.0, 1.0]) & (x.dt < g.dt.min())]
        med = train[feats].median()
        mdl = make_pipeline(StandardScaler(), LogisticRegression(C=team.WIN_C, max_iter=1000)).fit(train[feats].fillna(med), train.won.astype(int))
        rows.append(g[['match_id', 'team', 'team_key', 'opp_key']].assign(p_raw=mdl.predict_proba(g[feats].fillna(med))[:, 1]))
    r = pd.concat(rows)
    o = r[['match_id', 'team_key', 'p_raw']].rename(columns={'team_key': 'opp_key', 'p_raw': 'p_opp'})
    r = r.merge(o, on=['match_id', 'opp_key'])
    r['p_win'] = (r.p_raw + 1 - r.p_opp) / 2
    return r[['match_id', 'team', 'p_win']]


def totals(x, fut_ids, target):
    out = []
    # an unplayed game has no batting-first side unless the toss is in: price team1 batting first, and the swap
    xf = x.copy()
    fut = xf.match_id.isin(fut_ids)
    xf.loc[fut & xf.bat_first.isna(), 'batted_first'] = (xf.team == xf.team_first)[fut & xf.bat_first.isna()].astype(int)
    tf = team.totals_frame(xf, 'named')
    feats = team.totals_features(tf)
    ok = tf.full_first_inns.fillna(False).astype(bool) & tf.method.isna() & (tf.result != 'no result')
    if target == 'match_runs':
        ok &= tf.match_runs.notna()
    for (gender, comp), test in tf[tf.match_id.isin(fut_ids)].groupby(['gender', 'comp']):
        train = tf[ok & (tf.team_type == 'club') & (tf.gender == gender) & (tf.dt < test.dt.min())]
        med = train[feats].median()
        known = test.match_id.map(x.drop_duplicates('match_id').set_index('match_id').bat_first).notna().to_numpy()
        if team.TOTALS_KIND[(target, comp)] == 'venue':
            same = train[train.comp == comp]
            mu = test.venue_first_runs.fillna(same[target].mean()).to_numpy()
            rs = same[same.dt >= same.dt.max() - pd.Timedelta(days=3 * 365)]
            sd = float(np.std(rs[target] - rs.venue_first_runs.fillna(same[target].mean())))
        else:
            mdl = make_pipeline(StandardScaler(), Ridge(alpha=team.TOTALS_ALPHA)).fit(train[feats].fillna(med), train[target])
            mu = mdl.predict(test[feats].fillna(med))
            swapped = mdl.predict(team.swap_sides(test)[feats].fillna(med))
            mu = np.where(known, mu, (mu + swapped) / 2)
            rs = train[train.dt >= train.dt.max() - pd.Timedelta(days=3 * 365)]
            sd = float(np.std(rs[target] - mdl.predict(rs[feats].fillna(med))))
        out.append(pd.DataFrame({'match_id': test.match_id.to_numpy(), f'{target}_mu': mu, f'{target}_sd': sd}))
    return pd.concat(out) if out else pd.DataFrame(columns=['match_id'])


def recalibration_factors(d):
    """The factor each competition's next season gets: actual over predicted across every season already predicted."""
    path = os.path.join(d, 'props_preds.parquet')
    if not os.path.exists(path):
        return {}
    p = pd.read_parquet(path)
    f = {}
    for comp, g in p.groupby('comp'):
        for mu, y, played in (('mu_runs', 'bat_runs', 'did_bat'), ('mu_6s', 'bat_6s', 'did_bat'), ('mu_wkts', 'bowl_wkts', 'did_bowl')):
            q = g[g[played] == 1]
            raw = q[mu + '_raw'] if mu + '_raw' in q else q[mu]
            f[(comp, mu)] = float(q[y].sum() / raw.sum())
    return f


def player_prices(g, fut_ids, factors):
    out = []
    for gender, test in g[g.match_id.isin(fut_ids)].groupby('gender'):
        train = g[(g.gender == gender) & (g.team_type == 'club') & (g.dt < test.dt.min()) & ~g.future.fillna(False).astype(bool)]
        out.append(props.apply_models(props.fit_models(train), test))
    p = pd.concat(out, ignore_index=True)
    for mu in ('mu_runs', 'mu_6s', 'mu_wkts'):
        p[mu] = p[mu] * p.comp.map(lambda c: factors.get((c, mu), 1.0))
    for line in RUN_LINES:
        p[f'runs_over_{line}'] = props.p_over_nb(line, p.mu_runs, p.r_runs)          # given he bats
    for line in COUNT_LINES:
        p[f'sixes_over_{line}'] = props.p_over_nb(line, p.mu_6s, p.r_6s)
        p[f'wkts_over_{line}'] = props.p_over_nb(line, p.mu_wkts, p.r_wkts)           # given he bowls
    p['top_batter'] = np.nan
    for _, rows in p.groupby(['match_id', 'team']):
        p.loc[rows.index, 'top_batter'] = props.top_batter_probs(rows)
    return p


def price(d, fixtures, xis=None, squads=None):
    m, pl, dl, inn = load(d)
    fixtures = fixtures.copy()
    fixtures['date'] = pd.to_datetime(fixtures.date).dt.strftime('%Y-%m-%d')
    fm, fp, notes = future_rows(m, pl, fixtures, xis, squads)
    allm = pd.concat([m.assign(future=False), fm], ignore_index=True)
    allp = pd.concat([pl, fp], ignore_index=True)
    # league factors from every match before the first fixture (the backtest used matches before July 2022)
    from bbl.model.leagues import league_factors
    factors = league_factors(m, dl, fm.start_date.min())
    g, t = frame.build_from(allm, allp, dl, inn, factors)
    tt = allm[['match_id', 'team_type']]
    g, t = g.merge(tt, on='match_id'), t.merge(tt, on='match_id')
    fut_ids = set(fm.match_id)
    x = team.pairs(t)
    first = fm.set_index('match_id').team1
    x['team_first'] = x.match_id.map(first)
    games = fm[['match_id', 'start_date', 'competition', 'team1', 'team2', 'venue']].copy()
    w = win_chances(x, fut_ids)
    games = games.merge(w.rename(columns={'team': 'team1', 'p_win': 'p_team1'}), on=['match_id', 'team1'], how='left')
    for target in ('first_inns_runs', 'match_runs'):
        games = games.merge(totals(x, fut_ids, target), on='match_id', how='left')
    games['fair_team1'] = 1 / games.p_team1
    games['fair_team2'] = 1 / (1 - games.p_team1)
    players = player_prices(g, fut_ids, recalibration_factors(d))
    return games, players, notes


def write(d, games, players, notes):
    games.to_parquet(os.path.join(d, 'prices_games.parquet'), index=False)
    players.to_parquet(os.path.join(d, 'prices_players.parquet'), index=False)
    lines = ['# Our prices (fair odds, no margin)', '', '## Games', '', '| date | game | venue | team1 win | fair team1 | fair team2 | 1st inns runs | match runs |',
             '|---|---|---|---|---|---|---|---|']
    for r in games.itertuples():
        lines.append(f'| {r.start_date} | {r.team1} v {r.team2} | {r.venue} | {r.p_team1:.1%} | {r.fair_team1:.2f} | {r.fair_team2:.2f} | '
                     f'{r.first_inns_runs_mu:.0f} (sd {r.first_inns_runs_sd:.0f}) | {r.match_runs_mu:.0f} (sd {r.match_runs_sd:.0f}) |')
    lines += ['', '## Players: chance to bat, runs if he bats, sixes, top team batter', '',
              '| game | team | player | bats | runs if he bats | over 19.5 (if bats) | over 29.5 (if bats) | 1+ six (if bats) | top batter | bowls | 1+ wicket (if bowls) |',
              '|---|---|---|---|---|---|---|---|---|---|---|']
    for _, r in players.sort_values(['match_id', 'team', 'list_order']).iterrows():
        lines.append(f'| {r.match_id} | {r.team} | {r.player} | {r.p_bat:.0%} | {r.mu_runs:.1f} | {r["runs_over_19.5"]:.0%} | '
                     f'{r["runs_over_29.5"]:.0%} | {r["sixes_over_0.5"]:.0%} | {r.top_batter:.0%} | {r.p_bowl:.0%} | '
                     f'{r["wkts_over_0.5"]:.0%} |')
    lines += ['', '## Notes', ''] + [f'- {n}' for n in notes]
    text = '\n'.join(lines) + '\n'
    open(os.path.join(d, 'PRICES.md'), 'w').write(text)
    return text


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('parquet_dir')
    ap.add_argument('fixtures')
    ap.add_argument('--xi', help='named XIs: date, team, player')
    ap.add_argument('--squads', help='squads csv from bbl.collect.parse_squads (season, comp, club, player)')
    a = ap.parse_args()
    fx = pd.read_csv(a.fixtures, dtype=str)
    xi = pd.read_csv(a.xi, dtype=str) if a.xi else None
    if xi is not None:
        xi['date'] = pd.to_datetime(xi.date).dt.strftime('%Y-%m-%d')
    sq = pd.read_csv(a.squads, dtype=str) if a.squads else None
    print(write(a.parquet_dir, *price(a.parquet_dir, fx, xi, sq)))
