"""The paper-season ledger: every bet we would have placed, the price we took, the closing price, the result.

One CSV (afl/paper/ledger.csv by default). Three steps, each its own call, so the record shows what was known when:
  log    the bets, with our chance and projection (mu, a) and the book's price at the time
  close  the closing line and both prices, per bet
  settle the stat each player recorded (a player who did not take the field is void)

Closing-line value (CLV) is the main measure, because results take thousands of bets to separate skill from luck and
CLV takes hundreds: CLV = price taken x (the close's chance of our side, margin removed) - 1. If the line moved, the
close's chance is moved to our line by the difference our own model sees between the two lines.

Paper only: nothing here contacts a bookmaker.

Usage: python -m afl.betting.ledger summary [ledger.csv]
"""
import os
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from scipy import stats

PATH = 'afl/paper/ledger.csv'
COLUMNS = ['bet_id', 'logged_at', 'season', 'round', 'game', 'team', 'player', 'player_id', 'stat', 'side', 'line',
           'price', 'book', 'p_model', 'mu', 'a', 'stake', 'close_line', 'close_over', 'close_under', 'value', 'outcome',
           'pnl', 'clv']
KEY = ['game', 'player_id', 'stat', 'side', 'line', 'book']


def load(path=PATH):
    if not os.path.exists(path):
        return pd.DataFrame(columns=COLUMNS)
    return pd.read_csv(path)


def save(df, path=PATH):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    df[COLUMNS].to_csv(path, index=False)


def p_over(line, mu, a):
    n = 1 / a
    return 1 - stats.nbinom.cdf(np.floor(line), n, n / (n + mu))


def log_bets(bets, path=PATH, now=None):
    """Append bets. Refuses a bet already in the ledger (same game, player, stat, side, line, book)."""
    led = load(path)
    b = bets.copy()
    for c in COLUMNS:
        if c not in b:
            b[c] = np.nan
    if len(led):
        dup = b.merge(led[KEY], on=KEY, how='inner')
        if len(dup):
            raise ValueError(f'{len(dup)} bets already logged, e.g. {dup.iloc[0][KEY].to_dict()}')
    start = int(led.bet_id.max()) + 1 if len(led) else 1
    b['bet_id'] = range(start, start + len(b))
    b['logged_at'] = (now or datetime.now(timezone.utc)).isoformat(timespec='seconds')
    out = pd.concat([led, b[COLUMNS]], ignore_index=True) if len(led) else b[COLUMNS]
    save(out, path)
    return out


def novig_over(over, under):
    io, iu = 1 / over, 1 / under
    return io / (io + iu)


def clv(row):
    """Expected return at the close's chance of our side (margin removed), moved to our line if the line moved."""
    if pd.isna(row.close_over) or pd.isna(row.close_under) or pd.isna(row.close_line):
        return np.nan
    p = novig_over(row.close_over, row.close_under)
    if row.close_line != row.line and pd.notna(row.mu):
        p = p + p_over(row.line, row.mu, row.a) - p_over(row.close_line, row.mu, row.a)
    p = float(np.clip(p, 0.001, 0.999))
    return row.price * (p if row.side == 'over' else 1 - p) - 1


def record_close(closes, path=PATH):
    """closes: game, player_id, stat, close_line, close_over, close_under (optionally book)."""
    led = load(path)
    on = ['game', 'player_id', 'stat'] + (['book'] if 'book' in closes else [])
    led = led.drop(columns=['close_line', 'close_over', 'close_under']).merge(
        closes[on + ['close_line', 'close_over', 'close_under']], on=on, how='left')
    led['clv'] = led.apply(clv, axis=1)
    save(led, path)
    return led


def settle(results, path=PATH):
    """results: game, player_id, stat, value (what the player recorded). A logged bet with no result row is void
    only when `played` is given and false; otherwise it is left open."""
    led = load(path).drop(columns=['value'])
    led = led.merge(results[['game', 'player_id', 'stat', 'value'] + (['played'] if 'played' in results else [])],
                    on=['game', 'player_id', 'stat'], how='left')
    over_won = led.value > led.line
    push = led.value == led.line
    won = np.where(led.side == 'over', over_won, (led.value < led.line))
    led['outcome'] = pd.Series(np.where(push, 'push', np.where(won, 'win', 'loss')), index=led.index, dtype=object).where(led.value.notna())
    if 'played' in led:
        led.loc[led.played == False, 'outcome'] = 'void'  # noqa: E712
        led = led.drop(columns=['played'])
    led['pnl'] = np.select([led.outcome == 'win', led.outcome == 'loss'], [led.stake * (led.price - 1), -led.stake],
                           default=np.where(led.outcome.isin(['push', 'void']), 0.0, np.nan))
    save(led, path)
    return led


def summary(path=PATH):
    led = load(path)
    s = led[led.outcome.isin(['win', 'loss', 'push'])]
    rows = []
    for k, g in [('all', s)] + list(s.groupby('stat')):
        staked = g.stake.sum()
        rows.append({'stat': k, 'bets': len(g), 'staked': staked, 'profit': g.pnl.sum(),
                     'roi': g.pnl.sum() / staked if staked else np.nan,
                     'avg_clv': g.clv.mean(), 'beat_close': (g.clv > 0).mean() if g.clv.notna().any() else np.nan})
    return pd.DataFrame(rows)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'summary':
        print(summary(sys.argv[2] if len(sys.argv) > 2 else PATH).to_string(index=False))
