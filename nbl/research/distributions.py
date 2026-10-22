"""Experiment: the shape of each prop's distribution. Same projections (mean), different spreads:
  nb          negative binomial, one spread per market (current)
  nb_by_mu    negative binomial, spread a(mu) = a0 * mu^k, fitted on 2022-23
  shots       points only: two-point, three-point and free-throw attempts drawn from the player's rates and
              minutes, makes from his shrunk percentages, rescaled to the same mean; 4,000 draws a row
Scores: log score of the outcome, and binary log loss of over/under at three .5 lines around the projection
(what a bet actually needs). Usage: python -m nbl.research.distributions nbl/cache"""
import sys

import numpy as np
import pandas as pd
from scipy import optimize, stats

from nbl.model import props

SEASONS = {'tune 2022': [2022], 'confirm 2023-24': [2023, 2024]}
DRAWS = 4000


def nb_cdf(x, mu, a):
    n = 1 / a
    return stats.nbinom.cdf(x, n, n / (n + mu))


def nb_logpmf(y, mu, a):
    n = 1 / a
    return stats.nbinom.logpmf(y, n, n / (n + mu))


def fit_a_mu(y, mu):
    def nll(t):
        a = np.exp(t[0]) * mu ** t[1]
        return -np.sum(nb_logpmf(y, mu, np.clip(a, 1e-4, 50)))
    t = optimize.minimize(nll, [np.log(0.2), 0.0], method='Nelder-Mead').x
    return t


def shots_sample(d, mu, min_sd, rng):
    """Draws of points per row: minutes ~ normal(min_hat, min_sd) floored at 1, attempts Poisson, makes binomial."""
    n = len(d)
    m = np.clip(rng.normal(d.min_hat.to_numpy()[:, None], min_sd, (n, DRAWS)), 1, 48)
    fga, fg3a, fta = d.r_fga.to_numpy()[:, None], d.r_fg3a.to_numpy()[:, None], d.r_fta.to_numpy()[:, None]
    fga2 = np.clip(fga - fg3a, 1e-4, None)
    pct3 = np.clip(d.r_fg3m / d.r_fg3a.clip(1e-4), 0.05, 0.7).to_numpy()[:, None]
    pct_fg = np.clip(d.r_fgm / d.r_fga.clip(1e-4), 0.2, 0.8).to_numpy()[:, None]
    fgm3 = (pct3 * fg3a)
    pct2 = np.clip((pct_fg * fga - fgm3) / fga2, 0.2, 0.85)
    pctft = np.clip(d.r_ftm / d.r_fta.clip(1e-4), 0.3, 0.98).to_numpy()[:, None]
    a2 = rng.poisson(fga2 * m); a3 = rng.poisson(fg3a * m); trips = rng.poisson(fta * m / 2)
    pts = 2 * rng.binomial(a2, pct2) + 3 * rng.binomial(a3, pct3) + rng.binomial(2 * trips, pctft)
    # rescale to the projection's mean (the model owns the mean, the draws own the shape)
    scale = mu / np.clip(pts.mean(1), 0.1, None)
    return np.rint(pts * scale[:, None]).astype(int)


def main(cache):
    p = pd.read_parquet(f'{cache}/players.parquet')
    p = p[p.played.notna() & (p.season <= 2024)]
    e, choice, info = props.project(p)
    rng = np.random.default_rng(3)
    tune = e[e.season == 2022]
    min_sd = float(np.std(tune['min'] - tune.min_hat))
    rows = []
    for mk in props.PROPS:
        t = fit_a_mu(tune[mk].to_numpy(), tune[f'{mk}_hat'].to_numpy())
        for name, ss in SEASONS.items():
            d = e[e.season.isin(ss)]
            y, mu = d[mk].to_numpy(), d[f'{mk}_hat'].to_numpy()
            lines = [np.floor(mu) + off for off in (-1.5, 0.5, 2.5)]
            variants = {'nb': np.full(len(d), choice[mk]['a']), 'nb_by_mu': np.clip(np.exp(t[0]) * mu ** t[1], 1e-4, 50)}
            for v, a in variants.items():
                ll = [np.where(y > L, -np.log(np.clip(1 - nb_cdf(np.floor(L), mu, a), 1e-9, 1)),
                               -np.log(np.clip(nb_cdf(np.floor(L), mu, a), 1e-9, 1))) for L in lines if True]
                rows.append(dict(market=mk, seasons=name, dist=v, logscore=float(np.mean(nb_logpmf(y, mu, a))),
                                 line_logloss=float(np.mean([x[(L > 0)].mean() for x, L in zip(ll, lines)]))))
            if mk == 'pts':
                s = shots_sample(d, mu, min_sd, rng)
                pmf_y = (s == y[:, None]).mean(1)
                ll = []
                for L in lines:
                    po = np.clip((s > L[:, None]).mean(1), 1e-4, 1 - 1e-4)
                    ll.append(np.where(y > L, -np.log(po), -np.log(1 - po))[L > 0].mean())
                rows.append(dict(market=mk, seasons=name, dist='shots', logscore=float(np.mean(np.log(np.clip(pmf_y, 1e-4, 1)))),
                                 line_logloss=float(np.mean(ll))))
        print(mk, 'spread by mu: a0', round(float(np.exp(t[0])), 3), 'k', round(float(t[1]), 3), flush=True)
    r = pd.DataFrame(rows)
    print(r.pivot_table(index=['market', 'seasons'], columns='dist', values=['logscore', 'line_logloss']).round(4).to_string())


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'nbl/cache')
