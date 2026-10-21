"""Goals, marks and tackles props: the disposals method (afl/model/disposals.py) applied to other stats.

Per stat: pre-game features for that stat (form over several windows, per-full-game rate, share of the team's usual
total, the opponent's concessions against the league, the team's expected score for goals), a boosted-tree Poisson
model, a negative binomial spread fitted on the tuning season, then:
  marks, tackles  over/under against a STAND-IN line (recent average, tuned so a blind over wins half the time), as for
                  disposals: a proxy, not a market test
  goals           sold as anytime / 2+ / 3+ prices, not a 50/50 line, so no stand-in ROI is claimed: the test is how
                  much better our chances of 1+, 2+, 3+ goals are than a recent-average baseline (log loss), and
                  whether they are calibrated

Split as everywhere: fit 2013-2023, choose on 2024, score 2025 and 2026 once.
Usage: python -m afl.model.props afl/cache afl/docs/PROPS_STEP1.md
"""
import sys
import warnings

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy import stats

from afl.model.disposals import PARAMS, PRICE, bets, even_shift, fit_dispersion, nb_logpmf, p_over, roi_with_ci, stand_in_line
from afl.model.frame import FEATURES

warnings.filterwarnings('ignore')
TRAIN, TUNE, TESTS = (2013, 2023), 2024, (2025, 2026)


def stat_features(m, stat):
    """Rolling pre-game features for one stat (shifted one game, like every other feature)."""
    m = m.sort_values(['dt', 'game']).reset_index(drop=True).copy()
    p = m.groupby('player_id', sort=False)
    s = stat
    for n in (3, 5, 10, 20):
        m[f'{s}_l{n}'] = p[s].transform(lambda x: x.shift(1).rolling(n, min_periods=1).mean())
    m[f'{s}_ewm'] = p[s].transform(lambda x: x.shift(1).ewm(halflife=5, min_periods=1).mean())
    m[f'{s}_season'] = m.groupby(['player_id', 'season'], sort=False)[s].transform(lambda x: x.shift(1).expanding().mean())
    num = p[s].transform(lambda x: x.shift(1).rolling(20, min_periods=1).sum())
    den = p.tog_frac.transform(lambda x: x.shift(1).rolling(20, min_periods=1).sum())
    m[f'{s}_rate20'] = num / den.replace(0, np.nan)
    tg = m.groupby(['game', 'team'])
    m[f'{s}_team_pool'] = tg[f'{s}_l10'].transform('sum')
    m[f'{s}_share'] = m[f'{s}_l10'] / m[f'{s}_team_pool'].replace(0, np.nan)
    # opponent: how many of this stat it has conceded lately, against the league
    team_g = m.groupby(['game', 'dt', 'team', 'opp'], as_index=False)[s].sum()
    conc = team_g.rename(columns={'team': 'opp', 'opp': 'team', s: 'against'})[['game', 'team', 'against']]
    tgm = team_g.merge(conc, on=['game', 'team']).sort_values('dt')
    tgm['conc_l8'] = tgm.groupby('team').against.transform(lambda x: x.shift(1).rolling(8, min_periods=3).mean())
    tgm['for_l8'] = tgm.groupby('team')[s].transform(lambda x: x.shift(1).rolling(8, min_periods=3).mean())
    m = m.merge(tgm[['game', 'team', 'for_l8']].rename(columns={'for_l8': f'{s}_team_l8'}), on=['game', 'team'], how='left')
    m = m.merge(tgm[['game', 'team', 'conc_l8']].rename(columns={'team': 'opp', 'conc_l8': f'{s}_opp_conc_l8'}), on=['game', 'opp'], how='left')
    league = tgm.groupby('dt').against.mean().shift(1).rolling(30, min_periods=5).mean()
    m[f'{s}_opp_rel'] = m[f'{s}_opp_conc_l8'] / m.dt.map(league)
    feats = [c for c in m.columns if c.startswith(f'{s}_') and c != s]
    return m, feats


def team_expected_score(m):
    """Each team's expected score, from its recent scoring and the opponent's recent conceding (pre-game)."""
    tg = m.groupby(['game', 'dt', 'team', 'opp'], as_index=False).agg(sf=('score_for', 'first'), sa=('score_against', 'first')).sort_values('dt')
    tg['sf_l8'] = tg.groupby('team').sf.transform(lambda x: x.shift(1).rolling(8, min_periods=3).mean())
    tg['sa_l8'] = tg.groupby('team').sa.transform(lambda x: x.shift(1).rolling(8, min_periods=3).mean())
    opp = tg[['game', 'team', 'sa_l8']].rename(columns={'team': 'opp', 'sa_l8': 'opp_sa_l8'})
    tg = tg.merge(opp, on=['game', 'opp'], how='left')
    tg['exp_score'] = (tg.sf_l8 + tg.opp_sa_l8) / 2
    return m.merge(tg[['game', 'team', 'exp_score']], on=['game', 'team'], how='left')


def eligible(m):
    return m[(m.games_prior >= 5) & (m.named_sub != 1)].copy()


def fit_model(tr, tu, feats, stat):
    mdl = lgb.LGBMRegressor(objective='poisson', **PARAMS)
    mdl.fit(tr[feats], tr[stat], eval_set=[(tu[feats], tu[stat])], callbacks=[lgb.early_stopping(150, verbose=False)])
    return mdl


def nb_tail(mu, k, a):
    """P(stat >= k) under the negative binomial; a ~ 0 falls back to Poisson."""
    if a < 1e-3:
        return 1 - stats.poisson.cdf(k - 1, mu)
    n = 1 / a
    return 1 - stats.nbinom.cdf(k - 1, n, n / (n + mu))


def run(cache, out_md):
    base = pd.read_parquet(f'{cache}/frame.parquet')
    base = team_expected_score(base)
    rep = ['# AFL props, step 1: goals, marks, tackles', '',
           f'Fitted {TRAIN[0]}-{TRAIN[1]}, every choice made on {TUNE}, {TESTS[0]} and {TESTS[1]} scored once. Established players '
           '(5+ games on record), named subs excluded.', '']
    for stat, label in (('M', 'marks'), ('T', 'tackles'), ('G', 'goals')):
        m, sfeats = stat_features(base, stat)
        feats = FEATURES + [f for f in sfeats if f not in FEATURES] + ['exp_score']
        m = eligible(m)
        m = m[m[f'{stat}_l10'].notna()]
        tr, tu = m[m.season.between(*TRAIN)], m[m.season == TUNE]
        mdl = fit_model(tr, tu, feats, stat)
        tu = tu.assign(mu=mdl.predict(tu[feats]))
        a = fit_dispersion(tu[stat].to_numpy(), tu.mu.to_numpy())
        rep += [f'## {label.capitalize()}', '', f'Spread on {TUNE}: variance = mean + {a:.3f} x mean squared.', '']
        tests = {s: m[m.season == s].assign(mu=lambda d: mdl.predict(d[feats])) for s in TESTS}
        rep += ['| season | player-games | projection miss | last-10 average miss |', '|---|---|---|---|']
        for s, te in tests.items():
            rep.append(f'| {s} | {len(te):,} | {(te[stat] - te.mu).abs().mean():.2f} | {(te[stat] - te[f"{stat}_l10"]).abs().mean():.2f} |')
        rep.append('')
        if stat in ('M', 'T'):
            shift = even_shift(tu[stat].to_numpy(), tu[f'{stat}_l10'].to_numpy())
            rep += [f'Stand-in line: last-10 average {shift:+.2f}, rounded to the .5 below (tuned on {TUNE}). **Proxy, not market lines.**', '',
                    '| season | blind over wins | bet when chance over | bets | hit rate | ROI at 1.87 | 90% interval |', '|---|---|---|---|---|---|---|']
            for s, te in tests.items():
                d = te.copy()
                d['line'] = stand_in_line(d[f'{stat}_l10'].to_numpy(), shift)
                d['p_over'] = p_over(d.mu.to_numpy(), d.line.to_numpy(), max(a, 1e-3))
                for thr in (0.56, 0.60):
                    b = bets(d.rename(columns={stat: 'D'}) if False else d.assign(D=d[stat]), 'p_over', thr)
                    r, lo, hi = roi_with_ci(b)
                    rep.append(f'| {s} | {(d[stat] > d.line).mean():.1%} | {thr:.0%} | {len(b):,} | {b.win.mean():.1%} | {r:+.1%} | {lo:+.1%} to {hi:+.1%} |')
            rep.append('')
        else:
            # baseline: Poisson around the player's last-10 goal average
            rep += ['Chances of kicking 1+, 2+, 3+ goals: our model against a Poisson around the last-10 average. '
                    'Log loss, lower is better; calibration = average predicted against what happened.', '',
                    '| season | goals | model log loss | baseline log loss | model: predicted / actual | baseline: predicted / actual |',
                    '|---|---|---|---|---|---|']
            for s, te in tests.items():
                for k in (1, 2, 3):
                    y = (te.G >= k).to_numpy().astype(float)
                    pm = np.clip(nb_tail(te.mu.to_numpy(), k, a), 1e-6, 1 - 1e-6)
                    pb = np.clip(1 - stats.poisson.cdf(k - 1, te.G_l10.clip(lower=0.01).to_numpy()), 1e-6, 1 - 1e-6)
                    ll = lambda p: -(y * np.log(p) + (1 - y) * np.log(1 - p)).mean()
                    rep.append(f'| {s} | {k}+ | {ll(pm):.4f} | {ll(pb):.4f} | {pm.mean():.1%} / {y.mean():.1%} | {pb.mean():.1%} / {y.mean():.1%} |')
            rep.append('')
            # calibration of the anytime chance, both seasons
            te = pd.concat(tests.values())
            te['p1'] = nb_tail(te.mu.to_numpy(), 1, a)
            te['bin'] = pd.cut(te.p1, [0, .1, .2, .3, .4, .5, .6, .7, 1])
            rep += ['Anytime goal: calibration, both seasons', '', '| our chance | player-games | average predicted | actually kicked one |', '|---|---|---|---|']
            for k_, g in te.groupby('bin', observed=True):
                rep.append(f'| {k_} | {len(g):,} | {g.p1.mean():.1%} | {(g.G >= 1).mean():.1%} |')
            rep.append('')
        imp = pd.Series(mdl.booster_.feature_importance('gain'), index=feats)
        top = (imp / imp.sum()).sort_values(ascending=False).head(6)
        rep += ['Leans on: ' + ', '.join(f'{k} {v:.0%}' for k, v in top.items()), '']
        print(label, 'done', flush=True)
    open(out_md, 'w').write('\n'.join(rep) + '\n')
    print('\n'.join(rep))


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else 'afl/cache', sys.argv[2] if len(sys.argv) > 2 else 'afl/docs/PROPS_STEP1.md')
