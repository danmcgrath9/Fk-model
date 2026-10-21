"""Build player tables from the Ultimate A-League pages (ual_<season>.tar.gz on aleague-history).

Content: Ultimate A-League (ultimatealeague.com), CC BY 4.0. Derived tables keep that attribution.

Writes, beside matches.parquet:
  ual_matches.parquet    one row per page: teams, local kick-off, referee, crowd, score, and our match_id
                         when the page matches a row of matches.parquet (same teams, dates within a day)
                         with the same score
  player_games.parquet   one row per player per match: team, opponent, home or away, started or not,
                         minutes within 90, goals (own goals excluded), penalties scored, yellow and red
                         cards, the referee
  ual_events.parquet     every timeline event as given (for checking the event names)
  UAL_BUILD.md           counts, the event names seen, and the cross-check against matches.parquet

Usage: python -m aleague.data.ual_build <dir with ual_*.tar.gz> <tables dir>
"""
import datetime as dt
import glob
import gzip
import os
import re
import sys
import tarfile

import pandas as pd

from aleague.data.ual_parse import parse_match
from aleague.data.wiki_parse import club

GOAL = re.compile(r'^(goal|penalty goal|penalty)$', re.I)
OWN_GOAL = re.compile(r'own goal', re.I)
PEN = re.compile(r'penalty', re.I)
MISSED = re.compile(r'miss|saved', re.I)
YELLOW = re.compile(r'^yellow card$', re.I)
RED = re.compile(r'red card|second yellow', re.I)


def local_date(s):
    m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', s or '')
    return dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1))) if m else None


def read_tars(src):
    matches, events, players, bad = [], [], [], []
    for path in sorted(glob.glob(os.path.join(src, 'ual_*.tar.gz'))):
        with tarfile.open(path) as tar:
            for mem in tar.getmembers():
                m = re.search(r'/(\d+)\.html\.gz$', mem.name)
                if not m:
                    continue
                html = gzip.decompress(tar.extractfile(mem).read()).decode('utf-8', 'replace')
                try:
                    r = parse_match(html, int(m.group(1)))
                except ValueError as e:
                    bad.append(f'{mem.name}: {e}'); continue
                matches.append(r['match']); events += r['events']; players += r['players']
    return pd.DataFrame(matches), pd.DataFrame(events), pd.DataFrame(players), bad


def link(um, ours):
    """our match_id for each page: same canonical teams, dates within a day, same score."""
    key = {}
    for _, r in ours.iterrows():
        key.setdefault((r.home, r.away), []).append((r.date, r.match_id, r.home_goals, r.away_goals))
    ids, agree = [], []
    for _, r in um.iterrows():
        best = None
        for d, mid, hg, ag in key.get((r.home_c, r.away_c), []):
            if r.date is not None and abs((d - r.date).days) <= 1:
                best = (mid, hg, ag)
        ids.append(best[0] if best else None)
        agree.append(bool(best) and best[1] == r.home_goals and best[2] == r.away_goals)
    return ids, agree


def build(src, tables):
    um, ev, pl, bad = read_tars(src)
    um['home_c'], um['away_c'] = um.home.map(club), um.away.map(club)
    um['date'] = um.when_local.map(local_date)
    um['season'] = um.season.map(lambda x: int(x[:4]) + 1)  # '2021-22' -> 2022, as in matches.parquet
    ours = pd.read_parquet(os.path.join(tables, 'matches.parquet'))
    um['match_id'], um['score_agrees'] = link(um, ours)
    um = um[um.completed & um.home_goals.notna()].copy()

    # per-player counts from the timeline
    ev['goal'] = ev.event.fillna('').str.match(GOAL) & ~ev.event.fillna('').str.contains(MISSED)
    ev['own_goal'] = ev.event.fillna('').str.contains(OWN_GOAL)
    ev['pen_goal'] = ev.goal & ev.event.fillna('').str.contains(PEN)
    ev['yellow'] = ev.event.fillna('').str.match(YELLOW)
    ev['red'] = ev.event.fillna('').str.contains(RED)
    ev90 = ev[ev.minute.fillna(0) <= 90]  # extra-time events do not settle bets
    counts = ev90.groupby(['ual_match_id', 'side', 'player_id'])[['goal', 'pen_goal', 'yellow', 'red']].sum().reset_index()

    p = pl.merge(counts, on=['ual_match_id', 'side', 'player_id'], how='left')
    for c in ('goal', 'pen_goal', 'yellow', 'red'):
        p[c] = p[c].fillna(0).astype(int)
    p = p.merge(um[['ual_match_id', 'match_id', 'season', 'date', 'home_c', 'away_c', 'referee', 'score_agrees']],
                on='ual_match_id', how='inner')
    p['team'] = p.home_c.where(p.side == 'home', p.away_c)
    p['opponent'] = p.away_c.where(p.side == 'home', p.home_c)
    p['is_home'] = p.side == 'home'
    p = p.drop(columns=['home_c', 'away_c'])

    os.makedirs(tables, exist_ok=True)
    um.to_parquet(os.path.join(tables, 'ual_matches.parquet'), index=False)
    p.to_parquet(os.path.join(tables, 'player_games.parquet'), index=False)
    ev.to_parquet(os.path.join(tables, 'ual_events.parquet'), index=False)

    # checks: goals in the timeline against the score; minutes per side
    lines = ['# Ultimate A-League tables', '',
             f'{len(um):,} completed matches, {len(p):,} player-match rows, {len(ev):,} events; '
             f'{len(bad)} pages unreadable. Content: Ultimate A-League, CC BY 4.0.', '',
             'Event names seen: ' + ', '.join(f'{k} ({v})' for k, v in ev.event.value_counts().items()), '',
             '| season | matches | linked to matches.parquet | score agrees | player rows | starters per side | minutes per side |',
             '|---|---|---|---|---|---|---|']
    for s, x in um.groupby('season'):
        px = p[p.season == s]
        side = px.groupby(['ual_match_id', 'side'])
        lines.append(f'| {s - 1}-{str(s)[2:]} | {len(x)} | {x.match_id.notna().sum()} | {x.score_agrees.sum()} | {len(px):,} | '
                     f'{side.starter.sum().mean():.2f} | {side.minutes.sum().mean():.1f} |')
    lines += ['', 'Unreadable pages: ' + ('; '.join(bad[:10]) or 'none'), '']
    text = '\n'.join(lines) + '\n'
    open(os.path.join(tables, 'UAL_BUILD.md'), 'w').write(text)
    print(text)
    return um, p, ev


if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])
