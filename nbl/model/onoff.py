"""Who was on court, and what the score did while they were: stints from the play-by-play, and player
ratings from them (regularised adjusted plus/minus).

A stint is a stretch of one game with no substitution. For each one: the five on court for each side,
its length in minutes and the points each side scored. A player's rating is his effect on his team's
margin per 40 minutes on court, holding the other nine players fixed, shrunk toward a prior from his box
score (efficiency per minute) because a few hundred minutes of plus/minus alone is mostly noise.

Rating for a game uses only stints from earlier games (refitted every REFIT_DAYS days), so it can feed
pre-game features.

Reconstruction: the source lists events newest first; rows are reversed. Period 1 starts with the box
score's starters. Each later period starts with whoever finished the last one, corrected by the period's
own events (a player whose first event is "in" was not on; one who acts or goes "out" first was). Stints
where a side does not have exactly five are dropped and counted. The prior is league average (PRIOR_SCALE 0): a
box-score prior did no better on the development seasons.

Usage: python -m nbl.model.onoff nbl/cache     (writes stints.parquet, ratings.parquet, lineup_rapm.parquet)
"""
import sys

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.sparse.linalg import lsqr

from nbl.model.frame import name_key, season_year

PERIOD_MIN = {'REGULAR': 10.0, 'OVERTIME': 5.0}
REFIT_DAYS = 14
HALF_LIFE_DAYS = 365.0          # weight of a stint halves each year back
LAMBDA = 3000.0                 # ridge penalty toward the prior (minutes-weighted rows)


def _clock(gt):
    s = gt.astype('string').str.extract(r'^(\d+):(\d+)')
    return pd.to_numeric(s[0]) + pd.to_numeric(s[1]) / 60


def stints_for_game(ev, home, starters, s1_home=True):
    """ev: one game's events in time order; starters: {team: set(keys)}. Returns stint rows and a count of
    stints dropped for not having five a side."""
    ev = ev.copy()
    teams = [t for t in starters]
    on = {t: set(starters[t]) for t in teams}
    rows, dropped = [], 0
    s1 = s2 = 0.0
    last_t = 0.0                                       # elapsed minutes in the game at the last change
    elapsed_before = 0.0                               # minutes in completed periods
    stint_pts = {t: 0.0 for t in teams}
    for (period, ptype), pe in ev.groupby(['period', 'period_type'], sort=False):
        plen = PERIOD_MIN.get(str(ptype), 10.0)
        if period > 1 or str(ptype) == 'OVERTIME':
            # correct the carried-over lineup with this period's own first events per player
            for t in teams:
                te = pe[pe.team == t]
                first = te.dropna(subset=['key']).drop_duplicates('key')
                for r in first.itertuples():
                    if r.action_type == 'substitution' and str(r.sub_type).lower() == 'in':
                        on[t].discard(r.key)
                    else:
                        on[t].add(r.key)
        for r in pe.itertuples():
            t_now = elapsed_before + plen - (r.clock if pd.notna(r.clock) else plen)
            ns1, ns2 = r.s1, r.s2
            if pd.notna(ns1) and pd.notna(ns2):
                d1, d2 = ns1 - s1, ns2 - s2
                if d1 > 0 or d2 > 0:
                    away = [x for x in teams if x != home][0]
                    stint_pts[home if s1_home else away] += d1
                    stint_pts[away if s1_home else home] += d2
                s1, s2 = ns1, ns2
            if r.action_type == 'substitution' and r.team in on and pd.notna(r.key):
                if t_now > last_t + 1e-9 or any(stint_pts.values()):
                    rows.append(_stint(on, teams, home, t_now - last_t, stint_pts))
                    if rows[-1] is None:
                        rows.pop(); dropped += 1
                    stint_pts = {t: 0.0 for t in teams}
                    last_t = t_now
                if str(r.sub_type).lower() == 'in':
                    on[r.team].add(r.key)
                else:
                    on[r.team].discard(r.key)
        t_end = elapsed_before + plen
        if t_end > last_t + 1e-9 or any(stint_pts.values()):
            rows.append(_stint(on, teams, home, t_end - last_t, stint_pts))
            if rows[-1] is None:
                rows.pop(); dropped += 1
        stint_pts = {t: 0.0 for t in teams}
        last_t = t_end
        elapsed_before = t_end
    return rows, dropped


def _stint(on, teams, home, minutes, pts):
    away = [t for t in teams if t != home][0]
    if len(on[home]) != 5 or len(on[away]) != 5 or minutes <= 0:
        return None
    return dict(home_on=tuple(sorted(on[home])), away_on=tuple(sorted(on[away])), minutes=minutes,
                home_pts=pts[home], away_pts=pts[away])


def in_time_order(ev):
    """Events oldest first. The feed lists them newest first before 2025-26 and oldest first after, so sort:
    period (overtime after regulation), clock counting down, then the event number where there is one,
    else the reverse of the file order (the old newest-first listing)."""
    ev = ev.copy()
    ev['_p'] = ev.period.astype(float) + (ev.period_type.astype(str) == 'OVERTIME') * 10
    ev['_c'] = -ev.clock.fillna(99.0)
    ev['_n'] = ev.action_number if ev.action_number.notna().all() else -pd.Series(range(len(ev)), index=ev.index, dtype=float)
    return ev.sort_values(['_p', '_c', '_n'], kind='stable').drop(columns=['_p', '_c', '_n'])


def build_stints(cache):
    pbp = pd.read_parquet(f'{cache}/pbp.parquet')
    players = pd.read_parquet(f'{cache}/players.parquet')
    games = players.drop_duplicates('game')[['game', 'tip', 'season']]
    home_of = players[players.is_home == 1].drop_duplicates('game').set_index('game').team
    starters = players[players.starter == 1].groupby(['game', 'team']).key.apply(set)
    pbp = pbp[pbp.match_id.astype(str).isin(games.game.astype(str))].copy()
    pbp['key'] = [name_key(f, l) if pd.notna(l) else None for f, l in zip(pbp.first_name, pbp.family_name)]
    pbp['clock'] = _clock(pbp['gt'])
    pbp['team'] = pbp.team_name.replace({'NZ Breakers': 'New Zealand Breakers', 'The Hawks': 'Illawarra Hawks'})
    res = pd.read_parquet(f'{cache}/results.parquet')
    final = {str(g): (pd.to_numeric(h, errors='coerce'), pd.to_numeric(a, errors='coerce'))
             for g, h, a in zip(res.match_id, res.home_score_string, res.away_score_string)}
    pbp['s1'] = pd.to_numeric(pbp.s1, errors='coerce')
    pbp['s2'] = pd.to_numeric(pbp.s2, errors='coerce')
    out, dropped, kept_games, bad_score = [], 0, 0, 0
    for gm, ev in pbp.groupby('match_id', sort=False):
        gm = str(gm)
        if gm not in home_of.index:
            continue
        home = home_of[gm]
        teams = players[players.game == gm].team.unique()
        st = {t: starters.get((gm, t), set()) for t in teams}
        if len(teams) != 2 or any(len(v) != 5 for v in st.values()):
            continue
        ev = in_time_order(ev)
        # s1 is the home score in most games, the away score in some: decide from the final score
        fs1, fs2 = pd.to_numeric(ev.s1, errors='coerce').max(), pd.to_numeric(ev.s2, errors='coerce').max()
        hs, as_ = final.get(gm, (np.nan, np.nan))
        if fs1 == hs and fs2 == as_:
            s1_home = True
        elif fs1 == as_ and fs2 == hs:
            s1_home = False
        else:
            bad_score += 1
            continue
        rows, d = stints_for_game(ev, home, st, s1_home)
        dropped += d
        if rows:
            kept_games += 1
            for r in rows:
                r['game'] = gm
            out.extend(rows)
    s = pd.DataFrame(out).merge(games.astype({'game': str}), on='game')
    print(f'games skipped because the feed\'s final score matches neither side: {bad_score}')
    return s, dropped, kept_games


def check_score_side(s, players):
    """Which of s1/s2 is the home side: compare stint sums with the box scores."""
    tot = s.groupby('game')[['home_pts', 'away_pts']].sum()
    tg = players[players.played == 1].groupby(['game', 'is_home']).pts.sum().unstack()
    j = tot.join(tg, how='inner')
    return float(((j.home_pts - j[1.0]).abs() <= 2).mean()), float(((j.away_pts - j[0.0]).abs() <= 2).mean())


def fit_ratings(s, prior, asof, keys, lam=None):
    """Ridge plus/minus on stints before `asof`, minutes- and recency-weighted, toward `prior` (per-40 margin)."""
    s = s[s.tip < asof]
    if s.empty:
        return pd.Series(dtype=float)
    idx = {k: i for i, k in enumerate(keys)}
    rows, cols, vals = [], [], []
    for i, (h, a) in enumerate(zip(s.home_on, s.away_on)):
        for k in h:
            rows.append(i); cols.append(idx[k]); vals.append(1.0)
        for k in a:
            rows.append(i); cols.append(idx[k]); vals.append(-1.0)
    X = sparse.csr_matrix((vals, (rows, cols)), shape=(len(s), len(keys)))
    y = 40.0 * (s.home_pts - s.away_pts).to_numpy() / s.minutes.to_numpy()
    age = (asof - s.tip).dt.days.to_numpy()
    w = s.minutes.to_numpy() * 0.5 ** (age / HALF_LIFE_DAYS)
    hca = np.average(y, weights=w)                      # home court, per 40
    b0 = np.array([prior.get(k, 0.0) for k in keys])
    r = y - hca - X @ b0
    sw = np.sqrt(w)
    A = sparse.vstack([sparse.diags(sw) @ X, np.sqrt(LAMBDA if lam is None else lam) * sparse.identity(len(keys))])
    rhs = np.concatenate([sw * r, np.zeros(len(keys))])
    beta = lsqr(A, rhs, atol=1e-8, btol=1e-8, iter_lim=5000)[0]
    return pd.Series(b0 + beta, index=keys)


def ratings_by_date(s, players, prior_scale=None, lam=None):
    """Each player's rating as of every refit date (every REFIT_DAYS), from earlier stints only."""
    keys = sorted(set(k for t in s.home_on for k in t) | set(k for t in s.away_on for k in t))
    lr = players[players.played == 1]
    tips = players.tip.sort_values().unique()
    start, end = pd.Timestamp(tips[0]), pd.Timestamp(tips[-1]) + pd.Timedelta(days=REFIT_DAYS)
    out = []
    d = start + pd.Timedelta(days=60)
    while d <= end:
        # box prior: efficiency per minute above the league, as known before d, scaled to a per-40 margin
        hist = lr[lr.tip < d]
        if len(hist) > 500:
            eff = hist.groupby('key').agg(e=('eff', 'sum'), m=('min', 'sum'))
            lg = eff.e.sum() / eff.m.sum()
            shrunk = (eff.e + 100 * lg) / (eff.m + 100)
            prior = ((PRIOR_SCALE if prior_scale is None else prior_scale) * 40 * (shrunk - lg)).to_dict()
            rt = fit_ratings(s, prior, d, keys, lam)
            out.append(pd.DataFrame({'asof': d, 'key': rt.index, 'rating': rt.to_numpy()}))
        d += pd.Timedelta(days=REFIT_DAYS)
    return pd.concat(out, ignore_index=True)


PRIOR_SCALE = 0.0        # share of a player's box-score efficiency edge used as his prior; 0 = shrink to average
# Settings chosen on 2016-17 to 2022-23 only, by how well the squad rating tracked margin (nbl/docs/TEAM_STEP1.md):
# prior 0 / 0.15 / 0.35 / 0.6, penalty 300 / 1000 / 3000 / 10000, half-life 180 / 365 / 730 days.


def lineup_ratings(players, ratings):
    """Per team-game: the squad's rating (sum of each player's latest rating before the game x his expected
    share of the team's minutes x 5), for the named squad and the open squad (last game's)."""
    r = ratings.sort_values('asof')
    p = players.sort_values('tip')[['game', 'tip', 'team', 'key', 'min_ew']].copy()
    p = pd.merge_asof(p, r.rename(columns={'asof': 'tip'}).sort_values('tip'), on='tip', by='key', direction='backward',
                      allow_exact_matches=False)
    p['rating'] = p.rating.fillna(0.0)
    rows = []
    for team, g in p.groupby('team', sort=False):
        by = {k: v for k, v in g.groupby('game', sort=False)}
        order = g.drop_duplicates('game').game.tolist()
        prev = None
        for gm in order:
            cur = by[gm]

            def strength(d):
                m = d.min_ew.fillna(0).clip(lower=0)
                return float((d.rating * 200.0 * m / m.sum()).sum() / 40.0) if m.sum() > 0 else np.nan

            named = strength(cur)
            if prev is not None:
                was = by[prev][['key', 'min_ew']].merge(cur[['key', 'rating']], on='key', how='left')
                # players not in this game's rows keep their rating as of the last game
                miss = was.rating.isna()
                was.loc[miss, 'rating'] = by[prev].set_index('key').rating.reindex(was.key[miss]).to_numpy()
                open_ = strength(was)
            else:
                open_ = np.nan
            rows.append((gm, team, named, open_))
            prev = gm
    return pd.DataFrame(rows, columns=['game', 'team', 'named_rapm', 'open_rapm'])


if __name__ == '__main__':
    cache = sys.argv[1] if len(sys.argv) > 1 else 'nbl/cache'
    s, dropped, kept = build_stints(cache)
    players = pd.read_parquet(f'{cache}/players.parquet')
    print(f'{len(s):,} stints from {kept:,} games; {dropped:,} dropped for not having five a side')
    print('stint points match the box score (within 2), home / away:', check_score_side(s, players))
    s['mins_game'] = s.groupby('game').minutes.transform('sum')
    print('share of games whose kept stints cover 40+ minutes:', round(float((s.drop_duplicates('game').mins_game >= 39.9).mean()), 3))
    s.to_parquet(f'{cache}/stints.parquet', index=False)
    r = ratings_by_date(s, players[players.played.notna()])
    r.to_parquet(f'{cache}/ratings.parquet', index=False)
    lr = lineup_ratings(players, r)
    lr.to_parquet(f'{cache}/lineup_rapm.parquet', index=False)
    print(f'{r["asof"].nunique()} rating dates; squad ratings for {len(lr):,} team-games')
