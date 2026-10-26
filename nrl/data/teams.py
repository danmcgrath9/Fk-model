"""One name per club. RLP records each game under the name the club used THAT season (Bulldogs 2000-2009,
Sharks 2000-2002, New Zealand Warriors 2001, Warriors from 2002, ...); RLP's own team table maps every variant
to a unique name. Without this, every rename restarted a club's ratings at average (found 26 Oct 2026: the
Warriors' 2002 restart under-rated them by about 10 points a game for two months).

canonical(cache) returns a function mapping any RLP, Champion Data or NRL.com team name to RLP's unique name.
Genuinely new clubs (mergers like St George Illawarra 1999 and Wests Tigers 2000, Northern Eagles, Titans,
Dolphins, Perth Bears) keep their own name and start fresh.
"""
import re
import unicodedata

import pandas as pd


def _key(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().lower().replace('-', ' ')
    return re.sub(r'[^a-z ]', '', re.sub(r'\s+', ' ', s)).strip()


def canonical(cache):
    t = pd.read_parquet(f'{cache}/teams.parquet')
    m = {}
    for name, uniq in zip(t.team_name, t.team_unique):
        m[_key(name)] = uniq
        m[_key(uniq)] = uniq
    m.setdefault(_key('Warriors'), 'New Zealand Warriors')
    m[_key('The Dolphins')] = 'Dolphins'

    def f(name):
        if name is None or (isinstance(name, float) and pd.isna(name)):
            return name
        return m.get(_key(name), name)
    return f
