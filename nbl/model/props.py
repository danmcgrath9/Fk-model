"""NBL player props: points, rebounds, assists, threes, points+rebounds+assists.

Projection, per player per game, from pre-game information only (nbl/model/frame.py):
  structural  expected minutes (a model of minutes) x the player's per-minute rate (decayed, shrunk to the
              league) x a fitted adjustment for opponent, pace, expected margin and teammates out
  direct      gradient-boosted Poisson model on every pre-game feature
  blend       the average of the two (chosen on the tuning season if it beats both)
Each projection becomes a full distribution (negative binomial, spread fitted on the tuning season), so
any over/under line can be priced.

Which games count: the player dressed and played (an unplayed prop is void at Australian books), had at
least 5 earlier games and usually plays 12+ minutes (books list the rotation, not the end of the bench).

No real prop lines exist yet. The backtest is against STAND-IN lines: the player's last-10 (or last-5)
average, moved by one fixed amount chosen on the tuning season so a blind over wins half the time, at
1.87 each way. That is how books are said to set lines; real books see the same team news, so any
result here is an upper bound on a real edge, never a market test.

Seasons (named by the year they start): fit 2016-2021, tune 2022, confirm 2023-2024, final check
2025-2026 (2026 = this season to 18 Oct 2026).

The final-check seasons are left out of every table unless NBL_FINAL=1 is set, so the model can be
worked on against the confirm seasons and the final check is looked at once.

Usage: python -m nbl.model.props nbl/cache nbl/docs/PROPS_STEP1.md        (NBL_FINAL=1 to include 2025-2026)
"""
import os
import sys
import warnings

import numpy as np
import pandas as pd
from scipy import optimize, stats
from sklearn.ensemble import HistGradientBoostingRegressor

from nbl.model.frame import PLAYER_FEATURES, PROPS

warnings.filterwarnings('ignore')
FIT, TUNE, CONFIRM, FINAL = (2016, 2021), 2022, (2023, 2024), (2025, 2026)
PRICE = 1.87                      # both sides, about 7% overround
MIN_GAMES, MIN_MINUTES = 5, 12.0
USE_BOOST = False                 # usage redistribution: tried, no gain at any lookback (nbl/docs/RESEARCH.md)
NAMES = {'pts': 'points', 'reb': 'rebounds', 'ast': 'assists', 'fg3m': 'threes', 'pra': 'points+rebounds+assists'}
RATE = {'pts': 'r_pts', 'reb': 'r_reb', 'ast': 'r_ast', 'fg3m': 'r_fg3m'}
OPP = {'pts': 'opp_pts_rel', 'reb': 'opp_reb_rel', 'ast': 'opp_ast_rel', 'fg3m': 'opp_fg3m_rel'}
MIN_FEATURES = ['min_ew', 'min_ew_season', 'min_last', 'min_l3', 'min_sd', 'start_ew', 'start_last', 'dnp_l5', 'games_prior',
                'games_season', 'days_since', 'prev_team_same', 'squad_min_pool', 'min_out', 'min_in', 'n_out', 'min_share',
                'min_scaled', 'elo_margin', 'exp_blowout', 'is_home', 'days_rest', 'b2b', 'finals', 'r_eff', 'r_pts']


def eligible(p):
    """Rows that count: played (a prop on a player who does not play is void), or still to be played."""
    return p[((p.played == 1) | p.played.isna()) & (p.games_prior >= MIN_GAMES) & (p.min_ew >= MIN_MINUTES)].copy()


def gbm(X, y, Xv, yv, loss):
    best = None
    for lr, leaves in ((0.05, 15), (0.05, 31), (0.03, 15)):
        m = HistGradientBoostingRegressor(loss=loss, learning_rate=lr, max_leaf_nodes=leaves, max_iter=600, min_samples_leaf=40,
                                          l2_regularization=1.0, early_stopping=True, validation_fraction=0.15, random_state=7)
        m.fit(X, y)
        pred = np.clip(m.predict(Xv), 1e-3, None)
        score = poisson_dev(yv, pred) if loss == 'poisson' else np.mean((yv - pred) ** 2)
        if best is None or score < best[0]:
            best = (score, m)
    return best[1]


def poisson_dev(y, mu):
    y = np.asarray(y, float); mu = np.clip(np.asarray(mu, float), 1e-6, None)
    t = np.where(y > 0, y * np.log(np.where(y > 0, y, 1) / mu), 0.0)
    return float(2 * np.mean(t - (y - mu)))


def structural_design(d, market, min_hat):
    """log-scale inputs of the structural model: log(minutes x rate) as the offset, adjustments as features."""
    if market == 'pra':
        base = min_hat * (d.r_pts + d.r_reb + d.r_ast)
        opp = (d.opp_pts_rel * d.r_pts + d.opp_reb_rel * d.r_reb + d.opp_ast_rel * d.r_ast) / (d.r_pts + d.r_reb + d.r_ast)
    else:
        base = min_hat * d[RATE[market]]
        opp = d[OPP[market]]
    boost = (d.boost_pts + d.boost_reb + d.boost_ast) if market == 'pra' else d[f'boost_{market}'] if f'boost_{market}' in d else \
        d.boost_fg3a * (d.r_fg3m / d.r_fg3a.clip(1e-4))
    X = pd.DataFrame({'log_opp': np.log(opp.fillna(1.0).clip(0.5, 2)), 'log_pace': np.log(d.pace_rel.fillna(1.0).clip(0.8, 1.2)),
                      'blowout': d.exp_blowout.fillna(0) / 10, 'min_out': d.min_out.fillna(0) / 30,
                      'b2b': d.b2b.fillna(0), 'home': d.is_home})
    if USE_BOOST:
        # what absent teammates usually produce, this player's share of it, against his own base (usage redistribution)
        X['log_boost'] = np.log1p(boost.fillna(0) / np.exp(np.log(base.clip(1e-3))))
    return np.log(base.clip(1e-3)), X


def poisson_glm(offset, X, y, lam=1.0):
    """Poisson regression with an offset (log of minutes x rate) and a light ridge penalty."""
    Z = np.column_stack([np.ones(len(X)), X.to_numpy(float)])

    def f(b):
        eta = offset + Z @ b
        mu = np.exp(eta)
        return np.sum(mu - y * eta) + lam * np.sum(b[1:] ** 2), Z.T @ (mu - y) + 2 * lam * np.r_[0, b[1:]]
    return optimize.minimize(f, np.zeros(Z.shape[1]), jac=True, method='L-BFGS-B').x


def glm_predict(b, offset, X):
    return np.exp(offset + np.column_stack([np.ones(len(X)), X.to_numpy(float)]) @ b)


def fit_dispersion(y, mu):
    """Negative binomial: variance = mu + a mu^2. Maximum likelihood for a on the tuning season."""
    y = np.asarray(y, float); mu = np.asarray(mu, float)

    def nll(log_a):
        a = np.exp(log_a); n = 1 / a
        return -np.sum(stats.nbinom.logpmf(y, n, n / (n + mu)))
    return float(np.exp(optimize.minimize_scalar(nll, bounds=(-8, 2), method='bounded').x))


def fit_spread(y, mu):
    """Negative binomial spread that changes with the projection: a(mu) = a0 * mu^k, by maximum likelihood on
    the tuning season. Chosen over one spread per market because it scored better on 2022-23 and on 2023-24
    to 2024-25, in every market but rebounds (level) (nbl/research/distributions.py)."""
    y = np.asarray(y, float); mu = np.asarray(mu, float)

    def nll(t):
        a = np.clip(np.exp(t[0]) * mu ** t[1], 1e-4, 50); n = 1 / a
        return -np.sum(stats.nbinom.logpmf(y, n, n / (n + mu)))
    t = optimize.minimize(nll, [np.log(0.2), 0.0], method='Nelder-Mead').x
    return float(np.exp(t[0])), float(t[1])


def spread(c, mu):
    """The spread for projection(s) mu from a market's fitted (a0, k)."""
    return np.clip(c['a0'] * np.asarray(mu, float) ** c['k'], 1e-4, 50)


def p_over(mu, line, a):
    """Chance of finishing above a .5 line."""
    n = 1 / a
    return 1 - stats.nbinom.cdf(np.floor(line), n, n / (n + np.asarray(mu, float)))


SHOT_DRAWS = 3000
SIMULATED = ('pts', 'pra')        # markets that may be priced by simulation (chosen per market on the tuning season)


def shot_draws(d, mu, min_sd, seed=12345, market='pts'):
    """Points as shots: minutes ~ normal(min_hat, min_sd), two-point, three-point and free-throw attempts
    Poisson from the player's per-minute rates, makes binomial at his shrunk percentages; then rescaled so
    the draws' mean is the projection (the model owns the mean, the shots own the shape). One row per player."""
    rng = np.random.default_rng(seed)
    n = len(d)
    m = np.clip(rng.normal(d.min_hat.to_numpy(float)[:, None], min_sd, (n, SHOT_DRAWS)), 1, 48)
    fga, fg3a, fta = (d[c].to_numpy(float)[:, None] for c in ('r_fga', 'r_fg3a', 'r_fta'))
    pct3 = np.clip(d.r_fg3m.to_numpy(float) / np.clip(d.r_fg3a.to_numpy(float), 1e-4, None), 0.05, 0.7)[:, None]
    pct_fg = np.clip(d.r_fgm.to_numpy(float) / np.clip(d.r_fga.to_numpy(float), 1e-4, None), 0.2, 0.8)[:, None]
    fga2 = np.clip(fga - fg3a, 1e-4, None)
    pct2 = np.clip((pct_fg * fga - pct3 * fg3a) / fga2, 0.2, 0.85)
    pctft = np.clip(d.r_ftm.to_numpy(float) / np.clip(d.r_fta.to_numpy(float), 1e-4, None), 0.3, 0.98)[:, None]
    pts = (2 * rng.binomial(rng.poisson(fga2 * m), pct2) + 3 * rng.binomial(rng.poisson(fg3a * m), pct3)
           + rng.binomial(2 * rng.poisson(fta * m / 2), pctft)).astype(float)
    if market == 'pra':
        # rebounds and assists Poisson at the player's rates over the SAME minutes, so all three move together
        pts = pts + rng.poisson(d.r_reb.to_numpy(float)[:, None] * m) + rng.poisson(d.r_ast.to_numpy(float)[:, None] * m)
    scale = np.asarray(mu, float) / np.clip(pts.mean(1), 0.1, None)
    return np.rint(pts * scale[:, None])


def chance_over(mk, d, mu, line, c):
    """Our chance of finishing above a .5 line: shot simulation for points when chosen on the tuning season
    (c['shots']), else the negative binomial with the projection-dependent spread."""
    mu, line = np.asarray(mu, float), np.asarray(line, float)
    if mk in SIMULATED and c.get('shots'):
        draws = shot_draws(d, mu, c['min_sd'], market=mk)
        return (draws > line[:, None]).mean(1)
    return p_over(mu, line, spread(c, mu))


def line_logloss(y, po, line):
    po = np.clip(po, 1e-4, 1 - 1e-4)
    return float(np.mean(np.where(np.asarray(y) > np.asarray(line), -np.log(po), -np.log(1 - po))))


MIN_LINE = {'pts': 7.5, 'reb': 2.5, 'ast': 1.5, 'fg3m': 0.5, 'pra': 11.5}   # books post props on rotation players


def stand_in_line(avg, shift):
    return np.floor(avg + shift) + 0.5


def marketable(d, mk):
    """Only the lines a book would post: no line below the market's floor (set before the final check)."""
    return d[d.line >= MIN_LINE[mk]]


def even_shift(y, avg):
    grid = np.arange(-3.0, 3.01, 0.05)
    over = np.array([(y > stand_in_line(avg, s)).mean() for s in grid])
    return float(grid[np.argmin(np.abs(over - 0.5))])


def round_id(d):
    """Betting rounds for the bootstrap: season and Australian week."""
    return d.season.astype(str) + '-' + d.day.dt.isocalendar().week.astype(str)


def roi_ci(b, n_boot=2000, seed=11):
    """ROI of 1-unit bets (at each bet's price, PRICE if none), with a 90% interval from resampling whole rounds."""
    if len(b) == 0:
        return np.nan, np.nan, np.nan
    price = b['price'].to_numpy() if 'price' in b else np.full(len(b), PRICE)
    prof = np.where(b.win, price - 1, -1.0)
    g = pd.DataFrame({'r': b.rnd.to_numpy(), 'p': prof}).groupby('r').p.agg(['sum', 'count'])
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(g), size=(n_boot, len(g)))
    s, c = g['sum'].to_numpy()[idx].sum(1), g['count'].to_numpy()[idx].sum(1)
    boots = s / c
    return prof.mean(), np.percentile(boots, 5), np.percentile(boots, 95)


NAIVE_MARGIN = 0.07        # the stand-in book's overround


def naive_book(d, mk, col, k, a_naive):
    """A stand-in book that prices both sides of the stand-in line from the player's recent average alone:
    negative binomial around (average x k), k and the spread fitted on the tuning season, 7% overround."""
    p_o = np.clip(p_over(d[f'{mk}_{col}'] * k, d.line, a_naive), 0.02, 0.98)
    return 1 / (p_o * (1 + NAIVE_MARGIN)), 1 / ((1 - p_o) * (1 + NAIVE_MARGIN))


def value_bets(d, edge):
    """Bet a side when our chance x the stand-in book's price is at least 1 + edge."""
    eo = d.p_over * d.price_over - 1
    eu = (1 - d.p_over) * d.price_under - 1
    over = (eo >= edge) & (eo >= eu)
    under = (eu >= edge) & (eu > eo)
    return pd.concat([d[over].assign(side='over', win=lambda x: x.y > x.line, price=lambda x: x.price_over),
                      d[under].assign(side='under', win=lambda x: x.y < x.line, price=lambda x: x.price_under)])


def bets(d, thr):
    over = d.p_over >= thr
    under = (1 - d.p_over) >= thr
    b = pd.concat([d[over].assign(side='over', win=lambda x: x.y > x.line),
                   d[under].assign(side='under', win=lambda x: x.y < x.line)])
    return b


def project(p, fit_range=FIT, tune_season=TUNE):
    """Fit every model on fit_range, choose on tune_season; return projections for every eligible row
    (including games still to be played) and the choices."""
    e = eligible(p)
    done = e.played == 1
    fit, tune = e[done & e.season.between(*fit_range)], e[done & (e.season == tune_season)]
    # minutes model (shared by every market)
    mm = gbm(fit[MIN_FEATURES], fit['min'], tune[MIN_FEATURES], tune['min'], 'squared_error')
    e['min_hat'] = mm.predict(e[MIN_FEATURES])
    fit, tune = e[done & e.season.between(*fit_range)], e[done & (e.season == tune_season)]
    info = {'min_mae_model': float(np.abs(tune.min_hat - tune['min']).mean()),
            'min_mae_ew': float(np.abs(tune.min_ew - tune['min']).mean())}
    feats = PLAYER_FEATURES + ['min_hat']
    choice = {}
    for mk in PROPS:
        off_f, X_f = structural_design(fit, mk, fit.min_hat)
        b = poisson_glm(off_f.to_numpy(), X_f, fit[mk].to_numpy(float))
        off, X = structural_design(e, mk, e.min_hat)
        e[f'{mk}_struct'] = glm_predict(b, off.to_numpy(), X)
        dm = gbm(fit[feats], fit[mk], tune[feats], tune[mk], 'poisson')
        e[f'{mk}_direct'] = np.clip(dm.predict(e[feats]), 1e-3, None)
        e[f'{mk}_blend'] = (e[f'{mk}_struct'] + e[f'{mk}_direct']) / 2
        tu = e[done & (e.season == tune_season)]
        dev = {k: poisson_dev(tu[mk], tu[f'{mk}_{k}']) for k in ('struct', 'direct', 'blend')}
        pick = min(dev, key=dev.get)
        e[f'{mk}_hat'] = e[f'{mk}_{pick}']
        a = fit_dispersion(tu[mk], tu[f'{mk}_{pick}'])
        a0, k = fit_spread(tu[mk], tu[f'{mk}_{pick}'])
        choice[mk] = dict(pick=pick, dev=dev, a=a, a0=a0, k=k, min_sd=float(np.std(tu['min'] - tu.min_hat)), coef=dict(zip(['const'] + list(X_f.columns), np.round(b, 3))),
                          mae={k: float(np.abs(tu[mk] - tu[f'{mk}_{k}']).mean()) for k in ('struct', 'direct', 'blend')},
                          mae_l10=float(np.abs(tu[mk] - tu[f'{mk}_l10']).mean()))
    # points and PRA: simulation or negative binomial, whichever prices three lines around the projection better on
    # the tuning season (nbl/docs/RESEARCH.md: points 0.6709 to 0.6678, PRA 0.6791 to 0.6774 on 2022-23)
    tu = e[done & (e.season == tune_season)]
    for mk in SIMULATED:
        c, mu = choice[mk], tu[f'{mk}_hat'].to_numpy()
        lls = {}
        for shots in (False, True):
            c['shots'] = shots
            lls[shots] = np.mean([line_logloss(tu[mk], chance_over(mk, tu, mu, np.floor(mu) + off, c), np.floor(mu) + off)
                                  for off in (-1.5, 0.5, 2.5)])
        c['shots'] = lls[True] < lls[False]
        c['line_logloss'] = lls
    return e, choice, info


def run(cache, out_md):
    final = FINAL if os.environ.get('NBL_FINAL') == '1' else ()
    p = pd.read_parquet(f'{cache}/players.parquet')
    e, choice, info = project(p[p.played.notna()])
    e['rnd'] = round_id(e)
    (e if final else e[~e.season.isin(FINAL)]).to_parquet(f'{cache}/props_projections.parquet', index=False)
    tune = e[e.season == TUNE]
    L = []
    W = L.append
    W('# NBL player props, step 1: projections and a stand-in-line backtest')
    W('')
    W('**Every betting result below is against STAND-IN lines, not real ones.** No NBL prop lines are held yet '
      '(The Odds API key is not set up, and its NBL prop history may start only in September 2026). A stand-in line is '
      'the player\'s own recent average moved by one fixed amount, chosen on 2022-23 so a blind over wins half the '
      'time, at 1.87 each way. Books are said to set lines from recent averages, but they also see team news and '
      'some will price better, so these figures are an upper bound on a real edge, and may be far above it.')
    W('')
    W(f'Which games count: the player dressed and played (an unplayed prop is void), {MIN_GAMES}+ earlier games, and he '
      f'usually plays {MIN_MINUTES:.0f}+ minutes. Betting tables keep only lines a book would post: at least '
      + ', '.join(f'{NAMES[m]} {v}' for m, v in MIN_LINE.items()) + ' (this floor was set after looking at the confirm '
      'seasons and before the final check). Seasons are named by the year they start. Fit 2016-2021, tune 2022, '
      'confirm 2023 and 2024, final check 2025 and 2026 (2026 = this season to 18 Oct 2026).')
    W('')
    if final:
        W('**Honesty note.** The final-check seasons were scored once with the first version (21 Oct 2026). Since then '
          'per-stat memory and a spread that changes with the projection were adopted, both chosen on 2016-2022 and '
          'confirmed on 2023-2024 only (nbl/docs/RESEARCH.md); this is a second look at 2025-2026.')
        W('')
    W('## Projection accuracy')
    W('')
    W(f'Minutes, tuning season: our minutes model misses by {info["min_mae_model"]:.2f} minutes a game, the player\'s '
      f'decayed average by {info["min_mae_ew"]:.2f}.')
    W('')
    W('| market | model chosen on 2022 | miss per player-game, 2022: ours | last-10 average | spread a(mu) = a0 mu^k |')
    W('|---|---|---|---|---|')
    for mk in PROPS:
        c = choice[mk]
        W(f'| {NAMES[mk]} | {c["pick"]} | {c["mae"][c["pick"]]:.2f} | {c["mae_l10"]:.2f} | {c["a0"]:.3f} mu^{c["k"]:.2f} |')
    W('')
    W('| season | rows | ' + ' | '.join(f'{NAMES[m]}: ours / last 10' for m in PROPS) + ' |')
    W('|---|---|' + '---|' * len(PROPS))
    for s in CONFIRM + final:
        d = e[e.season == s]
        cells = [f'{np.abs(d[m] - d[f"{m}_hat"]).mean():.2f} / {np.abs(d[m] - d[f"{m}_l10"]).mean():.2f}' for m in PROPS]
        W(f'| {s} | {len(d)} | ' + ' | '.join(cells) + ' |')
    W('')

    W('## Is the over chance honest? (confirm seasons, against the last-10 stand-in)')
    W('')
    W('| market | our over chance | bets | over won |')
    W('|---|---|---|---|')
    shifts = {}
    for mk in PROPS:
        for col in ('l10', 'l5'):
            shifts[(mk, col)] = even_shift(tune[mk].to_numpy(), tune[f'{mk}_{col}'].to_numpy())
        d = e[e.season.isin(CONFIRM)].copy()
        d['line'] = stand_in_line(d[f'{mk}_l10'], shifts[(mk, 'l10')])
        d['po'] = chance_over(mk, d, d[f'{mk}_hat'], d.line, choice[mk])
        d['bin'] = pd.cut(d.po, [0, .3, .4, .5, .6, .7, 1])
        for bn, x in d.groupby('bin', observed=True):
            W(f'| {NAMES[mk]} | {bn.left:.0%} to {bn.right:.0%} | {len(x)} | {(x[mk] > x.line).mean():.0%} |')
    W('')

    W('## Betting against stand-in lines')
    W('')
    W(f'Bet a side when our chance of it is at least the stated figure; 1.87 breaks even at {1 / PRICE:.1%}. ROI per unit '
      'staked; the 90% interval comes from resampling whole rounds (weeks). Confirm seasons first, then the final check.')
    W('')
    W('| market | stand-in | seasons | bet at | bets | overs / unders | hit rate | ROI | 90% interval |')
    W('|---|---|---|---|---|---|---|---|---|')
    summary = []
    for mk in PROPS:
        for col in ('l10', 'l5'):
            for label, seasons in (('2023-2024', CONFIRM),) + ((('2025-2026', FINAL),) if final else ()):
                d = e[e.season.isin(seasons) & e[f'{mk}_{col}'].notna()].copy()
                d['line'] = stand_in_line(d[f'{mk}_{col}'], shifts[(mk, col)])
                d = marketable(d, mk)
                d['y'] = d[mk]
                d['p_over'] = chance_over(mk, d, d[f'{mk}_hat'], d.line, choice[mk])
                for thr in (0.56, 0.60):
                    b = bets(d, thr)
                    roi, lo, hi = roi_ci(b)
                    n_o, n_u = int((b.side == 'over').sum()), int((b.side == 'under').sum())
                    W(f'| {NAMES[mk]} | last {col[1:]} | {label} | {thr:.0%} | {len(b):,} | {n_o:,} / {n_u:,} | '
                      f'{b.win.mean():.1%} | {roi:+.1%} | {lo:+.1%} to {hi:+.1%} |')
                    summary.append(dict(market=mk, col=col, seasons=label, thr=thr, bets=len(b), roi=roi, lo=lo, hi=hi))
    W('')
    W('Blind check: with the shift chosen on 2022, how often the over won in each later season (50% means the stand-in is fair):')
    W('')
    W('| market | stand-in | ' + ' | '.join(str(s) for s in CONFIRM + final) + ' |')
    W('|---|---|' + '---|' * len(CONFIRM + final))
    for mk in PROPS:
        for col in ('l10', 'l5'):
            cells = []
            for s in CONFIRM + final:
                d = e[(e.season == s) & e[f'{mk}_{col}'].notna()]
                cells.append(f'{(d[mk] > stand_in_line(d[f"{mk}_{col}"], shifts[(mk, col)])).mean():.0%}')
            W(f'| {NAMES[mk]} | last {col[1:]} | ' + ' | '.join(cells) + ' |')
    W('')
    W('Shifts (chosen on 2022): ' + ', '.join(f'{NAMES[m]} last {c[1:]} {s:+.2f}' for (m, c), s in shifts.items()) + '.')
    W('')
    W('**Why the table above flatters us.** A line set at a rounded recent average and offered at 1.87 both ways is lopsided '
      'for small counts (a player averaging 1.4 threes faces a 1.5 line he clears well under half the time), and any '
      'distribution beats it. Real books shade the price on a lopsided line. The next table is the fairer test.')
    W('')
    W('## Betting against a naive stand-in book (the fairer test)')
    W('')
    W('Same stand-in lines, but the book prices both sides itself from the player\'s recent average alone (negative '
      'binomial around the average, its scale and spread fitted on 2022), with a 7% overround. This is a book that reads '
      'form the plain way. We bet a side when our chance times its price is at least 1 + the stated edge. A real book '
      'that also reads team news, minutes and matchups will be harder to beat than this one.')
    W('')
    W('| market | stand-in | seasons | edge at least | bets | overs / unders | hit rate | average price | ROI | 90% interval |')
    W('|---|---|---|---|---|---|---|---|---|---|')
    for mk in PROPS:
        for col in ('l10', 'l5'):
            # the naive book's scale and spread, fitted on the tuning season
            tu = tune[tune[f'{mk}_{col}'].notna()]
            k = float(tu[mk].mean() / tu[f'{mk}_{col}'].mean())
            a_n = fit_dispersion(tu[mk], (tu[f'{mk}_{col}'] * k).clip(0.05))
            for label, seasons in (('2023-2024', CONFIRM),) + ((('2025-2026', FINAL),) if final else ()):
                d = e[e.season.isin(seasons) & e[f'{mk}_{col}'].notna()].copy()
                d['line'] = stand_in_line(d[f'{mk}_{col}'], shifts[(mk, col)])
                d = marketable(d, mk)
                d['y'] = d[mk]
                d['p_over'] = chance_over(mk, d, d[f'{mk}_hat'], d.line, choice[mk])
                d['price_over'], d['price_under'] = naive_book(d, mk, col, k, a_n)
                for edge in (0.03, 0.08):
                    b = value_bets(d, edge)
                    roi, lo, hi = roi_ci(b)
                    n_o, n_u = int((b.side == 'over').sum()), int((b.side == 'under').sum())
                    W(f'| {NAMES[mk]} | last {col[1:]} | {label} | {edge:.0%} | {len(b):,} | {n_o:,} / {n_u:,} | '
                      f'{b.win.mean():.1%} | {b.price.mean():.2f} | {roi:+.1%} | {lo:+.1%} to {hi:+.1%} |')
                    summary.append(dict(book='naive', market=mk, col=col, seasons=label, thr=edge, bets=len(b), roi=roi, lo=lo, hi=hi))
    W('')
    W('## Where the edge comes from (naive book, last-10 stand-in, edge 3%)')
    W('')
    W('If shuffled projections also won, the test would be broken. If a plain projection (half the last-10 average, half '
      'the decayed per-minute rate x usual minutes) wins nearly as much, the edge is mostly "regress the recent average", '
      'which a real book may already do.')
    W('')
    W('| market | seasons | ours: bets, ROI | shuffled projections: bets, ROI | plain projection: bets, ROI |')
    W('|---|---|---|---|---|')
    rng = np.random.default_rng(1)
    for mk in PROPS:
        tu = tune[tune[f'{mk}_l10'].notna()]
        k = float(tu[mk].mean() / tu[f'{mk}_l10'].mean())
        a_n = fit_dispersion(tu[mk], (tu[f'{mk}_l10'] * k).clip(0.05))
        for label, seasons in (('2023-2024', CONFIRM),) + ((('2025-2026', FINAL),) if final else ()):
            d = e[e.season.isin(seasons) & e[f'{mk}_l10'].notna()].copy()
            d['line'] = stand_in_line(d[f'{mk}_l10'], shifts[(mk, 'l10')])
            d = marketable(d, mk)
            d['y'] = d[mk]
            d['price_over'], d['price_under'] = naive_book(d, mk, 'l10', k, a_n)
            rate = (d.r_pts + d.r_reb + d.r_ast) if mk == 'pra' else d[RATE[mk]]
            cells = []
            for mu in (d[f'{mk}_hat'].to_numpy(), rng.permutation(d[f'{mk}_hat'].to_numpy()),
                       (0.5 * d[f'{mk}_l10'] + 0.5 * d.min_ew * rate).to_numpy()):
                d['p_over'] = chance_over(mk, d, mu, d.line, choice[mk])
                b = value_bets(d, 0.03)
                cells.append(f'{len(b):,}, {roi_ci(b)[0]:+.1%}')
            W(f'| {NAMES[mk]} | {label} | ' + ' | '.join(cells) + ' |')
    W('')
    W('## By line size and side (naive book, last-10 stand-in, edge 3%, all seasons shown above)')
    W('')
    W('| market | line | side | bets | hit rate | ROI | 90% interval |')
    W('|---|---|---|---|---|---|---|')
    for mk in PROPS:
        tu = tune[tune[f'{mk}_l10'].notna()]
        k = float(tu[mk].mean() / tu[f'{mk}_l10'].mean())
        a_n = fit_dispersion(tu[mk], (tu[f'{mk}_l10'] * k).clip(0.05))
        d = e[e.season.isin(CONFIRM + final) & e[f'{mk}_l10'].notna()].copy()
        d['line'] = stand_in_line(d[f'{mk}_l10'], shifts[(mk, 'l10')])
        d = marketable(d, mk)
        d['y'] = d[mk]
        d['p_over'] = chance_over(mk, d, d[f'{mk}_hat'], d.line, choice[mk])
        d['price_over'], d['price_under'] = naive_book(d, mk, 'l10', k, a_n)
        b = value_bets(d, 0.03)
        cuts = np.unique(np.quantile(d.line, [0, 1 / 3, 2 / 3, 1]))
        b['band'] = pd.cut(b.line, cuts, include_lowest=True)
        for (band, side), x in b.groupby(['band', 'side'], observed=True):
            roi, lo, hi = roi_ci(x)
            W(f'| {NAMES[mk]} | {band.left:.1f} to {band.right:.1f} | {side} | {len(x):,} | {x.win.mean():.1%} | {roi:+.1%} | {lo:+.1%} to {hi:+.1%} |')
    W('')
    W('## What the structural model learned (Poisson, log scale, fitted 2016-2021)')
    W('')
    W('| market | ' + ' | '.join(next(iter(choice.values()))['coef'].keys()) + ' |')
    W('|---|' + '---|' * len(next(iter(choice.values()))['coef']))
    for mk in PROPS:
        W(f'| {NAMES[mk]} | ' + ' | '.join(f'{v:+.3f}' for v in choice[mk]['coef'].values()) + ' |')
    W('')
    W('log_opp: what the opponent has allowed lately against the league (1.0 = it passes straight through). '
      'log_pace: expected possessions against the league. blowout: expected margin size (per 10 points). '
      'min_out: usual minutes of teammates who dressed last game and not this one (per 30).')
    text = '\n'.join(L) + '\n'
    open(out_md, 'w').write(text)
    pd.DataFrame(summary).to_csv(f'{cache}/props_backtest_summary.csv', index=False)
    print(text)


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else 'nbl/cache', sys.argv[2] if len(sys.argv) > 2 else 'nbl/docs/PROPS_STEP1.md')
