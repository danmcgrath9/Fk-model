"""Price soccer markets from a matrix of final-score probabilities (90 minutes, as bets settle).

matrix[i, j] = P(home scores i, away scores j). Every market here is a sum over that matrix, so the
prices cannot contradict each other: head-to-head, draw no bet, totals and both teams to score, and
Asian handicaps and totals with whole, half and quarter lines (a quarter line is half the stake on
each neighbouring line, the way Australian books settle them).

fair_odds(outcomes) returns the decimal price at which a bet breaks even, from the probabilities of
win, half win, push, half loss and loss.
"""
import numpy as np
from scipy.stats import poisson


def score_matrix(lam_home, lam_away, rho=0.0, max_goals=10):
    """Independent Poisson goals with the Dixon-Coles adjustment for 0-0, 1-0, 0-1 and 1-1.
    rho < 0 makes 0-0 and 1-1 likelier (A-League, like most leagues, draws more than Poisson says)."""
    h = poisson.pmf(np.arange(max_goals + 1), lam_home)
    a = poisson.pmf(np.arange(max_goals + 1), lam_away)
    m = np.outer(h, a)
    if rho:
        m[0, 0] *= 1 - lam_home * lam_away * rho
        m[0, 1] *= 1 + lam_home * rho
        m[1, 0] *= 1 + lam_away * rho
        m[1, 1] *= 1 - rho
        if (m < 0).any():
            raise ValueError(f'rho {rho} too large for goal rates {lam_home:.2f}, {lam_away:.2f}')
    return m / m.sum()


def _diff_total(m):
    i, j = np.indices(m.shape)
    return i - j, i + j


def h2h(m):
    d, _ = _diff_total(m)
    return dict(home=m[d > 0].sum(), draw=m[d == 0].sum(), away=m[d < 0].sum())


def btts(m):
    return dict(yes=m[1:, 1:].sum(), no=1 - m[1:, 1:].sum())


def _settle(margin_probs, line):
    """Win/half-win/push/half-loss/loss probabilities for a bet that wins when margin + line > 0.
    margin_probs: {margin: probability}. Quarter lines split the stake across the two neighbours."""
    if round(line * 4) % 2:  # quarter line, e.g. -0.25 = half on 0, half on -0.5
        lo, hi = line - 0.25, line + 0.25
        out = dict(win=0.0, half_win=0.0, push=0.0, half_loss=0.0, loss=0.0)
        # both halves see the same margin; each half wins, pushes or loses half the stake
        for mg, p in margin_probs.items():
            r = [np.sign(mg + x) for x in (lo, hi)]  # +1 win, 0 push, -1 loss, per half
            s = sum(r)
            if s == 2:
                out['win'] += p
            elif s == -2:
                out['loss'] += p
            elif s == 1:
                out['half_win'] += p
            elif s == -1:
                out['half_loss'] += p
            else:
                out['push'] += p
        return out
    out = dict(win=0.0, half_win=0.0, push=0.0, half_loss=0.0, loss=0.0)
    for mg, p in margin_probs.items():
        v = mg + line
        out['win' if v > 0 else 'loss' if v < 0 else 'push'] += p
    return out


def asian_handicap(m, line, side='home'):
    """Settlement probabilities for the home (or away) side on handicap `line` (home -0.5 means the
    home side must win by one)."""
    d, _ = _diff_total(m)
    sign = 1 if side == 'home' else -1
    margins = {}
    for k in np.unique(d):
        margins[sign * int(k)] = margins.get(sign * int(k), 0) + m[d == k].sum()
    return _settle(margins, line)


def asian_total(m, line, side='over'):
    """Settlement probabilities for over/under `line` goals (2.5, 2.25, 3, ...)."""
    _, t = _diff_total(m)
    sign = 1 if side == 'over' else -1
    margins = {}
    for k in np.unique(t):
        margins[sign * (int(k))] = margins.get(sign * int(k), 0) + m[t == k].sum()
    # over 2.5 wins when total - 2.5 > 0; under wins when 2.5 - total > 0
    return _settle(margins, -line if side == 'over' else line)


def draw_no_bet(m, side='home'):
    return asian_handicap(m, 0.0, side)


def fair_odds(o):
    """Decimal price with zero expected profit, given settlement probabilities.
    EV per unit at price x: win (x-1) + half_win (x-1)/2 - half_loss/2 - loss = 0."""
    up = o['win'] + o['half_win'] / 2
    down = o['loss'] + o['half_loss'] / 2
    if up <= 0:
        return float('inf')
    return 1 + down / up


def price_all(m, handicaps=(-1.5, -1.25, -1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5),
              totals=(1.5, 2.0, 2.25, 2.5, 2.75, 3.0, 3.5)):
    """Every market's probabilities and fair prices for one match."""
    out = {}
    for k, p in h2h(m).items():
        out[f'h2h_{k}'] = p
    for k, p in btts(m).items():
        out[f'btts_{k}'] = p
    for line in handicaps:
        out[f'ah_home_{line:+g}'] = fair_odds(asian_handicap(m, line, 'home'))
    for line in totals:
        out[f'over_{line:g}'] = fair_odds(asian_total(m, line, 'over'))
        out[f'under_{line:g}'] = fair_odds(asian_total(m, line, 'under'))
    return out
