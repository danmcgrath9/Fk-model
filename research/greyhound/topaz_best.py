"""The best model, live (19 Nov 2026, founder: "Port the best model into the morning program")

Test 98 (round 79): Test 88's fit with only the inputs known on a live morning made +365.5 units by the corrected BSP
over 21 months at the 2-point margin and a quarter of Kelly, about twice the corrected blend's. It reads ours with
Isolynx against TAB's opening book, the walk's form inputs, and TAB's own moves on each dog's earlier runs; it leaves
out every input built from BSP, which Betfair publishes a month late. This is that model fitted once on every race and
priced at TAB's open, beside the corrected blend (topaz_iso), with the same field, inputs and kept cards:

  - the market's history: each dog's earlier runs in Betwatch (TAB's move open to last, to its first change, the other
    books' opening prices against TAB's, and how many prices TAB showed), the last run and the mean of the last five,
    from runs on EARLIER days only. One function serves the training rows and the morning's runners, so the model is
    priced on inputs built exactly as it was trained on
  - the fit: Test 88's settings (learning rate 0.04, 15 leaves, up to 4,000 rounds, rounds chosen on the winners over
    the last three months), offset TAB's opening book, label BSP corrected (Test 80's label fit)
  - at TAB's open: the 2-point margin on TAB's first price, our fair price under $15, a quarter of Kelly capped at 5%
    of the bank; paper only

GRV's values are personal use: the model and its inputs live in this repository's Actions cache only, never in a log.
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_v1 as V1             # noqa: E402

MH = ("tab", "first", "books", "nfl")
MARGIN = 0.02
FAIR_UNDER = 15.0
KELLY, CAP = 0.25, 0.05
LEARNING_RATE, MAX_ROUNDS = 0.04, 4000
MODEL, META = "best.txt", "best_meta.json"


def runs_history(bw: pd.DataFrame) -> pd.DataFrame:
    """Each Betwatch run (topaz_round65.tab_and_books: date, _dn, TAB's first, last and first-changed prices, its price
    count, the other books' opening prices) as the market's history inputs: date, _dn, tab, first, books, nfl."""
    if bw is None or bw.empty:
        return pd.DataFrame(columns=["date", "_dn", *MH])
    op = bw.tab_first_bw.values.astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = pd.DataFrame({"date": pd.to_datetime(bw.date.values), "_dn": bw._dn.values,
                            "tab": np.log(op / bw.tab_last.values.astype(float)),
                            "first": np.log(op / bw.tab_change.values.astype(float)),
                            "books": np.log(op / bw.books_first.values.astype(float)),
                            "nfl": np.log1p(bw.tab_n.values.astype(float))})
    return out.replace([np.inf, -np.inf], np.nan)


def mh_for(keys: pd.DataFrame, hist: pd.DataFrame) -> pd.DataFrame:
    """For each key (date, _dn): the dog's last run on an EARLIER day and the mean of its last five, for every history
    input (mh_<x>_last, mh_<x>_mean5). Aligned to keys' rows; nan where the dog has no earlier run."""
    cols = [f"mh_{c}_{k}" for c in MH for k in ("last", "mean5")]
    out = pd.DataFrame(np.nan, index=np.arange(len(keys)), columns=cols)
    if hist is None or hist.empty or not len(keys):
        return out
    h = hist.dropna(subset=["date"]).sort_values(["_dn", "date"], kind="mergesort").reset_index(drop=True)
    h = h.drop_duplicates(["_dn", "date"], keep="last")
    g = h.groupby("_dn", sort=False)
    for c in MH:
        h[f"mh_{c}_last"] = h[c]
        h[f"mh_{c}_mean5"] = g[c].transform(lambda s: s.rolling(5, min_periods=1).mean())
    k = pd.DataFrame({"date": pd.to_datetime(keys.date.values), "_dn": keys._dn.values, "_i": np.arange(len(keys))})
    k = k.dropna(subset=["date"]).sort_values("date", kind="mergesort")
    m = pd.merge_asof(k, h[["date", "_dn", *cols]].sort_values("date", kind="mergesort"), on="date", by="_dn",
                      allow_exact_matches=False, direction="backward")
    out.loc[m._i.values, cols] = m[cols].values
    return out


def kelly(p: np.ndarray, price: np.ndarray) -> np.ndarray:
    """A quarter of Kelly as a share of the bank, capped: 0.25 (price p - 1) / (price - 1), at most 5%."""
    with np.errstate(divide="ignore", invalid="ignore"):
        f = KELLY * (price * p - 1) / (price - 1)
    return np.where(np.isfinite(f), np.clip(f, 0, CAP), 0.0)


def bets(p: np.ndarray, price: np.ndarray) -> np.ndarray:
    """The 2-point margin at TAB's price: our chance at least 2 points over the price's (1 / price), our fair price under
    $15, and a stake above zero."""
    p, price = np.asarray(p, float), np.asarray(price, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        ok = np.isfinite(p) & (p > 0) & (price > 1) & (p - 1 / price >= MARGIN - 1e-12) & (1 / p < FAIR_UNDER)
    return ok & (kelly(p, price) > 0)


def model_dir() -> Path:
    return Path(os.environ.get("MODEL_DIR", "greyhound/cache/model"))


def fit_best(R: pd.DataFrame, XR: pd.DataFrame, hist: pd.DataFrame, label_fit, val_months: int = 3) -> tuple:
    """Test 98's model on every race: the correction's inputs plus the market's history, offset TAB's opening book over
    the runners that ran, rounds chosen on the last val_months (winners), refitted on every race. (booster or None,
    meta)."""
    import topaz_round41 as R41
    import topaz_round62 as R62
    import gbm_v0
    mh = mh_for(pd.DataFrame({"date": R.date.values, "_dn": gbm_v0.norm_name(R.dog_name.fillna("")).values}), hist)
    X = pd.concat([XR.reset_index(drop=True), mh], axis=1)
    q, full, _ = R62.bsp_label(R, *label_fit)
    d, race, won = R.date.values, R.race_id.values, R.won.values.astype(float)
    off = X.lp_tab.values.astype(float)
    vs = (R.date.max().to_period("M") - (val_months - 1)).start_time.to_datetime64()
    a, v = full & (d < vs), d >= vs
    old = R41.MAX_ROUNDS, R41.PARAMS
    R41.MAX_ROUNDS, R41.PARAMS = MAX_ROUNDS, dict(R41.PARAMS, learning_rate=LEARNING_RATE)
    try:
        k, l0, lk = R41.choose_rounds((X[a], q[a], off[a], race[a]), (X[v], won[v], off[v], race[v]))
        bst = R41.fit(X[full], q[full], off[full], race[full], k)
    finally:
        R41.MAX_ROUNDS, R41.PARAMS = old
    meta = {"cols": list(X.columns), "rounds": int(k), "learning_rate": LEARNING_RATE, "label_fit": list(label_fit),
            "races": int(pd.unique(race[full]).size), "first_day": f"{R.date.min():%Y-%m-%d}",
            "last_day": f"{R.date.max():%Y-%m-%d}", "history_runs": int(len(hist)),
            "check": f"the last {val_months} months: TAB's book {l0:.4f}, the best model {lk:.4f}"}
    return bst, meta


def train_best(R: pd.DataFrame, XR: pd.DataFrame, bdir: str, label_fit, trained: str) -> str:
    """Fit and keep the best model beside the corrected blend (MODEL_DIR); a note for the log (counts only)."""
    import topaz_round65 as R65
    hist = runs_history(R65.tab_and_books(bdir))
    bst, meta = fit_best(R, XR, hist, label_fit)
    mdir = model_dir()
    mdir.mkdir(parents=True, exist_ok=True)
    if bst is not None:
        bst.save_model(str(mdir / MODEL))
    else:
        (mdir / MODEL).unlink(missing_ok=True)
    meta["trained"] = trained
    (mdir / META).write_text(json.dumps(meta))
    return (f"the best model: fitted on {meta['races']:,} races at TAB's first price ({meta['first_day']} to "
            f"{meta['last_day']}), {meta['rounds']} rounds ({meta['check']}); {len(meta['cols'])} inputs, "
            f"{meta['history_runs']:,} Betwatch runs of history")


def load_best():
    mf, jf = model_dir() / MODEL, model_dir() / META
    if not jf.exists():
        return None, None
    meta = json.loads(jf.read_text())
    if not mf.exists():
        return None, meta
    import lightgbm as lgb
    return lgb.Booster(model_file=str(mf)), meta


def at_open(x: pd.DataFrame, bst, meta: dict, hist: pd.DataFrame) -> pd.DataFrame:
    """The races topaz_iso.at_open priced (TAB's field at its first price, every dog on the kept card_iso), priced again
    by the best model: p_best, its bets at the 2-point margin and the quarter-Kelly stake at TAB's first price."""
    if x is None or x.empty or meta is None:
        return pd.DataFrame()
    import gbm_v0
    x = x.copy()
    XR = pd.DataFrame(index=x.index)
    mh = mh_for(pd.DataFrame({"date": pd.to_datetime(x.date).values,
                              "_dn": gbm_v0.norm_name(x.dog_name.fillna("")).values}), hist)
    mh.index = x.index
    for col in meta["cols"]:
        if col in mh:
            XR[col] = mh[col]
        elif col == "lp_ours":
            XR[col] = np.log(x.p_i_open.clip(1e-12))
        elif col == "lp_tab":
            XR[col] = np.log(x.p_tab_open.clip(1e-12))
        elif col == "gap":
            XR[col] = np.log(x.p_i_open.clip(1e-12)) - np.log(x.p_tab_open.clip(1e-12))
        elif col == "tab_book":
            XR[col] = (1 / x.price).groupby(x.bw_race).transform("sum")
        elif col == "s_later":
            XR[col] = 0.0
        elif col == "n_bet":
            XR[col] = x.groupby("bw_race").bw_race.transform("size").astype(float)
        else:
            XR[col] = x[f"x_{col}"] if f"x_{col}" in x else np.nan
    for col in V1.CAT:
        if col in XR:
            XR[col] = XR[col].astype("category")
    off = np.log(x.p_tab_open.clip(1e-12).values)
    raw = off + (bst.predict(XR[meta["cols"]], raw_score=True) if bst is not None and meta.get("rounds", 0) > 0 else 0)
    x["p_best"] = V1.race_softmax(raw, x.bw_race.values)
    price = x.price.values.astype(float)
    x["best_bet"] = bets(x.p_best.values, price)
    x["best_kelly"] = kelly(x.p_best.values, price)
    return x
