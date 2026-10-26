"""Stage 2 (Benter 1994; the racing model's research/form_gbm/blend_open.py): blend our price with the market's.

For a two-way market (h2h, line, total, anytime try scorer "yes"):
    logit(p) = a * logit(p_ours) + b * logit(p_market) + c
fitted by maximum likelihood on results in older seasons, checked on newer ones. p_market is the book's price with
its margin removed (proportionally across both sides). Benter's finding, and the racing model's (KL to BSP 0.0801 ->
0.0765), is that the blend beats either price alone: the market knows things the model does not, and the model
knows things the market under-weights. The blended p is what is compared with a book's price before any bet.

Needs real odds, so nothing here runs on the backtest yet; the synthetic test proves the fit recovers known weights.
"""
import numpy as np
from scipy.optimize import minimize


def logit(p):
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def devig_two_way(price_a, price_b):
    """Fair probability of side A from two decimal prices, margin removed proportionally."""
    ia, ib = 1 / np.asarray(price_a, float), 1 / np.asarray(price_b, float)
    return ia / (ia + ib)


class Blend:
    def fit(self, p_ours, p_market, y, l2=1e-3):
        X = np.column_stack([logit(p_ours), logit(p_market), np.ones(len(y))])
        y = np.asarray(y, float)

        def nll(w):
            z = X @ w
            return np.sum(np.logaddexp(0, z) - y * z) / len(y) + l2 * np.sum(w[:2] ** 2)
        r = minimize(nll, np.array([0.5, 0.5, 0.0]), method='BFGS')
        self.a, self.b, self.c = r.x
        return self

    def predict(self, p_ours, p_market):
        z = self.a * logit(p_ours) + self.b * logit(p_market) + self.c
        return 1 / (1 + np.exp(-z))
