"""Our own greyhound ratings: Form King's job for dogs (research/greyhound/README.md, "Plan: our own base ratings";
MODELS_RESEARCH.md layers A to C). Built before Topaz arrives so that the day the key comes only the column mapping is
left: topaz_to_runs() is the one function that knows Topaz's names, and it is filled in from the probe's column list.

Everything works on a CANONICAL RUNS TABLE, one row per dog per race:
    race_id, meeting_id, date (datetime64), track, distance (int metres), grade (str), dog (str), box (int),
    finish (int, 1 = winner; NaN = did not finish), margin (lengths behind the winner; 0 for the winner),
    time (the dog's own run time in seconds, NaN if only the winner's is known), win_time (the race's winning time),
    split (first split in seconds, NaN if not timed), is_trial (bool)

POINT IN TIME, everywhere: a par or a rating used for a race is built only from races on EARLIER days. A meeting's
going variant is measured from that meeting itself, which is legitimate only because a run's rating is never used for
its own race, only as history for later ones (the gallops archive found 63% of stored race ratings moved after the
race; see research/form_gbm/README.md).

Pure: pandas and numpy only, no network.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SEC_PER_LENGTH = 0.07     # the usual greyhound conversion; one constant so a better figure is a one-line change
PAR_MIN = 20              # winners needed at a track and distance before it has a par
VARIANT_SHRINK = 2.0      # pseudo-races pulling a meeting's going variant toward 0 (a 1-race meeting is mostly noise)
ELO_START, ELO_K = 1500.0, 24.0


def dog_time(runs: pd.DataFrame) -> pd.Series:
    """The dog's own time: as recorded, else the winner's time plus its margin in lengths."""
    return runs["time"].fillna(runs["win_time"] + runs["margin"] * SEC_PER_LENGTH)


def _asof(left: pd.DataFrame, right: pd.DataFrame, by: list[str], col: str) -> pd.Series:
    """right[col] as it stood at the end of the last day BEFORE each left row's date (strictly earlier)."""
    l = left[by + ["date"]].reset_index().sort_values("date")
    r = right[by + ["date", col]].sort_values("date")
    m = pd.merge_asof(l, r, on="date", by=by, allow_exact_matches=False)
    return m.set_index("index")[col].reindex(left.index)


def pars(runs: pd.DataFrame, min_n: int = PAR_MIN) -> pd.DataFrame:
    """Point-in-time par per (track, distance): median winning time of earlier races (trials excluded), and median
    first split of every timed runner in earlier races. Returns columns par_time, par_split, aligned to runs."""
    races = runs[(runs.finish == 1) & ~runs.is_trial].drop_duplicates("race_id")
    races = races.sort_values("date")
    g = races.groupby(["track", "distance"])
    races = races.assign(par_time=g.win_time.transform(lambda s: s.expanding().median()),
                         n=g.cumcount() + 1)
    races.loc[races.n < min_n, "par_time"] = np.nan
    # one value per key per day (the last), so a same-day race never sees its own day
    day = races.groupby(["track", "distance", "date"]).par_time.last().reset_index()
    out = pd.DataFrame(index=runs.index)
    out["par_time"] = _asof(runs, day, ["track", "distance"], "par_time")

    timed = runs[runs.split.notna() & ~runs.is_trial].sort_values("date")
    gs = timed.groupby(["track", "distance"])
    timed = timed.assign(par_split=gs.split.transform(lambda s: s.expanding().median()), n=gs.cumcount() + 1)
    timed.loc[timed.n < min_n * 4, "par_split"] = np.nan          # splits are per runner, so ask for more of them
    sday = timed.groupby(["track", "distance", "date"]).par_split.last().reset_index()
    out["par_split"] = _asof(runs, sday, ["track", "distance"], "par_split")
    return out


def meeting_variant(runs: pd.DataFrame, par: pd.DataFrame, shrink: float = VARIANT_SHRINK) -> pd.DataFrame:
    """How fast the track ran that day, in seconds (positive = slow), from the meeting's own winners against par,
    shrunk toward 0 by `shrink` pseudo-races; the same for first splits from every timed runner."""
    df = runs.assign(par_time=par.par_time, par_split=par.par_split)
    w = df[(df.finish == 1) & ~df.is_trial & df.par_time.notna()].drop_duplicates("race_id")
    w = w.assign(resid=w.win_time - w.par_time)
    v = w.groupby("meeting_id").resid.agg(["sum", "count"])
    var_time = (v["sum"] / (v["count"] + shrink)).rename("variant_time")
    s = df[df.split.notna() & ~df.is_trial & df.par_split.notna()]
    s = s.assign(resid=s.split - s.par_split)
    vs = s.groupby("meeting_id").resid.agg(["sum", "count"])
    var_split = (vs["sum"] / (vs["count"] + shrink * 4)).rename("variant_split")
    out = pd.DataFrame(index=runs.index)
    out["variant_time"] = runs.meeting_id.map(var_time).fillna(0.0)
    out["variant_split"] = runs.meeting_id.map(var_split).fillna(0.0)
    return out


def run_ratings(runs: pd.DataFrame) -> pd.DataFrame:
    """Per run, in lengths (higher is better): time rating = (par + variant - the dog's time), split rating =
    (split par + split variant - the dog's first split). NaN where there is no par yet or no time."""
    par = pars(runs)
    var = meeting_variant(runs, par)
    t = dog_time(runs)
    out = pd.concat([par, var], axis=1)
    out["time_rating"] = (par.par_time + var.variant_time - t) / SEC_PER_LENGTH
    out["split_rating"] = (par.par_split + var.variant_split - runs.split) / SEC_PER_LENGTH
    out.loc[runs.finish.isna(), "time_rating"] = np.nan             # a dog that did not finish has no run time
    return out


def elo(runs: pd.DataFrame, k: float = ELO_K, start: float = ELO_START) -> pd.Series:
    """Who beat whom: every pair in a race is a match (lower finish wins, equal finish is a draw, a non-finisher
    loses to every finisher). Returns each runner's rating at the START OF THE DAY of the race; races are processed in
    date order and a day's changes apply when it ends; trials are skipped (they are not races). Zero-sum within a race."""
    order = runs[~runs.is_trial].sort_values(["date", "race_id"])
    dogs_all = order.dog.values
    pos_all = order.finish.fillna(99).values.astype(float)
    keys = order.race_id.values
    days = order.date.values
    cuts = np.flatnonzero(keys[1:] != keys[:-1]) + 1
    bounds = np.r_[0, cuts, len(order)]
    pre_vals = np.full(len(order), np.nan)
    r: dict = {}
    pending: dict = {}                     # a day's updates land when the day ends, so no race sees a same-day result
    for a, b in zip(bounds[:-1], bounds[1:]):
        if pending and days[a] != days[a - 1]:
            for d, delta in pending.items():
                r[d] = r.get(d, start) + delta
            pending = {}
        dogs = dogs_all[a:b]
        cur = np.array([r.get(d, start) for d in dogs])
        pre_vals[a:b] = cur
        n = b - a
        if n < 2:
            continue
        pos = pos_all[a:b]
        exp = 1 / (1 + 10 ** ((cur[None, :] - cur[:, None]) / 400))     # exp[i, j]: chance i beats j
        act = (pos[:, None] < pos[None, :]).astype(float) + 0.5 * (pos[:, None] == pos[None, :])
        np.fill_diagonal(exp, 0.0); np.fill_diagonal(act, 0.0)
        delta = k / (n - 1) * (act - exp).sum(axis=1)
        for d, v in zip(dogs, delta):
            pending[d] = pending.get(d, 0.0) + v
    pre = pd.Series(pre_vals, index=order.index).reindex(runs.index)
    return pre


def dog_form(runs: pd.DataFrame, rated: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Each runner's history as it stood at the END OF THE PREVIOUS DAY (so a second run on the same day never sees the
    first): last, mean and best of its last n time and split ratings, mean finish, runs, days since its last run,
    distance change, and its best trial split rating."""
    df = pd.concat([runs[["dog", "date", "race_id", "distance", "finish", "is_trial"]],
                    rated[["time_rating", "split_rating"]]], axis=1)
    races = df[~df.is_trial].sort_values(["dog", "date", "race_id"])
    g = races.groupby("dog", sort=False)
    cum = pd.DataFrame({"dog": races.dog, "date": races.date}, index=races.index)
    for c in ("time_rating", "split_rating"):
        roll = g[c].rolling(n, min_periods=1)
        cum[f"{c}_last"] = races[c]
        cum[f"{c}_mean{n}"] = roll.mean().reset_index(level=0, drop=True)
        cum[f"{c}_best{n}"] = roll.max().reset_index(level=0, drop=True)
    cum[f"finish_mean{n}"] = g.finish.rolling(n, min_periods=1).mean().reset_index(level=0, drop=True)
    cum["runs"] = g.cumcount() + 1
    cum["last_date"] = races.date
    cum["last_distance"] = races.distance
    day = cum.groupby(["dog", "date"]).last().reset_index()            # the dog's record at the end of each day
    out = pd.DataFrame(index=races.index)
    for c in [c for c in day.columns if c not in ("dog", "date")]:
        out[c] = _asof(races[["dog", "date"]], day, ["dog"], c)
    out["runs"] = out.runs.fillna(0)
    out["days_since"] = (races.date - out.pop("last_date")).dt.days
    out["dist_change"] = races.distance - out.pop("last_distance")
    # trials: the best split rating from any trial on an earlier day (a first starter's only form)
    tr = df[df.is_trial & df.split_rating.notna()][["dog", "date", "split_rating"]].sort_values("date")
    tr = tr.assign(trial_best=tr.groupby("dog").split_rating.cummax())
    tday = tr.groupby(["dog", "date"]).trial_best.last().reset_index()
    out["trial_split_best"] = _asof(races[["dog", "date"]], tday, ["dog"], "trial_best")
    return out.reindex(runs.index)


def topaz_to_runs(raw: pd.DataFrame) -> pd.DataFrame:
    """Topaz bulk runs to the canonical table. NOT WRITTEN YET, on purpose: the column names come from the first
    `gh topaz` probe, and guessing them would build the ratings on a mapping nobody has checked."""
    raise NotImplementedError("fill from the gh topaz probe's column list (research/greyhound/README.md)")
