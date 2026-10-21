"""Parse NRL.com's prose team-list articles (2009-2019) into Tuesday's named teams.

Each article is read as text in order: a club's label ("Rabbitohs", "Storm:"), then its numbered
players ("1 Greg Inglis" on a line, or "1. Billy Slater, 2. Suliasi Vunivalu, ..."). Each list is tied
to the club's first game on or after the article's date (within 8 days), and each name to the RLP
player id of someone who played for that club that season (full name first, then surname), so we
know who was named and who took the field.

Only the FIRST team-list article for a game counts as Tuesday's list; "updated" lists and late mail
are later and are kept separately (kind).

Writes nrl/cache/named_teams.parquet: match_id, team, jersey, name, player_id, played, kind, url
Usage: python nrl/teamlists/parse.py nrl/cache <dir with teamlists_<season>.jsonl.gz>
"""
import glob
import gzip
import html as H
import json
import os
import re
import sys
import unicodedata

import numpy as np
import pandas as pd

ALIASES = {
    'Broncos': 'Brisbane Broncos', 'Bulldogs': 'Canterbury Bankstown Bulldogs', 'Raiders': 'Canberra Raiders',
    'Sharks': 'Cronulla Sutherland Sharks', 'Dolphins': 'Dolphins', 'Roosters': 'Sydney Roosters',
    'Titans': 'Gold Coast Titans', 'Sea Eagles': 'Manly Warringah Sea Eagles', 'Storm': 'Melbourne Storm',
    'Knights': 'Newcastle Knights', 'Cowboys': 'North Queensland Cowboys', 'Eels': 'Parramatta Eels',
    'Panthers': 'Penrith Panthers', 'Rabbitohs': 'South Sydney Rabbitohs', 'Dragons': 'St George Illawarra Dragons',
    'Wests Tigers': 'Wests Tigers', 'Tigers': 'Wests Tigers', 'Warriors': 'Warriors',
}
LABEL = re.compile(r'^\s*(?:[A-Za-z .\-\']*?\s)?(' + '|'.join(sorted(map(re.escape, ALIASES), key=len, reverse=True))
                   + r')\s*(?:\(squad\))?\s*:?\s*(.*)$', re.I)
ALIAS_CI = {k.lower(): v for k, v in ALIASES.items()}
STOP = re.compile(r'^(Referees?|Coach|Venue|Video|Touch|Sideline|Toyota|Bench referee|Play |Tickets|Broadcast|National Rugby League respects|Related)', re.I)
ENTRY = re.compile(r'(?<![\d.])(\d{1,2})\s*[.)]?\s+([A-Z][^\d,;]*)')


def text_lines(html):
    t = re.sub(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>', ' ', html)
    for _ in range(2):   # older articles carry their markup escaped inside the text: strip it twice
        t = H.unescape(re.sub(r'<[^>]+>', '\n', t)).replace('\xa0', ' ')
    return [re.sub(r'\s+', ' ', l).strip() for l in t.split('\n') if l.strip()]


def clean(name):
    n = re.sub(r'[©®]|\[[^\]]*\]', '', name)
    n = re.split(r'\.\s', n)[0]          # "Daniel Fitzhenry. MONDAY": the sentence after a name is not the name
    n = re.sub(r'\((?:c|cc|C|captain|capt|vc)\)', '', n)
    n = re.sub(r'\(.*?\)', '', n)
    n = re.split(r'\b(?:Interchange|Reserves?|Coach|Bench|Replacement)\b', n)[0]
    return n.strip(' .:&-')


def parse_block(text):
    """[(jersey, name)] from one club's block: numbered if it is, otherwise by order (13 starters, then bench)."""
    numbered = [(int(n), clean(x)) for n, x in ENTRY.findall(text)]
    numbered = [(n, x) for n, x in numbered if 2 <= len(x) <= 40 and n <= 30]
    if len(numbered) >= 10:
        return numbered
    parts = re.split(r'\bInterchange(?: from)?\s*:?', text, maxsplit=1, flags=re.I)
    starters = [clean(x) for x in parts[0].split(',')]
    bench = [clean(x) for x in parts[1].split(',')] if len(parts) > 1 else []
    starters = [x for x in starters if 2 <= len(x) <= 40 and not re.search(r'\d', x)]
    bench = [x for x in bench if 2 <= len(x) <= 40 and not re.search(r'\d', x)]
    if len(starters) != 13:
        return []
    return [(i + 1, x) for i, x in enumerate(starters)] + [(14 + i, x) for i, x in enumerate(bench)]


def parse_article(html):
    """[(club, jersey, name)] in reading order."""
    out, club, buf = [], None, []

    def flush():
        if club and buf:
            out.extend((club, n, x) for n, x in parse_block(' '.join(buf)))

    for line in text_lines(html):
        m = LABEL.match(line)
        if m and (len(line) < 40 or ENTRY.search(m.group(2) or '') or (m.group(2) or '').count(',') >= 8) \
                and ' v ' not in line:
            flush()
            club, buf = ALIAS_CI[m.group(1).lower()], [m.group(2) or '']
        elif STOP.match(line):
            flush()
            club, buf = None, []
        elif ' v ' in line or ' vs ' in line:
            flush()
            club, buf = None, []
        elif club is not None:
            buf.append(line)
    flush()
    return out


def key(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z]', '', s)


def main(cache, src):
    m = pd.read_parquet(f'{cache}/matches.parquet')
    pm = pd.read_parquet(f'{cache}/player_matches.parquet')
    players = pd.read_parquet(f'{cache}/players.parquet')
    long = pd.concat([m[['match_id', 'date', 'season', 'home_team']].rename(columns={'home_team': 'team'}),
                      m[['match_id', 'date', 'season', 'away_team']].rename(columns={'away_team': 'team'})])
    long = long.sort_values('date')
    pm = pm.merge(players[['player_id', 'full_name', 'last_name']], on='player_id', how='left') \
        .merge(m[['match_id', 'season']], on='match_id')
    roster = pm.drop_duplicates(['season', 'team', 'player_id'])
    full = {(r.season, r.team, key(r.full_name)): r.player_id for r in roster.itertuples()}
    roster = roster.assign(k=roster.last_name.map(key), f0=roster.full_name.map(key).str[:1])
    last = roster.groupby(['season', 'team', 'k']).apply(lambda d: list(zip(d.player_id, d.f0)), include_groups=False)
    played = set(zip(pm.match_id, pm.player_id))
    rows = []
    for f in sorted(glob.glob(os.path.join(src, 'teamlists_*.jsonl.gz'))):
        for line in gzip.open(f, 'rt'):
            a = json.loads(line)
            if not a['html']:
                continue
            d = re.search(r'/news/(\d{4})/(\d{2})/(\d{2})/', a['url'])
            date = pd.Timestamp(f'{d.group(1)}-{d.group(2)}-{d.group(3)}')
            kind = 'late_mail' if 'late-mail' in a['url'] else 'updated' if 'updated' in a['url'] else 'named'
            for club, num, name in parse_article(a['html']):
                g = long[(long.team == club) & (long.date >= date) & (long.date <= date + pd.Timedelta(days=8))]
                if g.empty:
                    continue
                g = g.iloc[0]
                pid = full.get((g.season, club, key(name)))
                if pid is None:
                    cand = last.get((g.season, club, key(name.split()[-1])), [])
                    if len(cand) > 1:   # shared surname at the club: settle it by first initial
                        cand = [c for c in cand if c[1] == key(name)[:1]]
                    pid = cand[0][0] if len(cand) == 1 else None
                rows.append(dict(match_id=g.match_id, season=g.season, team=club, jersey=num, name=name,
                                 player_id=pid, kind=kind, url=a['url'], article_date=date))
    df = pd.DataFrame(rows)
    if df.empty:
        print('no lists parsed')
        return
    df['player_id'] = df.player_id.astype('Int64')
    df['played'] = [(mid, pid) in played if pd.notna(pid) else False for mid, pid in zip(df.match_id, df.player_id)]
    # one list per kind per team-game: the earliest article of that kind
    df = df.sort_values('article_date').drop_duplicates(['match_id', 'team', 'kind', 'jersey'])
    df.to_parquet(f'{cache}/named_teams.parquet', index=False)
    n = df[df.kind == 'named']
    tg = n.groupby(['match_id', 'team'])
    print(f'named_teams: {len(df):,} rows; Tuesday lists for {tg.ngroups:,} team-games, seasons '
          f'{sorted(n.season.unique())}; names matched to a player {n.player_id.notna().mean():.1%}; '
          f'named 1-17 who did not play {(~n[n.jersey <= 17].played).mean():.1%}')


if __name__ == '__main__':
    main(*sys.argv[1:3])
