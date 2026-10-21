"""NBL team model: margin and total per game from pre-game information, priced into head-to-head, line
and total.

Two predictions per game:
  open   what was knowable when books open: last game's squad, no team news
  named  the squad that dressed for this game
The gap between them is the value of team news; once real lines are recorded the test is whether
"named" beats the opening line by more than the market moved.

Inputs (nbl/model/frame.py, all pre-game): results-only rating (Elo), decayed offensive and defensive
efficiency and pace, squad value above average (open or named), rest, back-to-backs, travel, finals.
Ridge regression. The penalty is chosen by predicting each of 2018-19 to 2022-23 from the seasons before it;
then fitted on 2016-17 to 2022-23 and scored once on seasons it never saw: confirm 2023-24 and 2024-25,
final check 2025-26 and 2026-27 so far.
2015-16 is a warm-up season (histories start empty) and is not fitted.

Win chance = normal around the predicted margin; line = the same normal; total = normal around the
predicted total. Spreads fitted on the training seasons.

Usage: python -m nbl.model.team nbl/cache nbl/docs/TEAM_STEP1.md
"""
import sys

import numpy as np
import pandas as pd
from scipy import stats

FIT, CV_FROM, CONFIRM, FINAL = (2016, 2022), 2018, (2023, 2024), (2025, 2026)
TESTS = CONFIRM + FINAL


def games_table(tg):
    """One row per game, home minus away for every team feature."""
    tg = tg.copy()
    tg['net_ew'] = tg.ortg_ew - tg.drtg_ew
    side = ['game', 'season', 'tip', 'finals', 'venue', 'team', 'score', 'poss_ew', 'ortg_ew', 'drtg_ew', 'net_ew', 'margin_ew',
            'days_rest', 'b2b', 'travel_km', 'named_val', 'open_val', 'games_prior', 'elo_margin', 'league_poss', 'league_pts', 'ot']
    h = tg[tg.is_home == 1][side]
    a = tg[tg.is_home == 0][side]
    g = h.merge(a[['game', 'team', 'score', 'poss_ew', 'ortg_ew', 'drtg_ew', 'net_ew', 'margin_ew', 'days_rest', 'b2b', 'travel_km',
                   'named_val', 'open_val', 'games_prior']], on='game', suffixes=('_h', '_a'))
    g = g.rename(columns={'team_h': 'home', 'team_a': 'away'})
    g['home_margin'] = g.score_h - g.score_a
    g['total'] = g.score_h + g.score_a
    for c in ['net_ew', 'margin_ew', 'days_rest', 'b2b', 'travel_km', 'named_val', 'open_val']:
        g[f'd_{c}'] = g[f'{c}_h'] - g[f'{c}_a']
    g['news'] = g.d_named_val - g.d_open_val
    # expected total: both teams' scoring per 100 against the other's defence, at their combined pace
    g['exp_poss'] = (g.poss_ew_h + g.poss_ew_a) / 2
    g['exp_total'] = g.exp_poss * ((g.ortg_ew_h + g.drtg_ew_a) / 2 + (g.ortg_ew_a + g.drtg_ew_h) / 2) / 100
    g['sum_val_named'] = g.named_val_h + g.named_val_a
    g['sum_val_open'] = g.open_val_h + g.open_val_a
    return g.sort_values('tip').reset_index(drop=True)


MARGIN = {
    'elo': ['elo_margin'],
    'open': ['elo_margin', 'd_net_ew', 'd_margin_ew', 'd_open_val', 'd_days_rest', 'd_b2b', 'd_travel_km'],
    'named': ['elo_margin', 'd_net_ew', 'd_margin_ew', 'd_named_val', 'd_days_rest', 'd_b2b', 'd_travel_km'],
}
TOTAL = {
    'open': ['exp_total', 'exp_poss', 'league_pts', 'sum_val_open', 'finals'],
    'named': ['exp_total', 'exp_poss', 'league_pts', 'sum_val_named', 'finals'],
}


class Ridge:
    """Ridge with standardised inputs and missing values filled from the fitting data."""

    def __init__(self, cols, lam):
        self.cols, self.lam = cols, lam

    def fit(self, d, y):
        X = d[self.cols].astype(float)
        self.fill = X.mean()
        X = X.fillna(self.fill)
        self.mu, self.sd = X.mean(), X.std().replace(0, 1)
        Z = ((X - self.mu) / self.sd).to_numpy()
        Zc = np.column_stack([np.ones(len(Z)), Z])
        I = np.eye(Zc.shape[1]); I[0, 0] = 0
        self.b = np.linalg.solve(Zc.T @ Zc + self.lam * I, Zc.T @ np.asarray(y, float))
        return self

    def predict(self, d):
        Z = ((d[self.cols].astype(float).fillna(self.fill) - self.mu) / self.sd).to_numpy()
        return np.column_stack([np.ones(len(Z)), Z]) @ self.b

    def coefs(self):
        return dict(zip(['intercept'] + self.cols, np.round(self.b, 2)))


def choose(dev, cols, target):
    """Penalty with the lowest miss when each season from CV_FROM is predicted from the seasons before it."""
    best = None
    for lam in (0.1, 1, 10, 30, 100, 300, 1000):
        errs = []
        for s in range(CV_FROM, FIT[1] + 1):
            tr, te = dev[dev.season < s], dev[dev.season == s]
            errs.append(np.abs(Ridge(cols, lam).fit(tr, tr[target]).predict(te) - te[target]))
        mae = np.concatenate(errs).mean()
        if best is None or mae < best[0]:
            best = (mae, lam)
    return Ridge(cols, best[1]).fit(dev, dev[target])


def fitted(g):
    """Fit every model on FIT with the penalty chosen by rolling-origin validation; return models and spreads."""
    fit = g[g.season.between(*FIT)]
    models = {f'm_{k}': choose(fit, c, 'home_margin') for k, c in MARGIN.items()}
    models.update({f't_{k}': choose(fit, c, 'total') for k, c in TOTAL.items()})
    sd_m = float(np.std(fit.home_margin - models['m_named'].predict(fit)))
    sd_t = float(np.std(fit.total - models['t_named'].predict(fit)))
    return models, sd_m, sd_t, fit


def price(margin_hat, total_hat, sd_m, sd_t, line=None, total_line=None):
    """Our probabilities and fair prices for one game, from the home side."""
    p_home = stats.norm.cdf(margin_hat / sd_m)
    out = dict(p_home=p_home, fair_home=1 / p_home, fair_away=1 / (1 - p_home))
    if line is not None:          # home line, e.g. -4.5: home covers when margin + line > 0
        p = stats.norm.cdf((margin_hat + line) / sd_m)
        out.update(p_home_cover=p, fair_home_line=1 / p, fair_away_line=1 / (1 - p))
    if total_line is not None:
        p = 1 - stats.norm.cdf((total_line - total_hat) / sd_t)
        out.update(p_over=p, fair_over=1 / p, fair_under=1 / (1 - p))
    return out


def sn(season):
    return f'{season}-{(season + 1) % 100:02d}'


def logloss(p, y):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def run(cache, out_md):
    tg = pd.read_parquet(f'{cache}/teams.parquet')
    g = games_table(tg)
    g = g[(g.games_prior_h >= 1) & (g.games_prior_a >= 1)]
    models, sd_m, sd_t, fit = fitted(g)
    rows, preds = [], []
    for season in TESTS:
        te = g[g.season == season].copy()
        y = (te.home_margin > 0).astype(float)
        for k in MARGIN:
            te[f'm_{k}'] = models[f'm_{k}'].predict(te)
            te[f'p_{k}'] = stats.norm.cdf(te[f'm_{k}'] / sd_m)
        for k in TOTAL:
            te[f't_{k}'] = models[f't_{k}'].predict(te)
        base_home = (fit.home_margin > 0).mean()
        rows.append(dict(season=season, model='home team, at the training home-win rate', games=len(te),
                         tips=(y == 1).mean(), mae=np.abs(fit.home_margin.mean() - te.home_margin).mean(),
                         brier=np.mean((base_home - y) ** 2), ll=logloss(np.full(len(te), base_home), y)))
        for k, lab in (('elo', 'results-only rating (Elo)'), ('open', 'ours, at the open (no team news)'), ('named', 'ours, squads named')):
            rows.append(dict(season=season, model=lab, games=len(te), tips=((te[f'm_{k}'] > 0) == (y == 1)).mean(),
                             mae=np.abs(te[f'm_{k}'] - te.home_margin).mean(), brier=np.mean((te[f'p_{k}'] - y) ** 2),
                             ll=logloss(te[f'p_{k}'].to_numpy(), y.to_numpy())))
        preds.append(te)
    r = pd.DataFrame(rows)
    allte = pd.concat(preds)
    allte.to_parquet(f'{cache}/team_test_predictions.parquet', index=False)

    L = []
    W = L.append
    W('# NBL team model, step 1: margin and total')
    W('')
    W(f'Fitted on {sn(FIT[0])} to {sn(FIT[1])} ({len(fit)} games); the penalty was chosen by predicting each season from '
      f'{sn(CV_FROM)} on from the seasons before it. Each later season is scored once. 2026-27 is this season to 18 Oct 2026, 36 games. No public NBL model with an archive of '
      'predictions was found to compare against, and no betting lines are held yet, so the benchmarks are '
      'a results-only rating and always picking the home team. **The test that matters, against the market, waits for recorded lines.**')
    W('')
    W('**Honesty note.** The final-check seasons (2025-26, 2026-27) were scored once with a first version of this model '
      '(Elo K 0.06, penalty chosen on 2022-23 alone). The Elo settings and the penalty method were then changed, both '
      'chosen on 2016-17 to 2022-23 only, and everything was scored again. It is a second look, not a clean one; '
      'the first version was no better on those seasons.')
    W('')
    W(f'Win chance = normal around the predicted margin, spread {sd_m:.1f} points; total spread {sd_t:.1f} points (training seasons).')
    W('')
    for season in TESTS:
        t = r[r.season == season].sort_values('ll')
        tag = 'final check' if season in FINAL else 'confirmation season'
        W(f'## {sn(season)} ({tag})')
        W('')
        W('| model | games | winner picked | margin miss (pts) | Brier | log loss |')
        W('|---|---|---|---|---|---|')
        for x in t.itertuples():
            W(f'| {x.model} | {x.games} | {x.tips:.1%} | {x.mae:.1f} | {x.brier:.3f} | {x.ll:.3f} |')
        W('')
    W('Lower is better for margin miss, Brier and log loss. A coin flip scores Brier 0.250 and log loss 0.693.')
    W('')

    W('## Is the win chance honest? (all test seasons, squads named)')
    W('')
    W('| our home win chance | games | home won |')
    W('|---|---|---|')
    allte['bin'] = pd.cut(allte.p_named, [0, .2, .35, .5, .65, .8, 1])
    for b, x in allte.groupby('bin', observed=True):
        W(f'| {b.left:.0%} to {b.right:.0%} | {len(x)} | {(x.home_margin > 0).mean():.0%} |')
    W('')

    W('## Team news: how much the named squad moves the prediction (all test seasons)')
    W('')
    W('| change in our margin, open to named | games | open margin miss | named margin miss |')
    W('|---|---|---|---|')
    allte['move'] = (allte.m_named - allte.m_open).abs()
    for lo, hi in ((0, 1), (1, 2), (2, 4), (4, 100)):
        x = allte[(allte.move >= lo) & (allte.move < hi)]
        if len(x):
            W(f'| {lo} to {hi if hi < 100 else "more"} pts | {len(x)} | {(x.m_open - x.home_margin).abs().mean():.1f} | '
              f'{(x.m_named - x.home_margin).abs().mean():.1f} |')
    W('')

    W('## Totals')
    W('')
    W('| season | games | total miss, ours named (pts) | ours open | always the training average |')
    W('|---|---|---|---|---|')
    for season, te in allte.groupby('season'):
        W(f'| {sn(season)} | {len(te)} | {(te.t_named - te.total).abs().mean():.1f} | '
          f'{(te.t_open - te.total).abs().mean():.1f} | {(fit.total.mean() - te.total).abs().mean():.1f} |')
    W('')
    W('Scores include overtime, as head-to-head, line and total bets settle.')
    W('')
    W('## What the margin model leans on (named; standardised, points per standard deviation)')
    W('')
    for k, v in models['m_named'].coefs().items():
        W(f'- {k}: {v:+.2f}')
    W('')
    W(f'Penalties chosen: ' + ', '.join(f'{k} {m.lam}' for k, m in models.items()) + '.')
    text = '\n'.join(L) + '\n'
    open(out_md, 'w').write(text)
    print(text)


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else 'nbl/cache', sys.argv[2] if len(sys.argv) > 2 else 'nbl/docs/TEAM_STEP1.md')
