"""Candidate improvements from docs/RESEARCH.md, tested out of sample.

Every candidate makes each match's probabilities from earlier information only:
  dc            the frozen team model (settings.json)
  dc_home{N}    the same, with the league level and home edge re-estimated on an N-day half-life
  dc_recal      dc's expected goal difference fed through an ordered logit fitted on every EARLIER
                season's out-of-sample predictions (Goddard 2005's hybrid; aims at the overrated favourites)
  pi            pi-ratings (Constantinou & Fenton 2013: separate home and away ratings, updated by a
                diminishing function of the goal-difference error), through an ordered logit fitted the
                same way
  elo           rolling Elo (aleague/model/evaluate.py)
  ens           an equal-weight geometric mean of dc_recal, pi and elo, renormalised

Seasons: choices are made on 2015-16 to 2022-23 (tune and confirm). The three newest seasons were
already looked at for step 1, so their figures here are indicative, not a clean test; the clean test of
anything adopted now is 2026-27 as it is played.

Usage: python -m aleague.model.experiments <tables dir> <report.md>
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from aleague.model.evaluate import boot_diff, elo, losses, week_of
from aleague.model.team import rolling_predictions

SELECT = list(range(2016, 2024))
SPENT = [2024, 2025, 2026]
SETTINGS = os.path.join(os.path.dirname(__file__), 'settings.json')


def outcome(df):
    return np.where(df.home_goals > df.away_goals, 0, np.where(df.home_goals == df.away_goals, 1, 2))


def ordered_logit_fit(x, y):
    """P(away) = s(c1 - b x), P(away or draw) = s(c2 - b x); y: 0 home, 1 draw, 2 away."""
    def nll(t):
        b, c1, d = t
        c2 = c1 + np.exp(d)
        pa = 1 / (1 + np.exp(-(c1 - b * x)))
        pad = 1 / (1 + np.exp(-(c2 - b * x)))
        p = np.where(y == 2, pa, np.where(y == 1, pad - pa, 1 - pad))
        return -np.log(np.clip(p, 1e-12, 1)).sum()
    return minimize(nll, np.array([1.0, -0.5, 0.0]), method='Nelder-Mead', options=dict(maxiter=4000)).x


def ordered_logit_predict(t, x):
    b, c1, d = t
    c2 = c1 + np.exp(d)
    pa = 1 / (1 + np.exp(-(c1 - b * x)))
    pad = 1 / (1 + np.exp(-(c2 - b * x)))
    return np.column_stack([1 - pad, pad - pa, pa])


def by_earlier_seasons(df, feature):
    """Fit the ordered logit on all earlier seasons' rows, predict this season's: no look-ahead."""
    out = df.copy()
    P = np.full((len(df), 3), np.nan)
    for s in sorted(df.season.unique()):
        past = df[df.season < s]
        if len(past) < 200:
            continue
        t = ordered_logit_fit(past[feature].to_numpy(), outcome(past))
        k = (df.season == s).to_numpy()
        P[k] = ordered_logit_predict(t, df.loc[k, feature].to_numpy())
    out['p_home'], out['p_draw'], out['p_away'] = P[:, 0], P[:, 1], P[:, 2]
    return out[~np.isnan(P[:, 0])]


def pi_ratings(matches, lam=0.035, gamma=0.7):
    """Pre-match expected goal difference from pi-ratings, for every played match in date order."""
    played = matches[matches.home_goals_90.notna()].sort_values(['date', 'match_id'])
    hr, ar, rows = {}, {}, []

    def g(r):
        return np.sign(r) * (10 ** (abs(r) / 3) - 1)

    for _, m in played.iterrows():
        h, a = m.home, m.away
        egd = g(hr.get(h, 0.0)) - g(ar.get(a, 0.0))
        rows.append(dict(match_id=m.match_id, pi_gd=egd))
        e = (m.home_goals_90 - m.away_goals_90) - egd
        psi = np.sign(e) * 3 * np.log10(1 + abs(e))
        hr[h] = hr.get(h, 0.0) + lam * psi
        ar[h] = ar.get(h, 0.0) + gamma * lam * psi
        ar[a] = ar.get(a, 0.0) - lam * psi
        hr[a] = hr.get(a, 0.0) - gamma * lam * psi
    return pd.DataFrame(rows)


def pool(frames, names):
    base = frames[names[0]][['match_id', 'season', 'date', 'home_goals', 'away_goals']]
    logs = []
    for n in names:
        f = frames[n].set_index('match_id').reindex(base.match_id)
        logs.append(np.log(np.clip(f[['p_home', 'p_draw', 'p_away']].to_numpy(dtype=float), 1e-12, 1)))
    P = np.exp(np.mean(logs, axis=0))
    P = P / P.sum(axis=1, keepdims=True)
    out = base.copy()
    out['p_home'], out['p_draw'], out['p_away'] = P[:, 0], P[:, 1], P[:, 2]
    return out


def main(tables, report):
    m = pd.read_parquet(f'{tables}/matches.parquet')
    s = json.load(open(SETTINGS))
    seasons = list(range(2015, 2027))
    frames = {}
    frames['dc'] = rolling_predictions(m, seasons, **s)
    for hl in (60, 120, 240):
        frames[f'dc_home{hl}'] = rolling_predictions(m, seasons, home_half_life=hl, **s)
    d = frames['dc'].copy()
    d['xgd'] = np.log(d.lam_home) - np.log(d.lam_away)
    frames['dc_recal'] = by_earlier_seasons(d, 'xgd')
    pi = pi_ratings(m).merge(frames['dc'][['match_id', 'season', 'date', 'home_goals', 'away_goals']], on='match_id')
    frames['pi'] = by_earlier_seasons(pi, 'pi_gd')
    frames['elo'] = elo(m, seasons)
    frames['ens'] = pool(frames, ['dc_recal', 'pi', 'elo'])

    common = set.intersection(*[set(f.match_id) for f in frames.values()])
    frames = {k: f[f.match_id.isin(common)].sort_values('match_id').reset_index(drop=True) for k, f in frames.items()}
    for f in frames.values():  # losses() wants the goal columns; only h2h is compared here
        f['p_over25'] = f.get('p_over25', 0.5)
        f['p_btts'] = f.get('p_btts', 0.5)
    L = {k: losses(f) for k, f in frames.items()}
    base = frames['dc']
    lines = ['# Team model, step 2: candidate improvements (head-to-head log loss)', '',
             'Every candidate predicts each match from earlier information only. Choices are made on 2016-17 to '
             '2022-23 (2015-16 is the warm-up the recalibrated candidates need); 2023-24 to 2025-26 were already seen in step 1, so they are indicative only.', '',
             '| candidate | 2016-17 to 2022-23 | vs dc (90% interval, by week) | 2023-24 to 2025-26 (seen) | vs dc |',
             '|---|---|---|---|---|']
    for k in frames:
        rows = []
        for block in (SELECT, SPENT):
            mask = base.season.isin(block).to_numpy()
            mean = L[k].ll_h2h[mask].mean()
            if k == 'dc':
                rows += [f'{mean:.4f}', '']
            else:
                dd, lo, hi = boot_diff(L[k].ll_h2h[mask], L['dc'].ll_h2h[mask], week_of(base.date[mask]))
                rows += [f'{mean:.4f}', f'{dd:+.4f} ({lo:+.4f} to {hi:+.4f})']
        lines.append(f'| {k} | ' + ' | '.join(rows) + ' |')
    # calibration of favourites, the step 1 weakness
    lines += ['', '## Home sides priced 50% or more: predicted against happened', '',
              '| candidate | block | games | predicted home win | happened |', '|---|---|---|---|---|']
    for k in ('dc', 'dc_home120', 'dc_recal', 'ens'):
        f = frames[k]
        for name, block in (('select', SELECT), ('seen', SPENT)):
            x = f[f.season.isin(block) & (f.p_home >= 0.5)]
            lines.append(f'| {k} | {name} | {len(x)} | {x.p_home.mean():.3f} | {(x.home_goals > x.away_goals).mean():.3f} |')
    hl = frames['dc_home120'].groupby('season').home_adv.mean()
    lines += ['', 'Fitted home edge (log goals) by season with a 120-day home half-life: '
              + ', '.join(f'{s - 1}-{str(s)[2:]} {v:.3f}' for s, v in hl.items()), '']
    text = '\n'.join(lines) + '\n'
    open(report, 'w').write(text)
    print(text)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
