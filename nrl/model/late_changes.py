"""How optimistic is the "teams named" version? Tuesday's list against who took the field.

The team model's "teams named" version reads who PLAYED, which folds in every late change. Where
Tuesday's list was parsed (nrl/teamlists/parse.py), one margin model (ratings + player strength,
fitted on who played, FIT seasons) is scored three ways on the same games: with last game's 17
(open), with Tuesday's 1-17 (what a bettor really knows when lists come out), and with who played
(the backtest's assumption). Also: how many named players miss out, and how far that moves our margin.

Usage: python -m nrl.model.late_changes nrl/cache [nrl/docs/LATE_CHANGES.md]
"""
import sys

import numpy as np
import pandas as pd

from nrl.model.team import FIT, LinearT, games, score, win_prob


def main(cache, out=None):
    tf = pd.read_parquet(f'{cache}/team_frame.parquet')
    g = games(tf)
    fit = g[g.season.isin(FIT)].dropna(subset=['strength_diff_named'])
    mm = LinearT().fit(fit[['exp_margin', 'strength_diff_named']].to_numpy(), fit.margin.to_numpy())
    t = g.dropna(subset=['strength_diff_tuesday', 'strength_diff_open', 'strength_diff_named'])
    lines = ['# Late changes: Tuesday\'s list against who took the field', '',
             f'{len(t):,} games where both sides\' Tuesday lists were parsed, seasons '
             f'{", ".join(map(str, sorted(t.season.unique())))}. One margin model (ratings + player strength, fitted '
             f'on who played, {FIT.start}-{FIT.stop - 1}), fed three line-ups:', '',
             '| line-up fed in | bits/game | log loss | margin miss |', '|---|---|---|---|']
    for lab, col in (('last game\'s 17 (open)', 'strength_diff_open'), ('Tuesday\'s 1-17', 'strength_diff_tuesday'),
                     ('who took the field', 'strength_diff_named')):
        X = t[['exp_margin', col]].to_numpy()
        r = score(win_prob(mm, X), t.margin.to_numpy())
        lines.append(f'| {lab} | {r["bits"]:.3f} | {r["logloss"]:.4f} | {np.abs(mm.mean(X) - t.margin).mean():.2f} |')
    nt = pd.read_parquet(f'{cache}/named_teams.parquet')
    nt = nt[(nt.kind == 'named') & (nt.jersey <= 17)]
    per = nt.groupby(['match_id', 'team']).played.apply(lambda s: (~s).sum())
    shift = (t.strength_diff_named - t.strength_diff_tuesday).abs() * mm.coef[2]
    lines += ['', f'Named 1-17 who did not take the field: {(~nt.played).mean():.1%} of players; per team-game '
              f'{per.mean():.2f} on average, none in {(per == 0).mean():.0%}, three or more in {(per >= 3).mean():.0%}.',
              f'Late changes moved our predicted margin by {shift.mean():.2f} points on average, by 2+ points in '
              f'{(shift >= 2).mean():.0%} of games.', '']
    text = '\n'.join(lines)
    print(text)
    if out:
        open(out, 'w').write(text)


if __name__ == '__main__':
    main(*sys.argv[1:3])
