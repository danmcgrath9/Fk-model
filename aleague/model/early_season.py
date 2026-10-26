"""Early-season shrinkage of team strengths, plain and by squad continuity.

The team model is weakest in a season's first matches (head-to-head log loss gain over base rates 0.007
in the first 30 matches against 0.047 after 100, 2015-16 to 2022-23): A-League squads turn over heavily,
so last season's strengths mislead. Two candidates, applied to each club's attack and defence at
prediction time:
  plain       strength x (1 - alpha x exp(-n / tau)), n = the club's league matches so far this season
  continuity  the same, with alpha x (1 - continuity), continuity = share of the club's minutes LAST
              season played by players who have already played for it THIS season (before this match),
              or, for its first match, who are in its named starting XI (known at teams-named time)
alpha and tau are chosen on the tune seasons and checked on the confirm seasons; the newest seasons are
shown for information (the team model was looked at on them before).

Usage: python -m aleague.model.early_season <tables dir> <report.md>
"""
import itertools
import json
import os
import sys

import numpy as np
import pandas as pd

from aleague.model.evaluate import boot_diff, week_of
from aleague.model.markets import h2h, score_matrix
from aleague.model.team import Fit, fit, refit_level_and_home, training_rows, weights

SETTINGS = os.path.join(os.path.dirname(__file__), 'settings.json')
TUNE, CONFIRM, SEEN = [2016, 2017, 2018, 2019, 2020], [2021, 2022, 2023], [2024, 2025, 2026]


def continuity_table(pg, matches):
    """(match_id, team) -> share of last season's team minutes by players already used this season."""
    pg = pg[pg.match_id.notna()].sort_values(['date', 'match_id'])
    last_mins = pg.groupby(['team', 'season', 'player_id']).minutes.sum()
    out = {}
    for (team, season), g in pg.groupby(['team', 'season'], sort=False):
        try:
            prev = last_mins.loc[(team, season - 1)]
        except KeyError:
            continue  # a new club: no last season
        total = prev.sum()
        used = set()
        for mid, x in g.groupby('match_id', sort=False):
            # this match's starting XI counts (teams named), plus everyone used before it
            seen = used | set(x.player_id[x.starter])
            out[(mid, team)] = prev[prev.index.isin(seen)].sum() / total
            used |= set(x.player_id[x.minutes > 0])
    return out


def predictions(matches, seasons, s, cont, alphas, taus, mode):
    """{(alpha, tau): DataFrame of probabilities}, one fit per day shared across the grid."""
    played = matches[matches.home_goals_90.notna()]
    target = played[played.season.isin(seasons)]
    n_so_far = {}
    out = {k: [] for k in itertools.product(alphas, taus)}
    prev = None
    for day, games in target.groupby('date', sort=True):
        rows = training_rows(matches, day)
        season_now = int(games.season.iloc[0])
        prev = fit(rows, weights(rows, day, season_now, s['half_life'], s['carry']), s['reg'], start=prev)
        age = np.array([(day - d).days for d in rows.date], dtype=float)
        cur = refit_level_and_home(Fit(prev.teams, prev.mu, prev.home, list(prev.att.values()), list(prev.dfn.values())),
                                   rows, 0.5 ** (age / s['home_half_life']))
        for _, g in games.iterrows():
            nh = n_so_far.get((g.season, g.home), 0)
            na = n_so_far.get((g.season, g.away), 0)
            for (alpha, tau) in out:
                def k(team, n):
                    c = cont.get((g.match_id, team), 0.5) if mode == 'continuity' else 0.0
                    return 1 - alpha * (1 - c) * np.exp(-n / tau)
                kh, ka = k(g.home, nh), k(g.away, na)
                ah, dh = cur.att.get(g.home, 0) * kh, cur.dfn.get(g.home, 0) * kh
                aa, da = cur.att.get(g.away, 0) * ka, cur.dfn.get(g.away, 0) * ka
                hadv = 0 if g.neutral else cur.home
                lh, la = np.exp(cur.mu + ah + da + hadv), np.exp(cur.mu + aa + dh)
                r = h2h(score_matrix(lh, la, s['rho']))
                out[(alpha, tau)].append(dict(match_id=g.match_id, season=g.season, date=g.date,
                                              hg=g.home_goals_90, ag=g.away_goals_90, n=min(nh, na),
                                              ph=r['home'], pd=r['draw'], pa=r['away']))
        for _, g in games.iterrows():
            n_so_far[(g.season, g.home)] = n_so_far.get((g.season, g.home), 0) + 1
            n_so_far[(g.season, g.away)] = n_so_far.get((g.season, g.away), 0) + 1
    return {k: pd.DataFrame(v) for k, v in out.items()}


def ll(df):
    y = np.where(df.hg > df.ag, 0, np.where(df.hg == df.ag, 1, 2))
    P = df[['ph', 'pd', 'pa']].to_numpy()
    return -np.log(np.clip(P[np.arange(len(y)), y], 1e-12, 1))


def main(tables, report):
    s = json.load(open(SETTINGS))
    m = pd.read_parquet(f'{tables}/matches.parquet')
    pg = pd.read_parquet(f'{tables}/player_games.parquet')
    cont = continuity_table(pg, m)
    seasons = TUNE + CONFIRM + SEEN
    lines = ['# Early-season shrinkage of team strengths', '',
             'Head-to-head log loss, lower is better. alpha 0 is the current model. Chosen on the tune seasons.', '']
    for mode in ('plain', 'continuity'):
        preds = predictions(m, seasons, s, cont, [0.0, 0.25, 0.5, 0.75], [3.0, 6.0, 12.0], mode)
        rows = []
        for (alpha, tau), df in preds.items():
            L = ll(df)
            rows.append(dict(alpha=alpha, tau=tau, **{name: L[df.season.isin(b).to_numpy()].mean()
                                                      for name, b in (('tune', TUNE), ('confirm', CONFIRM), ('seen', SEEN))}))
        res = pd.DataFrame(rows).sort_values('tune')
        best = res.iloc[0]
        base = preds[(0.0, 3.0)]
        cand = preds[(best.alpha, best.tau)]
        lines += [f'## {mode}', '', res.round(4).to_markdown(index=False), '',
                  f'Chosen: alpha {best.alpha}, tau {best.tau}.', '',
                  '| seasons | first 10 club matches: current | chosen | all matches: difference (90% interval) |',
                  '|---|---|---|---|']
        for name, b in (('confirm', CONFIRM), ('seen', SEEN)):
            k = base.season.isin(b).to_numpy()
            early = k & (base.n < 10).to_numpy()
            d, lo, hi = boot_diff(ll(cand)[k], ll(base)[k], week_of(base.date[k].to_numpy()))
            lines.append(f'| {name} | {ll(base)[early].mean():.4f} | {ll(cand)[early].mean():.4f} | '
                         f'{d:+.4f} ({lo:+.4f} to {hi:+.4f}) |')
        lines.append('')
    text = '\n'.join(lines) + '\n'
    open(report, 'w').write(text)
    print(text)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
