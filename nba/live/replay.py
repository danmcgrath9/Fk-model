"""Replay the live pipeline on past days, with the injury report we hold for that hour, to
compare it with the research model on the same games. Usage: python nba/live/replay.py D1 D2 ..."""
import sys

import lightgbm as lgb
import numpy as np
import pandas as pd

import daily as d

sys.path.insert(0, str(d.HERE.parent))
import at_report as ar  # noqa: E402
import features as F  # noqa: E402
import project as pr  # noqa: E402


def run_day(raw, box_all, sched, day, hhmm="19:00"):
    games = d.slate(sched, day)
    box = box_all[box_all.date < day]
    rep = pd.read_csv(d.HERE.parent / f"injuries/raw/{day[:7]}.csv")
    rep = rep[rep.report_time == f"{day} {hhmm}"]
    tonight = d.placeholders(box, games, day, raw, rep)
    df = F.build(pd.concat([box, tonight.drop(columns=["tip"])], ignore_index=True))
    status = d.report_status(rep, tonight, day, hhmm)
    train = df[(df.date < pd.Timestamp(day)) & df.min_ewm5.notna() & df["min"].notna()]
    test = df[df.date == pd.Timestamp(day)].copy()
    av = ar.availability_at(test, status, hhmm, 0, prior=d.appear_rate(box, tonight))
    x = test.drop(columns=ar.AVAIL).merge(av, on=["gameId", "teamId", "personId"], how="left")
    m = lgb.LGBMRegressor(**pr.PARAMS, random_state=1).fit(train[F.FEATURES_MIN], train["min"])
    x["min_proj"] = np.clip(m.predict(x[F.FEATURES_MIN]), 0, 48)
    x = x[(x.min_ewm5 >= 20) & ~x.own_status.isin(["Out", "Doubtful"])]
    act = box_all[box_all.date == day][["personId", "min"]].rename(columns={"min": "actual"})
    j = x[["personId", "name", "team", "min_proj", "min_ewm5", "rot_present_min", "own_status"]].merge(act, on="personId", how="left")
    return j.assign(day=day, report_rows=len(rep), matched=len(status), candidates=len(tonight))


if __name__ == "__main__":
    days = sys.argv[1:]
    season = int(days[0][:4]) + 1
    raw, _ = d.load(season)
    sched = pd.read_parquet(d.fetch(f"espn_nba_schedules/nba_schedule_{season}.parquet", False))
    box_all = d.to_box(raw)
    out = pd.concat([run_day(raw, box_all, sched, dd) for dd in days])
    out.to_csv(d.HERE.parent / "data" / "replay.csv", index=False)
    played = out.actual.notna()
    print(out.groupby("day").agg(report_rows=("report_rows", "first"), matched=("matched", "first"),
                                 candidates=("candidates", "first"), projected=("personId", "size"),
                                 did_not_play=("actual", lambda s: s.isna().sum())).to_string())
    o = out[played]
    print(f"\nplayers who played: model miss {(o.min_proj - o.actual).abs().mean():.3f}, "
          f"recent-average miss {(o.min_ewm5 - o.actual).abs().mean():.3f}, bias {(o.min_proj - o.actual).mean():+.2f}")
