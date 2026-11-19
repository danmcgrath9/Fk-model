"""The band sheet, live: BetMatic orders for TAB's open, set the night before (20 Nov 2026, founder: "We need to create
like a betmatic sheet to bet before open"), paper only

Test 101 (round 82): a sheet set the night before kept about 95% of the best model's edge at TAB's open (+346.0 of
+364.3 corrected BSP units over 21 months) at the 2-point margin and a quarter of Kelly, without depending on anyone
seeing TAB's open quickly. This is that sheet, priced on the live models:

  - the TAB-open model: TAB's opening chance predicted from everything known the night before (the best model's inputs
    less the three built from TAB's price: lp_tab, gap, tab_book), fitted once on every race in the weekly train, as
    round 80 walked it (600 rounds, its settings), with TAB's usual book for each field size (the median over the six
    months to the last race) kept beside it
  - the rest of the field at the TAB-open model's predicted prices, not moving (Test 101's best sheet): each dog's own
    TAB price set to each of 28 ladder prices from $1.15 to $41, evenly spaced on a log scale, and the best model
    (topaz_best, Test 98) priced over the field at each one
  - a band is the price range between two neighbouring ladder prices. The dog gets an order on a band when the best
    model makes the bet at BOTH its ends (its chance at least 2 points over 1 / price, its fair price under $15), staked
    at the smaller quarter-Kelly share of the bank of the two ends (capped at 5%, as the morning program stakes). The
    bands tile the prices to the cent: a band from $a to $b fires on a TAB first price from a up to one cent under b
  - nothing is known of the dogs scratched after the open, so the price is TAB's as shown (round 82 judged the sheet on
    the price paid after TAB's deduction, which a sheet cannot know; with no scratching after the open they agree)

    sheet_for_day(day, cards_dir)   after topaz_iso.price has kept card_iso_DAY.csv.gz: the orders, kept beside it as
                                    sheet_DAY.csv.gz (Actions cache only) and returned for the sealed card
    train_tabopen(R, XR, bdir, ...) in the weekly train, after the best model: fit and keep tabopen.txt
    fired(sheet, facts, ...)        the morning program: each dog's order that TAB's first price falls in, as a paper bet

GRV's values are personal use: the sheet, the models and their inputs live in this repository's Actions cache only,
never in a log. The log prints counts.
"""
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_best                 # noqa: E402
import topaz_v1 as V1             # noqa: E402

GRID = np.geomspace(1.15, 41.0, 28)          # Test 101's ladder (round 81 and 82)
PRICE_COLS = ("lp_tab", "gap", "tab_book")   # the inputs built from TAB's price (round 80)
PRED_ROUNDS = 600                             # round 80's TAB-open model
PRED_PARAMS = dict(objective="regression", learning_rate=0.05, num_leaves=31, min_data_in_leaf=200,
                   feature_fraction=0.5, bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, verbose=-1, seed=1)
BOOK_MONTHS = 6
MIN_BOOK_RACES = 30
TABOPEN, TABOPEN_META = "tabopen.txt", "tabopen_meta.json"
SHEET = "Band sheet"


# ---- the TAB-open model, in the weekly train ------------------------------------------------------------------------

def usual_book(dates, race, tab_book, n_bet, months: int = BOOK_MONTHS) -> dict:
    """TAB's usual book (1 / price summed over the field at its first price): the median over the races in the `months`
    months to the last race, overall and for each field size with at least MIN_BOOK_RACES races."""
    r = pd.DataFrame({"date": pd.to_datetime(dates), "race": race, "book": np.asarray(tab_book, float),
                      "n": np.asarray(n_bet, float)}).drop_duplicates("race")
    r = r[np.isfinite(r.book) & (r.book > 0)]
    if r.empty:
        return {"all": float("nan"), "by_n": {}}
    last = r.date.max().to_period("M")
    w = r[r.date.dt.to_period("M") > last - months]
    by = w.groupby(w.n.astype(int)).book.agg(["median", "size"])
    return {"all": float(w.book.median()),
            "by_n": {str(int(n)): float(m) for n, (m, s) in by.iterrows() if s >= MIN_BOOK_RACES}}


def book_for(n: int, book: dict) -> float:
    return float(book.get("by_n", {}).get(str(int(n)), book.get("all", float("nan"))))


def fit_tabopen(R: pd.DataFrame, XR: pd.DataFrame, hist: pd.DataFrame, cols: list) -> tuple:
    """The TAB-open model on every race: the log of TAB's opening chance over the runners that ran, from the best
    model's inputs (cols) less PRICE_COLS. (booster, meta)."""
    import lightgbm as lgb
    import gbm_v0
    mh = topaz_best.mh_for(pd.DataFrame({"date": R.date.values, "_dn": gbm_v0.norm_name(R.dog_name.fillna("")).values}),
                           hist)
    X = pd.concat([XR.reset_index(drop=True), mh], axis=1)
    y = X.lp_tab.values.astype(float)
    use = [c for c in cols if c not in PRICE_COLS and c in X]
    cat = [c for c in V1.CAT if c in use]
    ok = np.isfinite(y)
    bst = lgb.train(PRED_PARAMS, lgb.Dataset(X.loc[ok, use], y[ok], categorical_feature=cat),
                    num_boost_round=PRED_ROUNDS)
    pred = bst.predict(X.loc[ok, use])
    meta = {"cols": use, "rounds": PRED_ROUNDS, "races": int(pd.unique(R.race_id.values[ok]).size),
            "first_day": f"{R.date.min():%Y-%m-%d}", "last_day": f"{R.date.max():%Y-%m-%d}",
            "book": usual_book(R.date.values, R.race_id.values, XR.tab_book.values, XR.n_bet.values),
            "check": f"in-sample miss of TAB's opening chance, median {np.median(np.abs(np.expm1(pred - y[ok]))):.1%}"}
    return bst, meta


def train_tabopen(R: pd.DataFrame, XR: pd.DataFrame, bdir: str, trained: str) -> str:
    """Fit and keep the TAB-open model beside the best model (MODEL_DIR), on the best model's inputs; a note for the
    log (counts only)."""
    import topaz_round65 as R65
    _, bmeta = topaz_best.load_best()
    if bmeta is None:
        return "the TAB-open model was not trained: no best model (best_meta.json) to take its inputs from"
    hist = topaz_best.runs_history(R65.tab_and_books(bdir))
    bst, meta = fit_tabopen(R, XR, hist, bmeta["cols"])
    mdir = topaz_best.model_dir()
    bst.save_model(str(mdir / TABOPEN))
    meta["trained"] = trained
    (mdir / TABOPEN_META).write_text(json.dumps(meta))
    nb = len(meta["book"]["by_n"])
    return (f"the TAB-open model (the band sheet's field): fitted on {meta['races']:,} races ({meta['first_day']} to "
            f"{meta['last_day']}), {meta['rounds']} rounds, {len(meta['cols'])} inputs; {meta['check']}; TAB's usual "
            f"book kept for {nb} field sizes")


def load_tabopen():
    mf, jf = topaz_best.model_dir() / TABOPEN, topaz_best.model_dir() / TABOPEN_META
    if not (mf.exists() and jf.exists()):
        return None, None
    import lightgbm as lgb
    return lgb.Booster(model_file=str(mf)), json.loads(jf.read_text())


# ---- the sheet, the night before -------------------------------------------------------------------------------------

def card_inputs(c: pd.DataFrame, cols: list, mh: pd.DataFrame) -> pd.DataFrame:
    """The best model's inputs for each runner on the kept card, as topaz_best.at_open builds them at TAB's open, with
    the inputs built from TAB's price left at zero (the ladder sets them) and nobody scratched later."""
    X = pd.DataFrame(index=c.index)
    lp_ours = np.log(c.p_i_open.clip(1e-12))
    for col in cols:
        if col in mh:
            X[col] = mh[col].values
        elif col == "lp_ours":
            X[col] = lp_ours
        elif col in PRICE_COLS or col == "s_later":
            X[col] = 0.0
        elif col == "n_bet":
            X[col] = c.groupby("race_key").race_key.transform("size").astype(float)
        else:
            X[col] = c[f"x_{col}"] if f"x_{col}" in c else np.nan
    for col in V1.CAT:
        if col in X:
            X[col] = X[col].astype("category")
    return X


def ladder_race(X: pd.DataFrame, lp_ours: np.ndarray, inv_pred: np.ndarray, bst, cols: list,
                grid: np.ndarray = GRID) -> np.ndarray:
    """One race: each runner's best-model chance (runners x ladder prices) with its own TAB price at each ladder price
    and the rest of the field at its predicted 1 / price (inv_pred), not moving. lp_tab, gap and tab_book are rebuilt
    for every runner of the field each time, as at TAB's open."""
    n, k = len(X), len(grid)
    own = np.repeat(np.arange(n), k * n)                 # the runner whose price is set
    g = np.tile(np.repeat(np.arange(k), n), n)           # the ladder price
    m = np.tile(np.arange(n), n * k)                     # each runner of the field priced with it
    inv = np.where(m == own, 1 / grid[g], inv_pred[m])
    gid = own * k + g
    s = np.bincount(gid, weights=inv, minlength=n * k)
    lp_tab = np.log(inv / s[gid])
    Z = X.iloc[m].reset_index(drop=True)
    for col, v in (("lp_tab", lp_tab), ("gap", lp_ours[m] - lp_tab), ("tab_book", s[gid])):
        if col in Z:
            Z[col] = v
    rounds = 0 if bst is None else 1
    raw = lp_tab + (bst.predict(Z[cols], raw_score=True) if rounds else 0.0)
    top = pd.Series(raw).groupby(gid).transform("max").values
    e = np.exp(raw - top)
    p = e / np.bincount(gid, weights=e, minlength=n * k)[gid]
    return p[m == own].reshape(n, k)


def bands(P: np.ndarray, grid: np.ndarray = GRID) -> list:
    """Each runner's orders from its ladder chances (runners x prices): [(runner, low, high, stake)], low and high in
    dollars to the cent (the order fires from low up to and including high), stake the quarter-Kelly share of the bank
    at the smaller of the band's two ends."""
    g = np.asarray(grid, float)[None, :]
    with np.errstate(divide="ignore", invalid="ignore"):
        ok = np.isfinite(P) & (P > 0) & (P - 1 / g >= topaz_best.MARGIN - 1e-12) & (1 / P < topaz_best.FAIR_UNDER)
    kel = topaz_best.kelly(np.where(np.isfinite(P), P, 0.0), np.broadcast_to(g, P.shape))
    cents = [math.ceil(round(v * 100, 6)) / 100 for v in grid]
    out = []
    for i in range(P.shape[0]):
        for j in range(len(cents) - 1):
            if ok[i, j] and ok[i, j + 1]:
                st = float(min(kel[i, j], kel[i, j + 1]))
                if st > 0:
                    out.append((i, cents[j], round(cents[j + 1] - 0.01, 2), round(st, 4)))
    return out


def build(cards: pd.DataFrame, bst, meta: dict, tob, tmeta: dict, mh_tab: pd.DataFrame) -> tuple:
    """The orders for every race on a day's kept card_iso whose every runner has our chance: (orders DataFrame, counts
    dict). Orders: day, race_key, venue, race_no, box, dog_name, dog, low, high, stake."""
    import gbm_v0
    c = cards.copy()
    c = c[c.p_iso.notna().groupby(c.race_key).transform("all").values].reset_index(drop=True)
    cols_o = ["day", "race_key", "venue", "race_no", "box", "dog_name", "dog", "low", "high", "stake"]
    if c.empty:
        return pd.DataFrame(columns=cols_o), {"races": 0, "dogs": 0, "orders": 0}
    c["p_i_open"] = c.p_iso / c.groupby("race_key").p_iso.transform("sum")
    mh = topaz_best.mh_for(pd.DataFrame({"date": pd.to_datetime(c.day).values,
                                         "_dn": gbm_v0.norm_name(c.dog_name.fillna("")).values}), mh_tab)
    X = card_inputs(c, meta["cols"], mh.reset_index(drop=True))
    T = X[tmeta["cols"]].copy()
    lp_pred = tob.predict(T)
    share = V1.race_softmax(lp_pred, c.race_key.values)
    nfield = c.groupby("race_key").race_key.transform("size").values
    book = np.array([book_for(n, tmeta["book"]) for n in nfield])
    inv_pred = book * share
    lp_ours = np.log(c.p_i_open.clip(1e-12).values)
    rows = []
    use = bst if meta.get("rounds", 0) > 0 else None
    for _, idx in c.groupby("race_key", sort=False).indices.items():
        idx = np.asarray(idx)
        if not np.isfinite(inv_pred[idx]).all():
            continue
        P = ladder_race(X.iloc[idx], lp_ours[idx], inv_pred[idx], use, meta["cols"])
        for i, lo, hi, st in bands(P):
            r = c.iloc[idx[i]]
            rows.append([r.day, r.race_key, r.venue, str(r.race_no), str(r.box), r.dog_name, str(r.dog), lo, hi, st])
    o = pd.DataFrame(rows, columns=cols_o)
    return o, {"races": int(c.race_key.nunique()), "dogs": int(o.groupby(["race_key", "dog"]).ngroups) if len(o) else 0,
               "orders": int(len(o))}


def sheet_path(cards_dir, day: str) -> Path:
    return Path(cards_dir) / f"sheet_{day}.csv.gz"


def sheet_for_day(day: str, cards_dir: str) -> tuple:
    """The night's sheet from the kept card_iso and the saved best and TAB-open models, kept as sheet_DAY.csv.gz
    (Actions cache only). (payload rows [venue, race_no, box, dog, low, high, stake], a note for the log: counts)."""
    import topaz_iso
    import topaz_round65 as R65
    bst, meta = topaz_best.load_best()
    if meta is None:
        return [], "no band sheet: no best model yet (best_meta.json in MODEL_DIR)"
    tob, tmeta = load_tabopen()
    if tob is None:
        return [], "no band sheet: no TAB-open model yet (tabopen.txt, from the weekly train)"
    bdir = os.environ.get("BETWATCH_DIR", "")
    if not bdir or not os.path.isdir(bdir):
        return [], "no band sheet: no Betwatch history (BETWATCH_DIR) for the best model's market inputs"
    cards = topaz_iso.iso_cards(cards_dir)
    cards = cards[cards.day.astype(str) == day] if len(cards) else cards
    if cards.empty:
        return [], f"no band sheet: no kept card_iso for {day}"
    hist = topaz_best.runs_history(R65.tab_and_books(bdir))
    o, n = build(cards, bst, meta, tob, tmeta, topaz_best.mh_table(hist))
    f = sheet_path(cards_dir, day)
    o.to_csv(f, index=False, compression="gzip")
    rows = [[r.venue, r.race_no, r.box, r.dog_name, float(r.low), float(r.high), float(r.stake)]
            for r in o.itertuples()]
    per = o.groupby(["race_key", "dog"]).size() if len(o) else pd.Series(dtype=int)
    return rows, (f"the band sheet kept (Actions cache only): {f.name}; {n['races']} races priced, {n['dogs']} dogs "
                  f"given orders, {n['orders']} orders (a dog carries a median {int(per.median()) if len(per) else 0}, "
                  f"at most {int(per.max()) if len(per) else 0}); TAB-open model trained {tmeta.get('trained', '?')}")


def load_sheet(cards_dir: str, day: str) -> pd.DataFrame:
    f = sheet_path(cards_dir, day) if cards_dir else None
    if f is None or not f.exists():
        return pd.DataFrame()
    return pd.read_csv(f, dtype={"race_no": str, "box": str, "dog": str})


# ---- the morning: which order TAB's first price fires ---------------------------------------------------------------

def fired(sheet: pd.DataFrame, facts: pd.DataFrame) -> list:
    """Each dog on the sheet whose race TAB has priced (facts: TAB's field at its first price, one race per bw_race),
    and the order its first price falls in: [{dog, box, card race, low, high, stake, TAB's first price and when}].
    Matched on the normalised name within the day (a name twice in a day is left out, as the tracker does)."""
    if sheet is None or sheet.empty or facts is None or facts.empty:
        return []
    import topaz_track as Tk
    f = facts.assign(_dn=Tk.norm(facts.dog_name))
    f = f.drop_duplicates(["date", "_dn"], keep=False) if "date" in f else f.drop_duplicates("_dn", keep=False)
    s = sheet.assign(_dn=Tk.norm(sheet.dog_name))
    once = s.groupby("_dn").race_key.transform("nunique") == 1
    s = s[once.values]
    x = s.merge(f[["_dn", "price", "tab_first_t", "venue", "race_no", "start", "bw_race"]].rename(
        columns={"venue": "bw_venue", "race_no": "bw_race_no"}), on="_dn", how="inner")
    x = x[(x.price >= x.low - 1e-9) & (x.price <= x.high + 1e-9)]
    out = []
    for r in x.itertuples():
        out.append({"model": SHEET, "venue": r.bw_venue, "race_no": str(r.bw_race_no), "start": r.start,
                    "box": str(r.box), "dog": r.dog_name, "low": float(r.low), "high": float(r.high),
                    "kelly": float(r.stake), "tab_open": float(r.price), "tab_open_at": r.tab_first_t,
                    "bw_race": r.bw_race})
    return sorted(out, key=lambda b: str(b["start"]))
