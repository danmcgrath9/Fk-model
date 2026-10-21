"""Disposals projection, step 1 of afl/README.md, and its backtest against a STAND-IN line.

Projection: expected time on ground x disposals per full game on the ground, each a boosted-tree
model on pre-game features (afl/model/frame.py), compared on the tuning season with one model
that predicts disposals directly. The projection becomes a distribution (negative binomial,
spread fitted on the tuning season) so every line gets an over and an under probability.

Split, by season: fit 2013-2023, every choice made on 2024, then 2025 and 2026 scored once.

THE BACKTEST IS NOT A MARKET TEST. No history of real AFL prop lines has been found, so each
player's line here is a stand-in built from his recent average, the way books are said to set
them, at 1.87 each way. It shows where the projection disagrees with a recent-average line and
whether those disagreements win. Real books also see team news and set some lines sharper, so
a real-line test can only come out worse than this.

Usage: python -m afl.model.disposals afl/cache afl/docs/DISPOSALS_STEP1.md
"""
import sys
import warnings

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy import stats

from afl.model.frame import FEATURES

warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', message='.*eval_set.*deprecated')   # lightgbm 4.7 renamed it; 4.3 needs the old name
PRICE = 1.87                       # both sides, about 7% overround
TRAIN, TUNE, TESTS = (2013, 2023), 2024, (2025, 2026)
PARAMS = dict(n_estimators=3000, learning_rate=0.02, num_leaves=31, min_child_samples=200, subsample=0.8,
              subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0, verbose=-1, random_state=7)


def eligible(m):
    """Rows a book would price: an established player (5+ games on record), not the named sub."""
    return m[(m.games_prior >= 5) & (m.named_sub != 1) & m.D_l10.notna()].copy()


def fit(model, X, y, Xv, yv, w=None, wv=None):
    model.fit(X, y, sample_weight=w, eval_set=[(Xv, yv)], eval_sample_weight=[wv] if wv is not None else None,
              callbacks=[lgb.early_stopping(150, verbose=False)])
    return model


def train_models(tr, tu):
    F = FEATURES
    direct = fit(lgb.LGBMRegressor(objective='poisson', **PARAMS), tr[F], tr.D, tu[F], tu.D)
    trt, tut = tr[tr.TOG.notna()], tu[tu.TOG.notna()]
    tog = fit(lgb.LGBMRegressor(objective='regression', **PARAMS), trt[F], trt.TOG, tut[F], tut.TOG)
    # disposals per full game on the ground; weighted by time on ground so a five-minute cameo counts for little
    trr, tur = trt[trt.TOG >= 20], tut[tut.TOG >= 20]
    rate = fit(lgb.LGBMRegressor(objective='regression', **PARAMS), trr[F], trr.D / (trr.TOG / 100), tur[F],
               tur.D / (tur.TOG / 100), w=trr.TOG / 100, wv=tur.TOG / 100)
    return direct, tog, rate


def predict(models, d):
    direct, tog, rate = models
    d = d.copy()
    d['mu_direct'] = direct.predict(d[FEATURES])
    d['tog_hat'] = tog.predict(d[FEATURES]).clip(5, 100)
    d['rate_hat'] = rate.predict(d[FEATURES]).clip(0, None)
    d['mu_struct'] = d.tog_hat / 100 * d.rate_hat
    d['mu_blend'] = (d.mu_direct + d.mu_struct) / 2
    return d


def nb_logpmf(k, mu, a):
    n = 1 / a
    return stats.nbinom.logpmf(k, n, n / (n + mu))


def fit_dispersion(y, mu):
    grid = np.linspace(0.002, 0.15, 75)
    ll = [nb_logpmf(y, mu, a).sum() for a in grid]
    return float(grid[int(np.argmax(ll))])


def p_over(mu, line, a):
    n = 1 / a
    return 1 - stats.nbinom.cdf(np.floor(line), n, n / (n + mu))


def stand_in_line(avg, shift):
    """A recent-average book line: the player's average moved by `shift`, rounded to the .5 below."""
    return np.floor(np.asarray(avg) + shift) + 0.5


def even_shift(y, avg):
    """The shift that makes a blind over win half the time on the tuning season, so the stand-in line
    has no lean of its own: a book setting lines off averages would correct a known lean the same way."""
    grid = np.arange(-3, 3.01, 0.05)
    over = [(y > stand_in_line(avg, s)).mean() for s in grid]
    return float(grid[int(np.argmin(np.abs(np.array(over) - 0.5)))])


def bets(d, prob_col, thr):
    o = d[d[prob_col] > thr].assign(side='over', win=lambda x: x.D > x.line)
    u = d[(1 - d[prob_col]) > thr].assign(side='under', win=lambda x: x.D < x.line)
    return pd.concat([o, u])


def roi_with_ci(b, n_boot=2000, seed=11):
    """Profit per unit staked, with a 90% interval from resampling whole rounds (a round's games move together)."""
    if b.empty:
        return np.nan, np.nan, np.nan
    pnl = np.where(b.win, PRICE - 1, -1.0)
    rounds = b.season.astype(str) + '-' + b.Round.astype(str)
    by = pd.DataFrame({'r': rounds.to_numpy(), 'p': pnl}).groupby('r').p.agg(['sum', 'size'])
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(by), (n_boot, len(by)))
    boot = by['sum'].to_numpy()[idx].sum(1) / by['size'].to_numpy()[idx].sum(1)
    return pnl.mean(), np.percentile(boot, 5), np.percentile(boot, 95)


def run(cache, out_md):
    m = pd.read_parquet(f'{cache}/frame.parquet')
    m = eligible(m)
    tr = m[m.season.between(*TRAIN)]
    tu = m[m.season == TUNE]
    models = train_models(tr, tu)
    tu = predict(models, tu)

    # choose the projection and its spread on the tuning season only
    a_by = {c: fit_dispersion(tu.D.to_numpy(), tu[c].to_numpy()) for c in ('mu_direct', 'mu_struct', 'mu_blend')}
    ll_by = {c: nb_logpmf(tu.D.to_numpy(), tu[c].to_numpy(), a_by[c]).mean() for c in a_by}
    best = max(ll_by, key=ll_by.get)
    a = a_by[best]

    lines = {'last-10 average': 'D_l10', 'last-5 average': 'D_l5', 'season average': 'D_season'}
    shifts = {col: even_shift(tu.D[tu[col].notna()].to_numpy(), tu[col].dropna().to_numpy()) for col in lines.values()}
    rep = []
    W = lambda s='': rep.append(s)
    W('# AFL disposals, step 1: projection and a stand-in-line backtest')
    W()
    W('**Stand-in lines, not market lines.** No history of real AFL prop lines has been found. Each line below is '
      'built from the player\'s own recent average, moved by one fixed amount (chosen on the tuning season so a blind over wins half the time), at 1.87 each way. That is roughly how '
      'books are said to set them, but real books also see team news, and some lines will be sharper. Treat every ROI '
      'here as an upper bound on what real lines would give; the real test is against recorded openers from round 1 2027.')
    W()
    W(f'Fitted on {TRAIN[0]}-{TRAIN[1]} ({len(tr):,} player-games). Every choice made on {TUNE} ({len(tu):,}). '
      f'{TESTS[0]} and {TESTS[1]} scored once, untouched until then. Rows: established players (5+ games on record), named subs excluded.')
    W()
    W('## Which projection, chosen on the tuning season')
    W()
    W('| projection | mean log-likelihood per player-game (higher is better) | spread a |')
    W('|---|---|---|')
    names = {'mu_direct': 'disposals directly', 'mu_struct': 'time on ground x disposals per full game', 'mu_blend': 'average of the two'}
    for c in ll_by:
        W(f'| {names[c]} | {ll_by[c]:.4f} | {a_by[c]:.3f} |')
    W(f'\nChosen: **{names[best]}**. Spread: variance = mean + {a:.3f} x mean squared (negative binomial).')
    W()

    results = {}
    for season in TESTS:
        te = predict(models, m[m.season == season])
        te['mu'] = te[best]
        results[season] = te
    W('## Accuracy, unseen seasons')
    W()
    W('| season | player-games | projection miss (avg disposals) | last-10 average | last-5 average | season average |')
    W('|---|---|---|---|---|---|')
    for season, te in results.items():
        ok = te.D_season.notna()
        W(f'| {season} | {len(te):,} | {(te.D - te.mu).abs().mean():.2f} | {(te.D - te.D_l10).abs().mean():.2f} | '
          f'{(te.D - te.D_l5).abs().mean():.2f} | {(te.D[ok] - te.D_season[ok]).abs().mean():.2f} |')
    W()

    W('## Betting against stand-in lines, unseen seasons')
    W()
    W(f'Bet when the projection gives a side more than the stated chance; 1.87 breaks even at {1 / PRICE:.1%}. '
      'ROI is profit per unit staked; the interval resamples whole rounds (90%).')
    W()
    W('| season | stand-in line | bet when chance over | bets | overs / unders | hit rate | ROI | 90% interval |')
    W('|---|---|---|---|---|---|---|---|')
    keep = {}
    for season, te in results.items():
        for lname, col in lines.items():
            d = te[te[col].notna()].copy()
            d['line'] = stand_in_line(d[col].to_numpy(), shifts[col])
            d['p_over'] = p_over(d.mu.to_numpy(), d.line.to_numpy(), a)
            keep[(season, lname)] = d
            for thr in (0.535, 0.56, 0.60):
                b = bets(d, 'p_over', thr)
                r, lo, hi = roi_with_ci(b)
                W(f'| {season} | {lname} | {thr:.1%} | {len(b):,} | {(b.side == "over").sum():,} / {(b.side == "under").sum():,} | '
                  f'{b.win.mean():.1%} | {r:+.1%} | {lo:+.1%} to {hi:+.1%} |')
    W()
    W('Shift applied to each stand-in (chosen on ' + str(TUNE) + '): ' + ', '.join(f'{k} {shifts[v]:+.2f}' for k, v in lines.items()) + '.')
    W()
    W('A blind bet on every over and every under against the same lines, unseen seasons (a line method with no lean sits near 50/50):')
    W()
    W('| season | stand-in line | under hit rate | over hit rate |')
    W('|---|---|---|---|')
    for (season, lname), d in keep.items():
        W(f'| {season} | {lname} | {(d.D < d.line).mean():.1%} | {(d.D > d.line).mean():.1%} |')
    W()

    W('## Where the projection disagrees with a last-10 line, and what happened (both seasons)')
    W()
    d = pd.concat([keep[(s, 'last-10 average')] for s in TESTS])
    d['gap'] = d.mu - d.D_l10
    d['bucket'] = pd.cut(d.gap, [-30, -3, -1.5, -0.5, 0.5, 1.5, 3, 30])
    W('| projection minus last-10 average | player-games | projection gap | actual minus last-10 | went over the line |')
    W('|---|---|---|---|---|')
    for k, g in d.groupby('bucket', observed=True):
        W(f'| {k} | {len(g):,} | {g.gap.mean():+.2f} | {(g.D - g.D_l10).mean():+.2f} | {(g.D > g.line).mean():.1%} |')
    W()
    W('## By line size, 56%+ bets against last-10 lines (both seasons)')
    W()
    W('| line | bets | hit rate | ROI | 90% interval |')
    W('|---|---|---|---|---|')
    b = bets(d, 'p_over', 0.56)
    for lo_, hi_, lab in ((0, 15, 'under 15'), (15, 20, '15.5 to 19.5'), (20, 25, '20.5 to 24.5'), (25, 70, '25.5 and up')):
        bb = b[(b.line > lo_) & (b.line < hi_)]
        r, l, h = roi_with_ci(bb)
        W(f'| {lab} | {len(bb):,} | {bb.win.mean():.1%} | {r:+.1%} | {l:+.1%} to {h:+.1%} |')
    W()
    W('## Calibration: projected chance of going over a last-10 line against what happened (both seasons)')
    W()
    d['pbin'] = pd.cut(d.p_over, [0, .3, .4, .45, .5, .55, .6, .7, 1])
    W('| projected chance over | player-games | average projected | actually over |')
    W('|---|---|---|---|')
    for k, g in d.groupby('pbin', observed=True):
        W(f'| {k} | {len(g):,} | {g.p_over.mean():.1%} | {(g.D > g.line).mean():.1%} |')
    W()
    imp = pd.Series(models[0].booster_.feature_importance('gain'), index=FEATURES)
    imp_r = pd.Series(models[2].booster_.feature_importance('gain'), index=FEATURES)
    imp_t = pd.Series(models[1].booster_.feature_importance('gain'), index=FEATURES)
    W('## What the models lean on (share of gain, top 10)')
    W()
    W('| direct model | | time on ground model | | per-full-game rate model | |')
    W('|---|---|---|---|---|---|')
    tops = [(s / s.sum()).sort_values(ascending=False).head(10) for s in (imp, imp_t, imp_r)]
    for i in range(10):
        W('| ' + ' | '.join(f'{t.index[i]} | {t.iloc[i]:.1%}' for t in tops) + ' |')
    open(out_md, 'w').write('\n'.join(rep) + '\n')
    print('\n'.join(rep))
    pd.concat(results.values()).to_parquet(f'{cache}/disposals_test_predictions.parquet', index=False)


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else 'afl/cache', sys.argv[2] if len(sys.argv) > 2 else 'afl/docs/DISPOSALS_STEP1.md')
