"""Experiment: offence and defence on-court ratings (two numbers per player, as in O-RAPM / D-RAPM), so a
squad's expected points for and against can feed the TOTAL, which the net rating cannot.

Each stint gives two rows: home points per 40 = league + home offence - away defence + home edge, and the
same for the away side. Ridge, recency-weighted, refitted every 14 days from earlier stints only (same
settings as model/onoff.py). Squad offence/defence = minutes-weighted sums (named squads).
Scored like research/team_experiments.py on totals: rolling 2018-19 to 2022-23, confirm 2023-24 and 2024-25.
Usage: python -m nbl.research.od_ratings nbl/cache"""
import sys

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.linalg import solve
from scipy.sparse.linalg import lsqr

from nbl.model import onoff, team


def fit_od(s, asof, keys, lam):
    s = s[s.tip < asof]
    if s.empty:
        return None
    n, P = len(s), len(keys)
    idx = {k: i for i, k in enumerate(keys)}
    rows, cols, vals = [], [], []
    for i, (h, a) in enumerate(zip(s.home_on, s.away_on)):
        for k in h:   # row i: home scoring; offence of home (col idx), defence of away (P + idx, minus)
            rows += [i, n + i]; cols += [idx[k], P + idx[k]]; vals += [1.0, -1.0]
        for k in a:
            rows += [i, n + i]; cols += [P + idx[k], idx[k]]; vals += [-1.0, 1.0]
    X = sparse.csr_matrix((vals, (rows, cols)), shape=(2 * n, 2 * P))
    y = np.r_[40.0 * s.home_pts / s.minutes, 40.0 * s.away_pts / s.minutes]
    home = np.r_[np.ones(n), -np.ones(n)]
    age = (asof - s.tip).dt.days.to_numpy()
    w = np.r_[s.minutes.to_numpy(), s.minutes.to_numpy()] * np.r_[0.5 ** (age / onoff.HALF_LIFE_DAYS)] .repeat(1) if False else \
        np.tile(s.minutes.to_numpy() * 0.5 ** (age / onoff.HALF_LIFE_DAYS), 2)
    mu = np.average(y, weights=w)
    hca = np.average(y * home, weights=w) / 1.0
    r = y - mu - hca * home / 2 * 0 - (np.average(y[:n], weights=w[:n]) - np.average(y[n:], weights=w[n:])) / 2 * home
    sw = np.sqrt(w)
    A = sparse.vstack([sparse.diags(sw) @ X, np.sqrt(lam) * sparse.identity(2 * P)])
    beta = lsqr(A, np.r_[sw * r, np.zeros(2 * P)], atol=1e-8, btol=1e-8, iter_lim=5000)[0]
    return pd.DataFrame({'key': keys, 'off': beta[:P], 'def': beta[P:]})


def od_by_date(s, players, lam):
    keys = sorted(set(k for t in s.home_on for k in t) | set(k for t in s.away_on for k in t))
    tips = players.tip.sort_values()
    d, end = tips.iloc[0] + pd.Timedelta(days=60), tips.iloc[-1] + pd.Timedelta(days=onoff.REFIT_DAYS)
    out = []
    while d <= end:
        r = fit_od(s, d, keys, lam)
        if r is not None:
            out.append(r.assign(asof=d))
        d += pd.Timedelta(days=onoff.REFIT_DAYS)
    return pd.concat(out, ignore_index=True)


def squad_od(players, r):
    p = players.sort_values('tip')[['game', 'tip', 'team', 'key', 'min_ew']].copy()
    rr = r.sort_values('asof').rename(columns={'asof': 'tip'})
    p = pd.merge_asof(p, rr, on='tip', by='key', direction='backward', allow_exact_matches=False)
    p[['off', 'def']] = p[['off', 'def']].fillna(0.0)
    m = p.min_ew.fillna(0).clip(lower=0)
    p['wm'] = m / p.groupby(['game', 'team']).min_ew.transform(lambda x: x.fillna(0).clip(lower=0).sum()).replace(0, np.nan) * 200 / 40
    p['o'] = p.off * p.wm; p['d'] = p['def'] * p.wm
    return p.groupby(['game', 'team'], as_index=False)[['o', 'd']].sum().rename(columns={'o': 'squad_off', 'd': 'squad_def'})


def main(cache):
    s = pd.read_parquet(f'{cache}/stints.parquet')
    players = pd.read_parquet(f'{cache}/players.parquet')
    players = players[players.played.notna()]
    tg = team.with_rapm(pd.read_parquet(f'{cache}/teams.parquet'), cache)
    from nbl.research.team_experiments import cv
    res = []
    for lam in (1000, 3000, 10000):
        r = od_by_date(s, players, lam)
        sq = squad_od(players, r)
        t = tg.merge(sq, on=['game', 'team'], how='left')
        g = team.games_table(t)
        h = t[t.is_home == 1][['game', 'squad_off', 'squad_def']]; a = t[t.is_home == 0][['game', 'squad_off', 'squad_def']]
        g = g.merge(h.merge(a, on='game', suffixes=('_h', '_a')), on='game')
        g['od_total'] = g.squad_off_h + g.squad_off_a - g.squad_def_h - g.squad_def_a
        g['od_margin'] = (g.squad_off_h - g.squad_def_h) - (g.squad_off_a - g.squad_def_a)
        g = g[(g.games_prior_h >= 1) & (g.games_prior_a >= 1) & g.season.between(2016, 2024)]
        for name, cols, tgt in (('total: current', team.TOTAL['named'], 'total'),
                                ('total: + squad offence/defence', team.TOTAL['named'] + ['od_total'], 'total'),
                                ('margin: current', team.MARGIN['named'], 'home_margin'),
                                ('margin: + offence/defence margin', team.MARGIN['named'] + ['od_margin'], 'home_margin')):
            x = cv(g, cols, tgt); x.update(name=name, lam_od=lam); res.append(x)
            print(x, flush=True)
    print(pd.DataFrame(res)[['lam_od', 'name', 'cv_mae', 'conf_mae', 'cv_ll', 'conf_ll']].round(4).to_string(index=False))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'nbl/cache')
