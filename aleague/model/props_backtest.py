"""Out-of-sample test of player-prop probabilities: anytime goal scorer and player carded.

Data: player_games.parquet (Ultimate A-League line-ups, CC BY 4.0), one row per player per match, with
minutes within 90, goals, cards and the referee; team expected goals from the frozen team model.

"Teams named" version: the starting XI and bench are known (A-League sides are named about an hour
before kick-off), so each player's expected minutes come from his own previous starts or bench
appearances. Every rate uses that player's EARLIER matches only, decayed by HALF_LIFE matches and
shrunk towards the league rate with the weight of PRIOR_90S full matches:

  scorer   P = 1 - exp(-rate90 x expected minutes / 90 x team xG / league average xG)
  carded   P = 1 - exp(-rate90 x expected minutes / 90 x referee factor)
           (referee factor = his earlier cards per match over the league's, shrunk)

Compared with what a lazy book could do: each player's raw goals (or cards) per appearance to date,
and a flat league rate per start / per bench appearance. Scored by log loss, with 90% intervals by
week, plus calibration. No odds yet, so this is not a profit test.

Usage: python -m aleague.model.props_backtest <tables dir> <report.md>
"""
import json
import os
import sys

import numpy as np
import pandas as pd

from aleague.model.evaluate import boot_diff, week_of
from aleague.model.team import rolling_predictions

HALF_LIFE = 20          # matches
PRIOR_90S = {'goal': 6.0, 'yellow': 6.0}
REF_PRIOR = 20.0        # matches of league average behind each referee
SETTINGS = os.path.join(os.path.dirname(__file__), 'settings.json')
EPS = 1e-9


def decayed_history(pg, cols):
    """For each row, decayed sums of `cols` and of minutes over the player's EARLIER matches."""
    pg = pg.sort_values(['player_id', 'date', 'match_id']).reset_index(drop=True)
    d = 0.5 ** (1 / HALF_LIFE)
    out = {f'h_{c}': np.zeros(len(pg)) for c in cols + ['minutes', 'apps', 'start_min', 'starts', 'bench_min', 'benches']}
    acc, last = None, None
    for i, r in enumerate(pg.itertuples(index=False)):
        if r.player_id != last:
            acc = {k: 0.0 for k in out}
            last = r.player_id
        for k in out:
            out[k][i] = acc[k]
        for k in out:
            acc[k] *= d
        for c in cols:
            acc[f'h_{c}'] += getattr(r, c)
        acc['h_minutes'] += r.minutes
        acc['h_apps'] += 1.0 if r.minutes > 0 else 0.0
        if r.starter:
            acc['h_start_min'] += r.minutes; acc['h_starts'] += 1
        else:
            acc['h_bench_min'] += r.minutes; acc['h_benches'] += 1
    for k, v in out.items():
        pg[k] = v
    return pg


def referee_factor(pg):
    """Each referee's earlier yellow cards per match over the league's, shrunk to 1."""
    per = pg.groupby(['match_id', 'date', 'referee']).yellow.sum().reset_index().sort_values('date')
    league = per.yellow.expanding().mean().shift(1)
    cum_y = per.groupby('referee').yellow.cumsum() - per.yellow
    cum_n = per.groupby('referee').cumcount()
    per['ref_factor'] = ((cum_y + REF_PRIOR * league) / (cum_n + REF_PRIOR)) / league
    return per[['match_id', 'ref_factor']].fillna(1.0)


def main(tables, report):
    pg = pd.read_parquet(f'{tables}/player_games.parquet')
    pg = pg[pg.match_id.notna()].copy()
    pg['goal'] = pg.goal.clip(upper=5)
    pg = decayed_history(pg, ['goal', 'yellow'])
    m = pd.read_parquet(f'{tables}/matches.parquet')
    s = json.load(open(SETTINGS))
    seasons = sorted(pg.season.unique())
    tm = rolling_predictions(m, [x for x in seasons if x >= 2015], **s)[['match_id', 'lam_home', 'lam_away']]
    pg = pg.merge(tm, on='match_id', how='inner')
    pg['team_xg'] = np.where(pg.is_home, pg.lam_home, pg.lam_away)
    pg = pg.merge(referee_factor(pg), on='match_id', how='left')

    # league rates from earlier seasons only, per 90 outfield minutes
    out = pg[~pg.gk]
    by_season = out.groupby('season').agg(g=('goal', 'sum'), y=('yellow', 'sum'), mins=('minutes', 'sum'),
                                          xg=('team_xg', 'mean'))
    cum = by_season[['g', 'y', 'mins']].cumsum().shift(1)
    league = pd.DataFrame({'goal90': cum.g / cum.mins * 90, 'yellow90': cum.y / cum.mins * 90,
                           'xg': by_season.xg.expanding().mean().shift(1)})
    pg = pg.merge(league, left_on='season', right_index=True, how='inner').dropna(subset=['goal90'])

    # expected minutes, teams named: the player's own decayed average for this role, else the league's
    st_avg = (pg.h_start_min + 75 * 3) / (pg.h_starts + 3)
    bn_avg = (pg.h_bench_min + 15 * 3) / (pg.h_benches + 3)
    pg['exp_min'] = np.where(pg.starter, st_avg, bn_avg)
    for c, prior in (('goal', 'goal90'), ('yellow', 'yellow90')):
        k = PRIOR_90S[c]
        pg[f'rate90_{c}'] = (pg[f'h_{c}'] + pg[prior] * k) / (pg.h_minutes / 90 + k)
    gk = pg.gk.to_numpy()
    lam_goal = pg.rate90_goal * pg.exp_min / 90 * pg.team_xg / pg.xg
    lam_card = pg.rate90_yellow * pg.exp_min / 90 * pg.ref_factor
    pg['p_goal'] = np.where(gk, 0.002, 1 - np.exp(-lam_goal))
    pg['p_card'] = 1 - np.exp(-lam_card)

    # lazy books: raw per-appearance rate to date (no shrinkage, no minutes), and a flat rate by role
    raw_g = (pg.h_goal + 0.5) / (pg.h_apps + 5)
    raw_y = (pg.h_yellow + 0.5) / (pg.h_apps + 5)
    pg['p_goal_raw'] = np.where(gk, 0.002, 1 - np.exp(-raw_g))
    pg['p_card_raw'] = 1 - np.exp(-raw_y)
    role = pg.groupby(['season', 'starter']).agg(gr=('goal', lambda x: (x > 0).mean()), yr=('yellow', lambda x: (x > 0).mean()))
    role = role.groupby(level='starter').shift(1).reset_index()  # the previous season's rate for the role
    pg = pg.merge(role, on=['season', 'starter'], how='left').dropna(subset=['gr'])
    pg['p_goal_flat'] = np.where(pg.gk, 0.002, pg.gr)
    pg['p_card_flat'] = pg.yr

    played = pg[pg.minutes > 0]  # a player who never came on is a void bet at most books
    lines = ['# Player props, step 1: anytime scorer and player carded, out of sample', '',
             f'{len(played):,} player-matches with minutes on the pitch, seasons {played.season.min()}-{played.season.max()}; '
             'a named player who never came on is left out (a void bet at most books). Every rate from earlier '
             'matches only. Log loss, lower is better; differences with 90% intervals resampling weeks.', '']
    for market, hit, cols in (('anytime scorer', played.goal > 0, ('p_goal', 'p_goal_raw', 'p_goal_flat')),
                              ('player carded', played.yellow > 0, ('p_card', 'p_card_raw', 'p_card_flat'))):
        y = hit.to_numpy()
        ll = {c: -np.where(y, np.log(np.clip(played[c], EPS, 1)), np.log(np.clip(1 - played[c], EPS, 1))) for c in cols}
        wk = week_of(played.date.to_numpy())
        lines += [f'## {market} (happened in {y.mean():.1%} of player-matches)', '',
                  '| season | rows | model | raw rate | flat rate |', '|---|---|---|---|---|']
        for s_, x in played.groupby('season'):
            k = (played.season == s_).to_numpy()
            lines.append(f'| {s_ - 1}-{str(s_)[2:]} | {k.sum():,} | ' + ' | '.join(f'{ll[c][k].mean():.4f}' for c in cols) + ' |')
        for other in cols[1:]:
            dd, lo, hi = boot_diff(ll[cols[0]], ll[other], wk)
            lines.append(f'\nModel minus {other.split("_")[-1]} rate: {dd:+.4f} ({lo:+.4f} to {hi:+.4f}); '
                         f'{"model better" if hi < 0 else "model worse" if lo > 0 else "no difference"}.')
        bands = pd.cut(played[cols[0]], [0, .05, .1, .15, .2, .3, .4, .6, 1])
        lines += ['', '| predicted band | rows | average predicted | happened |', '|---|---|---|---|']
        for b, x in played.groupby(bands, observed=True):
            lines.append(f'| {b} | {len(x):,} | {x[cols[0]].mean():.3f} | {hit[x.index].mean():.3f} |')
        lines.append('')
    text = '\n'.join(lines) + '\n'
    open(report, 'w').write(text)
    print(text)
    pg.to_parquet(report.replace('.md', '_rows.parquet'), index=False)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
