"""The weekly price sheet: every game's margin and total, every player's projection and fair prices.

For a past round it reads the out-of-sample projections (afl/model/walkforward.py: the season predicted by models that
never saw it) and the team model's predictions, and adds the actual results so the sheet can be checked. For 2027 the
same sheet is built from named teams once a live line-up feed exists (see afl/README.md: the AFL site's terms rule out
its API, so the source is still to be chosen).

Fair price = 1 / our chance, no margin. Per player: our median (the line at which over and under are as close to even
as a .5 line allows), fair over/under at that line, anytime goal and 2+ goals, and the milestone markets books run
(disposals 20+/25+/30+, marks 5+, tackles 5+), each with its own table under the game.

Usage: python -m afl.sheet afl/cache 2026 24
"""
import sys

import numpy as np
import pandas as pd
from scipy import stats


def nb_cdf(k, mu, a):
    n = 1 / a
    return stats.nbinom.cdf(k, n, n / (n + mu))


def median_line(mu, a):
    ks = np.arange(0, 80)
    c = nb_cdf(ks[None, :], np.asarray(mu)[:, None], np.asarray(a)[:, None])
    return ks[np.abs(c - 0.5).argmin(1)] + 0.5


MILESTONES = [('D', 20), ('D', 25), ('D', 30), ('M', 5), ('T', 5)]


def fair(p):
    return np.where(p > 0, 1 / np.clip(p, 1e-6, 1), np.inf)


def build(cache, season, rnd):
    wf = pd.read_parquet(f'{cache}/walkforward.parquet')
    r = wf[(wf.season == season) & (wf.Round.astype(str) == str(rnd))].copy()
    if r.empty:
        raise SystemExit(f'no out-of-sample projections for {season} round {rnd}')
    for s in ('D', 'M', 'T'):
        r[f'line_{s}'] = median_line(r[f'mu_{s}'].to_numpy(), r[f'a_{s}'].to_numpy())
        p_over = 1 - nb_cdf(np.floor(r[f'line_{s}']), r[f'mu_{s}'], r[f'a_{s}'])
        r[f'over_{s}'], r[f'under_{s}'] = fair(p_over), fair(1 - p_over)
    p1 = 1 - nb_cdf(0, r.mu_G, r.a_G)
    p2 = 1 - nb_cdf(1, r.mu_G, r.a_G)
    r['anytime'], r['two_plus'], r['p_anytime'] = fair(p1), fair(p2), p1
    for s, k in MILESTONES:
        r[f'{s}{k}'] = fair(1 - nb_cdf(k - 1, r[f'mu_{s}'], r[f'a_{s}']))
    team = pd.read_parquet(f'{cache}/team_test_predictions.parquet')
    tm = team[(team.season == season) & (team.Round.astype(str) == str(rnd))][['game', 'home', 'away', 'm_open', 't_hat', 'home_margin', 'total']]
    return r, tm


def px(v):
    return '100+' if v >= 100 else f'{v:.2f}'


def to_markdown(r, tm, season, rnd):
    out = [f'# AFL price sheet: {season} round {rnd}', '',
           'Out-of-sample: every number below came from models that never saw this season. Fair prices carry no margin. '
           'Actual results are shown because this round is past; a live sheet has none.', '']
    for g in tm.sort_values('game').itertuples():
        hp = stats.norm.cdf(g.m_open / 33.9)
        out += [f'## {g.home} v {g.away}', '',
                f'Margin {g.home} {g.m_open:+.1f} (win chance {hp:.0%}, fair {1 / hp:.2f} / {1 / (1 - hp):.2f}); total {g.t_hat:.0f}. '
                f'Actual: {g.home} {g.home_margin:+.0f}, total {g.total:.0f}.', '',
                '| player | team | disposals line | over / under | actual | marks line | over / under | actual | tackles line | over / under | actual | goal anytime | 2+ | goals |',
                '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
        p = r[r.game == g.game].sort_values(['team', 'mu_D'], ascending=[True, False])
        for x in p.itertuples():
            out.append(f'| {x.Player} | {x.team} | {x.line_D} | {x.over_D:.2f} / {x.under_D:.2f} | {x.D:.0f} | {x.line_M} | {x.over_M:.2f} / {x.under_M:.2f} | {x.M:.0f} | '
                       f'{x.line_T} | {x.over_T:.2f} / {x.under_T:.2f} | {x.T:.0f} | {px(x.anytime)} | {px(x.two_plus)} | {x.G:.0f} |')
        out += ['', 'Milestones (fair price; players shorter than 15.00 for at least one):', '',
                '| player | 20+ disposals | 25+ | 30+ | 5+ marks | 5+ tackles |', '|---|---|---|---|---|---|']
        for x in p.itertuples():
            row = [getattr(x, f'{s}{k}') for s, k in MILESTONES]
            if min(row) < 15:
                out.append(f'| {x.Player} | ' + ' | '.join(px(v) for v in row) + ' |')
        out.append('')
    return '\n'.join(out) + '\n'


def run(cache, season, rnd):
    r, tm = build(cache, int(season), rnd)
    md = to_markdown(r, tm, season, rnd)
    path = f'afl/docs/SHEET_{season}_R{rnd}.md'
    open(path, 'w').write(md)
    r.to_csv(f'{cache}/sheet_{season}_R{rnd}.csv', index=False)
    print(md[:3000])


if __name__ == '__main__':
    run(*(sys.argv[1:4] if len(sys.argv) > 3 else ('afl/cache', 2026, 24)))
