"""Ideas from afl/docs/RESEARCH_BEST_MODEL.md that can be tested before any bookmaker prop line exists.

1. The market's view of the game (its margin and win chance, Squiggle's "Punters", 2017 on) as an input beside or in
   place of our Elo margin (research rank 2).
2. Each stat its own memory: exponentially weighted averages with shorter and longer half-lives (rank 6).
3. Substitute risk: how often the player has lately been subbed off or named sub, and how much his time on ground
   swings (rank 3, the cheap half; the full two-stage version is in the doc).
4. A spread that depends on the player: negative binomial spread as a function of the projection and of the player's
   own recent volatility, fitted on 2024 projections and scored on 2025-2026 (rank 7).

Same rules as afl/model/extra_test.py: fit 2013-2023, tune 2024, score 2025-2026 (never seen), paired per player-game;
kept where more than two standard errors better.

Usage: python -m afl.model.research_tests afl/cache afl/docs/RESEARCH_TESTS.md
"""
import json
import sys
import warnings

import numpy as np
import pandas as pd
from scipy import optimize

from afl.model import props as P
from afl.model.disposals import nb_logpmf
from afl.model.extra_test import score
from afl.model.walkforward import STATS, stat_matrix

warnings.filterwarnings('ignore')


def market(m, cache):
    g = pd.read_parquet(f'{cache}/market_games.parquet')[['game', 'home', 'mkt_margin', 'mkt_p']]
    m = m.merge(g, on='game', how='left')
    home = m.team == m.home
    m['mkt_exp_margin'] = np.where(home, m.mkt_margin, -m.mkt_margin)
    m['mkt_win_p'] = np.where(home, m.mkt_p, 1 - m.mkt_p)
    m['mkt_blowout'] = m.mkt_exp_margin.abs()
    # the market's margin where it exists, our rating's where it does not (2013-2016)
    m['best_exp_margin'] = m.mkt_exp_margin.fillna(m.exp_margin)
    return m.drop(columns=['home', 'mkt_margin', 'mkt_p'])


def memory(m, stat):
    p = m.groupby('player_id', sort=False)[stat]
    for h in (2, 12, 30):
        m[f'{stat}_ewm{h}'] = p.transform(lambda x: x.shift(1).ewm(halflife=h, min_periods=1).mean())
    return m


def sub_risk(m):
    p = m.groupby('player_id', sort=False)
    m['subbed_off_rate10'] = p.subbed_off.transform(lambda x: x.shift(1).rolling(10, min_periods=1).mean())
    m['named_sub_rate10'] = p.named_sub.transform(lambda x: x.shift(1).rolling(10, min_periods=1).mean())
    m['TOG_sd10'] = p.TOG.transform(lambda x: x.shift(1).rolling(10, min_periods=3).std())
    m['TOG_min10'] = p.TOG.transform(lambda x: x.shift(1).rolling(10, min_periods=3).min())
    return m


def groups(stat):
    return {
        'market view of the game': ['mkt_exp_margin', 'mkt_win_p', 'mkt_blowout'],
        'market margin in place of ours': ['best_exp_margin'],
        'shorter and longer memory': [f'{stat}_ewm2', f'{stat}_ewm12', f'{stat}_ewm30'],
        'substitute risk': ['subbed_off_rate10', 'named_sub_rate10', 'TOG_sd10', 'TOG_min10'],
    }


def feature_tests(base, cache, rep, keep):
    for stat, label in STATS.items():
        m, feats, _ = stat_matrix(base, cache, stat)
        m = sub_risk(memory(market(m, cache), stat))
        tr, tu, te = m[m.season.between(2013, 2023)], m[m.season == 2024], m[m.season.isin([2025, 2026])]
        ll0, ae0 = score(tr, tu, te, feats, stat)
        rep += [f'### {label.capitalize()}', '', f'Current model: average miss {ae0.mean():.3f}.', '',
                '| tried | log-lik change | average miss change | kept |', '|---|---|---|---|']
        kept = []
        for g, cols in groups(stat).items():
            f = [c for c in feats if not (g == 'market margin in place of ours' and c in ('exp_margin', 'exp_blowout'))] + cols
            ll, ae = score(tr, tu, te, f, stat)
            d, da = ll - ll0, ae - ae0
            se = d.std() / np.sqrt(len(d))
            ok = d.mean() > 2 * se
            if ok:
                kept.append(g)
            rep.append(f'| {g} | {d.mean():+.4f} ± {se:.4f} | {da.mean():+.3f} ± {da.std() / np.sqrt(len(da)):.3f} | {"yes" if ok else "no"} |')
            print(stat, g, f'{d.mean():+.4f} ± {se:.4f}', flush=True)
        keep[stat] = kept
        rep.append('')


def volatility(cache):
    f = pd.read_parquet(f'{cache}/frame.parquet', columns=['game', 'player_id', 'dt', 'D', 'M', 'T', 'G']).sort_values('dt')
    p = f.groupby('player_id', sort=False)
    out = f[['game', 'player_id']].copy()
    for s in 'DMTG':
        sd = p[s].transform(lambda x: x.shift(1).rolling(10, min_periods=5).std())
        mean = p[s].transform(lambda x: x.shift(1).rolling(10, min_periods=5).mean())
        out[f'cv_{s}'] = (sd / mean.replace(0, np.nan)).clip(0, 3)
    return out


def fit_spread_model(y, mu, x):
    """a = exp(c0 + c1 log mu + c2 x), by maximum likelihood."""
    def nll(c):
        a = np.exp(np.clip(c[0] + c[1] * np.log(mu) + c[2] * x, -12, 3))
        return -nb_logpmf(y, mu, a).sum()
    return optimize.minimize(nll, x0=[np.log(0.05), 0.0, 0.0], method='Nelder-Mead', options={'maxiter': 2000}).x


def spread_test(cache, rep):
    wf = pd.read_parquet(f'{cache}/walkforward.parquet').merge(volatility(cache), on=['game', 'player_id'], how='left')
    rep += ['## A spread that depends on the player', '',
            'Spread = exp(c0 + c1 x log projection + c2 x the player\'s own recent volatility (sd / mean of his last 10)), '
            'fitted on 2024\'s out-of-sample projections, scored on 2025-2026 against the spread the walk-forward uses now '
            '(per position for disposals, one spread for the rest).', '',
            '| stat | c1 (projection) | c2 (volatility) | log-lik change | kept |', '|---|---|---|---|---|']
    res = {}
    for s, label in STATS.items():
        d = wf.dropna(subset=[s, f'mu_{s}', f'cv_{s}'])
        tu, te = d[d.season == 2024], d[d.season.isin([2025, 2026])]
        c = fit_spread_model(tu[s].to_numpy(), tu[f'mu_{s}'].to_numpy(), tu[f'cv_{s}'].to_numpy())
        a_new = np.exp(np.clip(c[0] + c[1] * np.log(te[f'mu_{s}']) + c[2] * te[f'cv_{s}'], -12, 3))
        diff = nb_logpmf(te[s].to_numpy(), te[f'mu_{s}'].to_numpy(), a_new.to_numpy()) - \
            nb_logpmf(te[s].to_numpy(), te[f'mu_{s}'].to_numpy(), te[f'a_{s}'].to_numpy())
        se = diff.std() / np.sqrt(len(diff))
        ok = diff.mean() > 2 * se
        res[s] = {'c': c.tolist(), 'kept': bool(ok)}
        rep.append(f'| {label} | {c[1]:+.3f} | {c[2]:+.3f} | {diff.mean():+.4f} ± {se:.4f} | {"yes" if ok else "no"} |')
        print(s, 'spread model', c, f'{diff.mean():+.4f} ± {se:.4f}', flush=True)
    rep.append('')
    return res


def run(cache, out_md):
    base = P.team_expected_score(pd.read_parquet(f'{cache}/frame.parquet'))
    rep = ['# Research ideas, tested without bookmaker lines', '',
           'From docs/RESEARCH_BEST_MODEL.md. Fitted 2013-2023, tuned 2024, scored 2025-2026 (never seen), paired per '
           'player-game, ± one standard error. Kept where more than two standard errors better. The market view of the game '
           'exists from 2017 (Squiggle "Punters"); earlier rows carry none and the model treats them as unknown.', '',
           '## New inputs', '']
    keep = {}
    feature_tests(base, cache, rep, keep)
    spread = spread_test(cache, rep)
    open(out_md, 'w').write('\n'.join(rep) + '\n')
    json.dump({'inputs': keep, 'spread': spread}, open(f'{cache}/research_kept.json', 'w'), indent=1)
    print('\n'.join(rep))


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else 'afl/cache', sys.argv[2] if len(sys.argv) > 2 else 'afl/docs/RESEARCH_TESTS.md')
