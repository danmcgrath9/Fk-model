"""Score the prediction log against results, once Cricsheet holds them. Paper only.

Uses, per game, the last price logged before the game's day (Sydney). Measures: head-to-head log loss and bits
(0 = a coin flip); first-innings runs CRPS (the miss of the whole distribution, in runs); player runs
log-likelihood when he batted (negative binomial), and the chance to bat. A game with no result (or rain-reduced)
is left out of the totals and the head-to-head.

Usage: python -m bbl.live.score <parquet dir> <log dir>   (writes PAPER_SCORE.md in the log dir)
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

from bbl.model import frame


def last_before(log):
    log = log.copy()
    log['logged_day'] = pd.to_datetime(log.logged_at).dt.tz_convert('Australia/Sydney').dt.date
    return log


def main(d, log_dir):
    gp, pp = os.path.join(log_dir, 'prediction_log_games.parquet'), os.path.join(log_dir, 'prediction_log_players.parquet')
    if not os.path.exists(gp):
        print('no prediction log yet')
        return
    m = frame.match_table(pd.read_parquet(os.path.join(d, 't20_matches.parquet')))
    inn = pd.read_parquet(os.path.join(d, 't20_innings.parquet'))
    g = last_before(pd.read_parquet(gp))
    g = g[g.logged_day < pd.to_datetime(g.start_date).dt.date]
    g = g.sort_values('logged_at').groupby('cricinfo_id').tail(1)
    x = g.merge(m[['match_id', 'team1', 'team2', 'winner', 'result', 'method', 'bat_first']].rename(
        columns={'team1': 'cs_team1', 'team2': 'cs_team2'}), left_on='cricinfo_id', right_on='match_id')
    lines = ['# Paper record: our logged prices against results', '',
             f'{len(g)} games priced before their day; {len(x)} have a result in Cricsheet.', '']
    dec = x[(x.result == 'win') & x.method.isna()]
    if len(dec):
        p = np.where(dec.winner == dec.team1, dec.p_team1, 1 - dec.p_team1).clip(0.01, 0.99)
        lines += [f'Head-to-head, {len(dec)} decided games: log loss {-np.log(p).mean():.3f}, bits {(1 + np.log2(p)).mean():.3f} '
                  f'(0 is a coin flip), favourite won {np.mean(p > 0.5):.0%}.', '']
    first = inn[(inn.innings == 1) & ~inn.super_over][['match_id', 'runs', 'legal_balls', 'wickets']]
    t = x.merge(first, on='match_id')
    t = t[((t.legal_balls >= 120) | (t.wickets >= 10)) & t.method.isna()]
    if len(t):
        z = (t.runs - t.first_inns_runs_mu) / t.first_inns_runs_sd
        crps = (t.first_inns_runs_sd * (z * (2 * stats.norm.cdf(z) - 1) + 2 * stats.norm.pdf(z) - 1 / np.sqrt(np.pi))).mean()
        lines += [f'First-innings runs, {len(t)} full innings: average miss {(t.runs - t.first_inns_runs_mu).abs().mean():.1f} runs, '
                  f'CRPS {crps:.1f}, within one sd {np.mean(z.abs() <= 1):.0%}.', '']
    if os.path.exists(pp) and len(x):
        pl = last_before(pd.read_parquet(pp))
        pl = pl.merge(g[['cricinfo_id', 'logged_at']], on=['cricinfo_id', 'logged_at'])
        # runs straight from the ball-by-ball for the logged games only (no full frame rebuild needed)
        dl = pd.read_parquet(os.path.join(d, 't20_deliveries.parquet'))
        dl = dl[dl.match_id.isin(set(x.match_id))]
        bat = frame.batting(dl)[['match_id', 'player', 'bat_runs']].groupby(['match_id', 'player'], as_index=False).bat_runs.sum()
        pls = pd.read_parquet(os.path.join(d, 't20_players.parquet'), columns=['match_id', 'player'])
        gf = pls[pls.match_id.isin(set(x.match_id))].merge(bat, on=['match_id', 'player'], how='left')
        gf['did_bat'] = gf.bat_runs.notna().astype(int)
        if len(gf):
            y = pl.merge(gf, left_on=['cricinfo_id', 'player'], right_on=['match_id', 'player'])
            b = y[y.did_bat == 1]
            if len(b):
                ll = stats.nbinom.logpmf(b.bat_runs, b.r_runs, b.r_runs / (b.r_runs + b.mu_runs)).mean()
                pb = y.p_bat.clip(1e-4, 1 - 1e-4)
                lines += [f'Players, {len(y)} player-games in the named XIs we priced ({len(b)} batted): runs log-likelihood {ll:.3f}, '
                          f'chance-to-bat log-likelihood {np.mean(np.where(y.did_bat == 1, np.log(pb), np.log(1 - pb))):.3f}.', '']
    text = '\n'.join(lines)
    open(os.path.join(log_dir, 'PAPER_SCORE.md'), 'w').write(text)
    print(text)


if __name__ == '__main__':
    main(*sys.argv[1:])
