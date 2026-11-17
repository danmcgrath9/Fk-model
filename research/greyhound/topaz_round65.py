"""Round 65: the market's history, built out (17 Nov 2026, founder: "Build the market history next, find more winning
bets")

Test 82: of every data set we hold, how the market moved on a dog's earlier runs was the biggest new information
TAB's opening price misses (2.7% of TAB's distance to BSP that nothing else closes), measured only as BSP against TAB's
open. Betwatch holds far more of the market than that: every TAB price change, and the other books' prices. Stated
before the run, on round 64's field, label and distance to BSP:

  - each runner's market on each EARLIER run, built from Betwatch: how far TAB's price moved from its open to its last
    before the jump, which way and how far TAB's first change went, how the other books' first prices stood against
    TAB's open (their geometric mean; an exchange left out), how many times TAB's price changed, and whether BSP
    closed 25% or more shorter than TAB's open (backed) or longer (drifted)
  - per dog, from earlier days only: its last run and the mean of its last five on each, and its backed and drifted
    rates over its last five; per trainer: the mean BSP move, the backed rate and the runners over the 90 days before
    the day (shrunk toward none as if 30 more runners stood at none); with Test 82's set beside them
  - which way each points: from February 2025, by fifths of each, today's mean move from TAB's open to BSP and the
    winners against TAB's book with its favourite bias learnt and against the corrected BSP
  - one model per row, as round 64: everything from Test 82; everything with every market-history input; that less
    each new part; and TAB's book with the market history alone
  - then everything with the market history walked forward from TAB's book exactly as Test 82's (refitted every two
    months from November 2024; up to 2,000 rounds, because Test 82's walk kept the 1,200 cap at nearly every refit),
    and its bets by the card's rule at TAB's first price after the deduction, flat, beside the card's blend, Test 80's
    corrected blend and Test 82's model, realised and by the corrected BSP, and on races with nothing scratched after
    the open

    python research/greyhound/topaz_round65.py DIR LABEL    (as round 64)

Counts, sums and rates only: no race, dog or price is printed. The models' inputs are named.
"""
import gzip
import json
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import gbm_v0                     # noqa: E402
import topaz_round32 as R32       # noqa: E402
import topaz_round41 as R41       # noqa: E402
import topaz_round58 as R58       # noqa: E402
import topaz_round62 as R62       # noqa: E402
import topaz_round63 as R63       # noqa: E402
import topaz_round64 as R64       # noqa: E402
import topaz_v1 as V1             # noqa: E402

TAG = "r65"
BIG = np.log(1.25)                # a move of 25% or more in the odds
WINDOW = "90D"
WALK_ROUNDS = 2000
PARTS = {
    "TAB's own moves": r"^mh_(tab|first|nfl)_",
    "the other books' opening prices": r"^mh_books_",
    "the backed and drifted rates": r"^mh_(steam|drift)5$",
    "the trainer's last 90 days": r"^mh_tr90_",
}
OLD = "Test 82's market history"


def tab_and_books(bdir: str) -> pd.DataFrame:
    """One row per runner (not scratched) with a TAB price before the jump: date, normalised name, TAB's last price
    before the jump, its first price that differs from its first, how many prices it had, and the geometric mean of the
    other books' first prices (exchanges left out)."""
    rows = []
    for f in sorted(Path(bdir).glob("betwatch_VIC_G_*.json.gz")):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for r in json.load(fh).get("races", []):
                start = R32.ts(r.get("start"))
                for ru in r.get("runners", []):
                    if ru.get("scratched"):
                        continue
                    tab, others = None, []
                    for bk, v in (ru.get("books") or {}).items():
                        fl = []
                        for p, t in (v or {}).get("flucs") or []:
                            try:
                                p = float(p)
                            except (TypeError, ValueError):
                                continue
                            ts = R32.ts(t)
                            if p > 1 and not np.isnan(ts) and (np.isnan(start) or ts <= start):
                                fl.append((ts, p))
                        if not fl:
                            continue
                        fl.sort()
                        if bk.lower() == "tab":
                            tab = fl
                        elif not any(e in bk.lower() for e in R63.EXCHANGES):
                            others.append(fl[0][1])
                    if tab is None:
                        continue
                    change = next((p for _, p in tab if p != tab[0][1]), tab[0][1])
                    rows.append({"date": r.get("date"), "dog_raw": ru.get("name"), "tab_first_bw": tab[0][1],
                                 "tab_last": tab[-1][1], "tab_change": change, "tab_n": len(tab),
                                 "books_first": float(np.exp(np.mean(np.log(others)))) if others else np.nan})
    bw = pd.DataFrame(rows)
    if bw.empty:
        return bw
    bw["date"] = pd.to_datetime(bw.date, errors="coerce")
    bw["_dn"] = gbm_v0.norm_name(bw.dog_raw.fillna(""))
    return bw.drop(columns="dog_raw").drop_duplicates(["date", "_dn"], keep=False)


def run_market(R: pd.DataFrame, bw: pd.DataFrame, mv: np.ndarray) -> pd.DataFrame:
    """Each runner's market on the day (only ever used as history for its later runs): TAB's move open to last
    (positive = shortened), its first change, the other books' open against TAB's (positive = they opened shorter),
    log of TAB's price count, and backed / drifted by BSP against TAB's open. Aligned to R's rows."""
    k = pd.DataFrame({"date": pd.to_datetime(R.date.values), "_dn": gbm_v0.norm_name(R.dog_name.fillna("")).values})
    m = k.merge(bw, on=["date", "_dn"], how="left") if len(bw) else k.assign(
        tab_last=np.nan, tab_change=np.nan, tab_n=np.nan, books_first=np.nan)
    assert len(m) == len(R), "Betwatch duplicated runners"
    op = R.price.values.astype(float)
    mv = np.asarray(mv, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = pd.DataFrame({
            "tab": np.log(op / m.tab_last.values), "first": np.log(op / m.tab_change.values),
            "books": np.log(op / m.books_first.values), "nfl": np.log1p(m.tab_n.values),
            "steam": np.where(np.isfinite(mv), (mv >= BIG).astype(float), np.nan),
            "drift": np.where(np.isfinite(mv), (mv <= -BIG).astype(float), np.nan)})
    return out.replace([np.inf, -np.inf], np.nan)


def dog_history(R: pd.DataFrame, day: pd.DataFrame) -> pd.DataFrame:
    """Per dog, from earlier days only: its last run's and the mean of its last five runs' tab, first, books and nfl,
    and the backed and drifted rates over its last five, all as they stood at the end of the day before. Every run on
    the same day sees the same history."""
    cols = ["tab", "first", "books", "nfl", "steam", "drift"]
    h = day[cols].copy()
    h["i"], h["date"], h["dog"] = np.arange(len(R)), pd.to_datetime(R.date.values), R.dog.astype(str).values
    h = h.sort_values(["dog", "date", "i"], kind="mergesort").reset_index(drop=True)
    r5 = h.groupby("dog", sort=False)[cols].rolling(5, min_periods=1).mean().reset_index(level=0, drop=True).sort_index()
    pos = np.arange(len(h))
    src = pos - h.groupby(["dog", "date"], sort=False).cumcount().values - 1      # the last run on an earlier day
    dog = h.dog.values
    ok = (src >= 0) & (dog[np.clip(src, 0, None)] == dog)
    s = np.clip(src, 0, None)
    out = pd.DataFrame(index=h.i.values)
    for c in cols:
        last = np.where(ok, h[c].values[s], np.nan)
        mean5 = np.where(ok, r5[c].values[s], np.nan)
        if c in ("steam", "drift"):
            out[f"mh_{c}5"] = mean5
        else:
            out[f"mh_{c}_last"], out[f"mh_{c}_mean5"] = last, mean5
    return out.sort_index()


def trainer_history(R: pd.DataFrame, mv: np.ndarray, steam: np.ndarray, shrink: float = R64.SHRINK,
                    window: str = WINDOW) -> pd.DataFrame:
    """Per trainer, over the window before the day (the day itself left out): the mean BSP move and the backed rate,
    each shrunk toward none, and the runners with a move they stand on."""
    out = pd.DataFrame(np.nan, index=np.arange(len(R)), columns=["mh_tr90_mv", "mh_tr90_steam", "mh_tr90_n"])
    if "trainer_id" not in R:
        return out
    mv, steam = np.asarray(mv, float), np.asarray(steam, float)
    t = pd.DataFrame({"i": np.arange(len(R)), "date": pd.to_datetime(R.date.values),
                      "tr": pd.to_numeric(R.trainer_id, errors="coerce").values, "s": np.nan_to_num(mv),
                      "st": np.nan_to_num(steam), "n": np.isfinite(mv).astype(float)})
    t = t[np.isfinite(t.tr.values)]
    if t.empty:
        return out
    day = t.groupby(["tr", "date"], sort=True)[["s", "st", "n"]].sum().reset_index()
    roll = (day.set_index("date").groupby("tr")[["s", "st", "n"]].rolling(window, closed="left").sum()
            .reset_index().fillna(0.0))
    t = t.merge(roll, on=["tr", "date"], how="left", suffixes=("", "_w"))
    out.loc[t.i.values, "mh_tr90_mv"] = (t.s_w / (t.n_w + shrink)).values
    out.loc[t.i.values, "mh_tr90_steam"] = (t.st_w / (t.n_w + shrink)).values
    out.loc[t.i.values, "mh_tr90_n"] = t.n_w.values
    return out


def which_way(v: np.ndarray, mv: np.ndarray, won: np.ndarray, p_tab: np.ndarray, q: np.ndarray) -> list:
    """By fifths of v (its finite values): runners, today's mean move from TAB's open to BSP as a % of the odds, and
    the winners over TAB-after-its-bias's and the corrected BSP's expected winners."""
    ok = np.isfinite(v) & np.isfinite(mv)
    if ok.sum() < 50 or pd.Series(v[ok]).nunique() < 5:
        return []
    f = pd.qcut(pd.Series(v[ok]).rank(method="first"), 5, labels=False).values
    rows = []
    for i in range(5):
        s = f == i
        w = won[ok][s]
        rows.append((i + 1, int(s.sum()), float(np.exp(mv[ok][s].mean()) - 1), w.sum() / p_tab[ok][s].sum(),
                     w.sum() / q[ok][s].sum()))
    return rows


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 65, the market's history, built out\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    if not os.environ.get("WALK_CACHE_USE", "").strip() or not os.environ.get("WALK_ISO_USE", "").strip():
        print("Both saved walks must be named (WALK_CACHE_USE and WALK_ISO_USE): nothing to test")
        return 1
    x, R, XR, num = R62.field(d, t0)
    race, dates = R.race_id.values, R.date.values.astype("datetime64[ns]")
    q, full, w = R62.bsp_label(R, *R62.LABEL_FIT)
    tab = R64.ran_share(R.p_book.values, race)
    off_tab = np.log(np.clip(tab, 1e-12, None))
    mv = R64.moves(R, q, full, tab)
    day = run_market(R, tab_and_books(bdir), mv)
    XR = pd.concat([XR.reset_index(drop=True), R64.move_history(R, mv),
                    dog_history(R, day).reset_index(drop=True), trainer_history(R, mv, day.steam.values)], axis=1)
    groups = R64.group_columns([c for c in XR.columns if not c.startswith("mh_")])
    every = [c for g in groups.values() for c in g]
    parts = {p: [c for c in XR.columns if re.search(pat, c)] for p, pat in PARTS.items()}
    hist = groups[R64.NEW] + [c for v in parts.values() for c in v]
    use = full.astype(bool)
    clean = (R.n_later.fillna(0).values == 0)
    test = use & clean & (dates >= np.datetime64(R64.SPLIT))
    print(f"Runners that ran at TAB's first price: {len(R):,} in {R.race_id.nunique():,} races; scored on "
          f"{pd.unique(race[test]).size:,} races. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    print("## 1. The market's history\n\n| part | inputs | share of the scored runners with a value |\n|---|---|---|")
    for p, cols in [(OLD, groups[R64.NEW])] + list(parts.items()):
        print(f"| {p} | {', '.join(cols)} | " + ", ".join(f"{float(np.isfinite(XR[c].values[test].astype(float)).mean()):.0%}"
                                                          for c in cols) + " |")
    print(f"\nOn the day (the history's source), share of runners that ran: TAB's last price {np.isfinite(day.tab).mean():.0%}, "
          f"the other books' first {np.isfinite(day.books).mean():.0%}; backed (BSP 25% or more shorter than TAB's "
          f"open) {np.nanmean(day.steam):.1%}, drifted {np.nanmean(day.drift):.1%}\n")

    rt, qt, wt = race[test], q[test], R.won.values[test].astype(float)
    tab_d = R64.distance(tab[test], qt, rt)
    _, p_fl, _ = R64.rank_one(XR[R64.BASE], q, off_tab, race, dates, use, test)
    print("## 2. Which way each points, Feb 2025 on (fifth 1 is the lowest; a move above 0 is BSP shorter than TAB's "
          "open)\n")
    print("| input | fifth | runners | today's mean move to BSP | winners / TAB after its bias | winners / BSP corrected |\n"
          "|---|---|---|---|---|---|")
    for c in groups[R64.NEW] + parts["TAB's own moves"] + parts["the other books' opening prices"] + \
            parts["the backed and drifted rates"] + parts["the trainer's last 90 days"]:
        if c.endswith("_n") or c.startswith("mh_nfl"):
            continue
        for f, n, m, a, b in which_way(XR[c].values[test].astype(float), mv[test], wt, p_fl, qt):
            print(f"| {c} | {f} | {n:,} | {m:+.1%} | {a:.3f} | {b:.3f} |")
    print(f"\n({(time.monotonic() - t0) / 60:.0f} minutes in)\n")

    print("## 3. How much of TAB's distance to BSP each closes, Feb 2025 on\n")
    print("| forecast | rounds | distance to BSP (thousandths) | share of TAB's distance closed | winners' log loss |\n"
          "|---|---|---|---|---|")
    print(f"| TAB's book with its favourite bias learnt | | {R64.distance(p_fl, qt, rt):.2f} | "
          f"{1 - R64.distance(p_fl, qt, rt) / tab_d:+.1%} | {V1.ll(p_fl, wt):.4f} |")
    no_hist = [c for c in every if c not in groups[R64.NEW]]
    rows = [("everything without any market history", R64.BASE + no_hist),
            ("Test 82's everything", R64.BASE + every),
            ("TAB's book + all the market history", R64.BASE + hist),
            ("everything + all the market history", R64.BASE + no_hist + hist)]
    rows += [(f"everything + all the market history but {p}", R64.BASE + no_hist + [c for c in hist if c not in cols])
             for p, cols in [(OLD, groups[R64.NEW])] + list(parts.items())]
    bst_all = None
    for name, cols in rows:
        k, p, bst = R64.rank_one(XR[cols], q, off_tab, race, dates, use, test)
        if name == "everything + all the market history":
            bst_all = bst
        dd = R64.distance(p, qt, rt)
        print(f"| {name} | {k:,} | {dd:.2f} | {1 - dd / tab_d:+.1%} | {V1.ll(p, wt):.4f} |", flush=True)
    if bst_all is not None:
        gain = pd.Series(bst_all.feature_importance("gain"), index=bst_all.feature_name())
        gain = gain / max(gain.sum(), 1e-12)
        print(f"\nThe market history's share of the gain: {gain.reindex(hist).fillna(0).sum():.1%}. Its inputs: " +
              ", ".join(f"{c} {v:.1%}" for c, v in gain.reindex(hist).fillna(0).sort_values(ascending=False).items()))
    print(f"\n({(time.monotonic() - t0) / 60:.0f} minutes in)\n")

    print("## 4. Everything with the market history, walked forward from November 2024 from TAB's opening book\n")
    old = R41.MAX_ROUNDS
    R41.MAX_ROUNDS = WALK_ROUNDS
    try:
        p, log, share = R41.walk_correction(R.assign(off=off_tab), XR[R64.BASE + no_hist + hist], q, use)
    finally:
        R41.MAX_ROUNDS = old
    print("; ".join(log) + "\n")
    print("Its inputs by share of gain: " + ", ".join(f"{k} {v:.1%}" for k, v in share.head(25).items()) + "\n")
    ok = test & np.isfinite(p)
    dd = R64.distance(p[ok], q[ok], race[ok])
    print(f"Distance to BSP, Feb 2025 on: {dd:.2f} thousandths ({1 - dd / R64.distance(tab[ok], q[ok], race[ok]):+.1%} "
          f"of TAB's closed); winners' log loss {V1.ll(p[ok], R.won.values[ok]):.4f}\n")
    s_tab = pd.Series(R.p_book.values).groupby(race).transform("sum").values
    x["c_m"] = x.p_book
    x.loc[R["index"].values, "c_m"] = p * s_tab
    ran = x.is_ran.astype(bool).values
    cdir = os.environ.get("WALK_CACHE_DIR", "")
    blends = {"the card's blend": "h_p_x_bet"}
    if R63.read_corrections(x):
        blends["Test 80's corrected blend"] = "c_q"
    f64 = Path(cdir) / f"corr_{R64.TAG}.csv.gz" if cdir else None
    if f64 is not None and f64.exists():
        c = pd.read_csv(f64, dtype={"race_id": "int64", "dog": str}).drop_duplicates(["race_id", "dog"])
        k = pd.DataFrame({"race_id": x.race_id.values[ran].astype("int64"), "dog": x.dog.values[ran].astype(str)})
        x["c_t"] = x.p_book
        x.loc[ran, "c_t"] = k.merge(c, on=["race_id", "dog"], how="left").c_t.values
        blends["Test 82's model"] = "c_t"
    blends["with the market history"] = "c_m"
    if cdir:
        Path(cdir).mkdir(parents=True, exist_ok=True)
        x.loc[ran, ["race_id", "dog", "c_m"]].to_csv(Path(cdir) / f"corr_{TAG}.csv.gz", index=False,
                                                     float_format="%.9g")
    t = x[ran].reset_index(drop=True)
    t["q_bsp"], _ = R58.corrected_bsp(t)
    since = [("Feb 2025 on", R63.SINCE, None)] + R63.HALVES
    print("## 5. The bets at TAB's first price, flat\n")
    R63.table(t, blends, {"TAB's first price": t.price.values}, since)
    c = t[(t.n_later.fillna(0) == 0).values].reset_index(drop=True)
    print("\n## 6. The same, races with nothing scratched after the open\n")
    R63.table(c, blends, {"TAB's first price": c.price.values}, [("Feb 2025 on", R63.SINCE, None)])
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 65")
