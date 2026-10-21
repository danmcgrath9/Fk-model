"""Our prices for the NBL games in the next few days: head-to-head, line and total per game, and the
five player props for each expected rotation player. Paper only: nothing here places a bet.

Squads are the open view: each team's squad from its latest completed game (no team news). When a
player is ruled out, his props are void and his team's other numbers move; re-run after team news.

Models are fitted on every completed season (team: 2016-17 on; props: fit 2016-17 to the season before
last, spread from last season), the same machinery as nbl/docs/TEAM_STEP1.md and PROPS_STEP1.md.

Writes <out>/prices_<YYYY-MM-DD>.md (to read) and prices_<YYYY-MM-DD>.csv (to compare with the lines and
the close later: the paper season).

Usage: python -m nbl.model.price_round nbl/cache nbl/out [days ahead, default 8]
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

from nbl.model import frame, onoff, props, team

MARKETS = props.PROPS


def build(cache, days):
    now = pd.Timestamp.now(tz='UTC')
    results = pd.read_parquet(f'{cache}/results.parquet')
    box = pd.read_parquet(f'{cache}/box_player.parquet')
    games = frame.base_games(results, scheduled_until=now + pd.Timedelta(days=days))
    games = games[~games.scheduled | (games.tip >= now)]           # a scheduled game already past has no result yet: skip it
    done = games[~games.scheduled]
    players = frame.base_players(box, done)
    upcoming = frame.expected_squads(players, games)
    allp = pd.concat([players, upcoming], ignore_index=True)
    tg = frame.team_features(frame.team_box(allp, games), games)
    p = frame.add_player_features(allp, tg)
    tg = tg.merge(frame.lineup_values(p, frame.league_rates(players)), on=['game', 'team'], how='left')
    rpath = f'{cache}/ratings.parquet'
    if os.path.exists(rpath):              # squad on-court ratings (onoff.py), refreshed by the workflow before pricing
        tg = tg.merge(onoff.lineup_ratings(p, pd.read_parquet(rpath)), on=['game', 'team'], how='left')
    else:
        tg['named_rapm'] = tg['open_rapm'] = np.nan
    return games, p, tg, now


def fair_line(mu, a):
    """The .5 line closest to an even chance, and our chance of the over there."""
    lines = np.arange(0.5, max(60.5, mu * 3), 1.0)
    po = props.p_over(np.full(len(lines), mu), lines, a)
    i = int(np.argmin(np.abs(po - 0.5)))
    return float(lines[i]), float(po[i])


def run(cache, out_dir, days=8):
    games, p, tg, now = build(cache, days)
    up = games[games.scheduled].sort_values('tip')
    os.makedirs(out_dir, exist_ok=True)
    stamp = now.tz_convert('Australia/Melbourne').strftime('%Y-%m-%d')
    L = [f'# NBL: our prices, {stamp}', '']
    if up.empty:
        L.append(f'No NBL games in the next {days} days.')
        open(f'{out_dir}/prices_{stamp}.md', 'w').write('\n'.join(L) + '\n')
        print('\n'.join(L))
        return
    last_done = int(games[~games.scheduled].season.max())

    # team markets
    g = team.games_table(tg)
    models, sd_m, sd_t, _ = team.fitted(g[g.home_margin.notna()], fit_range=(team.FIT[0], last_done))
    gu = g[g.game.isin(up.game)].copy()
    gu['m'] = models['m_open'].predict(gu)
    gu['t'] = models['t_open'].predict(gu)
    rows = []
    L += ['Paper only. Squads are each team\'s last squad (no team news): re-run after teams are named. Fair price = 1 / our '
          'chance, no margin; a book\'s price has to beat it by enough before it is a bet.', '',
          '## Games', '',
          '| tip (Melbourne) | home | away | our home margin | home win | fair home | fair away | our total | fair line |',
          '|---|---|---|---|---|---|---|---|---|']
    for x in gu.merge(up[['game', 'tip']], on='game', suffixes=('', '_u')).sort_values('tip').itertuples():
        pr = team.price(x.m, x.t, sd_m, sd_t)
        line = -np.round(x.m * 2) / 2
        tip = x.tip.tz_convert('Australia/Melbourne').strftime('%a %d %b %H:%M')
        L.append(f'| {tip} | {x.home} | {x.away} | {x.m:+.1f} | {pr["p_home"]:.0%} | {pr["fair_home"]:.2f} | {pr["fair_away"]:.2f} | '
                 f'{x.t:.1f} | home {line:+.1f} |')
        rows.append(dict(kind='team', game=x.game, tip=x.tip, home=x.home, away=x.away, market='h2h', side='home',
                         line=np.nan, p=pr['p_home'], fair=pr['fair_home'], mu=x.m))
        rows.append(dict(kind='team', game=x.game, tip=x.tip, home=x.home, away=x.away, market='h2h', side='away',
                         line=np.nan, p=1 - pr['p_home'], fair=pr['fair_away'], mu=x.m))
        for ln in (line - 2, line, line + 2):
            q = team.price(x.m, x.t, sd_m, sd_t, line=ln, total_line=None)
            rows.append(dict(kind='team', game=x.game, tip=x.tip, home=x.home, away=x.away, market='line', side='home',
                             line=ln, p=q['p_home_cover'], fair=q['fair_home_line'], mu=x.m))
        for tl in (np.floor(x.t) - 4.5, np.floor(x.t) + 0.5, np.floor(x.t) + 4.5):
            q = team.price(x.m, x.t, sd_m, sd_t, total_line=tl)
            rows.append(dict(kind='team', game=x.game, tip=x.tip, home=x.home, away=x.away, market='total', side='over',
                             line=tl, p=q['p_over'], fair=q['fair_over'], mu=x.t))
    L += ['', f'Margin spread {sd_m:.1f} points, total spread {sd_t:.1f}. Line and total prices at other numbers are in the CSV.', '']

    # player props
    e, choice, _ = props.project(p, fit_range=(props.FIT[0], last_done - 1), tune_season=last_done)
    eu = e[e.game.isin(up.game)].merge(up[['game', 'home', 'away']], on='game')
    L += ['## Player props (expected rotation, last squad)', '',
          'Our projection, the .5 line nearest an even chance and our over chance there, and fair prices at that line.', '']
    for gm in up.itertuples():
        d = eu[eu.game == gm.game].sort_values(['team', 'min_hat'], ascending=[True, False])
        if d.empty:
            continue
        tip = gm.tip.tz_convert('Australia/Melbourne').strftime('%a %d %b %H:%M')
        L += [f'### {gm.home} v {gm.away}, {tip}', '',
              '| player | team | minutes | ' + ' | '.join(props.NAMES[m] for m in MARKETS) + ' |',
              '|---|---|---|' + '---|' * len(MARKETS)]
        for x in d.itertuples():
            cells = []
            for mk in MARKETS:
                mu, a = getattr(x, f'{mk}_hat'), choice[mk]['a']
                ln, po = fair_line(mu, a)
                cells.append(f'{mu:.1f} (o{ln} {1 / po:.2f} / u {1 / (1 - po):.2f})')
                for l2 in (ln - 1, ln, ln + 1):
                    if l2 < 0:
                        continue
                    q = float(props.p_over(np.array([mu]), np.array([l2]), a)[0])
                    rows.append(dict(kind='prop', game=gm.game, tip=gm.tip, home=gm.home, away=gm.away, team=x.team, player=x.player,
                                     market=mk, side='over', line=l2, p=q, fair=1 / q if q > 0 else np.nan, mu=mu))
            L.append(f'| {x.player} | {x.team.split()[-1]} | {x.min_hat:.0f} | ' + ' | '.join(cells) + ' |')
        L.append('')
    L += ['Under prices: 1 / (1 - over chance). Props on a player who does not take the court are void at Australian books; '
          'a player subbed off hurt is not.']
    out = pd.DataFrame(rows)
    out['priced_at'] = now
    out.to_csv(f'{out_dir}/prices_{stamp}.csv', index=False)
    text = '\n'.join(L) + '\n'
    open(f'{out_dir}/prices_{stamp}.md', 'w').write(text)
    print(text)


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else 'nbl/cache', sys.argv[2] if len(sys.argv) > 2 else 'nbl/out',
        int(sys.argv[3]) if len(sys.argv) > 3 else 8)
