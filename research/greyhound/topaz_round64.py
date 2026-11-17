"""Round 64: what takes TAB's opening price to BSP? Every data set, one at a time (17 Nov 2026, founder: "MATE WE HAVE
SO MUCH DATA WE CAN ABSOLUTELY BEAT THAT, just find out the data sets that are key in going towards BSP")

TAB's first price is our bet; BSP is where the market closes. Every winning bet so far has been TAB's open priced longer
than the dog's true chance, and BSP is the best estimate of that chance we have (Test 80: log loss 1.5065 against
1.5600 for our best). So the question is which of our data sets tell us, at the open, where BSP will close. Stated
before the run, on round 62's field (TAB's first price from May 2023, runners that ran, races together):

  - the label: BSP corrected for its first-tip and weight leans, the factors fitted on May 2023 to January 2025
    (round 62's label)
  - the distance to BSP: per race, sum of BSP's chance x log(BSP's chance / the forecast's chance) (the KL divergence),
    averaged over races, in thousandths; TAB's opening book alone is the start, and each forecast is scored by the
    share of that distance it closes. Scored from February 2025 on races with a BSP on every runner and nothing
    scratched after the open
  - the data sets: our inputs grouped by where they come from (each group's inputs are printed), plus one new set,
    the market's moves on earlier runs: for each runner, how far BSP moved from TAB's opening book on the dog's
    previous five runs and on its trainer's earlier runners (shrunk toward none), from races on earlier days only
  - one model per row: round 41's race-softmax correction, started from TAB's opening book alone and learning only
    where it is wrong, fitted on the races before February 2025 with the rounds chosen on November 2024 to January
    2025 by the distance to BSP; TAB's book (its log chances over the runners that ran, its overround, the field) is
    in every row; each data set added alone; everything; and everything but each data set. The share scratched after
    the open is in no row: it is not known at the bet
  - then everything, walked forward exactly as round 62's corrections (refitted every two months from November 2024),
    started from TAB's book, and its bets by the card's rule at TAB's first price after the deduction, flat, beside
    the card's blend, the blend with Isolynx and round 62's corrected blend, judged realised and by the corrected BSP;
    also on races with nothing scratched after the open only, because round 62's correction saw the share scratched
    after the open and every forecast here is normalised over the runners that ran, which the bettor at the open does
    not know

    python research/greyhound/topaz_round64.py DIR LABEL    (as round 62)

Counts, sums and rates only: no race, dog or price is printed. The models' inputs are named.
"""
import os
import re
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round36 as R36       # noqa: E402
import topaz_round41 as R41       # noqa: E402
import topaz_round58 as R58       # noqa: E402
import topaz_round62 as R62       # noqa: E402
import topaz_round63 as R63       # noqa: E402
import topaz_v1 as V1             # noqa: E402

TAG = "r64"
SPLIT = "2025-02-01"              # scored from here
VAL_FROM = "2024-11-01"           # rounds chosen on these three months
MAX_ROUNDS = 1200
STEP = 25
PARAMS = dict(R41.PARAMS, learning_rate=0.05)     # faster than round 41's, for the ranking only
SHRINK = 30                       # a trainer's mean move is shrunk toward none as if it had 30 more runners at none
BASE = ["lp_tab", "tab_book", "n_bet"]
NEVER = {"s_later"}                                # not known at the bet
NEW = "the market's moves on earlier runs (new)"
GROUPS = [
    ("our model's forecast", r"^(lp_ours|gap)$"),
    ("GRV's rating and tips", r"^(grv_|tip_)"),
    ("Isolynx tracking", r"^(iso_|chk_)"),
    ("early speed and the map", r"^(p_lead|lead_|map_)"),
    ("the dog's past prices", r"^mkt_"),
    ("time ratings, Elo and finishes", r"^(time_rating|form_|finish|last5|elo|margin_elo)"),
    ("the trainer's record", r"^trainer_(?!mv)"),
    ("breeding", r"^(dam_|sire_)"),
    (NEW, r"^(dog_mv|trainer_mv)"),
]
OTHER = "everything else (the race, the box, the dog)"


def moves(R: pd.DataFrame, q: np.ndarray, full: np.ndarray, tab: np.ndarray) -> np.ndarray:
    """How far BSP closed from TAB's opening book, log(BSP's chance / TAB's), over the runners that ran; nan where the
    race has no BSP on every runner."""
    ok = np.asarray(full, bool) & (np.asarray(q) > 0) & (np.asarray(tab) > 0)
    out = np.full(len(R), np.nan)
    out[ok] = np.log(np.asarray(q, float)[ok]) - np.log(np.asarray(tab, float)[ok])
    return out


def move_history(R: pd.DataFrame, mv: np.ndarray, shrink: float = SHRINK) -> pd.DataFrame:
    """For each row of R, from rows on EARLIER days only: the dog's last move and the mean of its last five, how many
    it has, and its trainer's mean move shrunk toward none and how many that stands on. Aligned to R's rows."""
    h = pd.DataFrame({"i": np.arange(len(R)), "date": pd.to_datetime(R.date.values),
                      "dog": R.dog.astype(str).values, "mv": np.asarray(mv, float)})
    out = pd.DataFrame(index=np.arange(len(R)), columns=["dog_mv_last", "dog_mv_mean5", "dog_mv_n", "trainer_mv",
                                                         "trainer_mv_n"], dtype=float)
    # the dog: one row a day at most, so its earlier rows are its earlier days
    h = h.sort_values(["dog", "date", "i"], kind="mergesort")
    g = h.groupby("dog", sort=False)
    same = g.date.shift().values == h.date.values           # a second row the same day sees nothing of the first
    prev = g.mv.shift().where(~same)
    h["prev"] = prev.values
    h["mean5"] = h.groupby("dog", sort=False).prev.transform(lambda s: s.rolling(5, min_periods=1).mean()).values
    has = h.mv.notna().astype(float)
    h["n"] = (has.groupby(h.dog.values).cumsum() - has).values
    h.loc[same, ["mean5", "n"]] = np.nan
    out.loc[h.i.values, "dog_mv_last"] = h.prev.values
    out.loc[h.i.values, "dog_mv_mean5"] = h.mean5.values
    out.loc[h.i.values, "dog_mv_n"] = h.n.values
    # the trainer: every runner on earlier days
    if "trainer_id" in R:
        tr = pd.to_numeric(R.trainer_id, errors="coerce").values
        t = pd.DataFrame({"i": np.arange(len(R)), "date": pd.to_datetime(R.date.values), "tr": tr,
                          "s": np.nan_to_num(np.asarray(mv, float)), "n": np.isfinite(np.asarray(mv, float))})
        t = t[np.isfinite(t.tr.values)]
        day = t.groupby(["tr", "date"], sort=True)[["s", "n"]].sum().reset_index()
        cum = day.groupby("tr")[["s", "n"]].cumsum()
        day["S"], day["N"] = (cum.s - day.s).values, (cum.n - day.n).values
        t = t.merge(day[["tr", "date", "S", "N"]], on=["tr", "date"], how="left")
        out.loc[t.i.values, "trainer_mv"] = (t.S / (t.N + shrink)).values
        out.loc[t.i.values, "trainer_mv_n"] = t.N.values
    return out


def group_columns(cols) -> dict:
    """Every input in exactly one data set (TAB's book and those not known at the bet in none), in GROUPS' order with
    the rest last."""
    left = [c for c in cols if c not in BASE and c not in NEVER]
    out = {}
    for name, pat in GROUPS:
        out[name] = [c for c in left if re.search(pat, c)]
        left = [c for c in left if c not in out[name]]
    out[OTHER] = left
    return out


def distance(p, q, race) -> float:
    """Mean over races of sum q log(q / p), in thousandths (0 when p is q)."""
    p, q = np.clip(np.asarray(p, float), 1e-12, None), np.asarray(q, float)
    t = np.where(q > 0, q * (np.log(np.clip(q, 1e-12, None)) - np.log(p)), 0.0)
    return 1000 * float(pd.Series(t).groupby(np.asarray(race)).sum().mean())


def fit(X: pd.DataFrame, y: np.ndarray, offset: np.ndarray, race, rounds: int, params=PARAMS):
    """Round 41's correction on a soft label (BSP's chances): the race softmax's gradient is p - y either way."""
    if rounds <= 0 or not len(X):
        return None
    p = dict(params, objective=R41.offset_obj(np.asarray(offset, float), R41.groups_of(race)))
    cat = [c for c in V1.CAT if c in X]
    return lgb.train(p, lgb.Dataset(X, np.asarray(y, float), categorical_feature=cat, free_raw_data=False),
                     num_boost_round=rounds)


def rank_one(X, q, off, race, d, use, test, max_rounds=MAX_ROUNDS, step=STEP):
    """Rounds chosen by the distance to BSP on VAL_FROM to SPLIT (fitted on the `use` rows before), refitted on the
    `use` rows before SPLIT; (rounds, the chances over the test rows, the booster)."""
    a = use & (d < np.datetime64(VAL_FROM))
    v = use & (d >= np.datetime64(VAL_FROM)) & (d < np.datetime64(SPLIT))
    best_k = 0
    if a.any() and v.any():
        bst = fit(X[a], q[a], off[a], race[a], max_rounds)
        best = distance(R41.score(None, X[v], off[v], race[v]), q[v], race[v])
        for k in range(step, max_rounds + 1, step):
            dk = distance(R41.score(bst, X[v], off[v], race[v], k), q[v], race[v])
            if dk < best - 1e-6:
                best, best_k = dk, k
    tr = use & (d < np.datetime64(SPLIT))
    bst = fit(X[tr], q[tr], off[tr], race[tr], best_k)
    return best_k, R41.score(bst, X[test], off[test], race[test]), bst


def ran_share(p, race) -> np.ndarray:
    s = pd.Series(np.asarray(p, float))
    return (s / s.groupby(np.asarray(race)).transform("sum")).values


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 64, what takes TAB's opening price to BSP\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    if not os.environ.get("WALK_CACHE_USE", "").strip() or not os.environ.get("WALK_ISO_USE", "").strip():
        print("Both saved walks must be named (WALK_CACHE_USE and WALK_ISO_USE): nothing to test")
        return 1
    x, R, XR, num = R62.field(d, t0)
    race, dates = R.race_id.values, R.date.values.astype("datetime64[ns]")
    q, full, w = R62.bsp_label(R, *R62.LABEL_FIT)
    tab = ran_share(R.p_book.values, race)
    off_tab = np.log(np.clip(tab, 1e-12, None))
    XR = pd.concat([XR.reset_index(drop=True), move_history(R, moves(R, q, full, tab))], axis=1)
    groups = group_columns(list(XR.columns))
    every = [c for g in groups.values() for c in g]
    clean = (R.n_later.fillna(0).values == 0)
    use = full.astype(bool)
    test = use & clean & (dates >= np.datetime64(SPLIT))
    print(f"Runners that ran at TAB's first price: {len(R):,} in {R.race_id.nunique():,} races; scored on "
          f"{pd.unique(race[test]).size:,} races from February 2025 with a BSP on every runner and nothing scratched "
          f"after the open. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    print("## 1. The data sets\n\n| data set | inputs | the inputs |\n|---|---|---|")
    print(f"| TAB's opening book (in every row) | {len(BASE)} | {', '.join(BASE)} |")
    for g, cols in groups.items():
        print(f"| {g} | {len(cols)} | {', '.join(cols) if cols else '(none)'} |")
    has = {c: float(np.isfinite(XR[c].values[test].astype(float)).mean()) for c in groups[NEW]}
    print("\nThe new set, share of the scored runners it has a value for: "
          + ", ".join(f"{c} {v:.0%}" for c, v in has.items()) + "\n")

    rt, qt, wt = race[test], q[test], R.won.values[test].astype(float)
    tab_d = distance(tab[test], qt, rt)
    refs = {"TAB's opening book, as it is": tab[test],
            "the blend with Isolynx (0.54 / 0.67)": ran_share(np.exp(R.off.values), race)[test]}
    if R63.read_corrections(x):
        refs["round 62's corrected blend"] = ran_share(x.c_q.values[R["index"].values], race)[test]
    print("## 2. How much of the distance from TAB's opening book to BSP each data set closes, Feb 2025 on\n")
    print("| forecast | rounds | distance to BSP (thousandths) | share of TAB's distance closed | winners' log loss |\n"
          "|---|---|---|---|---|")
    for name, p in refs.items():
        dd = distance(p, qt, rt)
        print(f"| {name} | | {dd:.2f} | {1 - dd / tab_d:+.1%} | {V1.ll(p, wt):.4f} |")
    print(f"| BSP corrected itself | | 0.00 | +100.0% | {V1.ll(qt, wt):.4f} |")
    rows = [("TAB's book alone (its favourite bias learnt)", BASE)]
    rows += [(f"TAB's book + {g}", BASE + cols) for g, cols in groups.items() if cols]
    rows += [("everything", BASE + every)]
    rows += [(f"everything but {g}", BASE + [c for c in every if c not in cols]) for g, cols in groups.items() if cols]
    bst_all, res = None, {}
    for name, cols in rows:
        k, p, bst = rank_one(XR[cols], q, off_tab, race, dates, use, test)
        dd = distance(p, qt, rt)
        res[name] = dd
        if name == "everything":
            bst_all = bst
        print(f"| {name} | {k:,} | {dd:.2f} | {1 - dd / tab_d:+.1%} | {V1.ll(p, wt):.4f} |", flush=True)
    print(f"\n({(time.monotonic() - t0) / 60:.0f} minutes in)\n")
    base_d, all_d = res[rows[0][0]], res["everything"]
    print("## 3. Each data set: what it closes alone, and what is lost without it (share of TAB's distance)\n")
    print("| data set | alone, over TAB's book alone | everything, less what everything but it closes |\n|---|---|---|")
    for g, cols in groups.items():
        if cols:
            alone = (base_d - res[f"TAB's book + {g}"]) / tab_d
            lost = (res[f"everything but {g}"] - all_d) / tab_d
            print(f"| {g} | {alone:+.1%} | {lost:+.1%} |")
    if bst_all is not None:
        gain = pd.Series(bst_all.feature_importance("gain"), index=bst_all.feature_name())
        gain = gain / max(gain.sum(), 1e-12)
        by = {g: gain.reindex(cols).fillna(0).sum() for g, cols in [("TAB's opening book", BASE)] + list(groups.items())}
        print("\nEverything's gain by data set: " + ", ".join(f"{g} {v:.1%}" for g, v in
                                                          sorted(by.items(), key=lambda kv: -kv[1])))
        print("Its top 25 inputs: " + ", ".join(f"{c} {v:.1%}" for c, v in gain.sort_values(ascending=False)
                                               .head(25).items()) + "\n")

    print("## 4. Everything, walked forward from November 2024, started from TAB's opening book\n")
    p, log, share = R41.walk_correction(R.assign(off=off_tab), XR[BASE + every], q, use)
    print("; ".join(log) + "\n")
    print("Its inputs by share of gain: " + ", ".join(f"{k} {v:.1%}" for k, v in share.head(20).items()) + "\n")
    ok = test & np.isfinite(p)
    print(f"Distance to BSP, Feb 2025 on: {distance(p[ok], q[ok], race[ok]):.2f} thousandths "
          f"({1 - distance(p[ok], q[ok], race[ok]) / distance(tab[ok], q[ok], race[ok]):+.1%} of TAB's closed); "
          f"winners' log loss {V1.ll(p[ok], R.won.values[ok]):.4f}\n")
    s_tab = pd.Series(R.p_book.values).groupby(race).transform("sum").values
    x["c_t"] = x.p_book
    x.loc[R["index"].values, "c_t"] = p * s_tab
    cdir = os.environ.get("WALK_CACHE_DIR", "")
    if cdir:
        Path(cdir).mkdir(parents=True, exist_ok=True)
        ran = x.is_ran.astype(bool).values
        x.loc[ran, ["race_id", "dog", "c_t"]].to_csv(Path(cdir) / f"corr_{TAG}.csv.gz", index=False,
                                                     float_format="%.9g")
    t = x[x.is_ran.astype(bool).values].reset_index(drop=True)
    t["q_bsp"], _ = R58.corrected_bsp(t)
    blends = {"the card's blend": "h_p_x_bet", "blend with Isolynx": "h_p_i_bet"}
    if "c_q" in t:
        blends["round 62's corrected blend"] = "c_q"
    blends["from TAB's open, corrected on everything"] = "c_t"
    since = [("Feb 2025 on", R63.SINCE, None)] + R63.HALVES
    print("## 5. The bets at TAB's first price, flat\n")
    R63.table(t, blends, {"TAB's first price": t.price.values}, since)
    c = t[(t.n_later.fillna(0) == 0).values].reset_index(drop=True)
    print("\n## 6. The same, races with nothing scratched after the open\n")
    R63.table(c, blends, {"TAB's first price": c.price.values}, since)
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 64")
