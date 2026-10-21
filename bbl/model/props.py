"""Player props: a distribution per player per game for runs, sixes and wickets, priced over/under any line.

Walk-forward like the team model: each BBL/WBBL season is predicted by models fitted on club T20 player-games
of the same gender that started before it. Props are priced with teams named (the XI is known): books post
most player lines once teams are out, and a prop on a player who is not playing is void anyway.

  runs    P(bats) x negative binomial runs given he bats; mean from LightGBM (Poisson) on pre-game form,
          batting position, his side's and the opposition's strength and the ground's scoring
  sixes   negative binomial, same features, given he bats
  wickets P(bowls) x negative binomial wickets given he bowls

Dispersion of each negative binomial is fitted by maximum likelihood on the training rows, per batting
position band for runs (an opener's spread is not a No. 8's).

Usage: python -m bbl.model.props bbl/cache/parquet   (writes props_preds.parquet)
"""
import os
import sys

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy import optimize, stats

from bbl.model import frame
from bbl.model.team import CHOOSE, CONFIRM, EVAL_SEASONS, FINAL

CTX = ['venue_first_runs', 'elo_pre', 'opp_elo_pre', 'xi_runs_named', 'xi_econ_named', 'opp_xi_runs_named',
       'opp_xi_econ_named', 'opp_xi_wkts_named', 'venue_share']
BAT = ['pre_runs_pg', 'pre_balls_pg', 'pre_sixes_pg', 'pre_fours_pg', 'pre_bat_rate', 'pre_pos_ewm', 'pre_sr',
       'pre_out_per_ball', 'pre_games', 'pre_comp_games', 'pre_comp_runs_pg', 'days_rest', 'list_order']
BOWL = ['pre_bowl_balls_pg', 'pre_bowl_rate', 'pre_econ', 'pre_wkts_per_ball', 'pre_games', 'list_order', 'days_rest']
LGB = dict(objective='poisson', learning_rate=0.05, n_estimators=300, num_leaves=15, min_child_samples=100,
           subsample=0.8, subsample_freq=1, colsample_bytree=0.8, verbose=-1)
POS_BANDS = [(0, 2.5), (2.5, 4.5), (4.5, 6.5), (6.5, 99)]


def nb_logpmf(y, mu, r):
    p = r / (r + mu)
    return stats.nbinom.logpmf(y, r, p)


def fit_r(y, mu):
    """Negative binomial size parameter by maximum likelihood, given the means."""
    y, mu = np.asarray(y, float), np.clip(np.asarray(mu, float), 1e-3, None)
    res = optimize.minimize_scalar(lambda lr: -nb_logpmf(y, mu, np.exp(lr)).sum(), bounds=(-3, 5), method='bounded')
    return float(np.exp(res.x))


def band(pos):
    pos = np.asarray(pos, float)
    out = np.full(len(pos), len(POS_BANDS) - 1)
    for k, (lo, hi) in reversed(list(enumerate(POS_BANDS))):
        out[(np.nan_to_num(pos, nan=99) > lo) & (np.nan_to_num(pos, nan=99) <= hi)] = k
    return out


def _fit_cls(train, feats, y):
    m = lgb.LGBMClassifier(**{**LGB, 'objective': 'binary'})
    m.fit(train[feats], y)
    return m


def _fit_reg(train, feats, y):
    m = lgb.LGBMRegressor(**LGB)
    m.fit(train[feats], y)
    return m


def predict_season(g, gender, comp, season):
    test = g[(g.comp == comp) & (g.season == season)]
    if test.empty:
        return None
    train = g[(g.gender == gender) & (g.team_type == 'club') & (g.dt < test.dt.min())]
    out = test[['match_id', 'dt', 'season', 'comp', 'team', 'team_key', 'player', 'pid', 'did_bat', 'bat_runs', 'bat_6s',
                'did_bowl', 'bowl_wkts', 'bat_pos', 'pre_pos_ewm', 'pre_runs_pg', 'list_order']].copy()
    bf, wf = BAT + CTX, BOWL + CTX
    # runs and sixes
    out['p_bat'] = _fit_cls(train, bf, train.did_bat).predict_proba(test[bf])[:, 1]
    tb = train[train.did_bat == 1]
    m_runs = _fit_reg(tb, bf, tb.bat_runs)
    out['mu_runs'] = m_runs.predict(test[bf])
    tb_mu = m_runs.predict(tb[bf])
    tb_band, out_band = band(tb.pre_pos_ewm), band(test.pre_pos_ewm)
    r_band = {k: fit_r(tb.bat_runs[tb_band == k], tb_mu[tb_band == k]) for k in range(len(POS_BANDS))}
    out['r_runs'] = [r_band[k] for k in out_band]
    m6 = _fit_reg(tb, bf, tb.bat_6s)
    out['mu_6s'] = m6.predict(test[bf])
    out['r_6s'] = fit_r(tb.bat_6s, m6.predict(tb[bf]))
    # wickets
    out['p_bowl'] = _fit_cls(train, wf, train.did_bowl).predict_proba(test[wf])[:, 1]
    tw = train[train.did_bowl == 1]
    mw = _fit_reg(tw, wf, tw.bowl_wkts)
    out['mu_wkts'] = mw.predict(test[wf])
    out['r_wkts'] = fit_r(tw.bowl_wkts, mw.predict(tw[wf]))
    return out


def recalibrate(p):
    """Scale each season's means by how far off the model ran in EARLIER predicted seasons of the same competition.

    The models are fitted on every club league, and a BBL six is not an IPL six. Each season's factor is
    sum(actual) / sum(predicted) over the seasons before it only (out of sample), so this adds no hindsight.
    The first predicted season of each competition keeps a factor of 1.
    """
    p = p.sort_values('dt').copy()
    cols = [('mu_runs', 'bat_runs', 'did_bat'), ('mu_6s', 'bat_6s', 'did_bat'), ('mu_wkts', 'bowl_wkts', 'did_bowl')]
    for comp, g in p.groupby('comp'):
        seasons = sorted(g.season.unique())
        for k, s in enumerate(seasons):
            past = g[g.season.isin(seasons[:k])]
            rows = (p.comp == comp) & (p.season == s)
            for mu, y, played in cols:
                q = past[past[played] == 1]
                f = q[y].sum() / q[mu].sum() if len(q) and q[mu].sum() > 0 else 1.0
                p.loc[rows, mu + '_raw'] = p.loc[rows, mu]
                p.loc[rows, mu] = p.loc[rows, mu] * f
                p.loc[rows, mu + '_factor'] = f
    return p


def predict_all(d):
    g = pd.read_parquet(os.path.join(d, 'player_frame.parquet'))
    tt = pd.read_parquet(os.path.join(d, 't20_matches.parquet'), columns=['match_id', 'team_type'])
    g = g.merge(tt, on='match_id')
    seasons = EVAL_SEASONS if os.environ.get('FINAL') == '1' else [s for s in EVAL_SEASONS if s not in FINAL]
    parts = [predict_season(g, gender, comp, s) for gender, comp in (('male', 'BBL'), ('female', 'WBBL')) for s in seasons]
    return recalibrate(pd.concat([p for p in parts if p is not None], ignore_index=True))


# ---------------------------------------------------------------- pricing

def p_over_nb(line, mu, r):
    """P(count > line) for a .5 line under a negative binomial."""
    k = np.floor(line)
    return stats.nbinom.sf(k, r, r / (r + np.clip(mu, 1e-6, None)))


def p_runs_over(line, row, given_bats=True):
    """Over a runs line. given_bats=True prices the bet a book voids when the player does not bat."""
    p = p_over_nb(line, row['mu_runs'], row['r_runs'])
    return p if given_bats else row['p_bat'] * p


def top_batter_probs(team_rows, n=20000, seed=0):
    """Chance each player tops his side's runs, from independent draws of each player's distribution.

    Ties are split evenly (a dead heat). Independence is an approximation: a side's batters share the
    conditions, which moves all of them together and changes the levels more than the order.
    """
    rng = np.random.default_rng(seed)
    mu, r, pb = team_rows.mu_runs.to_numpy(), team_rows.r_runs.to_numpy(), team_rows.p_bat.to_numpy()
    draws = rng.negative_binomial(r[:, None], (r / (r + mu))[:, None], size=(len(mu), n))
    draws = np.where(rng.random((len(mu), n)) < pb[:, None], draws, -1)   # did not bat: cannot top score
    best = draws.max(axis=0)
    win = (draws == best) & (best >= 0)
    share = win / win.sum(axis=0).clip(min=1)
    return pd.Series(share.mean(axis=1), index=team_rows.index)


def main(d):
    p = predict_all(d)
    p.to_parquet(os.path.join(d, 'props_preds.parquet'), index=False)
    print(f'props_preds: {len(p):,} player-games, seasons {", ".join(sorted(p.season.unique()))}')


if __name__ == '__main__':
    main(sys.argv[1])
