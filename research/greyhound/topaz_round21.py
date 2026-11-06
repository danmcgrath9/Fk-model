"""Round 21: the horse book's rules on the dogs (6 Nov 2026, founder: "BRIEF: build a model and betting system like the
Fk-model horse book").

    python research/greyhound/topaz_round21.py DIR LABEL    (BETFAIR_DIR, RACES_DIR; WALK_GRV_RATING / WALK_RELIABLE /
                                                             WALK_LEAD / WALK_DRIFT as the weekly train sets them)

The production model (the weekly train's inputs) on the standard split, scored on the last quarter, both halves:
  1. KL divergence from BSP (the brief's first score; lower is better), against GRV's SP's
  2. THE LAY BOOK at BSP: lay 1 unit when BSP is $15-$40 and at least 1.6x our price, no first starters; a loser
     returns +0.92, a winner costs BSP - 1. And the same at 1.3x and 2x, and at $8-$15
  3. THE BACK BOOK at BSP: back 1 unit on the BSP favourite at $4-$7 when our price is at least 1.6x BSP (8%
     commission). And the dogs' version at $2-$4, and at 1.3x
  4. THE ORDER SHEET at GRV's SP (the dogs have no history of TAB's opens yet, so GRV's SP stands in for the open):
     chance(t) = our chance blended with the price's (Benter, fitted on the early-stopping months); a bet when
     chance(t) x t >= 1.2 (1.15 under $4), our price $1.60-$15, t at most 3x our price, no first starters; Kelly on
     sqrt(our chance x the price's), units = min(10, 125 x k x 5/8), doubled (cap 10) when t >= 2.2x our price and our
     price is under $8. Beside Test 27's 1.3x rule (x75 Kelly, cap 4) on the same races
  5. calibration by track (the brief's metro fix): A/E of our model and of the order sheet's bets, track by track
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round3 as R3         # noqa: E402
import topaz_round9 as R9         # noqa: E402
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402

COMM = 0.08


def kl_from(q: np.ndarray, p: np.ndarray, race: np.ndarray) -> float:
    """Mean over races of KL(q || p) = sum q log(q / p): how far our chances p sit from the market's q."""
    q, p = np.clip(np.asarray(q, float), 1e-12, 1), np.clip(np.asarray(p, float), 1e-12, 1)
    return float(pd.Series(q * np.log(q / p)).groupby(np.asarray(race)).sum().mean())


def lay_returns(won, bsp, comm=COMM) -> np.ndarray:
    """Laying 1 unit (the backer's stake) at BSP: a loser returns the stake less commission, a winner costs BSP - 1."""
    won, bsp = np.asarray(won), np.asarray(bsp, float)
    return np.where(won == 1, -(bsp - 1), 1 - comm)


def back_returns(won, price, comm=0.0) -> np.ndarray:
    won, price = np.asarray(won), np.asarray(price, float)
    return np.where(won == 1, (price - 1) * (1 - comm), -1.0)


def horse_units(p_ours, price, ours_price=None) -> np.ndarray:
    """The horse book's stake: Kelly on sqrt(our chance x the price's chance), units = min(10, 125 x k x 5/8); doubled
    (still capped at 10) when the price is 2.2x our price or more and our price is under $8."""
    p_ours, price = np.asarray(p_ours, float), np.asarray(price, float)
    k = (np.sqrt(p_ours * price) - 1) / np.maximum(price - 1, 1e-9)
    u = np.clip(125 * k * 5 / 8, 0, 10)
    ours_price = 1 / p_ours if ours_price is None else np.asarray(ours_price, float)
    big = (price >= 2.2 * ours_price) & (ours_price < 8)
    return np.where(big, np.minimum(2 * u, 10), u)


def order_sheet(p_ours, p_blend, price, first_starter) -> np.ndarray:
    """The horse book's bet mask at one price t: chance(t) x t >= 1.2 (1.15 when t is under $4), our price $1.60-$15,
    t at most 3x our price, no first starters."""
    ours = 1 / np.clip(np.asarray(p_ours, float), 1e-9, 1)
    price = np.asarray(price, float)
    edge = np.where(price < 4, 1.15, 1.2)
    return ((np.asarray(p_blend) * price >= edge) & (ours >= 1.6) & (ours <= 15) & (price <= 3 * ours)
            & ~np.asarray(first_starter, bool) & np.isfinite(price) & (price > 1))


def book_rows(name, sel, ret, units, won, p_mkt, h):
    """One row per half and all: bets, winners, A/E against the market price's chance, flat return, units."""
    out = []
    for hn, hm in (("1st", h), ("2nd", ~h), ("all", np.ones(len(h), bool))):
        m = sel & hm
        if not m.any():
            out.append(f"| {name} | {hn} | 0 | | | | | |")
            continue
        u = units[m]
        out.append(f"| {name} | {hn} | {m.sum():,} | {int(won[m].sum()):,} | {won[m].sum() / p_mkt[m].sum():.3f} | "
                   f"{ret[m].mean():+.1%} | {u.sum():,.0f} | {(u * ret[m]).sum():+,.1f} |")
    return out


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    df, num, rel, note = W.build_full(d)
    print(f"# {label}: round 21, the horse book's rules on the dogs\n\n{note}\n")
    q75 = df.date.quantile(0.75)
    es_start = q75 - min(pd.Timedelta(days=183), (q75 - df.date.min()) / 4)
    pre, te = df[df.date < q75], df[df.date >= q75].copy()
    fp, es = pre[pre.date < es_start].copy(), pre[pre.date >= es_start].copy()
    recency = 0.5 ** (((es_start - fp.date).dt.days / 365.25).values / 3.0)
    Xf, Xe, Xt = T.features(fp, num, rel), T.features(es, num, rel), T.features(te, num, rel)
    bst, k, _ = R3.fit_weighted(Xf, fp.p_mkt.values.astype(float), fp.race_id, Xe, es.won.values, es.race_id.values,
                                recency, rounds=6000)
    es["p_a"] = V1.race_softmax(bst.predict(Xe, num_iteration=k, raw_score=True), es.race_id.values)
    te["p_a"] = V1.race_softmax(bst.predict(Xt, num_iteration=k, raw_score=True), te.race_id.values)
    first = (te.runs == 0).values

    # 1. KL from BSP, races with a BSP on every runner
    full = te.p_bsp.notna().groupby(te.race_id).transform("all").values
    sp_full = full & te.p_sp.notna().groupby(te.race_id).transform("all").values
    t = te[sp_full]
    h_t = (t.date < t.date.quantile(0.5)).values
    print(f"## 1. Distance from BSP ({k} rounds; {t.race_id.nunique():,} races with BSP and GRV's SP on every runner)\n")
    print("| price | KL from BSP | 1st half | 2nd half |\n|---|---|---|---|")
    for name, col in (("our model", "p_a"), ("GRV's SP", "p_sp")):
        print(f"| {name} | {kl_from(t.p_bsp, t[col], t.race_id):.4f} | {kl_from(t.p_bsp[h_t], t[col][h_t], t.race_id[h_t]):.4f} | "
              f"{kl_from(t.p_bsp[~h_t], t[col][~h_t], t.race_id[~h_t]):.4f} |")

    # 2. the lay book and 3. the back book, at BSP
    b = te[te.bsp.notna() & (te.bsp > 1)].copy() if "bsp" in te else te.iloc[0:0]
    hb = (b.date < b.date.quantile(0.5)).values
    won, bsp, ours = b.won.values, b.bsp.values.astype(float), 1 / b.p_a.values
    pb = 1 / bsp
    fs = (b.runs == 0).values
    print("\n## 2. The lay book at BSP (1 unit, a loser +0.92, a winner -(BSP - 1); no first starters)\n")
    print("| rule | half | lays | winners | A/E vs BSP | return per lay | units laid | units won |\n|---|---|---|---|---|---|---|---|")
    for lo, hi, ratio in ((15, 40, 1.6), (15, 40, 1.3), (15, 40, 2.0), (8, 15, 1.6), (8, 15, 1.3)):
        sel = (bsp >= lo) & (bsp <= hi) & (bsp >= ratio * ours) & ~fs
        ret = lay_returns(won, bsp)
        for line in book_rows(f"BSP ${lo}-${hi}, BSP {ratio:g}x our price", sel, ret, np.ones(len(b)), won, pb, hb):
            print(line)
    fav = (b.groupby("race_id").bsp.rank(method="min") == 1).values
    print("\n## 3. The back book at BSP (1 unit on the BSP favourite, 8% commission)\n")
    print("| rule | half | bets | winners | A/E vs BSP | flat ROI | units staked | units won |\n|---|---|---|---|---|---|---|---|")
    for lo, hi, ratio in ((4, 7, 1.6), (4, 7, 1.3), (2, 4, 1.6), (2, 4, 1.3), (1, 2, 1.3)):
        sel = fav & (bsp >= lo) & (bsp <= hi) & (ours >= ratio * bsp)
        ret = back_returns(won, bsp, COMM)
        for line in book_rows(f"BSP favourite ${lo}-${hi}, our price {ratio:g}x BSP", sel, ret, np.ones(len(b)), won, pb, hb):
            print(line)

    # 4. the order sheet at GRV's SP, beside Test 27's rule
    e_ok, t_ok = es.p_sp.notna().values, te.p_sp.notna().values
    t2 = te[t_ok].copy()
    h2 = (t2.date < t2.date.quantile(0.5)).values
    price = t2.start_price.astype(float).values
    wts, _ = V1.blend(["p_a", "p_sp"], es[e_ok])
    t2["p_blend"] = V1.blend(["p_a", "p_sp"], t2, wts)[1]
    won2, psp = t2.won.values, 1 / price
    fs2 = (t2.runs == 0).values
    ret = back_returns(won2, price)
    print(f"\n## 4. The order sheet at GRV's SP (standing in for TAB's open; blend {wts[0]:.2f} x ours, {wts[1]:.2f} x GRV's)\n")
    print("| rule | half | bets | winners | A/E vs the price | flat ROI | units staked | units won |\n|---|---|---|---|---|---|---|---|")
    sheet = order_sheet(t2.p_a.values, t2.p_blend.values, price, fs2)
    for line in book_rows("the horse book's order sheet and stake", sheet, ret, horse_units(t2.p_a.values, price),
                          won2, psp, h2):
        print(line)
    m, o, u = R9.horse_bets(t2, t2.p_blend.values, t2.p_sp.values, price, 0.0, 1.3, (2, 15))
    for line in book_rows("Test 27's 1.3x rule (x75 Kelly, cap 4)", m, ret, u, won2, psp, h2):
        print(line)
    for line in book_rows("the order sheet, Test 27's stake", sheet, ret, u, won2, psp, h2):
        print(line)
    for line in book_rows("Test 27's bets, the horse book's stake", m, ret, horse_units(t2.p_a.values, price), won2, psp, h2):
        print(line)
    if "drift" in t2:
        keep = ~(t2.drift >= 1.3).values
        for line in book_rows("the order sheet, drift guard 1.3x", sheet & keep, ret, horse_units(t2.p_a.values, price),
                              won2, psp, h2):
            print(line)

    # 5. calibration by track
    print("\n## 5. Calibration by track (the scored quarter)\n")
    print("| track | runners | wins | A/E vs our model | order-sheet bets | their winners | their A/E vs the price |\n"
          "|---|---|---|---|---|---|---|")
    for trk, g in te.groupby("track"):
        if len(g) < 2000:
            continue
        mm = sheet & (t2.track == trk).values
        sh = (f"{mm.sum():,} | {int(won2[mm].sum()):,} | {won2[mm].sum() / psp[mm].sum():.3f}" if mm.sum() else "0 | | ")
        print(f"| {trk} | {len(g):,} | {int(g.won.sum()):,} | {g.won.sum() / g.p_a.sum():.3f} | {sh} |")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 21")
