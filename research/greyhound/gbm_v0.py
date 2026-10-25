"""Greyhound model v0: our own price from Betfair's free files and Iggy's early-speed ratings, no Topaz yet
(25 Oct 2026, founder: "we want to build our own model to be better than Iggy and we can bet early").

    python research/greyhound/gbm_v0.py DIR LABEL        (a LABEL containing since=YYYY-MM-DD keeps races from that day)

DIR holds the ANZ_Greyhounds files and the Iggy_Model*_Results files. Australian races only, 4+ runners with a BSP,
exactly one winner.

FEATURES, all point-in-time (a dog's history uses only its runs on EARLIER days; the race's own prices never enter):
- the dog's history from the Betfair files, keyed by its name (Betfair selection ids are not stable per dog): runs,
  wins, places, recent results, its past BSPs (the market's view of it), how it ran against what the market expected
  (won minus 1/BSP), days since its last run, last box, distance change, same track as last time;
- the race: box, field size, distance, track, state, grade, the point-in-time box rate for that track and distance
  (from t_box_bias.py);
- Iggy's Early Speed rating for this race, its rank in the field, and the early speed of the dogs either side
  (crowding at the first bend). Iggy publishes before the race; a leak check below tests that the rating does not
  know the result.
Each numeric feature is also given relative to the race's own field (value minus the race mean).

MODEL (the gallops recipe, research/form_gbm/README.md): LightGBM with a softmax-within-race objective trained against
the BSP's chances (soft labels: every runner carries a target, not only the winner); a second fit against the winner
only, for comparison. Split by date: fit on races before the 50th percentile date, choose blend weights on the 50th to
75th, score once on the last quarter, which is also cut into two halves.

SCORED: winner log loss of the model, Iggy, BSP and the pre-play WAP on the same races; the model blended with BSP;
by month. No opening price exists in these files, so this says how good the price is, not whether it beats the open."""
import io, os, re, sys, zipfile
import numpy as np, pandas as pd
import lightgbm as lgb
from scipy.optimize import minimize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_box_bias import point_in_time_ratio                                    # noqa: E402


def read_all(d, pattern):
    fs = []
    for name in sorted(os.listdir(d)):
        if not re.search(pattern, name):
            continue
        p = os.path.join(d, name)
        if name.endswith(".zip"):
            with zipfile.ZipFile(p) as z:
                fs += [pd.read_csv(io.BytesIO(z.read(m)), low_memory=False) for m in z.namelist() if m.endswith(".csv")]
        elif name.endswith(".csv"):
            fs.append(pd.read_csv(p, low_memory=False))
    return pd.concat(fs, ignore_index=True) if fs else pd.DataFrame()


def norm_name(s):
    return s.astype(str).str.replace(r"^\d+\.\s*", "", regex=True).str.upper().str.replace(r"[^A-Z0-9]", "", regex=True)


GRADES = ["MDN", "GR5", "GR4/5", "HEAT", "REST", "GR6", "FFA", "FINAL", "NVCE", "C1", "GR6/7", "N/G", "GR7", "GR3/4",
          "GR4", "C2", "C0", "GR5/6", "C3", "M5", "C5", "C4"]


def load(d):
    df = read_all(d, r"^ANZ_Greyhounds").drop_duplicates(["WIN_MARKET_ID", "SELECTION_ID"])
    raw = df.LOCAL_MEETING_DATE.astype(str).str.strip()
    df["date"] = pd.to_datetime(raw, errors="coerce", format="%d/%m/%Y").fillna(
        pd.to_datetime(raw.str[:10], errors="coerce", format="%Y-%m-%d"))
    for c in ("WIN_BSP", "WIN_PREPLAY_WEIGHTED_AVERAGE_PRICE_TAKEN", "TAB_NUMBER", "DISTANCE", "WIN_MARKET_ID",
              "SELECTION_ID"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["won"] = (df.WIN_RESULT == "WINNER").astype(int)
    df["placed"] = (df.PLACE_RESULT == "WINNER").astype(int)
    df = df[(df.STATE_CODE != "NZ") & df.date.notna()]
    df["dog"] = norm_name(df.SELECTION_NAME)
    df["t"] = pd.to_datetime(df.SCHEDULED_RACE_TIME.astype(str), format="%I:%M:%S %p", errors="coerce").dt.time
    return df


def dog_history(all_runs):
    """Point-in-time history per dog from every run in the files (any BSP), counting only EARLIER days."""
    r = all_runs[["dog", "date", "t", "WIN_MARKET_ID", "SELECTION_ID", "won", "placed", "WIN_BSP", "TAB_NUMBER",
                  "DISTANCE", "TRACK"]].copy()
    r = r.sort_values(["dog", "date", "t"], na_position="first").reset_index(drop=True)
    r["lbsp"] = np.log(r.WIN_BSP.where(r.WIN_BSP > 1))
    r["surprise"] = r.won - (1 / r.WIN_BSP.where(r.WIN_BSP > 1))
    g = r.groupby("dog", sort=False)
    # a dog runs at most once a day, so shifting by one row within the dog is "earlier days only"
    for c in ("won", "placed", "lbsp", "surprise", "date", "TAB_NUMBER", "DISTANCE", "TRACK"):
        r[f"prev_{c}"] = g[c].shift(1)
    r["runs"] = g.cumcount()
    r["wins"] = g.won.cumsum() - r.won
    r["places"] = g.placed.cumsum() - r.placed
    roll = lambda c, n, f: r.groupby("dog", sort=False)[c].rolling(n, min_periods=1).agg(f).reset_index(level=0, drop=True)
    r["lbsp_m5"] = roll("prev_lbsp", 5, "mean")
    r["lbsp_min5"] = roll("prev_lbsp", 5, "min")
    r["surprise_s5"] = roll("prev_surprise", 5, "sum")
    r["won_s5"] = roll("prev_won", 5, "sum")
    r["placed_s5"] = roll("prev_placed", 5, "sum")
    r["days_since"] = (r.date - r.prev_date).dt.days
    r["win_rate"] = r.wins / r.runs.where(r.runs > 0)
    r["place_rate"] = r.places / r.runs.where(r.runs > 0)
    r["dist_change"] = r.DISTANCE - r.prev_DISTANCE
    r["same_track"] = (r.TRACK == r.prev_TRACK).astype(float).where(r.prev_TRACK.notna())
    keep = ["WIN_MARKET_ID", "SELECTION_ID", "runs", "wins", "win_rate", "place_rate", "prev_won", "prev_placed",
            "won_s5", "placed_s5", "prev_lbsp", "lbsp_m5", "lbsp_min5", "surprise_s5", "days_since", "prev_TAB_NUMBER",
            "dist_change", "same_track"]
    return r[keep]


def iggy_speed(d):
    ig = read_all(d, r"^Iggy_Model")
    if ig.empty or "Early Speed" not in ig.columns:
        print("no Iggy Early Speed column: running without it")
        return None
    ig = ig.rename(columns={"MarketId": "WIN_MARKET_ID", "SelectionId": "SELECTION_ID", "Early Speed": "early_speed",
                            "Rated Price": "iggy_price"})
    for c in ("WIN_MARKET_ID", "SELECTION_ID", "early_speed", "iggy_price"):
        ig[c] = pd.to_numeric(ig[c], errors="coerce")
    return ig[["WIN_MARKET_ID", "SELECTION_ID", "early_speed", "iggy_price"]].drop_duplicates(
        ["WIN_MARKET_ID", "SELECTION_ID"], keep="last")


def build(d):
    runs = load(d)
    hist = dog_history(runs)
    df = runs[runs.WIN_BSP > 1]
    g = df.groupby("WIN_MARKET_ID")
    df = df[(g.won.transform("sum") == 1) & (g.WIN_BSP.transform("size") >= 4)].copy()
    df = df.merge(hist, on=["WIN_MARKET_ID", "SELECTION_ID"], how="left")
    df["box"] = df.TAB_NUMBER
    df["real_box"] = df.box.between(1, 8)
    df["dist"] = df.DISTANCE.round().astype("Int64")
    df["td"] = df.TRACK.astype(str) + " " + df.dist.astype(str) + "m"
    df["field"] = df.groupby("WIN_MARKET_ID").WIN_BSP.transform("size")
    df["p_bsp"] = (1 / df.WIN_BSP) / (1 / df.WIN_BSP).groupby(df.WIN_MARKET_ID).transform("sum")
    wap = 1 / df.WIN_PREPLAY_WEIGHTED_AVERAGE_PRICE_TAKEN.where(df.WIN_PREPLAY_WEIGHTED_AVERAGE_PRICE_TAKEN > 1)
    df["p_wap"] = wap / wap.groupby(df.WIN_MARKET_ID).transform("sum")
    df = df.sort_values(["date", "WIN_MARKET_ID"]).reset_index(drop=True)
    df = point_in_time_ratio(df)
    ig = iggy_speed(d)
    if ig is not None:
        df = df.merge(ig, on=["WIN_MARKET_ID", "SELECTION_ID"], how="left")
        df["es_rank"] = df.groupby("WIN_MARKET_ID").early_speed.rank(ascending=False)
        # early speed of the dogs in the boxes either side (first-bend crowding)
        key = df[["WIN_MARKET_ID", "box", "early_speed"]].dropna()
        for side, off in (("in", -1), ("out", 1)):
            k = key.assign(box=key.box - off).rename(columns={"early_speed": f"es_{side}"})
            df = df.merge(k, on=["WIN_MARKET_ID", "box"], how="left")
        ip = 1 / df.iggy_price.where(df.iggy_price > 1)
        df["p_iggy"] = ip / ip.groupby(df.WIN_MARKET_ID).transform("sum")
    df["grade"] = df.RACE_TYPE.astype(str).str.upper().str.strip()
    df.loc[~df.grade.isin(GRADES), "grade"] = "OTHER"
    return df


NUM = ["box", "field", "DISTANCE", "box_ratio", "runs", "wins", "win_rate", "place_rate", "prev_won", "prev_placed",
       "won_s5", "placed_s5", "prev_lbsp", "lbsp_m5", "lbsp_min5", "surprise_s5", "days_since", "prev_TAB_NUMBER",
       "dist_change", "same_track"]
IGGY = ["early_speed", "es_rank", "es_in", "es_out"]
REL = ["box_ratio", "win_rate", "place_rate", "prev_lbsp", "lbsp_m5", "lbsp_min5", "surprise_s5", "days_since",
       "early_speed"]
CAT = ["TRACK", "STATE_CODE", "grade"]


def features(df, use_iggy):
    X = df[NUM + (IGGY if use_iggy else [])].astype(float).copy()
    for c in REL:
        if c in X:
            X[f"{c}_rel"] = X[c] - X[c].groupby(df.WIN_MARKET_ID).transform("mean")
    for c in CAT:
        X[c] = df[c].astype("category")
    return X


def softmax_obj(groups):
    """Softmax within each race; the label is the target chance (soft, sums to 1 per race)."""
    starts = np.r_[0, np.cumsum(groups)[:-1]]

    def obj(preds, data):
        y = data.get_label()
        e = np.exp(preds - np.repeat(np.maximum.reduceat(preds, starts), groups))
        p = e / np.repeat(np.add.reduceat(e, starts), groups)
        return p - y, np.maximum(p * (1 - p), 1e-6)
    return obj


def race_softmax(score, race):
    s = pd.Series(score)
    e = np.exp(s - s.groupby(race.values).transform("max").values)
    return (e / e.groupby(race.values).transform("sum").values).values


def fit(X, y, race, valid=None, rounds=1000):
    groups = race.groupby(race.values, sort=False).size().values
    params = dict(objective=softmax_obj(groups), learning_rate=0.08, num_leaves=63, min_data_in_leaf=200,
                  feature_fraction=0.5, bagging_fraction=0.8, bagging_freq=1, lambda_l2=10, verbose=-1, seed=1)
    ds = lgb.Dataset(X, y, categorical_feature=CAT, free_raw_data=False)
    if valid is None:
        return lgb.train(params, ds, num_boost_round=rounds)
    Xv, yv, rv = valid
    best = (np.inf, 0)
    bst = lgb.train(params, ds, num_boost_round=rounds)
    for k in range(100, rounds + 1, 100):                       # rounds chosen on the validation period
        p = race_softmax(bst.predict(Xv, num_iteration=k, raw_score=True), rv)
        l = -np.log(np.clip(p[yv == 1], 1e-12, None)).mean()
        if l < best[0]:
            best = (l, k)
    return bst, best[1]


def ll(p, won):
    return -np.log(np.clip(p[won == 1], 1e-12, None)).mean()


def blend_fit(cols, df):
    def nll(w):
        s = sum(wi * np.log(np.clip(df[c].values, 1e-12, None)) for wi, c in zip(w, cols))
        return ll(race_softmax(s, df.WIN_MARKET_ID), df.won.values)
    return minimize(nll, np.ones(len(cols)) / len(cols), method="Nelder-Mead").x


def blend_apply(w, cols, df):
    s = sum(wi * np.log(np.clip(df[c].values, 1e-12, None)) for wi, c in zip(w, cols))
    return race_softmax(s, df.WIN_MARKET_ID)


def main(d, label):
    df = build(d)
    m = re.search(r"since=(\d{4}-\d{2}-\d{2})", label)
    if m:   # Iggy's Early Speed exists only from Jan 2024, so its test needs a window that starts there
        df = df[df.date >= m.group(1)].reset_index(drop=True)
    has_iggy = "p_iggy" in df
    q50, q75 = df.date.quantile(0.5), df.date.quantile(0.75)
    tr, va, te = df[df.date < q50], df[(df.date >= q50) & (df.date < q75)], df[df.date >= q75].copy()
    print(f"# {label}: greyhound model v0\n\nraces {df.WIN_MARKET_ID.nunique():,}; fit before {q50:%Y-%m-%d} "
          f"({tr.WIN_MARKET_ID.nunique():,}), blend and rounds {q50:%Y-%m-%d} to {q75:%Y-%m-%d} "
          f"({va.WIN_MARKET_ID.nunique():,}), scored from {q75:%Y-%m-%d} ({te.WIN_MARKET_ID.nunique():,})\n")
    if has_iggy:
        # leak check: if Iggy's early speed knew the result, the fastest-rated dog would win far above its BSP chance
        x = df[df.es_rank == 1]
        print(f"leak check, top early-speed dog: wins {x.won.mean():.1%}, BSP chance {x.p_bsp.mean():.1%}, "
              f"A/E {x.won.sum() / x.p_bsp.sum():.3f} (a leak would show as far above 1)\n")

    rows = {}
    for name, use_iggy, target in (("v0 soft (BSP chances)", False, "p_bsp"), ("v0 hard (winner)", False, "won"),
                                   ("v0 soft + Iggy early speed", True, "p_bsp")):
        if use_iggy and not has_iggy:
            continue
        Xtr, Xva, Xte = (features(x, use_iggy) for x in (tr, va, te))
        bst, k = fit(Xtr, tr[target].values.astype(float), tr.WIN_MARKET_ID, (Xva, va.won.values, va.WIN_MARKET_ID))
        col = "p_" + re.sub(r"[^a-z0-9]", "_", name.lower())
        va = va.assign(**{col: race_softmax(bst.predict(Xva, num_iteration=k, raw_score=True), va.WIN_MARKET_ID)})
        te[col] = race_softmax(bst.predict(Xte, num_iteration=k, raw_score=True), te.WIN_MARKET_ID)
        rows[name] = col
        imp = pd.Series(bst.feature_importance("gain"), index=Xtr.columns).sort_values(ascending=False)
        print(f"{name}: {k} rounds; top inputs: " + ", ".join(f"{c} {v / imp.sum():.0%}" for c, v in imp.head(8).items()))

    ok = te.p_wap.notna().groupby(te.WIN_MARKET_ID).transform("all")
    if has_iggy:
        ok &= te.p_iggy.notna().groupby(te.WIN_MARKET_ID).transform("all")
    s = te[ok]
    print(f"\n## Winner log loss, last quarter, the same {s.WIN_MARKET_ID.nunique():,} races (lower is sharper)\n")
    print("| price | all | first half | second half |\n|---|---|---|---|")
    mid = s.date.quantile(0.5)
    cols = list(rows.items()) + [("Iggy", "p_iggy")] * has_iggy + [("pre-play WAP", "p_wap"), ("BSP", "p_bsp")]
    for name, c in cols:
        print(f"| {name} | {ll(s[c].values, s.won.values):.4f} | {ll(s[s.date < mid][c].values, s[s.date < mid].won.values):.4f} | "
              f"{ll(s[s.date >= mid][c].values, s[s.date >= mid].won.values):.4f} |")

    best = list(rows.values())[-1]
    print(f"\n## Our price blended with the market (weights fitted on the middle quarter, scored on the last)\n")
    print("| blend | weights | log loss | gain on the market alone |\n|---|---|---|---|")
    for mkt in ("p_wap", "p_bsp"):
        vv = va[va[mkt].notna().groupby(va.WIN_MARKET_ID).transform("all")]
        w = blend_fit([best, mkt], vv)
        p = blend_apply(w, [best, mkt], s)
        print(f"| ours + {mkt[2:].upper()} | {w[0]:.3f} / {w[1]:.3f} | {ll(p, s.won.values):.4f} | "
              f"{ll(s[mkt].values, s.won.values) - ll(p, s.won.values):+.4f} |")

    print("\n## By month, last quarter\n\n| month | races | ours | " + ("Iggy | " if has_iggy else "") + "BSP |")
    print("|---|---|---|" + ("---|" if has_iggy else "") + "---|")
    for m, x in s.groupby(s.date.dt.strftime("%Y-%m")):
        print(f"| {m} | {x.WIN_MARKET_ID.nunique():,} | {ll(x[best].values, x.won.values):.4f} | "
              + (f"{ll(x.p_iggy.values, x.won.values):.4f} | " if has_iggy else "") + f"{ll(x.p_bsp.values, x.won.values):.4f} |")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "greyhounds")
