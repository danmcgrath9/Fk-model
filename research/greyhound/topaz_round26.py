"""Round 26: the rule search at BSP, re-chosen every month (6 Nov 2026; Test 40's next step, after the founder's "Surely
we could find rules with our markets to beat bsp").

    python research/greyhound/topaz_round26.py DIR LABEL    (BETFAIR_DIR, RACES_DIR, ISOLYNX_DIR optional; WALK_GRV_RATING
                                                             / WALK_RELIABLE / WALK_LEAD as the weekly train sets them;
                                                             BSP_COMM to change the 8% commission)

Test 40 chose its rules once, on the early-stopping months, and scored them on the quarter after. Five held in both
halves, a little more than luck. Here the choice is made fresh every month, so a rule only counts if the search keeps
finding it:
  - one model, fitted before the early-stopping months and never refitted, prices the early-stopping months and the
    scored quarter (every price out of sample)
  - for each month of the scored quarter, the rules (Test 40's segments x BSP bands x back/lay x 1.1, 1.3, 1.6) are
    chosen on the six months before it: at least MIN_BETS bets and a profit there
  - two ways to bet the month: EVERY chosen rule (a runner backed or laid once, however many rules pick it), and the
    BEST rule alone (the highest ROI in the six months)
Flat 1-unit stakes at BSP, commission on winnings. Reported month by month and as a whole (both halves, A/E against
BSP, months in profit), and how many months each of Test 40's two paper rules was chosen.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round3 as R3         # noqa: E402
import topaz_round18 as R18       # noqa: E402
import topaz_round24 as R24       # noqa: E402
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402

COMM = R24.COMM
MIN_BETS = R24.MIN_BETS
WINDOW_MONTHS = 6
PAPER = (("back", "boxes 1-2", 8, 15, 1.6), ("back", "backing up within 4 days", 15, 30, 1.6))


def choose(w: pd.DataFrame, comm=COMM, min_bets=MIN_BETS):
    """Every rule with min_bets+ bets and a profit on the window w, best first: (side, segment, lo, hi, r, bets, roi)."""
    seg = R24.segments(w)
    out = []
    for name, s in seg.items():
        for lo, hi in R24.BANDS:
            for side in ("back", "lay"):
                ret_all = R24.returns(side, w.won.values, w.bsp.values, comm)
                for r in R24.RATIOS:
                    m = R24.rule_mask(w, s, lo, hi, side, r)
                    if m.sum() < min_bets:
                        continue
                    roi = float(ret_all[m].mean())
                    if roi > 0:
                        out.append((side, name, lo, hi, r, int(m.sum()), roi))
    return sorted(out, key=lambda x: -x[6])


def bet(cur: pd.DataFrame, rules, comm=COMM) -> pd.DataFrame:
    """The month's bets for a list of rules: a runner once per side however many rules pick it, with its return."""
    if not rules:
        return cur.iloc[:0].assign(side="", ret=0.0)
    seg = R24.segments(cur)
    parts = []
    for side in ("back", "lay"):
        m = np.zeros(len(cur), bool)
        for sd, name, lo, hi, r, *_ in rules:
            if sd == side and name in seg:
                m |= R24.rule_mask(cur, seg[name], lo, hi, side, r)
        if m.any():
            parts.append(cur[m].assign(side=side, ret=R24.returns(side, cur.won.values[m], cur.bsp.values[m], comm)))
    return pd.concat(parts) if parts else cur.iloc[:0].assign(side="", ret=0.0)


def summary(name: str, b: pd.DataFrame) -> str:
    if b.empty:
        return f"| {name} | all | 0 | | | | | |"
    mid = b.date.quantile(0.5)
    rows = []
    for hn, hm in (("1st", b.date < mid), ("2nd", b.date >= mid), ("all", b.date.notna())):
        x = b[hm]
        if x.empty:
            rows.append(f"| {name} | {hn} | 0 | | | | | |")
            continue
        backs = x[x.side == "back"]
        ae = backs.won.sum() / (1 / backs.bsp).sum() if len(backs) else np.nan
        bym = x.groupby(x.date.dt.to_period("M")).ret.sum()
        rows.append(f"| {name} | {hn} | {len(x):,} ({len(backs):,} backs) | {int(backs.won.sum()):,} | {ae:.3f} | "
                    f"{x.ret.mean():+.1%} | {x.ret.sum():+,.0f} | {(bym > 0).sum()} of {len(bym)} |")
    return "\n".join(rows)


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    df, num, rel, note = W.build_full(d)
    df, chk, _ = R18.check_features(df, os.environ.get("ISOLYNX_DIR", ""))
    cols = num + chk
    print(f"# {label}: round 26, the rule search at BSP re-chosen every month ({COMM:.0%} commission)\n\n{note}\n")
    q75 = df.date.quantile(0.75)
    es_start = q75 - min(pd.Timedelta(days=183), (q75 - df.date.min()) / 4)
    fp, rest = df[df.date < es_start].copy(), df[df.date >= es_start].copy()
    es = rest[rest.date < q75]
    recency = 0.5 ** (((es_start - fp.date).dt.days / 365.25).values / 3.0)
    Xf, Xe, Xr = T.features(fp, cols, rel), T.features(es, cols, rel), T.features(rest, cols, rel)
    bst, k, _ = R3.fit_weighted(Xf, fp.p_mkt.values.astype(float), fp.race_id, Xe, es.won.values, es.race_id.values,
                                recency, rounds=6000)
    rest["p_x"] = V1.race_softmax(bst.predict(Xr, num_iteration=k, raw_score=True), rest.race_id.values)
    t = rest[rest.bsp.notna() & (rest.bsp > 1)].copy()
    months = pd.period_range(q75.to_period("M"), t.date.max().to_period("M"), freq="M")
    print(f"{k} rounds, {len(cols)} inputs, fitted on races before {es_start:%Y-%m-%d} and never refitted. Each month's "
          f"rules chosen on the {WINDOW_MONTHS} months before it ({MIN_BETS}+ bets and a profit there).\n")
    print("| month | rules chosen | best rule (bets, ROI on the 6 months) | every rule: bets, ROI | best rule: bets, ROI | "
          "cumulative units, every / best |\n|---|---|---|---|---|---|")
    every, best, paper_months, cum_e, cum_b = [], [], {p: 0 for p in PAPER}, 0.0, 0.0
    for M in months:
        w = t[(t.date >= (M - WINDOW_MONTHS).start_time) & (t.date < M.start_time)]
        cur = t[(t.date >= M.start_time) & (t.date < (M + 1).start_time)]
        if cur.empty:
            continue
        rules = choose(w)
        for p in PAPER:
            paper_months[p] += any((r[0], r[1], r[2], r[3], r[4]) == p for r in rules)
        be, bb = bet(cur, rules), bet(cur, rules[:1])
        every.append(be)
        best.append(bb)
        cum_e += be.ret.sum()
        cum_b += bb.ret.sum()
        top = (f"{rules[0][0]} {rules[0][1]}, ${rules[0][2]:g}-${rules[0][3]:g}, {rules[0][4]:g}x "
               f"({rules[0][5]:,}, {rules[0][6]:+.0%})") if rules else "none"
        print(f"| {M} | {len(rules)} | {top} | {len(be):,}, {(be.ret.mean() if len(be) else np.nan):+.1%} | "
              f"{len(bb):,}, {(bb.ret.mean() if len(bb) else np.nan):+.1%} | {cum_e:+,.0f} / {cum_b:+,.0f} |")
    print("\n| bets | half | bets | back winners | A/E vs BSP (backs) | flat ROI | units | months in profit |\n"
          "|---|---|---|---|---|---|---|---|")
    print(summary("every chosen rule", pd.concat(every)))
    print(summary("the best rule alone", pd.concat(best)))
    n = len([M for M in months if not t[(t.date >= M.start_time) & (t.date < (M + 1).start_time)].empty])
    print("\nTest 40's paper rules, months chosen: " + "; ".join(
        f"{s} {name} ${lo:g}-${hi:g} at {r:g}x: {c} of {n}" for (s, name, lo, hi, r), c in paper_months.items()))
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 26")
