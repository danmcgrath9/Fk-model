"""Attack and defence ratings per player, from points scored and conceded (games before each round only).

Each side's score in each game = league level + home edge + sum of its 17's ATTACK ratings + sum of the other 17's
DEFENCE ratings (a good defender has a negative rating), starters counted in full and the bench at BENCH_WEIGHT, older
games down-weighted with the same half-life as the margin ratings, every rating shrunk toward zero (ridge).
Per team-game: att_named (own 17's attack), def_named (own 17's defence, points it lets in), the same over the previous
game's 17 (_open). Writes nrl/cache/player_attdef.parquet.
"""
import sys

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.linear_model import Ridge

from nrl.model.player_ratings import BENCH_WEIGHT, FIRST_SEASON, HALF_LIFE_DAYS
from nrl.model.team_frame import load

ALPHA = float(__import__('os').environ.get('AD_ALPHA', '60'))


def main(cache):
    m, pm = load(cache)
    m = m.reset_index(drop=True)
    m = m[~m.upcoming].reset_index(drop=True) if 'upcoming' in m else m
    players = np.sort(pm.player_id.unique())
    col = {p: j for j, p in enumerate(players)}
    P = len(players)
    num = pd.to_numeric(pm.number, errors='coerce')
    pm = pm.assign(w=np.where(num <= 13, 1.0, BENCH_WEIGHT))
    gi = dict(zip(m.match_id, range(len(m))))
    pm = pm[pm.match_id.isin(gi)]
    home = dict(zip(m.match_id, m.home_team))
    # two rows per game: row 2g = home side's score, row 2g+1 = away side's score
    is_home = (pm.team.to_numpy() == pm.match_id.map(home).to_numpy())
    g = pm.match_id.map(gi).to_numpy()
    c = pm.player_id.map(col).to_numpy()
    w = pm.w.to_numpy()
    rows_att = 2 * g + np.where(is_home, 0, 1)          # a player attacks in his own side's row
    rows_def = 2 * g + np.where(is_home, 1, 0)          # and defends in the other side's row
    X = sparse.csr_matrix((np.r_[w, w], (np.r_[rows_att, rows_def], np.r_[c, c + P])), shape=(2 * len(m), 2 * P))
    hcol = sparse.csr_matrix(np.tile([[10.0], [0.0]], (len(m), 1)))      # home edge, barely penalised
    X = sparse.hstack([X, hcol]).tocsr()
    y = np.ravel(np.column_stack([m.home_team_score, m.away_team_score]))
    ko = np.repeat(m.kick_off.to_numpy(), 2)
    m['round_key'] = m.season.astype(str) + ' ' + m['round'].astype(str)
    first = m.groupby('round_key', sort=False).kick_off.min().sort_values()
    by_match = {k: v for k, v in pm.groupby('match_id')}
    prev = {}
    out = []
    for rk, start in first.items():
        idx = m.index[m.round_key == rk]
        past = np.where(ko < np.datetime64(start))[0]
        rating = None
        if m.loc[idx[0], 'season'] >= FIRST_SEASON and len(past) > 400:
            age = (np.datetime64(start) - ko[past]).astype('timedelta64[D]').astype(float)
            sw = 0.5 ** (age / HALF_LIFE_DAYS)
            yy = y[past]
            r = Ridge(alpha=ALPHA, fit_intercept=True, solver='sparse_cg').fit(X[past], yy, sample_weight=sw)
            rating = r.coef_[:-1]
        for i in idx:
            mid = m.at[i, 'match_id']
            for team, tg in by_match[mid].groupby('team'):
                lst = list(zip(tg.player_id, tg.w))
                if rating is not None:
                    att = float(sum(rating[col[p]] * ww for p, ww in lst))
                    dfn = float(sum(rating[col[p] + P] * ww for p, ww in lst))
                    pv = prev.get(team)
                    att_o = float(sum(rating[col[p]] * ww for p, ww in pv)) if pv else np.nan
                    dfn_o = float(sum(rating[col[p] + P] * ww for p, ww in pv)) if pv else np.nan
                    out.append(dict(match_id=mid, team=team, att_named=att, def_named=dfn, att_open=att_o, def_open=dfn_o))
                prev[team] = lst
    df = pd.DataFrame(out)
    df.to_parquet(f'{cache}/player_attdef.parquet', index=False)
    print(f'player_attdef: {len(df):,} team-games')


if __name__ == '__main__':
    main(sys.argv[1])
