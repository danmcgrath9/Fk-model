"""Round 66: a second look, with the morning's moves (17 Nov 2026, founder: "Keep going, find more winning bets")

Every bet so far is struck at TAB's first price, when nothing about today's market is known. An hour or two later
TAB's price has moved and the other books have started to open (a median 1.6 hours after TAB, Test 81), and Tests 82
and 83 say the market's moves carry what TAB's opening price misses. So a second look at TAB's price later in the
morning, knowing how the market has moved since the open, is a second chance at a bet. Stated before the run, on
round 64's field, label and distance to BSP, at 60 and 120 minutes after the race's TAB market opened (the price
standing then; a race already run by then is out; TAB's deduction for the dogs scratched after that time):

  - the inputs: everything of Test 82 and the market's history of round 65, from the dog's earlier runs; and the
    morning's moves: each runner's move in TAB's book since its first price (over the runners that ran), its price
    then against its first, and the other books that have opened by then (their first prices' geometric mean
    against TAB's first price, and how many)
  - how much of TAB's distance to BSP each closes at that time, against TAB's book then: TAB's book with its favourite
    bias learnt, everything with the market's history, that with the morning's moves, and TAB's book with the
    morning's moves alone (round 64's ranking fits)
  - everything with the morning's moves, walked forward from TAB's book at that time exactly as round 65's (refitted
    every two months from November 2024, up to 2,000 rounds), and its bets by the card's rule at TAB's price then
    after the deduction, flat, beside the card's blend at that price, realised and by the corrected BSP, in each half
  - the two looks together: round 65's model at TAB's first price (from the walk cache) plus the second look's bets on
    runners it did not already bet, by ratio

    python research/greyhound/topaz_round66.py DIR LABEL    (as round 64)

Counts, sums and rates only: no race, dog or price is printed. The models' inputs are named.
"""
import gzip
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import gbm_v0                     # noqa: E402
import topaz_round32 as R32       # noqa: E402
import topaz_round33 as R33       # noqa: E402
import topaz_round36 as R36       # noqa: E402
import topaz_round41 as R41       # noqa: E402
import topaz_round50 as R50       # noqa: E402
import topaz_round51 as R51       # noqa: E402
import topaz_round57 as R57       # noqa: E402
import topaz_round58 as R58       # noqa: E402
import topaz_round62 as R62       # noqa: E402
import topaz_round63 as R63       # noqa: E402
import topaz_round64 as R64       # noqa: E402
import topaz_round65 as R65       # noqa: E402
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402

KS = (60, 120)
TODAY = ["td_tab", "td_price", "td_books", "td_nbooks"]


def books_by(bdir: str, ks=KS) -> pd.DataFrame:
    """One row per runner (not scratched): Betwatch's race, date, normalised name, and for each k the geometric mean of
    the first prices of the other books (not TAB, not an exchange) that had opened by k minutes after the race's TAB
    market opened (`bk_<k>`, nan when none had) and how many had (`nbk_<k>`)."""
    rows = []
    for f in sorted(Path(bdir).glob("betwatch_VIC_G_*.json.gz")):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for r in json.load(fh).get("races", []):
                start = R32.ts(r.get("start"))
                firsts, per = [], []
                for ru in r.get("runners", []):
                    bks = {}
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
                        if fl:
                            bks[bk] = min(fl)
                    if "Tab" in bks:
                        firsts.append(bks["Tab"][0])
                    if not ru.get("scratched"):
                        per.append((ru.get("name"), bks))
                if not firsts:
                    continue
                open_t = min(firsts)
                for name, bks in per:
                    row = {"bw_race": r.get("id"), "date": r.get("date"), "dog_raw": name}
                    for k in ks:
                        ps = [p for bk, (ts, p) in bks.items() if bk.lower() != "tab"
                              and not any(e in bk.lower() for e in R63.EXCHANGES) and ts <= open_t + 60 * k]
                        row[f"bk_{k}"] = float(np.exp(np.mean(np.log(ps)))) if ps else np.nan
                        row[f"nbk_{k}"] = len(ps)
                    rows.append(row)
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["date"] = pd.to_datetime(out.date, errors="coerce")
    out["_dn"] = gbm_v0.norm_name(out.dog_raw.fillna(""))
    return out.drop(columns="dog_raw").drop_duplicates(["bw_race", "_dn"], keep=False)


def field_at(df: pd.DataFrame, X: pd.DataFrame, fr: pd.DataFrame, k: int):
    """Round 62's field at TAB's price k minutes after the market opened (k = 0: each runner's first price), the card's
    blends at that price, and the runners that ran (R, XR) with TAB's book then as the offset."""
    x = R33.at_time(df, fr, k)
    ran = x.is_ran.astype(bool).values
    x["p_i_bet"] = np.where(ran, x.p_i * (1 - x.s_later.fillna(0)), x.p_book)
    ok = pd.Series((x.price > 1).values).groupby(x.race_id.values).transform("all").values
    x = R57.term_columns(x[ok].reset_index(drop=True))
    for c in R51.OURS.values():
        x[f"h_{c}"] = R51.apply_weights(x, [c, "p_book"], R50.FIXED)
    R, XR = R41.ran_field(x.assign(p_x_bet=x.p_i_bet, pb6=x.p_book), X)
    return x, R, XR


def today_moves(Rk: pd.DataFrame, R0: pd.DataFrame, bk: pd.DataFrame, k: int) -> pd.DataFrame:
    """The morning's moves for Rk's runners: the move in TAB's book since its first price (log of its share over the
    runners that ran, then against at its first price), its price then against its first (positive = shortened), and
    the other books open by then (their first prices against TAB's first, positive = they opened shorter; how many).
    Aligned to Rk's rows."""
    key = ["race_id", "dog"]
    a = pd.DataFrame({"race_id": R0.race_id.values, "dog": R0.dog.astype(str).values,
                      "tab0": R64.ran_share(R0.p_book.values, R0.race_id.values), "price0": R0.price.values})
    a = a.drop_duplicates(key, keep=False)
    b = pd.DataFrame({"race_id": Rk.race_id.values, "dog": Rk.dog.astype(str).values,
                      "tabk": R64.ran_share(Rk.p_book.values, Rk.race_id.values), "pricek": Rk.price.values,
                      "bw_race": Rk.bw_race.values, "_dn": gbm_v0.norm_name(Rk.dog_name.fillna("")).values})
    m = b.merge(a, on=key, how="left")
    if len(bk):
        m = m.merge(bk[["bw_race", "_dn", f"bk_{k}", f"nbk_{k}"]], on=["bw_race", "_dn"], how="left")
    else:
        m[f"bk_{k}"], m[f"nbk_{k}"] = np.nan, np.nan
    assert len(m) == len(Rk), "the morning's moves duplicated runners"
    with np.errstate(divide="ignore", invalid="ignore"):
        out = pd.DataFrame({"td_tab": np.log(m.tabk.values / m.tab0.values),
                            "td_price": np.log(m.price0.values / m.pricek.values),
                            "td_books": np.log(m.price0.values / m[f"bk_{k}"].values),
                            "td_nbooks": m[f"nbk_{k}"].fillna(0).values.astype(float)})
    return out.replace([np.inf, -np.inf], np.nan)


def history_for(Rk: pd.DataFrame, H0: pd.DataFrame) -> pd.DataFrame:
    """The market's history (from the dog's earlier runs, built on the field at TAB's first price) for Rk's runners."""
    k = pd.DataFrame({"race_id": Rk.race_id.values, "dog": Rk.dog.astype(str).values})
    m = k.merge(H0.drop_duplicates(["race_id", "dog"], keep=False), on=["race_id", "dog"], how="left")
    assert len(m) == len(Rk)
    return m.drop(columns=["race_id", "dog"])


def combined(t0: pd.DataFrame, m0: np.ndarray, paid0: np.ndarray, tk: pd.DataFrame, mk: np.ndarray,
             paidk: np.ndarray) -> dict:
    """The first look's bets plus the second look's on runners the first did not bet: bets, winners, realised flat
    units, and the corrected BSP's units and return per bet over the bets with one."""
    k0 = set(zip(t0.race_id.values[m0], t0.dog.astype(str).values[m0]))
    extra = mk & ~np.array([(r, g) in k0 for r, g in zip(tk.race_id.values, tk.dog.astype(str).values)], bool)
    won = np.r_[t0.won.values[m0], tk.won.values[extra]].astype(float)
    paid = np.r_[paid0[m0], paidk[extra]]
    q = np.r_[t0.q_bsp.values[m0], tk.q_bsp.values[extra]].astype(float)
    real = np.where(won == 1, paid - 1, -1.0)
    has = np.isfinite(q)
    v = paid[has] * q[has] - 1
    return dict(n=len(won), extra=int(extra.sum()), w=int(won.sum()), real=float(real.sum()),
                roi=float(real.mean()) if len(real) else np.nan, bsp_units=float(v.sum()),
                bsp=float(v.mean()) if len(v) else np.nan,
                se=float(v.std(ddof=1) / np.sqrt(len(v))) if len(v) > 1 else np.nan)


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 66, a second look, with the morning's moves\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    if not os.environ.get("WALK_CACHE_USE", "").strip() or not os.environ.get("WALK_ISO_USE", "").strip():
        print("Both saved walks must be named (WALK_CACHE_USE and WALK_ISO_USE): nothing to test")
        return 1
    df, num, rel = R51.named_walks(d, t0, with_inputs=True)
    df = df.reset_index(drop=True)
    df["_row"] = np.arange(len(df))
    X = T.features(df, num, rel)
    fr = R33.load(bdir, times=(0,) + KS)
    bk = books_by(bdir)

    # the market's history, from the field at TAB's first price
    x0, R0, XR0 = field_at(df, X, fr, 0)
    del XR0
    q0, full0, _ = R62.bsp_label(R0, *R62.LABEL_FIT)
    tab0 = R64.ran_share(R0.p_book.values, R0.race_id.values)
    mv0 = R64.moves(R0, q0, full0, tab0)
    day = R65.run_market(R0, R65.tab_and_books(bdir), mv0)
    H0 = pd.concat([R64.move_history(R0, mv0), R65.dog_history(R0, day).reset_index(drop=True),
                    R65.trainer_history(R0, mv0, day.steam.values)], axis=1)
    hist = list(H0.columns)
    H0["race_id"], H0["dog"] = R0.race_id.values, R0.dog.astype(str).values
    print(f"\nAt TAB's first price: {len(R0):,} runners that ran in {R0.race_id.nunique():,} races. "
          f"{(time.monotonic() - t0) / 60:.0f} minutes in.\n")

    # the first look's bets, from round 65's walk (the walk cache)
    cdir = os.environ.get("WALK_CACHE_DIR", "")
    f65 = Path(cdir) / f"corr_{R65.TAG}.csv.gz" if cdir else None
    t_open = None
    if f65 is not None and f65.exists():
        c = pd.read_csv(f65, dtype={"race_id": "int64", "dog": str}).drop_duplicates(["race_id", "dog"])
        t_open = x0[x0.is_ran.astype(bool).values].reset_index(drop=True)
        t_open = t_open.merge(c, on=["race_id", "dog"], how="left")
        t_open["q_bsp"], _ = R58.corrected_bsp(t_open)
        print("(round 65's model at TAB's first price read from the walk cache)\n")
    else:
        print("(round 65's model is not in the walk cache: the two looks are not combined)\n")
    del x0

    for k in KS:
        x, R, XR = field_at(df, X, fr, k)
        race, dates = R.race_id.values, R.date.values.astype("datetime64[ns]")
        q, full, _ = R62.bsp_label(R, *R62.LABEL_FIT)
        tab = R64.ran_share(R.p_book.values, race)
        off = np.log(np.clip(tab, 1e-12, None))
        XR = pd.concat([XR.reset_index(drop=True), history_for(R, H0), today_moves(R, R0, bk, k)], axis=1)
        groups = R64.group_columns([c for c in XR.columns if c not in hist and c not in TODAY])
        every = [c for c in sum(groups.values(), []) if c not in groups[R64.NEW]]
        use = full.astype(bool)
        test = use & (R.n_later.fillna(0).values == 0) & (dates >= np.datetime64(R64.SPLIT))
        rt, qt, wt = race[test], q[test], R.won.values[test].astype(float)
        print(f"## {k} minutes after TAB opened\n")
        print(f"{len(R):,} runners that ran in {R.race_id.nunique():,} races at TAB's price then; scored on "
              f"{pd.unique(rt).size:,} races from February 2025. Other books open by then for "
              f"{float((XR.td_nbooks.values[test] > 0).mean()):.0%} of the scored runners. "
              f"{(time.monotonic() - t0) / 60:.0f} minutes in.\n")
        tab_d = R64.distance(tab[test], qt, rt)
        print("| forecast | rounds | distance to BSP (thousandths) | share of TAB's distance then closed | "
              "winners' log loss |\n|---|---|---|---|---|")
        lp0 = XR.lp_tab.values - XR.td_tab.values                       # log of TAB's share at its first price
        both = test & pd.Series(np.isfinite(lp0)).groupby(race).transform("all").values
        if both.any():
            p0 = R64.ran_share(np.exp(np.where(np.isfinite(lp0), lp0, 0.0)), race)[both]
            rb, qb = race[both], q[both]
            d0, dk = R64.distance(p0, qb, rb), R64.distance(tab[both], qb, rb)
            print(f"| TAB's book at its first price ({pd.unique(rb).size:,} of the races) | | {d0:.2f} | "
                  f"{1 - d0 / dk:+.1%} of TAB's then on these races | {V1.ll(p0, R.won.values[both]):.4f} |")
        print(f"| TAB's book then, as it is | | {tab_d:.2f} | +0.0% | {V1.ll(tab[test], wt):.4f} |")
        rows = [("TAB's book then, its favourite bias learnt", R64.BASE),
                ("TAB's book then + the morning's moves", R64.BASE + TODAY),
                ("everything + the market's history", R64.BASE + every + hist),
                ("everything + the market's history + the morning's moves", R64.BASE + every + hist + TODAY)]
        for name, cols in rows:
            kk, p, _ = R64.rank_one(XR[cols], q, off, race, dates, use, test)
            dd = R64.distance(p, qt, rt)
            print(f"| {name} | {kk:,} | {dd:.2f} | {1 - dd / tab_d:+.1%} | {V1.ll(p, wt):.4f} |", flush=True)
        print(f"\n({(time.monotonic() - t0) / 60:.0f} minutes in)\n")

        old = R41.MAX_ROUNDS
        R41.MAX_ROUNDS = R65.WALK_ROUNDS
        try:
            p, log, share = R41.walk_correction(R.assign(off=off), XR[R64.BASE + every + hist + TODAY], q, use)
        finally:
            R41.MAX_ROUNDS = old
        print("Walked: " + "; ".join(log) + "\n")
        print("Its inputs by share of gain: " + ", ".join(f"{a} {v:.1%}" for a, v in share.head(20).items()) + "\n")
        ok = test & np.isfinite(p)
        dd = R64.distance(p[ok], q[ok], race[ok])
        print(f"Walked, distance to BSP from Feb 2025: {dd:.2f} thousandths "
              f"({1 - dd / R64.distance(tab[ok], q[ok], race[ok]):+.1%} of TAB's then closed)\n")
        s_tab = pd.Series(R.p_book.values).groupby(race).transform("sum").values
        x["c_k"] = x.p_book
        x.loc[R["index"].values, "c_k"] = p * s_tab
        t = x[x.is_ran.astype(bool).values].reset_index(drop=True)
        t["q_bsp"], _ = R58.corrected_bsp(t)
        R63.table(t, {"the card's blend": "h_p_x_bet", "with the morning's moves": "c_k"},
                  {f"TAB's price {k} minutes after it opened": t.price.values},
                  [("Feb 2025 on", R63.SINCE, None)] + R63.HALVES)
        if t_open is not None:
            print("\n**The two looks together** (round 65's model at TAB's first price, plus this look's bets on "
                  "runners it did not bet), Feb 2025 on:\n")
            print("| ratio | bets | of them, this look's | a week | winners | realised flat ROI | realised units | "
                  "corrected BSP per bet (SE) | corrected BSP units |\n|---|---|---|---|---|---|---|---|---|")
            s0, sk = R36.in_period(t_open, R63.SINCE, None), R36.in_period(t, R63.SINCE, None)
            weeks = max((t.date[sk].max() - pd.Timestamp(R63.SINCE)).days / 7, 1)
            for r in R63.RATIOS:
                m0, paid0 = R63.bets(t_open, "c_m", t_open.price.values, r)
                mk, paidk = R63.bets(t, "c_k", t.price.values, r)
                s = combined(t_open, m0 & s0, paid0, t, mk & sk, paidk)
                print(f"| {r}x | {s['n']:,} | {s['extra']:,} | {s['n'] / weeks:.1f} | {s['w']:,} | {s['roi']:+.1%} | "
                      f"{s['real']:+,.1f} | {s['bsp']:+.1%} ({s['se']:.1%}) | {s['bsp_units']:+,.1f} |")
        print()
        del x, R, XR, t
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 66")
