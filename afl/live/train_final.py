"""The models a live round is priced with: one per stat, trained on everything through the last finished season.

Per stat: fit 2013..last-1 and stop early on the last season, which fixes the number of trees and gives out-of-sample
projections for the last season to fit the spread on (per position for disposals, as in the walk-forward). Then refit
on 2013..last with that number of trees. Saved to afl/cache/models/<stat>.txt with <stat>.json (features, spread,
trees, seasons). Nothing here sees a game the live round will be scored on.

Usage: python -m afl.live.train_final afl/cache [last_season]
"""
import json
import os
import sys
import warnings

import lightgbm as lgb
import numpy as np
import pandas as pd

from afl.model import props as P
from afl.model.disposals import fit_dispersion
from afl.model.walkforward import MIN_POS_ROWS, POS_SPREAD, STATS, params_for, stat_matrix

warnings.filterwarnings('ignore')


def train(cache, last=2026):
    os.makedirs(f'{cache}/models', exist_ok=True)
    base = P.team_expected_score(pd.read_parquet(f'{cache}/frame.parquet'))
    for stat, label in STATS.items():
        m, feats, kept = stat_matrix(base, cache, stat)
        tr, tu = m[m.season.between(2013, last - 1)], m[m.season == last]
        params = params_for(stat)
        first = lgb.LGBMRegressor(objective='poisson', **params).fit(
            tr[feats], tr[stat], eval_set=[(tu[feats], tu[stat])], callbacks=[lgb.early_stopping(150, verbose=False)])
        mu = first.predict(tu[feats])
        a = max(fit_dispersion(tu[stat].to_numpy(), mu), 1e-3)
        a_pos = {}
        if stat in POS_SPREAD:
            for p in tu.pos.unique():
                sel = (tu.pos == p).to_numpy()
                if sel.sum() >= MIN_POS_ROWS:
                    a_pos[p] = max(fit_dispersion(tu[stat].to_numpy()[sel], mu[sel]), 1e-3)
        trees = int(first.best_iteration_)
        full = m[m.season.between(2013, last)]
        final = lgb.LGBMRegressor(objective='poisson', **{**params, 'n_estimators': trees}).fit(full[feats], full[stat])
        final.booster_.save_model(f'{cache}/models/{stat}.txt')
        json.dump({'stat': stat, 'features': feats, 'a': a, 'a_pos': a_pos, 'trees': trees, 'trained': [2013, last],
                   'spread_fitted_on': last, 'extra_inputs': kept}, open(f'{cache}/models/{stat}.json', 'w'), indent=1)
        print(f'{label}: {trees} trees, spread {a:.3f} {a_pos or ""}, {len(full):,} player-games', flush=True)


if __name__ == '__main__':
    train(sys.argv[1] if len(sys.argv) > 1 else 'afl/cache', int(sys.argv[2]) if len(sys.argv) > 2 else 2026)
