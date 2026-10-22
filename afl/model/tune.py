"""Model settings per stat, chosen on 2024 only, then checked on 2025-2026.

For each stat and each candidate setting: fit 2013-2022, stop early on 2023, fit the spread on 2023, score 2024
(log-likelihood per player-game). The best on 2024 is then compared with the defaults on 2025-2026 (fit 2013-2023, stop
early and fit the spread on 2024), paired per player-game. It is adopted only if it is not worse there by more than one
standard error: 2024 chooses, the unseen seasons can only veto. Writes afl/model/tuned_params.json and afl/docs/TUNING.md.

Usage: python -m afl.model.tune afl/cache afl/docs/TUNING.md
"""
import json
import os
import sys
import warnings

import lightgbm as lgb
import numpy as np
import pandas as pd

from afl.model import props as P
from afl.model.disposals import PARAMS, fit_dispersion, nb_logpmf
from afl.model.walkforward import STATS, stat_matrix

warnings.filterwarnings('ignore')
CANDIDATES = [
    {},
    {'num_leaves': 15},
    {'num_leaves': 63},
    {'min_child_samples': 50},
    {'min_child_samples': 500},
    {'colsample_bytree': 0.5},
    {'num_leaves': 15, 'min_child_samples': 500},
    {'num_leaves': 63, 'min_child_samples': 100, 'colsample_bytree': 0.5},
    {'reg_lambda': 10.0},
    {'learning_rate': 0.01, 'n_estimators': 6000},
]


def loglik(tr, es, te, feats, stat, extra):
    mdl = lgb.LGBMRegressor(objective='poisson', **{**PARAMS, **extra}).fit(
        tr[feats], tr[stat], eval_set=[(es[feats], es[stat])], callbacks=[lgb.early_stopping(150, verbose=False)])
    a = max(fit_dispersion(es[stat].to_numpy(), mdl.predict(es[feats])), 1e-3)
    return nb_logpmf(te[stat].to_numpy(), mdl.predict(te[feats]), a), mdl.best_iteration_


def run(cache, out_md):
    base = P.team_expected_score(pd.read_parquet(f'{cache}/frame.parquet'))
    rep = ['# Model settings per stat', '',
           'Each candidate fitted 2013-2022, stopped early on 2023, scored on 2024 (log-likelihood per player-game, against '
           'the defaults). The best on 2024 is then checked on 2025-2026, never seen; adopted unless worse there by more than '
           'one standard error.', '']
    chosen = {}
    for stat, label in STATS.items():
        m, feats, _ = stat_matrix(base, cache, stat)
        tr, es, te = m[m.season.between(2013, 2022)], m[m.season == 2023], m[m.season == 2024]
        ll0, _ = loglik(tr, es, te, feats, stat, {})
        rows = []
        for c in CANDIDATES:
            ll, it = (ll0, None) if not c else loglik(tr, es, te, feats, stat, c)
            d = ll - ll0
            rows.append((c, d.mean(), d.std() / np.sqrt(len(d)), it))
            print(stat, c, f'{d.mean():+.5f}', flush=True)
        best = max(rows, key=lambda r: r[1])
        rep += [f'## {label.capitalize()}', '', '| setting | 2024 change vs defaults |', '|---|---|']
        rep += [f'| {json.dumps(c) if c else "defaults"} | {d:+.5f} ± {se:.5f} |' for c, d, se, _ in rows]
        verdict = 'defaults kept (no candidate beat them on 2024)'
        if best[0] and best[1] > 0:
            tr2, es2, te2 = m[m.season.between(2013, 2023)], m[m.season == 2024], m[m.season.isin([2025, 2026])]
            a, _ = loglik(tr2, es2, te2, feats, stat, {})
            b, _ = loglik(tr2, es2, te2, feats, stat, best[0])
            d = b - a
            se = d.std() / np.sqrt(len(d))
            ok = d.mean() > -se
            verdict = (f'best on 2024: {json.dumps(best[0])}; on 2025-2026 it changes log-likelihood by {d.mean():+.5f} ± {se:.5f}: '
                       + ('adopted' if ok else 'vetoed, defaults kept'))
            if ok:
                chosen[stat] = best[0]
        rep += ['', verdict, '']
    rep += ['The gains here are small next to the inputs: settings matter less than what the model is given.', '']
    json.dump(chosen, open(os.path.join(os.path.dirname(__file__), 'tuned_params.json'), 'w'), indent=1)
    open(out_md, 'w').write('\n'.join(rep) + '\n')
    print('\n'.join(rep))


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else 'afl/cache', sys.argv[2] if len(sys.argv) > 2 else 'afl/docs/TUNING.md')
