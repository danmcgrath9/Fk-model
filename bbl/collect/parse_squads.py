"""Contracted squads from the held Wikipedia pages: one row per player per club per season, with captain and
overseas country where the page marks them.

The season page's "Squads" section is a table: a header row of club names, then one cell per club holding a
bulleted list ("* [[Matthew Short|Matt Short]] (c)", "* [[Hasan Ali (cricketer)|Hassan Ali]] ([[Pakistan
cricket team|PAK]])"). Pages that lay squads out another way are counted as unparsed, never guessed at.
Names are as Wikipedia writes them ("Matt Short"); bbl/live/names.py maps them to Cricsheet's ("MW Short").

Usage: python -m bbl.collect.parse_squads <collect dir> <out csv>
"""
import glob
import json
import os
import re
import sys

import pandas as pd

from bbl.collect.parse_wiki import plain, season_years

CLUBS = ['Adelaide Strikers', 'Brisbane Heat', 'Hobart Hurricanes', 'Melbourne Renegades', 'Melbourne Stars',
         'Perth Scorchers', 'Sydney Sixers', 'Sydney Thunder']


def section(text, name):
    m = re.search(r'^(==+)\s*' + re.escape(name) + r'\s*\1\s*$', text, re.M)
    if not m:
        return None
    level = len(m.group(1))
    nxt = re.search(r'^={2,%d}[^=].*?={2,%d}\s*$' % (level, level), text[m.end():], re.M)
    return text[m.end(): m.end() + nxt.start()] if nxt else text[m.end():]


def player(line):
    name_m = re.match(r'\*+\s*(\[\[[^\]]+\]\]|[^(\[]+)', line)
    if not name_m:
        return None
    name = plain(name_m.group(1)).strip()
    if len(name.split()) > 4:      # a note in the list ("Unless otherwise specified, all players are Australian."), not a player
        return None
    rest = line[name_m.end():]
    country = re.search(r'\(\s*\[\[[^\]|]*\|([A-Z]{2,4})\]\]\s*\)', rest) or re.search(r'\(\s*([A-Z]{2,4})\s*\)', rest)
    return dict(player=name, captain=bool(re.search(r'\(\s*c\s*\)', rest)), overseas=country.group(1) if country else None,
                note=plain(re.sub(r'\(\s*\[\[[^\]]*\]\]\s*\)|\(\s*c\s*\)', '', rest)) or None)


def parse_table(sec):
    """Header club names in order, then each cell's bullets assigned to its club."""
    heads = [plain(h) for h in re.findall(r'^!\s*(?:scope="col"\s*)?(?:style="[^"]*"\s*)?\|?\s*(.+)$', sec, re.M)]
    heads = [next((c for c in CLUBS if c in h), None) for h in heads]
    heads = [h for h in heads if h]
    if len(heads) < 8:
        return []
    body = sec.split('|-', 2)[-1] if sec.count('|-') >= 2 else sec
    cells = re.split(r'^\|(?!-|\})[^\n]*?\|?\s*$', body, flags=re.M)
    cells = [c for c in cells if re.search(r'^\*', c, re.M)]
    rows = []
    for club, cell in zip(heads, cells):
        for line in re.findall(r'^\*.*$', cell, re.M):
            p = player(line)
            if p and p['player']:
                rows.append(dict(club=club, **p))
    return rows


def main(collect_dir, out):
    rows, report = [], []
    for f in sorted(glob.glob(os.path.join(collect_dir, 'wiki', 'pages', '*.json')) + glob.glob(os.path.join(collect_dir, 'squads', '*.json'))):
        page = json.load(open(f))
        if page.get('missing'):
            continue
        title = page['title']
        text = page['revisions'][0]['slots']['main']['content']
        sec = text if title.endswith('squads') else section(text, 'Squads')
        got = parse_table(sec) if sec else []
        y = season_years(title)
        comp = 'WBBL' if "Women's" in title else 'BBL'
        rows += [dict(r, season=f'{y[0]}/{y[1] % 100:02d}', comp=comp, source_title=title,
                      source_revid=page['revisions'][0].get('revid')) for r in got]
        report.append(dict(page=title, players=len(got), clubs=len({r['club'] for r in got})))
    df = pd.DataFrame(rows).drop_duplicates(['season', 'comp', 'club', 'player'])
    df.to_csv(out, index=False)
    rep = pd.DataFrame(report)
    print(f'{len(df)} player-club-seasons from {int((rep.players > 0).sum())} of {len(rep)} pages')
    print(rep.to_string(index=False))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
