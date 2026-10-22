"""Experiment: decay by days elapsed (DARKO) instead of by games played, so the off-season counts.
Same score as rate_memory.py. Usage: python -m nbl.research.rate_memory_days nbl/cache"""
import itertools
import sys

import numpy as np
import pandas as pd

from nbl.model.frame import league_rates
from nbl.research.rate_memory import rates as rates_games

DAY_DECAYS = [0.990, 0.993, 0.995, 0.997, 0.998]
PRIORS = [15, 30, 60, 120]


def rates_days(p, stat, decay, prior, lr):
    out = np.full(len(p), np.nan)
    keys = p.key.to_numpy(); order = np.argsort(keys, kind='stable')
    k = keys[order]; starts = np.r_[0, np.flatnonzero(k[1:] != k[:-1]) + 1, len(k)]
    st, mn, pl, se = p[stat].to_numpy(float), p['min'].to_numpy(float), p.played.to_numpy(float), p.season.to_numpy()
    day = p.day.to_numpy('datetime64[D]').astype(np.int64)
    for a, b in zip(starts[:-1], starts[1:]):
        s_st = s_m = 0.0; last = None
        for i in order[a:b]:
            if last is not None:
                f = decay ** (day[i] - last)
                s_st *= f; s_m *= f
            last = day[i]
            league = lr[se[i]][stat]
            out[i] = (s_st + prior * league) / (s_m + prior)
            if pl[i] == 1:
                s_st += st[i]; s_m += mn[i]
    return out


def main(cache):
    p = pd.read_parquet(f'{cache}/players.parquet')
    p = p[p.played.notna() & (p.season <= 2024)].sort_values(['tip', 'game']).reset_index(drop=True)
    lr = league_rates(p)
    ev = (p.played == 1) & (p.games_prior >= 5) & (p.min_ew >= 12)
    dev, conf = ev & p.season.between(2016, 2022), ev & p.season.between(2023, 2024)
    games_best = pd.read_csv(f'{cache}/research_rate_memory.csv').set_index('stat')
    rows = []
    for stat in ['pts', 'reb', 'ast', 'fg3m', 'fg3a', 'fga', 'fta', 'tov', 'stl', 'blk', 'eff']:
        g = games_best.loc[stat]
        rg = rates_games(p, stat, g.decay, g.prior_min, lr)
        eg = (rg * p['min'] - p[stat]) ** 2
        best = None
        for d, pr in itertools.product(DAY_DECAYS, PRIORS):
            e = (rates_days(p, stat, d, pr, lr) * p['min'] - p[stat]) ** 2
            if best is None or e[dev].mean() < best[0]:
                best = (e[dev].mean(), e[conf].mean(), d, pr)
        rows.append(dict(stat=stat, day_decay=best[2], prior=best[3], dev_days=best[0], dev_games=eg[dev].mean(),
                         conf_days=best[1], conf_games=eg[conf].mean()))
    r = pd.DataFrame(rows)
    r['conf_gain_days_vs_games_%'] = 100 * (1 - r.conf_days / r.conf_games)
    print(r.round(4).to_string(index=False))
    r.to_csv(f'{cache}/research_rate_memory_days.csv', index=False)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'nbl/cache')
