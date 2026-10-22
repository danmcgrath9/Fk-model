"""Voulgaris's angles on NBL data (quarter scores, 2015-16 on).
  1. Halves: do second halves outscore first halves, by how much, every season, and more in close games?
     (a book that splits a full-game total 50/50, or prices the 2nd half off the 1st, would be wrong)
  2. Tendencies: is a team's second-half lean, or its 4th-quarter scoring, a lasting trait (split-half and
     season-to-season reliability), as he found for certain coaches?
  3. At halftime: predicting 2nd-half points from the 1st half and the margin, against naive rules.
Usage: python -m nbl.research.voulgaris nbl/cache"""
import sys

import numpy as np
import pandas as pd

from nbl.model.frame import base_games, season_year


def quarters(cache):
    bt = pd.read_parquet(f'{cache}/box_team.parquet')
    bt['season'] = bt.season.map(season_year)
    for c in ['p1_score', 'p2_score', 'p3_score', 'p4_score', 'ot_score', 'score', 'opp_score']:
        bt[c] = pd.to_numeric(bt[c], errors='coerce')
    g = base_games(pd.read_parquet(f'{cache}/results.parquet'))
    bt = bt.merge(g[['game', 'tip', 'home', 'away', 'home_score', 'away_score', 'ot', 'finals']], left_on='match_id', right_on='game')
    home = bt.home_away.astype(str).str.lower().isin(['home', '1', '1.0'])     # 'home'/'away' in this file
    bt['team'] = np.where(home, bt.home, bt.away)
    bt = bt.drop_duplicates(['game', 'team'])
    bt = bt[bt[['p1_score', 'p2_score', 'p3_score', 'p4_score']].notna().all(axis=1)]
    bt['h1'] = bt.p1_score + bt.p2_score
    bt['h2_reg'] = bt.p3_score + bt.p4_score
    # keep games whose quarters add up to the final score (regulation games only for the clean split)
    bt['final'] = np.where(home.loc[bt.index], bt.home_score, bt.away_score)
    return bt


def main(cache):
    t = quarters(cache)
    reg = t[(t.ot == 0) & ((t.h1 + t.h2_reg) == t.final)]
    g = reg.groupby('game').agg(season=('season', 'first'), tip=('tip', 'first'), h1=('h1', 'sum'), h2=('h2_reg', 'sum'),
                                q4=('p4_score', 'sum'), q1=('p1_score', 'sum'), q2=('p2_score', 'sum'), q3=('p3_score', 'sum'))
    m = t.groupby('game').apply(lambda d: d.final.max() - d.final.min() if len(d) == 2 else np.nan)
    g['final_margin'] = g.index.map(m)
    hm = t.groupby('game').apply(lambda d: abs(d.h1.iloc[0] - d.h1.iloc[1]) if len(d) == 2 else np.nan)
    g['half_margin'] = g.index.map(hm)
    g = g[g.final_margin.notna()]
    print(f'{len(g)} regulation games with quarters that add up ({len(t.game.unique())} games with quarter scores)\n')

    print('## 1. Points by half and quarter, both teams (regulation games)')
    s = g.groupby('season').agg(games=('h1', 'size'), h1=('h1', 'mean'), h2=('h2', 'mean'), q1=('q1', 'mean'), q2=('q2', 'mean'),
                                q3=('q3', 'mean'), q4=('q4', 'mean'))
    s['h2_minus_h1'] = s.h2 - s.h1
    s['share_2nd'] = s.h2 / (s.h1 + s.h2)
    print(s.round(2).to_string())
    print(f'\nall seasons: 2nd half minus 1st {(g.h2 - g.h1).mean():+.2f} points (sd of the gap {(g.h2 - g.h1).std():.1f}); '
          f'2nd half wins {np.mean(g.h2 > g.h1):.1%}, level {np.mean(g.h2 == g.h1):.1%}')
    g['close'] = pd.cut(g.final_margin, [-1, 5, 10, 20, 100], labels=['0-5', '6-10', '11-20', '21+'])
    c = g.groupby('close', observed=True).agg(games=('h1', 'size'), h2_minus_h1=('h1', lambda x: 0))
    c['h2_minus_h1'] = g.groupby('close', observed=True).apply(lambda d: (d.h2 - d.h1).mean())
    c['q4_minus_avg_q'] = g.groupby('close', observed=True).apply(lambda d: (d.q4 - (d.q1 + d.q2 + d.q3) / 3).mean())
    print('\nby final margin (close games are fouled late):'); print(c.round(2).to_string())
    hc = g.groupby(pd.cut(g.half_margin, [-1, 5, 10, 20, 100]), observed=True).apply(lambda d: pd.Series(
        {'games': len(d), 'h2_minus_h1': (d.h2 - d.h1).mean()}))
    print('\nby margin at half time (known when the 2nd-half line is set):'); print(hc.round(2).to_string())

    print('\n## 2. Is a team\'s second-half lean a lasting trait?')
    tr = t[(t.ot == 0)].copy()
    tr['lean'] = (tr.h2_reg - tr.h1) + (tr.groupby('game').h2_reg.transform('sum') - tr.h2_reg) - (tr.groupby('game').h1.transform('sum') - tr.h1)
    tr['game_lean'] = tr.groupby('game').h2_reg.transform('sum') - tr.groupby('game').h1.transform('sum')
    tr = tr.sort_values('tip'); tr['n'] = tr.groupby(['season', 'team']).cumcount()
    odd = tr[tr.n % 2 == 1].groupby(['season', 'team']).game_lean.mean()
    even = tr[tr.n % 2 == 0].groupby(['season', 'team']).game_lean.mean()
    j = pd.concat([odd, even], axis=1, keys=['odd', 'even']).dropna()
    print(f'split-half (odd v even games, same team-season), games\' 2nd-minus-1st in that team\'s games: r = {j.corr().iloc[0, 1]:.2f} '
          f'({len(j)} team-seasons)')
    ts = tr.groupby(['team', 'season']).game_lean.mean().reset_index()
    ts['next'] = ts.groupby('team').game_lean.shift(-1)
    print(f'season to next season, same team: r = {ts[["game_lean", "next"]].corr().iloc[0, 1]:.2f} ({ts.next.notna().sum()} pairs)')
    q4 = tr.assign(q4_share=tr.p4_score / tr.final).groupby(['season', 'team']).q4_share
    o4 = tr[tr.n % 2 == 1].assign(x=lambda d: d.p4_score / d.final).groupby(['season', 'team']).x.mean()
    e4 = tr[tr.n % 2 == 0].assign(x=lambda d: d.p4_score / d.final).groupby(['season', 'team']).x.mean()
    print(f'split-half, a team\'s own share of its points in the 4th quarter: r = {pd.concat([o4, e4], axis=1).dropna().corr().iloc[0, 1]:.2f}')

    print('\n## 3. At half time: predicting 2nd-half points (both teams)')
    g = g.sort_values('tip')
    dev, conf = g[g.season.between(2016, 2022)], g[g.season.between(2023, 2024)]
    league_ratio = dev.h2.mean() / dev.h1.mean()
    rules = {'2nd half = 1st half': lambda d: d.h1, '2nd half = 1st half x league ratio (fitted 2016-22)': lambda d: d.h1 * league_ratio}
    X = lambda d: np.column_stack([np.ones(len(d)), d.h1, np.minimum(d.half_margin, 25)])
    b = np.linalg.lstsq(X(dev), dev.h2, rcond=None)[0]
    rules['regression on 1st half and half-time margin (2016-22)'] = lambda d: X(d) @ b
    from nbl.model import team as team_model
    gt = team_model.games_table(team_model.with_rapm(pd.read_parquet(f'{cache}/teams.parquet'), cache))
    g2 = g.join(gt.set_index('game')[['exp_total', 'season']].rename(columns={'season': 's2'}), how='inner')
    dev2, conf2 = g2[g2.season.between(2016, 2022)].dropna(subset=['exp_total']), g2[g2.season.between(2023, 2024)].dropna(subset=['exp_total'])
    X2 = lambda d: np.column_stack([np.ones(len(d)), d.exp_total, d.h1, np.minimum(d.half_margin, 25)])
    b2 = np.linalg.lstsq(X2(dev2), dev2.h2, rcond=None)[0]
    sh = (dev2.h2 / dev2.exp_total).mean()
    rules['pre-game total x 2nd-half share (2016-22), ignoring the 1st half'] = lambda d: d.exp_total * sh
    rules['pre-game total, 1st half and half-time margin (2016-22)'] = lambda d: X2(d) @ b2
    conf = conf.loc[conf.index.intersection(conf2.index)].join(conf2[['exp_total']])
    for k, f in rules.items():
        print(f'  {k}: miss {np.abs(f(conf) - conf.h2).mean():.2f} pts, bias {np.mean(f(conf) - conf.h2):+.2f} (2023-24, {len(conf)} games)')
    print(f'  fitted: 2nd half = {b[0]:.1f} + {b[1]:.3f} x 1st half {b[2]:+.3f} x half-time margin (capped 25)')
    print(f'  fitted: 2nd half = {b2[0]:.1f} + {b2[1]:.3f} x pre-game total + {b2[2]:.3f} x 1st half {b2[3]:+.3f} x half-time margin')
    print(f'  pre-game totals: 1st half share of the full game {1 - dev.h2.sum() / (dev.h1.sum() + dev.h2.sum()):.1%} (2016-22), '
          f'{1 - conf.h2.sum() / (conf.h1.sum() + conf.h2.sum()):.1%} (2023-24)')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'nbl/cache')
