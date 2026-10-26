"""Benter's second stage: blend our probability with the market's, weights fitted out of sample.

Benter (1994, Hong Kong racing): a fundamental model gives p_model; the public's odds, with the margin taken
out, give p_market; the final chance is

    p ∝ exp(alpha * log p_model + beta * log p_market)          (normalised over the outcomes of one event)

with alpha and beta fitted by maximum likelihood on events the fit has not seen. The market carries what no
model has (late news, money that knows something), so the blend beats both; alpha says how much our model
adds. A bet is only considered when the blended chance times the price beats 1 by the chosen edge, staked at a
fraction of Kelly because the edge is itself an estimate. Same idea as the racing model's stage 2
(research/form_gbm on main), here in its original two-coefficient form.

Everything here waits on real prices: the coefficients are fitted walk-forward by season once The Odds API's
history is pulled (bbl/lines/probe.py). Tested on made-up markets in tests/test_benter.py.
"""
import numpy as np
from scipy import optimize


def devig(prices, method='power'):
    """Bookmaker decimal prices for one event's outcomes -> probabilities that sum to 1.

    'proportional' divides each implied chance by the overround; 'power' finds k with sum((1/price)^k) = 1, which
    takes more margin off longshots (the usual favourite-longshot shape) and is the better default.
    """
    q = 1 / np.asarray(prices, float)
    if method == 'proportional':
        return q / q.sum()
    k = optimize.brentq(lambda k: (q ** k).sum() - 1, 0.5, 3.0)
    return q ** k


def blend(p_model, p_market, alpha, beta):
    """One event, any number of outcomes: Benter's blended probabilities."""
    z = alpha * np.log(np.clip(p_model, 1e-9, 1)) + beta * np.log(np.clip(p_market, 1e-9, 1))
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()


def fit(events):
    """Maximum likelihood (alpha, beta) over events: each a (p_model array, p_market array, index of the winner)."""
    def nll(w):
        return -sum(np.log(blend(pm, pk, w[0], w[1])[y]) for pm, pk, y in events)
    res = optimize.minimize(nll, x0=[0.5, 0.5], method='L-BFGS-B', bounds=[(-2, 4), (-2, 4)])
    return float(res.x[0]), float(res.x[1]), float(res.fun / max(len(events), 1))


def log_loss(events, alpha=None, beta=None, which='blend'):
    out = []
    for pm, pk, y in events:
        p = pm if which == 'model' else pk if which == 'market' else blend(pm, pk, alpha, beta)
        out.append(-np.log(max(p[y], 1e-9)))
    return float(np.mean(out))


def walk_forward(events_by_season):
    """{season: [events]} in time order -> per season: (alpha, beta) fitted on every earlier season, and log losses."""
    seasons = sorted(events_by_season)
    rows = []
    for k, s in enumerate(seasons):
        past = [e for t in seasons[:k] for e in events_by_season[t]]
        if not past:
            continue
        a, b, _ = fit(past)
        ev = events_by_season[s]
        rows.append(dict(season=s, alpha=a, beta=b, games=len(ev), ll_market=log_loss(ev, which='market'),
                         ll_model=log_loss(ev, which='model'), ll_blend=log_loss(ev, a, b)))
    return rows


def kelly(p, price, fraction=0.25):
    """Fractional Kelly stake as a share of the bank for a back bet at decimal price; 0 when there is no edge."""
    b = price - 1
    f = (p * b - (1 - p)) / b
    return max(0.0, f) * fraction
