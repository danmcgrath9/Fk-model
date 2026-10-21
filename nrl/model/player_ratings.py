"""Player ratings from margins: what each player adds to his side's margin, from games already played.

For the games of one round, a ridge regression is fitted on every earlier game (never the round
itself): margin = sum of the home 17's ratings - sum of the away 17's + home advantage, with starters
(jerseys 1-13) counted in full and the bench at BENCH_WEIGHT, older games down-weighted with a
HALF_LIFE, and every rating shrunk toward zero (an unknown player is an average one). From those
ratings, per team-game:

  strength_named  the sum over the 17 who took the field in this game
  strength_open   the sum over the 17 who took the field in the team's previous game (knowable when
                  books open, before Tuesday's lists)

Usage: python -m nrl.model.player_ratings nrl/cache  -> nrl/cache/player_strength.parquet
"""
import sys

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.linear_model import Ridge

from nrl.model.team_frame import load

HALF_LIFE_DAYS = 900
BENCH_WEIGHT = 0.5
ALPHA = 60.0
FIRST_SEASON = 2001


def design(m, pm, players):
    col = {p: j for j, p in enumerate(players)}
    gi = dict(zip(m.match_id, range(len(m))))
    home_team = dict(zip(m.match_id, m.home_team))
    num = pd.to_numeric(pm.number, errors='coerce')
    w = np.where(num <= 13, 1.0, BENCH_WEIGHT)
    sign = np.where(pm.team.to_numpy() == pm.match_id.map(home_team).to_numpy(), 1.0, -1.0)
    rows = pm.match_id.map(gi).to_numpy()
    cols = pm.player_id.map(col).to_numpy()
    X = sparse.csr_matrix((sign * w, (rows, cols)), shape=(len(m), len(players)))
    return X


def main(cache):
    m, pm = load(cache)
    m = m.reset_index(drop=True)
    players = np.sort(pm.player_id.unique())
    X = design(m, pm, players)
    # home advantage as one more column, barely penalised: scale it up so ridge leaves it almost alone
    Xh = sparse.hstack([X, sparse.csr_matrix(np.full((len(m), 1), 10.0))]).tocsr()
    y = (m.home_team_score - m.away_team_score).to_numpy(float)
    m['round_key'] = m.season.astype(str) + ' ' + m['round'].astype(str)
    num = pd.to_numeric(pm.number, errors='coerce')
    pm = pm.assign(w=np.where(num <= 13, 1.0, BENCH_WEIGHT))
    col = {p: j for j, p in enumerate(players)}
    by_match = {k: v for k, v in pm.groupby('match_id')}
    out = []
    prev_17 = {}
    order = m[m.season >= FIRST_SEASON - 3]
    first = order.groupby('round_key', sort=False).kick_off.min().sort_values()
    for rk, start in first.items():
        idx = m.index[(m.round_key == rk)]
        past = m.index[(m.kick_off < start) & ~m.upcoming]
        if m.loc[idx[0], 'season'] >= FIRST_SEASON and len(past) > 200:
            age = (start - m.loc[past, 'kick_off']).dt.days.to_numpy()
            sw = 0.5 ** (age / HALF_LIFE_DAYS)
            r = Ridge(alpha=ALPHA, fit_intercept=False, solver='sparse_cg').fit(Xh[past], y[past], sample_weight=sw)
            rating = r.coef_[:-1]
        else:
            rating = None
        for i in idx:
            mid = m.at[i, 'match_id']
            for team, tg in by_match[mid].groupby('team'):
                if rating is not None:
                    named = float(sum(rating[col[p]] * w for p, w in zip(tg.player_id, tg.w)))
                    prev = prev_17.get(team)
                    opened = float(sum(rating[col[p]] * w for p, w in prev)) if prev else np.nan
                    out.append(dict(match_id=mid, team=team, strength_named=named, strength_open=opened))
                prev_17[team] = list(zip(tg.player_id, tg.w))
    df = pd.DataFrame(out)
    df.to_parquet(f'{cache}/player_strength.parquet', index=False)
    print(f'player_strength: {len(df):,} team-games')


if __name__ == '__main__':
    main(sys.argv[1])
