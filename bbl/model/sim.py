"""Ball-by-ball match simulator (v2): every market priced from one simulated match, so the prices agree.

The design follows Davis, Perera and Swartz's T20 simulator (ANZ J. Stat. 2015) and the WASP lineage: each
ball's outcome is a multinomial whose probabilities depend on the batter, the bowler and the state of the
innings. Here the probabilities come from one LightGBM multiclass model, fitted walk-forward on club T20
balls of the same gender before the season being priced, on:
  batter    pre-game runs per ball, outs per ball, sixes and fours per ball, experience
  bowler    pre-game runs conceded and wickets per ball, usual workload
  state     innings, over, wickets down, balls the batter has already faced (dismissal risk RISES once a
            batter is set, bbl/docs/RESEARCH.md), runs so far, and in a chase the runs and rate required
  context   the ground's first-innings average and the league's factors (bbl/model/leagues.py)
Outcomes: dot, 1, 2, 3, 4, 6, wicket, wide, no-ball, bye (byes and leg byes count to the team only).

Simulation: batting order from each player's usual position (exp_pos, pre-game); bowling from each XI
member's usual workload, at most 4 overs each and never two in a row; the first innings is played out,
then the chase against each simulated target. N_SIMS matches per game, all advanced together.

Usage: python -m bbl.model.sim bbl/cache/parquet   (writes sim_preds.parquet and sim_players.parquet)
"""
import os
import sys

import lightgbm as lgb
import numpy as np
import pandas as pd

from bbl.model import frame
from bbl.model.team import CHOOSE, CONFIRM, FINAL

OUTCOMES = ['0', '1', '2', '3', '4', '6', 'W', 'wd', 'nb', 'bye']
RUNS = np.array([0, 1, 2, 3, 4, 6, 0, 1, 1, 1])        # runs to the team
BAT_RUNS = np.array([0, 1, 2, 3, 4, 6, 0, 0, 0, 0])    # runs to the batter
LEGAL = np.array([1, 1, 1, 1, 1, 1, 1, 0, 0, 1], bool)
WICKET = 6
SIX = 5
N_SIMS = 600
TRAIN_FROM = '2015-01-01'
MAX_TRAIN_BALLS = 600_000
BALL_FEATS = ['b_sr', 'b_out', 'b_six', 'b_four', 'b_games', 'w_econ', 'w_wkt', 'w_balls', 'innings', 'over', 'wkts',
              'faced', 'runs_so_far', 'need', 'req_rate', 'venue_first_runs', 'lf_bat_runs', 'lf_bat_outs',
              'bat_elo', 'bowl_elo', 'bat_home', 'bowl_home']
# batting order is not fixed in real games (pinch hitters, promotions): each simulation jitters the usual
# positions by this many places (sd) before ordering
ORDER_JITTER = 0.8
LGB = dict(objective='multiclass', num_class=len(OUTCOMES), learning_rate=0.08, n_estimators=150, num_leaves=31,
           min_child_samples=200, subsample=0.7, subsample_freq=1, colsample_bytree=0.8, verbose=-1)
SEASONS = CHOOSE + CONFIRM


def outcome_class(dl):
    c = np.select([dl.wides > 0, dl.noballs > 0,
                   dl.wicket_kind.notna() & ~dl.wicket_kind.isin(frame.NOT_DISMISSALS),
                   (dl.byes + dl.legbyes) > 0, dl.runs_batter >= 6, dl.runs_batter >= 4],
                  [7, 8, 6, 9, 5, 4], -1)
    c = np.where(c == -1, np.clip(dl.runs_batter.to_numpy(), 0, 3), c)
    return c.astype(int)


def player_rates(g):
    """Pre-game per-ball rates for every player-game (from the frame's ewm state)."""
    r = g[['match_id', 'player', 'pre_sr', 'pre_out_per_ball', 'pre_sixes_pg', 'pre_fours_pg', 'pre_balls_pg', 'pre_games',
           'pre_econ', 'pre_wkts_per_ball', 'pre_bowl_balls_pg']].copy()
    bpg = r.pre_balls_pg.replace(0, np.nan)
    r['six_pb'] = r.pre_sixes_pg / bpg
    r['four_pb'] = r.pre_fours_pg / bpg
    return r


def ball_table(m, dl, g, t):
    """One row per ball with its state and both players' pre-game rates (training data for the outcome model)."""
    # rain-rule games are left out: their chase target is not the first-innings total plus one
    keep = m[(m.team_type == 'club') & (m.start_date >= TRAIN_FROM) & m.method.isna()][['match_id', 'gender', 'dt', 'competition']]
    d = dl[~dl.super_over & dl.match_id.isin(keep.match_id)].copy()
    d['cls'] = outcome_class(d)
    k = d.groupby(['match_id', 'innings'])
    d['wkt'] = (d.cls == WICKET).astype(int)
    d['wkts'] = k.wkt.cumsum() - d.wkt
    d['runs_so_far'] = k.runs_total.cumsum() - d.runs_total
    d['legal_i'] = d.legal.astype(int)
    d['balls_so_far'] = k.legal_i.cumsum() - d.legal_i
    d['faced'] = d.groupby(['match_id', 'innings', 'batter']).cumcount()
    first = t[t.batted_first == 1].set_index('match_id').runs
    d['target'] = d.match_id.map(first) + 1
    second = d.innings == 2
    d['need'] = np.where(second, d.target - d.runs_so_far, np.nan)
    d['req_rate'] = np.where(second, d.need / ((120 - d.balls_so_far).clip(lower=1) / 6), np.nan)
    d = d.merge(keep, on='match_id')
    r = player_rates(g)
    d = d.merge(r.add_prefix('b_').rename(columns={'b_match_id': 'match_id', 'b_player': 'batter'}), on=['match_id', 'batter'], how='left')
    d = d.merge(r.add_prefix('w_').rename(columns={'w_match_id': 'match_id', 'w_player': 'bowler'}), on=['match_id', 'bowler'], how='left')
    d = d.rename(columns={'b_pre_sr': 'b_sr', 'b_pre_out_per_ball': 'b_out', 'b_six_pb': 'b_six', 'b_four_pb': 'b_four',
                          'b_pre_games': 'b_games', 'w_pre_econ': 'w_econ', 'w_pre_wkts_per_ball': 'w_wkt',
                          'w_pre_bowl_balls_pg': 'w_balls'})
    vf = t.drop_duplicates('match_id').set_index('match_id').venue_first_runs
    d['venue_first_runs'] = d.match_id.map(vf)
    # each side's pre-game rating and how often it has played at this ground (the batting side is `team` on the ball)
    side = t.drop_duplicates(['match_id', 'team']).set_index(['match_id', 'team'])
    opp = side.opp.reindex(pd.MultiIndex.from_arrays([d.match_id, d.team])).to_numpy()
    for who, teams in (('bat', d.team.to_numpy()), ('bowl', opp)):
        key = pd.MultiIndex.from_arrays([d.match_id.to_numpy(), teams])
        d[f'{who}_elo'] = side.elo_pre.reindex(key).to_numpy()
        d[f'{who}_home'] = side.venue_share.reindex(key).to_numpy()
    lf = g.drop_duplicates('match_id').set_index('match_id')
    for c in ('lf_bat_runs', 'lf_bat_outs'):
        d[c] = d.match_id.map(lf[c]) if c in lf else 1.0
    return d


def fit_ball_model(balls, gender, before, seed=0):
    tr = balls[(balls.gender == gender) & (balls.dt < before)]
    if len(tr) > MAX_TRAIN_BALLS:
        tr = tr.sample(MAX_TRAIN_BALLS, random_state=seed)
    mdl = lgb.LGBMClassifier(**LGB)
    mdl.fit(tr[BALL_FEATS], tr.cls)
    return mdl


# ---------------------------------------------------------------- simulation

def bowling_plan(xi, rng, n):
    """n bowling orders of 20 overs: each XI member weighted by his usual workload, max 4 overs, never consecutive."""
    w = xi.pre_bowl_balls_pg.fillna(0).to_numpy() / 6
    w = np.where(xi.pre_bowl_rate.fillna(0).to_numpy() < 0.2, 0, w)
    if (w > 0).sum() < 5:     # not enough known bowlers: the five with the most bowling history
        top = np.argsort(-xi.pre_bowl_balls_pg.fillna(0).to_numpy())[:5]
        w = np.zeros(len(xi)); w[top] = 1.0
    plans = np.zeros((n, 20), int)
    for s in range(n):
        left = np.full(len(xi), 4)
        prev = -1
        for o in range(20):
            p = w * (left > 0)
            if prev >= 0:
                p[prev] = 0
            if p.sum() == 0:
                p = (left > 0).astype(float)
                if prev >= 0 and p.sum() > 1:
                    p[prev] = 0
            k = rng.choice(len(xi), p=p / p.sum())
            plans[s, o] = k
            left[k] -= 1
            prev = k
    return plans


def batting_orders(xi, rng, n):
    """n batting orders: usual positions jittered by ORDER_JITTER places (sd) per simulation, then ranked."""
    base = xi.exp_pos.to_numpy(float)
    return np.argsort(base[None, :] + rng.normal(0, ORDER_JITTER, (n, len(base))), axis=1)


def simulate_innings(mdl, bat, bowl, plans, ctx, innings, target, rng, sides=(1500.0, 1500.0, np.nan, np.nan), orders=None):
    """Advance N simulations of one innings ball by ball.

    bat/bowl: the two XIs. orders: (n, 11) player indices in batting order per simulation (default: the XI as
    given). sides: batting side's rating, bowling side's rating, batting side's and bowling side's home share.
    Every per-player figure is indexed by player, not by position.
    """
    n = plans.shape[0]
    if orders is None:
        orders = np.tile(np.arange(len(bat)), (n, 1))
    bat_rates = bat[['pre_sr', 'pre_out_per_ball', 'six_pb', 'four_pb', 'pre_games']].to_numpy(float)
    bowl_rates = bowl[['pre_econ', 'pre_wkts_per_ball', 'pre_bowl_balls_pg']].to_numpy(float)
    striker = orders[:, 0].copy()        # player indices
    non = orders[:, 1].copy()
    nxt = np.full(n, 2)                  # next position in this simulation's order
    wkts = np.zeros(n, int)
    runs = np.zeros(n, int)
    legal = np.zeros(n, int)
    faced = np.zeros((n, len(bat)), int)
    p_runs = np.zeros((n, len(bat)), int)
    p_six = np.zeros((n, len(bat)), int)
    batted = np.zeros((n, len(bat)), bool)
    batted[np.arange(n), striker] = True
    batted[np.arange(n), non] = True
    w_wkts = np.zeros((n, len(bowl)), int)
    w_runs = np.zeros((n, len(bowl)), int)
    w_balls = np.zeros((n, len(bowl)), int)
    idx = np.arange(n)
    for _ in range(200):          # 120 legal balls plus extras
        live = (wkts < 10) & (legal < 120)
        if target is not None:
            live &= runs < target
        if not live.any():
            break
        i = idx[live]
        over = legal[i] // 6
        bw = plans[i, np.minimum(over, 19)]
        br = bat_rates[striker[i]]
        wr = bowl_rates[bw]
        need = (target[i] - runs[i]) if target is not None else np.full(len(i), np.nan)
        req = need / (np.maximum(120 - legal[i], 1) / 6) if target is not None else np.full(len(i), np.nan)
        X = np.column_stack([br, wr, np.full(len(i), innings), over, wkts[i], faced[i, striker[i]], runs[i], need, req,
                             np.full(len(i), ctx['venue_first_runs']), np.full(len(i), ctx['lf_bat_runs']),
                             np.full(len(i), ctx['lf_bat_outs']), np.full(len(i), sides[0]), np.full(len(i), sides[1]),
                             np.full(len(i), sides[2]), np.full(len(i), sides[3])])
        prob = mdl.predict_proba(pd.DataFrame(X, columns=BALL_FEATS))
        u = rng.random(len(i))[:, None]
        cls = (prob.cumsum(1) < u).sum(1).clip(max=len(OUTCOMES) - 1)
        s = striker[i]
        runs[i] += RUNS[cls]
        lg = LEGAL[cls]
        legal[i] += lg
        faced[i, s] += (cls != 7)
        p_runs[i, s] += BAT_RUNS[cls]
        p_six[i, s] += (cls == SIX)
        conc = BAT_RUNS[cls] + (cls == 7) + (cls == 8)
        w_runs[i, bw] += conc
        w_balls[i, bw] += lg
        out = cls == WICKET
        w_wkts[i[out], bw[out]] += 1
        wkts[i] += out
        # the out batter is replaced by the next in the order
        new = out & (nxt[i] < len(bat))
        incoming = orders[i[new], nxt[i[new]]]
        striker[i[new]] = incoming
        batted[i[new], incoming] = True
        nxt[i[new]] += 1
        # odd runs swap ends; so does the end of an over
        odd = (RUNS[cls] % 2 == 1) & ~out
        end_over = lg & (legal[i] % 6 == 0)
        swap = odd ^ end_over
        a, b = striker[i[swap]], non[i[swap]]
        striker[i[swap]], non[i[swap]] = b, a
    return dict(runs=runs, wkts=wkts, legal=legal, p_runs=p_runs, p_six=p_six, batted=batted, w_wkts=w_wkts,
                w_runs=w_runs, w_balls=w_balls)


def simulate_match(mdl, xi1, xi2, ctx, rng, n=N_SIMS):
    """Team 1 and team 2 each bat first in half the simulations (the toss is not known before it happens).

    ctx may carry 'elo1', 'elo2', 'home1', 'home2' (each side's pre-game rating and home-ground share).
    """
    e1, e2 = ctx.get('elo1', 1500.0), ctx.get('elo2', 1500.0)
    h1, h2 = ctx.get('home1', np.nan), ctx.get('home2', np.nan)
    res = {}
    for first, second, label, sf, ss in ((xi1, xi2, 't1_first', (e1, e2, h1, h2), (e2, e1, h2, h1)),
                                         (xi2, xi1, 't2_first', (e2, e1, h2, h1), (e1, e2, h1, h2))):
        h = n // 2
        a = simulate_innings(mdl, first, second, bowling_plan(second, rng, h), ctx, 1, None, rng, sf, batting_orders(first, rng, h))
        b = simulate_innings(mdl, second, first, bowling_plan(first, rng, h), ctx, 2, a['runs'] + 1, rng, ss,
                             batting_orders(second, rng, h))
        res[label] = (a, b)
    return res


def order_xi(xi):
    x = xi.sort_values('exp_pos').reset_index(drop=True)
    bpg = x.pre_balls_pg.replace(0, np.nan)
    x['six_pb'] = x.pre_sixes_pg / bpg
    x['four_pb'] = x.pre_fours_pg / bpg
    return x


def summarise(match_id, xi1, xi2, res):
    a1, b1 = res['t1_first']
    a2, b2 = res['t2_first']
    t1_win = np.concatenate([(a1['runs'] > b1['runs']) + 0.5 * (a1['runs'] == b1['runs']),
                             (b2['runs'] > a2['runs']) + 0.5 * (a2['runs'] == b2['runs'])])
    first_runs = np.concatenate([a1['runs'], a2['runs']])
    match_runs = np.concatenate([a1['runs'] + b1['runs'], a2['runs'] + b2['runs']])
    game = dict(match_id=match_id, p_team1=t1_win.mean(), first_mu=first_runs.mean(), first_sd=first_runs.std(),
                match_mu=match_runs.mean(), match_sd=match_runs.std(), first_runs=first_runs, match_runs=match_runs)
    players = []
    for xi, bat_inns, bowl_inns in ((xi1, [a1, b2], [b1, a2]), (xi2, [b1, a2], [a1, b2])):
        runs = np.concatenate([x['p_runs'] for x in bat_inns])
        six = np.concatenate([x['p_six'] for x in bat_inns])
        batted = np.concatenate([x['batted'] for x in bat_inns])
        wk = np.concatenate([x['w_wkts'] for x in bowl_inns])
        bb = np.concatenate([x['w_balls'] for x in bowl_inns])
        best = np.where(batted, runs, -1).max(1, keepdims=True)
        top = (np.where(batted, runs, -1) == best) & batted
        top = top / top.sum(1, keepdims=True).clip(min=1)
        for k, r in xi.iterrows():
            players.append(dict(match_id=match_id, player=r.player, team=r.team, sim_p_bat=batted[:, k].mean(),
                                sim_runs=runs[:, k][batted[:, k]], sim_six=six[:, k][batted[:, k]], sim_top=top[:, k].mean(),
                                sim_p_bowl=(bb[:, k] > 0).mean(), sim_wkts=wk[:, k][bb[:, k] > 0]))
    return game, players


def run(d, seasons=SEASONS):
    m = frame.match_table(pd.read_parquet(os.path.join(d, 't20_matches.parquet')))
    dl = pd.read_parquet(os.path.join(d, 't20_deliveries.parquet'))
    g = pd.read_parquet(os.path.join(d, 'player_frame.parquet'))
    t = pd.read_parquet(os.path.join(d, 'team_frame.parquet'))
    if 'team_type' not in m:
        raise SystemExit('t20_matches needs team_type')
    balls = ball_table(m, dl, g, t)
    games, players = [], []
    rng = np.random.default_rng(0)
    for gender, comp in (('male', 'BBL'), ('female', 'WBBL')):
        for season in seasons:
            mm = m[(m.comp == comp) & (m.season == season)]
            if mm.empty:
                continue
            mdl = fit_ball_model(balls, gender, mm.dt.min())
            for r in mm.itertuples():
                xg = g[g.match_id == r.match_id]
                xi1, xi2 = order_xi(xg[xg.team == r.team1]), order_xi(xg[xg.team == r.team2])
                if len(xi1) < 11 or len(xi2) < 11:
                    continue
                vfr = t.loc[t.match_id == r.match_id, 'venue_first_runs'].iloc[0]
                side = t[t.match_id == r.match_id].set_index('team')
                ctx = dict(elo1=float(side.elo_pre.get(r.team1, 1500.0)), elo2=float(side.elo_pre.get(r.team2, 1500.0)),
                           home1=float(side.venue_share.get(r.team1, np.nan)), home2=float(side.venue_share.get(r.team2, np.nan)),
                           venue_first_runs=vfr if pd.notna(vfr) else np.nan,
                           lf_bat_runs=float(xg.lf_bat_runs.iloc[0]) if 'lf_bat_runs' in xg else 1.0,
                           lf_bat_outs=float(xg.lf_bat_outs.iloc[0]) if 'lf_bat_outs' in xg else 1.0)
                gm, pls = summarise(r.match_id, xi1, xi2, simulate_match(mdl, xi1, xi2, ctx, rng))
                gm.update(season=season, comp=comp, team1=r.team1, team2=r.team2)
                games.append(gm)
                players += [dict(p, season=season, comp=comp) for p in pls]
            print(f'{comp} {season}: {len(mm)} games simulated', flush=True)
    return pd.DataFrame(games), pd.DataFrame(players)


def main(d):
    seasons = os.environ.get('SIM_SEASONS', ','.join(SEASONS)).split(',')
    games, players = run(d, seasons)
    games.to_pickle(os.path.join(d, 'sim_games.pkl'))
    players.to_pickle(os.path.join(d, 'sim_players.pkl'))
    print(f'sim: {len(games)} games, {len(players)} player-games')


if __name__ == '__main__':
    main(sys.argv[1])
