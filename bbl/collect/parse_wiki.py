"""Turn the held Wikipedia season pages into one row per match: date, local start time, day/night, home
side, venue, attendance, toss, result, rain note, and the ESPNcricinfo match id (Cricsheet's file name,
so the join to the ball-by-ball data is exact).

Matches are the {{Single-innings cricket match}} and older {{Limited overs matches}} templates. Older
pages leave the year off the date ("20 December"): it is the season's first year for July-December and
its second for January-June. Nothing is invented: a field the page leaves blank stays blank.

Usage: python -m bbl.collect.parse_wiki <wiki dir> <out csv>
"""
import glob
import json
import os
import re
import sys

import pandas as pd

TEMPLATES = ('Single-innings cricket match', 'Limited overs matches')


def blocks(text):
    """Every match template in the page, as its inner text (nested {{ }} kept)."""
    out, i = [], 0
    while True:
        starts = [(text.find('{{' + t, i), t) for t in TEMPLATES]
        starts = [(s, t) for s, t in starts if s >= 0]
        if not starts:
            return out
        s, t = min(starts)
        depth, j = 0, s
        while j < len(text):
            if text.startswith('{{', j):
                depth += 1
                j += 2
            elif text.startswith('}}', j):
                depth -= 1
                j += 2
                if depth == 0:
                    break
            else:
                j += 1
        out.append(text[s + 2 + len(t):j - 2])
        i = j


def params(inner):
    """Top-level | key = value pairs (pipes inside [[links]] and {{templates}} are not separators)."""
    parts, depth, cur, k = [], 0, [], 0
    while k < len(inner):
        two = inner[k:k + 2]
        if two in ('[[', '{{'):
            depth += 1
            cur.append(two)
            k += 2
            continue
        if two in (']]', '}}'):
            depth -= 1
            cur.append(two)
            k += 2
            continue
        if inner[k] == '|' and depth == 0:
            parts.append(''.join(cur))
            cur = []
        else:
            cur.append(inner[k])
        k += 1
    parts.append(''.join(cur))
    out = {}
    for p in parts:
        if '=' in p:
            key, val = p.split('=', 1)
            out[key.strip().lower()] = val.strip()
    return out


def plain(s):
    """Wiki markup to text: [[a|b]] -> b, [[a]] -> a, templates, refs and tags dropped."""
    s = re.sub(r'<ref[^>]*/>', '', s or '')
    s = re.sub(r'<ref[^>]*>.*?</ref>', '', s, flags=re.S)
    s = re.sub(r'\{\{[^{}]*\}\}', '', s)
    s = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]', r'\1', s)
    s = re.sub(r"<[^>]+>|'''|''", ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def team(s):
    home = '(H)' in (s or '')
    name = re.sub(r'\s*\(H\)\s*', ' ', plain(s)).replace('(WBBL)', '').strip()
    return name, home


def season_years(title):
    m = re.match(r'(\d{4})–(\d{2})', title)
    return int(m.group(1)), int(m.group(1)) + 1


def parse_date(raw, years):
    txt = plain(raw)
    m = re.search(r'(\d{1,2})\s+([A-Z][a-z]+)(?:\s+(\d{4}))?', txt)
    if not m:
        return None
    day, month, year = m.group(1), m.group(2), m.group(3)
    if not year:
        mo = pd.Timestamp(f'1 {month} 2000').month
        year = years[0] if mo >= 7 else years[1]
    return pd.Timestamp(f'{day} {month} {year}').strftime('%Y-%m-%d')


def parse_page(path):
    page = json.load(open(path))
    if page.get('missing'):
        return []
    title = page['title']
    rev = page['revisions'][0]
    text = rev['slots']['main']['content']
    years = season_years(title)
    comp = "Women's Big Bash League" if title.startswith(f'{years[0]}') and "Women's" in title else 'Big Bash League'
    rows = []
    for inner in blocks(text):
        p = params(inner)
        t1, h1 = team(p.get('team1'))
        t2, h2 = team(p.get('team2'))
        venue_raw = p.get('venue', '')
        att = re.search(r'Attendance:\s*([\d,]+)', venue_raw)
        rep = p.get('report', '')
        # link styles over the years: /engine/match/654031.html, /series/8044/scorecard/1114856/..., /...-1234567/full-scorecard
        cid = (re.search(r'/match/(\d+)', rep) or re.search(r'/(?:scorecard|game)/(\d+)', rep)
               or re.search(r'cricinfo\.com/\S*?-(\d{6,8})(?:/|\s|\])', rep))
        night = any(p.get(k, '').strip().lower() in ('y', 'yes') for k in ('daynight', 'night'))
        rnd = plain(p.get('round', '')) or plain(re.sub(r'\{\{anchor\|[^}]*\}\}', '', p.get('date', '')).split('\n')[0])
        rows.append(dict(
            source_title=title, source_revid=rev.get('revid'), competition=comp, season=f'{years[0]}/{years[1] % 100:02d}',
            date=parse_date(re.sub(r'\{\{anchor\|[^}]*\}\}', '', p.get('date', '')), years), local_time=plain(p.get('time')) or None,
            night=night, team1=t1, team2=t2, home_team=t1 if h1 else (t2 if h2 else None),
            venue=plain(re.split(r'<br\s*/?>', venue_raw)[0]).split(',')[0].strip() or None,
            venue_full=plain(re.split(r'<br\s*/?>', venue_raw)[0]) or None,
            attendance=int(att.group(1).replace(',', '')) if att else None, toss=plain(p.get('toss')) or None,
            result=plain(p.get('result')) or None, rain=plain(p.get('rain')) or None, round=rnd or None,
            cricinfo_id=cid.group(1) if cid else None))
    return rows


def main(wiki_dir, out):
    rows = [r for f in sorted(glob.glob(os.path.join(wiki_dir, 'pages', '*.json'))) for r in parse_page(f)]
    df = pd.DataFrame(rows)
    df.to_csv(out, index=False)
    print(f'{len(df)} matches from {df.source_title.nunique()} pages')
    print(df.groupby(['competition', 'season']).agg(matches=('date', 'size'), with_time=('local_time', lambda s: s.notna().sum()),
                                                     with_home=('home_team', lambda s: s.notna().sum()),
                                                     with_cricinfo_id=('cricinfo_id', lambda s: s.notna().sum()),
                                                     night=('night', 'sum')).to_string())


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
