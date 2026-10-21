"""Run metres and tackles props from Champion Data (2014 on), the AFL-disposals way.

  frame       one row per player who took the field; every feature from earlier games (exponentially
              weighted and last-10 averages of the stat, career average in this position group, games
              played), plus this game's position and jersey (on Tuesday's list), the team model's
              expected margin and total (teams named), and what the opponent has conceded per game to
              this position group
  projection  LightGBM on FIT seasons, trees chosen on DEV
  spread      the projection's errors on FIT, as a normal whose width grows with the projection
              (sd = a + b x mean, fitted on FIT), so every line has an over/under probability
  stand-in    PROXY line: the player's last-10 average less an offset fitted on FIT so a blind over wins
              half the time, rounded to .5; priced 1.87 each way. Never a market result.

Seasons: FIT 2014-2019, DEV 2020-2021, CONFIRM 2022-2023, FINAL 2024-2026 (touched once, --final).

Usage: python -m nrl.model.counts nrl/cache [nrl/docs/COUNTS_STEP1.md] [--final]
"""
import sys

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy import stats

from nrl.data.link_cd import POSITION, norm
from nrl.model.player_frame import GROUP, POSITIONS, ew

FIT = range(2014, 2020)
DEV = range(2020, 2022)
CONFIRM = range(2022, 2024)
FINAL = range(2024, 2027)
STATS = {'runMetres': 'run metres', 'tackles': 'tackles'}
PRICE = 1.87
THRESHOLDS = [0.54, 0.56, 0.58, 0.60]
PARAMS = dict(objective='regression', learning_rate=0.03, num_leaves=31, min_data_in_leaf=100,
              feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1, lambda_l2=5.0, verbose=-1, seed=7)


def frame(cache, stat):
    cp = pd.read_parquet(f'{cache}/cd_player_games.parquet')
    cp = cp[cp.took_field].copy()
    cp['kick_off'] = pd.to_datetime(cp.utc_start, utc=True)
    cp = cp.sort_values(['kick_off', 'cd_match_id', 'squad_id', 'jumperNumber']).reset_index(drop=True)
    pos = cp.position.map(POSITION)
    # early seasons carry no position: fall back to the jersey's usual position
    by_jersey = {1: 'FB', 2: 'W', 3: 'C', 4: 'C', 5: 'W', 6: 'FE', 7: 'HB', 8: 'FR', 9: 'HK', 10: 'FR', 11: '2R',
                 12: '2R', 13: 'L'}
    cp['pos'] = pos.fillna(cp.jumperNumber.map(by_jersey)).fillna('B')
    cp['group'] = cp.pos.map(GROUP).fillna('bench')
    cp['position_code'] = cp.pos.map({k: j for j, k in enumerate(POSITIONS)}).astype(float)
    cp['jersey'] = cp.jumperNumber.astype(float)
    cp['starter'] = (cp.jersey <= 13).astype(float)
    y = cp[stat].astype(float)
    cp['y'] = y
    g = cp.groupby('playerId').y
    cp['games'] = g.cumcount()
    cp['ew_fast'] = ew(None, cp.playerId, y, 0.3)
    cp['ew_slow'] = ew(None, cp.playerId, y, 0.1)
    cp['last10'] = g.transform(lambda s: s.shift(1).rolling(10, min_periods=1).mean())
    cp['last3'] = g.transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
    gg = cp.groupby(['playerId', 'group']).y
    cp['group_games'] = gg.cumcount()
    cp['group_avg'] = (gg.cumsum() - y) / cp.group_games.replace(0, np.nan)
    cp['prev_starter'] = cp.groupby('playerId').starter.shift(1)
    # opponent: stat conceded per game to this position group, before this game
    conc = cp.groupby(['kick_off', 'cd_match_id', 'opp', 'group']).y.sum().reset_index().sort_values('kick_off')
    conc['opp_conc'] = ew(None, list(zip(conc.opp, conc.group)), conc.y, 0.1)
    cp = cp.merge(conc[['cd_match_id', 'opp', 'group', 'opp_conc']], on=['cd_match_id', 'opp', 'group'], how='left')
    # team model, teams named, via the RLP link
    tf = pd.read_parquet(f'{cache}/team_frame.parquet')
    link = pd.read_parquet(f'{cache}/cd_game_link.parquet')
    tf = tf.assign(tnorm=tf.team.map(norm))[['match_id', 'tnorm', 'exp_margin', 'exp_total', 'strength_diff_named']]
    cp = cp.assign(tnorm=cp.team.map(norm)).merge(link, on='cd_match_id', how='left') \
        .merge(tf, on=['match_id', 'tnorm'], how='left')
    cp['home'] = cp.home.astype(float)
    return cp


FEATURES = ['position_code', 'jersey', 'starter', 'prev_starter', 'games', 'ew_fast', 'ew_slow', 'last10', 'last3',
            'group_games', 'group_avg', 'opp_conc', 'exp_margin', 'exp_total', 'strength_diff_named', 'home', 'is_final']


def run(cache, stat, final=False):
    f = frame(cache, stat)
    f['is_final'] = f.is_final.astype(float)
    f = f[f.games >= 3].copy()
    tr, dv = f[f.season.isin(FIT)], f[f.season.isin(DEV)]
    dtr = lgb.Dataset(tr[FEATURES], tr.y, categorical_feature=['position_code'])
    mdl = lgb.train(PARAMS, dtr, 3000, valid_sets=[lgb.Dataset(dv[FEATURES], dv.y, reference=dtr)],
                    callbacks=[lgb.early_stopping(100, verbose=False)])
    f['mu'] = mdl.predict(f[FEATURES], num_iteration=mdl.best_iteration)
    # spread on FIT: |error| ~ a + b * mu (mean absolute error of a normal is sd * sqrt(2/pi))
    trf = f[f.season.isin(FIT)]
    A = np.column_stack([np.ones(len(trf)), trf.mu])
    ab, *_ = np.linalg.lstsq(A, np.abs(trf.y - trf.mu) / np.sqrt(2 / np.pi), rcond=None)
    f['sd'] = np.maximum(ab[0] + ab[1] * f.mu, 1.0)
    # stand-in line, offset so a blind over wins half the time on FIT
    def line(offset):
        return np.floor(f.last10 - offset) + 0.5
    offs = np.linspace(-15, 15, 121) if stat == 'runMetres' else np.linspace(-5, 5, 101)
    fitmask = f.season.isin(FIT).to_numpy()
    best = min(offs, key=lambda o: abs((f.y.to_numpy()[fitmask] > line(o).to_numpy()[fitmask]).mean() - 0.5))
    f['line'] = line(best)
    f['p_over'] = 1 - stats.norm.cdf(f.line, f.mu, f.sd)
    sets = [('dev', DEV), ('confirm', CONFIRM)] + ([('final', FINAL)] if final else [])
    out = [f'## {STATS[stat]}', '', f'Stand-in line offset {best:+.2f} (fitted on FIT); trees {mdl.best_iteration}; '
           f'spread sd = {ab[0]:.2f} + {ab[1]:.3f} x projection.', '',
           '| set | player-games | projection miss | last-10 miss | blind over wins | bets at 56%+ | hit rate | ROI at 1.87 | 90% interval |',
           '|---|---|---|---|---|---|---|---|---|']
    thr = ['', f'### {STATS[stat]}: by threshold', '', '| set | threshold | bets | hit rate | ROI |', '|---|---|---|---|---|']
    for lab, ss in sets:
        t = f[f.season.isin(ss)].copy()
        over = t.y > t.line
        rows = {}
        for th in THRESHOLDS:
            take_o, take_u = t.p_over >= th, (1 - t.p_over) >= th
            win = np.r_[over[take_o].to_numpy(), (~over[take_u]).to_numpy()]
            rk = np.r_[t.kick_off[take_o].dt.strftime('%G-%V').to_numpy(), t.kick_off[take_u].dt.strftime('%G-%V').to_numpy()]
            rows[th] = (win, rk)
            if len(win):
                thr.append(f'| {lab} | {th:.0%} | {len(win):,} | {win.mean():.1%} | {win.mean() * PRICE - 1:+.1%} |')
        win, rk = rows[0.56]
        lo, hi = boot(win, rk)
        out.append(f'| {lab} | {len(t):,} | {np.abs(t.y - t.mu).mean():.2f} | {np.abs(t.y - t.last10).mean():.2f} | '
                   f'{over.mean():.1%} | {len(win):,} | {win.mean():.1%} | {win.mean() * PRICE - 1:+.1%} | {lo:+.1%} to {hi:+.1%} |')
    imp = pd.Series(mdl.feature_importance('gain'), index=FEATURES)
    imp = (imp / imp.sum()).sort_values(ascending=False)
    out += thr + ['', 'What drives it: ' + ', '.join(f'{k} {v:.0%}' for k, v in imp.head(6).items()), '']
    return out


def boot(win, rk, n=2000, seed=1):
    if len(win) == 0:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    d = pd.DataFrame(dict(w=win.astype(float), r=rk)).groupby('r').w.agg(['sum', 'count'])
    idx = rng.integers(0, len(d), size=(n, len(d)))
    s, c = d['sum'].to_numpy()[idx].sum(1), d['count'].to_numpy()[idx].sum(1)
    return np.percentile(s / c * PRICE - 1, [5, 95])


def main(cache, out=None, final=False):
    lines = ['# Run metres and tackles, step 1 (stand-in lines only)', '']
    for stat in STATS:
        lines += run(cache, stat, final)
    text = '\n'.join(lines)
    print(text)
    if out:
        open(out, 'w').write(text)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    main(args[0], args[1] if len(args) > 1 else None, final='--final' in sys.argv)
