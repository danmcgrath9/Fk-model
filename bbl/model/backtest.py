"""Prop backtest against STAND-IN lines. A proxy, not a market test: no real BBL prop lines exist yet.

The stand-in line is how books are said to set player lines: off the player's recent average. Line =
floor(k x his last-10 average) + 0.5, with k tuned on the fit-era seasons (2018/19-2021/22) so a blind
over wins half the time there. Both sides at 1.87 (a typical Australian prop price, 7% margin).

That works for runs. For sixes and wickets the counts are too small for any whole-number line to split
half and half (a blind over on a WBBL sixes line wins about a fifth of the time), so no return is reported
for them: a fixed 1.87 both ways hands the under a free win, and a stand-in price from a ten-game average
is far softer than a real book. priced()/priced_bets() are the rule for real prices when they exist.

Graded only when the player batted (runs, sixes) or bowled (wickets): the bet a book voids otherwise.
Players offered: batters with a usual position of 5 or higher and 10+ prior T20 innings; bowlers who
bowled in 80%+ of recent games. The betting threshold (our chance on the chosen side) is chosen on the
choose seasons (2022/23-2023/24) and then applied unchanged to 2024/25. Profit is bootstrapped by
round (game week), because one week's games share conditions and selections.

Usage: python -m bbl.model.backtest bbl/cache/parquet  (writes PROPS.md)
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

from bbl.model.props import p_over_nb
from bbl.model.team import CHOOSE, CONFIRM, EVAL_SEASONS, md

FIT_ERA = EVAL_SEASONS[:4]
PRICE = 1.87
THRESHOLDS = [0.54, 0.56, 0.58, 0.60, 0.62]
EDGES = [0.0, 0.05, 0.10, 0.15, 0.20]
MARGIN = 1.07
PRICED = {'sixes': (0.5, 1.5), 'wickets': (0.5, 1.5)}


def recent_averages(d):
    """Last-10 simple averages from the player's PRIOR games only (what a book's trader sees)."""
    g = pd.read_parquet(os.path.join(d, 'player_frame.parquet'),
                        columns=['match_id', 'pid', 'dt', 'did_bat', 'bat_runs', 'bat_6s', 'did_bowl', 'bowl_wkts'])
    g = g.sort_values(['dt', 'match_id'])
    out = g[['match_id', 'pid']].copy()
    for col, cond, name in (('bat_runs', 'did_bat', 'avg_runs'), ('bat_6s', 'did_bat', 'avg_6s'), ('bowl_wkts', 'did_bowl', 'avg_wkts')):
        v = g[col].where(g[cond] == 1)
        out[name] = v.groupby(g.pid).transform(lambda s: s.shift(1).rolling(40, min_periods=1).apply(
            lambda a: np.nanmean(a[~np.isnan(a)][-10:]) if (~np.isnan(a)).sum() else np.nan, raw=True))
        out[name.replace('avg', 'n')] = g[cond].groupby(g.pid).transform(lambda s: s.shift(1).cumsum())
    return out


def market_rows(p, avg):
    x = p.merge(avg, on=['match_id', 'pid'], how='left')
    rows = []
    bat = x[(x.pre_pos_ewm <= 5) & (x.n_runs >= 10)]
    for market, mu, r, avgc, y, played in (('runs', 'mu_runs', 'r_runs', 'avg_runs', 'bat_runs', 'did_bat'),
                                           ('sixes', 'mu_6s', 'r_6s', 'avg_6s', 'bat_6s', 'did_bat')):
        rows.append(bat.assign(market=market, mu=bat[mu], r=bat[r], avg=bat[avgc], y=bat[y], played=bat[played]))
    bw = x[(x.p_bowl >= 0.8) & (x.n_wkts >= 10)]
    rows.append(bw.assign(market='wickets', mu=bw.mu_wkts, r=bw.r_wkts, avg=bw.avg_wkts, y=bw.bowl_wkts, played=bw.did_bowl))
    return pd.concat(rows, ignore_index=True)


def tune_k(rows):
    """Per market, the k that makes a blind over win closest to half in the fit era (graded rows only)."""
    ks = {}
    for market, g in rows[rows.season.isin(FIT_ERA) & (rows.played == 1)].groupby('market'):
        best = min(np.arange(0.5, 1.5, 0.01), key=lambda k: abs((g.y > np.floor(k * g.avg) + 0.5).mean() - 0.5))
        ks[market] = float(best)
    return ks


def with_lines(rows, ks):
    rows = rows.copy()
    rows['line'] = np.floor(rows.market.map(ks) * rows.avg) + 0.5
    rows['p_over'] = p_over_nb(rows.line, rows.mu, rows.r)
    rows['over_won'] = (rows.y > rows.line).astype(int)
    return rows[(rows.played == 1) & rows.avg.notna()]


def bets(rows, thr):
    b = rows.copy()
    b['side'] = np.where(b.p_over >= thr, 'over', np.where(1 - b.p_over >= thr, 'under', None))
    b = b[b.side.notna()].copy()
    b['won'] = np.where(b.side == 'over', b.over_won, 1 - b.over_won)
    b['profit'] = np.where(b.won == 1, PRICE - 1, -1.0)
    b['round'] = b.season + '|' + b.dt.dt.isocalendar().week.astype(str)
    return b


def bootstrap(b, n=4000, seed=0):
    rng = np.random.default_rng(seed)
    by = b.groupby('round').profit.agg(['sum', 'size'])
    if len(by) < 2:
        return np.nan, np.nan
    idx = rng.integers(0, len(by), size=(n, len(by)))
    roi = by['sum'].to_numpy()[idx].sum(1) / by['size'].to_numpy()[idx].sum(1)
    return np.percentile(roi, 5), np.percentile(roi, 95)


def summary(b):
    lo, hi = bootstrap(b)
    return dict(bets=len(b), hit=b.won.mean() if len(b) else np.nan, roi=b.profit.mean() if len(b) else np.nan,
                roi_5=lo, roi_95=hi, rounds=b['round'].nunique() if len(b) else 0)


def priced(rows):
    """Sixes and wickets at the 0.5 and 1.5 lines, against a stand-in price from the last-10 average."""
    out = []
    for market, lines in PRICED.items():
        g = rows[rows.market == market]
        for line in lines:
            h = g.assign(line=line)
            book = stats.poisson.sf(np.floor(line), h.avg.clip(1e-6))
            h = h.assign(p_book=book, p_over=p_over_nb(line, h.mu, h.r), over_won=(h.y > line).astype(int))
            out.append(h[(h.p_book >= 0.1) & (h.p_book <= 0.9)])     # a line a book would actually offer
    x = pd.concat(out, ignore_index=True)
    x['odds_over'] = 1 / (MARGIN * x.p_book)
    x['odds_under'] = 1 / (MARGIN * (1 - x.p_book))
    return x


def priced_bets(x, edge):
    ev_o = x.p_over * x.odds_over - 1
    ev_u = (1 - x.p_over) * x.odds_under - 1
    b = x.assign(side=np.where((ev_o >= edge) & (ev_o >= ev_u), 'over', np.where(ev_u >= edge, 'under', None)))
    b = b[b.side.notna()].copy()
    b['won'] = np.where(b.side == 'over', b.over_won, 1 - b.over_won)
    b['profit'] = np.where(b.won == 1, np.where(b.side == 'over', b.odds_over, b.odds_under) - 1, -1.0)
    b['round'] = b.season + '|' + b.dt.dt.isocalendar().week.astype(str)
    return b


def projection_table(rows):
    """Our mean against his last-10 average, and log-likelihood of our distribution against one centred on the average."""
    out = []
    for (market, comp), g in rows.groupby(['market', 'comp']):
        for group, seasons in (('choose', CHOOSE), ('confirm', CONFIRM)):
            h = g[g.season.isin(seasons)]
            if h.empty:
                continue
            r_avg = h.r  # same spread, centred on the average: isolates the value of the mean
            ll_ours = stats.nbinom.logpmf(h.y, h.r, h.r / (h.r + h.mu.clip(1e-6))).mean()
            ll_avg = stats.nbinom.logpmf(h.y, r_avg, r_avg / (r_avg + h.avg.clip(1e-6))).mean()
            out.append(dict(market=market, comp=comp, seasons=group, n=len(h), miss_ours=(h.y - h.mu).abs().mean(),
                            miss_last10=(h.y - h.avg).abs().mean(), loglik_gain=ll_ours - ll_avg))
    return pd.DataFrame(out)


def calibration(rows):
    h = rows[rows.season.isin(CHOOSE + CONFIRM)].copy()
    h['bin'] = pd.cut(h.p_over, [0, 0.3, 0.4, 0.45, 0.5, 0.55, 0.6, 0.7, 1])
    c = h.groupby(['market', 'bin'], observed=True).agg(n=('over_won', 'size'), said=('p_over', 'mean'), happened=('over_won', 'mean')).reset_index()
    c['bin'] = c.bin.astype(str)
    return c


def report(d):
    p = pd.read_parquet(os.path.join(d, 'props_preds.parquet'))
    rows = market_rows(p, recent_averages(d))
    ks = tune_k(rows)
    rows = with_lines(rows, ks)
    lines = ['# BBL and WBBL player props: backtest against STAND-IN lines (a proxy, not a market test)', '',
             'Stand-in line: floor(k x last-10 average) + 0.5, k tuned on 2018/19-2021/22 so a blind over wins half the time: '
             + ', '.join(f'{m} k={k:.2f}' for m, k in ks.items()) + '. Both sides at 1.87 (runs only; see below for sixes and wickets). Graded only when the player batted '
             '(runs, sixes) or bowled (wickets). Threshold chosen on 2022/23-2023/24, applied unchanged to 2024/25. '
             '2025/26 held back. 90% intervals: game weeks resampled.', '']
    blind = rows.groupby(['market', 'comp', rows.season.isin(FIT_ERA).map({True: 'fit era', False: 'later'})]).over_won.mean().unstack()
    lines += ['## Blind over hit rate (should be near 50% in the fit era)', '', md(blind.reset_index()), '']
    lines += ['## Projections: our mean against the last-10 average', '',
              'miss = average absolute miss; loglik_gain = average log-likelihood per player-game of our distribution over the '
              'same distribution centred on the last-10 average (above 0: ours is better).', '', md(projection_table(rows)), '']
    lines += ['## Calibration of P(over), 2022/23-2024/25', '', md(calibration(rows)), '']
    res, chosen = [], {}
    for (market, comp), g in rows[rows.market == 'runs'].groupby(['market', 'comp']):
        ch = {thr: summary(bets(g[g.season.isin(CHOOSE)], thr)) for thr in THRESHOLDS}
        # choose the threshold with the best choose-season ROI among those with 100+ bets
        ok = {t: s for t, s in ch.items() if s['bets'] >= 100}
        thr = max(ok, key=lambda t: ok[t]['roi']) if ok else max(THRESHOLDS)
        chosen[(market, comp)] = thr
        for group, seasons in (('choose', CHOOSE), ('confirm', CONFIRM)):
            s = summary(bets(g[g.season.isin(seasons)], thr))
            res.append(dict(market=market, comp=comp, seasons=group, threshold=thr, **s))
    lines += ['## Runs: bets at the chosen threshold (stand-in line, 1.87 both ways)', '', md(pd.DataFrame(res)), '']
    # Sixes and wickets: no ROI is reported against a stand-in. A Poisson "book" around a ten-game average
    # prices a player with one six in ten games at 9.3 for a six; a real book shrinks that, so the stand-in
    # shows +40% to +70% returns that say nothing about a real market. priced()/priced_bets() are kept for
    # the real prices: the same rule (our chance x price - 1 >= edge) runs on recorded odds.
    lines += ['## Sixes and wickets: no return reported', '',
              'No fair stand-in exists for these: the counts are too small for a fixed line at 1.87, and a stand-in price '
              'built from a ten-game average is far softer than any real book (it showed +40% to +70%, which is the stand-in '
              'failing, not an edge). The projections and calibration above are the evidence until real prices are recorded.', '']
    # where the edge sits: runs by line size, confirm season
    rr = bets(rows[(rows.market == 'runs') & rows.season.isin(CONFIRM)], 0.56)
    if len(rr):
        rr['line_band'] = pd.cut(rr.line, [0, 15, 25, 35, 200]).astype(str)
        by = rr.groupby(['comp', 'line_band', 'side']).agg(bets=('won', 'size'), hit=('won', 'mean'), roi=('profit', 'mean')).reset_index()
        lines += ['## Runs, 2024/25, threshold 0.56: by line size and side', '', md(by), '']
    text = '\n'.join(lines)
    open(os.path.join(d, 'PROPS.md'), 'w').write(text)
    print(text)


if __name__ == '__main__':
    report(sys.argv[1])
