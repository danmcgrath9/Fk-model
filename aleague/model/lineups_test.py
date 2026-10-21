"""Does knowing the starting XI improve the team prices? ("teams named" against "at the open")

For each match: plus-minus ratings fitted on segments before the match's week (aleague/model/plusminus.py),
the confirmed XI's rating minus that side's usual XI (decayed average of its earlier starting XIs, rated
with the same ratings), and the team model's expected goals shifted by
    log lam_home += b x (delta_home - delta_away) / 2,   log lam_away -= the same
b is chosen on the tune seasons only (grid), checked on the confirm seasons, then the newest seasons are
scored once. The line-up feature is new information, so the newest seasons are a fair test of it even
though the goals-only model was looked at on them before.

Usage: python -m aleague.model.lineups_test <tables dir> <report.md>
"""
import json
import os
import sys

import numpy as np
import pandas as pd

from aleague.model.evaluate import boot_diff, week_of
from aleague.model.markets import h2h, score_matrix
from aleague.model.plusminus import fit, segments
from aleague.model.team import rolling_predictions

SETTINGS = os.path.join(os.path.dirname(__file__), 'settings.json')
TUNE, CONFIRM, FINAL = [2016, 2017, 2018, 2019, 2020], [2021, 2022, 2023], [2024, 2025, 2026]
B_GRID = [0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0]
USUAL_HALF_LIFE = 5  # matches


def xi_deltas(pg, seg, matches_needed):
    """Per match and side: the starting XI's rating minus the side's usual XI rating, leak-free."""
    pg = pg[pg.match_id.isin(matches_needed)]
    starters = pg[pg.starter].groupby(['match_id', 'date', 'team', 'is_home']).player_id.apply(tuple).reset_index()
    starters['week'] = pd.to_datetime(starters.date).dt.to_period('W-SUN')
    out, usual = [], {}
    for wk, games in starters.sort_values('date').groupby('week', sort=True):
        before = games.date.min()
        ratings, _ = fit(seg, before)
        for _, r in games.iterrows():
            xi = sum(ratings.get(p, 0.0) for p in r.player_id)
            prev = usual.get(r.team)
            # the side's usual XI, rated with today's ratings: a decayed set of its recent starters' minutes
            u = (sum(ratings.get(p, 0.0) * w for p, w in prev.items()) / (sum(prev.values()) / 11)) if prev else xi
            out.append(dict(match_id=r.match_id, is_home=r.is_home, delta=xi - u))
        for _, r in games.iterrows():  # update the usual XIs after the week's games
            d = usual.setdefault(r.team, {})
            for p in list(d):
                d[p] *= 0.5 ** (1 / USUAL_HALF_LIFE)
            for p in r.player_id:
                d[p] = d.get(p, 0.0) + 1.0
    t = pd.DataFrame(out)
    return t.pivot_table(index='match_id', columns='is_home', values='delta').rename(columns={True: 'd_home', False: 'd_away'})


def probs(df, b, rho):
    P = []
    for lh, la, dh, da in zip(df.lam_home, df.lam_away, df.d_home, df.d_away):
        shift = b * (dh - da) / 2
        r = h2h(score_matrix(lh * np.exp(shift), la * np.exp(-shift), rho))
        P.append([r['home'], r['draw'], r['away']])
    return np.array(P)


def logloss(P, df):
    y = np.where(df.home_goals > df.away_goals, 0, np.where(df.home_goals == df.away_goals, 1, 2))
    return -np.log(np.clip(P[np.arange(len(y)), y], 1e-12, 1))


def main(tables, report):
    s = json.load(open(SETTINGS))
    m = pd.read_parquet(f'{tables}/matches.parquet')
    pg = pd.read_parquet(f'{tables}/player_games.parquet')
    ev = pd.read_parquet(f'{tables}/ual_events.parquet')
    seasons = TUNE + CONFIRM + FINAL
    dc = rolling_predictions(m, seasons, **s)
    seg = segments(pg, ev)
    d = xi_deltas(pg, seg, set(dc.match_id))
    df = dc.merge(d, left_on='match_id', right_index=True, how='inner').dropna(subset=['d_home', 'd_away'])
    res = []
    for b in B_GRID:
        ll = logloss(probs(df, b, s['rho']), df)
        res.append(dict(b=b, **{name: ll[df.season.isin(block).to_numpy()].mean()
                                for name, block in (('tune', TUNE), ('confirm', CONFIRM), ('final', FINAL))}))
    res = pd.DataFrame(res)
    best = res.sort_values('tune').iloc[0]
    base = logloss(probs(df, 0.0, s['rho']), df)
    named = logloss(probs(df, best.b, s['rho']), df)
    lines = ['# Teams named: does the starting XI improve the head-to-head prices?', '',
             f'{len(df):,} matches with both line-ups. Plus-minus ratings from segments before each match week; '
             'the XI\'s rating against the side\'s usual XI shifts the team model\'s expected goals. '
             'b chosen on the tune seasons only.', '',
             res.round(4).to_markdown(index=False), '', f'Chosen b = {best.b}.', '',
             '| seasons | games | at the open | teams named | difference (90% interval, by week) | verdict |',
             '|---|---|---|---|---|---|']
    for name, block in (('tune 2015-16 to 2019-20', TUNE), ('confirm 2020-21 to 2022-23', CONFIRM),
                        ('final 2023-24 to 2025-26', FINAL)):
        k = df.season.isin(block).to_numpy()
        dd, lo, hi = boot_diff(named[k], base[k], week_of(df.date[k].to_numpy()))
        v = 'teams named better' if hi < 0 else 'teams named worse' if lo > 0 else 'no difference'
        lines.append(f'| {name} | {k.sum()} | {base[k].mean():.4f} | {named[k].mean():.4f} | '
                     f'{dd:+.4f} ({lo:+.4f} to {hi:+.4f}) | {v} |')
    big = df[(df.d_home - df.d_away).abs() > (df.d_home - df.d_away).abs().quantile(0.9)]
    lines += ['', f'In the tenth of matches where the line-ups moved most ({len(big)}), mean |XI difference| '
              f'{(big.d_home - big.d_away).abs().mean():.2f} goals per 90.', '']
    text = '\n'.join(lines) + '\n'
    open(report, 'w').write(text)
    print(text)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
