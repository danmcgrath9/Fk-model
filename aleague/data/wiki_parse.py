"""Read A-League Men matches and goals out of Wikipedia club season pages (aleague/data/wiki_fetch.py).

Each club season page lists its matches as {{football box}} templates under section headings. A box
is kept as a league match when it sits under an A-League heading (regular season or finals) and not
under a cup, pre-season, friendly or Asian heading. Every league match appears on both clubs' pages,
so each match is read twice: the two readings are merged, and any disagreement on the score is
reported, never silently resolved.

Outputs (pure functions, no I/O beyond reading the files given):
  parse_page(text, season) -> list of match dicts, each with its goals
  read_dir(path)           -> (matches DataFrame, goals DataFrame, problems list)

Text is CC BY-SA 4.0, Wikipedia contributors; aleague/README.md carries the attribution.
"""
import datetime as dt
import os
import re
from collections import defaultdict

import pandas as pd

MONTHS = {m: i for i, m in enumerate(['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
                                      'september', 'october', 'november', 'december'], 1)}
MONTHS.update({k[:3]: v for k, v in list(MONTHS.items())})
# headings that are never league football
NOT_LEAGUE = re.compile(r'cup|pre-?season|friendl|afc|champions|asian|club world|tour|trial|exhibition|'
                        r'women|youth|nyl|npl|summary|statistic|squad|transfer', re.I)
LEAGUE = re.compile(r'a-league|regular season|finals|league', re.I)

# one name per club, whatever the page calls it (link target or display text)
CLUB_ALIASES = {
    'adelaide united': 'Adelaide United', 'auckland': 'Auckland FC', 'auckland fc': 'Auckland FC',
    'brisbane roar': 'Brisbane Roar', 'central coast mariners': 'Central Coast Mariners',
    'macarthur': 'Macarthur FC', 'macarthur fc': 'Macarthur FC',
    'melbourne city': 'Melbourne City', 'melbourne heart': 'Melbourne City',
    'melbourne victory': 'Melbourne Victory', 'newcastle jets': 'Newcastle Jets', 'perth glory': 'Perth Glory',
    'sydney': 'Sydney FC', 'sydney fc': 'Sydney FC', 'wellington phoenix': 'Wellington Phoenix',
    'western sydney wanderers': 'Western Sydney Wanderers', 'western united': 'Western United',
}


def club(raw):
    """Canonical club name from a team field ('[[Adelaide United FC|Adelaide United]]', 'Sydney FC', ...)."""
    s = re.sub(r'\{\{[^}]*\}\}|<[^>]+>', '', raw or '')
    names = re.findall(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]', s)
    candidates = [x for pair in names for x in pair if x] if names else [s]
    for c in candidates:
        key = re.sub(r'\s+(fc|football club)$', '', c.strip().lower())
        key = re.sub(r'\s+', ' ', key)
        if key in CLUB_ALIASES:
            return CLUB_ALIASES[key]
        if c.strip().lower() in CLUB_ALIASES:
            return CLUB_ALIASES[c.strip().lower()]
    return None


def boxes(text):
    """(heading path, box body) for every football box, matching nested braces."""
    out = []
    heads = {}
    pos = 0
    pat = re.compile(r'^(={2,6})\s*(.*?)\s*\1\s*$|\{\{\s*football ?box', re.I | re.M)
    while True:
        m = pat.search(text, pos)
        if not m:
            return out
        if m.group(1):
            level = len(m.group(1))
            heads = {k: v for k, v in heads.items() if k < level}
            heads[level] = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', m.group(2))
            pos = m.end()
            continue
        depth, i = 0, m.start()
        while i < len(text):
            if text.startswith('{{', i):
                depth += 1; i += 2; continue
            if text.startswith('}}', i):
                depth -= 1; i += 2
                if depth == 0:
                    break
                continue
            i += 1
        out.append(([heads[k] for k in sorted(heads)], text[m.start():i]))
        pos = i


def fields(box):
    """Top-level |key = value fields of a template (values may span lines)."""
    body = box[2:-2]
    parts, depth, cur = [], 0, []
    i = 0
    while i < len(body):
        two = body[i:i + 2]
        if two in ('{{', '[['):
            depth += 1; cur.append(two); i += 2; continue
        if two in ('}}', ']]'):
            depth -= 1; cur.append(two); i += 2; continue
        if body[i] == '|' and depth == 0:
            parts.append(''.join(cur)); cur = []; i += 1; continue
        cur.append(body[i]); i += 1
    parts.append(''.join(cur))
    out = {}
    for p in parts[1:]:
        if '=' in p:
            k, v = p.split('=', 1)
            out[k.strip().lower()] = v.strip()
    return out


def parse_date(raw):
    s = re.sub(r'\{\{[^}]*\|(\d{4})\|(\d{1,2})\|(\d{1,2})[^}]*\}\}', r'\3 \2 \1', raw or '')  # {{start date|y|m|d}}
    m = re.search(r'(\d{1,2})\s*([A-Za-z]+)\s*(\d{4})', s)
    if m and m.group(2).lower()[:3] in MONTHS:
        return dt.date(int(m.group(3)), MONTHS[m.group(2).lower()[:3]], int(m.group(1)))
    m = re.search(r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})', s)
    if m and m.group(1).lower()[:3] in MONTHS:
        return dt.date(int(m.group(3)), MONTHS[m.group(1).lower()[:3]], int(m.group(2)))
    m = re.search(r'(\d{1,2})\s+(\d{1,2})\s+(\d{4})', s)
    if m:
        return dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    return None


def parse_kickoff(date, raw):
    """Kick-off in UTC from '19:35 [[UTC+11|AEDT]]'; None if the page gives no time or zone."""
    if date is None:
        return None
    t = re.search(r'(\d{1,2}):(\d{2})', raw or '')
    z = re.search(r'UTC\s*([+−-])\s*(\d{1,2})(?::(\d{2}))?', raw or '')
    if not t or not z:
        return None
    sign = -1 if z.group(1) in '-−' else 1
    off = dt.timedelta(hours=int(z.group(2)), minutes=int(z.group(3) or 0)) * sign
    local = dt.datetime(date.year, date.month, date.day, int(t.group(1)), int(t.group(2)))
    return (local - off).replace(tzinfo=dt.timezone.utc)


def parse_score(raw):
    """(home, away, extra) from '2–1', '1–1 (4–3 p)', '2–1 (a.e.t.)'; None if not played."""
    s = re.sub(r'\{\{[^}]*\}\}|<ref[^>]*/>|<ref.*?</ref>', '', raw or '', flags=re.S)
    m = re.search(r'(\d+)\s*[–−-]\s*(\d+)', s)
    if not m:
        return None
    extra = 'aet' if re.search(r'a\.?e\.?t|extra', s, re.I) else ''
    if re.search(r'\bp\b|pen', s[m.end():], re.I):
        extra = 'pens'
    return int(m.group(1)), int(m.group(2)), extra


def parse_goals(raw):
    """One dict per goal: scorer (link target), minute, stoppage, penalty, own goal."""
    out = []
    for line in re.split(r'\n|<br\s*/?>', raw or ''):
        name = re.search(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]', line)
        if not name:
            plain = re.sub(r'\{\{.*?\}\}|[*\[\]]', '', line).strip()
            if not plain:
                continue
            scorer = plain
        else:
            scorer = name.group(1).strip()
        for g in re.findall(r'\{\{\s*goal\s*\|(.*?)\}\}', line, re.I):
            args = [a.strip() for a in g.split('|')]
            i = 0
            while i < len(args):
                minute = args[i]
                note = args[i + 1].lower() if i + 1 < len(args) else ''
                i += 2
                if not minute:
                    continue
                m = re.match(r'(\d+)(?:\+(\d+))?', minute)
                out.append(dict(scorer=scorer, minute=int(m.group(1)) if m else None,
                                stoppage=int(m.group(2)) if m and m.group(2) else 0,
                                penalty='pen' in note, own_goal='o.g' in note or note == 'og'))
    return out


def parse_page(text, season):
    """League matches on one club season page."""
    out = []
    for heads, box in boxes(text):
        path = ' / '.join(heads)
        if NOT_LEAGUE.search(path) or not LEAGUE.search(path):
            continue
        f = fields(box)
        home, away = club(f.get('team1')), club(f.get('team2'))
        if not home or not away or home == away:
            continue
        date = parse_date(f.get('date'))
        score = parse_score(f.get('score'))
        round_ = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', f.get('round', '')).strip()
        out.append(dict(season=season, date=date, kickoff_utc=parse_kickoff(date, f.get('time')), round=round_,
                        home=home, away=away,
                        home_goals=score[0] if score else None, away_goals=score[1] if score else None,
                        extra=score[2] if score else '', heading=path,
                        venue=re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', f.get('stadium', '')).strip() or None,
                        attendance=int(re.sub(r'\D', '', f['attendance'])) if re.search(r'\d', f.get('attendance', '').split('<')[0]) else None,
                        goals_home=parse_goals(f.get('goals1')), goals_away=parse_goals(f.get('goals2'))))
    return out


def read_dir(path):
    """Merge the two readings of every match across all club pages in a directory.

    The two clubs' pages sometimes date one match a day apart (a Perth night game is the next day in
    Sydney), so readings of the same home and away pair in one season within two days are one match.
    The home club's page decides the date, because it gives the date where the match was played."""
    by_pair = defaultdict(list)
    for fn in sorted(os.listdir(path)):
        m = re.match(r'(\d{4}–\d{2})_(.+)_season\.wiki$', fn)
        if not m:
            continue
        season = m.group(1)
        for r in parse_page(open(os.path.join(path, fn)).read(), season):
            r['page'] = m.group(2)
            by_pair[(season, r['home'], r['away'])].append(r)
    groups = []
    for rs in by_pair.values():
        rs = sorted(rs, key=lambda r: (r['date'] is None, r['date'] or dt.date.min))
        cur = []
        for r in rs:
            if cur and r['date'] and cur[-1]['date'] and (r['date'] - cur[-1]['date']).days <= 2:
                cur.append(r)
            else:
                if cur:
                    groups.append(cur)
                cur = [r]
        if cur:
            groups.append(cur)

    def quality(r):
        ok = r['home_goals'] is not None and len(r['goals_home']) == r['home_goals'] and len(r['goals_away']) == r['away_goals']
        return (r['home_goals'] is not None, ok, r['kickoff_utc'] is not None, len(r['goals_home']) + len(r['goals_away']))

    matches, goals, problems = [], [], []
    for rs in groups:
        played = [r for r in rs if r['home_goals'] is not None]
        scores = {(r['home_goals'], r['away_goals']) for r in played}
        key = (rs[0]['season'], rs[0]['home'], rs[0]['away'], rs[0]['date'])
        if len(scores) > 1:
            problems.append(f'{key}: pages disagree on the score {sorted(scores)}')
        if len(rs) == 1:
            problems.append(f'{key}: on one page only ({rs[0]["page"]})')
        if len(rs) > 2:
            problems.append(f'{key}: read {len(rs)} times')
        best = dict(max(rs, key=quality))
        home_page = [r for r in rs if club(r['page'].replace('_', ' ')) == r['home'] and r['date']]
        if home_page:
            best['date'] = home_page[0]['date']
        if best['kickoff_utc'] is None:
            best['kickoff_utc'] = next((r['kickoff_utc'] for r in rs if r['kickoff_utc'] is not None), None)
        mid = f'{best["date"]}_{best["home"]}_{best["away"]}'.replace(' ', '')
        row = {k: v for k, v in best.items() if k not in ('goals_home', 'goals_away', 'page')}
        row['match_id'] = mid
        row['pages'] = len(rs)
        row['goals_reconcile'] = quality(best)[1]
        matches.append(row)
        for side, team, opp in (('goals_home', best['home'], best['away']), ('goals_away', best['away'], best['home'])):
            for g in best[side]:
                goals.append(dict(match_id=mid, team=team, opponent=opp, **g))
    m = pd.DataFrame(matches).sort_values(['date', 'home']).reset_index(drop=True)
    return m, pd.DataFrame(goals), problems
