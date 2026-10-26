"""Stage two of a Benter-style model: combine our probabilities with the market's, then size bets.

Benter (1994): a fundamental model alone is beaten by the public's odds; the edge comes from a second
stage that fits the result on BOTH, so the fitted weights say how much the model adds beyond the market.
For a match with outcomes i (home/draw/away, or over/under, or scorer yes/no):

    log P(i) = a x log p_model(i) + b x log p_market(i) - log Z

fitted by maximum likelihood on earlier seasons only (fit_by_season), so each season is priced with
weights it never saw. a near 0 means the model adds nothing the market does not already know.

  devig_power(prices)      fair probabilities from one book's prices: p_i = (1/o_i)^k, k solved so they sum
                           to 1 (handles the favourite-longshot bias better than plain normalising)
  devig_shin(prices)       Shin's method (Štrumbelj 2014: better than normalising on RPS)
  fit_blend(pm, pk, y)     (a, b)
  blend(pm, pk, a, b)      the combined probabilities
  stake(p, price, frac, min_edge)   fractional Kelly on one outcome, zero below the edge threshold
                           (Baker & McHale 2013: shrink stakes when p is itself an estimate)

Ready before odds exist; tested on synthetic data with known answers (aleague/tests/test_benter.py).
"""
import numpy as np
from scipy.optimize import brentq, minimize


def devig_power(prices):
    inv = 1 / np.asarray(prices, dtype=float)
    k = brentq(lambda k: (inv ** k).sum() - 1, 0.5, 3.0)
    return inv ** k


def devig_shin(prices):
    """Shin (1993) as solved by Jullien & Salanié: z is the insider share, found so the p sum to 1."""
    inv = 1 / np.asarray(prices, dtype=float)
    s = inv.sum()

    def probs(z):
        return (np.sqrt(z ** 2 + 4 * (1 - z) * inv ** 2 / s) - z) / (2 * (1 - z))
    z = brentq(lambda z: probs(z).sum() - 1, 0.0, 0.4)
    return probs(z)


def blend(pm, pk, a, b):
    """Rows of outcome probabilities: model pm, market pk (same shape)."""
    lg = a * np.log(np.clip(pm, 1e-12, 1)) + b * np.log(np.clip(pk, 1e-12, 1))
    lg -= lg.max(axis=1, keepdims=True)
    e = np.exp(lg)
    return e / e.sum(axis=1, keepdims=True)


def fit_blend(pm, pk, y):
    """(a, b) by maximum likelihood; y holds the index of the outcome that happened."""
    def nll(t):
        p = blend(pm, pk, t[0], t[1])
        return -np.log(np.clip(p[np.arange(len(y)), y], 1e-12, 1)).mean()
    return minimize(nll, np.array([0.3, 0.7]), method='Nelder-Mead').x


def fit_by_season(seasons, pm, pk, y, min_rows=150):
    """Blended probabilities for each season from weights fitted on earlier seasons only; NaN where
    there is not yet enough history. Returns (probabilities, {season: (a, b)})."""
    seasons = np.asarray(seasons)
    out = np.full(pm.shape, np.nan)
    weights = {}
    for s in sorted(set(seasons)):
        past = seasons < s
        if past.sum() < min_rows:
            continue
        a, b = fit_blend(pm[past], pk[past], y[past])
        weights[s] = (a, b)
        k = seasons == s
        out[k] = blend(pm[k], pk[k], a, b)
    return out, weights


def stake(p, price, frac=0.25, min_edge=0.03):
    """Fraction of bank on one outcome: frac x Kelly, only when p x price - 1 >= min_edge."""
    edge = p * price - 1
    if edge < min_edge:
        return 0.0
    return frac * edge / (price - 1)
