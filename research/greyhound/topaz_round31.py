"""Round 31: every rule at TAB's own prices (13 Nov 2026, founder: "Well try all rules", on round 30's 1.3x rule at
TAB's first price).

    python research/greyhound/topaz_round31.py DIR LABEL    (BETWATCH_DIR, BETFAIR_DIR, RACES_DIR; WALK_GRV_RATING /
                                                             WALK_RELIABLE / WALK_LEAD / WALK_SP_WEIGHT / WALK_TRACK /
                                                             WALK_ROUNDS_A as the weekly train; WALK_REFIT_EVERY,
                                                             6 by default; BENCH_PAIRS=yes for the pairs)

THE MODEL PRICES every race from Betwatch's first month (Nov 2022) on, out of sample: the production model refitted
every WALK_REFIT_EVERY months on every race before (topaz_walk.walk), so no price comes from a fit that saw its race.
Each month from six months in, ours is blended with each price's own book (Benter's blend, refitted on the six months
before), as the card does.

THE PRICES, all known when the bet is struck, no commission (a bookmaker's price):
  TAB's first price of the day (Betwatch: close to the open, can miss a sharp early move)
  TAB's last price before the jump
  the best first price of TAB, Sportsbet and Ladbrokes (valued against the blend with TAB's first book)

Every return is after TAB's deduction for dogs scratched after the bet (topaz_round32.table_cents: 100c over the
scratched dog's price then, rounded down, 75c at most), because Test 50 found the rule's value at the open sat mostly in
races with a scratching after it. The model still prices the field that ran, which a bettor at the open cannot see.

A RULE is a segment x a band of the price taken ($1.50-$3, $3-$5, $5-$8, $8-$15, $15-$40, $40-$100, and $1.50-$100) x a
bet: every runner (the market alone), our top pick in the race, or the price at least r times ours (r = 1.0, 1.1, 1.2,
1.3, 1.5, 2.0). The segments are round 29's (box, track, distance, grade, field, Betfair's scheduled start, starts,
days since, last start, first time at the track, GRV's tip, the trainer's second runner, early speed; with
BENCH_PAIRS the box x early speed, box x a quicker beginner inside, early speed x track pairs) and every runner; NOT
the late moves or the pre-play volume, which are not known at the open. Flat stakes.
  1. CHOSEN on the first 60% of race days (300+ bets and a profit), scored ONCE on the last 40%, in halves; with no
     edge, about 2.3% of chosen rules reach z >= 2 by luck
  2. RE-CHOSEN every month of the last 40% on the 12 months before (150+ bets and a profit), then bet the month (a
     runner once per price, however many rules pick it)
Before the rules, each book's log loss on the same races: ours, the blends, TAB's first and last books, GRV's SP, BSP.
"""
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round12 as R12       # noqa: E402
import topaz_round18 as R18       # noqa: E402
import topaz_round29 as R29       # noqa: E402
import topaz_round30 as R30       # noqa: E402
import topaz_round32 as R32       # noqa: E402
import gbm_v0                     # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402

PRICES = {"TAB's first price": ("tab_first", "pb_first"),
          "TAB's last price before the jump": ("tab_last", "pb_last"),
          "best first price of TAB, Sportsbet and Ladbrokes": ("best_first", "pb_first")}
# TAB's deduction off each price's winnings (topaz_round32: 100c over each dog scratched after the bet, at its price
# then, 75c at most): scratchings after the market opened for the first prices, after TAB's last change for the last
DEDUCTION = {"tab_first": "dedt_open", "tab_last": "dedt_last", "best_first": "dedt_open"}
RATIOS = (1.0, 1.1, 1.2, 1.3, 1.5, 2.0)
SIGNALS = ("every runner", "our top pick") + tuple(f"price {r:g}x ours or more" for r in RATIOS)
BANDS = R29.BANDS + [(1.5, 100)]
MIN_CHOOSE, MIN_MONTHLY, WINDOW, BLEND_MONTHS = 300, 150, 12, 6


def best_first(t: pd.DataFrame) -> np.ndarray:
    """The best of TAB's, Sportsbet's and Ladbrokes' first prices, only where TAB has one (the same runners)."""
    cols = [c for c in ("tab_first", "sportsbet_first", "ladbrokes_first") if c in t]
    best = t[cols].where(t[cols] > 1).max(axis=1)
    return best.where(t.tab_first > 1).values


def monthly_blend(df: pd.DataFrame, mkt_col: str, months) -> pd.Series:
    """Ours (p_a) blended with `mkt_col`, the weights refitted each month on the BLEND_MONTHS before it."""
    out = pd.Series(np.nan, index=df.index)
    ok = df.p_a.notna() & df[mkt_col].notna()
    for M in months:
        w = df[ok & (df.date >= (M - BLEND_MONTHS).start_time) & (df.date < M.start_time)]
        cur = ok & (df.date >= M.start_time) & (df.date < (M + 1).start_time)
        if len(w) < 1000 or not cur.any():
            continue
        wb, _ = V1.blend(["p_a", mkt_col], w)
        out[cur] = V1.blend(["p_a", mkt_col], df[cur], wb)[1]
    return out


def bench_segments(t: pd.DataFrame, tracks, pairs) -> dict:
    """Round 29's segments without the ones not known at the open (late moves; pre-play volume is off without its
    cuts), and every runner."""
    seg = {k: v for k, v in R29.segments(t, None, tracks, pairs).items() if " late" not in k}
    return {"every runner": np.ones(len(t), bool), **seg}


def bases(t: pd.DataFrame):
    """(price, bet, lo, hi) -> mask, and price -> flat returns. The band is on the price taken."""
    masks, rets = {}, {}
    race = t.race_id.values
    for pname, (pcol, bcol) in PRICES.items():
        price, pb = t[pcol].values.astype(float), t[bcol].values.astype(float)
        ded = t[DEDUCTION[pcol]].fillna(0).values if DEDUCTION[pcol] in t else np.zeros(len(t))
        rets[pname] = np.where(t.won.values == 1, (price - 1) * (1 - ded), -1.0)
        top = pd.Series(pb).groupby(race).rank(ascending=False, method="first").values == 1
        sig = {"every runner": np.ones(len(t), bool), "our top pick": top}
        for r in RATIOS:
            sig[f"price {r:g}x ours or more"] = price * pb >= r
        for sname in SIGNALS:
            for lo, hi in BANDS:
                masks[(pname, sname, lo, hi)] = sig[sname] & (price >= lo) & (price < hi)
    return masks, rets


def log_loss_table(t: pd.DataFrame) -> None:
    cols = [("ours", "p_a"), ("ours blended with TAB's first book", "pb_first"),
            ("ours blended with TAB's last book", "pb_last"), ("TAB's first book", "p_tab_first"),
            ("TAB's last book", "p_tab_last"), ("GRV's SP", "p_sp"), ("BSP", "p_bsp")]
    cols = [(n, c) for n, c in cols if c in t]
    full = np.ones(len(t), bool)
    for _, c in cols:
        full &= t[c].notna().groupby(t.race_id).transform("all").values
    w = t[full & (t.won == 1).values]
    print(f"Log loss on the {w.race_id.nunique():,} bench races where every book prices every runner (lower is "
          f"better):\n\n| book | log loss | less TAB's first book |\n|---|---|---|")
    base = float(-np.log(w.p_tab_first.clip(1e-9)).mean())
    for n, c in cols:
        ll = float(-np.log(w[c].clip(1e-9)).mean())
        print(f"| {n} | {ll:.4f} | {ll - base:+.4f} |")
    print()


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    bw = R30.load_betwatch(bdir) if bdir and os.path.isdir(bdir) else pd.DataFrame()
    print(f"# {label}: round 31, every rule at TAB's own prices (Betwatch)\n")
    if bw.empty:
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    df, num, rel, note = W.build_full(d)
    df, _, _ = R18.check_features(df, os.environ.get("ISOLYNX_DIR", ""))
    df = R12.tale_columns(df)
    bfd = os.environ.get("BETFAIR_DIR", "")
    if bfd and os.path.isdir(bfd):
        df = R29.betfair_extras(df, bfd)
    every = max(1, int(os.environ.get("WALK_REFIT_EVERY", "6") or 6))
    first_pred = bw.date.min().to_period("M")
    print(f"{note}\nOurs refitted every {every} months from {first_pred} on every race before, {W.ROUNDS_A} rounds; "
          f"{len(num)} inputs. Betwatch: {len(bw):,} runners, {bw.date.min():%Y-%m-%d} to {bw.date.max():%Y-%m-%d}.\n")
    df, log = W.walk(df, num, rel, first_pred, t0, every)
    print("Refits: " + "; ".join(f"{m}: {s}" for m, s in log if "priced by" not in s) + "\n")
    df = R30.join_betwatch(df[df.p_a.notna()].copy(), bw)
    ded = R32.load(bdir)[["date", "_dn", "dedt_open", "dedt_last", "scr_after_open"]]
    df = df.assign(_dn=gbm_v0.norm_name(df.dog_name)).merge(ded, on=["date", "_dn"], how="left").drop(columns="_dn")
    df["best_first"] = best_first(df)
    df["p_tab_first"], df["p_tab_last"] = R30.book_chance(df, "tab_first"), R30.book_chance(df, "tab_last")
    months = pd.period_range(first_pred + BLEND_MONTHS, df.date.max().to_period("M"), freq="M")
    df["pb_first"], df["pb_last"] = monthly_blend(df, "p_tab_first", months), monthly_blend(df, "p_tab_last", months)
    ok = pd.Series((df.pb_first.notna() & df.pb_last.notna() & (df.tab_first > 1) & (df.tab_last > 1)).values)
    t = df[ok.groupby(df.race_id.values).transform("all").values].reset_index(drop=True)   # whole races only
    days = np.sort(t.date.unique())
    cut = pd.Timestamp(days[int(len(days) * 0.6)])
    ch, te = t[t.date < cut].reset_index(drop=True), t[t.date >= cut].reset_index(drop=True)
    mid = te.date.quantile(0.5)
    sc_r = t.drop_duplicates("race_id").scr_after_open
    print(f"TAB's deductions taken off the winnings: {sc_r.gt(0).mean():.1%} of bench races had a runner scratched "
          f"after the open; deduction there {t.dedt_open[t.scr_after_open > 0].median():.0%} (median).\n")
    print(f"Bench: {t.race_id.nunique():,} races, {len(t):,} runners with TAB's first and last price on every runner: "
          f"choosing on {ch.date.min():%Y-%m-%d} to {ch.date.max():%Y-%m-%d} ({ch.race_id.nunique():,} races), scored "
          f"once on {te.date.min():%Y-%m-%d} to {te.date.max():%Y-%m-%d} ({te.race_id.nunique():,} races), halves "
          f"split at {mid:%Y-%m-%d}. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")
    log_loss_table(t)

    tracks = sorted(t.track.astype(str).unique())
    pairs = os.environ.get("BENCH_PAIRS", "").strip().lower() == "yes"
    sc, st = bench_segments(ch, tracks, pairs), bench_segments(te, tracks, pairs)
    bc, rc = bases(ch)
    bt, rt = bases(te)
    h = (te.date < mid).values
    print(f"Segments: {len(st):,}; rules: {len(st) * len(bt):,}\n")

    # the market alone and the model alone: every runner, any price
    print("Every runner, $1.50-$100, by bet:\n\n| price | bet | choosing: bets, return | scored 1st half: bets, "
          "return | 2nd half: bets, return | scored: bets, A/E vs the price paid, return, z |\n|---|---|---|---|---|---|")
    for pname, (pcol, _) in PRICES.items():
        for sname in SIGNALS:
            k = (pname, sname, 1.5, 100)
            mc, mt = bc[k], bt[k]
            n_c, roi_c, _ = R29.stats(rc[pname][mc])
            n, roi, z = R29.stats(rt[pname][mt])
            r1, r2 = R29.stats(rt[pname][mt & h]), R29.stats(rt[pname][mt & ~h])
            ae = te.won.values[mt].sum() / (1 / te[pcol].values[mt]).sum() if mt.any() else np.nan
            print(f"| {pname} | {sname} | {n_c:,}, {roi_c:+.1%} | {r1[0]:,}, {r1[1]:+.1%} | {r2[0]:,}, {r2[1]:+.1%} | "
                  f"{n:,}, {ae:.3f}, {roi:+.1%}, {z:+.1f} |")

    # 1. chosen once, scored once
    rows, tried_by = [], {p: 0 for p in PRICES}
    for bk, bm in bc.items():
        pname = bk[0]
        r = rc[pname]
        for sname, sm in sc.items():
            m = bm & sm
            n = int(np.count_nonzero(m))
            if n < MIN_CHOOSE:
                continue
            tried_by[pname] += 1
            n_c, roi_c, z_c = R29.stats(r[m])
            if roi_c <= 0:
                continue
            mt = bt[bk] & st[sname]
            ret = rt[pname][mt]
            n_t, roi_t, z_t = R29.stats(ret)
            r1, r2 = R29.stats(rt[pname][mt & h]), R29.stats(rt[pname][mt & ~h])
            pcol = PRICES[pname][0]
            ae = te.won.values[mt].sum() / (1 / te[pcol].values[mt]).sum() if mt.any() else np.nan
            rows.append(((sname,) + bk, n_c, roi_c, z_c, n_t, roi_t, z_t, r1, r2, ae))
    print("\n| price | rules with 300+ bets on the choosing years | chosen (a profit there) | chosen, profit in the "
          "scored years | chosen, profit in both halves | chosen, z >= 2 on the scored years | z >= 2 expected by luck |"
          "\n|---|---|---|---|---|---|---|")
    for pname in PRICES:
        rr = [r for r in rows if r[0][1] == pname]
        print(f"| {pname} | {tried_by[pname]:,} | {len(rr):,} | {sum(r[5] > 0 for r in rr if r[4]):,} | "
              f"{sum(1 for r in rr if r[7][0] and r[8][0] and r[7][1] > 0 and r[8][1] > 0):,} | "
              f"{sum(r[6] >= 2 for r in rr):,} | {0.023 * len(rr):.1f} |")
    print("\nChosen rules with z >= 2 on the scored years, best first (at most 40):\n")
    print("| rule | choosing years: bets, return, z | scored 1st half: bets, return | 2nd half: bets, return | "
          "scored: bets, A/E vs the price paid, return, z |\n|---|---|---|---|---|")
    for i, (key, n_c, roi_c, z_c, n, roi, z, r1, r2, ae) in enumerate(sorted(rows, key=lambda r: -r[6])):
        if z < 2 or i >= 40:
            break
        seg, pname, sname, lo, hi = key
        both = r1[0] and r2[0] and r1[1] > 0 and r2[1] > 0
        print(f"| {pname}, {sname}: {seg}, ${lo:g}-${hi:g} | {n_c:,}, {roi_c:+.1%}, {z_c:+.1f} | {r1[0]:,}, "
              f"{r1[1]:+.1%} | {r2[0]:,}, {r2[1]:+.1%} | {n:,}, {ae:.3f}, {roi:+.1%}, {z:+.1f}"
              f"{' **both halves**' if both else ''} |")

    # 2. re-chosen every month
    bet_months = pd.period_range(cut.to_period("M"), t.date.max().to_period("M"), freq="M")
    bets, picked = {p: [] for p in PRICES}, {p: [] for p in PRICES}
    for M in bet_months:
        w = t[(t.date >= (M - WINDOW).start_time) & (t.date < M.start_time)].reset_index(drop=True)
        cur = t[(t.date >= max(M.start_time, cut)) & (t.date < (M + 1).start_time)].reset_index(drop=True)
        if cur.empty or w.empty:
            continue
        sw, sm_ = bench_segments(w, tracks, pairs), bench_segments(cur, tracks, pairs)
        bw_, rw = bases(w)
        bcur, rcur = bases(cur)
        hit = {p: np.zeros(len(cur), bool) for p in PRICES}
        n_rules = {p: 0 for p in PRICES}
        for bk, bm in bw_.items():
            for sname, sm in sw.items():
                m = bm & sm
                if np.count_nonzero(m) >= MIN_MONTHLY and rw[bk[0]][m].mean() > 0:
                    hit[bk[0]] |= bcur[bk] & sm_[sname]
                    n_rules[bk[0]] += 1
        for pname, (pcol, _) in PRICES.items():
            hm = hit[pname]
            bets[pname].append(cur[hm].assign(ret=rcur[pname][hm], price=cur[pcol].values[hm]))
            picked[pname].append(n_rules[pname])
    print(f"\n## Re-chosen every month on the {WINDOW} months before ({MIN_MONTHLY}+ bets and a profit there), then bet\n")
    print("| price | rules chosen a month | half | bets | winners | A/E vs the price paid | return | units | months in "
          "profit |\n|---|---|---|---|---|---|---|---|---|")
    for pname in PRICES:
        allb = pd.concat(bets[pname]) if bets[pname] else pd.DataFrame()
        if allb.empty:
            print(f"| {pname} | {min(picked[pname], default=0)}-{max(picked[pname], default=0)} | all | 0 | | | | | |")
            continue
        for hn, hm in (("1st", allb.date < mid), ("2nd", allb.date >= mid), ("all", allb.date.notna())):
            x = allb[hm]
            if x.empty:
                continue
            bym = x.groupby(x.date.dt.to_period("M")).ret.sum()
            print(f"| {pname} | {min(picked[pname])}-{max(picked[pname])} | {hn} | {len(x):,} | {int(x.won.sum()):,} | "
                  f"{x.won.sum() / (1 / x.price).sum():.3f} | {x.ret.mean():+.1%} | {x.ret.sum():+,.0f} | "
                  f"{(bym > 0).sum()} of {len(bym)} |")
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 31")
