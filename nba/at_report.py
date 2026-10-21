"""Projections as they could have been made at a given injury-report time, not after tip-off.

The model in project.py is told who actually played. That is the right way to TRAIN it
(it learns how minutes move when a teammate is missing) and the wrong way to TEST it
against a line that was posted hours earlier. Here the "who plays tonight" inputs are
rebuilt from the official injury report filed by time T instead:

  * the team's candidates are the rotation players (10+ minutes a game) who played in one
    of its last three games, plus anyone who actually plays tonight (a player back from a
    long absence is on the report as available, so this is known before tip);
  * Out or Doubtful at T: counted as missing (Doubtful players played 0 of 14 in the
    January 2025 check);
  * Questionable at T: counted as half there (they played 49% of the time);
  * everyone else: there.

The trained models are the same walk-forward models as project.py; only their
availability inputs change. Snapshots: 5pm the day before, and 11am, 1pm, 3pm, 5pm, 7pm on
game day (US Eastern).

    python nba/at_report.py      # -> nba/data/projections_at_report.parquet
"""
from __future__ import annotations

import lightgbm as lgb
import numpy as np
import pandas as pd

import injuries_check as ic
import project as pr
from features import DATA, FEATURES_MIN, FEATURES_RATE, ROTATION_MIN

AVAIL = ["rot_present_min", "rot_present_n", "vacated_min", "others_present_min", "share_proj"]
WEIGHT = {"Out": 0.0, "Doubtful": 0.0, "Questionable": 0.5}


def report_status() -> pd.DataFrame:
    """(date, personId, report_time) -> status, for every matched report row."""
    m, _ = ic.joined()
    m = m[m.match == "one"].copy()
    m["personId"] = m.personId.astype(int)
    return m[["date", "personId", "report_time", "Current Status"]].drop_duplicates(
        ["date", "personId", "report_time"])


def availability_at(df: pd.DataFrame, status: pd.DataFrame, report_time: str, day_offset: int) -> pd.DataFrame:
    """Availability inputs for every player-game, as known at `report_time` on each game day
    (HH:MM, US Eastern) shifted by `day_offset` days (-1 = the day before)."""
    games = (df[["gameId", "teamId", "date"]].drop_duplicates()
             .sort_values(["teamId", "date", "gameId"]).reset_index(drop=True))
    games["k"] = games.groupby("teamId").cumcount()
    r = df[["gameId", "teamId", "personId", "min_ewm5", "min_ewm5_post"]].merge(
        games[["gameId", "teamId", "k", "date"]], on=["gameId", "teamId"])
    r["date_s"] = r.date.dt.strftime("%Y-%m-%d")
    stamp = (r.date + pd.Timedelta(days=day_offset)).dt.strftime("%Y-%m-%d") + " " + report_time
    st = status.rename(columns={"Current Status": "status"})
    st = st.assign(key=st.date + "|" + st.personId.astype(str) + "|" + st.report_time)
    lookup = dict(zip(st.key, st.status))

    rows = []
    for t, g in r.groupby("teamId"):
        by_k = {k: x for k, x in g.groupby("k")}
        for k in sorted(by_k):
            tonight = by_k[k]
            date_s = tonight.date_s.iloc[0]
            when = stamp.loc[tonight.index[0]]
            cand = {}
            for j in (k - 3, k - 2, k - 1):
                if j in by_k:
                    cand.update(dict(zip(by_k[j].personId, by_k[j].min_ewm5_post)))
            pre = dict(zip(tonight.personId, tonight.min_ewm5.fillna(0)))
            for p, v in pre.items():
                cand[p] = v                      # tonight's players carry their pre-game average
            w = {p: WEIGHT.get(lookup.get(f"{date_s}|{p}|{when}"), 1.0) for p in cand}
            rot = {p: v for p, v in cand.items() if v >= ROTATION_MIN}
            present = sum(v * w[p] for p, v in rot.items())
            n_present = sum(w[p] for p in rot)
            vacated = sum(v * (1 - w[p]) for p, v in rot.items())
            for p in tonight.personId:
                me = rot.get(p, 0.0) * w.get(p, 1.0)
                mine = pre.get(p, 0.0)
                others = present - me
                rows.append((tonight.gameId.iloc[0], t, p, present, n_present, vacated, others,
                             mine / (mine + others) * 240 if (mine + others) > 0 else np.nan,
                             lookup.get(f"{date_s}|{p}|{when}", "not listed")))
    return pd.DataFrame(rows, columns=["gameId", "teamId", "personId", *AVAIL, "own_status"])


def main() -> None:
    df = pd.read_parquet(DATA / "features.parquet")
    df = df[df.game_ok]
    status = report_status()
    have = pd.to_datetime(status.date)
    snaps = [("17:00", -1, "5pm day before"), ("11:00", 0, "11am"), ("13:00", 0, "1pm"),
             ("15:00", 0, "3pm"), ("17:00", 0, "5pm"), ("19:00", 0, "7pm")]
    out = []
    for season in pr.TEST:
        train = df[(df.season < season) & (df.season >= pr.TRAIN[0]) & df.min_ewm5.notna()]
        test = df[(df.season == season) & df.date.between(have.min(), have.max())]
        if test.empty:
            continue
        m_min = lgb.LGBMRegressor(**pr.PARAMS, random_state=1).fit(train[FEATURES_MIN], train["min"])
        tr = train[train["min"] >= 1]
        m_rate = {st: lgb.LGBMRegressor(**pr.PARAMS, random_state=2).fit(
            tr[FEATURES_RATE], tr[st] / tr["min"], sample_weight=tr["min"]) for st in pr.TARGETS}
        for hhmm, off, label in snaps:
            av = availability_at(test, status, hhmm, off)
            x = test.drop(columns=AVAIL).merge(av, on=["gameId", "teamId", "personId"], how="left")
            res = x[["gameId", "date", "season", "personId", "teamId", "own_status", "min", *pr.TARGETS]].copy()
            res["snapshot"] = label
            res["min_proj"] = np.clip(m_min.predict(x[FEATURES_MIN]), 0, 48)
            for st in pr.TARGETS:
                res[f"{st}_proj"] = res.min_proj * np.clip(m_rate[st].predict(x[FEATURES_RATE]), 0, None)
            out.append(res)
            print(f"{season}/{str(season + 1)[2:]} {label:<15} {len(res):,} player-games")
    out = pd.concat(out, ignore_index=True)
    out.to_parquet(DATA / "projections_at_report.parquet", index=False)


if __name__ == "__main__":
    main()
