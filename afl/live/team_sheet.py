"""Read named teams from pasted team-sheet text into the CSV afl/live/price_round.py takes.

Any source's team sheet can be pasted in the newspaper layout clubs and media use, one game per block:

    Game: Adelaide v Fremantle, Adelaide Oval, 2027-03-20, round 2
    Adelaide
    B: Name, Name, Name
    HB: Name, Name, Name
    C: Name, Name, Name
    HF: Name, Name, Name
    F: Name, Name, Name
    FOL: Name, Name, Name
    I/C: Name, Name, Name, Name
    EMG: Name, Name          (emergencies: not playing, ignored)
    Fremantle
    B: ...

There is no substitute from 2026, so a side is 22 (18 on the ground, four on the bench); a SUB: line is still read for
older sheets. Lines can also be labelled INT, INTERCHANGE, FOLL, FOLLOWERS, R (ruck line) or EMERG; labels are not case sensitive and
a missing line is fine. IN:/OUT: lines are ignored. The position each player is named in is kept (named_pos) because
starting in the centre square is a role signal (afl/model/named_position.py).

Usage: python -m afl.live.team_sheet pasted.txt > named.csv   (the season is each game's year)
"""
import re
import sys

import pandas as pd

LINES = {'B': 'back', 'FB': 'back', 'HB': 'halfback', 'HBF': 'halfback', 'C': 'centre_line', 'HF': 'halfforward',
         'HFF': 'halfforward', 'F': 'forward', 'FF': 'forward', 'FOL': 'followers', 'FOLL': 'followers',
         'FOLLOWERS': 'followers', 'R': 'followers', 'I/C': 'bench', 'IC': 'bench', 'INT': 'bench',
         'INTERCHANGE': 'bench', 'SUB': 'sub', 'SUBSTITUTE': 'sub', 'EMG': None, 'EMERG': None, 'EMERGENCIES': None,
         'IN': None, 'OUT': None, 'INS': None, 'OUTS': None}
GAME = re.compile(r'^\s*game\s*:\s*(?P<home>.+?)\s+v(?:s\.?)?\s+(?P<away>.+?)\s*,\s*(?P<venue>.+?)\s*,\s*(?P<date>\d{4}-\d{2}-\d{2})'
                  r'\s*,\s*round\s+(?P<round>\w+)\s*$', re.I)
LABEL = re.compile(r'^\s*(?P<label>[A-Za-z/]+)\s*:\s*(?P<names>.*)$')


def named_pos(line, i):
    """The position group for the i-th name on a line: on the centre line the middle name is the centre and the outer
    two the wings; among the followers the first is the ruck and the others the rover and ruck-rover (centre square)."""
    if line == 'centre_line':
        return 'centre' if i == 1 else 'wing'
    if line == 'followers':
        return 'ruck' if i == 0 else 'centre'
    return line


def parse(text, season=None):
    """season: taken from each game's date unless given."""
    rows, game, team, errors = [], None, None, []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        g = GAME.match(line)
        if g:
            game, team = g.groupdict(), None
            continue
        lab = LABEL.match(line)
        if lab and lab.group('label').upper() in LINES:
            if game is None or team is None:
                errors.append(f'line {n}: "{line[:40]}" comes before a Game: line and a team name')
                continue
            kind = LINES[lab.group('label').upper()]
            if kind is None:
                continue
            names = [x.strip() for x in re.split(r',|;', lab.group('names')) if x.strip()]
            for i, name in enumerate(names):
                rows.append(dict(season=season or int(game['date'][:4]), round=game['round'], date=game['date'], venue=game['venue'],
                                 home_team=game['home'], away_team=game['away'], team=team, player=name,
                                 sub=1 if kind == 'sub' else '', named_pos=named_pos(kind, i)))
            continue
        if game is None:
            errors.append(f'line {n}: "{line[:40]}" is not a Game: line')
            continue
        team = line                    # a line on its own, with no label: the team the next lines belong to
    if errors:
        raise ValueError('team sheet not understood:\n' + '\n'.join(errors))
    df = pd.DataFrame(rows)
    # once a sub is named everyone else is known not to be the sub
    if len(df):
        has_sub = df.groupby(['date', 'team']).sub.transform(lambda s: (s == 1).any())
        df.loc[has_sub & (df['sub'] != 1), 'sub'] = 0
    return df


def check(df):
    """Problems a person should look at before pricing: a side without 22-23 players, a team not in its game."""
    out = []
    for (date, team), g in df.groupby(['date', 'team']):
        if not 22 <= len(g) <= 23:
            out.append(f'{team} on {date}: {len(g)} players named (expected 22; 23 only in a season with a substitute)')
        if not ((g.team == g.home_team) | (g.team == g.away_team)).all():
            out.append(f'{team} on {date} is not one of the two sides in its Game: line')
    return out


if __name__ == '__main__':
    text = open(sys.argv[1]).read()
    df = parse(text, int(sys.argv[2]) if len(sys.argv) > 2 else None)
    for p in check(df):
        print('CHECK:', p, file=sys.stderr)
    df.to_csv(sys.stdout, index=False)
