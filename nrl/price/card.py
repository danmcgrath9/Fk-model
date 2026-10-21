"""Price a round: our probabilities and fair prices for every game and every named player.

Input:
  games.csv   home,away,kick_off[,line,total]   kick_off as Sydney time 'YYYY-MM-DD HH:MM'; line is the
              home side's handicap to price (e.g. -6.5), total the points line (e.g. 44.5)
  teams.csv   team,jersey,name   (optional) Tuesday's lists. A club without a list is priced on the 17 it
              used last game: that is the "at the open" price, before teams are named.

The games are added to the history as upcoming (no result), every frame is rebuilt, and the same team
and try models as the backtest price them. Nothing is bet and nothing leaves this machine: the card is
written to nrl/cache/card/ for the founder to read.

Fair price = 1 / our probability. A bet is worth considering only when a book's price beats ours by
enough, and the backtest decides how much is enough.

Usage: python -m nrl.price.card nrl/cache games.csv [teams.csv]
"""
import contextlib
import io
import os
import re
import shutil
import sys
import tempfile
import unicodedata

import numpy as np
import pandas as pd

from nrl.model import player_frame, player_ratings, team, team_frame, tries

JERSEY_POSITION = {1: 'FB', 2: 'W', 3: 'C', 4: 'C', 5: 'W', 6: 'FE', 7: 'HB', 8: 'FR', 9: 'HK', 10: 'FR', 11: '2R',
                   12: '2R', 13: 'L'}


def key(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z]', '', s)


def canon_team(name, known):
    k = key(name)
    for t in known:
        if k == key(t) or k in key(t):
            return t
    raise SystemExit(f'unknown team "{name}"; use one of: {", ".join(sorted(known))}')


def resolve_players(cache, named, m, pm):
    """Map each named player to a player id: full name among his club's recent players first, then anyone."""
    players = pd.read_parquet(f'{cache}/players.parquet')
    recent = pm.merge(m[['match_id', 'date']], on='match_id').sort_values('date')
    last_team = recent.drop_duplicates('player_id', keep='last').set_index('player_id').team
    by_name = {}
    for r in players.itertuples():
        by_name.setdefault(key(r.full_name), []).append(r.player_id)
    try:
        cd = pd.read_parquet(f'{cache}/cd_player_games.parquet')
        links = pd.read_parquet(f'{cache}/cd_links.parquet')
        to_rlp = dict(zip(links.cd_player_id, links.player_id))
        for r in cd.drop_duplicates('playerId').itertuples():
            pid = to_rlp.get(r.playerId, -r.playerId)
            by_name.setdefault(key(f'{r.firstname} {r.surname}'), [])
            if pid not in by_name[key(f'{r.firstname} {r.surname}')]:
                by_name[key(f'{r.firstname} {r.surname}')].append(pid)
    except FileNotFoundError:
        pass
    ids, unknown = [], []
    for r in named.itertuples():
        cands = by_name.get(key(r.name), [])
        same = [c for c in cands if last_team.get(c) == r.team]
        pick = (same or cands or [None])[0]
        if pick is None:
            unknown.append(f'{r.name} ({r.team})')
            pick = -(10 ** 9) - len(unknown)   # a debutant: an average player to every model
        ids.append(int(pick))
    return ids, unknown


def main(cache, games_csv, teams_csv=None):
    """Works on a copy of the cache, so a priced round never enters the backtest's history."""
    home = cache
    cache = os.path.join(tempfile.mkdtemp(), 'cache')
    shutil.copytree(home, cache, ignore=shutil.ignore_patterns('card', 'cd', '*.tar.gz', 'teamlists*', 'sources'))
    for f in ('matches_upcoming.parquet', 'player_matches_upcoming.parquet'):
        if os.path.exists(f'{cache}/{f}'):
            os.remove(f'{cache}/{f}')
    m, pm = team_frame.history(cache)
    known = set(m.home_team) | set(m.away_team)
    games = pd.read_csv(games_csv)
    games['home'] = [canon_team(t, known) for t in games.home]
    games['away'] = [canon_team(t, known) for t in games.away]
    games['kick_off'] = pd.to_datetime(games.kick_off)
    games['match_id'] = -(2 * 10 ** 9) - np.arange(len(games))
    named = pd.read_csv(teams_csv) if teams_csv else pd.DataFrame(columns=['team', 'jersey', 'name'])
    if len(named):
        named['team'] = [canon_team(t, known) for t in named.team]
    rows, prow, notes = [], [], []
    for g in games.itertuples():
        rows.append(dict(competition='NRL', competition_year=f'NRL {g.kick_off.year}', round='Round 0',
                         special_round=None, date=pd.Timestamp(g.kick_off.date()), time=None,
                         time_24hr=g.kick_off.strftime('%H:%M:%S'), match_id=g.match_id, venue_id=-1, crowd=np.nan,
                         home_team=g.home, home_team_ht_score=np.nan, home_team_score=np.nan,
                         home_team_penalties=np.nan, away_team=g.away, away_team_ht_score=np.nan,
                         away_team_score=np.nan, away_team_penalties=np.nan, season=g.kick_off.year))
        for side, opp in ((g.home, g.away), (g.away, g.home)):
            lst = named[named.team == side]
            if len(lst):
                lst = lst[lst.jersey <= 17].copy()
                ids, unknown = resolve_players(cache, lst, m, pm)
                notes += [f'not found, priced as an average debutant: {u}' for u in unknown]
                for (j, pid) in zip(lst.jersey, ids):
                    prow.append(dict(player_id=pid, match_id=g.match_id, team=side, opposition_team=opp,
                                     number=float(j), position=JERSEY_POSITION.get(int(j), 'B')))
                notes.append(f'{side}: Tuesday list ({len(lst)} players)')
            else:
                last = m[(m.home_team == side) | (m.away_team == side)].dropna(subset=['home_team_score']) \
                    .sort_values('date').match_id.iloc[-1]
                prev = pm[(pm.match_id == last) & (pm.team == side)]
                for r in prev.itertuples():
                    prow.append(dict(player_id=r.player_id, match_id=g.match_id, team=side, opposition_team=opp,
                                     number=r.number, position=r.position))
                notes.append(f'{side}: no list given, priced on its last game\'s 17 (at the open)')
    pu = pd.DataFrame(prow)
    for c in pm.columns:
        if c not in pu:
            pu[c] = np.nan if c not in ('captain',) else False
    pd.DataFrame(rows).to_parquet(f'{cache}/matches_upcoming.parquet', index=False)
    pu[pm.columns].to_parquet(f'{cache}/player_matches_upcoming.parquet', index=False)

    with contextlib.redirect_stdout(io.StringIO()):
        player_ratings.main(cache)
        team_frame.main(cache)
        player_frame.main(cache)
        tries.main(cache)
    tf = pd.read_parquet(f'{cache}/team_frame.parquet')
    g_all = team.games(tf)
    _, models = team.evaluate(g_all, [], '')
    up = g_all[g_all.match_id.isin(games.match_id)].set_index('match_id').loc[games.match_id]
    named_teams = set(named.team)
    out = ['# Price card', '', f'Built {pd.Timestamp.now(tz="Australia/Sydney"):%Y-%m-%d %H:%M} Sydney. '
           'Fair price = 1 / our probability. Paper only.', '',
           '| game | version | home win | fair home | fair away | our margin (home) | line | P(home covers) | '
           'our total | total line | P(over) |', '|---|---|---|---|---|---|---|---|---|---|---|']
    for g, (mid, r) in zip(games.itertuples(), up.iterrows()):
        ver = 'teams named' if g.home in named_teams and g.away in named_teams else 'open'
        feats, mm, tm = models[ver]
        X = r[feats].to_numpy(float)[None, :]
        Xt = r[team.TOTAL_FEATURES].to_numpy(float)[None, :]
        pw = float(team.win_prob(mm, X)[0])
        line = getattr(g, 'line', np.nan)
        tot = getattr(g, 'total', np.nan)
        cover = float(mm.prob_above(X, -line)[0]) if pd.notna(line) else np.nan
        over = float(tm.prob_above(Xt, tot)[0]) if pd.notna(tot) else np.nan
        out.append(f'| {g.home} v {g.away} | {ver} | {pw:.1%} | {1 / pw:.2f} | {1 / (1 - pw):.2f} | '
                   f'{float(mm.mean(X)[0]):+.1f} | {line if pd.notna(line) else ""} | '
                   f'{"" if np.isnan(cover) else f"{cover:.1%}"} | {float(tm.mean(Xt)[0]):.1f} | '
                   f'{tot if pd.notna(tot) else ""} | {"" if np.isnan(over) else f"{over:.1%}"} |')
    tp = pd.read_parquet(f'{cache}/try_predictions.parquet')
    tp = tp[tp.match_id.isin(games.match_id)]
    players = pd.read_parquet(f'{cache}/players.parquet').set_index('player_id').full_name
    pu_names = dict(zip(pu.player_id, pu.player_id.map(players)))
    if len(named):
        nm = named.copy()
        nm['player_id'] = sum((resolve_players(cache, named[named.team == t], m, pm)[0] for t in named.team.unique()), [])
        pu_names.update(dict(zip(nm.player_id, nm.name)))
    out += ['', '## Try scorers', '', '| game | team | player | position | anytime | fair | 2+ | fair | first | fair |',
            '|---|---|---|---|---|---|---|---|---|---|']
    gname = dict(zip(games.match_id, games.home + ' v ' + games.away))
    for r in tp.sort_values(['match_id', 'p_any'], ascending=[True, False]).itertuples():
        out.append(f'| {gname[r.match_id]} | {r.team} | {pu_names.get(r.player_id, r.player_id)} | {r.position} | '
                   f'{r.p_any:.1%} | {1 / r.p_any:.2f} | {r.p_two:.1%} | {1 / max(r.p_two, 1e-4):.1f} | '
                   f'{r.p_first:.1%} | {1 / max(r.p_first, 1e-4):.1f} |')
    out += ['', '## Notes', ''] + [f'- {n}' for n in notes]
    os.makedirs(f'{home}/card', exist_ok=True)
    text = '\n'.join(out) + '\n'
    open(f'{home}/card/CARD.md', 'w').write(text)
    shutil.rmtree(os.path.dirname(cache), ignore_errors=True)
    print(text)


if __name__ == '__main__':
    main(*sys.argv[1:4])
