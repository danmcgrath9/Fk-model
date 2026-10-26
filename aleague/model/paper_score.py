"""Score every round of recorded prices (aleague/paper/) against results, and later against closing odds.

Each round is recorded BEFORE kick-off by price_round and price_props, written to aleague/paper/ and
committed, so the git history proves when a price was made. This script reads them all and reports the
running record: head-to-head and over 2.5 log loss for the team prices, scorer and card log loss for
the props, with the counts that say how little a few rounds can show.

Usage: python -m aleague.model.paper_score <tables dir> [<out.md>]
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.join(os.path.dirname(__file__), '..', 'paper')


def ll(p, hit):
    p = np.clip(np.asarray(p, dtype=float), 1e-9, 1 - 1e-9)
    return -np.where(hit, np.log(p), np.log(1 - p))


def main(tables, out=None):
    m = pd.read_parquet(f'{tables}/matches.parquet')
    pg = pd.read_parquet(f'{tables}/player_games.parquet')
    lines = ['# Paper record', '']
    team = [pd.read_parquet(f).assign(file=os.path.basename(f)) for f in sorted(glob.glob(f'{HERE}/*_team.parquet'))]
    t = None
    if team:
        t = pd.concat(team).merge(m[['date', 'home', 'away', 'home_goals_90', 'away_goals_90']], on=['date', 'home', 'away'])
        t = t[t.home_goals_90.notna()]
    if t is not None and len(t):
        y = np.where(t.home_goals_90 > t.away_goals_90, 0, np.where(t.home_goals_90 == t.away_goals_90, 1, 2))
        P = t[['h2h_home', 'h2h_draw', 'h2h_away']].to_numpy()
        llh = -np.log(np.clip(P[np.arange(len(y)), y], 1e-9, 1))
        over = (t.home_goals_90 + t.away_goals_90 > 2.5).to_numpy()
        llo = ll(1 / t['over_2.5'], over)
        lines += [f'Team prices: {len(t)} matches settled. Head-to-head log loss {llh.mean():.3f} (step 1 test seasons: '
                  f'1.07), over 2.5 {llo.mean():.3f} (0.68). Fewer than about 150 matches says next to nothing.', '']
    props = [pd.read_parquet(f) for f in sorted(glob.glob(f'{HERE}/*_props.parquet'))]
    if props:
        p = pd.concat(props)
        res = pg[['date', 'player', 'team', 'goal', 'yellow', 'red', 'minutes']]
        p = p.merge(res, on=['date', 'player', 'team'])
        p = p[p.minutes > 0]  # a non-runner is void
        if len(p):
            lines += [f'Props: {len(p)} settled player-matches. Scorer log loss {ll(p.p_goal, p.goal > 0).mean():.3f} '
                      f'(test seasons 0.27), carded {ll(p.p_card, (p.yellow + p.red) > 0).mean():.3f} (0.37).', '']
    text = '\n'.join(lines) + '\n'
    if out:
        open(out, 'w').write(text)
    print(text)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
