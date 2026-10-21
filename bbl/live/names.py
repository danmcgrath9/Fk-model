"""Match a name as a bookmaker or a team sheet writes it ("Steve Smith") to a Cricsheet player ("SPD Smith").

Only within a pool (the players a side has used recently), and never a guess: a name that fits two
players, or none, comes back unmatched with the reason, to be fixed by hand in bbl/live/name_overrides.csv.
"""
import os
import re
import unicodedata

import pandas as pd

OVERRIDES = os.path.join(os.path.dirname(__file__), 'name_overrides.csv')


def _norm(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode()
    return re.sub(r'\s+', ' ', re.sub(r"[^A-Za-z' -]", ' ', s)).strip()


def split_cricsheet(name):
    """Cricsheet writes initials then surname: 'SPD Smith' -> ('spd', 'smith'); 'Rashid Khan' has no initials."""
    toks = _norm(name).split(' ')
    if len(toks) > 1 and toks[0].isupper() and len(toks[0]) <= 4:
        return toks[0].lower(), ' '.join(toks[1:]).lower()
    return '', ' '.join(toks).lower()


def split_display(name):
    toks = _norm(name).split(' ')
    return (toks[0][:1].lower() if len(toks) > 1 else ''), ' '.join(toks[1:]).lower() if len(toks) > 1 else toks[0].lower()


def overrides():
    if os.path.exists(OVERRIDES):
        o = pd.read_csv(OVERRIDES, dtype=str)
        return {(r.team, _norm(r.display_name).lower()): r.cricsheet_name for r in o.itertuples()}
    return {}


def match(display, pool, team=None, manual=None):
    """display: a name; pool: Cricsheet names to choose from. Returns (cricsheet name or None, how)."""
    manual = overrides() if manual is None else manual
    key = (team, _norm(display).lower())
    if key in manual:
        return manual[key], 'override'
    pool = list(dict.fromkeys(pool))
    exact = [p for p in pool if _norm(p).lower() == _norm(display).lower()]
    if len(exact) == 1:
        return exact[0], 'exact'
    ini, sur = split_display(display)
    parts = {p: split_cricsheet(p) for p in pool}
    same_sur = [p for p, (pi, ps) in parts.items() if ps == sur or ps.endswith(' ' + sur)]
    if ini:
        both = [p for p in same_sur if parts[p][0][:1] == ini or (not parts[p][0] and _norm(p).lower().startswith(ini))]
        if len(both) == 1:
            return both[0], 'initial+surname'
        if len(both) > 1:
            return None, 'ambiguous: ' + ', '.join(both)
    if len(same_sur) == 1:
        return same_sur[0], 'surname only'
    if len(same_sur) > 1:
        return None, 'ambiguous: ' + ', '.join(same_sur)
    return None, 'no player of that name in the pool'
