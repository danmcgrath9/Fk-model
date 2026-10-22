"""Experiment: per-stat memory (DARKO-style). For each stat, which decay per game and how many minutes of
league-average prior best predict a player's NEXT game, given the minutes he actually played?

Score: mean squared error of rate x actual minutes against the stat, on played games, 2016-17 to 2022-23
(choices) and 2023-24 to 2024-25 (confirm). Isolates the rate from the minutes projection.

Usage: python -m nbl.research.rate_memory nbl/cache
"""
import itertools
import sys

import numpy as np
import pandas as pd

from nbl.model.frame import RATE_COLS, league_rates

DECAYS = [0.85, 0.90, 0.92, 0.95, 0.97, 0.985]
PRIORS = [15, 30, 60, 120, 240]


def rates(p, stat, decay, prior, lr):
    """Pre-game per-minute rate for one stat (same rule as frame.player_history)."""
    out = np.full(len(p), np.nan)
    keys = p.key.to_numpy(); order = np.argsort(keys, kind='stable')
    k = keys[order]; starts = np.r_[0, np.flatnonzero(k[1:] != k[:-1]) + 1, len(k)]
    st, mn, pl, se = p[stat].to_numpy(float), p['min'].to_numpy(float), p.played.to_numpy(float), p.season.to_numpy()
    for a, b in zip(starts[:-1], starts[1:]):
        s_st = s_m = 0.0
        for i in order[a:b]:
            league = lr[se[i]][stat]
            out[i] = (s_st + prior * league) / (s_m + prior)
            if pl[i] == 1:
                s_st = decay * s_st + st[i]
                s_m = decay * s_m + mn[i]
    return out


def main(cache):
    p = pd.read_parquet(f'{cache}/players.parquet')
    p = p[p.played.notna() & (p.season <= 2024)].sort_values(['tip', 'game']).reset_index(drop=True)
    lr = league_rates(p)
    ev = (p.played == 1) & (p.games_prior >= 5) & (p.min_ew >= 12)
    dev, conf = ev & p.season.between(2016, 2022), ev & p.season.between(2023, 2024)
    rows = []
    for stat in ['pts', 'reb', 'ast', 'fg3m', 'fg3a', 'fga', 'fta', 'tov', 'stl', 'blk', 'eff']:
        best = None
        for d, pr in itertools.product(DECAYS, PRIORS):
            r = rates(p, stat, d, pr, lr)
            err = (r * p['min'] - p[stat]) ** 2
            e_dev, e_conf = err[dev].mean(), err[conf].mean()
            if (d, pr) == (0.92, 60):
                cur = (e_dev, e_conf)
            if best is None or e_dev < best[0]:
                best = (e_dev, e_conf, d, pr)
        rows.append(dict(stat=stat, decay=best[2], prior_min=best[3], mse_dev_best=best[0], mse_dev_now=cur[0],
                         mse_conf_best=best[1], mse_conf_now=cur[1]))
        print(rows[-1], flush=True)
    r = pd.DataFrame(rows)
    r['conf_gain_%'] = 100 * (1 - r.mse_conf_best / r.mse_conf_now)
    print(r.round(4).to_string(index=False))
    r.to_csv(f'{cache}/research_rate_memory.csv', index=False)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'nbl/cache')
