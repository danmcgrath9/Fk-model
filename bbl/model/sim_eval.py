"""v2 (ball-by-ball simulator) against v1 (separate team and prop models), on the same games, seasons and measures.

Choices are made on the choose seasons (2022/23, 2023/24); 2024/25 is reported as the confirm season.
Measures: head-to-head bits and log loss; first-innings runs CRPS (the miss of the whole distribution);
player runs log-likelihood given he batted (a negative binomial with the simulated mean and variance) and
the chance to bat; runs against the same stand-in lines as bbl/model/backtest.py.

Usage: python -m bbl.model.sim_eval bbl/cache/parquet   (writes SIM.md)
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

from bbl.model import backtest
from bbl.model.team import CHOOSE, CONFIRM, md


def crps_sample(samples, y):
    s = np.sort(samples)
    n = len(s)
    return np.mean(np.abs(s - y)) - np.sum((2 * np.arange(1, n + 1) - n - 1) * s) / n ** 2


def nb_from_moments(mean, var):
    """A negative binomial with the simulated mean and variance (floors keep a 0-run or 1-sample player defined)."""
    mean = max(float(mean), 0.05)
    var = float(var) if np.isfinite(var) else 3 * mean
    var = max(var, mean * 1.01)
    r = mean ** 2 / (var - mean)
    return r, r / (r + mean)


def main(d):
    games = pd.read_pickle(os.path.join(d, 'sim_games.pkl'))
    pls = pd.read_pickle(os.path.join(d, 'sim_players.pkl'))
    t = pd.read_parquet(os.path.join(d, 'team_frame.parquet'))
    v1w = pd.read_parquet(os.path.join(d, 'team_preds.parquet'))
    v1p = pd.read_parquet(os.path.join(d, 'props_preds.parquet'))
    out = ['# v2 (ball-by-ball simulator) against v1, same games', '']

    # head-to-head
    res = t[['match_id', 'team', 'won']].drop_duplicates(['match_id', 'team'])
    g = games.merge(res.rename(columns={'team': 'team1', 'won': 'won1'}), on=['match_id', 'team1'])
    w1 = v1w[v1w.model == 'win_open'][['match_id', 'team_key', 'p']]
    w1['team1'] = w1.team_key.str.split('|').str[0]
    g = g.merge(w1[['match_id', 'team1', 'p']].rename(columns={'p': 'p_v1'}), on=['match_id', 'team1'], how='left')
    g = g[g.won1.isin([0.0, 1.0]) & g.p_v1.notna()]
    rows = []
    for (comp, grp), x in g.assign(grp=np.where(g.season.isin(CHOOSE), 'choose', 'confirm')).groupby(['comp', 'grp']):
        for name, col in (('v1', 'p_v1'), ('v2 sim', 'p_team1')):
            p = x[col].clip(0.01, 0.99)
            win_p = np.where(x.won1 == 1, p, 1 - p)
            rows.append(dict(comp=comp, seasons=grp, model=name, games=len(x), logloss=float(-np.log(win_p).mean()),
                             bits=float((1 + np.log2(win_p)).mean())))
    out += ['## Head-to-head', '', md(pd.DataFrame(rows)), '']

    # first-innings runs (full first innings, no rain rule)
    bf = t[(t.batted_first == 1) & t.full_first_inns.fillna(False).astype(bool) & t.method.isna()][['match_id', 'runs']]
    v1t = v1w[v1w.model == 'first_inns_runs_named'][['match_id', 'mu', 'sd']]
    x = games.merge(bf, on='match_id').merge(v1t, on='match_id', how='left').dropna(subset=['mu'])
    rows = []
    for (comp, grp), y in x.assign(grp=np.where(x.season.isin(CHOOSE), 'choose', 'confirm')).groupby(['comp', 'grp']):
        z = (y.runs - y.mu) / y.sd
        c1 = (y.sd * (z * (2 * stats.norm.cdf(z) - 1) + 2 * stats.norm.pdf(z) - 1 / np.sqrt(np.pi))).mean()
        c2 = np.mean([crps_sample(s, r) for s, r in zip(y.first_runs, y.runs)])
        rows.append(dict(comp=comp, seasons=grp, games=len(y), crps_v1=float(c1), crps_v2=float(c2),
                         mae_v1=float((y.runs - y.mu).abs().mean()), mae_v2=float((y.runs - y.first_mu).abs().mean())))
    out += ['## First-innings runs (lower is better)', '', md(pd.DataFrame(rows)), '']

    # player runs
    p = pls.merge(v1p[['match_id', 'player', 'did_bat', 'bat_runs', 'p_bat', 'mu_runs', 'r_runs', 'pre_pos_ewm', 'pid', 'dt']],
                  on=['match_id', 'player'])
    p['sim_mu'] = p.sim_runs.map(lambda a: a.mean() if len(a) else np.nan)
    p['sim_var'] = p.sim_runs.map(lambda a: a.var() if len(a) > 1 else np.nan)
    rows = []
    for (comp, grp), y in p.assign(grp=np.where(p.season.isin(CHOOSE), 'choose', 'confirm')).groupby(['comp', 'grp']):
        pb1, pb2 = y.p_bat.clip(1e-4, 1 - 1e-4), y.sim_p_bat.clip(1e-3, 1 - 1e-3)
        b = y[(y.did_bat == 1) & y.sim_mu.notna()]
        ll1 = stats.nbinom.logpmf(b.bat_runs, b.r_runs, b.r_runs / (b.r_runs + b.mu_runs)).mean()
        ll2 = np.mean([stats.nbinom.logpmf(r, *nb_from_moments(mu, v)) for r, mu, v in zip(b.bat_runs, b.sim_mu, b.sim_var)])
        rows.append(dict(comp=comp, seasons=grp, player_games=len(y), bats_ll_v1=float(np.mean(np.where(y.did_bat == 1, np.log(pb1), np.log(1 - pb1)))),
                         bats_ll_v2=float(np.mean(np.where(y.did_bat == 1, np.log(pb2), np.log(1 - pb2)))),
                         runs_ll_v1=float(ll1), runs_ll_v2=float(ll2)))
    out += ['## Players: log-likelihood of whether he batted and of his runs (higher is better)', '', md(pd.DataFrame(rows)), '']

    # runs against the stand-in lines
    avg = backtest.recent_averages(d)
    q = p.merge(avg, on=['match_id', 'pid'], how='left')
    q = q[(q.pre_pos_ewm <= 5) & (q.n_runs >= 10) & (q.did_bat == 1) & q.avg_runs.notna() & q.sim_mu.notna()].copy()
    rows_all = backtest.market_rows(v1p, avg)
    ks = backtest.tune_k(rows_all)
    q['line'] = np.floor(ks['runs'] * q.avg_runs) + 0.5
    q['p_over'] = [np.mean(s > l) for s, l in zip(q.sim_runs, q.line)]
    q['over_won'] = (q.bat_runs > q.line).astype(int)
    rows = []
    for comp, y in q.groupby('comp'):
        ch = {thr: backtest.summary(backtest.bets(y[y.season.isin(CHOOSE)], thr)) for thr in backtest.THRESHOLDS}
        ok = {k: v for k, v in ch.items() if v['bets'] >= 100}
        thr = max(ok, key=lambda k: ok[k]['roi']) if ok else max(backtest.THRESHOLDS)
        for grp, ss in (('choose', CHOOSE), ('confirm', CONFIRM)):
            rows.append(dict(comp=comp, seasons=grp, threshold=thr, **backtest.summary(backtest.bets(y[y.season.isin(ss)], thr))))
    out += ['## v2 runs against the stand-in line (a proxy; same line and grading as PROPS.md)', '', md(pd.DataFrame(rows)), '']
    text = '\n'.join(out)
    open(os.path.join(d, 'SIM.md'), 'w').write(text)
    print(text)


if __name__ == '__main__':
    main(sys.argv[1])
