"""Two ideas from the research (docs/RESEARCH_BEST_MODEL.md, rank 11) for the results-only rating behind exp_margin:

1. Learn from scoring shots, not only the score: goal-kicking accuracy is mostly luck from week to week, so a rating
   that updates on the shot margin (scoring shots x the league's points per shot) may track strength better. Matter of
   Stats reports that scoring forecasts against shot-based margins cut every forecaster's error. The update uses a blend:
   w x shot margin + (1 - w) x actual margin.
2. Home ground worth more when the away side has travelled interstate, less when the home side has.

Grid chosen on 2018-2023 (2013-2017 is burn-in), scored once on 2024-2026 against the actual margin, with Squiggle's
"Punters" (the market) and our current rating alongside.

Usage: python -m afl.model.team_ideas afl/cache afl/docs/TEAM_IDEAS.md
"""
import itertools
import sys

import numpy as np
import pandas as pd
from scipy import stats

from afl.model.team import CLUB_STATE, VENUE_STATE, bits


def games(cache):
    m = pd.read_parquet(f'{cache}/frame.parquet', columns=['game', 'dt', 'season', 'venue', 'team', 'opp', 'is_home', 'margin', 'G', 'B'])
    t = m.groupby(['game', 'dt', 'season', 'venue', 'team', 'opp', 'is_home', 'margin'], as_index=False)[['G', 'B']].sum()
    h, a = t[t.is_home == 1], t[t.is_home == 0][['game', 'G', 'B']]
    g = h.merge(a, on='game', suffixes=('_h', '_a')).sort_values('dt').reset_index(drop=True)
    g = g.rename(columns={'team': 'home', 'opp': 'away', 'margin': 'margin_home'})
    pts = (6 * (g.G_h + g.G_a) + g.B_h + g.B_a) / (g.G_h + g.G_a + g.B_h + g.B_a)
    pps = pts.shift(1).rolling(200, min_periods=50).mean().fillna(pts.mean())      # league points per shot, before the game
    g['shot_margin'] = ((g.G_h + g.B_h) - (g.G_a + g.B_a)) * pps
    g['away_trav'] = (g.away.map(CLUB_STATE) != g.venue.map(VENUE_STATE)).astype(float)
    g['home_trav'] = (g.home.map(CLUB_STATE) != g.venue.map(VENUE_STATE)).astype(float)
    mk = pd.read_parquet(f'{cache}/market_games.parquet')[['game', 'mkt_margin', 'mkt_p']]
    return g.merge(mk, on='game', how='left')


def rate(g, k, carry, w, hga, trav):
    r, season, out = {}, None, np.empty(len(g))
    for i, x in enumerate(g.itertuples()):
        if x.season != season:
            r = {t: carry * v for t, v in r.items()}
            season = x.season
        rh, ra = r.get(x.home, 0.0), r.get(x.away, 0.0)
        exp = rh - ra + hga + trav * (x.away_trav - x.home_trav)
        out[i] = exp
        target = w * x.shot_margin + (1 - w) * x.margin_home
        r[x.home] = rh + k * (target - exp)
        r[x.away] = ra - k * (target - exp)
    return out


def run(cache, out_md):
    g = games(cache)
    choose = g.season.between(2018, 2023).to_numpy()
    test = g.season.between(2024, 2026).to_numpy()
    grid = list(itertools.product((0.05, 0.065, 0.08, 0.1), (0.6, 0.7, 0.8), (0.0, 0.25, 0.5, 0.75, 1.0), (6.0, 8.0), (0.0, 6.0, 12.0)))
    best, rows = None, []
    for k, c, w, h, tr in grid:
        e = rate(g, k, c, w, h, tr)
        mae = np.abs(e[choose] - g.margin_home[choose]).mean()
        rows.append((k, c, w, h, tr, mae))
        if best is None or mae < best[-1]:
            best = (k, c, w, h, tr, mae)
    base = rate(g, 0.08, 0.7, 0.0, 8.0, 0.0)          # the rating in afl/model/frame.py today
    sd = np.std((base - g.margin_home)[g.season.between(2013, 2023)])
    k, c, w, h, tr, _ = best
    new = rate(g, k, c, w, h, tr)
    # the best with each idea switched off, to see what each adds
    def best_where(cond):
        r = [x for x in rows if cond(x)]
        return min(r, key=lambda x: x[-1])
    no_shots = best_where(lambda x: x[2] == 0.0)
    no_trav = best_where(lambda x: x[4] == 0.0)
    cands = {'current rating (K 0.08, carry 0.7, no shots, no travel)': base,
             f'best without shots (K {no_shots[0]}, carry {no_shots[1]}, travel {no_shots[4]})': rate(g, *no_shots[:5]),
             f'best without travel (K {no_trav[0]}, carry {no_trav[1]}, shots {no_trav[2]})': rate(g, *no_trav[:5]),
             f'best overall (K {k}, carry {c}, shots weight {w}, home {h}, travel {tr})': new}
    rep = ['# Results-only rating: learning from scoring shots, and travel', '',
           'Chosen on 2018-2023 by average margin miss; scored once on 2024-2026. Win chance = normal around the margin, '
           f'spread {sd:.1f}. Bits: Squiggle\'s score (higher is better). Punters = the betting market.', '',
           '| rating | 2024-26 margin miss | bits per game | change in bits vs current | ± |', '|---|---|---|---|---|']
    yb = g.margin_home[test].to_numpy()
    b0 = bits(stats.norm.cdf(base[test] / sd), yb)
    for name, e in cands.items():
        b = bits(stats.norm.cdf(e[test] / sd), yb)
        d = b - b0
        rep.append(f'| {name} | {np.abs(e[test] - yb).mean():.2f} | {b.mean():.4f} | {d.mean():+.4f} | {d.std() / np.sqrt(len(d)):.4f} |')
    mk = g[test & g.mkt_p.notna().to_numpy()]
    rep.append(f'| Punters (market), same games where present ({len(mk)}) | {np.abs(mk.mkt_margin - mk.margin_home).mean():.2f} | '
               f'{bits(mk.mkt_p, mk.margin_home).mean():.4f} | | |')
    rep += ['', 'Shots weight 1 means the rating learns from the shot margin alone; 0 from the score alone.', '']
    open(out_md, 'w').write('\n'.join(rep) + '\n')
    print('\n'.join(rep))
    return best


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else 'afl/cache', sys.argv[2] if len(sys.argv) > 2 else 'afl/docs/TEAM_IDEAS.md')
