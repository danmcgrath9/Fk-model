"""What the Cricsheet pull actually holds, as a markdown report (printed and written to INVENTORY.md).

Facts only, each counted from the parquet tables cricsheet.py wrote: seasons, matches, rows,
columns and gaps for BBL and WBBL, then every other T20 competition (the player-history pool),
then the rules-related fields (powerplay types, substitution reasons, XI sizes) that the BBL
model will need to read correctly.

Usage: python bbl/data/inventory.py <parquet dir>
"""
import os
import sys

import pandas as pd

BBL = 'Big Bash League'
WBBL = "Women's Big Bash League"


def md_table(df):
    cols = list(df.columns)
    lines = ['| ' + ' | '.join(map(str, cols)) + ' |', '|' + '---|' * len(cols)]
    for row in df.itertuples(index=False):
        lines.append('| ' + ' | '.join('' if pd.isna(v) else str(v) for v in row) + ' |')
    return '\n'.join(lines)


def season_table(m, inn, comp):
    g = m[m.competition == comp]
    if g.empty:
        return f'No matches named `{comp}` in the file.'
    reg = inn[~inn.super_over.astype(bool)].merge(g[['match_id', 'season']], on='match_id')
    first = reg[reg.innings == 1].groupby('season').runs.mean().round(1).rename('avg 1st-innings runs')
    t = g.groupby('season').agg(matches=('match_id', 'size'), first=('start_date', 'min'), last=('start_date', 'max'),
                                no_result=('result', lambda s: int((s == 'no result').sum())),
                                tie=('result', lambda s: int((s == 'tie').sum())),
                                rain_rule=('method', lambda s: int(s.notna().sum())),
                                super_over=('has_super_over', 'sum'),
                                no_toss=('toss_winner', lambda s: int(s.isna().sum())),
                                venues=('venue', 'nunique'), teams=('team1', 'nunique'))
    t = t.join(first).reset_index()
    return md_table(t)


def main(d):
    m = pd.read_parquet(os.path.join(d, 't20_matches.parquet'))
    inn = pd.read_parquet(os.path.join(d, 't20_innings.parquet'))
    pl = pd.read_parquet(os.path.join(d, 't20_players.parquet'))
    dl = pd.read_parquet(os.path.join(d, 't20_deliveries.parquet'))
    pp = pd.read_parquet(os.path.join(d, 't20_powerplays.parquet'))
    rp = pd.read_parquet(os.path.join(d, 't20_replacements.parquet'))
    mt = pd.read_parquet(os.path.join(d, 'match_types.parquet'))
    people = os.path.join(d, 'people.parquet')

    r = ['# Cricsheet pull: what came back', '']
    r += [f'T20 matches parsed: **{len(m):,}** ({m.start_date.min()} to {m.start_date.max()}); '
          f'balls: **{len(dl):,}**; player-match rows: **{len(pl):,}**; innings: {len(inn):,}.', '']
    r += ['## Everything in the zip, by match type (only T20 and IT20 are parsed)', '', md_table(mt), '']

    for comp in (BBL, WBBL):
        r += [f'## {comp}, by season', '', season_table(m, inn, comp), '']
        g = m[m.competition == comp]
        if not g.empty:
            ids = set(g.match_id)
            xi = pd.concat([g.n_players_team1, g.n_players_team2]).value_counts().sort_index()
            r += [f'Players listed per team: ' + ', '.join(f'{k} ({v} team-games)' for k, v in xi.items()), '']
            ppg = pp[pp.match_id.isin(ids)].merge(g[['match_id', 'season']], on='match_id')
            if not ppg.empty:
                r += ['Powerplay types recorded, by season:', '',
                      md_table(ppg.groupby(['season', 'pp_type']).size().rename('innings').reset_index()), '']
            else:
                r += ['No powerplay records for this competition.', '']
            rpg = rp[rp.match_id.isin(ids)].merge(g[['match_id', 'season']], on='match_id')
            if not rpg.empty:
                r += ['Substitutions recorded, by season and reason:', '',
                      md_table(rpg.groupby(['season', 'kind', 'reason'], dropna=False).size().rename('rows').reset_index()), '']
            else:
                r += ['No substitutions recorded for this competition.', '']
            unk = pl[pl.match_id.isin(ids) & pl.player_id.isna()]
            r += [f'Player-match rows without a Cricsheet registry id: {len(unk):,} of {int(pl.match_id.isin(ids).sum()):,}.', '']
            r += ['Venues (matches):', '', md_table(g.venue.value_counts().rename_axis('venue').rename('matches').reset_index()), '']

    others = (m[~m.competition.isin([BBL, WBBL])]
              .assign(year=lambda x: x.start_date.str[:4])
              .groupby(['competition', 'gender'], dropna=False)
              .agg(matches=('match_id', 'size'), first=('start_date', 'min'), last=('start_date', 'max'))
              .reset_index().sort_values('matches', ascending=False))
    r += ['## The rest of the T20 pool (player history), by competition', '', md_table(others), '']

    bbl_ids = set(m.loc[m.competition.isin([BBL, WBBL]), 'match_id'])
    pool_ids = pl[pl.match_id.isin(bbl_ids)].player_id.dropna().unique()
    elsewhere = pl[pl.player_id.isin(pool_ids) & ~pl.match_id.isin(bbl_ids)]
    r += [f'Players who have appeared in BBL or WBBL: {len(pool_ids):,}; their T20 games outside BBL/WBBL in the file: '
          f'{elsewhere.match_id.nunique():,} matches, {len(elsewhere):,} player-match rows.', '']

    if os.path.exists(people):
        pe = pd.read_parquet(people)
        r += [f'People register: {len(pe):,} people; columns: {", ".join(pe.columns)}. '
              f'Rows with a Cricinfo key: {int(pe["key_cricinfo"].notna().sum()) if "key_cricinfo" in pe else "n/a"}.', '']

    r += ['## Columns, per table', '']
    for name in sorted(f for f in os.listdir(d) if f.endswith('.parquet')):
        cols = pd.read_parquet(os.path.join(d, name)).columns
        r.append(f'- `{name}`: {", ".join(cols)}')
    r.append('')

    text = '\n'.join(r)
    open(os.path.join(d, 'INVENTORY.md'), 'w').write(text)
    print(text)


if __name__ == '__main__':
    main(sys.argv[1])
