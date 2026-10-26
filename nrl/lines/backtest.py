"""Backtest against REAL prices: our walk-forward probabilities against each book's price at the open (before teams),
after teams are named, and near the close; ROI by market, timing and edge; closing line value; and the stage-2 blend.

Prices: nrl/cache/odds.parquet (parse.py). Ours: team_wf.parquet / tries_wf.parquet (walkforward.py): every season
priced by a model fitted only on earlier seasons. The open snapshot uses the "open" model (no team news); named and
close use "teams named". A bet: our probability x the book's price >= 1 + edge, one unit, at that book's price.
CLV: the de-margined closing probability of the side we backed against the price we took (positive = beat the close).
Usage: python -m nrl.lines.backtest nrl/cache [nrl/docs/LINES_BACKTEST.md]
"""
import re
import sys
import unicodedata

import numpy as np
import pandas as pd
from scipy import stats

from nrl.model.blend import Blend, devig_two_way

EDGES = [0.0, 0.03, 0.05, 0.10]


def key(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z]', '', s)


def link_games(odds, wf):
    """event -> our match_id (home view row): canonical teams, commence within 36 hours of our kick-off."""
    g = wf.drop_duplicates('match_id')[['match_id', 'team', 'opp', 'kick_off']].copy()
    g['ko'] = pd.to_datetime(g.kick_off).dt.tz_localize('Australia/Sydney', ambiguous=True, nonexistent='shift_forward')
    ev = odds.drop_duplicates('event_id')[['event_id', 'home', 'away', 'commence']]
    out = {}
    for e in ev.itertuples():
        c = g[(((g.team == e.home) & (g.opp == e.away)) | ((g.team == e.away) & (g.opp == e.home)))
              & ((g.ko - e.commence).abs() < pd.Timedelta(hours=36))]
        if len(c):
            out[e.event_id] = c.match_id.iloc[0]
    return out


def team_bets(odds, wf):
    link = link_games(odds, wf)
    o = odds[odds.label.str.startswith('team-')].copy()
    o['match_id'] = o.event_id.map(link)
    o = o.dropna(subset=['match_id'])
    w = wf.set_index('match_id')
    bets = []
    for (mid, label, book), q in o.groupby(['match_id', 'label', 'book']):
        r = w.loc[mid]
        kind = label.split('-')[1]
        ver = 'open' if kind == 'open' else 'named'
        mu, sc, df = r[f'mu_{ver}'], r[f'scale_{ver}'], r[f'df_{ver}']
        home = r.team
        for mk, qq in q.groupby('market'):
            if len(qq) != 2:
                continue
            a, b = qq.iloc[0], qq.iloc[1]
            for side, other in ((a, b), (b, a)):
                if mk == 'h2h':
                    p_home = r[f'p_home_{ver}']
                    p = p_home if side.outcome == home else 1 - p_home
                elif mk == 'spreads':
                    # side covers if its margin + point > 0
                    sign = 1 if side.outcome == home else -1
                    p = 1 - stats.t.cdf(-side.point - sign * mu, df, scale=sc) if sign == 1 else \
                        1 - stats.t.cdf(-side.point + mu, df, scale=sc)
                elif mk == 'totals':
                    p_over = 1 - stats.t.cdf(side.point - r.total_mu, r.total_df, scale=r.total_scale)
                    p = p_over if side.outcome == 'Over' else 1 - p_over
                else:
                    continue
                bets.append(dict(match_id=mid, season=r.season, kind=kind, book=book, market=mk, outcome=side.outcome,
                                 point=side.point, price=side.price, p=p, p_mkt=devig_two_way(side.price, other.price),
                                 won=_won(mk, side, home, r)))
    return pd.DataFrame(bets)


def _won(mk, side, home, r):
    m = r.margin if side.outcome == home else -r.margin
    if mk == 'h2h':
        return 1.0 if m > 0 else 0.5 if m == 0 else 0.0
    if mk == 'spreads':
        x = m + side.point
        return 1.0 if x > 0 else 0.5 if x == 0 else 0.0
    x = r.total - side.point if side.outcome == 'Over' else side.point - r.total
    return 1.0 if x > 0 else 0.5 if x == 0 else 0.0


def add_clv(bets):
    # h2h has no point: a missing point never equals itself in a lookup, so key it as 0 (found by the fake-book test)
    pt = bets.point.fillna(0.0)
    c = bets.kind == 'close'
    close = bets[c].assign(pt=pt[c]).groupby(['match_id', 'book', 'market', 'outcome', 'pt']).p_mkt.first()
    k = list(zip(bets.match_id, bets.book, bets.market, bets.outcome, pt))
    bets['p_close'] = [close.get(x, np.nan) for x in k]
    bets['clv'] = bets.p_close * bets.price - 1
    return bets


def summarise(bets, label):
    lines = [f'## {label}', '', '| market | timing | edge | bets | ROI | average CLV | 90% interval (rounds resampled) |',
             '|---|---|---|---|---|---|---|']
    for (mk, kind), q in bets.groupby(['market', 'kind']):
        for e in EDGES:
            b = q[q.p * q.price >= 1 + e]
            if len(b) < 20:
                continue
            ret = np.where(b.won == 1, b.price, np.where(b.won == 0.5, (1 + b.price) / 2 if mk == 'h2h' else 1.0, 0.0))
            roi = ret.mean() - 1
            lo, hi = _boot(b.match_id.to_numpy(), ret)
            lines.append(f'| {mk} | {kind} | {e:.0%} | {len(b):,} | {roi:+.1%} | {b.clv.mean():+.1%} | {lo:+.1%} to {hi:+.1%} |')
    return lines + ['']


def _boot(groups, ret, n=2000, seed=1):
    rng = np.random.default_rng(seed)
    d = pd.DataFrame(dict(g=groups, r=ret)).groupby('g').r.agg(['sum', 'count'])
    idx = rng.integers(0, len(d), size=(n, len(d)))
    s, c = d['sum'].to_numpy()[idx].sum(1), d['count'].to_numpy()[idx].sum(1)
    return np.percentile(s / c - 1, [5, 95])


def blend_report(bets):
    """Stage 2: fit the blend on the older half of seasons, judge on the newer half, per market and timing."""
    out = ['## Stage 2: our price blended with the market (Benter), fitted on older seasons, judged on newer', '',
           '| market | timing | weight ours / market | log loss ours | market | blend |', '|---|---|---|---|---|---|']
    seasons = sorted(bets.season.unique())
    if len(seasons) < 2:
        return out + ['(needs at least two seasons of prices)', '']
    cut = seasons[len(seasons) // 2]
    for (mk, kind), q in bets[bets.won != 0.5].groupby(['market', 'kind']):
        tr, te = q[q.season < cut], q[q.season >= cut]
        if len(tr) < 100 or len(te) < 100:
            continue
        b = Blend().fit(tr.p, tr.p_mkt, tr.won)
        ll = lambda p, y: -np.mean(np.where(y == 1, np.log(np.clip(p, 1e-6, 1)), np.log(np.clip(1 - p, 1e-6, 1))))
        out.append(f'| {mk} | {kind} | {b.a:.2f} / {b.b:.2f} | {ll(te.p, te.won):.4f} | {ll(te.p_mkt, te.won):.4f} | '
                   f'{ll(b.predict(te.p, te.p_mkt), te.won):.4f} |')
    return out + ['']


def main(cache, out=None):
    odds = pd.read_parquet(f'{cache}/odds.parquet')
    wf = pd.read_parquet(f'{cache}/team_wf.parquet')
    bets = add_clv(team_bets(odds, wf))
    bets.to_parquet(f'{cache}/team_bets.parquet', index=False)
    text = '\n'.join(['# Backtest against real prices (team markets)', ''] + summarise(bets, 'Every book, one unit a bet')
                     + blend_report(bets))
    print(text)
    if out:
        open(out, 'w').write(text)


if __name__ == '__main__':
    main(*sys.argv[1:3])
