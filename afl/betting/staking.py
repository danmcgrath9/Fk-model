"""Stakes for a round of paper bets: fractional Kelly, shrunk for bets that tend to win or lose together.

Kelly says stake (p x price - 1) / (price - 1) of the bank on a bet with chance p at decimal price `price`. We stake a
fraction of that (a quarter by default) because our p is an estimate, and cap any one bet and the whole round.

Correlated bets: five teammates' disposal overs are not five independent bets. For bets i and j we take the
correlation of the model's misses (standardised residuals, 2024-2026 walk-forward, afl/model/tails.py data), signed by
side (an over and an under on correlated stats offset). Each bet's stake is multiplied by
1 / sqrt(1 + sum of its positive correlations with the other bets), which for n equal bets with correlation rho is
1 / sqrt(1 + (n - 1) rho): the shrink that keeps the round's variance what n independent bets would have. Negative
correlations are ignored, which errs small. Residual correlations overstate the correlation of win/lose outcomes, which
also errs small.

Paper only. Nothing here places a bet.
"""
import numpy as np
import pandas as pd

# measured 2024-2026, out of sample (see afl/docs/STAKING.md)
SAME_PLAYER = {('D', 'M'): 0.503, ('D', 'T'): 0.093, ('D', 'G'): 0.109, ('M', 'T'): -0.045, ('M', 'G'): 0.122, ('T', 'G'): 0.009}
TEAMMATES = {'D': 0.031, 'M': 0.095, 'T': 0.047, 'G': -0.002}
OPPONENTS = {'D': -0.016, 'M': 0.004, 'T': 0.041, 'G': -0.005}


def kelly(p, price):
    return np.maximum((p * price - 1) / (price - 1), 0.0)


def pair_corr(x, y):
    """Correlation between two bets' outcomes, as the signed correlation of the model's misses."""
    if x.game != y.game:
        return 0.0
    sign = (1 if x.side == 'over' else -1) * (1 if y.side == 'over' else -1)
    if x.player_id == y.player_id:
        r = 1.0 if x.stat == y.stat else SAME_PLAYER.get((x.stat, y.stat), SAME_PLAYER.get((y.stat, x.stat), 0.0))
    elif x.stat != y.stat:
        r = 0.0              # cross-stat between different players: not measured, taken as none
    elif x.team == y.team:
        r = TEAMMATES[x.stat]
    else:
        r = OPPONENTS[x.stat]
    return sign * r


def stakes(bets, bank, fraction=0.25, max_bet=0.02, max_round=0.15):
    """bets: DataFrame with game, team, player_id, stat (D/M/T/G), side (over/under), p (our chance), price.
    Returns the frame with kelly, shrink and stake (in bank units, rounded down to whole dollars)."""
    b = bets.reset_index(drop=True).copy()
    b['kelly'] = kelly(b.p.to_numpy(), b.price.to_numpy())
    rows = list(b.itertuples())
    shrink = []
    for i, x in enumerate(rows):
        pos = sum(max(pair_corr(x, y), 0.0) for j, y in enumerate(rows) if j != i)
        shrink.append(1 / np.sqrt(1 + pos))
    b['shrink'] = shrink
    raw = np.minimum(fraction * b.kelly * b.shrink, max_bet) * bank
    total = raw.sum()
    if total > max_round * bank:
        raw = raw * (max_round * bank / total)
    b['stake'] = np.floor(raw)
    return b
