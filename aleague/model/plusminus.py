"""Regularised plus-minus player ratings from line-up minutes (docs/RESEARCH.md item 3).

Sæbø & Hvattum (2015, 2019) and Kharrat, McHale & Peña (2020): cut each match into segments at every
substitution and sending-off; in each segment the same players are on the pitch, and the segment's
goal difference per 90 minutes is regressed on who was on (+1 for the home side, -1 for the away side)
with a home term, weighted by the segment's length, ridge-penalised so a player with few minutes stays
near zero. A player's rating is his estimated effect on goal difference per 90.

What it is for here: a confirmed line-up can be rated against the side's usual line-up, so the team
model's prices move when key players are out (the "teams named" model).

segments(player_games, events) -> one row per segment with its players
fit(segments, before, half_life, reg) -> {player_id: rating}, from segments before a date only
lineup_rating(ratings, player_ids) -> the sum over a starting XI
"""
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from scipy.sparse.linalg import lsqr


def segments(pg, ev):
    """Segments of each match between changes of personnel, within 90 minutes."""
    goals = ev[ev.event.isin(['Goal', 'Penalty', 'Own Goal']) & (ev.minute.fillna(0) <= 90)]
    goals_by = {k: g for k, g in goals.groupby('ual_match_id')}
    out = []
    for mid, m in pg.groupby('ual_match_id'):
        on = m[m.minutes > 0]
        if on.empty:
            continue
        # each player's time on: from start (0 or sub_on) to start + minutes
        start = np.where(on.starter, 0, on.sub_on.fillna(0)).astype(float)
        end = start + on.minutes.to_numpy(dtype=float)
        cuts = sorted({0.0, 90.0, *start, *end})
        g = goals_by.get(mid)
        for a, b in zip(cuts[:-1], cuts[1:]):
            if b - a < 1:
                continue
            here = (start <= a) & (end >= b)
            home = set(on.player_id[here & on.is_home.to_numpy()])
            away = set(on.player_id[here & ~on.is_home.to_numpy()])
            if not home or not away:
                continue
            gh = ga = 0
            if g is not None:
                # a goal in minute t falls in the segment (a, b]; the listed side is the side it counts for
                inside = g[(g.minute > a) & (g.minute <= b)]
                gh, ga = int((inside.side == 'home').sum()), int((inside.side == 'away').sum())
            out.append(dict(ual_match_id=mid, date=m.date.iloc[0], season=m.season.iloc[0],
                            neutral=False, length=b - a, home_players=tuple(sorted(home)),
                            away_players=tuple(sorted(away)), gd=gh - ga))
    return pd.DataFrame(out)


def fit(seg, before, half_life=365.0, reg=30.0):
    """Ridge plus-minus on segments before `before`: {player_id: goal difference per 90}."""
    s = seg[seg.date < before]
    if s.empty:
        return {}, 0.0
    players = sorted({p for t in s.home_players for p in t} | {p for t in s.away_players for p in t})
    ix = {p: i for i, p in enumerate(players)}
    rows, cols, vals = [], [], []
    for r, (h, a) in enumerate(zip(s.home_players, s.away_players)):
        for p in h:
            rows.append(r); cols.append(ix[p]); vals.append(1.0)
        for p in a:
            rows.append(r); cols.append(ix[p]); vals.append(-1.0)
    n, k = len(s), len(players)
    X = csr_matrix((vals, (rows, cols)), shape=(n, k))
    X = hstack([X, csr_matrix(np.ones((n, 1)))]).tocsr()  # the home term
    age = np.array([(before - d).days for d in s.date], dtype=float)
    w = s.length.to_numpy() / 90 * 0.5 ** (age / half_life)
    y = s.gd.to_numpy() / (s.length.to_numpy() / 90)   # goal difference per 90
    sw = np.sqrt(w)
    Xw = X.multiply(sw[:, None]).tocsr()
    # ridge through lsqr's damp; the home term is penalised too, lightly enough not to matter at this size
    beta = lsqr(Xw, y * sw, damp=np.sqrt(reg))[0]
    return {p: beta[i] for p, i in ix.items()}, float(beta[-1])


def lineup_rating(ratings, player_ids):
    return float(sum(ratings.get(p, 0.0) for p in player_ids))
