"""Live odds for the 2027 paper season: snapshot the books, compare with our sheet, log paper bets, record the close,
settle. Paper only: nothing here places a bet or talks to BetMatic.

Costs (the provider's v4 docs): listing events is free; one event's odds cost 1 credit per market per region, so a
snapshot of the four prop markets and three team markets in the AU region is about 7 credits a game.

Snapshots are saved in the same shape as the historical pull ({"timestamp", "data"}) under afl/cache/lines/live/odds/,
one file per event and label, and an event's label is never fetched twice. Labels:
  teams   after the teams are named (Thursday night): the prices the paper bets are taken at
  close   the last hour before the bounce: the closing line for closing-line value

Steps (each a CLI command, run by the afl live workflow once ODDS_API_KEY is set):
  python -m afl.lines.live snapshot teams --hours 168
  python -m afl.lines.live snapshot close --hours 1
  python -m afl.lines.live bets afl/cache/live_2027_R1.csv          # paper bets at the teams prices
  python -m afl.lines.live close                                    # closing prices onto the ledger
  python -m afl.lines.live settle afl/cache                         # results from the latest stats
"""
import argparse
import datetime as dt
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

from afl.betting import ledger as L
from afl.betting import staking as S
from afl.lines import parse
from afl.lines.odds_api import BASE, PROPS, SPORT, TEAM_MARKETS

LIVE = 'afl/cache/lines/live'
STAT_OF = {'player_disposals': 'D', 'player_marks_over': 'M', 'player_tackles_over': 'T', 'player_goals_scored_over': 'G'}
EDGE = 0.05          # our chance x the best price - 1 must clear this
# Rounds 1-3: the projection misses by more (3.85 disposals against 3.70 later, 2025-2026) and its level swings with
# each summer's rule changes (+0.86 disposals under-projected early 2026, -0.09 early 2024), so ask for more edge.
# A caution, not a tested edge: it only means fewer paper bets in the first three rounds.
EARLY_EDGE, EARLY_ROUNDS = 0.08, 3
PAPER_BANK = 10_000  # a notional bank for paper stakes


def _get(path, params, key):
    import requests
    r = requests.get(f'{BASE}{path}', params={**params, 'apiKey': key}, timeout=60)
    if r.status_code != 200:
        # never echo the URL: it carries the key
        raise RuntimeError(f'HTTP {r.status_code}: {r.text[:200]}')
    return r.json(), int(float(r.headers.get('x-requests-last', 0) or 0)), r.headers.get('x-requests-remaining')


def snapshot(label, hours, key, max_credits=200, now=None, fetch=_get, out=LIVE):
    """Odds for every event starting within `hours`, once per event and label. Returns credits spent."""
    now = now or dt.datetime.now(dt.timezone.utc)
    events, _, _ = fetch(f'/sports/{SPORT}/events', {}, key)            # free
    markets = PROPS + TEAM_MARKETS
    spent = 0
    for e in sorted(events, key=lambda e: e['commence_time']):
        start = dt.datetime.fromisoformat(e['commence_time'].replace('Z', '+00:00'))
        if not (now < start <= now + dt.timedelta(hours=hours)):
            continue
        path = f'{out}/odds/{e["id"]}/{label}.json'
        if os.path.exists(path):
            continue
        if spent + len(markets) > max_credits:
            print(f'stopping: the next call would pass {max_credits} credits (spent {spent})')
            break
        body, cost, left = fetch(f'/sports/{SPORT}/events/{e["id"]}/odds',
                                 {'regions': 'au', 'markets': ','.join(markets), 'oddsFormat': 'decimal'}, key)
        spent += cost
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump({'timestamp': now.strftime('%Y-%m-%dT%H:%M:%SZ'), 'data': body}, open(path, 'w'))
        print(f'{label}: {e["home_team"]} v {e["away_team"]}, {cost} credits ({left} left)')
    return spent


def lines_for(label, sheet, out=LIVE):
    """Prop prices at one label's snapshots, matched to the sheet's games and players."""
    lines = parse.flatten(out, label)
    if lines.empty:
        return lines
    # our game key is date|home|away (afl/model/frame.py)
    fx = sheet.drop_duplicates('game')[['game']].assign(
        date=lambda d: d.game.str.split('|').str[0], home=lambda d: d.game.str.split('|').str[1],
        away=lambda d: d.game.str.split('|').str[2])
    lines = parse.match_games(lines, fx)
    props = parse.match_players(lines[lines.market.isin(STAT_OF) & lines.game.notna()], sheet)
    return props[props.player_id.notna()]


def p_over(mu, a, point):
    n = 1 / np.asarray(a, float)
    return 1 - stats.nbinom.cdf(np.floor(point), n, n / (n + np.asarray(mu, float)))


def candidates(sheet, props, edge=EDGE):
    """Best price per player, market, line and side across books; kept where our chance x price - 1 > edge."""
    if props.empty:
        return pd.DataFrame()
    props = props.copy()
    props['stat'] = props.market.map(STAT_OF)
    best = props.sort_values('price').groupby(['game', 'player_id', 'stat', 'point', 'side']).tail(1)
    sh = sheet.set_index(['game', 'player_id'])
    rows = []
    for r in best.itertuples():
        if (r.game, r.player_id) not in sh.index:
            continue
        x = sh.loc[(r.game, r.player_id)]
        mu, a = x[f'mu_{r.stat}'], x[f'a_{r.stat}']
        if pd.isna(mu):
            continue
        po = float(p_over(mu, a, r.point))
        p = po if str(r.side).lower() == 'over' else 1 - po
        rows.append(dict(game=r.game, team=x.team, player=x.Player, player_id=r.player_id, stat=r.stat,
                         side=str(r.side).lower(), line=r.point, price=r.price, book=r.book, p=p, p_model=p,
                         mu=mu, a=a, ev=p * r.price - 1, season=x.season, round=x.Round))
    c = pd.DataFrame(rows)
    if c.empty:
        return c
    rnd = pd.to_numeric(c['round'], errors='coerce')
    c = c[c.ev > np.where(rnd <= EARLY_ROUNDS, max(edge, EARLY_EDGE), edge)]
    # one side per player, stat and line (the better one), and one line per player and stat (the bigger edge)
    return c.sort_values('ev', ascending=False).drop_duplicates(['game', 'player_id', 'stat'])


def bets(sheet_csv, label='teams', edge=EDGE, bank=PAPER_BANK, ledger=L.PATH, out=LIVE):
    sheet = pd.read_csv(sheet_csv)
    c = candidates(sheet, lines_for(label, sheet, out), edge)
    if c.empty:
        print('no paper bets: no line clears the edge (or no lines yet)')
        return c
    # a round priced again (final teams, the sub named) keeps the bets already logged: never logged twice
    led = L.load(ledger)
    if len(led):
        done = set(zip(led.game, led.player_id.astype(float), led.stat))
        c = c[[(g, float(p), s) not in done for g, p, s in zip(c.game, c.player_id, c.stat)]]
        if c.empty:
            print('every paper bet on this sheet is already logged')
            return c
    staked = S.stakes(c, bank)
    staked = staked[staked.stake > 0]
    L.log_bets(staked.drop(columns=['p', 'ev', 'kelly', 'shrink']), ledger)
    print(f'{len(staked)} paper bets logged, {staked.stake.sum():.0f} staked on a {bank:,} paper bank')
    return staked


def close(ledger=L.PATH, out=LIVE):
    """The same book's closing prices on each logged bet: the same line if it closed, else its nearest line."""
    led = L.load(ledger)
    if led.empty:
        return led
    sheet = led.rename(columns={'player': 'Player'})[['game', 'player_id', 'Player']].drop_duplicates()
    p = lines_for('close', sheet, out)
    if p.empty:
        print('no closing snapshots yet')
        return led
    p['stat'] = p.market.map(STAT_OF)
    two = p.pivot_table(index=['game', 'player_id', 'stat', 'book', 'point'], columns=p.side.str.lower(), values='price', aggfunc='last').reset_index()
    if not {'over', 'under'} <= set(two.columns):
        print('closing lines carry no two-way prices; closing-line value needs both sides')
        return led
    rows = []
    for b in led.itertuples():
        g = two[(two.game == b.game) & (two.player_id == b.player_id) & (two.stat == b.stat) & (two.book == b.book)].dropna(subset=['over', 'under'])
        if g.empty:
            continue
        x = g.iloc[(g.point - b.line).abs().argsort().iloc[0]]
        rows.append(dict(game=b.game, player_id=b.player_id, stat=b.stat, book=b.book, close_line=x.point,
                         close_over=x.over, close_under=x.under))
    if not rows:
        return led
    return L.record_close(pd.DataFrame(rows), ledger)


def settle(cache, ledger=L.PATH):
    """Results from the latest stats (afl/data/mirror.py): a player not in the game's stats did not play (void)."""
    from afl.model import frame as F
    led = L.load(ledger)
    if led.empty:
        return led
    m = F.base_table(pd.read_parquet(f'{cache}/afltables.parquet'), pd.read_parquet(f'{cache}/footywire.parquet'))
    played_games = set(m.game)
    rows = []
    for b in led[led.outcome.isna()].itertuples():
        if b.game not in played_games:
            continue
        x = m[(m.game == b.game) & (m.player_id == b.player_id)]
        rows.append(dict(game=b.game, player_id=b.player_id, stat=b.stat, value=x[b.stat].iloc[0] if len(x) else np.nan,
                         played=bool(len(x))))
    if not rows:
        print('nothing to settle yet')
        return led
    return L.settle(pd.DataFrame(rows), ledger)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('step', choices=['snapshot', 'bets', 'close', 'settle'])
    ap.add_argument('arg', nargs='?')
    ap.add_argument('--hours', type=float, default=168)
    ap.add_argument('--max-credits', type=int, default=200)
    a = ap.parse_args()
    if a.step == 'snapshot':
        key = os.environ.get('ODDS_API_KEY', '')
        if not key:
            print('ODDS_API_KEY is not set; nothing fetched')
            return
        print(f'spent {snapshot(a.arg or "teams", a.hours, key, a.max_credits)} credits')
    elif a.step == 'bets':
        bets(a.arg)
    elif a.step == 'close':
        close()
    else:
        settle(a.arg or 'afl/cache')


if __name__ == '__main__':
    main()
