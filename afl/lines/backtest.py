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


def market_compare(ev):
    """Our chance of each over against the market's, at the close, with the bookmaker's margin taken out.

    Per book: where it closed both sides of a line, its chance of the over = (1/over) / (1/over + 1/under). The
    CONSENSUS is the median of those across books on the same player, market and line: one Australian book's close can
    be a copy of another's, so a single book is not a fair benchmark. Returns one row per player/market/line with our
    chance, the consensus, the number of books and the outcome, for log loss and closing-line value against the consensus.
    """
    if ev.empty:
        return pd.DataFrame()
    keys = ['game', 'player_id', 'market_stat', 'point']
    two = ev.pivot_table(index=keys + ['book'], columns=ev.side.str.lower(), values='price_close', aggfunc='last')
    if not {'over', 'under'} <= set(two.columns):
        return pd.DataFrame()
    two = two.dropna(subset=['over', 'under'])
    two['p_book'] = (1 / two.over) / (1 / two.over + 1 / two.under)
    cons = two.groupby(level=keys).p_book.agg(p_mkt='median', books='size').reset_index()
    ours = ev[ev.side.str.lower() == 'over'].groupby(keys).agg(p_ours=('p_side', 'first'), won=('won', 'first'),
                                                                 season=('season', 'first')).reset_index()
    return cons.merge(ours, on=keys, how='inner')


def _logit(p):
    p = np.clip(np.asarray(p, float), 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


def benter_fit(p_ours, p_mkt, y):
    """Benter's second stage: chance = logistic(a + b x logit(ours) + c x logit(market)), fitted by maximum likelihood.
    b and c say how much weight the data gives our model next to the market (Benter, "Computer based horse race
    handicapping and wagering systems", 1994: the public's odds carry information a fundamental model lacks, and the
    two together beat either alone)."""
    from scipy import optimize
    X = np.column_stack([np.ones(len(y)), _logit(p_ours), _logit(p_mkt)])
    y = np.asarray(y, float)

    def nll(w):
        z = X @ w
        return np.sum(np.logaddexp(0, z) - y * z)
    return optimize.minimize(nll, x0=[0.0, 0.5, 0.5], method='BFGS').x


def benter_apply(w, p_ours, p_mkt):
    z = w[0] + w[1] * _logit(p_ours) + w[2] * _logit(p_mkt)
    return 1 / (1 + np.exp(-z))


def benter(mc, fit_seasons, test_seasons):
    """Fit the blend on earlier seasons, score it on later ones against the market alone and our model alone."""
    f, t = mc[mc.season.isin(fit_seasons)], mc[mc.season.isin(test_seasons)]
    if len(f) < 200 or len(t) < 200:
        return None
    w = benter_fit(f.p_ours, f.p_mkt, f.won.astype(float))
    # the fair comparison: the market's chance refitted on its own (a books' price can be miscalibrated, and refitting
    # alone would improve on it); only what the blend adds beyond that is ours
    wm = benter_fit(np.full(len(f), 0.5), f.p_mkt, f.won.astype(float))
    y = t.won.astype(float).to_numpy()
    pb = benter_apply(w, t.p_ours, t.p_mkt)
    pm = benter_apply(wm, np.full(len(t), 0.5), t.p_mkt)
    ll = {k: log_loss(np.asarray(v), y) for k, v in (('market', t.p_mkt), ('market_refit', pm), ('ours', t.p_ours), ('blend', pb))}
    d = ll['blend'] - ll['market_refit']
    return dict(w=w, lines=len(t), market=ll['market'].mean(), market_refit=ll['market_refit'].mean(), ours=ll['ours'].mean(),
                blend=ll['blend'].mean(), blend_vs_market=d.mean(), se=d.std() / np.sqrt(len(d)), p_blend=pb, rows=t)


def log_loss(p, y):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


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
    mc = market_compare(ev)
    if not mc.empty:
        out += ['', '## Our chances against the market\'s, at the close', '',
                'Log loss of the over (lower is better): ours, and the consensus of the books (median, margin removed). '
                'Positive "ours minus market" means the market was better. This is the honest test of the model: it '
                'needs no bet selection.', '',
                '| market | season | lines | books (median) | ours | market | ours minus market | ± |', '|---|---|---|---|---|---|---|---|']
        for (mkt, season), g in mc.groupby(['market_stat', 'season']):
            y = g.won.astype(float).to_numpy()
            d = log_loss(g.p_ours.to_numpy(), y) - log_loss(g.p_mkt.to_numpy(), y)
            out.append(f'| {mkt} | {season} | {len(g):,} | {g.books.median():.0f} | {log_loss(g.p_ours.to_numpy(), y).mean():.4f} | '
                       f'{log_loss(g.p_mkt.to_numpy(), y).mean():.4f} | {d.mean():+.4f} | {d.std() / np.sqrt(len(d)):.4f} |')
        seasons = sorted(mc.season.unique())
        if len(seasons) >= 2:
            out += ['', '## Benter blend: our chance and the market\'s, together', '',
                    'chance = logistic(a + b x logit(ours) + c x logit(market)), fitted on the earlier seasons and scored on the '
                    'last. If the blend beats the market (refitted on its own, so a miscalibrated price is not credited to us), our model carries information the market does not, and '
                    'the blend (not our raw chance) is what bets should be judged on.', '',
                    '| market | fitted on | scored on | lines | weight on ours (b) | weight on market (c) | log loss: market | market refitted | ours | blend | blend minus refitted market | ± |',
                    '|---|---|---|---|---|---|---|---|---|---|---|---|']
            for mkt, g in mc.groupby('market_stat'):
                r = benter(g, seasons[:-1], seasons[-1:])
                if r:
                    out.append(f'| {mkt} | {seasons[0]}-{seasons[-2]} | {seasons[-1]} | {r["lines"]:,} | {r["w"][1]:+.2f} | {r["w"][2]:+.2f} | '
                               f'{r["market"]:.4f} | {r["market_refit"]:.4f} | {r["ours"]:.4f} | {r["blend"]:.4f} | {r["blend_vs_market"]:+.4f} | {r["se"]:.4f} |')
        b = ev[ev.ev_open > 0.05].merge(mc[['game', 'player_id', 'market_stat', 'point', 'p_mkt']],
                                         on=['game', 'player_id', 'market_stat', 'point'], how='inner')
        if len(b):
            b['p_mkt_side'] = np.where(b.side.str.lower() == 'over', b.p_mkt, 1 - b.p_mkt)
            b['clv_cons'] = b.price_open * b.p_mkt_side - 1
            out += ['', '## Closing-line value against the consensus (bets at the open, 5% edge)', '',
                    'Expected return of the price taken if the consensus close is the truth. Positive and steady is the '
                    'sign of a real edge long before profit can show one.', '',
                    '| market | bets | average | share positive |', '|---|---|---|---|']
            for mkt, g in b.groupby('market_stat'):
                out.append(f'| {mkt} | {len(g):,} | {g.clv_cons.mean():+.2%} | {(g.clv_cons > 0).mean():.0%} |')
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
