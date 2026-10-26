"""The market's chance, and our chance combined with it (Benter's second stage).

Benter's finding in racing: his fundamental model alone did not beat the public's odds, but the two combined in a
logit did, and the combination is what he bet on. The racing model here does the same (research/form_gbm/t_benter.py;
live stakes on a 50/50 blend of our chance and the market's). This is the NBL version.

  fair_chances   strip a book's margin from a two-way market (over/under, home/away): proportional by default, or
                 the power method (shades favourites less, longshots more, as books do)
  combine        logit(p) = w_ours * logit(our chance) + w_market * logit(market chance) + bias
                 Until enough recorded results exist (MIN_RESULTS), the weights are the racing rule: half each, no bias.
  fit_combination  maximum likelihood for the three numbers on recorded results (our chance, market chance, outcome),
                 once there are enough of them; refit as the season goes on

Paper only. Nothing here places a bet.
"""
import numpy as np
from scipy import optimize

MIN_RESULTS = 400          # recorded results needed before the weights are fitted instead of assumed
DEFAULT = dict(w_ours=0.5, w_market=0.5, bias=0.0)


def _logit(p):
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def _expit(x):
    return 1 / (1 + np.exp(-np.asarray(x, float)))


def fair_chances(price_a, price_b, method='proportional'):
    """Chances of the two sides of a market with the book's margin removed. Prices are decimal odds."""
    qa, qb = 1 / np.asarray(price_a, float), 1 / np.asarray(price_b, float)
    if method == 'proportional':
        return qa / (qa + qb), qb / (qa + qb)
    if method == 'power':
        # find k with qa^k + qb^k = 1 for each market (k > 1 when there is a margin)
        def one(a, b):
            f = lambda k: a ** k + b ** k - 1
            k = optimize.brentq(f, 0.5, 5.0) if f(0.5) * f(5.0) < 0 else 1.0
            return a ** k, b ** k
        out = np.array([one(a, b) for a, b in zip(np.atleast_1d(qa), np.atleast_1d(qb))])
        return out[:, 0], out[:, 1]
    raise ValueError(method)


def combine(p_ours, p_market, w=None):
    """Combined chance: logit(p) = w_ours logit(ours) + w_market logit(market) + bias."""
    w = w or DEFAULT
    return _expit(w['w_ours'] * _logit(p_ours) + w['w_market'] * _logit(p_market) + w['bias'])


def fit_combination(p_ours, p_market, won, min_results=MIN_RESULTS):
    """Weights by maximum likelihood on recorded results. Returns DEFAULT (and says so) below min_results."""
    p_ours, p_market, won = (np.asarray(x, float) for x in (p_ours, p_market, won))
    ok = np.isfinite(p_ours) & np.isfinite(p_market) & np.isfinite(won)
    if ok.sum() < min_results:
        return dict(DEFAULT, fitted=False, n=int(ok.sum()))
    X = np.column_stack([_logit(p_ours[ok]), _logit(p_market[ok]), np.ones(ok.sum())])
    y = won[ok]

    def nll(b):
        z = X @ b
        return np.sum(np.logaddexp(0, z) - y * z)

    b = optimize.minimize(nll, [0.5, 0.5, 0.0], method='BFGS').x
    return dict(w_ours=float(b[0]), w_market=float(b[1]), bias=float(b[2]), fitted=True, n=int(ok.sum()))
