"""Simulator mechanics with a fixed-probability model: the arithmetic of an innings, not the cricket."""
import numpy as np
import pandas as pd

from bbl.model import sim


class Fixed:
    def __init__(self, p):
        self.p = np.asarray(p, float) / np.sum(p)

    def predict_proba(self, X):
        return np.tile(self.p, (len(X), 1))


def xi(team, bowl_from=6):
    return pd.DataFrame(dict(player=[f'{team}{k}' for k in range(11)], team=team, exp_pos=range(1, 12),
                             pre_sr=1.2, pre_out_per_ball=0.05, pre_sixes_pg=0.5, pre_fours_pg=1.5, pre_balls_pg=15.0,
                             pre_games=50.0, pre_econ=1.3, pre_wkts_per_ball=0.05,
                             pre_bowl_balls_pg=[0.0] * bowl_from + [22.0] * (11 - bowl_from),
                             pre_bowl_rate=[0.0] * bowl_from + [1.0] * (11 - bowl_from)))


CTX = dict(venue_first_runs=160.0, lf_bat_runs=1.0, lf_bat_outs=1.0)
#             0    1    2    3    4    6    W    wd   nb   bye
PROBS = [0.35, 0.33, 0.07, 0.01, 0.10, 0.05, 0.05, 0.02, 0.01, 0.01]


def test_innings_arithmetic():
    rng = np.random.default_rng(1)
    bat, bowl = sim.order_xi(xi('A')), sim.order_xi(xi('B'))
    plans = sim.bowling_plan(bowl, rng, 300)
    r = sim.simulate_innings(Fixed(PROBS), bat, bowl, plans, CTX, 1, None, rng)
    assert (r['legal'] <= 120).all() and (r['wkts'] <= 10).all()
    assert ((r['legal'] == 120) | (r['wkts'] == 10)).all()               # every innings finished
    # team runs = batters' runs + wides + no-balls + byes; bowlers are charged batters' runs + wides + no-balls
    extras = r['runs'] - r['p_runs'].sum(1)
    assert (extras >= 0).all() and (r['w_runs'].sum(1) <= r['runs']).all()
    assert (r['w_wkts'].sum(1) == r['wkts']).all()
    assert (r['batted'].sum(1) == np.minimum(r['wkts'] + 2, 11)).all()   # openers plus one per wicket
    assert (r['w_balls'].sum(1) == r['legal']).all()


def test_chase_stops_at_the_target_and_bowling_rules():
    rng = np.random.default_rng(2)
    bat, bowl = sim.order_xi(xi('A')), sim.order_xi(xi('B'))
    plans = sim.bowling_plan(bowl, rng, 200)
    target = np.full(200, 60)
    r = sim.simulate_innings(Fixed(PROBS), bat, bowl, plans, CTX, 2, target, rng)
    won = r['runs'] >= 60
    assert (r['runs'][won] <= 60 + 6).all()              # stops on the ball that gets there
    assert won.mean() > 0.9                              # 60 off 120 at these rates is nearly certain
    counts = np.stack([(plans == k).sum(1) for k in range(11)], 1)
    assert counts.max() <= 4 and (counts.sum(1) == 20).all()
    assert not (plans[:, 1:] == plans[:, :-1]).any()     # nobody bowls two overs in a row


def test_match_summary_is_coherent():
    rng = np.random.default_rng(3)
    a, b = sim.order_xi(xi('A')), sim.order_xi(xi('B'))
    game, players = sim.summarise('m', a, b, sim.simulate_match(Fixed(PROBS), a, b, CTX, rng, n=200))
    assert 0.35 < game['p_team1'] < 0.65                 # identical sides
    tops = pd.DataFrame(players).groupby('team').sim_top.sum()
    assert np.allclose(tops, 1.0)
