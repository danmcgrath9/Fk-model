"""Round 80: the best model's order sheet, set before TAB opens (19 Nov 2026, founder: "We missed early prices on even
the ones we'd bet with like a 70c difference", then "Yep build it")

On 19 Nov three of the six dogs the morning program liked were cut 30c to 90c within 15 seconds to 5 minutes of TAB's
first price, and Jill's Fantasy went from $4.40 to $3.50 in 15 seconds. Watching Betwatch cannot be that fast. An
order loaded into BetMatic before TAB opens fires within a couple of seconds of the open, at TAB's first price, if that
price is at least the order's minimum. Test 94 found a sheet built on our own price alone loses (-12.3% a unit at
1.1x): the edge is in reading ours AGAINST TAB's opening book. The best model (Test 98) does that, so its order needs
each dog's minimum TAB price worked out before TAB has priced anything. The dog's own TAB price is the trigger; the
rest of the field is predicted.

Stated before the run. Test 98's walk again (Test 88's fit with only what is known on a live morning, learning rate
0.04, up to 4,000 rounds, the same refits), keeping each refit's model. February 2025 on, for every runner that ran:

  - the rest of the field predicted two ways, before the open:
      ours: our own chance over the runners (ours with Isolynx), scaled to TAB's usual book for that field size (the
        median over the six months before the race's month)
      a TAB-open model: TAB's opening chance predicted from everything known the night before (the model's inputs
        less the three built from TAB's price: lp_tab, gap, tab_book), walked forward on the same refits
  - TAB's book over the field held at the predicted total: the dog's own price takes its share and the rest of the
    field shares what is left in the predicted proportions (a dog TAB opens longer leaves the others shorter). As a
    check, the TAB-open model's field left at its predicted prices whatever the dog's own price
  - the dog's minimum TAB price: the lowest price at which the best model, with the rest of the field so predicted,
    makes the bet (the 2-point margin, our fair price under $15). Found on a 12-point price ladder
    from $1.15 to $41, then halved 7 times between the last price that fails and the first that clears
  - the order fires when TAB's first price is at least the minimum, and is paid TAB's first price after its deduction
  - judged beside the best model priced on TAB's whole opening book (Test 98's bets, at the open and so the best a
    reaction could do): flat, and at a quarter of Kelly on Test 98's scale (the stake at TAB's actual first price, the
    rest of the field still predicted), by half and by three months; the bets both make and each alone; how many
    orders fire; how often the minimum is a band (the rule fails again higher up the ladder)
  - how close each prediction comes to TAB's first price

Saved as corr_r80 (race_id, dog, m_ours, m_model, m_free, p_model: the minimums and the model's chance at TAB's first
price), and the walk's refit models as r80_models, both in the walk cache (ROUND80_REUSE=yes reads the walk back).

    python research/greyhound/topaz_round80.py DIR LABEL    (as round 79; the walk cache holds corr_r70 and corr_r79)

Counts, sums and rates only: no race, dog or price is printed. The model's inputs are named.
"""
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round41 as R41       # noqa: E402
import topaz_round58 as R58       # noqa: E402
import topaz_round63 as R63       # noqa: E402
import topaz_round67 as R67       # noqa: E402
import topaz_round68 as R68       # noqa: E402
import topaz_round70 as R70       # noqa: E402
import topaz_round73 as R73       # noqa: E402
import topaz_round79 as R79       # noqa: E402
import topaz_v1 as V1             # noqa: E402

TAG = "r80"
MARGIN, FAIR_UNDER = 0.02, 15.0
GRID = np.geomspace(1.15, 41.0, 12)
BISECT = 7
PRICE_COLS = ("lp_tab", "gap", "tab_book")
NAMES = [("ours", "ours"), ("model", "the TAB-open model"), ("free", "the TAB-open model, the rest not moving")]


def VARIANTS(inv_ours, inv_model):
    """(name, predicted 1 / price, hold TAB's book) for each way the sheet predicts the field."""
    return [("ours", inv_ours, True), ("model", inv_model, True), ("free", inv_model, False)]
BOOK_MONTHS = 6
PRED_ROUNDS = 600
PRED_PARAMS = dict(objective="regression", learning_rate=0.05, num_leaves=31, min_data_in_leaf=200,
                   feature_fraction=0.5, bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, verbose=-1, seed=1)


def pairs(race: np.ndarray) -> tuple:
    """Rows with each race's rows together: every (own row, row) pair in a race, each own row's pairs together and in
    row order. (own, row, starts): pair k is own row own[k] seeing row row[k]; own row g's pairs begin at starts[g]."""
    r = np.asarray(race)
    n = len(r)
    if not n:
        return np.zeros(0, int), np.zeros(0, int), np.zeros(0, int)
    change = np.r_[True, r[1:] != r[:-1]]
    first = np.flatnonzero(change)
    size = np.diff(np.r_[first, n])
    race_of = np.cumsum(change) - 1
    rep = size[race_of]
    own = np.repeat(np.arange(n), rep)
    starts = np.r_[0, np.cumsum(rep)[:-1]]
    row = first[race_of][own] + (np.arange(len(own)) - starts[own])
    return own, row, starts


class Sheet:
    """The best model's chance for each runner when its own TAB price is P and the rest of its field is predicted.
    inv_pred is each runner's predicted 1 / TAB price, later the race's predicted 1 / price summed over dogs scratched
    after the open, and `predict(X)` the correction's raw score (None: no correction).

    hold_book (the sheet's own rule): TAB's book over the runners stays at the predicted total, so the rest of the field
    shares what the dog's own price leaves, in its predicted proportions (a dog TAB opens longer leaves the others
    shorter, as a bookmaker pricing to its margin would). Otherwise the rest stays at its predicted prices whatever the
    dog's price, and the book moves with it."""

    def __init__(self, X: pd.DataFrame, lp_ours: np.ndarray, inv_pred: np.ndarray, later: np.ndarray,
                 race: np.ndarray, predict=None, hold_book: bool = True):
        self.own, self.row, self.starts = pairs(race)
        self.n = len(race)
        self.X = X.iloc[self.row].reset_index(drop=True)
        self.lp_ours = np.asarray(lp_ours, float)[self.row]
        inv_pred = np.asarray(inv_pred, float)
        self.inv_pred = inv_pred[self.row]
        self.s_pred = np.bincount(self.own, weights=self.inv_pred, minlength=self.n)[self.own]
        self.others = self.s_pred - inv_pred[self.own]
        self.later = np.asarray(later, float)[self.own]
        self.is_own = self.own == self.row
        self.predict = predict
        self.hold_book = hold_book

    def chance(self, price: np.ndarray) -> np.ndarray:
        """Each runner's chance (over its race's runners) with its own TAB price at price[runner]."""
        if not self.n:
            return np.zeros(0)
        pin = 1 / np.asarray(price, float)[self.own]
        if self.hold_book:
            rest = np.maximum(self.s_pred - pin, 1e-6)
            with np.errstate(divide="ignore", invalid="ignore"):
                other = np.where(self.others > 0, rest * self.inv_pred / self.others, 0.0)
        else:
            other = self.inv_pred
        inv = np.where(self.is_own, pin, other)
        s = np.bincount(self.own, weights=inv, minlength=self.n)
        lp_tab = np.log(inv / s[self.own])
        for col, v in (("lp_tab", lp_tab), ("gap", self.lp_ours - lp_tab), ("tab_book", s[self.own] + self.later)):
            if col in self.X:
                self.X[col] = v
        raw = lp_tab + (np.asarray(self.predict(self.X), float) if self.predict is not None else 0.0)
        top = np.maximum.reduceat(raw, self.starts)
        e = np.exp(raw - top[self.own])
        p = e / np.add.reduceat(e, self.starts)[self.own]
        return p[self.is_own]

    def ok(self, price: np.ndarray) -> np.ndarray:
        """The best model's rule at that price: its chance at least 2 points over 1 / price, its fair price under $15."""
        p = self.chance(price)
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.isfinite(p) & (p > 0) & (p - 1 / price >= MARGIN - 1e-12) & (1 / p < FAIR_UNDER)

    def minimum(self) -> tuple:
        """(each runner's minimum TAB price for the bet, nan where no price on the ladder makes it; the first ladder
        price above the minimum at which the rule fails again, nan where none does)."""
        n, k = self.n, len(GRID)
        okg = np.zeros((n, k), bool)
        for j, g in enumerate(GRID):
            okg[:, j] = self.ok(np.full(n, g))
        has = okg.any(axis=1)
        f = np.where(has, okg.argmax(axis=1), -1)
        hi = np.where(has, GRID[np.maximum(f, 0)], np.nan)
        lo = np.where(f > 0, GRID[np.maximum(f - 1, 0)], np.nan)
        live = f > 0
        for _ in range(BISECT):
            if not live.any():
                break
            mid = np.where(live, np.sqrt(lo * hi), GRID[-1])
            o = self.ok(mid)
            hi = np.where(live & o, mid, hi)
            lo = np.where(live & ~o, mid, lo)
        after = (~okg) & (np.arange(k)[None, :] > f[:, None]) & has[:, None]
        top = np.where(after.any(axis=1), GRID[after.argmax(axis=1)], np.nan)
        return hi, top


def usual_book(R: pd.DataFrame) -> np.ndarray:
    """TAB's usual book (1 / price summed over the field at its first price) for each row's field size: the median over
    the races in the BOOK_MONTHS months before the row's month (all field sizes when that size has fewer than 30)."""
    r = R.drop_duplicates("race_id")
    mon = r.date.dt.to_period("M")
    out = pd.Series(np.nan, index=R.index)
    rmon = R.date.dt.to_period("M")
    for m in sorted(rmon.unique()):
        w = (mon < m) & (mon >= m - BOOK_MONTHS)
        if not w.any():
            continue
        allm = float(r.tab_book[w].median())
        by = r[w].groupby("n_bet").tab_book.agg(["median", "size"])
        at = rmon == m
        nb = R.n_bet[at]
        med = nb.map(by["median"].where(by["size"] >= 30)).fillna(allm)
        out[at] = med.values
    return out.values


def walk_tab_open(R: pd.DataFrame, X: pd.DataFrame) -> tuple:
    """TAB's opening chance over the runners that ran (its log), predicted from what is known the night before (every
    input but those built from TAB's price), walked forward as the correction: refit every EVERY months from FROM on
    every race before the month. (prediction, nan before FROM; the refit log)."""
    import lightgbm as lgb
    d = R.date.values
    y = X.lp_tab.values.astype(float)
    cols = [c for c in X.columns if c not in PRICE_COLS]
    cat = [c for c in V1.CAT if c in cols]
    out, log = np.full(len(R), np.nan), []
    bst, fitted = None, None
    for M in pd.period_range(R41.FROM, R.date.max().to_period("M"), freq="M"):
        start, end = M.start_time.to_datetime64(), (M + 1).start_time.to_datetime64()
        pr = np.flatnonzero((d >= start) & (d < end))
        if not len(pr):
            continue
        if fitted is None or (M - fitted).n >= R41.EVERY:
            tr = np.flatnonzero((d < start) & np.isfinite(y))
            bst = lgb.train(PRED_PARAMS, lgb.Dataset(X.iloc[tr][cols], y[tr], categorical_feature=cat),
                            num_boost_round=PRED_ROUNDS)
            fitted = M
            log.append(f"{M}: fit on {pd.unique(R.race_id.values[tr]).size:,} races")
        out[pr] = bst.predict(X.iloc[pr][cols])
    return out, log


def race_share(v: np.ndarray, race: np.ndarray) -> np.ndarray:
    """exp(v) as a share of its race's sum."""
    e = pd.Series(np.exp(np.asarray(v, float)))
    return (e / e.groupby(np.asarray(race)).transform("sum")).values


def errors(pred_inv: np.ndarray, act_inv: np.ndarray, m: np.ndarray) -> str:
    """How far predicted prices sit from TAB's first prices: the median miss and the share within 10% and 20%."""
    with np.errstate(divide="ignore", invalid="ignore"):
        a = np.abs(np.log(pred_inv[m] / act_inv[m]))
    a = a[np.isfinite(a)]
    if not len(a):
        return "no rows"
    return (f"median miss {np.expm1(np.median(a)):.1%}, within 10% {np.mean(a <= np.log(1.1)):.0%}, within 20% "
            f"{np.mean(a <= np.log(1.2)):.0%} ({len(a):,} runners)")


def walk_kept(R: pd.DataFrame, XK: pd.DataFrame, q: np.ndarray, use: np.ndarray, off_tab: np.ndarray) -> tuple:
    """Test 98's walk with each refit's model kept in the walk cache (r80_models: one model file a refit, the refit
    months and the walk's chances by race and dog), so a run that stops after the walk is picked up without walking
    again (ROUND80_REUSE=yes). (chances over R's rows, the refit log, [(month, booster or None)])."""
    import lightgbm as lgb
    cdir = os.environ.get("WALK_CACHE_DIR", "")
    mdir = Path(cdir) / "r80_models" if cdir else None
    if mdir is not None and os.environ.get("ROUND80_REUSE", "") == "yes" and (mdir / "index.json").exists():
        idx = json.loads((mdir / "index.json").read_text())
        models = [(pd.Period(m, "M"), lgb.Booster(model_file=str(mdir / f)) if f else None) for m, f in idx["models"]]
        c = pd.read_csv(mdir / "walk.csv.gz", dtype={"race_id": "int64", "dog": str})
        k = pd.DataFrame({"race_id": R.race_id.values.astype("int64"), "dog": R.dog.values.astype(str)})
        p = k.merge(c.drop_duplicates(["race_id", "dog"]), on=["race_id", "dog"], how="left").p.values
        return p, idx["log"] + ["(the walk read back from the walk cache)"], models
    models = []
    p, log, _ = R70.walk_faster(R.assign(off=off_tab), XK, q, use, models=models)
    if mdir is not None:
        mdir.mkdir(parents=True, exist_ok=True)
        files = []
        for m, b in models:
            f = f"refit_{m}.txt" if b is not None else ""
            if b is not None:
                b.save_model(str(mdir / f))
            files.append([str(m), f])
        pd.DataFrame({"race_id": R.race_id.values, "dog": R.dog.values, "p": p}).to_csv(
            mdir / "walk.csv.gz", index=False, float_format="%.9g")
        (mdir / "index.json").write_text(json.dumps({"models": files, "log": log}))
    return p, log, models


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 80, the best model's order sheet, set before TAB opens\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    x, R, XR, q, use, off_tab, tab, inputs = R67.build(d, t0)
    keep, drop = R79.live_inputs(inputs)
    XK = XR[keep]
    has70 = R67.read_saved(x, "r70", "c_f")
    has79 = R67.read_saved(x, "r79", "c_v")
    print(f"Inputs known on the morning: {len(keep)} (dropped as BSP-based: {len(drop)}). Test 88's fit "
          f"{'is' if has70 else 'is NOT'} in the walk cache, Test 98's {'is' if has79 else 'is NOT'}. "
          f"{(time.monotonic() - t0) / 60:.0f} minutes in.\n")

    p, log, models = walk_kept(R, XK, q, use, off_tab)
    print("## 1. Test 98's walk again, keeping each refit's model\n\n" + "; ".join(log) + "\n")
    race, dates = R.race_id.values, R.date.values.astype("datetime64[ns]")
    ran = x.is_ran.astype(bool).values
    t = x[ran].reset_index(drop=True)
    to_t = np.full(len(x), -1)
    to_t[np.flatnonzero(ran)] = np.arange(int(ran.sum()))
    tpos = to_t[R["index"].values]

    def on_t(a):
        out = np.full(len(t), np.nan)
        out[tpos] = a
        return out

    if has79:
        pv = R70.on_runners(R, t, "c_v")
        both = np.isfinite(p) & np.isfinite(pv)
        print(f"Against Test 98's saved walk: {int(both.sum()):,} runners, mean difference "
              f"{np.mean(np.abs(p[both] - pv[both])):.5f} in chance\n")

    since_r = dates >= np.datetime64(R63.SINCE)
    inv_act = 1 / R.price.values.astype(float)
    book = usual_book(R)
    nb = R.n_bet.values.astype(float)
    nl = np.clip(nb - pd.Series(np.ones(len(R))).groupby(race).transform("sum").values, 0, None)
    later_pred = book * nl / nb
    ran_book = book * (1 - nl / nb)
    inv_ours = ran_book * np.exp(XK.lp_ours.values.astype(float))
    pred, plog = walk_tab_open(R, XK)
    inv_model = ran_book * race_share(pred, race)
    print(f"## 2. The rest of the field before the open ({(time.monotonic() - t0) / 60:.0f} minutes in)\n")
    print("The TAB-open model's refits: " + "; ".join(plog) + "\n")
    with np.errstate(divide="ignore", invalid="ignore"):
        bm = np.abs(np.log(book / R.tab_book.values.astype(float)))
    bm = bm[since_r & np.isfinite(bm)]
    print(f"TAB's book from the six months before: median miss {np.expm1(np.median(bm)):.1%} (Feb 2025 on)\n")
    print("| prediction of each runner's TAB first price | how close, February 2025 on |\n|---|---|")
    for nm, v in (("ours, scaled to TAB's usual book", inv_ours), ("the TAB-open model", inv_model)):
        print(f"| {nm} | {errors(v, inv_act, since_r)} |")

    lp_ours = XK.lp_ours.values.astype(float)
    month = pd.Series(R.date.values).dt.to_period("M").values
    res = {f"{a}_{nm}": np.full(len(R), np.nan) for a in ("m", "top", "p") for nm, _ in NAMES}
    for i, (M, bst) in enumerate(models):
        nxt = models[i + 1][0] if i + 1 < len(models) else None
        blk = np.flatnonzero(since_r & (month >= M) & ((month < nxt) if nxt is not None else True) & np.isfinite(p))
        if not len(blk) or bst is None:
            continue
        pf = (lambda X, b=bst: b.predict(X, raw_score=True))
        for nm, inv_o, hold in VARIANTS(inv_ours, inv_model):
            gap_races = pd.unique(race[blk][~np.isfinite(inv_o[blk]) | ~np.isfinite(later_pred[blk])])
            rows = blk[~np.isin(race[blk], gap_races)]           # a race is priced whole or not at all
            if not len(rows):
                continue
            sh = Sheet(XK.iloc[rows], lp_ours[rows], inv_o[rows], later_pred[rows], race[rows], pf, hold_book=hold)
            mmin, top = sh.minimum()
            res[f"m_{nm}"][rows], res[f"top_{nm}"][rows] = mmin, top
            res[f"p_{nm}"][rows] = sh.chance(R.price.values.astype(float)[rows])
        print(f"{M}: {len(blk):,} runners priced against the ladder, {(time.monotonic() - t0) / 60:.0f} minutes in")

    s_tab = pd.Series(R.p_book.values).groupby(race).transform("sum").values
    x["c_o"] = x.p_book
    x.loc[R["index"].values, "c_o"] = p * s_tab
    cdir = os.environ.get("WALK_CACHE_DIR", "")
    if cdir:
        Path(cdir).mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"race_id": R.race_id.values, "dog": R.dog.values, "m_ours": res["m_ours"],
                      "m_model": res["m_model"], "m_free": res["m_free"], "p_model": res["p_model"]}).to_csv(
            Path(cdir) / f"corr_{TAG}.csv.gz", index=False, float_format="%.6g")

    t["q_bsp"], _ = R58.corrected_bsp(t)
    tq = t.assign(p_bsp=t.q_bsp)
    paid = R68.paid_price(t)
    price = t.price.values.astype(float)
    since = R63.R36.in_period(t, R63.SINCE, None)
    pm = on_t(p)
    m98 = R68.margin_bets(t, pm, MARGIN)
    base = R67.model_chance(t, "c_f") if has70 else pm
    scale = R73.raw_kelly(base, paid)[R68.margin_bets(t, base, MARGIN) & since].mean()
    u98 = R73.raw_kelly(pm, paid) / scale
    m98 &= u98 > 0
    flat = np.ones(len(t))
    rules = {"the best model on TAB's whole opening book (Test 98)": (m98 & since, u98, flat)}
    for nm, lab in NAMES:
        mm, pp = on_t(res[f"m_{nm}"]), on_t(res[f"p_{nm}"])
        fire = since & np.isfinite(mm) & np.isfinite(price) & (price >= mm - 1e-9)
        uk = R73.raw_kelly(pp, paid) / scale
        rules[f"the sheet, the field from {lab}"] = (fire, uk, flat)
        res[f"fire_{nm}"], res[f"set_{nm}"] = fire, since & np.isfinite(mm)
        top = on_t(res[f"top_{nm}"])
        res[f"band_{nm}"] = fire & np.isfinite(top) & (price >= top)

    periods = [("Feb 2025 on", R63.SINCE, None)] + R63.HALVES
    print(f"\n## 3. The bets, flat and at a quarter of Kelly ({(time.monotonic() - t0) / 60:.0f} minutes in)\n")
    print("| rule | stake | period | bets | units staked | corrected BSP per unit staked (SE) | corrected BSP units | "
          "realised units | luck in the realised units (SD) | deepest fall, realised | losing months |\n|" + "---|" * 11)
    for nm, (m, uk, fl) in rules.items():
        for sname, u, mk in (("flat", fl, m), ("quarter Kelly", uk, m & (uk > 0))):
            for pname, lo, hi in periods:
                per = R63.R36.in_period(t, lo, hi)
                print(f"| {nm} | {sname} | {pname} | " + R73.kelly_row(t, tq, mk & per, paid, u) + " |")

    print("\n## 4. The sheet's orders, February 2025 on\n")
    print("| field from | orders set | fired (TAB opened at the minimum or more) | of them, a band (the rule fails "
          "again at TAB's price) | bets Test 98 makes too | Test 98's bets the sheet misses |\n|---|---|---|---|---|---|")
    for nm, lab in NAMES:
        fire = res[f"fire_{nm}"]
        print(f"| {lab} | {int(res[f'set_{nm}'].sum()):,} | {int(fire.sum()):,} | {int(res[f'band_{nm}'].sum()):,} | "
              f"{int((fire & m98 & since).sum()):,} | {int((m98 & since & ~fire).sum()):,} |")

    print("\n## 5. Flat, by who makes the bet (corrected BSP units / realised units, bets)\n")
    print("| field from | both | the sheet only | Test 98 only |\n|---|---|---|---|")
    for nm, lab in NAMES:
        fire = res[f"fire_{nm}"]
        cells = []
        for mk in (fire & m98 & since, fire & ~m98, m98 & since & ~fire):
            s = R68.staked(tq, mk, paid, flat)
            cells.append(f"{s['units']:+,.1f} / {s['real']:+,.1f} ({s['n']:,})" if s["n"] else "none")
        print(f"| {lab} | " + " | ".join(cells) + " |")

    print("\n## 6. By three months, flat: corrected BSP units / realised units\n")
    print("| three months | " + " | ".join(rules) + " |\n|" + "---|" * (len(rules) + 1))
    for bname, lo, hi in R68.blocks(R63.SINCE, None):
        per = R63.R36.in_period(t, lo, hi)
        cells = []
        for m, _, fl in rules.values():
            s = R68.staked(tq, m & per, paid, fl)
            cells.append(f"{s['units']:+,.1f} / {s['real']:+,.1f}" if s["n"] else "no BSP yet")
        print(f"| {bname} | " + " | ".join(cells) + " |")
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 80")
