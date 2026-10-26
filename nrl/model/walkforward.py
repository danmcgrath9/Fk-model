"""Walk-forward predictions: for each season S, refit on every completed season before S, then price S.

This is how the model is used live (refit before each season, nrl/docs/RESEARCH_LOG.md), so it is the honest set to
compare with real odds: every season's prices come from a model that never saw that season. Team models: margin and
total (teams named, open, ratings only), win and margin bands from the key-number distribution. Try model: trees
counted on the last two seasons before S, then refit on all of them.

Writes nrl/cache/team_wf.parquet and nrl/cache/tries_wf.parquet, prints a per-season score.
Usage: python -m nrl.model.walkforward nrl/cache [first_season=2019]
"""
import sys

import lightgbm as lgb
import numpy as np
import pandas as pd

from nrl.model import team, tries
from nrl.model.team_frame import FEATURES_NAMED, FEATURES_OPEN


def team_walk(cache, first):
    g = team.games(pd.read_parquet(f'{cache}/team_frame.parquet'))
    out = []
    for s in range(first, int(g.season.max()) + 1):
        done = g[(g.season >= 2003) & (g.season < s)]
        t = g[g.season == s]
        if t.empty:
            continue
        row = t[['match_id', 'season', 'kick_off', 'team', 'opp', 'margin', 'total']].copy()
        for name, feats in (('named', FEATURES_NAMED), ('open', FEATURES_OPEN), ('ratings', ['exp_margin'])):
            mm = team.LinearT().fit(done[feats].to_numpy(), done.margin.to_numpy())
            kn = team.KeyNumbers().fit(mm, done[feats].to_numpy(), done.margin.to_numpy())
            X = t[feats].to_numpy()
            b = kn.bands(X)
            row[f'mu_{name}'] = mm.mean(X)
            row[f'p_home_{name}'] = b[:, 0] + b[:, 1] + 0.5 * b[:, 2]
            row[f'scale_{name}'] = mm.scale
            row[f'df_{name}'] = mm.df
        tm = team.LinearT().fit(done[team.TOTAL_FEATURES].to_numpy(), done.total.to_numpy())
        row['total_mu'] = tm.mean(t[team.TOTAL_FEATURES].to_numpy())
        row['total_scale'], row['total_df'] = tm.scale, tm.df
        out.append(row)
    wf = pd.concat(out, ignore_index=True)
    wf.to_parquet(f'{cache}/team_wf.parquet', index=False)
    print('team walk-forward (bits per game, teams named / open / ratings only):')
    for s, t in wf.groupby('season'):
        sc = {n: team.score(t[f'p_home_{n}'].to_numpy(), t.margin.to_numpy())['bits'] for n in ('named', 'open', 'ratings')}
        print(f'  {s}: ' + ' / '.join(f'{v:.3f}' for v in sc.values()) + f'  ({len(t)} games)')
    return wf


def tries_walk(cache, first):
    p = pd.read_parquet(f'{cache}/player_frame.parquet')
    p = p[p.season >= 2001]
    out = []
    for s in range(first, int(p.season.max()) + 1):
        t = p[p.season == s]
        if t.empty:
            continue
        tr, dv = p[(p.season >= 2003) & (p.season < s - 2)], p[p.season.isin([s - 2, s - 1])]
        d = lgb.Dataset(tr[tries.FEATURES], tr.tries, categorical_feature=['position_code'])
        m = lgb.train(tries.PARAMS, d, 3000, valid_sets=[lgb.Dataset(dv[tries.FEATURES], dv.tries, reference=d)],
                      callbacks=[lgb.early_stopping(100, verbose=False)])
        alln = p[(p.season >= 2003) & (p.season < s)]
        live = lgb.train(tries.PARAMS, lgb.Dataset(alln[tries.FEATURES], alln.tries, categorical_feature=['position_code']),
                         m.best_iteration)
        lam = live.predict(t[tries.FEATURES])
        r = t[['match_id', 'player_id', 'team', 'season', 'position', 'tries']].copy()
        r['lam'] = lam
        r['p_any'] = 1 - np.exp(-lam)
        tot = pd.Series(lam, index=t.index).groupby(t.match_id).transform('sum')
        r['p_first'] = lam / tot * (1 - np.exp(-tot))
        out.append(r)
        print(f'  tries {s}: log loss {tries.logloss(r.p_any, (r.tries > 0).astype(float)):.4f}')
    wf = pd.concat(out, ignore_index=True)
    wf.to_parquet(f'{cache}/tries_wf.parquet', index=False)
    return wf


def main(cache, first='2019'):
    team_walk(cache, int(first))
    tries_walk(cache, int(first))


if __name__ == '__main__':
    main(*sys.argv[1:3])
