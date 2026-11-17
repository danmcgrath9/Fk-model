"""The corrected blend in the nightly run, paper only (17 Nov 2026, founder: "Yep build it, track both 1.1x and 1.2x").

Test 80: ours with Isolynx, blended with TAB's first book (held at 0.54 / 0.67) and then corrected for its own mistakes
(Test 59's correction, fitted on BSP corrected for its first-tip and weight leans), bet flat from 1.1x at TAB's first
price, made about 15 bets a week since February 2025 at +14% to +16%; from 1.2x about 6 a week at +23% (Test 81).
Nothing here changes the card: the card's model, rule and page are untouched. Three parts:

  train(d, label)    PRICE_MODE=train_iso. Ours with Isolynx (every input ours has plus Isolynx's tracking and check
                     inputs) fitted on every resulted race exactly as the card's model is, saved as model_iso.txt; then
                     the correction, fitted on every race at TAB's first price from April 2023 that has an out-of-sample
                     chance from ours with Isolynx (the research walk, saved once as iso_walk.csv.gz, and every kept
                     card_iso file since), the number of rounds chosen on the last three months as in Test 59, saved as
                     corr.txt. ISO_DIR (the Isolynx pull), BETWATCH_DIR, BETFAIR_DIR, CARDS_DIR, MODEL_DIR.
  price(...)         Called by topaz_price_upcoming after the card is kept: tomorrow's runners priced by ours with
                     Isolynx, kept as card_iso_DAY.csv.gz beside the card with every input the correction needs.
  at_open(...)       Called by the tracker the day after: each race as it stood at TAB's first price, with only what
                     was known then (every dog in TAB's field priced by ours, none known to be scratched later), the
                     blend and the correction over it; the bets are the corrected chance's, at 1.1x and 1.2x, flat.

The research rebuilt each race as it stood at TAB's first price with the dogs scratched later at TAB's chance (Test
51); the tracker cannot know who will be scratched, so it prices every dog in TAB's field, as the bet would be struck.

GRV's values are personal use: the kept files live in this repository's Actions cache only, never in a log.
"""
import json
import os
import shutil
import sys
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import gbm_v0                     # noqa: E402
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402

ISO_ENV = "ISO_DIR"               # the Isolynx pull; never ISOLYNX_DIR, which would change the card's own build
ISO_WALK = "3175ebcbfe9eb070"     # the research walk of ours with Isolynx (round 50), out of sample to 13 Nov 2026
FIXED = (0.54, 0.67)              # Test 51's held weights
LABEL_FIT = ("2023-05-01", "2025-02-01")   # Test 80's BSP correction for the label
BW_FROM = "2023-04-01"
VAL_MONTHS = 3
RATIOS = (1.1, 1.2)
BAND = (2.0, 15.0)
EXTRA = ["lp_ours", "lp_tab", "gap", "tab_book", "s_later", "n_bet"]


def model_dir() -> Path:
    return Path(os.environ.get("MODEL_DIR", "greyhound/cache/model"))


@contextmanager
def isolynx_env(iso_dir: str):
    """ISOLYNX_DIR set for one build only, so the card's build never sees it."""
    old = os.environ.get("ISOLYNX_DIR")
    os.environ["ISOLYNX_DIR"] = iso_dir
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("ISOLYNX_DIR", None)
        else:
            os.environ["ISOLYNX_DIR"] = old


def add_checks(df: pd.DataFrame, num: list, iso_dir: str):
    """Round 50's base: the Isolynx check inputs (checked last time, the dip, places lost, the share checked) as inputs."""
    import topaz_round18 as R18
    df, chk, _ = R18.check_features(df, iso_dir)
    return df, list(dict.fromkeys(list(num) + list(chk)))


def norm(s) -> np.ndarray:
    return gbm_v0.norm_name(pd.Series(s, dtype=object).fillna("")).values


# ---- training ------------------------------------------------------------------------------------------------------

def oos_chances(mdir: Path, cards_dir: str) -> pd.DataFrame:
    """Ours with Isolynx out of sample, (race_id, dog, p_i): the research walk, then every kept card_iso file (a later
    source wins a race both hold)."""
    parts = []
    f = mdir / "iso_walk.csv.gz"
    if f.exists():
        w = pd.read_csv(f, dtype={"race_id": "int64", "dog": str})
        parts.append(w[["race_id", "dog", "p_a"]].rename(columns={"p_a": "p_i"}).dropna())
    for c in sorted(Path(cards_dir).glob("card_iso_*.csv.gz")) if cards_dir and os.path.isdir(cards_dir) else []:
        k = pd.read_csv(c, usecols=["race_id", "dog", "p_iso"], dtype={"dog": str})
        k["race_id"] = pd.to_numeric(k.race_id, errors="coerce")
        parts.append(k.dropna().astype({"race_id": "int64"}).rename(columns={"p_iso": "p_i"}))
    if not parts:
        return pd.DataFrame(columns=["race_id", "dog", "p_i"])
    return pd.concat(parts, ignore_index=True).drop_duplicates(["race_id", "dog"], keep="last")


def correction_field(df: pd.DataFrame, X: pd.DataFrame, oos: pd.DataFrame, bdir: str):
    """The runners that ran at TAB's first price with an out-of-sample chance (every runner of the race), the blend
    with Isolynx over the field at the bet as the offset, and the correction's inputs aligned: (R, XR)."""
    import topaz_round33 as R33
    import topaz_round41 as R41
    import topaz_round57 as R57
    d = df.assign(_row=np.arange(len(df)))
    d = d[(d.date >= BW_FROM).values]
    k = pd.DataFrame({"race_id": pd.to_numeric(d.race_id, errors="coerce").values, "dog": d.dog.astype(str).values})
    d = d.assign(p_i=k.merge(oos, on=["race_id", "dog"], how="left").p_i.values)
    d = d[d.p_i.notna().groupby(d.race_id.values).transform("all").values]
    d = d.assign(p_x=d.p_i / d.groupby("race_id").p_i.transform("sum"))
    fr = R33.load(bdir, times=(0,))
    x = R33.at_time(d, fr, 0)
    ok = pd.Series((x.price > 1).values).groupby(x.race_id.values).transform("all").values
    x = R57.term_columns(x[ok].reset_index(drop=True))
    x["pb6"] = V1.blend(["p_x_bet", "p_book"], x, np.asarray(FIXED))[1]
    return R41.ran_field(x, X)


def fit_correction(R: pd.DataFrame, XR: pd.DataFrame) -> tuple:
    """Test 80's correction on BSP corrected, fitted once on every race: rounds chosen on the last VAL_MONTHS months
    (fitted on the months before, scored on the winners), then refitted on every race with that many. Returns
    (booster or None for no rounds, meta)."""
    import topaz_round41 as R41
    import topaz_round62 as R62
    q, full, w = R62.bsp_label(R, *LABEL_FIT)
    d, race, off, won = R.date.values, R.race_id.values, R.off.values, R.won.values.astype(float)
    vs = (R.date.max().to_period("M") - (VAL_MONTHS - 1)).start_time.to_datetime64()
    a, v = full & (d < vs), d >= vs
    k, l0, lk = R41.choose_rounds((XR[a], q[a], off[a], race[a]), (XR[v], won[v], off[v], race[v]))
    bst = R41.fit(XR[full], q[full], off[full], race[full], k)
    meta = {"cols": list(XR.columns), "rounds": int(k), "blend": list(FIXED), "label": [float(x) for x in w],
            "label_fit": list(LABEL_FIT), "races": int(pd.unique(race[full]).size),
            "first_day": f"{R.date.min():%Y-%m-%d}", "last_day": f"{R.date.max():%Y-%m-%d}",
            "check": f"the last {VAL_MONTHS} months: the blend {l0:.4f}, the correction {lk:.4f}"}
    return bst, meta


def train(d, label) -> int:
    """PRICE_MODE=train_iso: ours with Isolynx, then the correction."""
    import topaz_walk as W
    from greyhound.preview import SYDNEY
    iso = os.environ.get(ISO_ENV, "")
    if not iso or not os.path.isdir(iso):
        print(f"# {label}\n\nNo Isolynx pull ({ISO_ENV}): nothing trained")
        return 1
    mdir = model_dir()
    mdir.mkdir(parents=True, exist_ok=True)
    wf = Path(os.environ.get("WALK_CACHE_DIR", "")) / f"walk_{ISO_WALK}.csv.gz"
    if not (mdir / "iso_walk.csv.gz").exists() and wf.exists():
        shutil.copy(wf, mdir / "iso_walk.csv.gz")       # kept with the model, so the walk cache may expire
    os.environ.pop("WALK_LEAD_MODEL", None)             # the training rows' lead chance is forward-chained, as the card's
    with isolynx_env(iso):
        df, num, rel, note = W.build_full(d)
    df, num = add_checks(df, num, iso)
    X = T.features(df, num, rel)
    today = pd.Timestamp.now(tz=SYDNEY).normalize().tz_localize(None)
    rec = 0.5 ** ((((today - df.date).dt.days) / 365.25).values / 3.0)
    bst = W.fit_fixed(X, df.p_mkt.values.astype(float), df.race_id, rec * W.label_weight(df), W.ROUNDS_A)
    bst.save_model(str(mdir / "model_iso.txt"))
    meta = {"cols": list(X.columns), "num": num, "rel": rel, "rounds": int(W.ROUNDS_A),
            "fit_races": int(df.race_id.nunique()), "last_day": f"{df.date.max():%Y-%m-%d}",
            "trained": pd.Timestamp.now(tz=SYDNEY).isoformat(timespec="minutes")}
    (mdir / "meta_iso.json").write_text(json.dumps(meta))
    print(f"# {label}: ours with Isolynx and the correction\n\n{note}\nours with Isolynx: fitted on "
          f"{meta['fit_races']:,} races to {meta['last_day']}, {meta['rounds']:,} rounds, {len(meta['cols'])} inputs")
    bdir = os.environ.get("BETWATCH_DIR", "")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): the correction is not trained")
        return 1
    oos = oos_chances(mdir, os.environ.get("CARDS_DIR", ""))
    R, XR = correction_field(df, X, oos, bdir)
    cb, cmeta = fit_correction(R, XR)
    if cb is not None:
        cb.save_model(str(mdir / "corr.txt"))
    else:
        (mdir / "corr.txt").unlink(missing_ok=True)
    cmeta["trained"] = meta["trained"]
    (mdir / "corr_meta.json").write_text(json.dumps(cmeta))
    print(f"the correction: {len(oos):,} out-of-sample chances; fitted on {cmeta['races']:,} races at TAB's first price "
          f"({cmeta['first_day']} to {cmeta['last_day']}), {cmeta['rounds']} rounds ({cmeta['check']}); "
          f"{len(cmeta['cols'])} inputs")
    return 0


# ---- the nightly price ---------------------------------------------------------------------------------------------

def load_model(name: str = "model_iso.txt", meta: str = "meta_iso.json"):
    mf, jf = model_dir() / name, model_dir() / meta
    if not (mf.exists() and jf.exists()):
        return None, None
    import lightgbm as lgb
    return lgb.Booster(model_file=str(mf)), json.loads(jf.read_text())


def align(X: pd.DataFrame, cols: list) -> pd.DataFrame:
    out = X.reindex(columns=cols)
    for c in V1.CAT:
        if c in out:
            out[c] = out[c].astype("category")
    return out


def price(cache, rows, races, day: str, since: str, out_dir: Path, build_day, txt) -> str:
    """Tomorrow's runners priced by ours with Isolynx, kept as card_iso_DAY.csv.gz (ids, our chance, every input) for
    the tracker. Returns a one-line note for the log (counts only)."""
    iso = os.environ.get(ISO_ENV, "")
    if not iso or not os.path.isdir(iso):
        return f"no Isolynx pull ({ISO_ENV}): no corrected-blend card"
    bst, meta = load_model()
    if bst is None:
        return "no model_iso.txt yet (PRICE_MODE=train_iso): no corrected-blend card"
    with isolynx_env(iso):
        df, num, rel, _, _ = build_day(cache, rows, races, day, since)
    df, num = add_checks(df, num, iso)
    today = (df.date == pd.Timestamp(day)).values
    t = df[today]
    if t.empty:
        return "the Isolynx build has no runners for the day: no corrected-blend card"
    X = T.features(t, num, rel)
    p = V1.race_softmax(bst.predict(align(X, meta["cols"]), raw_score=True), t.race_id.values)
    out = pd.DataFrame({"day": day,
                        "venue": [txt(a) or txt(b) for a, b in zip(t.get("track_name", t.track), t.track)],
                        "race_no": [txt(v) for v in t.get("race_number", pd.Series("", index=t.index))],
                        "box": [txt(v) for v in t.box], "dog_name": [txt(v) for v in t.dog_name],
                        "race_id": t.race_id.values, "dog": t.dog.astype(str).values, "p_iso": np.round(p, 6)})
    out.insert(1, "race_key", [f"{day}|{v}|{r}" for v, r in zip(out.venue, out.race_no)])
    X = X.reset_index(drop=True)
    for c in V1.CAT:
        if c in X:
            X[c] = X[c].astype(object)
    out = pd.concat([out.reset_index(drop=True), X.add_prefix("x_")], axis=1)
    out_dir.mkdir(parents=True, exist_ok=True)
    f = out_dir / f"card_iso_{day}.csv.gz"
    out.to_csv(f, index=False, compression="gzip", float_format="%.6g")
    return f"the corrected-blend card kept (Actions cache only): {f.name}, {len(out)} runners, {X.shape[1]} inputs"


# ---- at TAB's open, for the tracker --------------------------------------------------------------------------------

def iso_cards(d: str) -> pd.DataFrame:
    fs = sorted(Path(d).glob("card_iso_*.csv.gz")) if d and os.path.isdir(d) else []
    if not fs:
        return pd.DataFrame()
    return pd.concat([pd.read_csv(f, dtype={"race_no": str, "box": str, "dog": str}, low_memory=False) for f in fs],
                     ignore_index=True)


def at_open(facts: pd.DataFrame, cards: pd.DataFrame, bst, meta: dict) -> pd.DataFrame:
    """Each race of the facts (TAB's field at its first price: date, bw_race, dog_name, price, p_book, ...) whose every
    dog is on one kept card_iso race: ours with Isolynx over that field, the blend held at 0.54 / 0.67, and the
    corrected chance (p_corr; the blend itself when the correction kept no rounds). Only what was known at TAB's first
    price: no dog is known to be scratched later (s_later 0)."""
    if facts.empty or cards.empty:
        return pd.DataFrame()
    f = facts.assign(_dn=norm(facts.dog_name))
    c = cards.assign(_dn=norm(cards.dog_name)).rename(columns={"day": "date", "dog_name": "card_dog", "venue": "card_venue",
                                                               "race_no": "card_race_no", "box": "card_box"})
    c = c.drop_duplicates(["date", "_dn"], keep=False)
    x = f.merge(c, on=["date", "_dn"], how="left")
    g = x.groupby("bw_race")
    whole = g.p_iso.transform(lambda s: s.notna().all()) & (g.race_key.transform("nunique") == 1)
    x = x[whole.values & (x.price > 1).values].copy()
    if x.empty:
        return x
    x["race_id"] = x.bw_race
    x["p_i_open"] = x.p_iso / x.groupby("bw_race").p_iso.transform("sum")
    x["p_tab_open"] = (1 / x.price) / (1 / x.price).groupby(x.bw_race).transform("sum")
    x["p_blend"] = V1.blend(["p_i_open", "p_tab_open"], x, np.asarray(FIXED))[1]
    x["p_corr"] = x.p_blend
    if bst is not None and meta and meta.get("rounds", 0) > 0:
        XR = pd.DataFrame(index=x.index)
        for col in meta["cols"]:
            if col in EXTRA:
                continue
            XR[col] = x[f"x_{col}"] if f"x_{col}" in x else np.nan
        for col in V1.CAT:
            if col in XR:
                XR[col] = XR[col].astype("category")
        XR["lp_ours"] = np.log(x.p_i_open.clip(1e-12))
        XR["lp_tab"] = np.log(x.p_tab_open.clip(1e-12))
        XR["gap"] = XR.lp_ours - XR.lp_tab
        XR["tab_book"] = (1 / x.price).groupby(x.bw_race).transform("sum")
        XR["s_later"] = 0.0
        XR["n_bet"] = x.groupby("bw_race").bw_race.transform("size").astype(float)
        XR = XR[meta["cols"]]
        raw = np.log(x.p_blend.clip(1e-12).values) + bst.predict(XR, raw_score=True)
        x["p_corr"] = V1.race_softmax(raw, x.bw_race.values)
    return x


def bets(x: pd.DataFrame, ratio: float) -> np.ndarray:
    """The rule on the corrected chance: our odds $2 to $15 and TAB's first price at the ratio x our odds or over."""
    if x.empty:
        return np.zeros(0, bool)
    fair = 1 / x.p_corr.values
    price = x.price.values.astype(float)
    return (fair >= BAND[0]) & (fair < BAND[1]) & (price > 1) & (price >= ratio * fair)
