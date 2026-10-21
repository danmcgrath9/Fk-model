"""Team model: predicted margin and total per game, priced into head-to-head, line and total.

Two versions, same machinery, different line-up information:
  open   what was knowable when books open a round: ratings, schedule, and LAST game's line-up
  named  adds THIS game's line-up (who took the field; RLP has no Tuesday lists, so late changes are
         folded in and this version is a little optimistic)

Margin and total are each a linear model on the features, fitted on FIT seasons. Their errors are
fitted as a Student-t on the same seasons, so every price (win, line at any handicap, total at any
line) is a probability from one distribution. Scored on DEV and CONFIRM seasons; FINAL seasons are
touched once, when the model is frozen (`--final`).

Usage: python -m nrl.model.team nrl/cache [nrl/docs/TEAM_STEP1.md] [--final]
"""
import sys

import numpy as np
import pandas as pd
from scipy import stats

from nrl.model.team_frame import FEATURES_NAMED, FEATURES_OPEN

FIT = range(2003, 2019)
DEV = range(2019, 2023)
CONFIRM = range(2023, 2025)
FINAL = range(2025, 2027)
# extra features made the total worse on DEV (miss 10.11 against 10.07): the ratings' expected total alone
TOTAL_FEATURES = ['exp_total']


def games(tf):
    """One row per game, from the home side's view."""
    g = tf[tf.home == 1].copy()
    for c in FEATURES_OPEN + FEATURES_NAMED:
        if c in g:
            g[c] = g[c].astype(float)
    g['is_final'] = g['is_final'].astype(float)
    return g


class LinearT:
    """Least squares for the mean, a Student-t fitted to the residuals for the spread."""

    def fit(self, X, y):
        X = self._x(X)
        ok = ~np.isnan(X).any(axis=1)
        self.coef, *_ = np.linalg.lstsq(X[ok], y[ok], rcond=None)
        resid = y[ok] - X[ok] @ self.coef
        self.df, _, self.scale = stats.t.fit(resid, floc=0)
        return self

    def mean(self, X):
        return self._x(X) @ self.coef

    def prob_above(self, X, line):
        """P(outcome > line); a line ending in .5 never pushes."""
        return 1 - stats.t.cdf(line - self.mean(X), self.df, scale=self.scale)

    @staticmethod
    def _x(X):
        X = np.asarray(X, dtype=float)
        return np.column_stack([np.ones(len(X)), np.nan_to_num(X, nan=0.0)])


def win_prob(model, X):
    """Home win, counting a draw as half (the scoring rule below does the same)."""
    return model.prob_above(X, 0.0) + 0.5 * (model.prob_above(X, -0.5) - model.prob_above(X, 0.5))


def score(p, margin):
    """Bits (1 + log2 of the probability given to what happened; a draw scores 1 + log2 of sqrt(p(1-p))),
    log loss and Brier on the home-win probability."""
    p = np.clip(p, 1e-6, 1 - 1e-6)
    y = np.where(margin > 0, 1.0, np.where(margin < 0, 0.0, 0.5))
    bits = np.where(y == 1, 1 + np.log2(p), np.where(y == 0, 1 + np.log2(1 - p), 1 + 0.5 * np.log2(p * (1 - p))))
    ll = -(y * np.log(p) + (1 - y) * np.log(1 - p))
    return dict(bits=bits.mean(), logloss=ll.mean(), brier=((p - y) ** 2).mean(),
                tips=((p > 0.5) == (y == 1)).mean())


def evaluate(g, seasons, label):
    fit = g[g.season.isin(FIT)]
    rows = []
    variants = {
        'home team always 59%': None,
        'ratings only': ['exp_margin'],
        'open': FEATURES_OPEN,
        'teams named': FEATURES_NAMED,
    }
    models = {}
    for name, feats in variants.items():
        if feats is None:
            continue
        mm = LinearT().fit(fit[feats].to_numpy(), fit.margin.to_numpy())
        tm = LinearT().fit(fit[TOTAL_FEATURES].to_numpy(), fit.total.to_numpy())
        models[name] = (feats, mm, tm)
    base = (fit.margin > 0).mean() + 0.5 * (fit.margin == 0).mean()
    for s in seasons:
        t = g[g.season == s]
        r = score(np.full(len(t), base), t.margin.to_numpy())
        rows.append(dict(season=s, model=f'home team always {base:.0%}', **r, mae_margin=np.nan, mae_total=np.nan))
        for name, (feats, mm, tm) in models.items():
            p = win_prob(mm, t[feats].to_numpy())
            r = score(p, t.margin.to_numpy())
            tf_ = TOTAL_FEATURES
            rows.append(dict(season=s, model=name, **r,
                             mae_margin=np.abs(mm.mean(t[feats].to_numpy()) - t.margin).mean(),
                             mae_total=np.abs(tm.mean(t[tf_].to_numpy()) - t.total).mean()))
    out = pd.DataFrame(rows)
    out['set'] = label
    return out, models


def table(df):
    lines = ['| season | model | bits/game | log loss | Brier | tips right | margin miss | total miss |',
             '|---|---|---|---|---|---|---|---|']
    for r in df.itertuples():
        mm = '' if np.isnan(r.mae_margin) else f'{r.mae_margin:.2f}'
        mt = '' if np.isnan(r.mae_total) else f'{r.mae_total:.2f}'
        lines.append(f'| {r.season} | {r.model} | {r.bits:.3f} | {r.logloss:.3f} | {r.brier:.3f} | {r.tips:.1%} | {mm} | {mt} |')
    return lines


def main(cache, out=None, final=False):
    g = games(pd.read_parquet(f'{cache}/team_frame.parquet'))
    sets = [('dev', DEV), ('confirm', CONFIRM)] + ([('final', FINAL)] if final else [])
    res = pd.concat([evaluate(g, s, lab)[0] for lab, s in sets])
    agg = res.groupby(['set', 'model'], sort=False)[['bits', 'logloss', 'brier', 'tips', 'mae_margin', 'mae_total']].mean()
    print(agg.round(4).to_string())
    _, models = evaluate(g, [], '')
    for name, (feats, mm, tm) in models.items():
        print(name, 'margin coef', dict(zip(['const'] + feats, np.round(mm.coef, 3))), f't df {mm.df:.1f} scale {mm.scale:.2f}')
    if out:
        with open(out, 'w') as fh:
            fh.write('\n'.join(table(res)) + '\n')
    return res, agg


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    main(args[0], args[1] if len(args) > 1 else None, final='--final' in sys.argv)
