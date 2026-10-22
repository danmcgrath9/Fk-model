"""Flatten saved Odds API responses into rows, and match them to our games and players.

One row per snapshot x book x market x player x side: event, commence, snapshot time, hours before the bounce, book,
market, player (as the book names him), side (Over/Under, or team name for team markets), point (the line), price.
Team names: the API uses full club names ("Greater Western Sydney Giants"); ours are the AFL Tables short forms.
Player names: matched within the two sides that played that game, by full name, then surname + first initial.
"""
import glob
import json
import os
import re
import unicodedata

import pandas as pd

OUR_TEAMS = ['Adelaide', 'Brisbane', 'Carlton', 'Collingwood', 'Essendon', 'Fremantle', 'Geelong', 'Gold Coast', 'GWS',
             'Hawthorn', 'Melbourne', 'North Melbourne', 'Port Adelaide', 'Richmond', 'St Kilda', 'Sydney', 'West Coast',
             'Western Bulldogs']
TEAM_ALIASES = {'greater western sydney': 'GWS', 'gws': 'GWS', 'brisbane': 'Brisbane', 'kangaroos': 'North Melbourne',
                'footscray': 'Western Bulldogs', 'bulldogs': 'Western Bulldogs', 'st. kilda': 'St Kilda', 'saint kilda': 'St Kilda'}


def _norm(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'\s+', ' ', re.sub(r"[^a-z .']", ' ', s)).strip()


def team_name(api_name):
    """'Greater Western Sydney Giants' -> 'GWS'; longest club name that the API name starts with wins
    (so 'North Melbourne Kangaroos' is not read as 'Melbourne')."""
    n = _norm(api_name)
    for alias, ours in sorted(TEAM_ALIASES.items(), key=lambda kv: -len(kv[0])):
        if n.startswith(alias):
            return ours
    for ours in sorted(OUR_TEAMS, key=len, reverse=True):
        if n.startswith(_norm(ours)):
            return ours
    return None


def flatten(raw_dir, label='*'):
    """Every saved odds snapshot under raw_dir/odds/<event>/<label>.json (all labels by default)."""
    rows = []
    for f in glob.glob(os.path.join(raw_dir, 'odds', '*', f'{label}.json')):
        with open(f) as fh:
            body = json.load(fh)
        snap = body.get('timestamp')
        e = body.get('data') or {}
        if not e:
            continue
        start = pd.Timestamp(e['commence_time'])
        for bk in e.get('bookmakers', []):
            for mk in bk.get('markets', []):
                for o in mk.get('outcomes', []):
                    rows.append(dict(event=e['id'], commence=start, home_api=e['home_team'], away_api=e['away_team'],
                                     snapshot=pd.Timestamp(snap), book=bk['key'], market=mk['key'],
                                     player=o.get('description'), side=o.get('name'), point=o.get('point'), price=o.get('price')))
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df['hours_before'] = (df.commence - df.snapshot).dt.total_seconds() / 3600
    df['home'] = df.home_api.map(team_name)
    df['away'] = df.away_api.map(team_name)
    # one row per book/market/player/side/snapshot (overlapping offsets can return the same snapshot twice)
    return df.drop_duplicates(['event', 'snapshot', 'book', 'market', 'player', 'side', 'point'])


def match_games(lines, fixture):
    """Attach our game id: same two teams, local date within a day of the commence time."""
    ev = lines.drop_duplicates('event')[['event', 'commence', 'home', 'away']].copy()
    ev['local'] = ev.commence.dt.tz_convert('Australia/Melbourne').dt.date
    fx = fixture.copy()
    fx['d'] = pd.to_datetime(fx.date).dt.date
    out = []
    for r in ev.itertuples():
        cand = fx[((fx.home == r.home) & (fx.away == r.away)) | ((fx.home == r.away) & (fx.away == r.home))]
        cand = cand[cand.d.map(lambda d: abs((d - r.local).days) <= 1)]
        out.append((r.event, cand.game.iloc[0] if len(cand) == 1 else None))
    return lines.merge(pd.DataFrame(out, columns=['event', 'game']), on='event', how='left')


def _key(name):
    return re.sub(r'[^a-z ]', '', _norm(name)).strip()


def match_players(lines, players):
    """players: one row per player-game with game, player_id, Player. Adds player_id to prop rows."""
    lk = players[['game', 'player_id', 'Player']].copy()
    lk['key'] = lk.Player.map(_key)
    lk['si'] = lk.key.str.split().str[-1] + '|' + lk.key.str[:1]
    full = lk.drop_duplicates(['game', 'key'], keep=False).set_index(['game', 'key']).player_id
    si = lk.drop_duplicates(['game', 'si'], keep=False).set_index(['game', 'si']).player_id
    props = lines[lines.player.notna()].copy()
    props['key'] = props.player.map(_key)
    props['si'] = props.key.str.split().str[-1] + '|' + props.key.str[:1]
    pid = [full.get((g, k), si.get((g, s))) for g, k, s in zip(props.game, props.key, props.si)]
    props['player_id'] = pid
    return props
