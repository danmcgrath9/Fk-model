"""Betting angles: do they exist in the games, and are they already in the line?

Angles (every one built from games BEFORE the one it describes):
  dvp        opponent's defence against the player's role: how much more (or less) per
             minute that opponent has allowed guards / wings / bigs than those players
             usually score, over its recent games, times the player's expected minutes
  total      stand-in game total (both teams' prior scoring and allowing; the real
             total needs The Odds API)
  pace       both teams' recent possessions per 48 minutes (FGA + 0.44 FTA + TOV)
  blowout    stand-in expected margin, absolute
  rest       back-to-back, or 3+ days off
  home       home or away
  last_game  the player's last game against his season average (does the market
             overreact to one big night?)
  line_gap   the line against the player's season average (is a line set well above his
             average too high?)

Role, since the data has no positions: by the player's own per-minute rates up to the
previous game. Guard = assists 0.13+ a minute (top quarter); big = rebounds 0.23+ a minute
and not a guard; wing = everyone else.

Test 1, all prop-able player-games 2024/25-2025/26: by angle bucket, the average miss of
the player's season average (does the angle matter in real games?) and of our model (has
the model already learned it?).
Test 2, the 6,625 DunkAPI lines: by bucket, how often the over landed against what the
market's no-vig price said, found on 2024/25 and checked on 2025/26. Only an angle that
points the same way in both seasons is worth anything; with this many buckets a few will
look good by luck.

    python nba/angles.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import line_test as lt
import project as pr
from features import DATA

STATS = ["pts", "reb", "ast", "fg3m"]


def roles(df: pd.DataFrame) -> pd.Series:
    guard = df.ast_pm_l >= 0.13
    big = (df.reb_pm_l >= 0.23) & ~guard
    return np.select([guard, big], ["guard", "big"], "wing")


def add_angles(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["date", "gameId"]).copy()
    df["role"] = roles(df)

    # Defence against role. Per player-game: what he scored per minute above his own
    # long-run rate. Summed per (game, defending team, role), then each defence's EWM over
    # its PREVIOUS games.
    for st in STATS:
        df[f"{st}_over_pm"] = (df[st] - df[f"{st}_pm_l"] * df["min"])
    agg = (df[df["min"] > 0].groupby(["gameId", "date", "opp_teamId", "role"])
           .agg(**{f"{st}_over": (f"{st}_over_pm", "sum") for st in STATS}, mins=("min", "sum"))
           .reset_index().sort_values(["date", "gameId"]))
    for st in STATS:
        agg[f"{st}_allow_pm"] = agg[f"{st}_over"] / agg.mins
        agg[f"dvp_{st}_pm"] = (agg.groupby(["opp_teamId", "role"])[f"{st}_allow_pm"]
                               .transform(lambda x: x.shift(1).ewm(halflife=10, min_periods=5).mean()))
    df = df.merge(agg[["gameId", "opp_teamId", "role", *[f"dvp_{st}_pm" for st in STATS]]],
                  on=["gameId", "opp_teamId", "role"], how="left")
    for st in STATS:
        df[f"dvp_{st}"] = df[f"dvp_{st}_pm"] * df.min_ewm5

    # Pace: team possessions per 48, each team's previous games, both teams averaged.
    tg = (df.groupby(["gameId", "date", "teamId", "opp_teamId", "game_minutes"])[["fga", "fta", "tov"]].sum()
          .reset_index().sort_values(["date", "gameId"]))
    tg["poss48"] = (tg.fga + 0.44 * tg.fta + tg.tov) * 48 / tg.game_minutes
    tg["pace_ewm"] = tg.groupby("teamId").poss48.transform(lambda x: x.shift(1).ewm(halflife=10, min_periods=5).mean())
    opp = tg[["gameId", "teamId", "pace_ewm"]].rename(columns={"teamId": "opp_teamId", "pace_ewm": "opp_pace"})
    tg = tg.merge(opp, on=["gameId", "opp_teamId"])
    tg["pace"] = (tg.pace_ewm + tg.opp_pace) / 2
    df = df.merge(tg[["gameId", "teamId", "pace"]], on=["gameId", "teamId"], how="left")

    # Last game against season average, per stat (shifted: the last game, not this one).
    df = df.sort_values(["personId", "date", "gameId"])
    for st in STATS:
        last = df.groupby("personId")[st].shift(1)
        df[f"last_vs_avg_{st}"] = last - df[f"{st}_season"]
    df["rest"] = np.select([df.b2b == 1, df.days_rest >= 3], ["back-to-back", "3+ days off"], "1-2 days")
    df["home_away"] = np.where(df.home, "home", "away")
    return df


def buckets(s: pd.Series, q=(0, .2, .4, .6, .8, 1), labels=("low", "low-mid", "mid", "mid-high", "high")):
    return pd.qcut(s, q, labels=labels, duplicates="drop")


def test_games(df: pd.DataFrame) -> None:
    """Test 1: does the angle matter in real games, and has our model learned it?"""
    proj = pd.read_parquet(DATA / "projections.parquet")
    g = df.merge(proj[["gameId", "personId", *[f"{s}_proj" for s in STATS]]], on=["gameId", "personId"])
    g = g[pr.propable(g)]
    print(f"TEST 1. All prop-able player-games 2024/25-2025/26 ({len(g):,}). Average of actual minus")
    print("season average (does the angle move real output?) and actual minus our model (does the model")
    print("already have it?). Positive = scored MORE than expected.\n")
    for st in STATS:
        cols = {
            "dvp": buckets(g[f"dvp_{st}"]), "total": buckets(g.exp_total), "pace": buckets(g.pace),
            "blowout": buckets(g.abs_exp_margin), "rest": g.rest, "home": g.home_away,
            "last game": buckets(g[f"last_vs_avg_{st}"]),
        }
        print(f"  {st}")
        for name, b in cols.items():
            t = g.assign(b=b).groupby("b", observed=True).apply(lambda x: pd.Series({
                "n": len(x), "vs avg": (x[st] - x[f"{st}_season"]).mean(),
                "vs model": (x[st] - x[f"{st}_proj"]).mean()}), include_groups=False)
            spread_avg = t["vs avg"].max() - t["vs avg"].min()
            spread_mod = t["vs model"].max() - t["vs model"].min()
            print(f"    {name:<10} range vs avg {spread_avg:5.2f} | vs model {spread_mod:5.2f}   " +
                  "  ".join(f"{i}:{r['vs avg']:+.2f}/{r['vs model']:+.2f}" for i, r in t.iterrows()))
        print()


def test_lines(df: pd.DataFrame) -> pd.DataFrame:
    """Test 2: against the line. Over rate minus the market's no-vig over price, by bucket,
    2024/25 (found) and 2025/26 (checked)."""
    L = lt.load_lines()
    L = L[L.actual.notna() & L.over_odds.notna() & (L.result != "push")].copy()
    do, du = lt.american_to_decimal(L.over_odds), lt.american_to_decimal(L.under_odds)
    L["dec_over"], L["dec_under"] = do, du
    L["p_mkt"] = (1 / do) / (1 / do + 1 / du)
    L["went_over"] = (L.result == "over").astype(float)
    d = df.assign(date=df.date.dt.strftime("%Y-%m-%d"))
    rows = []
    for st in STATS:
        x = L[L.st == st].merge(d, on=["personId", "date"], how="inner")
        x["line_gap"] = x.line - x[f"{st}_season"]
        angle = {"dvp": x[f"dvp_{st}"], "total": x.exp_total, "pace": x.pace, "blowout": x.abs_exp_margin,
                 "last game": x[f"last_vs_avg_{st}"], "line vs avg": x.line_gap}
        for name, v in angle.items():
            x["b"] = pd.qcut(v, [0, 1 / 3, 2 / 3, 1], labels=["low", "mid", "high"], duplicates="drop")
            rows += _rows(x, st, name)
        for name, col in [("rest", "rest"), ("home", "home_away")]:
            x["b"] = x[col]
            rows += _rows(x, st, name)
    return pd.DataFrame(rows)


def _rows(x, st, name):
    out = []
    for b, g in x.groupby("b", observed=True):
        r = {"stat": st, "angle": name, "bucket": b}
        for season, h in [("24/25", g[g.date < "2025-07-01"]), ("25/26", g[g.date >= "2025-07-01"])]:
            over_pnl = np.where(h.went_over == 1, h.dec_over - 1, -1.0)
            under_pnl = np.where(h.went_over == 0, h.dec_under - 1, -1.0)
            r[f"n {season}"] = len(h)
            r[f"over-mkt {season}"] = h.went_over.mean() - h.p_mkt.mean()
            r[f"best side ROI {season}"] = max(over_pnl.mean(), under_pnl.mean()) if len(h) else np.nan
            r[f"side {season}"] = "over" if over_pnl.mean() > under_pnl.mean() else "under"
        out.append(r)
    return out


def main() -> None:
    df = pd.read_parquet(DATA / "features.parquet")
    df = df[df.game_ok & df.min_ewm5.notna()]
    df = add_angles(df)
    test_games(df[df.season.isin(pr.TEST)])
    t = test_lines(df)
    pd.set_option("display.width", 220)
    print("TEST 2. Against the line (12 players). over-mkt = over rate minus the market's no-vig over price.")
    print("An angle counts only if the same side wins in BOTH seasons, and by enough to beat the margin.\n")
    keep = t[(t["side 24/25"] == t["side 25/26"]) & (t["best side ROI 24/25"] > 0) & (t["best side ROI 25/26"] > 0)]
    print(t.round(3).to_string(index=False))
    print(f"\n{len(keep)} of {len(t)} buckets profitable on the same side in both seasons "
          f"(about {len(t) * 0.25:.0f} expected by luck alone if each season is a coin flip):")
    print(keep.round(3).to_string(index=False))
    t.to_csv(DATA / "angles_lines.csv", index=False)


if __name__ == "__main__":
    main()
