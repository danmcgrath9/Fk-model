"""Experiment: DARKO-style Kalman filter for each per-minute rate, against the adopted per-stat decay.

Local level model per player and stat: true rate x drifts by variance Q per game (Q_OFF extra across a
season break); each game observes stat/minutes with variance S x league rate / minutes (count noise shrinks
with minutes). Start at the league rate with variance P0. Score as rate_memory.py: squared error of
predicted rate x actual minutes against the stat, choices on 2016-22, confirm 2023-24.
Usage: python -m nbl.research.kalman_rates nbl/cache"""
import itertools
import sys

import numpy as np
import pandas as pd

from nbl.model.frame import RATE_MEMORY, league_rates
from nbl.research.rate_memory import rates as rates_decay


def rates_kalman(p, stat, q, q_off, p0, s_noise, lr):
    out = np.full(len(p), np.nan)
    keys = p.key.to_numpy(); order = np.argsort(keys, kind='stable')
    k = keys[order]; starts = np.r_[0, np.flatnonzero(k[1:] != k[:-1]) + 1, len(k)]
    st, mn, pl, se = p[stat].to_numpy(float), p['min'].to_numpy(float), p.played.to_numpy(float), p.season.to_numpy()
    for a, b in zip(starts[:-1], starts[1:]):
        x = P = None; last_season = None
        for i in order[a:b]:
            league = lr[se[i]][stat]
            if x is None:
                x, P = league, p0 * league ** 2
            elif se[i] != last_season:
                P += q_off * league ** 2
            last_season = se[i]
            out[i] = x
            if pl[i] == 1 and mn[i] > 0:
                P += q * league ** 2
                R = s_noise * max(league, 1e-3) / mn[i]
                K = P / (P + R)
                x = x + K * (st[i] / mn[i] - x)
                P = (1 - K) * P
    return out


def main(cache):
    p = pd.read_parquet(f'{cache}/players.parquet')
    p = p[p.played.notna() & (p.season <= 2024)].sort_values(['tip', 'game']).reset_index(drop=True)
    lr = league_rates(p)
    ev = (p.played == 1) & (p.games_prior >= 5) & (p.min_ew >= 12)
    dev, conf = ev & p.season.between(2016, 2022), ev & p.season.between(2023, 2024)
    rows = []
    for stat in ['pts', 'reb', 'ast', 'fg3m', 'fg3a', 'fga', 'fta', 'tov']:
        d, pr = RATE_MEMORY[stat]
        e0 = (rates_decay(p, stat, d, pr, lr) * p['min'] - p[stat]) ** 2
        best = None
        for q, qo, p0, sn in itertools.product([0.0005, 0.002, 0.008], [0.0, 0.02, 0.08], [0.1, 0.4], [0.5, 1.0, 2.0]):
            e = (rates_kalman(p, stat, q, qo, p0, sn, lr) * p['min'] - p[stat]) ** 2
            if best is None or e[dev].mean() < best[0]:
                best = (e[dev].mean(), e[conf].mean(), (q, qo, p0, sn))
        rows.append(dict(stat=stat, kalman=best[2], dev_kalman=best[0], dev_decay=e0[dev].mean(),
                         conf_kalman=best[1], conf_decay=e0[conf].mean()))
        print(rows[-1], flush=True)
    r = pd.DataFrame(rows)
    r['conf_gain_%'] = 100 * (1 - r.conf_kalman / r.conf_decay)
    print(r.round(4).to_string(index=False))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'nbl/cache')
