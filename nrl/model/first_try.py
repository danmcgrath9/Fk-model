"""First try scorer: how good are the try model's first-try probabilities? (Champion Data, 2014 on)

The try model (nrl/model/tries.py) gives every player an expected try count lam; with the whole
game as a Poisson race, P(player scores the first try) = lam / sum(lam) x (1 - exp(-sum(lam))).
Champion Data's score flow says who did score first. Compared with a stand-in that shares the first
try by POSITION only (each position's try rate on FIT seasons), scored as the average of -log(the
probability given to the actual first scorer), lower is better, and backtested against that stand-in at
its fair price (an upper bound, never a market result).

Usage: python -m nrl.model.first_try nrl/cache [nrl/docs/FIRST_TRY_STEP1.md]
"""
import sys

import numpy as np
import pandas as pd

from nrl.model.tries import CONFIRM, DEV, FIT, bootstrap_roi

EDGES = [0.10, 0.25, 0.50]


def first_scorers(cache):
    sc = pd.read_parquet(f'{cache}/cd_scores.parquet')
    sc = sc[sc.scoreName.isin(['try', 'penalty try'])].sort_values(['cd_match_id', 'period', 'periodSeconds'])
    first = sc.drop_duplicates('cd_match_id')[['cd_match_id', 'playerId']]
    links = pd.read_parquet(f'{cache}/cd_links.parquet')
    gl = pd.read_parquet(f'{cache}/cd_game_link.parquet')
    first = first.merge(gl, on='cd_match_id').merge(links[['cd_player_id', 'player_id']], left_on='playerId',
                                                     right_on='cd_player_id', how='left')
    first['player_id'] = first.player_id.fillna(-first.playerId).astype('int64')
    return first[['match_id', 'player_id']].rename(columns={'player_id': 'first_scorer'})


def main(cache, out=None):
    tp = pd.read_parquet(f'{cache}/try_predictions.parquet')
    fs = first_scorers(cache)
    p = tp.merge(fs, on='match_id', how='inner')
    p['is_first'] = (p.player_id == p.first_scorer).astype(float)
    # games where the first scorer is in our rows (a penalty try has no player)
    good = p.groupby('match_id').is_first.transform('sum') == 1
    p = p[good].copy()
    rate = tp[tp.season.isin(FIT)].groupby('position').lam.mean()
    p['pos_rate'] = p.position.map(rate).fillna(rate.mean())
    tot = p.groupby('match_id').pos_rate.transform('sum')
    p['p_pos'] = p.pos_rate / tot * (1 - np.exp(-p.groupby('match_id').lam.transform('sum')))
    p['round_key'] = p.match_id   # one game per bet "round" is too fine; replaced below
    lines = ['## First try scorer (Champion Data score flow)', '',
             '| set | games | model -log p(first scorer) | position-share stand-in | model top pick right | stand-in top pick right |',
             '|---|---|---|---|---|---|']
    bt = ['', '### Backtest against the position-share PROXY at its fair price (upper bound)', '',
          '| set | edge needed | bets | strike rate | avg price | ROI | 90% interval |', '|---|---|---|---|---|---|---|']
    for lab, ss in (('dev', DEV), ('confirm', CONFIRM)):
        t = p[p.season.isin(ss)]
        if t.empty:
            continue
        hit = t[t.is_first == 1]
        top_m = t.loc[t.groupby('match_id').p_first.idxmax()].is_first.mean()
        top_p = t.loc[t.groupby('match_id').p_pos.idxmax()].is_first.mean()
        lines.append(f'| {lab} | {hit.match_id.nunique():,} | {-np.log(hit.p_first).mean():.3f} | '
                     f'{-np.log(hit.p_pos).mean():.3f} | {top_m:.1%} | {top_p:.1%} |')
        for e in EDGES:
            b = t[t.p_first >= t.p_pos * (1 + e)].copy()
            if b.empty:
                continue
            b['stake'] = 1.0
            b['ret'] = np.where(b.is_first == 1, 1 / b.p_pos, 0.0)
            b['round_key'] = b.season.astype(str) + '-' + (b.match_id.rank(method='dense') // 8).astype(str)
            roi = b.ret.sum() / len(b) - 1
            lo, hi = bootstrap_roi(b)
            bt.append(f'| {lab} | {e:.0%} | {len(b):,} | {b.is_first.mean():.1%} | {(1 / b.p_pos).mean():.1f} | '
                      f'{roi:+.1%} | {lo:+.1%} to {hi:+.1%} |')
    text = '\n'.join(lines + bt) + '\n'
    print(text)
    if out:
        open(out, 'w').write(text)


if __name__ == '__main__':
    main(*sys.argv[1:3])
