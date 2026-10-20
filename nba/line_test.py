"""First line test: our projections against DunkAPI's prop lines (10 players, 2024/25-2025/26).

The line is DunkAPI's median across books from ONE pre-game capture (their docs; and in
this pull the "opening" line equals it in 100% of rows), so this is us against roughly
the close. Regular season only: our model does not cover the playoffs.

Three questions, in order of how little they assume:
  1. Is our projection closer to what happened than the bookie's line is?  (MAE)
  2. When we disagree with the line, which side wins more often?
  3. Flat 1-unit bets wherever our probability beats the price by an edge, at the
     prices DunkAPI recorded. Profit bootstrapped by game date.

Probabilities (step 2 in miniature): P(over) = P(projection + error > line), with the
error drawn from the model's OUT-OF-SAMPLE misses on 2023/24 (trained on 2020-2022),
by stat and projection size. It is a first cut, not the finished step 2.

    python nba/line_test.py
"""
from __future__ import annotations

import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd

import project as pr
from features import DATA

HERE = Path(__file__).resolve().parent
STAT = {"points": "pts", "rebounds": "reb", "assists": "ast", "threes": "fg3m"}


def load_lines() -> pd.DataFrame:
    rows = []
    for f in glob.glob(str(HERE / "lines/dunkapi/*_player_*.json")):
        d = json.loads(Path(f).read_text())
        for g in d["data"]["games"]:
            rows.append(dict(personId=d["personId"], name=d["name"],
                             st=STAT[d["market"].replace("player_", "")], **g))
    return pd.DataFrame(rows).rename(columns={"game_date": "date"})


def american_to_decimal(a: pd.Series) -> pd.Series:
    return np.where(a > 0, 1 + a / 100, 1 + 100 / a.abs())


def residual_table() -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Out-of-sample misses (actual - projection) on 2023/24, model trained on 2020-2022."""
    df = pd.read_parquet(DATA / "features.parquet")
    df = df[df.game_ok]
    train = df[df.season.isin([2020, 2021, 2022]) & df.min_ewm5.notna()]
    val = df[df.season == 2023]
    p = pr.fit_predict(train, val).merge(val[["gameId", "personId", "min_ewm5", "gp_season"]],
                                          on=["gameId", "personId"])
    p = p[pr.propable(p)]
    return {st: (p[f"{st}_proj"].to_numpy(), (p[st] - p[f"{st}_proj"]).to_numpy())
            for st in pr.TARGETS}


def p_over_under(proj: float, line: float, table) -> tuple[float, float]:
    """Errors from the 300 nearest projections in 2023/24, so a 30-point projection gets
    30-point-sized misses."""
    projs, res = table
    near = np.argsort(np.abs(projs - proj))[:300]
    outcome = proj + res[near]
    actual = np.round(outcome)                 # stats are whole numbers
    return float((actual > line).mean()), float((actual < line).mean())


def main() -> None:
    L = load_lines()
    proj = pd.read_parquet(DATA / "projections.parquet")
    long = []
    for st in pr.TARGETS:
        long.append(proj[["gameId", "date", "personId", f"{st}_proj", st]].rename(
            columns={f"{st}_proj": "proj", st: "ours"}).assign(st=st))
    proj = pd.concat(long)
    proj["date"] = pd.to_datetime(proj["date"]).dt.strftime("%Y-%m-%d")
    j = L.merge(proj, on=["personId", "date", "st"], how="inner")
    j = j[j.actual.notna()].copy()
    assert (j.actual == j.ours).mean() > 0.99, "lines do not line up with our box scores"
    print(f"{len(j):,} lines matched to a regular-season projection, "
          f"{j.name.nunique()} players, {j.date.min()} to {j.date.max()}\n")

    # 1. Who is closer to what happened?
    print("1. Average miss (lower is better)")
    t = j.groupby("st").apply(lambda g: pd.Series({
        "lines": len(g), "our projection": (g.proj - g.actual).abs().mean(),
        "bookie line": (g.line - g.actual).abs().mean()}), include_groups=False)
    print(t.round(2).to_string(), "\n")

    # 2. When we disagree, who wins?
    j["side"] = np.where(j.proj > j.line, "over", "under")
    j["win"] = np.where(j.result == "push", np.nan, (j.result == j.side).astype(float))
    print("2. Our side's win rate against the line (52.4% breaks even at -110)")
    for gap in [0, 1, 2, 3]:
        g = j[(j.proj - j.line).abs() >= gap]
        print(f"   disagree by {gap}+  : {g.win.mean():.1%} of {g.win.notna().sum():,}")
    print()

    # 3. Flat bets where our probability beats the price
    tables = residual_table()
    po, pu = zip(*[p_over_under(r.proj, r.line, tables[r.st]) for r in j.itertuples()])
    j["p_over"], j["p_under"] = po, pu
    j["dec_over"], j["dec_under"] = american_to_decimal(j.over_odds), american_to_decimal(j.under_odds)
    # A push returns the stake: EV = p_win x decimal + p_push - 1
    j["ev_over"] = j.p_over * j.dec_over + (1 - j.p_over - j.p_under) - 1
    j["ev_under"] = j.p_under * j.dec_under + (1 - j.p_over - j.p_under) - 1
    j["bet"] = np.where(j.ev_over >= j.ev_under, "over", "under")
    j["ev"] = j[["ev_over", "ev_under"]].max(axis=1)
    dec = np.where(j.bet == "over", j.dec_over, j.dec_under)
    j["pnl"] = np.where(j.result == "push", 0.0, np.where(j.result == j.bet, dec - 1, -1.0))

    rng = np.random.default_rng(0)
    print("3. Flat 1-unit bets at the recorded prices, by the edge we demand")
    print(f"   {'edge':>6} {'bets':>6} {'win%':>6} {'ROI':>7}   95% bootstrap ROI (by game date)")
    for edge in [0.0, 0.03, 0.05, 0.10]:
        b = j[j.ev >= edge]
        if len(b) < 30:
            print(f"   {edge:>6.0%} {len(b):>6}  too few bets to say anything")
            continue
        byday = b.groupby("date").pnl.agg(["sum", "size"])
        s, c = byday["sum"].to_numpy(), byday["size"].to_numpy()
        idx = rng.integers(0, len(byday), (2000, len(byday)))
        boot = s[idx].sum(1) / c[idx].sum(1)
        win = (b.pnl > 0).sum() / (b.result != "push").sum()
        print(f"   {edge:>6.0%} {len(b):>6} {win:>6.1%} {b.pnl.sum() / len(b):>+7.1%}   "
              f"{np.percentile(boot, 2.5):+.1%} to {np.percentile(boot, 97.5):+.1%}")
    b = j[j.ev >= 0.05]
    print("\n   At a 5% edge, by stat:")
    print(b.groupby("st").agg(bets=("pnl", "size"), roi=("pnl", "mean")).round(3).to_string())
    j.to_parquet(DATA / "line_test.parquet", index=False)


if __name__ == "__main__":
    main()
