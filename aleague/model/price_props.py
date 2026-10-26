"""Our prices for player props in the coming A-League Men matches, at the open (teams not yet named).

Built exactly as the backtest builds them (aleague/model/props_backtest.py): each player's decayed goal
and card rates from his earlier matches, shrunk to the league; expected minutes from his recent role
(share of recent squads he started); the scorer chance scaled by the match's expected goals over his
team's recent average and blended 50/50 with his raw per-appearance rate; the card chance blended 70/30
and Platt-rescaled (constants from the selection seasons, docs/PROPS_STEP1.md). Players listed are each
club's last two matchday squads. Prices assume the player takes the field (a non-runner is void at most
books; check each book's rule).

Usage: python -m aleague.model.price_props <tables dir> <out.md> [days ahead, default 8]
"""
import datetime as dt
import json
import os
import sys

import numpy as np
import pandas as pd

from aleague.model.props_backtest import HALF_LIFE, PRIOR_90S
from aleague.model.team import early_shrink, fit, refit_level_and_home, season_counts, training_rows, weights

SETTINGS = os.path.join(os.path.dirname(__file__), 'settings.json')
PLATT_CARD = (-0.304, 0.751)   # fitted on 2016-17 to 2020-21 (docs/PROPS_STEP1.md)


def player_state(pg, before):
    """Decayed totals per player over matches before `before`."""
    d = 0.5 ** (1 / HALF_LIFE)
    dr = 0.5 ** (1 / 3)
    hist = pg[pg.date < before].sort_values(['date', 'match_id'])
    st = {}
    for r in hist.itertuples(index=False):
        a = st.setdefault(r.player_id, dict(goal=0., card=0., mins=0., apps=0., smin=0., starts=0., bmin=0., benches=0.,
                                            rs=0., rn=0., team=r.team, player=r.player, gk=r.gk))
        for k in ('goal', 'card', 'mins', 'apps', 'smin', 'starts', 'bmin', 'benches'):
            a[k] *= d
        a['rs'] *= dr; a['rn'] *= dr
        a['goal'] += r.goal; a['card'] += r.yellow + r.red; a['mins'] += r.minutes; a['apps'] += r.minutes > 0
        if r.starter:
            a['smin'] += r.minutes; a['starts'] += 1
        else:
            a['bmin'] += r.minutes; a['benches'] += 1
        a['rs'] += r.starter; a['rn'] += 1
        a['team'], a['player'], a['gk'] = r.team, r.player, r.gk
    return st


def main(tables, out, days=8, today=None):
    s = json.load(open(SETTINGS))
    m = pd.read_parquet(f'{tables}/matches.parquet')
    pg = pd.read_parquet(f'{tables}/player_games.parquet')
    pg = pg[pg.match_id.notna()]
    today = today or dt.date.today()
    upcoming = m[(~m.played) & (m.date >= today) & (m.date <= today + dt.timedelta(days=days))].sort_values('date')
    if upcoming.empty:
        print('no fixtures in range'); return
    first = upcoming.date.min()
    rows = training_rows(m, first)
    f = fit(rows, weights(rows, first, int(upcoming.season.iloc[0]), s['half_life'], s['carry']), s['reg'])
    age = np.array([(first - d_).days for d_ in rows.date], dtype=float)
    f = refit_level_and_home(f, rows, 0.5 ** (age / s['home_half_life']))
    counts = season_counts(m, first)
    league = pg[(pg.date < first) & ~pg.gk]
    recent = league[league.season >= league.season.max() - 2]
    goal90 = recent.goal.sum() / recent.minutes.sum() * 90
    card90 = (recent.yellow + recent.red).sum() / recent.minutes.sum() * 90
    st = player_state(pg, first)
    # each club's last two matchday squads
    last2 = pg[pg.date < first].sort_values('date').groupby('team').match_id.apply(lambda x: list(dict.fromkeys(x))[-2:])
    lines = [f'# Our player-prop prices, A-League Men, {today} to {today + dt.timedelta(days=days)}', '',
             f'Run {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC, at the open (teams not named). Fair prices, no '
             'margin, assuming the player takes the field. Top ten scorer chances per match.', '']
    all_rows = []
    for _, g in upcoming.iterrows():
        kh = early_shrink(counts.get((g.season, g.home), 0), s['early_alpha'], s['early_tau'])
        ka = early_shrink(counts.get((g.season, g.away), 0), s['early_alpha'], s['early_tau'])
        lh, la = f.rates(g.home, g.away, bool(g.neutral), kh, ka)
        rows_ = []
        for team, xg, k in ((g.home, lh, kh), (g.away, la, ka)):
            squad = set(pg[pg.match_id.isin(last2.get(team, []))].player_id)
            # the team's usual expected goals: against an average defence, with half the home edge
            team_avg = float(np.exp(f.mu + f.att.get(team, 0.0) * k + 0.5 * f.home))
            for pid in squad:
                a = st.get(pid)
                if a is None or a['team'] != team:
                    continue
                r90g = (a['goal'] + goal90 * PRIOR_90S['goal']) / (a['mins'] / 90 + PRIOR_90S['goal'])
                r90c = (a['card'] + card90 * PRIOR_90S['yellow']) / (a['mins'] / 90 + PRIOR_90S['yellow'])
                p_start = (a['rs'] + 0.5) / (a['rn'] + 1)
                exp_min = p_start * (a['smin'] + 225) / (a['starts'] + 3) + (1 - p_start) * max((a['bmin'] + 45) / (a['benches'] + 3), 20)
                p_model = 0.002 if a['gk'] else 1 - np.exp(-r90g * exp_min / 90 * xg / team_avg)
                raw = 0.002 if a['gk'] else 1 - np.exp(-(a['goal'] + 0.5) / (a['apps'] + 5))
                p_goal = np.exp(0.5 * np.log(max(p_model, 1e-9)) + 0.5 * np.log(max(raw, 1e-9)))
                c_model = 1 - np.exp(-r90c * exp_min / 90)
                c_raw = 1 - np.exp(-(a['card'] + 0.5) / (a['apps'] + 5))
                c = np.exp(0.7 * np.log(c_model) + 0.3 * np.log(c_raw))
                z = PLATT_CARD[0] + PLATT_CARD[1] * np.log(c / (1 - c))
                p_card = 1 / (1 + np.exp(-z))
                rows_.append(dict(date=g.date, match=f'{g.home} v {g.away}', team=team, player=a['player'],
                                  p_start=p_start, exp_min=exp_min, p_goal=p_goal, p_card=p_card))
        t = pd.DataFrame(rows_).sort_values('p_goal', ascending=False)
        all_rows.append(t)
        lines += [f'## {g.date} {g.home} v {g.away} (xG {lh:.2f}-{la:.2f})', '',
                  '| player | team | starts lately | scorer | fair price | carded | fair price |', '|---|---|---|---|---|---|---|']
        for _, r in t.head(10).iterrows():
            lines.append(f'| {r.player} | {r.team} | {r.p_start:.0%} | {r.p_goal:.1%} | {1 / r.p_goal:.2f} | '
                         f'{r.p_card:.1%} | {1 / r.p_card:.2f} |')
        lines.append('')
    if all_rows:
        pd.concat(all_rows).to_parquet(out.replace('.md', '.parquet'), index=False)
    text = '\n'.join(lines) + '\n'
    open(out, 'w').write(text)
    print(text)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 8)
