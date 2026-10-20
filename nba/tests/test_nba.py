"""Hand-checked tests for the box-score rebuild and the no-leak rule.

Run:  python -m pytest nba/tests -q
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import boxscores as b  # noqa: E402
import features as f  # noqa: E402

HOME, AWAY = 100, 200


def ev(order, period, clock, action, sub="", pid=0, team=0, result="", sh=0, sa=0, ast=0):
    return dict(gameId=1, orderNumber=order, period=period, clock=clock,
                timeActual="2025-01-01T00:30:00Z", actionType=action, subType=sub,
                personId=pid, teamId=team, teamTricode={HOME: "HOM", AWAY: "AWY"}.get(team),
                shotResult=result, assistPersonId=ast, pointsTotal=0, reboundTotal=0,
                assistTotal=0, scoreHome=sh, scoreAway=sa)


def tiny_game():
    """Four periods. Home starters 1-5, away 11-15. Player 5 does nothing until a
    rebound in period 2 and nothing after it (invisible in periods 1, 3 and 4); player 1
    is subbed out for 6 at 6:00 of period 2 and back in for 6 at 12:00 of period 3."""
    rows, o = [], 1
    def add(*a, **k):
        nonlocal o
        rows.append(ev(o, *a, **k)); o += 1
    sh = sa = 0
    for p in range(1, 5):
        add(p, "PT12M00.00S", "period", "start")
        if p == 1:
            for i, pid in enumerate([1, 2, 3, 4]):
                sh += 2
                add(p, f"PT{11 - i:02d}M00.00S", "2pt", "Jump Shot", pid, HOME, "Made", sh, sa,
                    ast=2 if pid == 1 else 0)
            for i, pid in enumerate([11, 12, 13, 14, 15]):
                sa += 3
                add(p, f"PT{5 - i:02d}M00.00S", "3pt", "Jump Shot", pid, AWAY, "Made", sh, sa)
        if p == 2:
            add(p, "PT06M00.00S", "substitution", "out", 1, HOME, sh=sh, sa=sa)
            add(p, "PT06M00.00S", "substitution", "in", 6, HOME, sh=sh, sa=sa)
            add(p, "PT03M00.00S", "rebound", "defensive", 6, HOME, sh=sh, sa=sa)
            add(p, "PT02M00.00S", "rebound", "defensive", 5, HOME, sh=sh, sa=sa)
        if p == 3:
            add(p, "PT12M00.00S", "substitution", "out", 6, HOME, sh=sh, sa=sa)
            add(p, "PT12M00.00S", "substitution", "in", 1, HOME, sh=sh, sa=sa)
        add(p, "PT00M00.00S", "period", "end", sh=sh, sa=sa)
    return pd.DataFrame(rows)


def test_clock():
    assert b.clock_seconds("PT11M43.00S") == 703.0
    assert b.clock_seconds("PT00M04.50S") == 4.5


def test_minutes_and_box():
    box = b.box_for_game(tiny_game()).set_index("personId")
    # Player 1: P1 12 + P2 6 + P3 12 + P4 12 = 42 minutes. Player 6: 6 minutes.
    assert box.loc[1, "min"] == 42 and box.loc[6, "min"] == 6
    # Player 5 is filled in from the previous period's five in periods 3 and 4, but in
    # period 1 there is no previous period, so 36 minutes, not the 48 he really played.
    assert box.loc[5, "min"] == 36
    assert box.loc[2, "min"] == 48 and bool(box.loc[2, "starter"])
    assert not bool(box.loc[6, "starter"])
    assert box.loc[1, "pts"] == 2 and box.loc[2, "ast"] == 1 and box.loc[6, "reb"] == 1
    assert box.loc[11, "fg3m"] == 1 and box.loc[11, "pts"] == 3
    # Home team: 8 points, 4 x 2pt; away 15. Points match the final score.
    assert bool(box.loc[1, "home"]) and not bool(box.loc[11, "home"])
    assert bool(box.loc[1, "points_ok"])
    # The period-1 hole means home minutes do not sum to 240: the game is flagged.
    assert not bool(box.loc[1, "minutes_ok"]) and not bool(box.loc[1, "game_ok"])


def _fake_box(n=12):
    rng = np.random.default_rng(0)
    rows = []
    for g in range(n):
        for pid, team in [(1, HOME), (2, HOME), (3, AWAY)]:
            rows.append(dict(gameId=g, personId=pid, teamId=team, opp_teamId=AWAY if team == HOME else HOME,
                             date=f"2025-01-{g + 1:02d}", season=2024, home=team == HOME,
                             team_pts=100 + g, opp_pts=95, game_minutes=48, starter=True,
                             min=float(rng.integers(20, 40)), pts=float(rng.integers(0, 40)),
                             reb=1.0, ast=1.0, fg3m=1.0, fga=10.0, fta=2.0, tov=1.0))
    return pd.DataFrame(rows)


def test_no_feature_sees_its_own_game():
    """Change one game's result wildly: no feature on that game's row may move."""
    box = _fake_box()
    base = f.build(box)
    hit = box.copy()
    mask = (hit.gameId == 7) & (hit.personId == 1)
    hit.loc[mask, ["min", "pts", "reb", "ast", "fg3m", "fga", "fta"]] = [48, 99, 30, 25, 12, 40, 20]
    hit.loc[hit.gameId == 7, ["team_pts"]] = 200
    moved = f.build(hit)
    cols = sorted(set(f.FEATURES_RATE))
    a = base[(base.gameId == 7)].sort_values("personId")[cols].reset_index(drop=True)
    c = moved[(moved.gameId == 7)].sort_values("personId")[cols].reset_index(drop=True)
    pd.testing.assert_frame_equal(a, c)
    # ...and the NEXT game does see it.
    a8 = base[(base.gameId == 8) & (base.personId == 1)].iloc[0]
    c8 = moved[(moved.gameId == 8) & (moved.personId == 1)].iloc[0]
    assert c8.min_last == 48 and a8.min_last != 48
