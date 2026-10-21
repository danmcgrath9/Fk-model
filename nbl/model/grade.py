"""Grade our saved prices against what happened: the paper season's own scorecard.

Reads every prices_<date>.csv (nbl/model/price_round.py), keeps for each game the last sheet priced
before the tip, and scores it once the game is in the results:
  head-to-head  our home win chance against who won
  line, total   our chance at each priced line against the result (a push is left out)
  props         our over chance at each priced line against the player's figure; a player who did not
                take the court is left out (void at Australian books)
Brier score and log loss (lower is better), how often the side we made favourite won, and our chance in
bands against how often it happened. No book prices are involved yet: when recorded lines exist, closing
line value is added beside this.

Usage: python -m nbl.model.grade nbl/cache <dir with prices_*.csv> <out.md>
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

from nbl.model.frame import base_games, base_players, name_key


def load_sheets(price_dir):
    files = sorted(glob.glob(os.path.join(price_dir, 'prices_*.csv')))
    if not files:
        return pd.DataFrame()
    s = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    s['tip'] = pd.to_datetime(s.tip, utc=True)
    s['priced_at'] = pd.to_datetime(s.priced_at, utc=True)
    s = s[s.priced_at < s.tip]
    # the last sheet before each game's tip
    last = s.groupby('game').priced_at.transform('max')
    return s[s.priced_at == last].copy()


def outcomes(sheet, games, players):
    """One row per priced chance with what happened: y = 1 if the priced side won, NaN if void or a push."""
    g = games.set_index('game')
    s = sheet[sheet.game.isin(g.index[~g.scheduled])].copy()
    if s.empty:
        return s.assign(y=pd.Series(dtype=float))
    hm = (g.home_score - g.away_score).reindex(s.game).to_numpy()
    tot = (g.home_score + g.away_score).reindex(s.game).to_numpy()
    y = np.full(len(s), np.nan)
    h2h = (s.market == 'h2h').to_numpy()
    home = (s.side == 'home').to_numpy()
    y[h2h & home] = (hm[h2h & home] > 0).astype(float)
    y[h2h & ~home] = (hm[h2h & ~home] < 0).astype(float)
    ln = (s.market == 'line').to_numpy()
    cover = hm + s.line.to_numpy()
    y[ln] = np.where(cover[ln] == 0, np.nan, (cover[ln] > 0).astype(float))
    tl = (s.market == 'total').to_numpy()
    y[tl] = np.where(tot[tl] == s.line.to_numpy()[tl], np.nan, (tot[tl] > s.line.to_numpy()[tl]).astype(float))
    s['actual_margin'], s['actual_total'] = hm, tot
    pr = (s.kind == 'prop').to_numpy()
    if pr.any():
        pl = players[players.game.isin(s.game)].copy()
        pl['pkey'] = [name_key(n, '') for n in pl.player]
        s['pkey'] = [name_key(n, '') if isinstance(n, str) else '' for n in s.player]
        stat = {}
        for mk in ['pts', 'reb', 'ast', 'fg3m', 'pra']:
            stat.update({(r.game, r.pkey, mk): (r[mk] if r['played'] == 1 else np.nan) for _, r in pl.iterrows()})
        vals = np.array([stat.get((gm, k, mk), np.nan) for gm, k, mk in zip(s.game, s.pkey, s.market)], float)
        s['actual'] = np.where(pr, vals, np.nan)
        y[pr] = np.where(np.isnan(vals[pr]), np.nan, (vals[pr] > s.line.to_numpy()[pr]).astype(float))
    s['y'] = y
    return s


def score(d):
    d = d[d.y.notna()]
    if d.empty:
        return None
    p = np.clip(d.p.to_numpy(float), 1e-6, 1 - 1e-6)
    y = d.y.to_numpy(float)
    return dict(n=len(d), brier=float(np.mean((p - y) ** 2)), ll=float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))),
                fav_won=float(np.mean((p > 0.5) == (y == 1))), mean_p=float(p.mean()), hit=float(y.mean()))


def report(s):
    L = ['# NBL paper season: how our prices have done', '']
    if s.empty or s.y.notna().sum() == 0:
        return '\n'.join(L + ['No priced game has been played yet.']) + '\n'
    games_n = s[s.y.notna()].game.nunique()
    L += [f'{games_n} games graded, from the last sheet priced before each tip. Lower Brier and log loss is better; a coin '
          'flip is 0.250 and 0.693. No book prices yet, so this is accuracy only, not profit.', '',
          '| market | chances | Brier | log loss | favourite won | our average chance | it happened |', '|---|---|---|---|---|---|---|']
    for (kind, mk), d in s.groupby(['kind', 'market']):
        if mk == 'h2h':
            d = d[d.side == 'home']
        r = score(d)
        if r:
            L.append(f'| {mk} | {r["n"]:,} | {r["brier"]:.3f} | {r["ll"]:.3f} | {r["fav_won"]:.0%} | {r["mean_p"]:.0%} | {r["hit"]:.0%} |')
    h = s[(s.market == 'h2h') & (s.side == 'home') & s.y.notna()]
    if len(h):
        L += ['', f'Margin: we missed by {np.abs(h.mu - h.actual_margin).mean():.1f} points a game on average ({len(h)} games).']
    t = s[(s.market == 'total') & s.y.notna()].drop_duplicates('game')
    if len(t):
        L.append(f'Total: we missed by {np.abs(t.mu - t.actual_total).mean():.1f} points a game on average.')
    pr = s[(s.kind == 'prop') & s.y.notna()].copy()
    if len(pr):
        L += ['', '## Props: our over chance against how often the over came in', '', '| our over chance | chances | over came in |',
              '|---|---|---|']
        pr['band'] = pd.cut(pr.p, [0, .2, .35, .5, .65, .8, 1])
        for b, d in pr.groupby('band', observed=True):
            L.append(f'| {b.left:.0%} to {b.right:.0%} | {len(d):,} | {d.y.mean():.0%} |')
        void = s[(s.kind == 'prop') & s.y.isna()].drop_duplicates(['game', 'player']).shape[0]
        L += ['', f'{void} priced players did not take the court (their props are void and left out).']
    return '\n'.join(L) + '\n'


def run(cache, price_dir, out_md):
    games = base_games(pd.read_parquet(f'{cache}/results.parquet'), scheduled_until=pd.Timestamp.now(tz='UTC') + pd.Timedelta(days=30))
    players = base_players(pd.read_parquet(f'{cache}/box_player.parquet'), games[~games.scheduled])
    s = outcomes(load_sheets(price_dir), games, players)
    text = report(s)
    open(out_md, 'w').write(text)
    print(text)


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2], sys.argv[3])
