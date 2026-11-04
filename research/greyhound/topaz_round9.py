"""Round 9: the gallops value rule on the dogs (5 Nov 2026, founder: "the value rule from the horse racing, the 1.3x
pricing bands with Benter or quarter Kelly, would work with the open TAB price").

    python research/greyhound/topaz_round9.py DIR LABEL      (BETFAIR_DIR, RACES_DIR as before; results only)

The gallops rule (research/form_gbm/README.md, Staking and Sizing sections): Benter's stage 2, a logit blend of our
chance with the market's; a value bet when the market price is at least RATIO times the blended price; our price
$2-$15; staked Kelly x75 units on a chance halfway between the blend and the market (Baker and McHale), capped at 4
units. On the horses it made about +50% at the open and broke even at BSP. Here it runs on the dogs' best model so far
(round 8's F2: D1 + preview + tips, 6,000-round cap), fitted once on the standard split, blend weights fitted on the
early-stopping months, scored once on the same 22,841 races, at two prices we hold history for: GRV's SP (no
commission) and BSP (8% on winnings). Ratio 1.3 is the founder's and is the headline, decided before the run; 1.2 (the
gallops live line) and 1.1 ride beside it, and the price band is reported both ways. TAB's open is not in any history
we hold, so this is the test the open will be scored on, not the open's answer.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_preview_test as PT   # noqa: E402
import topaz_round3 as R3         # noqa: E402
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402

RATIOS = [1.3, 1.2, 1.1]
BANDS = [(2.0, 15.0), (1.01, 1000.0)]
KELLY_X, CAP = 75.0, 4.0


def horse_bets(df, p_blend, p_mkt, price, comm, ratio, band):
    """Mask, odds after commission and Kelly units for the gallops rule on one price."""
    o = 1 + (price - 1) * (1 - comm)
    ours = 1 / np.clip(p_blend, 1e-9, 1)
    m = np.isfinite(price) & (price > 1) & (price >= ratio * ours) & (ours >= band[0]) & (ours < band[1])
    pk = 0.5 * p_blend + 0.5 * p_mkt
    f = (pk * o - 1) / np.maximum(o - 1, 1e-9)
    units = np.clip(KELLY_X * f, 0, CAP)
    m = m & (units > 0)
    return m, o, units


def summary(df, m, o, units, price):
    idx = np.flatnonzero(m)
    if not len(idx):
        return dict(n=0)
    idx = idx[np.argsort(df.date.values[idx], kind="stable")]
    won = df.won.values[idx]
    ret_flat = np.where(won == 1, o[idx] - 1, -1.0)
    ret_k = units[idx] * ret_flat
    cum = np.cumsum(ret_k)
    dd = float((np.maximum.accumulate(np.r_[0, cum]) - np.r_[0, cum]).max())
    run = worst = 0
    for w in won:
        run = 0 if w else run + 1
        worst = max(worst, run)
    return dict(n=len(idx), w=int(won.sum()), ae=won.sum() / (1 / price[idx]).sum(), flat=ret_flat.mean(),
                staked=units[idx].sum(), kroi=ret_k.sum() / units[idx].sum(), kunits=ret_k.sum(), dd=dd, run=worst,
                avg=units[idx].mean())


def main(d, label):
    df, num, rel, bsp_note = W.build(d)
    if "is_best_bet" not in df and "isBestBet" in df:
        df["is_best_bet"] = df.isBestBet
    df, fpv, _ = PT.preview_features(df)
    ftip = []
    races_dir = os.environ.get("RACES_DIR", "")
    if races_dir and os.path.isdir(races_dir):
        from greyhound.races import load_races, tip_features
        df, ftip = tip_features(df, load_races(races_dir))
    df = df.copy()
    cols = num + fpv + ftip
    q75 = df.date.quantile(0.75)
    es_start = q75 - min(pd.Timedelta(days=183), (q75 - df.date.min()) / 4)
    pre, te = df[df.date < q75], df[df.date >= q75].copy()
    fp, es = pre[pre.date < es_start], pre[pre.date >= es_start].copy()
    recency = 0.5 ** (((es_start - fp.date).dt.days / 365.25).values / 3.0)
    Xf, Xe, Xt = T.features(fp, cols, rel), T.features(es, cols, rel), T.features(te, cols, rel)
    bst, k, _ = R3.fit_weighted(Xf, fp.p_mkt.values.astype(float), fp.race_id, Xe, es.won.values, es.race_id.values,
                                recency, rounds=6000)
    es["p_a"] = V1.race_softmax(bst.predict(Xe, num_iteration=k, raw_score=True), es.race_id.values)
    te["p_a"] = V1.race_softmax(bst.predict(Xt, num_iteration=k, raw_score=True), te.race_id.values)
    h = (te.date < te.date.quantile(0.5)).values
    print(f"# {label}: round 9, the gallops value rule on the dogs\n\n{bsp_note}\nmodel: D1 + preview + tips, {k} rounds; "
          f"scored on {te.race_id.nunique():,} races from {te.date.min():%Y-%m-%d}\n")
    for pname, col, pcol, comm in (("GRV's SP, no commission", "start_price", "p_sp", 0.0),
                                   ("BSP, 8% commission on winnings", "bsp", "p_bsp", 0.08)):
        e_ok, t_ok = es[pcol].notna().values, te[pcol].notna().values
        w, _ = V1.blend(["p_a", pcol], es[e_ok])
        t2 = te[t_ok].copy()
        t2["p_blend"] = V1.blend(["p_a", pcol], t2, w)[1]
        price = t2[col].astype(float).values
        hh = h[t_ok]
        print(f"## At {pname}\n\nBenter blend weights (ours, market) fitted on the early-stopping months: {w[0]:.2f}, {w[1]:.2f}; "
              f"{t2.race_id.nunique():,} races\n")
        print("| ratio | our price | half | bets | winners | A/E | flat ROI | Kelly x75 units staked | Kelly ROI | units won | worst drawdown (units) | longest losing run |")
        print("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for ratio in RATIOS:
            for band in BANDS:
                bname = f"${band[0]:g}-${band[1]:g}" if band[1] < 1000 else "any"
                for hn, hm in (("1st", hh), ("2nd", ~hh)):
                    sub = t2[hm]
                    m, o, u = horse_bets(sub, sub.p_blend.values, sub[pcol].values, price[hm], comm, ratio, band)
                    r = summary(sub, m, o, u, price[hm])
                    if r["n"]:
                        print(f"| {ratio:g}x | {bname} | {hn} | {r['n']:,} | {r['w']:,} | {r['ae']:.3f} | {r['flat']:+.1%} | "
                              f"{r['staked']:,.0f} (avg {r['avg']:.2f}) | {r['kroi']:+.1%} | {r['kunits']:+,.0f} | {r['dd']:,.0f} | {r['run']} |")
                    else:
                        print(f"| {ratio:g}x | {bname} | {hn} | 0 | | | | | | | | |")
        print()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 9")
