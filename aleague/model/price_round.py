"""Our prices for the coming A-League Men matches: every team market, at the open (no team news).

Fits the team model on every played match before the first upcoming kick-off, with the settings
frozen in aleague/model/settings.json, then prices each fixture in the next N days. Writes a markdown
table and a parquet of every market's fair price, ready to set beside a bookmaker's when lines arrive.

Usage: python -m aleague.model.price_round <tables dir> <out.md> [days ahead, default 8]
"""
import datetime as dt
import json
import os
import sys

import pandas as pd

from aleague.model.markets import price_all, score_matrix
import numpy as np

from aleague.model.team import fit, refit_level_and_home, training_rows, weights

SETTINGS = os.path.join(os.path.dirname(__file__), 'settings.json')


def main(tables, out, days=8, today=None):
    s = json.load(open(SETTINGS))
    m = pd.read_parquet(f'{tables}/matches.parquet')
    today = today or dt.date.today()
    upcoming = m[(~m.played) & (m.date >= today) & (m.date <= today + dt.timedelta(days=days))].sort_values('date')
    if upcoming.empty:
        print(f'no fixtures between {today} and {today + dt.timedelta(days=days)}')
        return
    first = upcoming.date.min()
    rows = training_rows(m, first)
    season_now = int(upcoming.season.iloc[0])
    f = fit(rows, weights(rows, first, season_now, s['half_life'], s['carry']), s['reg'])
    if s.get('home_half_life'):  # the league level and home edge on their own decay (docs/TEAM_STEP2.md)
        age = np.array([(first - d).days for d in rows.date], dtype=float)
        f = refit_level_and_home(f, rows, 0.5 ** (age / s['home_half_life']))
    priced = []
    for _, g in upcoming.iterrows():
        lh, la = f.rates(g.home, g.away, bool(g.neutral))
        p = price_all(score_matrix(lh, la, s['rho']))
        priced.append(dict(date=g.date, kickoff_utc=g.kickoff_utc, home=g.home, away=g.away, xg_home=lh, xg_away=la,
                           **{k: v for k, v in p.items()}))
    t = pd.DataFrame(priced)
    t.to_parquet(out.replace('.md', '.parquet'), index=False)
    lines = [f'# Our prices, A-League Men, {today} to {today + dt.timedelta(days=days)}', '',
             f'Fitted on {len(rows):,} matches played before {first}, run {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC; settings {s}. '
             'At the open: no team news. '
             'Fair prices, no margin: a book must beat these by enough before a bet is worth it.', '',
             '| date | match | xG | home | draw | away | over 2.5 | under 2.5 | BTTS yes | home -0.5 | home +0.5 |',
             '|---|---|---|---|---|---|---|---|---|---|---|']
    for _, r in t.iterrows():
        lines.append(f'| {r.date} | {r.home} v {r.away} | {r.xg_home:.2f}-{r.xg_away:.2f} | {1 / r.h2h_home:.2f} | '
                     f'{1 / r.h2h_draw:.2f} | {1 / r.h2h_away:.2f} | {r["over_2.5"]:.2f} | {r["under_2.5"]:.2f} | '
                     f'{1 / r.btts_yes:.2f} | {r["ah_home_-0.5"]:.2f} | {r["ah_home_+0.5"]:.2f} |')
    text = '\n'.join(lines) + '\n'
    open(out, 'w').write(text)
    print(text)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 8)
