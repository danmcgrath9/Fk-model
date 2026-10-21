"""Our props against REAL lines: ROI at the open and at the close, closing line value, by book, line size, season.

Lines come from afl/lines/odds_api.py (saved raw responses), flattened and matched by afl/lines/parse.py. Projections
come from afl/model/walkforward.py: every season predicted by a model that never saw it.

For each book's line on each player: the OPEN is the earliest snapshot holding it, the CLOSE the last before the bounce.
Our chance of the over at that line comes from the negative binomial around our projection. A side is bet where our
chance x the book's price - 1 clears the edge threshold. Settled at the price taken, against the player's actual count.
Closing line value: the price taken against the same book's close on the same line, as implied chances (positive =
we beat the close). A player who did not play is void (no row in our data: the bet is dropped, as books void it).

Usage: python -m afl.lines.backtest afl/cache afl/docs/LINES_BACKTEST.md
"""
import sys

import numpy as np
import pandas as pd
from scipy import stats

from afl.lines import parse
from afl.lines.odds_api import RAW, fixture

STAT_OF = {'player_disposals': 'D', 'player_disposals_over': 'D', 'player_marks_over': 'M', 'player_tackles_over': 'T',
           'player_goals_scored_over': 'G'}
EDGES = (0.0, 0.05, 0.10)


def p_over_nb(mu, line, a):
    n = 1 / a
    return 1 - stats.nbinom.cdf(np.floor(line), n, n / (n + mu))


def open_close(props):
    """Per book/market/player/line/side: price at the open (earliest snapshot) and at the close (latest)."""
    keys = ['event', 'game', 'player_id', 'book', 'market', 'side', 'point']
    s = props.sort_values('snapshot')
    first = s.groupby(keys, dropna=False).first().reset_index()[keys + ['price', 'snapshot', 'hours_before']]
    last = s.groupby(keys, dropna=False).last().reset_index()[keys + ['price', 'snapshot']]
    oc = first.merge(last, on=keys, suffixes=('_open', '_close'))
    return oc


def evaluate(oc, wf):
    rows = []
    for market, stat in STAT_OF.items():
        d = oc[oc.market == market]
        if d.empty:
            continue
        d = d.merge(wf[['game', 'player_id', stat, f'mu_{stat}', f'a_{stat}', 'season', 'Round']].dropna(subset=[f'mu_{stat}']),
                    on=['game', 'player_id'], how='inner')
        p = p_over_nb(d[f'mu_{stat}'].to_numpy(), d.point.to_numpy(), d[f'a_{stat}'].to_numpy())
        over = d.side.str.lower() == 'over'
        d['p_side'] = np.where(over, p, 1 - p)
        d['won'] = np.where(over, d[stat] > d.point, d[stat] < d.point)
        d['market_stat'] = market
        rows.append(d)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows)


def roi_ci(b, price_col, n_boot=2000, seed=5):
    if b.empty:
        return np.nan, np.nan, np.nan
    pnl = np.where(b.won, b[price_col] - 1, -1.0)
    by = pd.DataFrame({'r': (b.season.astype(str) + '-' + b.Round.astype(str)).to_numpy(), 'p': pnl}).groupby('r').p.agg(['sum', 'size'])
    idx = np.random.default_rng(seed).integers(0, len(by), (n_boot, len(by)))
    boot = by['sum'].to_numpy()[idx].sum(1) / by['size'].to_numpy()[idx].sum(1)
    return pnl.mean(), np.percentile(boot, 5), np.percentile(boot, 95)


def report(ev):
    out = ['# AFL props against real lines', '',
           'Every projection out of sample (afl/model/walkforward.py). Bet where our chance x the price - 1 clears the edge. '
           'ROI per unit staked; 90% interval resamples whole rounds. CLV = our implied-chance gain from the price taken '
           'to the same book\'s closing price on the same line (positive = we beat the close).', '']
    if ev.empty:
        return out + ['No matched lines yet.']
    ev = ev.copy()
    ev['ev_open'] = ev.p_side * ev.price_open - 1
    ev['ev_close'] = ev.p_side * ev.price_close - 1
    ev['clv'] = 1 / ev.price_close - 1 / ev.price_open
    out += ['## Betting at the open vs at the close', '',
            '| market | edge needed | bets at open | ROI at open | 90% | CLV (pts of chance) | bets at close | ROI at close | 90% |',
            '|---|---|---|---|---|---|---|---|---|']
    for mkt, g in ev.groupby('market_stat'):
        for e in EDGES:
            bo, bc = g[g.ev_open > e], g[g.ev_close > e]
            ro, lo, hi = roi_ci(bo, 'price_open')
            rc, lc, hc = roi_ci(bc, 'price_close')
            out.append(f'| {mkt} | {e:.0%} | {len(bo):,} | {ro:+.1%} | {lo:+.1%} to {hi:+.1%} | {100 * bo.clv.mean():+.2f} | '
                       f'{len(bc):,} | {rc:+.1%} | {lc:+.1%} to {hc:+.1%} |')
    out += ['', '## At the open, 5% edge, by book', '', '| book | bets | ROI | 90% | CLV |', '|---|---|---|---|---|']
    for bk, g in ev[ev.ev_open > 0.05].groupby('book'):
        r, lo, hi = roi_ci(g, 'price_open')
        out.append(f'| {bk} | {len(g):,} | {r:+.1%} | {lo:+.1%} to {hi:+.1%} | {100 * g.clv.mean():+.2f} |')
    out += ['', '## At the open, 5% edge, by line and season', '', '| season | line | bets | ROI | 90% |', '|---|---|---|---|---|']
    b = ev[ev.ev_open > 0.05].copy()
    b['band'] = pd.cut(b.point, [0, 4.5, 14.5, 19.5, 24.5, 100], labels=['0.5-4.5', '5.5-14.5', '15.5-19.5', '20.5-24.5', '25.5+'])
    for (s, band), g in b.groupby(['season', 'band'], observed=True):
        r, lo, hi = roi_ci(g, 'price_open')
        out.append(f'| {s} | {band} | {len(g):,} | {r:+.1%} | {lo:+.1%} to {hi:+.1%} |')
    return out


def run(cache, out_md):
    lines = parse.flatten(RAW)
    if lines.empty:
        print('no saved lines yet: run afl/lines/odds_api.py first')
        return
    lines = parse.match_games(lines, fixture(cache))
    wf = pd.read_parquet(f'{cache}/walkforward.parquet')
    props = parse.match_players(lines[lines.market.isin(STAT_OF)], wf)
    matched = props.player_id.notna().mean()
    ev = evaluate(open_close(props[props.player_id.notna()]), wf)
    rep = report(ev)
    rep.insert(2, f'Lines matched to our players: {matched:.1%} of {len(props):,} prop rows.')
    open(out_md, 'w').write('\n'.join(rep) + '\n')
    print('\n'.join(rep))


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else 'afl/cache', sys.argv[2] if len(sys.argv) > 2 else 'afl/docs/LINES_BACKTEST.md')
