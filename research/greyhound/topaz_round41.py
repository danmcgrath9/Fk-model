"""Round 41: what does TAB's opening book get wrong that ours could learn? (16 Nov 2026, founder: "Well keep testing
and lets get a fucking good model")

Test 58: refitting ours more often closed about a third of the gap to TAB's first book and barely moved the bets, so
the rest of the gap is in what ours knows, not in how fresh it is. Every blend so far is two numbers, a weight on ours
and a weight on TAB's first book, the same for every race. Here a second model starts FROM that blend (Test 51's held
weights, 0.54 / 0.67) and learns only where it is wrong: a gradient-boosted correction over every input ours has, plus
ours and TAB's first book themselves, how far apart they are, and TAB's opening overround. Two labels:

  - the winners: where the blend is wrong about who wins
  - BSP: where the market closes against the blend (races with a BSP on every runner that ran)

Walked forward: refitted every two months from November 2024 on the races at TAB's first price before it. The number of
rounds is chosen on the three months before each refit (the correction fitted on the months before those, scored on
the winners' log loss there, none at all if no round beats the blend), and the correction is then refitted on every
race before the refit month with that many rounds, so nothing it prices has been seen. Then log loss and the card's
rule at 1.3x at TAB's first price after the deduction, as in Test 58.

The correction redistributes only the share of the runners that ran; a dog scratched after the open keeps the blend's
chance, so the rule sees the field as it stood at the bet, as before.

    python research/greyhound/topaz_round41.py DIR LABEL    (as round 40; WALK_CACHE_USE names the six-month walk)

Counts, sums and rates only: no race, dog or price is printed. The correction's inputs are named with their share of
its gain (they are the model's inputs, not data).
"""
import os
import sys
import time

import lightgbm as lgb
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round33 as R33       # noqa: E402
import topaz_round36 as R36       # noqa: E402
import topaz_round38 as R38       # noqa: E402
import topaz_round40 as R40       # noqa: E402
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402

FROM = "2024-11"                  # first month the correction prices (as round 40)
BW_FROM = "2023-04-01"            # Betwatch's history starts in May 2023
EVERY = 2                         # refit every two months
VAL_MONTHS = 3                    # rounds chosen on the three months before each refit
FIXED = (0.54, 0.67)              # Test 51's held weights: the blend the correction starts from
MAX_ROUNDS = 1200
STEP = 25
PARAMS = dict(learning_rate=0.02, num_leaves=15, min_data_in_leaf=500, feature_fraction=0.5, bagging_fraction=0.8,
              bagging_freq=1, lambda_l2=20.0, verbose=-1, seed=1, metric="None")
EXTRA = ["lp_ours", "lp_tab", "gap", "tab_book", "s_later", "n_bet"]
PERIODS = R40.PERIODS


def groups_of(race) -> np.ndarray:
    """Runners per race, in row order; every race's rows must sit together (the race softmax needs it)."""
    r = np.asarray(race)
    if not len(r):
        return np.zeros(0, int)
    first = np.flatnonzero(np.r_[True, r[1:] != r[:-1]])
    if len(first) != len(pd.unique(r)):
        raise ValueError("a race's rows are not together")
    return np.diff(np.r_[first, len(r)])


def offset_obj(offset: np.ndarray, groups: np.ndarray):
    """The race softmax on (offset + the trees' score): the trees learn only the correction to the offset."""
    starts = np.r_[0, np.cumsum(groups)[:-1]]

    def obj(preds, data):
        y = data.get_label()
        s = preds + offset
        e = np.exp(s - np.repeat(np.maximum.reduceat(s, starts), groups))
        p = e / np.repeat(np.add.reduceat(e, starts), groups)
        return p - y, np.maximum(p * (1 - p), 1e-6)
    return obj


def fit(X: pd.DataFrame, y: np.ndarray, offset: np.ndarray, race, rounds: int):
    """The correction, `rounds` trees on top of the offset; None for no rounds (the offset itself)."""
    if rounds <= 0 or not len(X):
        return None
    params = dict(PARAMS, objective=offset_obj(np.asarray(offset, float), groups_of(race)))
    cat = [c for c in V1.CAT if c in X]
    return lgb.train(params, lgb.Dataset(X, np.asarray(y, float), categorical_feature=cat, free_raw_data=False),
                     num_boost_round=rounds)


def score(bst, X: pd.DataFrame, offset: np.ndarray, race, k=None) -> np.ndarray:
    """Chances over each race's rows: the offset, plus the correction's first k trees (all of them when k is None)."""
    raw = np.asarray(offset, float)
    if bst is not None:
        raw = raw + bst.predict(X, num_iteration=k, raw_score=True)
    return V1.race_softmax(raw, np.asarray(race))


def choose_rounds(fit_rows: tuple, val_rows: tuple):
    """Rounds of correction that minimise the winners' log loss on the validation rows (0 when none beats the
    offset). Each is (X, label, offset, race), the validation label being the winners. Returns (rounds, log loss of
    the offset alone, log loss at the rounds chosen)."""
    Xv, wv, ov, rv = val_rows
    base = V1.ll(score(None, Xv, ov, rv), wv)
    if not len(fit_rows[0]) or not len(Xv):
        return 0, base, base
    bst = fit(*fit_rows, MAX_ROUNDS)
    best_l, best_k = base, 0
    for k in range(STEP, MAX_ROUNDS + 1, STEP):
        lk = V1.ll(score(bst, Xv, ov, rv, k), wv)
        if lk < best_l - 1e-6:
            best_l, best_k = lk, k
    return best_k, base, best_l


def walk_correction(R: pd.DataFrame, X: pd.DataFrame, label: np.ndarray, use: np.ndarray):
    """The correction walked forward over R (runners that ran, races together, with date, race_id, won, off): refit
    every EVERY months from FROM on the `use` rows before the month, rounds chosen on the VAL_MONTHS before it.
    Returns the chances over each race's runners that ran (nan before FROM), the refit log and the mean gain share by
    input over the refits that kept any rounds."""
    d, race, off, won = R.date.values, R.race_id.values, R.off.values, R.won.values.astype(float)
    p = np.full(len(R), np.nan)
    log, bst, fitted, gains = [], None, None, []
    for M in pd.period_range(FROM, R.date.max().to_period("M"), freq="M"):
        start, end = M.start_time.to_datetime64(), (M + 1).start_time.to_datetime64()
        pr = (d >= start) & (d < end)
        if not pr.any():
            continue
        if fitted is None or (M - fitted).n >= EVERY:
            vs = (M - VAL_MONTHS).start_time.to_datetime64()
            a, v = use & (d < vs), (d >= vs) & (d < start)
            k, l0, lk = choose_rounds((X[a], label[a], off[a], race[a]), (X[v], won[v], off[v], race[v]))
            tr = use & (d < start)
            bst, fitted = fit(X[tr], label[tr], off[tr], race[tr], k), M
            log.append(f"{M}: {k} rounds (three months before: {l0:.4f} to {lk:.4f}), fit on "
                       f"{pd.unique(race[tr]).size:,} races")
            if bst is not None:
                g = bst.feature_importance("gain")
                gains.append(pd.Series(g / max(g.sum(), 1e-12), index=bst.feature_name()))
        p[pr] = score(bst, X[pr], off[pr], race[pr])
    share = pd.concat(gains, axis=1).mean(axis=1).sort_values(ascending=False) if gains else pd.Series(dtype=float)
    return p, log, share


def ours(d: str, t0: float):
    """Ours every six months (the named saved walk) on Betwatch's years, with its inputs."""
    df, num, rel, note = R40.base(d)
    print(note)
    a, log_a = W.walk_cached(df, num, rel, pd.Period("2022-11", "M"), t0, 6)
    print("Ours, every six months: " + "; ".join(f"{m}: {s}" for m, s in log_a if "priced by" not in s) + "\n")
    a = a[a.p_a.notna() & (a.date >= BW_FROM)].reset_index(drop=True)
    a["p_x"] = a.p_a
    a["_row"] = np.arange(len(a))
    return a, T.features(a, num, rel)


def ran_field(x: pd.DataFrame, X: pd.DataFrame):
    """The runners that ran, races together, with the offset (the blend over them) and the extra inputs; and their
    inputs aligned. x holds the field at TAB's first price with pb6, the blend over it."""
    x = x.copy()
    x["tab_book"] = (1 / x.price).groupby(x.race_id.values).transform("sum")
    x["n_bet"] = x.groupby("race_id").race_id.transform("size")
    R = x[x.is_ran.astype(bool).values].sort_values("race_id", kind="mergesort").reset_index()
    g = R.race_id.values
    s_ran = R.pb6.groupby(g).transform("sum").values
    R["s_ran"] = s_ran
    R["off"] = np.log(np.clip(R.pb6.values / s_ran, 1e-12, None))
    ours_ran = R.p_x_bet / R.p_x_bet.groupby(g).transform("sum")
    tab_ran = R.p_book / R.p_book.groupby(g).transform("sum")
    XR = X.iloc[R._row.values.astype(int)].reset_index(drop=True)
    XR["lp_ours"] = np.log(np.clip(ours_ran.values, 1e-12, None))
    XR["lp_tab"] = np.log(np.clip(tab_ran.values, 1e-12, None))
    XR["gap"] = XR.lp_ours - XR.lp_tab
    for c in ("tab_book", "s_later", "n_bet"):
        XR[c] = R[c].values.astype(float)
    return R, XR


def bsp_label(R: pd.DataFrame):
    """BSP's chances over the runners that ran, and which rows sit in races with a BSP on every one of them."""
    if "p_bsp" not in R:
        return np.zeros(len(R)), np.zeros(len(R), bool)
    g = R.race_id.values
    full = R.p_bsp.notna().groupby(g).transform("all").values
    q = (R.p_bsp / R.p_bsp.groupby(g).transform("sum")).fillna(0).values
    return np.where(full, q, 0.0), full


def ll(g: pd.DataFrame, col: str) -> float:
    return float(-np.log(g[col].clip(1e-9)).mean())


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 41, what does TAB's opening book get wrong that ours could learn?\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    a, X = ours(d, t0)
    fr = R33.load(bdir, times=(0,))
    x = R33.at_time(a, fr, 0)
    x["pb6"] = V1.blend(["p_x_bet", "p_book"], x, np.asarray(FIXED))[1]
    ok = pd.Series((x.price > 1).values).groupby(x.race_id.values).transform("all").values
    x = x[ok].reset_index(drop=True)
    R, XR = ran_field(x, X)
    print(f"Field at TAB's first price: {R.race_id.nunique():,} races, {len(R):,} runners that ran, "
          f"{R.date.min():%Y-%m} to {R.date.max():%Y-%m}. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    q, full = bsp_label(R)
    every = np.ones(len(R), bool)
    cols = {"blend, held": "pb6"}
    for name, col, y, use in (("correction on the winners", "pw", R.won.values.astype(float), every),
                              ("correction on BSP", "pq", q, full)):
        p, log, share = walk_correction(R, XR, y, use)
        print(f"**{name}**: " + "; ".join(log))
        if len(share):
            print("Its inputs by mean share of the gain: " + ", ".join(f"{k} {v:.0%}" for k, v in share.head(12).items()))
        print(f"({(time.monotonic() - t0) / 60:.0f} minutes in)\n")
        x[col] = x.pb6
        x.loc[R["index"].values, col] = p * R.s_ran.values
        cols[name] = col
    ran = x.is_ran.astype(bool).values
    t = x[ran & (x.date >= pd.Period(FROM, "M").start_time).values & x.pw.notna().values
          & x.pq.notna().values].reset_index(drop=True)
    print(f"Priced by both corrections from {FROM}: {t.race_id.nunique():,} races, {len(t):,} runners that ran.\n")
    print("## 1. Log loss on races with nothing scratched after the open (lower is better)\n")
    clean = t[(t.n_later == 0).values]
    full_c = clean.p_bsp.notna().groupby(clean.race_id).transform("all").values if "p_bsp" in clean else True
    w = clean[full_c & (clean.won == 1).values]
    print("| period | races | TAB's first book | blend, held | correction on the winners | correction on BSP | BSP |\n"
          "|---|---|---|---|---|---|---|")
    for pname, lo, hi in PERIODS:
        g = w[R36.in_period(w, lo, hi)]
        if g.empty:
            continue
        print(f"| {pname} | {g.race_id.nunique():,} | {ll(g, 'p_book'):.4f} | {ll(g, 'pb6'):.4f} | {ll(g, 'pw'):.4f} | "
              f"{ll(g, 'pq'):.4f} | {ll(g, 'p_bsp') if 'p_bsp' in g else float('nan'):.4f} |")
    old = R36.PERIODS
    R36.PERIODS = PERIODS
    try:
        print("\n## 2. The card's rule at 1.3x, TAB's first price, after TAB's deduction")
        R38.rule_table(t, cols, "Every race:")
        R38.rule_table(t[(t.n_later == 0).values].reset_index(drop=True), cols,
                       "Races with nothing scratched after the open:")
    finally:
        R36.PERIODS = old
    rec = (t.date >= "2025-02-01").values
    m0 = R38.R37.rule(t, "pb6", 1.3)[0] & rec
    for name, col in list(cols.items())[1:]:
        m = R38.R37.rule(t, col, 1.3)[0] & rec
        print(f"\nSince February 2025 the held blend makes {int(m0.sum())} bets and the {name} {int(m.sum())}, "
              f"{int((m0 & m).sum())} of them the same dog.")
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 41")
