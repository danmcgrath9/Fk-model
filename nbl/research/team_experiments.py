"""Team-model experiments, scored the same way as the model chooses its penalty: each season 2018-19 to
2022-23 predicted from the seasons before it (rolling origin), then 2023-24 and 2024-25 (confirm).
2025-26 and later are not used here.
  adj   opponent-adjusted offence and defence (KenPom, additive): per team-game points per 100 possessions =
        league + offence(team) - defence(opponent) + home, ridge-fitted on earlier games with recency weights,
        refitted every 14 days
  early squad ratings weighted up early in the season: interactions with how many games a team has played
Usage: python -m nbl.research.team_experiments nbl/cache"""
import sys

import numpy as np
import pandas as pd
from scipy import stats

from nbl.model import team

HALF_LIFE = 120.0       # days


def adjusted_ratings(tg):
    """Pre-game opponent-adjusted offence/defence (points per 100 possessions above the league) for every team-game."""
    t = tg[tg.poss.notna() & tg.score.notna()].copy()
    t['ppp'] = 100 * t.score / t.poss
    teams = sorted(tg.team.unique()); ix = {k: i for i, k in enumerate(teams)}; nT = len(teams)
    dates = pd.date_range(tg.tip.min().normalize() + pd.Timedelta(days=14), tg.tip.max() + pd.Timedelta(days=14), freq='14D')
    out = []
    for d in dates:
        h = t[t.tip < d]
        if len(h) < 60:
            continue
        w = 0.5 ** ((d - h.tip).dt.days.to_numpy() / HALF_LIFE)
        X = np.zeros((len(h), 2 * nT + 1))
        r = np.arange(len(h))
        X[r, h.team.map(ix).to_numpy()] = 1.0                 # offence of the scoring team
        X[r, nT + h.opp.map(ix).to_numpy()] = -1.0            # defence of the opponent
        X[:, -1] = h.is_home.to_numpy() * 2 - 1
        y = h.ppp.to_numpy() - np.average(h.ppp, weights=w)
        lam = 5.0
        A = X.T @ (X * w[:, None]) + lam * np.diag(np.r_[np.ones(2 * nT), 0.0])
        b = np.linalg.solve(A, X.T @ (w * y))
        out.append(pd.DataFrame({'asof': d, 'team': teams, 'adj_o': b[:nT], 'adj_d': b[nT:2 * nT]}))
    r = pd.concat(out).sort_values('asof')
    g = tg[['game', 'tip', 'team']].sort_values('tip')
    g = pd.merge_asof(g, r.rename(columns={'asof': 'tip'}), on='tip', by='team', direction='backward', allow_exact_matches=False)
    return g[['game', 'team', 'adj_o', 'adj_d']]


def cv(g, cols, target='home_margin'):
    best = None
    for lam in (0.1, 1, 10, 100, 1000):
        errs, lls = [], []
        for s in range(2018, 2023):
            tr, te = g[g.season < s], g[g.season == s]
            m = team.Ridge(cols, lam).fit(tr, tr[target])
            pred = m.predict(te); sd = np.std(tr[target] - m.predict(tr))
            errs.append(np.abs(pred - te[target]))
            p = np.clip(stats.norm.cdf(pred / sd), 1e-6, 1 - 1e-6); y = (te[target] > 0).to_numpy()
            lls.append(-(y * np.log(p) + (1 - y) * np.log(1 - p)))
        mae, ll = np.concatenate(errs).mean(), np.concatenate(lls).mean()
        if best is None or ll < best[1]:
            best = (mae, ll, lam)
    lam = best[2]
    tr, te = g[g.season.between(2016, 2022)], g[g.season.between(2023, 2024)]
    m = team.Ridge(cols, lam).fit(tr, tr[target]); pred = m.predict(te); sd = np.std(tr[target] - m.predict(tr))
    p = np.clip(stats.norm.cdf(pred / sd), 1e-6, 1 - 1e-6); y = (te[target] > 0).to_numpy()
    return dict(cv_mae=best[0], cv_ll=best[1], lam=lam, conf_mae=float(np.abs(pred - te[target]).mean()),
                conf_ll=float(np.mean(-(y * np.log(p) + (1 - y) * np.log(1 - p)))))


def main(cache):
    tg = team.with_rapm(pd.read_parquet(f'{cache}/teams.parquet'), cache)
    adj = adjusted_ratings(tg)
    tg = tg.merge(adj, on=['game', 'team'], how='left')
    g = team.games_table(tg)
    h = tg[tg.is_home == 1][['game', 'adj_o', 'adj_d']]; a = tg[tg.is_home == 0][['game', 'adj_o', 'adj_d']]
    g = g.merge(h.merge(a, on='game', suffixes=('_h', '_a')), on='game')
    g['d_adj_net'] = (g.adj_o_h - g.adj_d_h) - (g.adj_o_a - g.adj_d_a)
    g = g[(g.games_prior_h >= 1) & (g.games_prior_a >= 1) & g.season.between(2016, 2024)]
    early = np.clip(1 - np.minimum(g.games_prior_h, g.games_prior_a) / 10, 0, 1)   # 1 at a team's first game of history
    gp = g.groupby(['season', 'home']).cumcount()
    g['season_games'] = np.minimum(g.groupby(['season']).cumcount(), 999)
    # games into this season for the less-experienced side
    th = pd.concat([g[['game', 'season', 'tip', 'home']].rename(columns={'home': 't'}), g[['game', 'season', 'tip', 'away']].rename(columns={'away': 't'})])
    th = th.sort_values('tip'); th['n'] = th.groupby(['season', 't']).cumcount()
    nmin = th.groupby('game').n.min()
    g['early'] = np.clip(1 - g.game.map(nmin) / 8, 0, 1)
    g['elo_x_early'] = g.elo_margin * g.early
    g['rapm_x_early'] = g.d_named_rapm * g.early
    base = team.MARGIN['named']
    sets = {'elo only': ['elo_margin'], 'current named': base, 'current + adjusted efficiency': base + ['d_adj_net'],
            'adjusted efficiency instead of raw': [c for c in base if c != 'd_net_ew'] + ['d_adj_net'],
            'current + early-season weights': base + ['elo_x_early', 'rapm_x_early', 'early'],
            'all': base + ['d_adj_net', 'elo_x_early', 'rapm_x_early', 'early'],
            'lean: elo + rapm + adj + rest': ['elo_margin', 'd_named_rapm', 'd_adj_net', 'd_days_rest']}
    rows = []
    for k, c in sets.items():
        r = cv(g, c); r['features'] = k; rows.append(r); print(r, flush=True)
    print(pd.DataFrame(rows)[['features', 'lam', 'cv_mae', 'cv_ll', 'conf_mae', 'conf_ll']].round(4).to_string(index=False))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'nbl/cache')
