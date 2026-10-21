"""Build the A-League Men match and goal tables from the raw sources (aleague-history release).

Sources and which one is trusted for what:
  scores to May 2025   FBref, through worldfootballR's GitHub copy (AUS_match_results.rds)
  scores from 2025-26  Wikipedia club season pages (no free FBref copy past May 2025)
  kick-off times, scorers and goal minutes, every season: Wikipedia, attached to a match only when
    Wikipedia's score for it equals the trusted score, so a page with a typo cannot plant goals
Where both sources hold a season, the build counts how often Wikipedia's score disagrees with FBref,
which is the error rate to expect in the seasons only Wikipedia holds.

Writes:
  <out>/matches.parquet  one row per league match (regular season and finals), played or scheduled
  <out>/goals.parquet    one row per goal with scorer, minute, penalty, own goal
  <out>/BUILD.md         counts per season and the cross-check

Usage: python -m aleague.data.build <raw dir> <out dir>
"""
import datetime as dt
import os
import sys

import pandas as pd

from aleague.data.wiki_parse import read_dir

FBREF_NAMES = {'Adelaide': 'Adelaide United', 'Auckland FC': 'Auckland FC', 'Brisbane': 'Brisbane Roar',
               'Central Coast': 'Central Coast Mariners', 'Macarthur FC': 'Macarthur FC', 'Melb City': 'Melbourne City',
               'Melb Heart': 'Melbourne City', 'Melb Victory': 'Melbourne Victory', 'Newcastle': 'Newcastle Jets',
               'Perth Glory': 'Perth Glory', 'Sydney FC': 'Sydney FC', 'W Sydney': 'Western Sydney Wanderers',
               'Wellington': 'Wellington Phoenix', 'Western United': 'Western United'}
FIRST_SEASON = 2014          # 2013-14, the first season both sources hold
WIKI_ONLY_FROM = 2026        # 2025-26 onwards: no FBref copy


def season_end(label):
    """'2025–26' -> 2026."""
    return int(label[:4]) + 1


def load_fbref(path):
    import pyreadr
    df = pyreadr.read_r(path)[None]
    df = df[(df.Gender == 'M') & (df.Season_End_Year >= FIRST_SEASON)].copy()
    out = pd.DataFrame({
        'season': df.Season_End_Year.astype(int),
        'date': pd.to_datetime(df.Date).dt.date,
        'home': df.Home.map(FBREF_NAMES), 'away': df.Away.map(FBREF_NAMES),
        'home_goals': df.HomeGoals, 'away_goals': df.AwayGoals,
        'stage': df.Round.fillna('Regular season').where(df.Round.notna(), 'Regular season'),
        'venue': df.Venue.fillna('').str.replace(' (Neutral Site)', '', regex=False),
        'fbref_neutral': df.Venue.fillna('').str.contains('Neutral Site'),
        'attendance': df.Attendance,
        'notes': df.Notes.fillna(''),
    })
    if out.home.isna().any() or out.away.isna().any():
        raise ValueError(f'unmapped FBref team names: {set(df.Home[out.home.isna()]) | set(df.Away[out.away.isna()])}')
    return out.reset_index(drop=True)


def match_up(trusted, wiki):
    """Index of the Wikipedia reading for each trusted match: same home and away, dates within two days."""
    w = wiki.reset_index(drop=True)
    by_pair = {}
    for i, r in w.iterrows():
        by_pair.setdefault((r.home, r.away), []).append((r.date, i))
    idx = []
    for _, r in trusted.iterrows():
        best = None
        for d, i in by_pair.get((r.home, r.away), []):
            gap = abs((d - r.date).days) if d else 99
            if gap <= 2 and (best is None or gap < best[0]):
                best = (gap, i)
        idx.append(best[1] if best else None)
    return idx


def goals_at_90(goals, mid, team):
    g = goals[(goals.match_id == mid) & (goals.team == team)]
    return int((g.minute.fillna(0) <= 90).sum())


def flag_neutral(m):
    """A home side at a ground it used fewer than twice as home that season is at a neutral ground
    (the 2020 Sydney hub, Unite Round, finals moved for a clash), unless FBref says otherwise."""
    use = m[m.venue.fillna('') != ''].groupby(['season', 'home', 'venue']).size()
    home_grounds = use[use >= 2].reset_index()[['season', 'home', 'venue']]
    home_grounds['usual'] = True
    m = m.merge(home_grounds, on=['season', 'home', 'venue'], how='left')
    m['neutral'] = m.fbref_neutral.fillna(False).astype(bool) | (m.usual.isna() & (m.venue.fillna('') != ''))
    return m.drop(columns=['usual'])


def build(raw, out):
    os.makedirs(out, exist_ok=True)
    wm, wg, problems = read_dir(os.path.join(raw, 'wiki'))
    undated = wm[wm.date.isna()]
    for _, r in undated.iterrows():
        problems.append(f"('{r.season}', '{r.home}', '{r.away}'): no date on the page, left out")
    wm = wm[wm.date.notna()].reset_index(drop=True)
    wm['season'] = wm.season.map(season_end)
    fb = load_fbref(os.path.join(raw, 'AUS_match_results.rds'))

    # cross-check: every FBref match against its Wikipedia reading
    fb_wiki = wm[wm.season < WIKI_ONLY_FROM]
    idx = match_up(fb, fb_wiki)
    found = [i is not None for i in idx]
    agree = [i is not None and fb_wiki.iloc[i].home_goals == r.home_goals and fb_wiki.iloc[i].away_goals == r.away_goals
             for i, (_, r) in zip(idx, fb.iterrows())]
    fb['wiki_idx'] = idx
    fb['wiki_found'] = found
    fb['wiki_score_agrees'] = agree
    fb['source'] = 'fbref'

    wiki_only = wm[wm.season >= WIKI_ONLY_FROM].copy()
    wiki_only['stage'] = wiki_only.apply(lambda r: 'Finals' if 'final' in f'{r.heading} {r["round"]}'.lower() else 'Regular season', axis=1)
    wiki_only['fbref_neutral'] = False
    wiki_only['notes'] = ''
    wiki_only['source'] = 'wikipedia'

    # one table; Wikipedia supplies kick-off, venue and goals where its score agrees
    rows = []
    for _, r in fb.iterrows():
        w = fb_wiki.iloc[int(r.wiki_idx)] if r.wiki_found else None
        rows.append(dict(season=r.season, date=r.date, home=r.home, away=r.away, home_goals=r.home_goals,
                         away_goals=r.away_goals, stage=r.stage, venue=r.venue or (w.venue if w is not None else None),
                         fbref_neutral=r.fbref_neutral, attendance=r.attendance, notes=r.notes, source='fbref',
                         kickoff_utc=w.kickoff_utc if w is not None else None,
                         wiki_match_id=w.match_id if (w is not None and r.wiki_score_agrees) else None,
                         goals_reconcile=bool(w.goals_reconcile) if (w is not None and r.wiki_score_agrees) else False))
    for _, w in wiki_only.iterrows():
        rows.append(dict(season=w.season, date=w.date, home=w.home, away=w.away, home_goals=w.home_goals,
                         away_goals=w.away_goals, stage=w.stage, venue=w.venue, fbref_neutral=False,
                         attendance=w.attendance, notes='', source='wikipedia', kickoff_utc=w.kickoff_utc,
                         wiki_match_id=w.match_id, goals_reconcile=bool(w.goals_reconcile)))
    m = pd.DataFrame(rows)
    m['match_id'] = m.apply(lambda r: f'{r.date}_{r.home}_{r.away}'.replace(' ', ''), axis=1)
    m['stage'] = m.stage.where(m.stage == 'Regular season', 'Finals')
    m['extra_time'] = m.notes.str.contains('extra time|penalt', case=False) | m.wiki_match_id.map(
        dict(zip(wm.match_id, wm.extra))).fillna('').isin(['aet', 'pens'])
    # bets settle on 90 minutes: an extra-time match counts only if its goals can be cut at 90
    m['home_goals_90'] = m.home_goals.astype('Float64')
    m['away_goals_90'] = m.away_goals.astype('Float64')
    for i, r in m[m.extra_time].iterrows():
        if r.goals_reconcile and r.wiki_match_id:
            m.at[i, 'home_goals_90'] = goals_at_90(wg, r.wiki_match_id, r.home)
            m.at[i, 'away_goals_90'] = goals_at_90(wg, r.wiki_match_id, r.away)
        else:
            m.at[i, 'home_goals_90'] = pd.NA
            m.at[i, 'away_goals_90'] = pd.NA
    m['played'] = m.home_goals.notna()
    m = flag_neutral(m)
    m = m.sort_values(['date', 'home']).reset_index(drop=True)
    dup = m.match_id.duplicated(keep=False)
    if dup.any():
        raise ValueError(f'duplicate match ids: {m.match_id[dup].tolist()[:5]}')

    # goals only for matches whose Wikipedia goal list adds up to the trusted score
    keep = m[m.goals_reconcile & m.wiki_match_id.notna()][['match_id', 'wiki_match_id', 'season']]
    g = wg.merge(keep, left_on='match_id', right_on='wiki_match_id', suffixes=('_wiki', ''))
    g = g.drop(columns=['match_id_wiki', 'wiki_match_id'])

    m.to_parquet(os.path.join(out, 'matches.parquet'), index=False)
    g.to_parquet(os.path.join(out, 'goals.parquet'), index=False)

    played = m[m.played]
    lines = ['# A-League Men tables: what was built', '',
             f'{len(m):,} matches ({len(played):,} played), {len(g):,} goals with scorer and minute.', '',
             '| season | source | played | finals | to play | neutral | kick-off known | goals attached |',
             '|---|---|---|---|---|---|---|---|']
    for s, x in m.groupby('season'):
        p = x[x.played]
        lines.append(f'| {s - 1}-{str(s)[2:]} | {x.source.iloc[0]} | {len(p)} | {(p.stage == "Finals").sum()} | '
                     f'{(~x.played).sum()} | {x.neutral.sum()} | {x.kickoff_utc.notna().sum()} | '
                     f'{p.goals_reconcile.sum()} |')
    n = len(fb[fb.home_goals.notna()])
    lines += ['', '## Wikipedia against FBref, 2013-14 to 2024-25', '',
              f'Of {n:,} FBref matches, Wikipedia holds {sum(found):,} ({sum(found) / n:.1%}); '
              f'the score agrees on {sum(agree):,} ({sum(agree) / n:.1%}).', '']
    bad = fb[fb.wiki_found & ~fb.wiki_score_agrees]
    if len(bad):
        lines += ['Disagreements:', '', '| date | home | away | FBref | Wikipedia |', '|---|---|---|---|---|']
        for _, r in bad.iterrows():
            w = fb_wiki.iloc[int(r.wiki_idx)]
            lines.append(f'| {r.date} | {r.home} | {r.away} | {r.home_goals:.0f}-{r.away_goals:.0f} | '
                         f'{w.home_goals}-{w.away_goals} |')
    missing = fb[~fb.wiki_found]
    if len(missing):
        lines += ['', f'FBref matches Wikipedia does not hold: {len(missing)} '
                  f'({", ".join(f"{r.date} {r.home} v {r.away}" for _, r in missing.head(8).iterrows())}'
                  f'{" ..." if len(missing) > 8 else ""})']
    wiki_probs = [p for p in problems if str(WIKI_ONLY_FROM - 1) in p.split(',')[0] or str(WIKI_ONLY_FROM) in p.split(',')[0]]
    lines += ['', f'## Wikipedia problems in the seasons it alone holds ({len(wiki_probs)})', ''] + [f'- {p}' for p in wiki_probs]
    text = '\n'.join(lines) + '\n'
    open(os.path.join(out, 'BUILD.md'), 'w').write(text)
    print(text)
    return m, g


if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])
