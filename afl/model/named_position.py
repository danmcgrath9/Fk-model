"""The position a player is named in on the team sheet (Thursday night), from Fryzigg's per-game records.

A team sheet names a centre square (C, R, RR = centre, rover, ruck-rover), a ruck (RK), wings, the back and forward
lines, the interchange (INT) and, since 2021, the substitute. Starting in the centre square is the public, pre-game
signal closest to centre bounce attendance, which the research (docs/RESEARCH_BEST_MODEL.md, rank 4) puts near the top
for disposals. Fryzigg holds 2012-2025; 2026 is not published, so this is tested on 2024-2025 with 2023 for tuning.
For live use the positions come from the pasted team sheet (afl/live/team_sheet.py names the same groups).
Kept for disposals, tackles and goals (docs/RESEARCH_TESTS.md); not for marks.
"""
import glob

import numpy as np
import pandas as pd

from afl.model.frame import _key
from afl.model.strength import FRYZIGG_TEAM

GROUPS = {'C': 'centre', 'R': 'centre', 'RR': 'centre', 'RK': 'ruck', 'WL': 'wing', 'WR': 'wing',
          'HBFL': 'halfback', 'HBFR': 'halfback', 'CHB': 'halfback', 'BPL': 'back', 'BPR': 'back', 'FB': 'back',
          'HFFL': 'halfforward', 'HFFR': 'halfforward', 'CHF': 'halfforward', 'FPL': 'forward', 'FPR': 'forward',
          'FF': 'forward', 'INT': 'bench', 'SUB': 'sub'}
NAMES = sorted(set(GROUPS.values()))


def attach(m, cache):
    fz = pd.concat([pd.read_parquet(f, columns=['match_date', 'player_team', 'player_first_name', 'player_last_name',
                                                'player_position']) for f in sorted(glob.glob(f'{cache}/fryzigg_*.parquet'))])
    fz['date'] = pd.to_datetime(fz.match_date).dt.strftime('%Y-%m-%d')
    fz['team'] = fz.player_team.replace(FRYZIGG_TEAM)
    fz['key'] = (fz.player_first_name.fillna('') + ' ' + fz.player_last_name.fillna('')).map(_key)
    fz = fz.drop_duplicates(['date', 'team', 'key'], keep=False)
    fz['named_pos'] = fz.player_position.map(GROUPS)
    m = m.assign(key=m.Player.map(_key)).merge(fz[['date', 'team', 'key', 'named_pos']].rename(columns={'named_pos': 'fz_pos'}),
                                               on=['date', 'team', 'key'], how='left')
    # rows that already carry a position (a pasted team sheet, afl/live/team_sheet.py) keep it
    m['named_pos'] = m['named_pos'].combine_first(m.fz_pos) if 'named_pos' in m else m.fz_pos
    m = m.drop(columns=['fz_pos'])
    for g in NAMES:
        m[f'sheet_{g}'] = (m.named_pos == g).astype(float).where(m.named_pos.notna())
    # how often he has been named in the centre square lately (shifted: earlier games only)
    m = m.sort_values(['player_id', 'dt'])
    m['centre_rate10'] = m.groupby('player_id').sheet_centre.transform(lambda x: x.shift(1).rolling(10, min_periods=1).mean())
    m['bench_rate10'] = m.groupby('player_id').sheet_bench.transform(lambda x: x.shift(1).rolling(10, min_periods=1).mean())
    return m.drop(columns=['key'])


def columns():
    return [f'sheet_{g}' for g in NAMES] + ['centre_rate10', 'bench_rate10']
