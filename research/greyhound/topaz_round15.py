"""Round 15: sharpen the price, and the place market (6 Nov 2026, founder: "keep testing the model while we wait").

    python research/greyhound/topaz_round15.py DIR LABEL   (BETFAIR_DIR, RACES_DIR; WALK_GRV_RATING / WALK_RELIABLE /
                                                            WALK_LEAD as the weekly train sets them; results only)

The production model (the weekly train's inputs) fitted on the standard split and scored on the last quarter, then:

PART A, SHARPEN. Test 24: the SP favourite wins 16% more than our model says. Is the model too flat? A power on its
race softmax, p ~ p_model ^ a, with `a` fitted on the early-stopping months (a > 1 sharpens: favourites shorter,
outsiders longer). Log loss and gap to BSP with and without, both halves, and the SP favourite's A/E after.

PART B, THE PLACE MARKET. Betfair's place market is thinner than its win market, and our model has never been scored
on it. Each race's number of places is read from Betfair's own place result (2 or 3); our place chance is Harville's
from our win chances (the chance of finishing in the first k, each later place drawn from the dogs left in proportion
to their win chances); the market's is 1 / place BSP rescaled to add to k. Binary log loss and A/E for ours, the
market's, and a logit blend of the two fitted on the early-stopping months; then the gallops value rule on place BSP
(8% commission): a bet when place BSP is at least RATIO times the blended place price, Kelly x75 on the chance halfway
between the blend and the market, cap 4, both halves.
"""
import os
import sys
from itertools import permutations

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round12 as R12       # noqa: E402
import topaz_round3 as R3         # noqa: E402
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402

COMM, KELLY_X, CAP = 0.08, 75.0, 4.0


def harville_place(p: np.ndarray, k: int) -> np.ndarray:
    """Each runner's chance of finishing in the first k, from win chances p (one race, summing to 1), by Harville:
    the dog in each later place is drawn from those left in proportion to their win chances."""
    p = np.asarray(p, dtype=float)
    n = len(p)
    out = np.zeros(n)
    k = min(k, n)
    for ahead in range(k):                         # the runner finishes in place ahead+1
        if ahead == 0:
            out += p
            continue
        for seq in permutations(range(n), ahead):  # who filled the places before it
            prob, left = 1.0, 1.0
            for j in seq:
                prob *= p[j] / left
                left -= p[j]
            if left <= 1e-12:
                continue
            rest = np.ones(n, bool)
            rest[list(seq)] = False
            out[rest] += prob * p[rest] / left
    return out


def place_columns(t: pd.DataFrame, pcol: str) -> pd.DataFrame:
    """k (places paid, from Betfair's result), our Harville place chance from `pcol`, and the market's from place
    BSP; only races where every runner has a place BSP and k is 2 or 3."""
    t = t.copy()
    t["k"] = t.groupby("race_id").placed.transform("sum")
    full = (t.PLACE_BSP > 1).groupby(t.race_id).transform("all")
    t = t[full & t.k.isin([2, 3])].copy()
    t["p_place"] = np.nan
    for _, idx in t.groupby("race_id").groups.items():
        g = t.loc[idx]
        p = g[pcol].values / g[pcol].values.sum()
        t.loc[idx, "p_place"] = harville_place(p, int(g.k.iloc[0]))
    inv = 1 / t.PLACE_BSP
    t["q_place"] = inv / inv.groupby(t.race_id).transform("sum") * t.k
    return t


def logit(x):
    x = np.clip(np.asarray(x, float), 1e-6, 1 - 1e-6)
    return np.log(x / (1 - x))


def bll(p, y):
    p = np.clip(np.asarray(p, float), 1e-9, 1 - 1e-9)
    y = np.asarray(y, float)
    return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())


def fit_place_blend(e: pd.DataFrame):
    """Weights (a, b, c) of logit(blend) = a logit(ours) + b logit(market) + c, by binary log loss on e."""
    from scipy.optimize import minimize
    xo, xm, y = logit(e.p_place), logit(e.q_place), e.placed.values

    def f(w):
        return bll(1 / (1 + np.exp(-(w[0] * xo + w[1] * xm + w[2]))), y)
    return minimize(f, [0.5, 0.5, 0.0], method="Nelder-Mead").x


def apply_blend(t, w):
    return 1 / (1 + np.exp(-(w[0] * logit(t.p_place) + w[1] * logit(t.q_place) + w[2])))


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    df, num, rel, note = W.build_full(d)
    print(f"# {label}: round 15, sharpen the price, and the place market\n\n{note}\n")
    R12.EXTRA[:] = ["PLACE_BSP", "placed"]
    df, have = R12.add_betfair_extra(df)
    q75 = df.date.quantile(0.75)
    es_start = q75 - min(pd.Timedelta(days=183), (q75 - df.date.min()) / 4)
    pre, te = df[df.date < q75], df[df.date >= q75].copy()
    fp, es = pre[pre.date < es_start], pre[pre.date >= es_start].copy()
    recency = 0.5 ** (((es_start - fp.date).dt.days / 365.25).values / 3.0)
    Xf, Xe, Xt = T.features(fp, num, rel), T.features(es, num, rel), T.features(te, num, rel)
    bst, k, _ = R3.fit_weighted(Xf, fp.p_mkt.values.astype(float), fp.race_id, Xe, es.won.values, es.race_id.values,
                                recency, rounds=6000)
    se, st = bst.predict(Xe, num_iteration=k, raw_score=True), bst.predict(Xt, num_iteration=k, raw_score=True)
    es["p_a"], te["p_a"] = V1.race_softmax(se, es.race_id.values), V1.race_softmax(st, te.race_id.values)

    # PART A: sharpen
    hb, hbe = te.p_bsp.notna().values, es.p_bsp.notna().values
    h = (te.date < te.date.quantile(0.5)).values
    grid = np.round(np.arange(0.80, 1.61, 0.02), 2)
    lle = [V1.ll(V1.race_softmax(a * se, es.race_id.values)[hbe], es.won.values[hbe]) for a in grid]
    a_best = float(grid[int(np.argmin(lle))])
    te["p_s"] = V1.race_softmax(a_best * st, te.race_id.values)
    w = te.won.values
    b_all, b1, b2 = (V1.ll(te.p_bsp.values[m], w[m]) for m in (hb, hb & h, hb & ~h))
    print(f"## Part A: sharpen ({k} rounds, {len(num)} inputs; {te[hb].race_id.nunique():,} scored races with BSP, BSP {b_all:.4f})\n")
    print(f"Power fitted on the early-stopping months: {a_best:.2f} (1.00 = as fitted; early-stopping log loss "
          f"{lle[list(grid).index(1.0)]:.4f} at 1.00, {min(lle):.4f} at {a_best:.2f})\n")
    print("| price | log loss | gap to BSP | 1st half | 2nd half | SP favourite A/E |\n|---|---|---|---|---|---|")
    sp = te.start_price.where(te.start_price > 1)
    fav = (sp.groupby(te.race_id).rank(method="min") == 1).values & hb
    for name, col in (("the model as fitted", "p_a"), (f"sharpened, power {a_best:.2f}", "p_s")):
        p = te[col].values
        l, l1, l2 = V1.ll(p[hb], w[hb]), V1.ll(p[hb & h], w[hb & h]), V1.ll(p[hb & ~h], w[hb & ~h])
        print(f"| {name} | {l:.4f} | {l - b_all:+.4f} | {l1 - b1:+.4f} | {l2 - b2:+.4f} | {w[fav].sum() / p[fav].sum():.3f} |")

    # PART B: the place market
    if "PLACE_BSP" not in have:
        print("\nBetfair's files carry no place BSP: Part B skipped")
        return 0
    use = "p_s" if a_best != 1.0 else "p_a"
    es["p_s"] = V1.race_softmax(a_best * se, es.race_id.values)
    e2 = place_columns(es[es.p_bsp.notna()], use)
    t2 = place_columns(te[te.p_bsp.notna()], use)
    wb = fit_place_blend(e2)
    t2["p_blend"] = apply_blend(t2, wb)
    h2 = (t2.date < t2.date.quantile(0.5)).values
    print(f"\n## Part B: the place market, {t2.race_id.nunique():,} scored races with a place BSP on every runner "
          f"(2 places in {(t2.groupby('race_id').k.first() == 2).mean():.0%}, 3 in the rest)\n")
    print(f"Blend fitted on the early-stopping months: logit(blend) = {wb[0]:.2f} x ours + {wb[1]:.2f} x market "
          f"{'+' if wb[2] >= 0 else '-'} {abs(wb[2]):.2f}\n")
    print("| place chance | binary log loss | 1st half | 2nd half | A/E |\n|---|---|---|---|---|")
    y = t2.placed.values
    for name, col in (("ours (Harville from our win chances)", "p_place"), ("place BSP", "q_place"), ("the blend", "p_blend")):
        p = t2[col].values
        print(f"| {name} | {bll(p, y):.4f} | {bll(p[h2], y[h2]):.4f} | {bll(p[~h2], y[~h2]):.4f} | {y.sum() / p.sum():.3f} |")
    print("\n| our place price | runners | placed | A/E vs ours | A/E vs place BSP |\n|---|---|---|---|---|")
    pr = 1 / t2.p_place
    for lo, hi in ((1, 1.5), (1.5, 2), (2, 3), (3, 5), (5, 10), (10, 1000)):
        m = ((pr >= lo) & (pr < hi)).values
        if m.sum() >= 300:
            g = t2[m]
            print(f"| ${lo:g}-${hi:g} | {m.sum():,} | {int(g.placed.sum()):,} | {g.placed.sum() / g.p_place.sum():.3f} | "
                  f"{g.placed.sum() / g.q_place.sum():.3f} |")
    print("\n| rule (place BSP, 8% commission) | half | bets | placed | flat ROI | units staked | Kelly ROI | units won |\n"
          "|---|---|---|---|---|---|---|---|")
    price = t2.PLACE_BSP.values
    o = 1 + (price - 1) * (1 - COMM)
    for ratio in (1.1, 1.2, 1.3):
        ours = 1 / t2.p_blend.values
        m = (price >= ratio * ours) & (ours >= 1.2) & (ours < 10)
        pk = 0.5 * t2.p_blend.values + 0.5 * t2.q_place.values
        u = np.clip(KELLY_X * (pk * o - 1) / np.maximum(o - 1, 1e-9), 0, CAP)
        m = m & (u > 0)
        for hn, hm in (("1st", h2), ("2nd", ~h2)):
            sel = m & hm
            if not sel.any():
                print(f"| {ratio:g}x | {hn} | 0 | | | | | |")
                continue
            ret = np.where(y[sel] == 1, o[sel] - 1, -1.0)
            print(f"| {ratio:g}x, our place price $1.20-$10 | {hn} | {sel.sum():,} | {int(y[sel].sum()):,} | {ret.mean():+.1%} | "
                  f"{u[sel].sum():,.0f} | {(u[sel] * ret).sum() / u[sel].sum():+.1%} | {(u[sel] * ret).sum():+,.0f} |")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 15")
