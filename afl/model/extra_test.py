"""Which extra inputs (afl/model/extra.py) earn a place? Per stat: the current model, then each extra group added on its
own, then all of them, fitted 2013-2023, tuned on 2024, scored on 2025-2026 (unseen). Paired against the current model,
per player-game, with standard errors. A group is kept where it improves log-likelihood by more than two standard errors.

Usage: python -m afl.model.extra_test afl/cache afl/docs/EXTRA_INPUTS.md
"""
import sys
import warnings

import lightgbm as lgb
import numpy as np
import pandas as pd

from afl.model import extra as X
from afl.model import props as P
from afl.model.disposals import PARAMS, fit_dispersion, nb_logpmf
from afl.model.frame import FEATURES

warnings.filterwarnings('ignore')
NAMES = {'D': 'disposals', 'M': 'marks', 'T': 'tackles', 'G': 'goals'}


def score(tr, tu, te, f, stat):
    mdl = lgb.LGBMRegressor(objective='poisson', **PARAMS).fit(tr[f], tr[stat], eval_set=[(tu[f], tu[stat])],
                                                               callbacks=[lgb.early_stopping(150, verbose=False)])
    a = max(fit_dispersion(tu[stat].to_numpy(), mdl.predict(tu[f])), 1e-3)
    mu = mdl.predict(te[f])
    return nb_logpmf(te[stat].to_numpy(), mu, a), np.abs(te[stat] - mu).to_numpy()


def run(cache, out_md):
    base = P.team_expected_score(pd.read_parquet(f'{cache}/frame.parquet'))
    rep = ['# Extra inputs: which earn a place', '',
           'Per stat, fitted 2013-2023, tuned on 2024, scored on 2025-2026 (never seen). Each row adds one group to the current '
           'model; "all extra" adds every group. Change in log-likelihood per player-game (higher is better) and in average '
           'miss, paired, ± one standard error. Kept: more than two standard errors better. Weather exists to 2025 only, so '
           'its 2026 rows carry no weather (the model treats it as unknown).', '']
    keep = {}
    for stat, label in NAMES.items():
        m, sfeats = P.stat_features(base, stat)
        m = X.add_extra(m, cache, stat)
        m = P.eligible(m)
        m = m[m[f'{stat}_l10'].notna()]
        core = list(dict.fromkeys(FEATURES + sfeats + ['exp_score']))
        tr, tu, te = m[m.season.between(2013, 2023)], m[m.season == 2024], m[m.season.isin([2025, 2026])]
        ll0, ae0 = score(tr, tu, te, core, stat)
        rep += [f'## {label.capitalize()}', '', f'Current model: average miss {ae0.mean():.3f}.', '',
                '| added | log-lik change | average miss change | kept |', '|---|---|---|---|']
        kept = []
        groups = X.extra_groups(stat)
        for g, cols in list(groups.items()) + [('all extra', sum(groups.values(), []))]:
            ll, ae = score(tr, tu, te, core + cols, stat)
            d, da = ll - ll0, ae - ae0
            se = d.std() / np.sqrt(len(d))
            ok = g != 'all extra' and d.mean() > 2 * se
            if ok:
                kept += cols
            rep.append(f'| {g} | {d.mean():+.4f} ± {se:.4f} | {da.mean():+.3f} ± {da.std() / np.sqrt(len(da)):.3f} | {"yes" if ok else ("" if g == "all extra" else "no")} |')
            print(stat, g, f'{d.mean():+.4f} ± {se:.4f}', flush=True)
        if kept:
            ll, ae = score(tr, tu, te, core + kept, stat)
            d, da = ll - ll0, ae - ae0
            rep.append(f'| **kept groups together** | {d.mean():+.4f} ± {d.std() / np.sqrt(len(d)):.4f} | {da.mean():+.3f} | |')
        keep[stat] = kept
        rep.append('')
    rep += ['## Kept, per stat', ''] + [f'- {NAMES[s]}: {", ".join(k) if k else "none"}' for s, k in keep.items()]
    open(out_md, 'w').write('\n'.join(rep) + '\n')
    from afl.model.walkforward import KEPT
    pd.Series({s: ','.join(k) for s, k in keep.items()}).to_json(KEPT)
    print('\n'.join(rep))


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else 'afl/cache', sys.argv[2] if len(sys.argv) > 2 else 'afl/docs/EXTRA_INPUTS.md')
