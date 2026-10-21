"""Anytime try scorer (and 2+, first try scorer): a count model of each player's tries in a game.

  model   LightGBM with a Poisson objective on nrl/model/player_frame.FEATURES, fitted on FIT seasons,
          number of trees chosen on DEV. Expected tries lam -> P(anytime) = 1 - exp(-lam),
          P(2+) = 1 - exp(-lam)(1 + lam). First try scorer: lam / (sum of lam over both 17s) x
          (1 - exp(-sum)), the share of a Poisson race.
  proxies two stand-in "books", labelled PROXY everywhere (no real try-scorer prices exist in our data
          yet; The Odds API holds them from May 2023):
            naive     the player's strike rate over his last 10 games, shrunk toward his position's rate
            position-aware  a logistic model on position, career and recent strike rate and the team's
                      expected points, fitted on FIT: roughly how a competent book would price it

Backtest: take every anytime "yes" where our probability beats the proxy's by EDGE or more, at the
proxy's FAIR price (no bookmaker margin). The ROI is therefore the margin a real book could charge
before the edge is gone; it is an upper bound, never a market result. Profit is bootstrapped by round.

Usage: python -m nrl.model.tries nrl/cache [nrl/docs/TRIES_STEP1.md] [--final]
"""
import sys

import lightgbm as lgb
from sklearn.linear_model import LogisticRegression
import numpy as np
import pandas as pd

from nrl.model.player_frame import CD_FEATURES, FEATURES as BASE_FEATURES

# CD_TRY=1 adds the Champion Data features (2014 on); compared against the base set in nrl/docs/TRIES_STEP1.md
import os
FEATURES = BASE_FEATURES + (CD_FEATURES if os.environ.get('CD_TRY') == '1' else [])

FIT = range(2003, 2019)
DEV = range(2019, 2023)
CONFIRM = range(2023, 2025)
FINAL = range(2025, 2027)
EDGES = [0.05, 0.10, 0.20, 0.30]
PARAMS = dict(objective='poisson', learning_rate=0.03, num_leaves=15, min_data_in_leaf=200,
              feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1, lambda_l2=5.0, verbose=-1, seed=7)


def proxy(p, k):
    """Last-10-games strike rate shrunk toward the position's strike rate in earlier seasons."""
    p = p.sort_values('i')
    g = p.groupby('player_id').scored
    hits = g.transform(lambda s: s.shift(1).rolling(10, min_periods=1).sum()).fillna(0)
    n = g.transform(lambda s: s.shift(1).rolling(10, min_periods=1).count()).fillna(0)
    pos_rate = p.groupby(['season', 'position']).scored.mean().groupby('position').shift(1)
    pr = pos_rate.reindex(pd.MultiIndex.from_arrays([p.season, p.position])).to_numpy()
    pr = np.where(np.isnan(pr), p.scored.mean(), pr)
    return pd.Series((hits + k * pr) / (n + k), index=p.index).reindex(p.index)


def sensible_proxy(p):
    """Position-aware stand-in book, fitted on FIT seasons only."""
    def X(d):
        pos = pd.get_dummies(d.position.astype(str)).reindex(columns=sorted(p.position.astype(str).unique()), fill_value=0)
        num = pd.DataFrame({'career': np.log(d.career_rate.clip(lower=0.01)), 'slow': d.try_ew_slow.fillna(d.career_rate),
                            'exp_for': d.exp_for, 'starter': d.starter}, index=d.index)
        return pd.concat([pos.astype(float), num], axis=1).fillna(0).to_numpy()
    tr = p[p.season.isin(FIT)]
    lr = LogisticRegression(C=1.0, max_iter=2000).fit(X(tr), tr.scored)
    return lr.predict_proba(X(p))[:, 1]


def logloss(prob, y):
    prob = np.clip(prob, 1e-6, 1 - 1e-6)
    return float(-(y * np.log(prob) + (1 - y) * np.log(1 - prob)).mean())


def fit(p):
    tr, dv = p[p.season.isin(FIT)], p[p.season.isin(DEV)]
    dtr = lgb.Dataset(tr[FEATURES], tr.tries, categorical_feature=['position_code'])
    ddv = lgb.Dataset(dv[FEATURES], dv.tries, reference=dtr)
    return lgb.train(PARAMS, dtr, 3000, valid_sets=[ddv], callbacks=[lgb.early_stopping(100, verbose=False)])


def first_try(p, lam):
    tot = pd.Series(lam, index=p.index).groupby(p.match_id).transform('sum')
    return lam / tot * (1 - np.exp(-tot))


def bootstrap_roi(bets, n=2000, seed=1):
    rng = np.random.default_rng(seed)
    by = bets.groupby('round_key').agg(stake=('stake', 'sum'), ret=('ret', 'sum'))
    s, r = by.stake.to_numpy(), by.ret.to_numpy()
    idx = rng.integers(0, len(by), size=(n, len(by)))
    roi = (r[idx].sum(1) - s[idx].sum(1)) / s[idx].sum(1)
    return np.percentile(roi, [5, 95])


def main(cache, out=None, final=False):
    p = pd.read_parquet(f'{cache}/player_frame.parquet')
    p = p[p.season >= 2001].copy()
    p['round_key'] = p.kick_off.dt.strftime('%G-%V')   # one NRL round per ISO week

    # proxy shrinkage on FIT only
    fitp = p[p.season.isin(FIT)]
    best_k = min([1, 2, 4, 6, 10], key=lambda k: logloss(proxy(fitp, k), fitp.scored))
    p['p_proxy'] = proxy(p, best_k)
    p['p_book'] = sensible_proxy(p)

    model = fit(p)
    p['lam'] = model.predict(p[FEATURES], num_iteration=model.best_iteration)
    p['p_any'] = 1 - np.exp(-p.lam)
    p['p_two'] = 1 - np.exp(-p.lam) * (1 + p.lam)
    p['p_first'] = first_try(p, p.lam.to_numpy())
    p['pos_only'] = p.groupby(['season', 'position']).scored.transform('mean')

    sets = [('dev', DEV), ('confirm', CONFIRM)] + ([('final', FINAL)] if final else [])
    lines = [f'Proxy shrinkage k = {best_k} (fitted on {FIT.start}-{FIT.stop - 1}); trees = {model.best_iteration}.', '',
             '## Who scores: log loss on P(anytime), lower is better', '',
             '| set | games | model | naive proxy | position-aware proxy | position average (same season, hindsight) | model 2+ log loss |',
             '|---|---|---|---|---|---|---|']
    bt = ['## Backtest against the PROXY at its fair price (an upper bound, not a market test)', '',
          '| set | proxy | edge needed | bets | strike rate | avg price | ROI | 90% interval (rounds resampled) |',
          '|---|---|---|---|---|---|---|---|']
    band = ['## By price band, position-aware proxy, 10% edge (where books charge most is the long end)', '',
            '| set | fair price | bets | strike rate | ROI | 90% interval |', '|---|---|---|---|---|---|']
    cal = ['## Calibration (all non-final sets): predicted vs actual anytime rate by decile', '',
           '| decile | predicted | actual | players |', '|---|---|---|---|']
    for lab, seasons in sets:
        t = p[p.season.isin(seasons)]
        lines.append(f'| {lab} {seasons.start}-{seasons.stop - 1} | {t.match_id.nunique():,} | {logloss(t.p_any, t.scored):.4f} | '
                     f'{logloss(t.p_proxy, t.scored):.4f} | {logloss(t.p_book, t.scored):.4f} | {logloss(t.pos_only, t.scored):.4f} | '
                     f'{logloss(t.p_two, (t.tries >= 2).astype(float)):.4f} |')
        for col, name in (('p_proxy', 'naive'), ('p_book', 'position-aware')):
            for e in EDGES:
                b = t[t.p_any >= t[col] * (1 + e)].copy()
                if len(b) == 0:
                    continue
                b['stake'] = 1.0
                b['ret'] = np.where(b.scored == 1, 1 / b[col], 0.0)
                roi = (b.ret.sum() - len(b)) / len(b)
                lo, hi = bootstrap_roi(b)
                bt.append(f'| {lab} | {name} | {e:.0%} | {len(b):,} | {b.scored.mean():.1%} | {(1 / b[col]).mean():.2f} | '
                          f'{roi:+.1%} | {lo:+.1%} to {hi:+.1%} |')
        b = t[t.p_any >= t.p_book * 1.10].copy()
        b['price'] = 1 / b.p_book
        b['stake'] = 1.0
        b['ret'] = np.where(b.scored == 1, b.price, 0.0)
        for lo_, hi_ in ((1, 2.5), (2.5, 4), (4, 7), (7, 15), (15, 1000)):
            c = b[(b.price >= lo_) & (b.price < hi_)]
            if len(c) < 30:
                continue
            roi = (c.ret.sum() - len(c)) / len(c)
            a, z = bootstrap_roi(c)
            band.append(f'| {lab} | {lo_}-{hi_ if hi_ < 1000 else "+"} | {len(c):,} | {c.scored.mean():.1%} | {roi:+.1%} | {a:+.1%} to {z:+.1%} |')
    nonfinal = p[p.season.isin(list(DEV) + list(CONFIRM))]
    nonfinal = nonfinal.assign(dec=pd.qcut(nonfinal.p_any, 10, labels=False))
    for d, grp in nonfinal.groupby('dec'):
        cal.append(f'| {d + 1} | {grp.p_any.mean():.3f} | {grp.scored.mean():.3f} | {len(grp):,} |')
    imp = pd.Series(model.feature_importance('gain'), index=FEATURES).sort_values(ascending=False)
    imp = (imp / imp.sum()).round(3)
    text = '\n'.join(lines + [''] + bt + [''] + band + [''] + cal + ['', '## What drives it (share of gain)', '',
                                                         ', '.join(f'{k} {v:.0%}' for k, v in imp.head(10).items()), ''])
    print(text)
    if out:
        open(out, 'w').write(text)
    p[['match_id', 'player_id', 'team', 'season', 'position', 'tries', 'lam', 'p_any', 'p_two', 'p_first', 'p_proxy', 'p_book']] \
        .to_parquet(f'{cache}/try_predictions.parquet', index=False)
    return p


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    main(args[0], args[1] if len(args) > 1 else None, final='--final' in sys.argv)
