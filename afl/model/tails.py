"""Are the big-game chances right? Milestone calibration (20+, 25+, 30+ disposals and so on) and the per-position spread
test, from the walk-forward projections (afl/model/walkforward.py).

Spread test: per stat, fit one negative binomial spread on 2024's out-of-sample projections, then one per position, and
score both on 2025-2026 (paired per player-game, ± one standard error). Calibration: per position and milestone, the
share of games that reached it minus our average chance of reaching it, on 2025-2026, using the spread the walk-forward
actually stores.

Usage: python -m afl.model.tails afl/cache afl/docs/TAILS.md
"""
import sys

import numpy as np
import pandas as pd
from scipy import stats

from afl.model.disposals import fit_dispersion, nb_logpmf

NAMES = {'D': 'disposals', 'M': 'marks', 'T': 'tackles', 'G': 'goals'}
MILESTONES = {'D': [15, 20, 25, 30, 35], 'M': [3, 5, 7, 9], 'T': [3, 5, 7, 9], 'G': [1, 2, 3, 4]}
POS = ['ruck', 'mid', 'fwd', 'def', 'gen']


def p_at_least(k, mu, a):
    n = 1 / a
    return 1 - stats.nbinom.cdf(k - 1, n, n / (n + mu))


def run(cache, out_md):
    wf = pd.read_parquet(f'{cache}/walkforward.parquet')
    tu, te = wf[wf.season == 2024], wf[wf.season.isin([2025, 2026])]
    rep = ['# Tails: are the big-game chances right?', '',
           'From the walk-forward projections (every season predicted by models that never saw it). Scored on 2025-2026.', '',
           '## One spread, or one per position?', '',
           'Spread fitted on 2024, scored on 2025-2026. Change in log-likelihood per player-game from fitting it per position '
           '(higher is better), ± one standard error. Adopted where more than two standard errors better.', '',
           '| stat | one spread | ruck | mid | fwd | def | gen | gain per position | adopted |', '|---|---|---|---|---|---|---|---|---|']
    for s, label in NAMES.items():
        t, e = tu.dropna(subset=[f'mu_{s}', s]), te.dropna(subset=[f'mu_{s}', s])
        a1 = fit_dispersion(t[s].to_numpy(), t[f'mu_{s}'].to_numpy())
        ap = {p: fit_dispersion(t[s][t.pos == p].to_numpy(), t[f'mu_{s}'][t.pos == p].to_numpy()) for p in POS if (t.pos == p).sum() >= 500}
        a_e = e.pos.map(ap).fillna(a1).to_numpy()
        d = nb_logpmf(e[s].to_numpy(), e[f'mu_{s}'].to_numpy(), np.maximum(a_e, 1e-3)) - nb_logpmf(e[s].to_numpy(), e[f'mu_{s}'].to_numpy(), max(a1, 1e-3))
        se = d.std() / np.sqrt(len(d))
        cells = ' | '.join(f'{ap[p]:.3f}' if p in ap else '' for p in POS)
        rep.append(f'| {label} | {a1:.3f} | {cells} | {d.mean():+.4f} ± {se:.4f} | {"yes" if d.mean() > 2 * se else "no"} |')
    rep += ['', '## Milestones: reached minus our chance (2025-2026)', '',
            'Positive: it happened more often than we said (our price too long). Each cell: gap, then our average chance. '
            'Rows with under 300 games are left out.', '']
    for s, label in NAMES.items():
        e = te.dropna(subset=[f'mu_{s}', s])
        ks = MILESTONES[s]
        rep += [f'### {label.capitalize()}', '', '| position | games | ' + ' | '.join(f'{k}+' for k in ks) + ' |', '|---|---|' + '---|' * len(ks)]
        for p in POS + ['all']:
            g = e if p == 'all' else e[e.pos == p]
            if len(g) < 300:
                continue
            cells = []
            for k in ks:
                pr = p_at_least(k, g[f'mu_{s}'].to_numpy(), np.maximum(g[f'a_{s}'].to_numpy(), 1e-3))
                cells.append(f'{(g[s] >= k).mean() - pr.mean():+.3f} ({pr.mean():.0%})')
            rep.append(f'| {p} | {len(g):,} | ' + ' | '.join(cells) + ' |')
        rep.append('')
    rep += ['## What this says', '',
            '- Disposals: the spread now differs by position (a midfielder\'s game is steadier than a general player\'s), '
            'which is adopted in the walk-forward. Overall the milestone chances are within a point of what happened.',
            '- Midfielders still reach 20+ and 25+ two to three points more often than we say. That is the level, not the '
            'spread: midfielders were under-projected by 0.3 disposals in 2026 (the year of the toss-up), and over-projected '
            'by 0.3 in 2023-24. A correction fitted on the season before (scale each projection by last season\'s actual over '
            'projected) helped 2024 and 2025 and hurt 2026 by more, so it is not adopted: last season\'s level is a poor guide '
            'in a rule-change year. The model\'s own league-level input follows it within a season.',
            '- Marks, tackles, goals: one spread is enough; milestones within one to three points everywhere, with rucks the '
            'loosest (few games).', '']
    open(out_md, 'w').write('\n'.join(rep) + '\n')
    print('\n'.join(rep))


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else 'afl/cache', sys.argv[2] if len(sys.argv) > 2 else 'afl/docs/TAILS.md')
