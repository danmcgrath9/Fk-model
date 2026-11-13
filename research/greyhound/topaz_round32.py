"""Round 32: can TAB's first price be had? (13 Nov 2026, on Test 49: the 1.3x rule at TAB's first price made +44.7%
flat on 1,051 bets, 28 of 30 months in profit.)

    python research/greyhound/topaz_round32.py DIR LABEL    (BETWATCH_DIR, BETFAIR_DIR, RACES_DIR; the weekly train's
                                                             WALK_* settings)

Round 30's model and rule (the production model on the standard split, scored on the last quarter; the 1.3x rule on the
blend of ours with that price's own book, our blended price $2-$15, Kelly x75 cap 4, no commission), and three checks:
  1. HOW LONG THE FIRST PRICE STOOD for the rule's bets: minutes from TAB's first recorded price to its next change
     (to the jump when it never changed), and how often the next change was shorter
  2. THE RULE LATER IN THE MORNING: at the price standing 5, 30, 60 and 120 minutes after the race's market opened
     (TAB's earliest first price in the race), each with its own book and blend; a race already run by then is out
  3. SCRATCHINGS AFTER THE BET: the rule split by races with no runner scratched after the bet and races with one or
     more, and with an APPROXIMATE fixed-odds deduction taken off the winnings: the scratched runners' share of TAB's
     opening book (the bookmakers' deduction table is not in the data, and it is built from the same chance). Kelly
     stakes stay as struck, because the bettor cannot see the scratching coming. In a race with no scratching after the
     bet, the field the model priced is the field that was bet into. Beside it, a flat DEDUCT_CENTS (6 by default) in
     the dollar off every bet's winnings, as TAB takes a deduction ($21 at 6c pays $19.80), and the larger of the two;
     and TAB's own deduction as the founder's records show it (100c over the scratched dog's price, rounded down)
  4. BSP AGAINST THE PRICE TAKEN and against the price paid after that deduction, by races with and without a
     scratching after the open (a scratching shortens every dog left in, whoever is right about them)
"""
import gzip
import json
import os
import sys
from bisect import bisect_right
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import gbm_v0                     # noqa: E402
import topaz_round3 as R3         # noqa: E402
import topaz_round9 as R9         # noqa: E402
import topaz_round30 as R30       # noqa: E402
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402

RATIO, BAND = 1.3, (2, 15)
FLAT_CENTS = float(os.environ.get("DEDUCT_CENTS", "6") or 6)   # founder, 13 Nov 2026: "Did you apply 6c to every bet?"
MAX_CENTS = 75                    # the most a race's deductions take off the winnings


def table_cents(p: float) -> int:
    """A scratched runner's deduction in cents: 100 / its price at the scratching, rounded down. It matches five of the
    six TAB deductions in the founder's records (data/live_bets: $12 8c, $14 7c, $16 6c, $26 3c, $34 2c) and gives $17
    5c where the record says 6c (those records carry the card's price, not the price at the scratching)."""
    return int(100 // p) if p and p > 1 else 0
LATER = (5, 30, 60, 120)         # minutes after the market opened


def ts(s) -> float:
    """Epoch seconds from an ISO time (Z or an offset); NaN when missing or unreadable."""
    if not s:
        return np.nan
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()
    except ValueError:
        t = pd.to_datetime(s, utc=True, errors="coerce")
        return np.nan if pd.isna(t) else t.timestamp()


def price_at(flucs: list, t: float) -> float:
    """The price standing at time t: the last change at or before t; NaN before the first."""
    i = bisect_right([f[1] for f in flucs], t)
    return flucs[i - 1][0] if i else np.nan


def race_rows(r: dict) -> list:
    """One row per runner that ran: TAB's first price, how long it stood, the price at each LATER minute, and the
    race's scratchings after the open and after each later bet time with their share of TAB's opening book."""
    start = ts(r.get("start"))
    runners = []
    for ru in r.get("runners", []):
        fl = sorted(((float(p), ts(t)) for p, t in ((ru.get("books") or {}).get("Tab") or {}).get("flucs") or []
                     if p and float(p) > 1 and not np.isnan(ts(t))), key=lambda f: f[1])
        if not np.isnan(start):
            fl = [f for f in fl if f[1] <= start]
        runners.append((ru, fl))
    firsts = [fl[0][1] for _, fl in runners if fl]
    if not firsts:
        return []
    open_t = min(firsts)
    book = sum(1 / fl[0][0] for _, fl in runners if fl)
    scr = []
    for ru, fl in runners:
        st = ts(ru.get("scratched"))
        if ru.get("scratched") and not np.isnan(st):
            p = price_at(fl, st) if fl else np.nan
            p = fl[0][0] if fl and np.isnan(p) else p
            priced = bool(p) and not np.isnan(p)
            scr.append((st, (1 / p) / book if priced else 0.0, priced, table_cents(p) if priced else 0))
    last_t = max((fl[-1][1] for ru, fl in runners if fl and not ru.get("scratched")), default=open_t)
    bet_times = {"open": open_t, **{f"{k}m": open_t + 60 * k for k in LATER}, "last": last_t}
    race = {}
    for name, bt in bet_times.items():
        after = [(q, pr, c) for s, q, pr, c in scr if s > bt]
        race[f"scr_after_{name}"] = len(after)
        race[f"scr_priced_{name}"] = sum(pr for _, pr, _ in after)
        race[f"ded_{name}"] = float(sum(q for q, _, _ in after))
        race[f"dedt_{name}"] = min(MAX_CENTS, sum(c for _, _, c in after)) / 100
    rows = []
    for ru, fl in runners:
        if ru.get("scratched"):
            continue
        row = {"date": r.get("date"), "dog_raw": ru.get("name"), **race}
        if fl:
            row["tab_first"], row["first_t"] = fl[0][0], fl[0][1]
            nxt = next((f for f in fl[1:] if f[0] != fl[0][0]), None)
            row["stood_min"] = ((nxt[1] if nxt else start) - fl[0][1]) / 60
            row["next_shorter"] = float(nxt[0] < fl[0][0]) if nxt else np.nan
        for k in LATER:
            bt = open_t + 60 * k
            row[f"tab_{k}m"] = price_at(fl, bt) if fl and (np.isnan(start) or bt < start) else np.nan
        rows.append(row)
    return rows


def load(d: str) -> pd.DataFrame:
    rows = []
    for f in sorted(Path(d).glob("betwatch_VIC_G_*.json.gz")):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for r in json.load(fh).get("races", []):
                rows.extend(race_rows(r))
    bw = pd.DataFrame(rows)
    if bw.empty:
        return bw
    bw["date"] = pd.to_datetime(bw.date, errors="coerce")
    bw["_dn"] = gbm_v0.norm_name(bw.dog_raw)
    return bw.drop(columns="dog_raw").drop_duplicates(["date", "_dn"], keep=False)


def rule(es, te, price_col):
    """Round 30's rule at one price: (bets frame, mask, odds, units, price, blend weights), or None if too few."""
    mkt = f"p_{price_col}"
    for t in (es, te):
        t[mkt] = R30.book_chance(t, price_col)
    e_ok, t_ok = es[mkt].notna().values, (te[mkt].notna() & te[price_col].gt(1)).values
    if e_ok.sum() < 1000 or t_ok.sum() < 1000:
        return None
    wb, _ = V1.blend(["p_x", mkt], es[e_ok])
    t2 = te[t_ok].copy()
    pb = V1.blend(["p_x", mkt], t2, wb)[1]
    price = t2[price_col].astype(float).values
    m, o, u = R9.horse_bets(t2, pb, t2[mkt].values, price, 0.0, RATIO, BAND)
    return t2, m, o, u, price, wb


def line(name, t2, mm, o, u, price, h_cut):
    h = (t2.date < h_cut).values
    for hn, hm in (("1st", h), ("2nd", ~h), ("all", np.ones(len(t2), bool))):
        r = R9.summary(t2, mm & hm, o, u, price)
        if not r["n"]:
            print(f"| {name} | {hn} | 0 | | | | | | | |")
            continue
        x = mm & hm
        bym = pd.Series(np.where(t2.won.values[x] == 1, o[x] - 1, -1) * u[x]).groupby(
            pd.to_datetime(t2.date.values[x]).to_period("M")).sum()
        print(f"| {name} | {hn} | {r['n']:,} | {r['w']:,} | {r['ae']:.3f} | {r['flat']:+.1%} | {r['staked']:,.0f} | "
              f"{r['kroi']:+.1%} | {r['kunits']:+,.0f} | {(bym > 0).sum()} of {len(bym)} |")


HEAD = ("| bets | half | bets | winners | A/E vs the price | flat ROI | units staked | Kelly ROI | units won | months in "
        "profit |\n|---|---|---|---|---|---|---|---|---|---|")


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 32, can TAB's first price be had?\n")
    bw = load(bdir) if bdir and os.path.isdir(bdir) else pd.DataFrame()
    if bw.empty:
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    df, num, rel, note = W.build_full(d)
    df = df.assign(_dn=gbm_v0.norm_name(df.dog_name)).merge(bw, on=["date", "_dn"], how="left").drop(columns="_dn")
    q75 = df.date.quantile(0.75)
    es_start = q75 - min(pd.Timedelta(days=183), (q75 - df.date.min()) / 4)
    pre, te = df[df.date < q75], df[df.date >= q75].copy()
    fp, es = pre[pre.date < es_start].copy(), pre[pre.date >= es_start].copy()
    recency = 0.5 ** (((es_start - fp.date).dt.days / 365.25).values / 3.0) * W.label_weight(fp)
    Xf, Xe, Xt = T.features(fp, num, rel), T.features(es, num, rel), T.features(te, num, rel)
    bst, k, _ = R3.fit_weighted(Xf, fp.p_mkt.values.astype(float), fp.race_id, Xe, es.won.values, es.race_id.values,
                                recency, rounds=6000)
    es["p_x"] = V1.race_softmax(bst.predict(Xe, num_iteration=k, raw_score=True), es.race_id.values)
    te["p_x"] = V1.race_softmax(bst.predict(Xt, num_iteration=k, raw_score=True), te.race_id.values)
    h_cut = te.date.quantile(0.5)
    print(f"{note}\n\n{k} rounds, {len(num)} inputs. Betwatch: {len(bw):,} runners. Scored {te.date.min():%Y-%m-%d} to "
          f"{te.date.max():%Y-%m-%d}, halves split at {h_cut:%Y-%m-%d}.\n")
    races = te.drop_duplicates("race_id")
    print(f"Scratchings: {races.scr_after_open.gt(0).mean():.1%} of scored races had a runner scratched after TAB's "
          f"market opened (median deduction where one did: {races.ded_open[races.scr_after_open > 0].median():.1%} of "
          f"the winnings; {races.scr_priced_open.sum() / max(races.scr_after_open.sum(), 1):.0%} of those scratched "
          f"runners had a TAB price to deduct by).\n")

    first = rule(es, te, "tab_first")
    if first is None:
        print("Too few runners with TAB's first price")
        return 1
    t2, m, o, u, price, wb = first
    x = t2[m]
    print(f"## 1. How long the first price stood, for the rule's {m.sum():,} bets at TAB's first price (blend {wb[0]:.2f}"
          f" / {wb[1]:.2f})\n\n| minutes to TAB's next change (to the jump if none) | under 1 | under 5 | under 30 | "
          f"under 60 | median | next change shorter |\n|---|---|---|---|---|---|---|")
    s = x.stood_min
    print(f"| share of bets | {s.lt(1).mean():.1%} | {s.lt(5).mean():.1%} | {s.lt(30).mean():.1%} | {s.lt(60).mean():.1%} | "
          f"{s.median():.0f} min | {x.next_shorter.mean():.1%} |\n")

    print(f"## 2. The rule later in the morning\n\n{HEAD}")
    line("TAB's first price", t2, m, o, u, price, h_cut)
    for kmin in LATER:
        got = rule(es, te, f"tab_{kmin}m")
        if got is None:
            print(f"| {kmin} minutes after the open | too few | | | | | | | | |")
            continue
        a, b, c, e, f, w = got
        line(f"{kmin} minutes after the open ({w[0]:.2f} / {w[1]:.2f})", a, b, c, e, f, h_cut)

    print(f"\n## 3. Scratchings after the bet, at TAB's first price\n\n{HEAD}")
    clean = (t2.scr_after_open.fillna(0) == 0).values
    line("races with no runner scratched after the open", t2, m & clean, o, u, price, h_cut)
    line("races with one or more scratched after the open", t2, m & ~clean, o, u, price, h_cut)
    o_ded = 1 + (o - 1) * (1 - t2.ded_open.fillna(0).values)
    line("every race, approximate deduction off the winnings", t2, m, o_ded, u, price, h_cut)
    o_flat = 1 + (o - 1) * (1 - FLAT_CENTS / 100)
    line(f"every bet, {FLAT_CENTS:g}c in the dollar off the winnings", t2, m, o_flat, u, price, h_cut)
    o_both = 1 + (o - 1) * (1 - np.maximum(FLAT_CENTS / 100, t2.ded_open.fillna(0).values))
    line(f"every bet, the larger of {FLAT_CENTS:g}c and the race's own deduction", t2, m, o_both, u, price, h_cut)
    o_tab = 1 + (o - 1) * (1 - t2.dedt_open.fillna(0).values)
    line("every race, TAB's deduction (100c / the scratched dog's price, rounded down; 75c at most)", t2, m, o_tab, u,
         price, h_cut)

    print("\n## 4. Did BSP come in under the price taken? For the rule's bets at TAB's first price\n\n"
          "| races | half | bets with a BSP | BSP under the price taken | BSP under the price paid after TAB's deduction | "
          "mean log(price taken / BSP) | mean log(price paid / BSP) | A/E vs BSP |\n|---|---|---|---|---|---|---|---|")
    paid = 1 + (price - 1) * (1 - t2.dedt_open.fillna(0).values)
    hb = (t2.date < h_cut).values
    has = (t2.bsp > 1).values if "bsp" in t2 else np.zeros(len(t2), bool)
    for rn, rm in (("every race", np.ones(len(t2), bool)), ("no scratching after the open", clean),
                   ("a scratching after the open", ~clean)):
        for hn, hm in (("1st", hb), ("2nd", ~hb), ("all", np.ones(len(t2), bool))):
            x = m & rm & hm & has
            if not x.any():
                continue
            b = t2.bsp.values[x]
            print(f"| {rn} | {hn} | {x.sum():,} | {(b < price[x]).sum():,} ({(b < price[x]).mean():.1%}) | "
                  f"{(b < paid[x]).sum():,} ({(b < paid[x]).mean():.1%}) | {np.log(price[x] / b).mean():+.3f} | "
                  f"{np.log(paid[x] / b).mean():+.3f} | {t2.won.values[x].sum() / (1 / b).sum():.3f} |")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 32")
