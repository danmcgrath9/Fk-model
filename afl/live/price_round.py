"""Price a round that has not been played: from the named teams to every player's projection and fair prices.

Input: a CSV of the named teams (template: afl/live/teams_template.csv), one row per named player:
    season, round, date (YYYY-MM-DD), venue, home_team, away_team, team, player, sub
`sub` is 1 for the named substitute and 0 for everyone else once the sub is announced (about an hour before the
bounce); leave it blank until then, which the models read as unknown, as they read 2026 (which carries no sub flag). `player_id`
may be added as a column to settle a name the matcher cannot. Team and venue names are AFL Tables names (as in
afl/cache/frame.parquet); anything unknown is refused with the list of known names, never guessed.

How: the named rows are appended to the full history, with no stats, and the SAME feature code is run over the lot.
Every feature is shifted one game, so an unplayed game's features come only from games before it; an unplayed game's
totals are NaN, never zero (afl/model/frame.py `unplayed`). afl/tests/test_live.py checks that a past round priced this
way gets the same features as the history has for it. Models: afl/live/train_final.py.

Output: afl/docs/LIVE_<season>_R<round>.md and afl/cache/live_<season>_R<round>.csv. Players with under five games on
record, and the named sub, are listed as not priced (books price them, we have too little to go on).

Usage: python -m afl.live.price_round afl/cache named_teams.csv
"""
import json
import sys

import lightgbm as lgb
import numpy as np
import pandas as pd

from afl.model import extra as X
from afl.model import frame as F
from afl.model import props as P
from afl.model.walkforward import STATS
from afl.sheet import MILESTONES, fair, median_line, nb_cdf, px

COLUMNS = ['season', 'round', 'date', 'venue', 'home_team', 'away_team', 'team', 'player', 'sub']


def load_named(path, history):
    n = pd.read_csv(path)
    missing = [c for c in COLUMNS if c not in n.columns]
    if missing:
        raise SystemExit(f'named-teams CSV is missing columns: {missing}')
    n['team'] = n.team.replace(F.TEAM)
    n['home_team'] = n.home_team.replace(F.TEAM)
    n['away_team'] = n.away_team.replace(F.TEAM)
    teams = set(history.team)
    bad = sorted((set(n.team) | set(n.home_team) | set(n.away_team)) - teams)
    if bad:
        raise SystemExit(f'unknown team names {bad}; known: {sorted(teams)}')
    venues = set(history.venue)
    badv = sorted(set(n.venue) - venues)
    if badv:
        raise SystemExit(f'unknown venues {badv}; known: {sorted(venues)}')
    wrong = n[(n.team != n.home_team) & (n.team != n.away_team)]
    if len(wrong):
        raise SystemExit(f'{len(wrong)} players named for a team not in their game, e.g. {wrong.iloc[0].to_dict()}')
    return n


def match_players(n, history):
    """player_id for each named player: by name among players seen in the last two seasons, preferring his own club
    (so a traded player keeps his history). Ambiguous or unknown names are returned, not guessed."""
    recent = history[history.season >= history.season.max() - 1]
    last = recent.sort_values('dt').groupby('player_id').tail(1)[['player_id', 'Player', 'team']]
    last['key'] = last.Player.map(F._key)
    ids, problems = [], []
    for r in n.itertuples():
        if 'player_id' in n.columns and pd.notna(getattr(r, 'player_id', np.nan)):
            ids.append(int(r.player_id))
            continue
        c = last[last.key == F._key(r.player)]
        if len(c) > 1:
            c = c[c.team == r.team]
        if len(c) == 1:
            ids.append(int(c.player_id.iloc[0]))
        else:
            ids.append(np.nan)
            problems.append((r.team, r.player, 'no match' if c.empty else 'more than one match'))
    return n.assign(player_id=ids), problems


def future_rows(n, history):
    """The named players as rows of the base table, with every stat unknown."""
    ref = history.sort_values('dt').groupby('player_id').tail(1).set_index('player_id')
    dt = pd.to_datetime(n.date)
    is_home = (n.team == n.home_team)
    rows = pd.DataFrame({
        'season': n.season.astype(int), 'Round': n['round'].astype(str), 'round_no': pd.to_numeric(n['round'], errors='coerce'),
        'finals': ~n['round'].astype(str).str.fullmatch(r'\d+'), 'date': dt.dt.strftime('%Y-%m-%d'), 'dt': dt,
        'game': dt.dt.strftime('%Y-%m-%d') + '|' + n.home_team + '|' + n.away_team, 'venue': n.venue, 'team': n.team,
        'opp': np.where(is_home, n.away_team, n.home_team), 'is_home': is_home.astype(float),
        'player_id': n.player_id, 'Player': n.player, 'named_sub': pd.to_numeric(n['sub'], errors='coerce'),   # blank = not known yet
    })
    # age on the day: his age at his last game plus the days since (unknown for a debutant, who is not priced anyway)
    last_age, last_dt = rows.player_id.map(ref.age), rows.player_id.map(ref.dt)
    rows['age'] = last_age + (rows.dt - last_dt).dt.days / 365.25
    return rows


def features(cache, csv):
    at = pd.read_parquet(f'{cache}/afltables.parquet')
    fw = pd.read_parquet(f'{cache}/footywire.parquet')
    hist = F.base_table(at, fw)
    return build_live(hist, load_named(csv, hist))


def build_live(hist, n):
    """History plus the named rows, through the same feature code. Returns the table, the unplayed games, and any
    names that could not be matched."""
    n, problems = match_players(n, hist)
    fut = future_rows(n[n.player_id.notna()], hist)
    if fut.game.isin(hist.game).any():
        raise SystemExit('a named game is already in the history (played); price it with afl/sheet.py instead')
    m = pd.concat([hist, fut], ignore_index=True).sort_values(['dt', 'game', 'team']).reset_index(drop=True)
    m = F.add_features(m)
    m['finals'] = m.finals.astype(float)
    m = P.team_expected_score(m)
    return m, set(fut.game), problems


def project(cache, m, games):
    out = None
    for stat in STATS:
        meta = json.load(open(f'{cache}/models/{stat}.json'))
        s, _ = P.stat_features(m, stat)
        if meta['extra_inputs']:
            s = X.add_extra(s, cache, stat)
        if 'pos' not in s:
            s = s.assign(pos=X.position(s))
        s = s[s.game.isin(games)]
        s = P.eligible(s)
        s = s[s[f'{stat}_l10'].notna()]
        mdl = lgb.Booster(model_file=f'{cache}/models/{stat}.txt')
        s[f'mu_{stat}'] = mdl.predict(s[meta['features']])
        s[f'a_{stat}'] = s.pos.map(meta['a_pos']).fillna(meta['a']).astype(float)
        cols = ['game', 'season', 'Round', 'date', 'team', 'opp', 'player_id', 'Player', 'pos', 'exp_margin', f'mu_{stat}', f'a_{stat}']
        p = s[cols]
        out = p if out is None else out.merge(p[['game', 'player_id', f'mu_{stat}', f'a_{stat}']], on=['game', 'player_id'], how='outer')
    return out


def prices(r):
    r = r.copy()
    for s in ('D', 'M', 'T'):
        r[f'line_{s}'] = median_line(r[f'mu_{s}'].to_numpy(), r[f'a_{s}'].to_numpy())
        po = 1 - nb_cdf(np.floor(r[f'line_{s}']), r[f'mu_{s}'], r[f'a_{s}'])
        r[f'over_{s}'], r[f'under_{s}'] = fair(po), fair(1 - po)
    r['anytime'] = fair(1 - nb_cdf(0, r.mu_G, r.a_G))
    r['two_plus'] = fair(1 - nb_cdf(1, r.mu_G, r.a_G))
    for s, k in MILESTONES:
        r[f'{s}{k}'] = fair(1 - nb_cdf(k - 1, r[f'mu_{s}'], r[f'a_{s}']))
    return r


def to_markdown(r, named, problems, season, rnd):
    out = [f'# AFL price sheet: {season} round {rnd} (live)', '',
           'Fair prices, no margin, from the named teams. Margin is our results-only rating (the market is better at this; '
           'see docs/TEAM_STEP1.md). Not a tip: compare with the book, and only a price clearly longer than ours is a bet.', '']
    if problems:
        out += ['**Names not matched (not priced; add a player_id column to fix):** ' + '; '.join(f'{t}: {p} ({w})' for t, p, w in problems), '']
    for g, p in r.groupby('game', sort=True):
        home, away = g.split('|')[1:]
        em = p[p.team == home].exp_margin.iloc[0] if (p.team == home).any() else np.nan
        out += [f'## {home} v {away}', '', f'Rating margin: {home} {em:+.1f}.', '',
                '| player | team | disposals | over / under | marks | over / under | tackles | over / under | goal | 2+ | 20+ D | 25+ D | 30+ D | 5+ M | 5+ T |',
                '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
        for x in p.sort_values(['team', 'mu_D'], ascending=[True, False]).itertuples():
            out.append(f'| {x.Player} | {x.team} | {x.line_D} | {x.over_D:.2f} / {x.under_D:.2f} | {x.line_M} | {x.over_M:.2f} / {x.under_M:.2f} | '
                       f'{x.line_T} | {x.over_T:.2f} / {x.under_T:.2f} | {px(x.anytime)} | {px(x.two_plus)} | '
                       + ' | '.join(px(getattr(x, f'{s}{k}')) for s, k in MILESTONES) + ' |')
        priced = set(p.Player)
        unpriced = named[(named.home_team == home) & (named.away_team == away) & ~named.player.isin(priced)].player.tolist()
        if unpriced:
            out += ['', 'Named, not priced (under five games on record, or the named sub): ' + ', '.join(unpriced)]
        out.append('')
    return '\n'.join(out) + '\n'


def run(cache, csv):
    named = pd.read_csv(csv)
    m, games, problems = features(cache, csv)
    r = prices(project(cache, m, games))
    season, rnd = named.season.iloc[0], named['round'].iloc[0]
    md = to_markdown(r, named.assign(home_team=named.home_team.replace(F.TEAM), away_team=named.away_team.replace(F.TEAM)),
                     problems, season, rnd)
    open(f'afl/docs/LIVE_{season}_R{rnd}.md', 'w').write(md)
    r.to_csv(f'{cache}/live_{season}_R{rnd}.csv', index=False)
    print(md[:2500])


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])
