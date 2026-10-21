"""Does weather help? Totals, anytime try scorer, run metres and tackles, with and without it.

Weather here is what actually happened (Open-Meteo archive, nrl/weather/pull.py). At bet time only a
forecast exists, so any gain is an upper bound on what a forecast can add. Roofed grounds count as dry and
still. Judged on DEV and CONFIRM only: the final seasons were already scored once (21 Oct 2026), so they
cannot vote on a change made after it. Adopted only if it helps on both.

Usage: python -m nrl.model.weather_test nrl/cache [nrl/docs/WEATHER.md]
"""
import sys

import lightgbm as lgb
import numpy as np
import pandas as pd

from nrl.model import counts, team, tries
from nrl.model.player_frame import POSITIONS

W = ['w_rain_game', 'w_rain_pre3', 'w_rain_24', 'w_wind', 'w_gusts', 'w_temp', 'w_dew']


def weather(cache):
    w = pd.read_parquet(f'{cache}/weather/weather.parquet')
    for c in ('rain_game', 'rain_pre3', 'rain_24', 'wind', 'gusts'):
        w.loc[w.roof, c] = 0.0
    return w.rename(columns={c: f'w_{c}' for c in ('rain_game', 'rain_pre3', 'rain_24', 'wind', 'gusts', 'temp',
                                                   'dew_point')}).rename(columns={'w_dew_point': 'w_dew'})


def totals(cache, w):
    g = team.games(pd.read_parquet(f'{cache}/team_frame.parquet')).merge(w, on='match_id', how='left')
    g = g[g.season >= 2009].dropna(subset=['w_temp'])
    fit = g[g.season.isin(range(2009, 2019))]
    rows = []
    for name, feats in (('ratings only', team.TOTAL_FEATURES), ('ratings + weather', team.TOTAL_FEATURES + W)):
        tm = team.LinearT().fit(fit[feats].to_numpy(), fit.total.to_numpy())
        for lab, ss in (('dev', team.DEV), ('confirm', team.CONFIRM)):
            t = g[g.season.isin(ss)]
            rows.append(f'| totals | {lab} | {name} | miss {np.abs(tm.mean(t[feats].to_numpy()) - t.total).mean():.3f} points |')
        if name != 'ratings only':
            coef = dict(zip(['const'] + feats, np.round(tm.coef, 3)))
            rows.append(f'| | | coefficients | rain in game {coef["w_rain_game"]:+.2f} pts/mm, rain before {coef["w_rain_pre3"]:+.2f}, '
                        f'wind {coef["w_wind"]:+.3f} pts per km/h, temp {coef["w_temp"]:+.3f}, dew point {coef["w_dew"]:+.3f} |')
    wet = g[g.season.isin(list(team.DEV) + list(team.CONFIRM))]
    hard = wet[wet.w_rain_game >= 2]
    rows.append(f'| totals | dev+confirm | games with 2mm+ of rain during the game | {len(hard)} games, '
                f'average total {hard.total.mean():.1f} against {wet.total.mean():.1f} |')
    return rows


def tries_test(cache, w):
    p = pd.read_parquet(f'{cache}/player_frame.parquet').merge(w, on='match_id', how='left')
    p = p[p.season >= 2001]
    out = []
    for name, feats in (('without weather', tries.FEATURES), ('with weather', tries.FEATURES + W)):
        tr, dv = p[p.season.isin(tries.FIT)], p[p.season.isin(tries.DEV)]
        d = lgb.Dataset(tr[feats], tr.tries, categorical_feature=['position_code'])
        mdl = lgb.train(tries.PARAMS, d, 3000, valid_sets=[lgb.Dataset(dv[feats], dv.tries, reference=d)],
                        callbacks=[lgb.early_stopping(100, verbose=False)])
        for lab, ss in (('dev', tries.DEV), ('confirm', tries.CONFIRM)):
            t = p[p.season.isin(ss) & p.w_temp.notna()]
            pa = 1 - np.exp(-mdl.predict(t[feats], num_iteration=mdl.best_iteration))
            out.append(f'| anytime try | {lab} | {name} | log loss {tries.logloss(pa, t.scored):.5f} |')
    return out


def counts_test(cache, w):
    out = []
    for stat, label in counts.STATS.items():
        f = counts.frame(cache, stat).merge(w, on='match_id', how='left')
        f['is_final'] = f.is_final.astype(float)
        f = f[f.games >= 3]
        for name, feats in (('without weather', counts.FEATURES), ('with weather', counts.FEATURES + W)):
            tr, dv = f[f.season.isin(counts.FIT)], f[f.season.isin(counts.DEV)]
            d = lgb.Dataset(tr[feats], tr.y, categorical_feature=['position_code'])
            mdl = lgb.train(counts.PARAMS, d, 3000, valid_sets=[lgb.Dataset(dv[feats], dv.y, reference=d)],
                            callbacks=[lgb.early_stopping(100, verbose=False)])
            for lab, ss in (('dev', counts.DEV), ('confirm', counts.CONFIRM)):
                t = f[f.season.isin(ss) & f.w_temp.notna()]
                miss = np.abs(mdl.predict(t[feats], num_iteration=mdl.best_iteration) - t.y).mean()
                out.append(f'| {label} | {lab} | {name} | projection miss {miss:.3f} |')
    return out


def forecast_test(cache, w):
    """Live use: weather effects learned from actual weather (2009-2018), then fed the archived FORECAST."""
    try:
        wf = pd.read_parquet(f'{cache}/weather/weather_forecast.parquet')
    except FileNotFoundError:
        return ['| forecast test | | | weather_forecast.parquet not pulled yet |']
    wf = weather(cache).iloc[:0].pipe(lambda _: wf)
    for c in ('rain_game', 'rain_pre3', 'rain_24', 'wind', 'gusts'):
        wf.loc[wf.roof, c] = 0.0
    wf = wf.rename(columns={c: f'w_{c}' for c in ('rain_game', 'rain_pre3', 'rain_24', 'wind', 'gusts', 'temp')})
    wf = wf.rename(columns={'dew_point': 'w_dew'})
    g = team.games(pd.read_parquet(f'{cache}/team_frame.parquet'))
    ga, gf = g.merge(w, on='match_id'), g.merge(wf, on='match_id')
    fit = ga[ga.season.isin(range(2009, 2019))]
    base = team.LinearT().fit(fit[team.TOTAL_FEATURES].to_numpy(), fit.total.to_numpy())
    wm = team.LinearT().fit(fit[team.TOTAL_FEATURES + W].to_numpy(), fit.total.to_numpy())
    out = []
    for lab, ss in (('2022', [2022]), ('2023-2024', [2023, 2024])):
        ta, tf_ = ga[ga.season.isin(ss)], gf[gf.season.isin(ss)]
        ta = ta[ta.match_id.isin(tf_.match_id)]
        tf_ = tf_.set_index('match_id').loc[ta.match_id].reset_index()
        miss = lambda mdl, d, f: np.abs(mdl.mean(d[f].to_numpy()) - d.total).mean()
        out += [f'| totals, live test | {lab} | no weather | miss {miss(base, ta, team.TOTAL_FEATURES):.3f} ({len(ta)} games) |',
                f'| totals, live test | {lab} | actual weather (hindsight) | miss {miss(wm, ta, team.TOTAL_FEATURES + W):.3f} |',
                f'| totals, live test | {lab} | archived forecast (what a bettor knew) | miss {miss(wm, tf_, team.TOTAL_FEATURES + W):.3f} |']
        r = tf_.merge(ta[['match_id', 'w_rain_game']], on='match_id', suffixes=('_fc', '_act'))
        out.append(f'| | {lab} | forecast against actual rain in the game | correlation {r.w_rain_game_fc.corr(r.w_rain_game_act):.2f} |')
    return out


def main(cache, out=None):
    w = weather(cache)
    lines = ['# Weather: does it help? (dev and confirm only; actual weather, so an upper bound on a forecast)', '',
             f'{len(w):,} games with weather; {int(w.roof.sum())} under a roof.', '',
             '| market | set | version | result |', '|---|---|---|---|']
    lines += totals(cache, w) + forecast_test(cache, w) + tries_test(cache, w) + counts_test(cache, w)
    text = '\n'.join(lines) + '\n'
    print(text)
    if out:
        open(out, 'w').write(text)


if __name__ == '__main__':
    main(*sys.argv[1:3])
