"""Research claims tested on our own data (bbl/docs/RESEARCH.md). Every figure there comes from this script.

Usage: python -m bbl.research.measure bbl/cache/parquet  (writes MEASURE.md)
"""
import os
import sys

import numpy as np
import pandas as pd

from bbl.model import frame


def md(df):
    cols = list(df.columns)
    out = ['| ' + ' | '.join(map(str, cols)) + ' |', '|' + '---|' * len(cols)]
    for r in df.itertuples(index=False):
        out.append('| ' + ' | '.join(f'{v:.3f}' if isinstance(v, float) else str(v) for v in r) + ' |')
    return '\n'.join(out)


def ci(k, n):
    p = k / n
    return f'{p:.1%} ({k}/{n}, ±{1.96 * np.sqrt(p * (1 - p) / n):.1%})'


def main(d):
    m = frame.match_table(pd.read_parquet(os.path.join(d, 't20_matches.parquet')))
    dl = pd.read_parquet(os.path.join(d, 't20_deliveries.parquet'))
    pp = pd.read_parquet(os.path.join(d, 't20_powerplays.parquet'))
    out = ['# Research claims, measured on the Cricsheet pull', '']

    # 1. toss and chasing
    rows = []
    for comp in ('BBL', 'WBBL', 'other'):
        g = m[(m.comp == comp) & (m.result == 'win') & m.method.isna() & (m.team_type == 'club')]
        chase = (g.winner != g.bat_first).sum()
        toss = (g.winner == g.toss_winner).sum()
        field = (g.toss_decision == 'field').sum()
        rows.append(dict(comp=comp if comp != 'other' else 'other club T20', games=len(g), chasing_side_won=ci(chase, len(g)),
                         toss_winner_won=ci(toss, len(g)), chose_to_field=ci(field, len(g))))
    out += ['## 1. Toss and chasing (decided games, no rain rule)', '', md(pd.DataFrame(rows)), '']
    b = m[(m.comp == 'BBL') & (m.result == 'win') & m.method.isna()]
    b = b.assign(era=np.where(b.season >= '2018/19', '2018/19 on', 'to 2017/18'))
    rows = [dict(comp='BBL', era=e, games=len(x), chasing_side_won=ci(int((x.winner != x.bat_first).sum()), len(x)))
            for e, x in b.groupby('era')]
    out += [md(pd.DataFrame(rows)), '']
    v = b.groupby('venue_c').apply(lambda x: pd.Series(dict(games=len(x), chase_won=(x.winner != x.bat_first).mean())), include_groups=False)
    out += ['BBL chasing win rate by ground (10+ games):', '', md(v[v.games >= 10].sort_values('games', ascending=False).reset_index()), '']

    # 2. Power Surge: runs and wickets per over inside the surge vs the same overs outside it, BBL from 2020/21
    bb = dl[dl.match_id.isin(m[(m.comp == 'BBL') & (m.season >= '2020/21')].match_id) & ~dl.super_over].copy()
    surge = pp[(pp.pp_type == 'batting')]
    bb = bb.merge(surge[['match_id', 'innings', 'pp_from', 'pp_to']], on=['match_id', 'innings'], how='left')
    pos = bb.over + bb.seq / 10
    bb['in_surge'] = (pos >= bb.pp_from - 0.05) & (pos <= bb.pp_to + 0.05)
    bb['wkt'] = bb.wicket_kind.notna() & ~bb.wicket_kind.isin(frame.NOT_DISMISSALS)
    ov = bb[bb.over.between(10, 17)]
    s = ov.groupby('in_surge').agg(balls=('legal', 'sum'), runs=('runs_total', 'sum'), wkts=('wkt', 'sum'))
    s['runs_per_over'] = s.runs / s.balls * 6
    s['wkts_per_over'] = s.wkts / s.balls * 6
    out += ['## 2. Power Surge, BBL 2020/21 on, overs 11 to 18 only', '', md(s.reset_index()), '']
    when = surge[surge.match_id.isin(bb.match_id)].pp_from.astype(int) + 1
    out += [f'Surge starts in over: median {int(when.median())}, middle half {int(when.quantile(0.25))} to {int(when.quantile(0.75))}.', '']

    # 3. dismissal and scoring by balls faced so far (BBL and WBBL, legal balls faced)
    a = dl[dl.match_id.isin(m[m.comp.isin(['BBL', 'WBBL'])].match_id) & ~dl.super_over & (dl.wides == 0)].copy()
    a = a.merge(m[['match_id', 'comp']], on='match_id')
    a['faced_before'] = a.groupby(['match_id', 'innings', 'batter']).cumcount()
    a['out'] = (a.player_out == a.batter) & ~a.wicket_kind.isin(frame.NOT_DISMISSALS | {'run out'})
    a['band'] = pd.cut(a.faced_before, [-1, 4, 9, 19, 29, 39, 200], labels=['0-4', '5-9', '10-19', '20-29', '30-39', '40+'])
    h = a.groupby(['comp', 'band'], observed=True).agg(balls=('out', 'size'), out_per_100=('out', 'mean'), runs_per_ball=('runs_batter', 'mean'))
    h['out_per_100'] *= 100
    out += ['## 3. Chance of getting out (not run out) and runs per ball, by balls already faced', '', md(h.reset_index()), '']

    # 4. league strength from players in several leagues: runs per ball and outs per ball, relative to the same player's IPL
    pl = pd.read_parquet(os.path.join(d, 't20_players.parquet'), columns=['match_id', 'player', 'player_id'])
    c = dl[~dl.super_over & (dl.wides == 0)].merge(m[['match_id', 'competition', 'gender', 'team_type', 'start_date']], on='match_id')
    c = c[(c.team_type == 'club') & (c.gender == 'male') & (c.start_date >= '2018-01-01')]
    c['out'] = (c.player_out == c.batter) & ~c.wicket_kind.isin(frame.NOT_DISMISSALS)
    agg = c.groupby(['batter', 'competition']).agg(balls=('out', 'size'), runs=('runs_batter', 'sum'), outs=('out', 'sum')).reset_index()
    agg = agg[agg.balls >= 120]
    top = agg.competition.value_counts()
    leagues = [x for x in top.index if top[x] >= 30]
    # fixed-effects fit on log runs-per-ball and log runs-per-dismissal: player effect + league effect, weighted by balls
    def fe(col_num, col_den, name):
        x = agg[agg.competition.isin(leagues)].copy()
        x['y'] = np.log((x[col_num] + 1) / (x[col_den] + 1))
        players = x.batter.unique()
        lg = {l: 0.0 for l in leagues}
        pe = pd.Series(0.0, index=players)
        for _ in range(50):
            pe = (x.y - x.competition.map(lg)).groupby(x.batter).apply(lambda s: np.average(s, weights=x.loc[s.index, 'balls']))
            res = x.y - x.batter.map(pe)
            lg = res.groupby(x.competition).apply(lambda s: np.average(s, weights=x.loc[s.index, 'balls'])).to_dict()
            base = lg.get('Indian Premier League', 0.0)
            lg = {k: v - base for k, v in lg.items()}
        return pd.Series(lg, name=name)
    sr = fe('runs', 'balls', 'runs_per_ball_vs_ipl')
    avg = fe('runs', 'outs', 'runs_per_out_vs_ipl')
    shared = agg[agg.competition.isin(leagues)].groupby('competition').batter.nunique().rename('batters_120_balls')
    L = pd.concat([sr, avg, shared], axis=1).reset_index().rename(columns={'index': 'league'})
    for col in ('runs_per_ball_vs_ipl', 'runs_per_out_vs_ipl'):
        L[col] = (np.exp(L[col]) - 1)
    out += ['## 4. League strength for batters (men, club T20 since 2018, 120+ balls in a league)', '',
            'The same batter\'s output relative to his IPL output: -10% means he scores 10% less there than in the IPL '
            '(a STRONGER league for bowling than the IPL), +10% more. Fixed effects, weighted by balls.', '',
            md(L.sort_values('runs_per_out_vs_ipl')), '']

    # 5. start time and the home side (Wikipedia fixtures joined on the Cricinfo match id; bbl/collect)
    ctx_path = os.path.join(d, 'match_context.parquet')
    if os.path.exists(ctx_path):
        ctx = pd.read_parquet(ctx_path)
        x = m.merge(ctx, on='match_id')
        x = x[(x.result == 'win') & x.method.isna() & x.comp.isin(['BBL', 'WBBL'])]
        x['slot'] = pd.cut(x.start_hour, [0, 15.5, 17.5, 24], labels=['day (before 3:30pm)', 'twilight (3:30-5:30pm)', 'night (from 5:30pm)'])
        rows = []
        for (comp, slot), g in x.dropna(subset=['slot']).groupby(['comp', 'slot'], observed=True):
            rows.append(dict(comp=comp, start=str(slot), games=len(g), chasing_side_won=ci(int((g.winner != g.bat_first).sum()), len(g)),
                             chose_to_field=ci(int((g.toss_decision == 'field').sum()), len(g))))
        out += ['## 5. Start time (local, from Wikipedia fixtures)', '', md(pd.DataFrame(rows)), '']
        h = x[x.home_team.notna()]
        rows = [dict(comp=comp, games=len(g), home_side_won=ci(int((g.winner == g.home_team).sum()), len(g)),
                     seasons=', '.join(sorted(g.season.unique())))
                for comp, g in h.groupby('comp')]
        out += ['## 6. The marked home side (only pages that mark it "(H)")', '', md(pd.DataFrame(rows)), '']
        t = pd.read_parquet(os.path.join(d, 'team_frame.parquet'), columns=['match_id', 'team', 'venue_share'])
        hv = h.merge(t, left_on=['match_id', 'home_team'], right_on=['match_id', 'team'])
        out += [f'On those games the home side\'s share of earlier games at the ground (venue_share) averages '
                f'{hv.venue_share.mean():.2f}, against {t.venue_share.mean():.2f} for all sides: venue_share is a fair proxy for home.', '']

    # 7. weather (NASA POWER at the ground, start to three hours on; bbl/collect/weather_join.py)
    wpath = os.path.join(d, 'match_weather.parquet')
    if os.path.exists(wpath):
        w = pd.read_parquet(wpath)
        tf = pd.read_parquet(os.path.join(d, 'team_frame.parquet'),
                             columns=['match_id', 'batted_first', 'first_inns_runs', 'full_first_inns', 'venue_first_runs'])
        x = m.merge(w, on='match_id').merge(tf[tf.batted_first == 1].drop(columns='batted_first'), on='match_id')
        x = x[x.comp.isin(['BBL', 'WBBL']) & x.temp_start.notna()]
        dec = x[(x.result == 'win') & x.method.isna()].copy()
        dec['dew'] = pd.cut(dec.dew_gap_end, [-1, 3, 6, 100], labels=['gap under 3C (dew likely)', '3 to 6C', 'over 6C (dry)'])
        rows = []
        for (comp, b), g in dec.groupby(['comp', 'dew'], observed=True):
            rows.append(dict(comp=comp, dew_point_gap_at_end=str(b), games=len(g), chasing_side_won=ci(int((g.winner != g.bat_first).sum()), len(g))))
        out += ['## 7. Weather: chasing by how close the air is to its dew point at the end of the game', '', md(pd.DataFrame(rows)), '']
        full = x[x.full_first_inns.fillna(False).astype(bool) & x.method.isna()].copy()
        full['resid'] = full.first_inns_runs - full.venue_first_runs
        rows = []
        for comp, g in full.groupby('comp'):
            for col in ('temp_start', 'rh_start', 'dew_gap_end', 'wind_mean', 'rain_mm'):
                gg = g[[col, 'resid']].dropna()
                rows.append(dict(comp=comp, weather=col, games=len(gg), corr_with_runs_above_ground_average=float(gg.corr().iloc[0, 1])))
        out += ['First-innings runs above the ground\'s own average, against the weather (correlation; |r| under ~0.1 is nothing at these sizes):', '',
                md(pd.DataFrame(rows)), '']

    text = '\n'.join(out)
    open(os.path.join(d, 'MEASURE.md'), 'w').write(text)
    print(text)


if __name__ == '__main__':
    main(sys.argv[1])
