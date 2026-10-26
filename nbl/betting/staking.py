"""Stakes for NBL paper bets: fractional Kelly on the combined chance (nbl/betting/market.py), shrunk for bets
that tend to win or lose together, capped per bet and per round.

Kelly stakes (p x price - 1) / (price - 1) of the bank. We stake a quarter of it by default, because p is an
estimate (shrunk Kelly beats plug-in Kelly when the chance is estimated; Baker and McHale 2013).

Correlated bets: a player's points and his PRA are nearly the same bet. Measured on 2023-24 and 2024-25 (our
standardised misses, out of sample; nbl/docs/RESEARCH.md):
  same player   points-PRA 0.915, points-threes 0.648, rebounds-PRA 0.575, threes-PRA 0.565, assists-PRA 0.382,
                points-rebounds 0.271, rebounds-assists 0.193, points-assists 0.152, rebounds-threes 0.104,
                assists-threes 0.088
  teammates     same stat: points -0.059, PRA -0.040, threes -0.021, rebounds -0.020, assists -0.014 (they share the ball)
  opponents     same stat: about zero
Each bet's stake is multiplied by 1 / sqrt(1 + sum of its positive correlations with the other bets in the round),
signed by side (an over and an under on correlated stats offset). Negative correlations are ignored, which errs small.

Paper only. Nothing here places a bet.
"""
import numpy as np
import pandas as pd

SAME_PLAYER = {('pts', 'reb'): 0.271, ('pts', 'ast'): 0.152, ('pts', 'fg3m'): 0.648, ('pts', 'pra'): 0.915,
               ('reb', 'ast'): 0.193, ('reb', 'fg3m'): 0.104, ('reb', 'pra'): 0.575, ('ast', 'fg3m'): 0.088,
               ('ast', 'pra'): 0.382, ('fg3m', 'pra'): 0.565}
TEAMMATES = {'pts': -0.059, 'reb': -0.020, 'ast': -0.014, 'fg3m': -0.021, 'pra': -0.040}


def kelly(p, price):
    return np.maximum((np.asarray(p, float) * np.asarray(price, float) - 1) / (np.asarray(price, float) - 1), 0.0)


def pair_corr(x, y):
    """Correlation between two prop bets' outcomes in one round (0 across games and for unmeasured pairs)."""
    if x.game != y.game:
        return 0.0
    sign = (1 if x.side == 'over' else -1) * (1 if y.side == 'over' else -1)
    if x.player == y.player:
        r = 1.0 if x.market == y.market else SAME_PLAYER.get((x.market, y.market), SAME_PLAYER.get((y.market, x.market), 0.0))
    elif x.market == y.market and x.team == y.team:
        r = TEAMMATES.get(x.market, 0.0)
    else:
        r = 0.0
    return sign * r


def stakes(bets, bank, fraction=0.25, max_bet=0.02, max_round=0.15):
    """bets: DataFrame with game, team, player, market, side (over/under), p (combined chance), price.
    Returns it with kelly, shrink and stake (bank units, rounded down to whole dollars)."""
    b = bets.reset_index(drop=True).copy()
    b['kelly'] = kelly(b.p, b.price)
    rows = list(b.itertuples())
    b['shrink'] = [1 / np.sqrt(1 + sum(max(pair_corr(x, y), 0.0) for j, y in enumerate(rows) if j != i))
                   for i, x in enumerate(rows)]
    raw = np.minimum(fraction * b.kelly * b.shrink, max_bet) * bank
    if raw.sum() > max_round * bank:
        raw = raw * (max_round * bank / raw.sum())
    b['stake'] = np.floor(raw)
    return b
