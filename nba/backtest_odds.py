"""Backtest against timestamped prices (The Odds API format), using only what was known then.

For each player prop, each book, each snapshot time T:
  * our projection from the injury report filed by T (at_report.py: 5pm the day before, then
    11am, 1pm, 3pm, 5pm, 7pm US Eastern on game day; before 5pm the day before = no bet);
  * calibrated P(over) from the projection (probability.py), blended with the market's no-vig
    price using weights fitted on 2024/25 only, scored on 2025/26;
  * at each decision time (the open, then each report hour, then 1 hour before tip) we bet the
    side with the best expected value at the BEST price across the books on offer, if it
    clears the edge;
  * closing price = each book's last snapshot before tip-off; closing-line value = the
    no-vig closing probability of our side minus the no-vig probability when we bet.

Reports, by decision time, by book, by stat: bets, ROI, a 95% range by game date, and CLV.

    python nba/backtest_odds.py odds/raw/basketball_nba/*.csv.gz
"""
from __future__ import annotations

import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import injuries_check as ic
import probability as pb
from features import DATA

HERE = Path(__file__).resolve().parent
MARKET_STAT = {"player_points": "pts", "player_rebounds": "reb", "player_assists": "ast", "player_threes": "fg3m"}
REPORT_HOURS = [("5pm day before", -1, 17), ("11am", 0, 11), ("1pm", 0, 13), ("3pm", 0, 15), ("5pm", 0, 17),
                ("7pm", 0, 19)]


def load_odds(paths: list[str]) -> pd.DataFrame:
    o = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)
    o = o[o.market.isin(MARKET_STAT) & o.side.isin(["Over", "Under"])].dropna(subset=["point", "price"])
    o["snapshot"] = pd.to_datetime(o.snapshot, utc=True)
    o["commence"] = pd.to_datetime(o.commence, utc=True)
    o["date"] = o.commence.dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
    o["st"] = o.market.map(MARKET_STAT)
    wide = (o.pivot_table(index=["event_id", "commence", "date", "home", "away", "snapshot", "book", "st",
                                 "player", "point"], columns="side", values="price", aggfunc="last")
            .reset_index().dropna(subset=["Over", "Under"]))
    return wide.rename(columns={"Over": "dec_over", "Under": "dec_under"})


def attach_players(w: pd.DataFrame) -> pd.DataFrame:
    """Odds-API full names -> our personId, by (season, team, last name + first initial).
    Unmatched or ambiguous names are dropped and counted, never guessed."""
    names = ic.player_names()
    box = pd.read_parquet(DATA / "box.parquet")[["season", "team", "personId"]].drop_duplicates()
    roster = box.merge(names, on="personId")
    parts = w.player.str.split(" ", n=1, expand=True)
    w["key"] = [ic.name_key(last, first) for first, last in zip(parts[0], parts[1].fillna(""))]
    d = pd.to_datetime(w.date)
    w["season"] = d.dt.year - (d.dt.month < 8).astype(int)
    teams = w.home.map(ic.TEAMS), w.away.map(ic.TEAMS)
    cand = []
    for side in teams:
        cand.append(w.assign(team=side).merge(roster, on=["season", "team", "key"], how="inner"))
    m = pd.concat(cand)
    n = m.groupby(["event_id", "snapshot", "book", "st", "player", "point"]).personId.transform("nunique")
    dropped = 1 - m[n == 1].drop_duplicates(["player", "event_id"]).shape[0] / max(1, w.drop_duplicates(["player", "event_id"]).shape[0])
    print(f"name match: {dropped:.1%} of player-games could not be matched to exactly one player and are left out")
    return m[n == 1]


def report_label(row_snapshot: pd.Series, date: pd.Series) -> pd.Series:
    """The latest injury report filed by each snapshot time (US Eastern)."""
    et = row_snapshot.dt.tz_convert("America/New_York").dt.tz_localize(None)
    day = pd.to_datetime(date)
    label = pd.Series(pd.NA, index=row_snapshot.index, dtype="object")
    for name, off, hour in REPORT_HOURS:
        t = day + pd.Timedelta(days=off) + pd.Timedelta(hours=hour)
        label = label.mask(et >= t, name)
    return label


def run(w: pd.DataFrame, edge: float = 0.03) -> pd.DataFrame:
    proj = pd.read_parquet(DATA / "projections_at_report.parquet")
    proj["date"] = pd.to_datetime(proj.date).dt.strftime("%Y-%m-%d")
    box = pd.read_parquet(DATA / "box.parquet")[["date", "personId", "pts", "reb", "ast", "fg3m"]]
    long = pd.concat([proj[["date", "personId", "snapshot", f"{s}_proj"]].rename(
        columns={f"{s}_proj": "proj", "snapshot": "report"}).assign(st=s) for s in MARKET_STAT.values()])
    act = box.melt(id_vars=["date", "personId"], var_name="st", value_name="actual")

    w["report"] = report_label(w.snapshot, w.date)
    w = w.dropna(subset=["report"]).merge(long, on=["date", "personId", "st", "report"]).merge(
        act, on=["date", "personId", "st"])
    var = pb.fit_alphas()
    o, u = pb.p_over_under(np.maximum(w.proj.to_numpy(), 0.05), w.point.to_numpy(), np.stack([var[s] for s in w.st]))
    w["p_model"] = o / (o + u)
    io, iu = 1 / w.dec_over, 1 / w.dec_under
    w["p_mkt"] = io / (io + iu)

    # Closing no-vig probability per book: that book's last snapshot before tip-off.
    close = (w[w.snapshot < w.commence].sort_values("snapshot").groupby(["event_id", "book", "st", "personId"])
             .tail(1)[["event_id", "book", "st", "personId", "point", "p_mkt"]]
             .rename(columns={"point": "close_point", "p_mkt": "close_p_over"}))

    # Blend weights from 2024/25 only (each line once, at its last pre-tip snapshot).
    last = w.sort_values("snapshot").groupby(["event_id", "book", "st", "personId", "point"]).tail(1)
    last = last[last.actual != last.point].assign(went_over=lambda x: (x.actual > x.point).astype(float))
    wts = pb.fit_blend(last[last.date < "2025-07-01"]) if (last.date < "2025-07-01").any() else np.array([0, 1, 0])
    w["p_over"] = pb.blend(w, wts)

    # Decision times: the first snapshot carrying the prop (the open), each report hour, 1h before.
    w["mins_before"] = (w.commence - w.snapshot).dt.total_seconds() / 60
    first = w.groupby(["event_id", "st", "personId"]).snapshot.transform("min")
    decisions = {"open": w.snapshot == first, "1h before": w.mins_before.between(45, 75)}
    for name, _, _ in REPORT_HOURS:
        decisions[f"report {name}"] = w.report.eq(name) & (w.groupby(["event_id", "st", "personId", "report"])
                                                            .snapshot.transform("min") == w.snapshot)
    out = []
    for name, mask in decisions.items():
        d = w[mask].copy()
        d["ev_over"] = d.p_over * d.dec_over - 1
        d["ev_under"] = (1 - d.p_over) * d.dec_under - 1
        d["side"] = np.where(d.ev_over >= d.ev_under, "over", "under")
        d["ev"] = d[["ev_over", "ev_under"]].max(axis=1)
        d["price"] = np.where(d.side == "over", d.dec_over, d.dec_under)
        # best book for the chosen side, same line
        d = d.sort_values("price").groupby(["event_id", "st", "personId", "point", "side"]).tail(1)
        d = d[d.ev >= edge].sort_values("ev").groupby(["event_id", "st", "personId"]).tail(1)
        won = np.where(d.side == "over", d.actual > d.point, d.actual < d.point)
        push = d.actual == d.point
        d["pnl"] = np.where(push, 0.0, np.where(won, d.price - 1, -1.0))
        d = d.merge(close, on=["event_id", "book", "st", "personId"], how="left")
        p_side_now = np.where(d.side == "over", d.p_mkt, 1 - d.p_mkt)
        p_side_close = np.where(d.side == "over", d.close_p_over, 1 - d.close_p_over)
        d["clv"] = np.where(d.close_point == d.point, p_side_close - p_side_now, np.nan)
        out.append(d.assign(decision=name))
    return pd.concat(out, ignore_index=True)


def summarise(b: pd.DataFrame) -> None:
    rng = np.random.default_rng(0)
    rows = []
    for (dec, season), g in b.assign(season=np.where(b.date < "2025-07-01", "24/25 (fit)", "25/26 (test)")
                                     ).groupby(["decision", "season"]):
        s = g.groupby("date").pnl.agg(["sum", "size"])
        a, c = s["sum"].to_numpy(), s["size"].to_numpy()
        idx = rng.integers(0, len(s), (2000, len(s)))
        boot = a[idx].sum(1) / c[idx].sum(1)
        rows.append(dict(decision=dec, season=season, bets=len(g), roi=g.pnl.mean(),
                         lo=np.percentile(boot, 2.5), hi=np.percentile(boot, 97.5), clv=g.clv.mean()))
    print(pd.DataFrame(rows).round(3).to_string(index=False))
    print("\nBy book (all decisions, 2025/26):")
    print(b[b.date >= "2025-07-01"].groupby("book").agg(bets=("pnl", "size"), roi=("pnl", "mean"),
                                                         clv=("clv", "mean")).round(3).to_string())


def main(paths: list[str]) -> None:
    w = attach_players(load_odds(paths))
    b = run(w)
    b.to_parquet(DATA / "backtest_odds.parquet", index=False)
    summarise(b)


if __name__ == "__main__":
    main(sys.argv[1:] or glob.glob(str(HERE / "odds/raw/basketball_nba/*.csv.gz")))
