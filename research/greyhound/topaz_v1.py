"""Greyhound model v1: our own price from Topaz form, against GRV's starting price (4 Nov 2026, founder: "And then we
get to fucking work").

    python research/greyhound/topaz_v1.py DIR LABEL      (DIR: the pull's runs_<STATE>_<YYYY-MM>.json.gz files;
                                                           a LABEL containing since=YYYY-MM-DD keeps races from that day)

Prints results only (the workflow's mode=run throws the data away; GRV's data is personal use).

RACES: not trials, 4+ runners, exactly one winner, every runner with a starting price above $1.

FEATURES, all point in time (built only from EARLIER days; nothing from the race's own result or price):
- our ratings (greyhound/ratings.py): time rating and first-split rating in lengths, from track-and-distance pars and
  a meeting going variant (last, mean and best of the last 5), mean finish, runs, days since, distance change, best
  trial split, and the Elo over finishing order;
- the race card: box, field size, distance, track, grade, weight and its change since the dog's last run, age, sex;
- point-in-time rates: the trainer's strike rate, and the box's win rate at that track and distance against the
  field-size share.
Numeric features are also given relative to the race's field.

MODELS (LightGBM, softmax within the race, rounds chosen on the middle quarter):
- "form, trained on SP chances": the copy recipe that won on the free files (soft labels);
- "form, trained on winners": the fundamental model Benter's stage 1 asks for.
SCORED once on the last quarter, in two date halves: winner log loss against the SP's chances on the same races, then
Benter's stage 2 (each model blended with the SP, weights fitted on the middle quarter), and A/E of the runners our
model rates well above the SP. GRV's startPrice is the market here; Betfair's BSP is the next comparison.
"""
import os
import re
import sys

import numpy as np
import pandas as pd
import lightgbm as lgb
from scipy.optimize import minimize

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from greyhound.ratings import dog_form, elo, load_topaz, run_ratings   # noqa: E402

CAT = ["track", "grade", "sex"]
NUM = ["box", "field", "distance", "weight", "weight_change", "age_days", "trainer_rate", "trainer_runs", "box_ratio",
       "elo", "runs", "days_since", "dist_change", "finish_mean5", "trial_split_best",
       "time_rating_last", "time_rating_mean5", "time_rating_best5",
       "split_rating_last", "split_rating_mean5", "split_rating_best5"]
REL = ["elo", "time_rating_mean5", "time_rating_best5", "time_rating_last", "split_rating_mean5", "split_rating_best5",
       "finish_mean5", "trainer_rate", "box_ratio", "weight", "days_since"]


def prior_rate(df, keys, won):
    """Wins and runs for `keys` from EARLIER days only (a day's results land when the day ends)."""
    day = df.assign(_w=won).groupby(keys + ["date"], sort=True)._w.agg(["sum", "count"]).reset_index()
    g = day.groupby(keys)
    day["w"] = g["sum"].cumsum() - day["sum"]
    day["n"] = g["count"].cumsum() - day["count"]
    m = df[keys + ["date"]].merge(day[keys + ["date", "w", "n"]], on=keys + ["date"], how="left")
    return m.w.values, m.n.values


def build(d):
    runs = load_topaz(d)
    runs = runs[~runs.is_trial].reset_index(drop=True)
    for c in ("weight", "trainer_id", "whelped", "sex", "start_price"):   # optional Topaz fields
        if c not in runs:
            runs[c] = np.nan
    rated = run_ratings(runs)
    form = dog_form(runs, rated)
    runs["elo"] = elo(runs).values
    df = pd.concat([runs, form.drop(columns=[c for c in form.columns if c in runs.columns])], axis=1)
    df["won"] = (df.finish == 1).astype(int)
    df["field"] = df.groupby("race_id").dog.transform("size")
    df["sex"] = df.get("sex", pd.Series("", index=df.index)).fillna("").astype(str)
    df["age_days"] = (df.date - pd.to_datetime(df.whelped, errors="coerce", utc=True).dt.tz_convert(None)).dt.days
    df = df.sort_values(["dog", "date", "race_id"])
    df["weight_change"] = df.weight - df.groupby("dog").weight.shift()
    df = df.sort_values(["date", "race_id", "box"]).reset_index(drop=True)
    tw, tn = prior_rate(df.assign(trainer_id=df.trainer_id.fillna(-1)), ["trainer_id"], df.won.values)
    df["trainer_rate"], df["trainer_runs"] = np.where(tn >= 20, tw / np.maximum(tn, 1), np.nan), tn
    bw, bn = prior_rate(df, ["track", "distance", "box"], df.won.values)
    share = prior_rate(df.assign(_s=1 / df.field), ["track", "distance", "box"], (1 / df.field).values)[0]
    df["box_ratio"] = np.where(bn >= 50, bw / np.maximum(share, 1e-9), np.nan)
    # the races scored: one winner, 4+ runners, every runner priced
    g = df.groupby("race_id")
    ok = (g.won.transform("sum") == 1) & (g.dog.transform("size") >= 4) & g.start_price.transform(lambda s: (s > 1).all())
    df = df[ok].reset_index(drop=True)
    sp = 1 / df.start_price
    df["p_sp"] = sp / sp.groupby(df.race_id).transform("sum")
    return df


def features(df):
    X = df[NUM].astype(float).copy()
    for c in REL:
        X[f"{c}_rel"] = X[c] - X[c].groupby(df.race_id).transform("mean")
    for c in CAT:
        X[c] = df[c].astype("category")
    return X


def softmax_obj(groups):
    starts = np.r_[0, np.cumsum(groups)[:-1]]

    def obj(preds, data):
        y = data.get_label()
        e = np.exp(preds - np.repeat(np.maximum.reduceat(preds, starts), groups))
        p = e / np.repeat(np.add.reduceat(e, starts), groups)
        return p - y, np.maximum(p * (1 - p), 1e-6)
    return obj


def race_softmax(score, race):
    s = pd.Series(np.asarray(score))
    r = np.asarray(race)
    e = np.exp(s - s.groupby(r).transform("max").values)
    return (e / e.groupby(r).transform("sum").values).values


def ll(p, won):
    return -np.log(np.clip(np.asarray(p)[np.asarray(won) == 1], 1e-12, None)).mean()


def fit(X, y, race, Xv, wv, rv, rounds=1500):
    groups = race.groupby(race.values, sort=False).size().values
    params = dict(objective=softmax_obj(groups), learning_rate=0.05, num_leaves=63, min_data_in_leaf=300,
                  feature_fraction=0.6, bagging_fraction=0.8, bagging_freq=1, lambda_l2=10, verbose=-1, seed=1)
    bst = lgb.train(params, lgb.Dataset(X, y, categorical_feature=CAT, free_raw_data=False), num_boost_round=rounds)
    best = (np.inf, 100)
    for k in range(100, rounds + 1, 100):
        l = ll(race_softmax(bst.predict(Xv, num_iteration=k, raw_score=True), rv), wv)
        if l < best[0]:
            best = (l, k)
    return bst, best[1]


def blend(cols, df, w=None):
    def score(w):
        s = sum(wi * np.log(np.clip(df[c].values, 1e-12, None)) for wi, c in zip(w, cols))
        return race_softmax(s, df.race_id.values)
    if w is None:
        w = minimize(lambda w: ll(score(w), df.won.values), np.ones(len(cols)) / len(cols), method="Nelder-Mead").x
    return w, score(w)


def main(d, label):
    df = build(d)
    m = re.search(r"since=(\d{4}-\d{2}-\d{2})", label)
    if m:
        df = df[df.date >= m.group(1)].reset_index(drop=True)
    q50, q75 = df.date.quantile(0.5), df.date.quantile(0.75)
    tr, va, te = (df[df.date < q50], df[(df.date >= q50) & (df.date < q75)].copy(), df[df.date >= q75].copy())
    mid = te.date.quantile(0.5)
    h = te.date < mid
    print(f"# {label}: model v1 on Topaz form\n\n{df.race_id.nunique():,} races scored ({df.date.min():%Y-%m-%d} to "
          f"{df.date.max():%Y-%m-%d}); fit before {q50:%Y-%m-%d} ({tr.race_id.nunique():,}), choose and blend "
          f"{q50:%Y-%m-%d} to {q75:%Y-%m-%d} ({va.race_id.nunique():,}), score from {q75:%Y-%m-%d} "
          f"({te.race_id.nunique():,}; halves split {mid:%Y-%m-%d})\n")
    Xtr, Xva, Xte = features(tr), features(va), features(te)
    out = {}
    for name, target in (("form, trained on SP chances", "p_sp"), ("form, trained on winners", "won")):
        bst, k = fit(Xtr, tr[target].values.astype(float), tr.race_id, Xva, va.won.values, va.race_id.values)
        c = "p_" + re.sub(r"[^a-z]+", "_", name.split(",")[1].strip())
        va[c] = race_softmax(bst.predict(Xva, num_iteration=k, raw_score=True), va.race_id.values)
        te[c] = race_softmax(bst.predict(Xte, num_iteration=k, raw_score=True), te.race_id.values)
        out[name] = c
        imp = pd.Series(bst.feature_importance("gain"), index=Xtr.columns).sort_values(ascending=False)
        print(f"{name}: {k} rounds; top inputs: " + ", ".join(f"{i} {v / imp.sum():.0%}" for i, v in imp.head(8).items()))

    def row(name, p):
        p = np.asarray(p)
        return (f"| {name} | {ll(p, te.won.values):.4f} | {ll(p[h.values], te.won.values[h.values]):.4f} | "
                f"{ll(p[~h.values], te.won.values[~h.values]):.4f} |")

    field = te.groupby("race_id").dog.transform("size")
    print("\n## Last quarter, winner log loss (lower is better)\n\n| price | all | first half | second half |\n|---|---|---|---|")
    print(row("a random runner (1 / field)", 1 / field))
    for name, c in out.items():
        print(row(name, te[c]))
    print(row("GRV starting price", te.p_sp))

    print("\n## Benter's stage 2: blended with the SP, weights fitted on the middle quarter\n")
    print("| blend | weights | all | first half | second half | gain on the SP alone |\n|---|---|---|---|---|---|")
    base = ll(te.p_sp, te.won)
    for name, c in out.items():
        w, _ = blend([c, "p_sp"], va)
        _, p = blend([c, "p_sp"], te, w)
        r = row(f"{name} + SP", p).replace(f"| {name} + SP |", f"| {name} + SP | {w[0]:.3f} / {w[1]:.3f} |", 1)
        print(r + f" {base - ll(p, te.won):+.4f} |")

    print("\n## Where our chance is well above the SP's (back at SP, no commission: TAB fixed odds are not SP)\n")
    print("| model | our chance / SP chance | runners 1st / 2nd half | A/E 1st / 2nd | ROI at SP 1st / 2nd |")
    print("|---|---|---|---|---|")
    for name, c in out.items():
        for k in (1.2, 1.5):
            sel = te[te[c] >= k * te.p_sp]
            cells = []
            for half in (True, False):
                s = sel[(sel.date < mid) == half]
                ae = s.won.sum() / (1 / s.start_price).sum() if len(s) else np.nan
                roi = (np.where(s.won == 1, s.start_price - 1, -1)).mean() if len(s) else np.nan
                cells.append((len(s), ae, roi))
            print(f"| {name} | >= {k} | {cells[0][0]:,} / {cells[1][0]:,} | {cells[0][1]:.3f} / {cells[1][1]:.3f} | "
                  f"{cells[0][2]:+.1%} / {cells[1][2]:+.1%} |")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz v1")
