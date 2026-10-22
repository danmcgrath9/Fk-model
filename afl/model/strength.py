"""Player value and lineup strength, on AFL Player Ratings.

Value of a player-game = his AFL Player Rating points (Fryzigg, 2012-2025). Where no rating exists (all of 2026, which
Fryzigg has not published, and the odd unmatched row) a stand-in is predicted from the same game's Footywire box score,
fitted on seasons up to 2024 and checked on 2025, where the real ratings are known (see rating_proxy_check).

Strength going into a game = recency-weighted average of his past values, pulled toward a replacement level when he has
played few games (a debutant is not assumed to be average). Two lineup measures per team per game:
  named  the players who took the field, valued as they stood before the game
  open   last week's side less anyone subbed off injured, valued after last week: what was knowable when books open,
         before team news
"""
import glob

import lightgbm as lgb
import numpy as np
import pandas as pd

from afl.model.frame import _key

FRYZIGG_TEAM = {'Brisbane Lions': 'Brisbane', 'Greater Western Sydney': 'GWS', 'Footscray': 'Western Bulldogs'}
BOX = ['D', 'K', 'HB', 'M', 'G', 'B', 'T', 'HO', 'GA', 'I50', 'CL', 'CG', 'R50', 'FF', 'FA', 'AF', 'SC', 'CP', 'UP', 'ED',
       'DE', 'CM', 'MI5', 'OP', 'BO', 'TOG', 'MG', 'SI', 'TO', 'ITC', 'T5', 'CCL', 'SCL']
HALFLIFE = 8          # games
REPLACEMENT = 6.0     # rating points a fringe player is worth (about the 30th percentile of a game)
PRIOR_GAMES = 5       # weight of the replacement level, in games


def attach_ratings(m, cache):
    fz = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f'{cache}/fryzigg_*.parquet'))], ignore_index=True)
    fz['date'] = pd.to_datetime(fz.match_date).dt.strftime('%Y-%m-%d')
    fz['team'] = fz.player_team.replace(FRYZIGG_TEAM)
    fz['key'] = (fz.player_first_name.fillna('') + ' ' + fz.player_last_name.fillna('')).map(_key)
    fz = fz.drop_duplicates(['date', 'team', 'key'])
    m = m.copy()
    m['key'] = m.Player.map(_key)
    m = m.merge(fz[['date', 'team', 'key', 'rating_points', 'match_weather_type', 'match_weather_temp_c']],
                on=['date', 'team', 'key'], how='left')
    return m


def rating_proxy(m):
    """Predict rating points from the same game's box score; returns the model and its 2025 check."""
    x = m.assign(won=(m.margin > 0).astype(float))
    cols = BOX + ['margin', 'won']
    tr = x[(x.season <= 2024) & x.rating_points.notna()]
    te = x[(x.season == 2025) & x.rating_points.notna()]
    mdl = lgb.LGBMRegressor(n_estimators=600, learning_rate=0.05, num_leaves=63, min_child_samples=100,
                            subsample=0.8, subsample_freq=1, colsample_bytree=0.8, verbose=-1, random_state=3)
    mdl.fit(tr[cols], tr.rating_points)
    pred = mdl.predict(te[cols])
    r2 = 1 - ((te.rating_points - pred) ** 2).sum() / ((te.rating_points - te.rating_points.mean()) ** 2).sum()
    check = dict(r2_2025=float(r2), mae_2025=float(np.abs(te.rating_points - pred).mean()),
                 corr_2025=float(np.corrcoef(te.rating_points, pred)[0, 1]), rows_2025=int(len(te)))
    return mdl, cols, check


def player_values(m):
    """value per player-game, then pre-game and post-game strength."""
    mdl, cols, check = rating_proxy(m)
    m = m.copy()
    m['won'] = (m.margin > 0).astype(float)
    m['rp_hat'] = mdl.predict(m[cols])
    m['value'] = m.rating_points.fillna(m.rp_hat)
    m['value_is_proxy'] = m.rating_points.isna()
    m = m.sort_values(['dt', 'game']).reset_index(drop=True)
    p = m.groupby('player_id', sort=False)
    ew_pre = p.value.transform(lambda s: s.shift(1).ewm(halflife=HALFLIFE, min_periods=1).mean())
    ew_post = p.value.transform(lambda s: s.ewm(halflife=HALFLIFE, min_periods=1).mean())
    n_pre = p.cumcount()
    n_post = n_pre + 1
    m['str_pre'] = ((ew_pre.fillna(REPLACEMENT) * n_pre + REPLACEMENT * PRIOR_GAMES) / (n_pre + PRIOR_GAMES))
    m['str_post'] = (ew_post * n_post + REPLACEMENT * PRIOR_GAMES) / (n_post + PRIOR_GAMES)
    return m.drop(columns=['won']), check


def lineup_strength(m):
    rows = []
    for team, g in m.groupby('team', sort=False):
        order = g.drop_duplicates('game').sort_values('dt').game.tolist()
        by = {k: v for k, v in g.groupby('game')}
        prev = None
        for gm in order:
            cur = by[gm]
            named = cur.str_pre.nlargest(22).sum()
            if prev is None:
                opn, n_out, n_in = np.nan, np.nan, np.nan
            else:
                was = by[prev]
                exp = was[was.subbed_off != 1]
                top = exp.str_post.nlargest(22)
                # a spot left by an injured player is filled by someone; value him at replacement level
                opn = top.sum() + REPLACEMENT * (22 - len(top))
                n_out = float((~was.player_id.isin(cur.player_id)).sum())
                n_in = float((~cur.player_id.isin(was.player_id)).sum())
            rows.append((gm, team, named, opn, n_out, n_in))
            prev = gm
    out = pd.DataFrame(rows, columns=['game', 'team', 'named_val', 'open_val', 'n_out', 'n_in'])
    out['news_val'] = out.named_val - out.open_val      # what team news changed, in rating points
    return out
