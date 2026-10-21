"""How hard each T20 league is, measured on the players who play in several of them.

A run in India's domestic T20 is not a run in the IPL: the same batter averages about 20% more per
dismissal there (bbl/docs/RESEARCH.md). This fits, per gender, a player effect plus a league effect on
four per-ball rates (batting runs, batting outs, bowling runs conceded, bowling wickets), weighted by
balls, by alternating weighted means (fixed effects). A league with few shared players is shrunk toward
no adjustment. Factors are relative to the ball-weighted average league, and are estimated only from
matches before a cutoff, so a season scored out of sample never informs its own factors.

factor > 1 means the league is EASIER for that rate (more runs, more outs, more runs conceded, more
wickets than the same players manage elsewhere). Dividing a game's figure by its league's factor puts it
on a common scale.
"""
import numpy as np
import pandas as pd

from bbl.model.frame import BOWLER_WICKETS, NOT_DISMISSALS

MIN_BALLS = 60        # a player's balls in a league before that league-season counts
SHRINK_PLAYERS = 20   # a league's factor is shrunk by n / (n + 20), n = players it shares with others
ITERATIONS = 30


def _fit(x, player, league, num, den):
    """Weighted two-way fixed effects on log((num + 1) / (den + 1)); returns league effects (log scale) and player counts."""
    x = x[x[den] >= MIN_BALLS].copy()
    n_leagues = x.groupby(player)[league].transform('nunique')
    x = x[n_leagues >= 2]                     # only players seen in 2+ leagues identify league differences
    if x.empty:
        return {}, {}
    x['y'] = np.log((x[num] + 1) / (x[den] + 1))
    w = x[den].astype(float)
    lg = pd.Series(0.0, index=x[league].unique())
    for _ in range(ITERATIONS):
        r = x.y - x[league].map(lg)
        pe = (r * w).groupby(x[player]).sum() / w.groupby(x[player]).sum()
        r = x.y - x[player].map(pe)
        lg = (r * w).groupby(x[league]).sum() / w.groupby(x[league]).sum()
        lg = lg - np.average(lg, weights=w.groupby(x[league]).sum().reindex(lg.index))
    n = x.groupby(league)[player].nunique()
    return lg.to_dict(), n.to_dict()


def league_factors(m, dl, before):
    """{(competition, gender): {'bat_runs', 'bat_outs', 'bowl_runs', 'bowl_wkts'}} from club T20 matches before `before`."""
    mm = m[(m.team_type == 'club') & (pd.to_datetime(m.start_date) < pd.Timestamp(before))][['match_id', 'competition', 'gender']]
    d = dl[~dl.super_over].merge(mm, on='match_id')
    faced = d[d.wides == 0]
    bat = faced.assign(out=((faced.player_out == faced.batter) & ~faced.wicket_kind.isin(NOT_DISMISSALS)).astype(int)) \
        .groupby(['gender', 'batter', 'competition']).agg(balls=('out', 'size'), runs=('runs_batter', 'sum'), outs=('out', 'sum')).reset_index()
    wk = d.wicket_kind.isin(BOWLER_WICKETS).astype(int) + d.wicket_kind_2.isin(BOWLER_WICKETS).astype(int)
    bowl = d.assign(lg=d.legal.astype(int), conc=d.runs_batter + d.wides + d.noballs, wk=wk) \
        .groupby(['gender', 'bowler', 'competition']).agg(balls=('lg', 'sum'), runs=('conc', 'sum'), wkts=('wk', 'sum')).reset_index()
    out = {}
    for gender in mm.gender.unique():
        fits = {
            'bat_runs': _fit(bat[bat.gender == gender], 'batter', 'competition', 'runs', 'balls'),
            'bat_outs': _fit(bat[bat.gender == gender], 'batter', 'competition', 'outs', 'balls'),
            'bowl_runs': _fit(bowl[bowl.gender == gender], 'bowler', 'competition', 'runs', 'balls'),
            'bowl_wkts': _fit(bowl[bowl.gender == gender], 'bowler', 'competition', 'wkts', 'balls'),
        }
        comps = set().union(*[set(f[0]) for f in fits.values()])
        for c in comps:
            row = {}
            for k, (lg, n) in fits.items():
                eff, cnt = lg.get(c, 0.0), n.get(c, 0)
                row[k] = float(np.exp(eff * cnt / (cnt + SHRINK_PLAYERS)))
            out[(c, gender)] = row
    return out


def apply_factors(g, factors):
    """Each player-game's figures divided by its league's factors: the same performance on a common scale.

    Adds adj_bat_runs, adj_bat_6s, adj_bat_4s, adj_bat_out, adj_bowl_runs, adj_bowl_wkts, and the game's own
    league factors as context (lf_bat_runs, ...): a model predicting this game's raw figure needs to know
    how easy this league is.
    """
    g = g.copy()
    keys = list(zip(g.competition, g.gender))
    for k in ('bat_runs', 'bat_outs', 'bowl_runs', 'bowl_wkts'):
        g['lf_' + k] = [factors.get(x, {}).get(k, 1.0) for x in keys]
    g['adj_bat_runs'] = g.bat_runs / g.lf_bat_runs
    g['adj_bat_6s'] = g.bat_6s / g.lf_bat_runs
    g['adj_bat_4s'] = g.bat_4s / g.lf_bat_runs
    g['adj_bat_out'] = g.bat_out / g.lf_bat_outs
    g['adj_bowl_runs'] = g.bowl_runs / g.lf_bowl_runs
    g['adj_bowl_wkts'] = g.bowl_wkts / g.lf_bowl_wkts
    return g
