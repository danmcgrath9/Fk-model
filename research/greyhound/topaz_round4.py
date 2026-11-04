"""Round 4: a staking plan worth trusting (4 Nov 2026, founder: "then we have to get staking and ROI").

    python research/greyhound/topaz_round4.py DIR LABEL     (BETFAIR_DIR as for topaz_theories.py; results only)

The model is round 3's chosen one (B2 + B2w ensemble). What changes is how bets are picked and sized, and that
every rule is CHOSEN ON THE EARLY-STOPPING MONTHS and only then scored on the scored quarter (both halves), so the
reported ROI is not the best of many tries on the same races:
  1. calibration: the model's chances raised to a power and renormalised in the race, the power fitted on the
     early-stopping months (Test 11's Kelly blew up on uncalibrated chances);
  2. one bet a race: only the runner with the largest edge;
  3. price bands ($1.50-$3, $3-$5, $5-$8, $8-$13, $13-$21) and edges of 10, 20, 30 and 50%;
  4. sizing: flat, and fractional Kelly (0.1 and 0.25) on the calibrated chance, capped at 2% of the bank;
  5. for the chosen rule: ROI by month, the longest losing run, and the worst drawdown.
At GRV's SP (no commission) and at BSP (8% commission on winnings). Both prices are set at the jump: these test
the price, not a bet we could place.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import topaz_round3 as R3    # noqa: E402
import topaz_theories as T   # noqa: E402
import topaz_v1 as V1        # noqa: E402

BANDS = [(1.5, 3), (3, 5), (5, 8), (8, 13), (13, 21), (1.5, 21)]
EDGES = [0.10, 0.20, 0.30, 0.50]


def _power(p, race, a):
    s = pd.Series(np.clip(p, 1e-12, 1) ** a)
    return (s / s.groupby(np.asarray(race)).transform("sum")).values


def calibrate(p, race, won, power=None):
    """p ** power renormalised within the race; the power that minimises winner log loss when not given."""
    if power is None:
        grid = np.arange(0.6, 1.61, 0.05)
        power = float(grid[int(np.argmin([V1.ll(_power(p, race, a), won) for a in grid]))])
    return _power(p, race, power), power


def selections(df, p, price, comm, edge, band, one_per_race):
    o = 1 + (price - 1) * (1 - comm)
    ev = p * o - 1
    m = (ev >= edge) & (price >= band[0]) & (price < band[1]) & np.isfinite(price)
    if one_per_race:
        best = pd.Series(np.where(m, ev, -np.inf)).groupby(df.race_id.values).transform("max").values
        m = m & (ev == best)
    return m, o


def result(df, m, o, p, sizing, raw):
    idx = np.flatnonzero(m)
    if not len(idx):
        return dict(n=0)
    idx = idx[np.argsort(df.date.values[idx], kind="stable")]
    won = df.won.values[idx]
    price = o[idx]
    out = dict(n=len(idx), w=int(won.sum()), ae=won.sum() / (1 / raw[idx]).sum(),
               roi=np.where(won == 1, price - 1, -1).mean())
    bank, peak, dd, run, worst_run = 1.0, 1.0, 0.0, 0, 0
    for i, w, oo in zip(idx, won, price):
        f = 0.01 if sizing == 0 else min(sizing * (p[i] * oo - 1) / (oo - 1), 0.02)
        bank *= 1 + f * ((oo - 1) if w else -1)
        peak, dd = max(peak, bank), max(dd, 1 - bank / max(peak, 1e-12))
        run = 0 if w else run + 1
        worst_run = max(worst_run, run)
    out.update(bank=bank, dd=dd, run=worst_run)
    return out


def main(d, label):
    df = V1.build(d)
    for src, dst in (("rating", "topaz_rating"), ("totalFormCount", "total_form"), ("careerPrizeMoney", "career_prize"),
                     ("prizeMoney", "prize"), ("last5", "last5")):
        if dst not in df and src in df:
            df[dst] = df[src]
    df, f2 = T.V2.add_map(df)
    df = df.reset_index(drop=True)
    df, f3 = T.t3(df)
    df, f4 = T.t4(df)
    df, f5, _ = T.t5(df, df.columns)
    df, f6 = T.t6(df)
    df, bsp_note = T.add_bsp(df)
    df = df.sort_values(["date", "race_id", "box"]).reset_index(drop=True)
    df["p_mkt"] = df.p_bsp.fillna(df.p_sp) if "p_bsp" in df else df.p_sp
    df, fnew, _ = R3.new_features(df)
    df = df.copy()

    q75 = df.date.quantile(0.75)
    span = q75 - df.date.min()
    es_start = q75 - min(pd.Timedelta(days=183), span / 4)
    pre, te = df[df.date < q75], df[df.date >= q75].copy()
    fp, es = pre[pre.date < es_start], pre[pre.date >= es_start].copy()
    base = list(dict.fromkeys(V1.NUM + f2 + f3 + f4 + f5 + f6))
    num = base + fnew
    rel = V1.REL + [f for f in ["style_early", "style_led_rate", "style_gain", "dog_place_91D", "dog_won_91D",
                                "trainer_id_won_91D", "box_vacancy_ratio", "last5_mean", "mkt_lsp_mean5",
                                "mkt_prev_lsp", "time_rating_mean5_trk", "time_rating_ewm", "split_rating_ewm",
                                "class_step"] if f in num]
    recency = 0.5 ** (((es_start - fp.date).dt.days / 365.25).values / 3.0)
    Xf, Xe, Xt = T.features(fp, num, rel), T.features(es, num, rel), T.features(te, num, rel)
    preds = {}
    for name, target in (("a", "p_mkt"), ("b", "won")):
        bst, k, _ = R3.fit_weighted(Xf, fp[target].values.astype(float), fp.race_id, Xe, es.won.values,
                                    es.race_id.values, recency)
        preds[name] = (V1.race_softmax(bst.predict(Xe, num_iteration=k, raw_score=True), es.race_id.values),
                       V1.race_softmax(bst.predict(Xt, num_iteration=k, raw_score=True), te.race_id.values))
    es["a"], es["b"], te["a"], te["b"] = preds["a"][0], preds["b"][0], preds["a"][1], preds["b"][1]
    w, pe = V1.blend(["a", "b"], es)
    _, pt = V1.blend(["a", "b"], te, w)
    pe_c, power = calibrate(pe, es.race_id.values, es.won.values)
    pt_c, _ = calibrate(pt, te.race_id.values, te.won.values, power)
    hb = te.p_bsp.notna().values
    print(f"# {label}: round 4, staking\n\n{bsp_note}\nmodel: round 3's B2 + B2w ensemble ({w[0]:.2f} / {w[1]:.2f}); "
          f"calibration power {power:.2f} fitted on the early-stopping months; scored log loss {V1.ll(pt[hb], te.won.values[hb]):.4f} "
          f"raw, {V1.ll(pt_c[hb], te.won.values[hb]):.4f} calibrated (BSP {V1.ll(te.p_bsp.values[hb], te.won.values[hb]):.4f})\n")

    h = (te.date < te.date.quantile(0.5)).values
    for pname, col, comm in (("GRV's SP, no commission", "start_price", 0.0), ("BSP, 8% commission", "bsp", 0.08)):
        if col not in te:
            continue
        print(f"\n## {pname}\n")
        # choose on the early-stopping months: flat ROI, at least 300 bets
        cands = []
        for one in (False, True):
            for band in BANDS:
                for e in EDGES:
                    m, o = selections(es, pe_c, es[col].values, comm, e, band, one)
                    r = result(es, m, o, pe_c, 0, es[col].values)
                    if r["n"] >= 300:
                        cands.append((r["roi"], one, band, e, r["n"]))
        cands.sort(reverse=True)
        print("Best five rules on the early-stopping months (flat ROI; at least 300 bets):\n")
        print("| one a race | price band | edge | bets | ROI there |\n|---|---|---|---|---|")
        for roi, one, band, e, n in cands[:5]:
            print(f"| {'yes' if one else 'no'} | ${band[0]:g}-${band[1]:g} | {e:.0%} | {n:,} | {roi:+.1%} |")
        if not cands:
            print("(no rule had 300 bets)")
            continue
        _, one, band, e, _ = cands[0]
        print(f"\n**Chosen there: one a race {'yes' if one else 'no'}, ${band[0]:g}-${band[1]:g}, edge {e:.0%}.** "
              "On the scored quarter:\n")
        print("| sizing | half | bets | winners | A/E | flat ROI | bank x | worst drawdown | longest losing run |")
        print("|---|---|---|---|---|---|---|---|---|")
        for sizing, sname in ((0, "flat 1% of bank"), (0.10, "0.1 Kelly"), (0.25, "0.25 Kelly")):
            for hn, hm in (("1st", h), ("2nd", ~h)):
                sub = te[hm]
                m, o = selections(sub, pt_c[hm], sub[col].values, comm, e, band, one)
                r = result(sub, m, o, pt_c[hm], sizing, sub[col].values)
                if not r["n"]:
                    print(f"| {sname} | {hn} | 0 | | | | | | |")
                    continue
                print(f"| {sname} | {hn} | {r['n']:,} | {r['w']:,} | {r['ae']:.3f} | {r['roi']:+.1%} | "
                      f"{r['bank']:.2f} | {r['dd']:.0%} | {r['run']} |")
        m, o = selections(te, pt_c, te[col].values, comm, e, band, one)
        t = te[m].assign(ret=np.where(te.won.values[m] == 1, o[m] - 1, -1))
        bym = t.groupby(t.date.dt.to_period("M")).ret.agg(["size", "mean"])
        print("\nBy month (flat): " + "; ".join(f"{p}: {int(r['size'])} bets {r['mean']:+.0%}" for p, r in bym.iterrows()))
        print(f"Months in profit: {(bym['mean'] > 0).sum()} of {len(bym)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 4")
