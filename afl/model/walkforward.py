"""Out-of-sample projections for every prop, season by season, for testing against real lines.

For each season S from 2023: fit on 2013..S-2, early-stop and fit the spread on S-1, predict S. So every projection was
made by a model that never saw that season, which is what a backtest against 2023-2026 lines needs. Stats: disposals,
marks, tackles, goals. Output: afl/cache/walkforward.parquet, one row per player-game with mu (expected count) and a
(negative binomial spread) per stat.

Usage: python -m afl.model.walkforward afl/cache
"""
import json
import os
import sys
import warnings

import lightgbm as lgb
import numpy as np
import pandas as pd

from afl.model import extra as X
from afl.model import named_position as NP
from afl.model import props as P
from afl.model.disposals import PARAMS, fit_dispersion
from afl.model.frame import FEATURES

warnings.filterwarnings('ignore')
STATS = {'D': 'disposals', 'M': 'marks', 'T': 'tackles', 'G': 'goals'}
SEASONS = (2023, 2024, 2025, 2026)
# Stats whose spread is fitted per position. Disposals only: a midfielder's spread is narrower than a general player's
# (0.015 against 0.045 on 2024), and fitting it per position improved 2025-2026 log-likelihood by 0.0018 ± 0.0006 per
# player-game. Marks, tackles and goals showed no gain (afl/docs/TAILS.md), so they keep one spread.
POS_SPREAD = {'D'}
MIN_POS_ROWS = 500   # a position with fewer tuning rows than this uses the single spread
# the position named on the team sheet (afl/model/named_position.py): better on 2024-2025 for these stats
POSITION_STATS = {'D', 'T', 'G'}
KEPT = os.path.join(os.path.dirname(__file__), 'kept_inputs.json')   # written by afl/model/extra_test.py


def position_spread(tu, mu_tu, te, stat, a_single):
    """Spread per position, fitted on the tuning season; the single spread where a position is thin."""
    a_te = np.full(len(te), a_single)
    for p in te.pos.unique():
        sel = (tu.pos == p).to_numpy()
        if sel.sum() >= MIN_POS_ROWS:
            a_te[(te.pos == p).to_numpy()] = max(fit_dispersion(tu[stat].to_numpy()[sel], mu_tu[sel]), 1e-3)
    return a_te


def prepare(base, cache, stat):
    """Every row with this stat's features: the core list, the stat's own, the extra inputs afl/model/extra_test.py
    kept for it (more than two standard errors better on unseen seasons), and the team-sheet position where kept.
    Shared by the walk-forward, the final models and live pricing, so all three build the same inputs."""
    m, sfeats = P.stat_features(base, stat)
    kept = [c for c in json.load(open(KEPT)).get(stat, '').split(',') if c] if os.path.exists(KEPT) else []
    if kept:
        m = X.add_extra(m, cache, stat)
    feats = list(dict.fromkeys(FEATURES + sfeats + ['exp_score'] + kept))
    if 'pos' not in m:
        m = m.assign(pos=X.position(m))
    if stat in POSITION_STATS:
        m = NP.attach(m, cache)
        feats += NP.columns()
    return m, feats, kept


def stat_matrix(base, cache, stat):
    """Rows a book would price for this stat (an established player, not the named sub), with its features."""
    m, feats, kept = prepare(base, cache, stat)
    m = P.eligible(m)
    return m[m[f'{stat}_l10'].notna()], feats, kept


def params_for(stat):
    """Model settings per stat: the tuned ones (afl/model/tune.py, chosen on 2024) where they exist, else the defaults."""
    p = os.path.join(os.path.dirname(__file__), 'tuned_params.json')
    tuned = json.load(open(p)).get(stat, {}) if os.path.exists(p) else {}
    return {**PARAMS, **tuned}


def run(cache):
    base = P.team_expected_score(pd.read_parquet(f'{cache}/frame.parquet'))
    keys = ['game', 'season', 'Round', 'date', 'team', 'opp', 'player_id', 'Player']
    out = None
    for stat in STATS:
        m, feats, kept = stat_matrix(base, cache, stat)
        parts = []
        for S in SEASONS:
            tr, tu, te = m[m.season.between(2013, S - 2)], m[m.season == S - 1], m[m.season == S]
            mdl = lgb.LGBMRegressor(objective='poisson', **params_for(stat)).fit(
                tr[feats], tr[stat], eval_set=[(tu[feats], tu[stat])], callbacks=[lgb.early_stopping(150, verbose=False)])
            mu_tu = mdl.predict(tu[feats])
            a = max(fit_dispersion(tu[stat].to_numpy(), mu_tu), 1e-3)
            a_te = np.full(len(te), a)
            if stat in POS_SPREAD:
                a_te = position_spread(tu, mu_tu, te, stat, a)
            parts.append(te[keys + ['pos', stat]].assign(**{f'mu_{stat}': mdl.predict(te[feats]), f'a_{stat}': a_te}))
            print(f'{STATS[stat]} {S}: {len(te):,} player-games, spread {a:.3f}, extra inputs: {kept or "none"}', flush=True)
        p = pd.concat(parts)
        out = p if out is None else out.merge(p.drop(columns=['Player', 'pos']), on=[k for k in keys if k != 'Player'], how='outer')
    out.to_parquet(f'{cache}/walkforward.parquet', index=False)
    return out


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else 'afl/cache')
