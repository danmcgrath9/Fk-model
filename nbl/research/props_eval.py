"""Yardstick for props experiments: log score (mean log chance of what happened, higher is better) and
mean miss, per market, on 2022-23 (where choices are made) and 2023-24 to 2024-25 (confirm).
2025-26 and later are not used. Usage: from nbl.research.props_eval import evaluate"""
import numpy as np
import pandas as pd
from scipy import stats

from nbl.model import props

SEASONS = {'tune 2022': [2022], 'confirm 2023-24': [2023, 2024]}


def nb_logscore(y, mu, a):
    n = 1 / a
    return stats.nbinom.logpmf(np.asarray(y, int), n, n / (n + np.asarray(mu, float)))


def evaluate(p, label, dist=None):
    """p: players frame. dist(mk, d, mu, a) -> log chance per row (default: negative binomial)."""
    p = p[p.played.notna() & (p.season <= 2024)]
    e, choice, info = props.project(p)
    rows = []
    for mk in props.PROPS:
        for name, ss in SEASONS.items():
            d = e[e.season.isin(ss)]
            mu, a = d[f'{mk}_hat'].to_numpy(), choice[mk]['a']
            ls = dist(mk, d, mu, a) if dist else nb_logscore(d[mk], mu, a)
            rows.append(dict(exp=label, market=mk, seasons=name, rows=len(d), logscore=float(np.mean(ls)),
                             mae=float(np.abs(d[mk] - mu).mean())))
    r = pd.DataFrame(rows)
    r.attrs['info'] = info
    return r, e, choice
