"""A-League Men team model: expected goals for each side, priced into every team market.

The method (Dixon and Coles 1997, with Maher's 1982 attack/defence model underneath): each club has an
attack and a defence strength and there is one home advantage; a side's expected goals are
exp(mu + attack + opposing defence [+ home]). Fitted by weighted Poisson likelihood, where a match's
weight halves every HALF_LIFE days and is multiplied by CARRY for each season boundary behind it
(A-League squads turn over a lot between seasons), with a ridge penalty REG pulling every club
towards average (which is also how a new club such as Auckland FC starts). The goals go into a score
matrix with the Dixon-Coles low-score correction RHO, and every market is read off that matrix
(aleague/model/markets.py).

No leakage by construction: the prediction for a match on day D is made from a fit on matches before
D only (rolling_predictions), and aleague/tests/test_team.py changes a match's own result to prove it.

"At the open" only: without line-ups in the data, this is what is knowable before teams are named.
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson

from aleague.model.markets import asian_total, btts, h2h, score_matrix

DEFAULTS = dict(half_life=365.0, carry=0.75, reg=2.0, rho=-0.05)


def training_rows(matches, before):
    """Played matches strictly before `before`, with 90-minute goals."""
    m = matches[(matches.date < before) & matches.home_goals_90.notna()]
    return m


def weights(rows, before, season_now, half_life, carry):
    age = np.array([(before - d).days for d in rows.date], dtype=float)
    back = season_now - rows.season.to_numpy()
    return 0.5 ** (age / half_life) * carry ** np.maximum(back, 0)


class Fit:
    def __init__(self, teams, mu, home, att, dfn):
        self.teams, self.mu, self.home = teams, mu, home
        self.att = dict(zip(teams, att))
        self.dfn = dict(zip(teams, dfn))

    def rates(self, home, away, neutral=False):
        ah, dh = self.att.get(home, 0.0), self.dfn.get(home, 0.0)
        aa, da = self.att.get(away, 0.0), self.dfn.get(away, 0.0)
        hadv = 0.0 if neutral else self.home
        return float(np.exp(self.mu + ah + da + hadv)), float(np.exp(self.mu + aa + dh))


def fit(rows, w, reg, start=None):
    """Weighted Poisson maximum likelihood with a ridge penalty on attack and defence."""
    teams = sorted(set(rows.home) | set(rows.away))
    ix = {t: i for i, t in enumerate(teams)}
    T = len(teams)
    hi = rows.home.map(ix).to_numpy()
    ai = rows.away.map(ix).to_numpy()
    hadv = (~rows.neutral.astype(bool)).to_numpy().astype(float)
    yh = rows.home_goals_90.astype(float).to_numpy()
    ya = rows.away_goals_90.astype(float).to_numpy()
    sw = w.sum()

    def f(x):
        mu, home, att, dfn = x[0], x[1], x[2:2 + T], x[2 + T:]
        lh = mu + att[hi] + dfn[ai] + home * hadv
        la = mu + att[ai] + dfn[hi]
        eh, ea = np.exp(lh), np.exp(la)
        nll = (w * (eh - yh * lh + ea - ya * la)).sum() / sw
        pen = reg / sw * ((att ** 2).sum() + (dfn ** 2).sum())
        rh, ra = w * (eh - yh) / sw, w * (ea - ya) / sw
        g = np.zeros_like(x)
        g[0] = rh.sum() + ra.sum()
        g[1] = (rh * hadv).sum()
        g[2:2 + T] = np.bincount(hi, rh, T) + np.bincount(ai, ra, T) + 2 * reg / sw * att
        g[2 + T:] = np.bincount(ai, rh, T) + np.bincount(hi, ra, T) + 2 * reg / sw * dfn
        return nll + pen, g

    x0 = np.zeros(2 + 2 * T)
    x0[0] = np.log(max(yh.mean() + ya.mean(), 0.5) / 2)
    if start is not None:
        for t, i in ix.items():
            x0[2 + i] = start.att.get(t, 0.0)
            x0[2 + T + i] = start.dfn.get(t, 0.0)
        x0[0], x0[1] = start.mu, start.home
    r = minimize(f, x0, jac=True, method='L-BFGS-B')
    x = r.x
    return Fit(teams, x[0], x[1], x[2:2 + T], x[2 + T:])


def refit_level_and_home(f, rows, w2):
    """Re-estimate the league scoring level (mu) and the home advantage on weights w2, holding every
    club's attack and defence where the main fit put them. With w2 decaying faster than the main
    weights, the home edge follows a league whose home advantage is moving (it fell from about 45% home
    wins to about 36% in 2024-25 and 2025-26) without making team strengths noisier."""
    ah = rows.home.map(f.att).to_numpy(); dh = rows.home.map(f.dfn).to_numpy()
    aa = rows.away.map(f.att).to_numpy(); da = rows.away.map(f.dfn).to_numpy()
    hadv = (~rows.neutral.astype(bool)).to_numpy().astype(float)
    yh = rows.home_goals_90.astype(float).to_numpy(); ya = rows.away_goals_90.astype(float).to_numpy()
    sw = w2.sum()

    def nll(x):
        lh = x[0] + ah + da + x[1] * hadv
        la = x[0] + aa + dh
        eh, ea = np.exp(lh), np.exp(la)
        v = (w2 * (eh - yh * lh + ea - ya * la)).sum() / sw
        rh, ra = w2 * (eh - yh) / sw, w2 * (ea - ya) / sw
        return v, np.array([rh.sum() + ra.sum(), (rh * hadv).sum()])

    r = minimize(nll, np.array([f.mu, f.home]), jac=True, method='L-BFGS-B')
    f.mu, f.home = float(r.x[0]), float(r.x[1])
    return f


def rolling_predictions(matches, seasons, half_life=DEFAULTS['half_life'], carry=DEFAULTS['carry'],
                        reg=DEFAULTS['reg'], rho=DEFAULTS['rho'], include_unplayed=False, home_half_life=None):
    """One row per match in `seasons`: expected goals and market probabilities from a fit on
    earlier days only. home_half_life (days): re-estimate the league level and home edge with their own,
    usually faster, decay (refit_level_and_home); None keeps them from the main fit."""
    target = matches[matches.season.isin(seasons)]
    if not include_unplayed:
        target = target[target.home_goals_90.notna()]
    out, prev = [], None
    for day, games in target.groupby('date', sort=True):
        rows = training_rows(matches, day)
        if len(rows) < 50:
            continue
        season_now = int(games.season.iloc[0])
        w = weights(rows, day, season_now, half_life, carry)
        prev = fit(rows, w, reg, start=prev)
        cur = prev
        if home_half_life:
            age = np.array([(day - d).days for d in rows.date], dtype=float)
            cur = refit_level_and_home(Fit(prev.teams, prev.mu, prev.home, list(prev.att.values()), list(prev.dfn.values())),
                                       rows, 0.5 ** (age / home_half_life))
        for _, g in games.iterrows():
            lh, la = cur.rates(g.home, g.away, bool(g.neutral))
            m = score_matrix(lh, la, rho)
            p = h2h(m)
            out.append(dict(match_id=g.match_id, season=g.season, date=g.date, home=g.home, away=g.away,
                            neutral=bool(g.neutral), stage=g.stage, lam_home=lh, lam_away=la,
                            p_home=p['home'], p_draw=p['draw'], p_away=p['away'],
                            p_over25=asian_total(m, 2.5)['win'], p_btts=btts(m)['yes'],
                            home_goals=g.home_goals_90, away_goals=g.away_goals_90,
                            fit_matches=len(rows), home_adv=cur.home))
    return pd.DataFrame(out)


def fit_rho(preds):
    """The Dixon-Coles correction that best fits the scores, given each match's expected goals."""
    preds = preds[preds.home_goals.notna()]
    lh, la = preds.lam_home.to_numpy(), preds.lam_away.to_numpy()
    x, y = preds.home_goals.astype(int).to_numpy(), preds.away_goals.astype(int).to_numpy()

    def nll(rho):
        tau = np.ones(len(x))
        tau[(x == 0) & (y == 0)] = 1 - (lh * la * rho)[(x == 0) & (y == 0)]
        tau[(x == 0) & (y == 1)] = 1 + (lh * rho)[(x == 0) & (y == 1)]
        tau[(x == 1) & (y == 0)] = 1 + (la * rho)[(x == 1) & (y == 0)]
        tau[(x == 1) & (y == 1)] = 1 - rho
        if (tau <= 0).any():
            return np.inf
        return -np.log(tau).sum()

    grid = np.linspace(-0.4, 0.1, 101)
    return float(grid[np.argmin([nll(r) for r in grid])])


def reprice(preds, rho):
    """Recompute market probabilities for a different rho without refitting."""
    p = preds.copy()
    cols = {'p_home': [], 'p_draw': [], 'p_away': [], 'p_over25': [], 'p_btts': []}
    for lh, la in zip(p.lam_home, p.lam_away):
        m = score_matrix(lh, la, rho)
        r = h2h(m)
        cols['p_home'].append(r['home']); cols['p_draw'].append(r['draw']); cols['p_away'].append(r['away'])
        cols['p_over25'].append(asian_total(m, 2.5)['win']); cols['p_btts'].append(btts(m)['yes'])
    for k, v in cols.items():
        p[k] = v
    return p
