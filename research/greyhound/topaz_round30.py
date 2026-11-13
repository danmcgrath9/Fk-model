"""Round 30: the rule at TAB's own prices, from Betwatch (13 Nov 2026, founder: "we will win long term on opening ... Just
have to get that data and then get a strategy").

    python research/greyhound/topaz_round30.py DIR LABEL    (BETWATCH_DIR, BETFAIR_DIR, RACES_DIR; WALK_GRV_RATING /
                                                             WALK_RELIABLE / WALK_LEAD / WALK_DRIFT / WALK_SP_WEIGHT /
                                                             WALK_TRACK as the weekly train sets them)

Betwatch's month files (greyhound/betwatch.py) give, per runner, TAB's price changes with timestamps from Nov 2022.
Joined to the runs by date and dog name:
  tab_first   TAB's first recorded price that day (Betwatch: "usually close to the open but can miss sharp early
              moves", so close to the open, not always the open)
  tab_last    TAB's last recorded price before the jump
The production model (the weekly train's inputs and label weight) on the standard split, scored on the last quarter,
both halves. For each price, GRV's SP as before beside TAB's first and last:
  1. coverage: runners and races with each price
  2. the 1.3x rule at that price (blend of ours and that price's own book, fitted on the early-stopping months; our
     blended price $2-$15; Kelly x75 on halfway between the blend and that price's chance, cap 4; no commission), with
     the drift guard beside it
  3. closing-line value of the bets at TAB's first price: how often BSP came in shorter than the price we took, the
     mean log of (price taken / BSP), and A/E against BSP
"""
import gzip
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import gbm_v0                     # noqa: E402
import topaz_round3 as R3         # noqa: E402
import topaz_round9 as R9         # noqa: E402
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402

RATIO, BAND = 1.3, (2, 15)


def load_betwatch(d: str) -> pd.DataFrame:
    """One row per runner: date, normalised name, TAB's first and last prices (and when), Sportsbet's and Ladbrokes'
    first prices."""
    rows = []
    for f in sorted(Path(d).glob("betwatch_VIC_G_*.json.gz")):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for r in json.load(fh).get("races", []):
                start = pd.to_datetime(r.get("start"), utc=True, errors="coerce")
                for ru in r.get("runners", []):
                    if ru.get("scratched"):
                        continue
                    b = ru.get("books") or {}
                    tab = [f for f in (b.get("Tab") or {}).get("flucs") or []
                           if pd.isna(start) or pd.to_datetime(f[1], utc=True, errors="coerce") <= start]
                    row = {"date": r.get("date"), "dog_raw": ru.get("name"),
                           "tab_first": tab[0][0] if tab else np.nan, "tab_first_t": tab[0][1] if tab else None,
                           "tab_last": tab[-1][0] if tab else np.nan, "tab_n": len(tab),
                           "bw_start": r.get("start")}
                    for bk in ("Sportsbet", "Ladbrokes"):
                        fl = (b.get(bk) or {}).get("flucs") or []
                        row[f"{bk.lower()}_first"] = fl[0][0] if fl else np.nan
                    rows.append(row)
    bw = pd.DataFrame(rows)
    if bw.empty:
        return bw
    bw["date"] = pd.to_datetime(bw.date, errors="coerce")
    bw["_dn"] = gbm_v0.norm_name(bw.dog_raw)
    return bw.drop(columns="dog_raw").drop_duplicates(["date", "_dn"], keep=False)


def join_betwatch(df: pd.DataFrame, bw: pd.DataFrame) -> pd.DataFrame:
    df = df.assign(_dn=gbm_v0.norm_name(df.dog_name))
    return df.merge(bw, on=["date", "_dn"], how="left").drop(columns="_dn")


def book_chance(t: pd.DataFrame, col: str) -> pd.Series:
    """Each price's own chances, normalised to 100% a race, on races where every runner has that price."""
    inv = (1 / t[col]).where(t[col] > 1)
    full = inv.notna().groupby(t.race_id).transform("all")
    return (inv / inv.groupby(t.race_id).transform("sum")).where(full)


def clv(t: pd.DataFrame, m: np.ndarray, price_col: str) -> dict:
    x = t[m & t.bsp.notna().values & (t.bsp > 1).values]
    if x.empty:
        return dict(n=0)
    lr = np.log(x[price_col].values / x.bsp.values)
    return dict(n=len(x), shorter=float((x.bsp.values < x[price_col].values).mean()), mean_log=float(lr.mean()),
                ae_bsp=float(x.won.sum() / (1 / x.bsp).sum()))


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    df, num, rel, note = W.build_full(d)
    bdir = os.environ.get("BETWATCH_DIR", "")
    bw = load_betwatch(bdir) if bdir and os.path.isdir(bdir) else pd.DataFrame()
    print(f"# {label}: round 30, the rule at TAB's own prices (Betwatch)\n\n{note}\n")
    if bw.empty:
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    df = join_betwatch(df, bw)
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
    for t in (es, te):
        t["p_tab_first"] = book_chance(t, "tab_first")
        t["p_tab_last"] = book_chance(t, "tab_last")
    print(f"{k} rounds, {len(num)} inputs. Betwatch: {len(bw):,} runners from {bw.date.min():%Y-%m-%d} to "
          f"{bw.date.max():%Y-%m-%d}.\n")
    print("| scored quarter | runners | races | TAB's first price on | races with it on every runner | TAB's first price "
          "came this many hours before the jump (median) | its book (median) | GRV's SP book (median) |\n"
          "|---|---|---|---|---|---|---|---|")
    hrs = (pd.to_datetime(te.bw_start, utc=True, errors="coerce") - pd.to_datetime(te.tab_first_t, utc=True, errors="coerce"))
    hrs = hrs.dt.total_seconds() / 3600
    full_tab = te.tab_first.gt(1).groupby(te.race_id).all()
    bk_tab = (1 / te.tab_first).groupby(te.race_id).sum()[full_tab]
    bk_sp = (1 / te.start_price.where(te.start_price > 1)).groupby(te.race_id).sum()
    print(f"| {te.date.min():%Y-%m-%d} to {te.date.max():%Y-%m-%d} | {len(te):,} | {te.race_id.nunique():,} | "
          f"{te.tab_first.notna().mean():.1%} | {te[te.p_tab_first.notna()].race_id.nunique():,} | "
          f"{hrs.median():.1f} | {bk_tab.median():.0%} | {bk_sp.median():.0%} |\n")

    h_all = (te.date < te.date.quantile(0.5)).values
    print("| price | rule | half | bets | winners | A/E vs that price | flat ROI | units staked | Kelly ROI | units won | "
          "worst drawdown | months in profit |\n|---|---|---|---|---|---|---|---|---|---|---|---|")
    keep = {}
    for name, price_col, mkt_col in (("GRV's SP", "start_price", "p_sp"), ("TAB's first price", "tab_first", "p_tab_first"),
                                     ("TAB's last price before the jump", "tab_last", "p_tab_last")):
        e_ok = es[mkt_col].notna().values & es.p_sp.notna().values
        t_ok = (te[mkt_col].notna() & te[price_col].gt(1)).values
        if e_ok.sum() < 1000 or t_ok.sum() < 1000:
            print(f"| {name} | too few runners with this price ({e_ok.sum():,} / {t_ok.sum():,}) | | | | | | | | | | |")
            continue
        bw_, _ = V1.blend(["p_x", mkt_col], es[e_ok])
        t2 = te[t_ok].copy()
        pb = V1.blend(["p_x", mkt_col], t2, bw_)[1]
        price = t2[price_col].astype(float).values
        m, o, u = R9.horse_bets(t2, pb, t2[mkt_col].values, price, 0.0, RATIO, BAND)
        keep[name] = (t2, m, price_col)
        h2 = (t2.date < te.date.quantile(0.5)).values
        guards = [("no guard", np.ones(len(t2), bool))]
        if "drift" in t2:
            guards.append(("drift guard 1.3x", ~(t2.drift >= 1.3).values))
        for gname, g in guards:
            for hn, hm in (("1st", h2), ("2nd", ~h2), ("all", np.ones(len(t2), bool))):
                r = R9.summary(t2, m & g & hm, o, u, price)
                if not r["n"]:
                    print(f"| {name} ({bw_[0]:.2f} / {bw_[1]:.2f}) | {gname} | {hn} | 0 | | | | | | | | |")
                    continue
                mm = m & g & hm
                bym = pd.Series(np.where(t2.won.values[mm] == 1, o[mm] - 1, -1) * u[mm],
                                index=t2.date.values[mm]).groupby(pd.to_datetime(t2.date.values[mm]).to_period("M")).sum()
                print(f"| {name} ({bw_[0]:.2f} / {bw_[1]:.2f}) | {gname} | {hn} | {r['n']:,} | {r['w']:,} | {r['ae']:.3f} | "
                      f"{r['flat']:+.1%} | {r['staked']:,.0f} | {r['kroi']:+.1%} | {r['kunits']:+,.0f} | {r['dd']:,.0f} | "
                      f"{(bym > 0).sum()} of {len(bym)} |")

    print("\n| bets at | half | bets with a BSP | BSP shorter than the price taken | mean log(price taken / BSP) | "
          "A/E vs BSP |\n|---|---|---|---|---|---|")
    for name, (t2, m, price_col) in keep.items():
        h2 = (t2.date < te.date.quantile(0.5)).values
        for hn, hm in (("1st", h2), ("2nd", ~h2), ("all", np.ones(len(t2), bool))):
            c = clv(t2, m & hm, price_col)
            if c["n"]:
                print(f"| {name} | {hn} | {c['n']:,} | {c['shorter']:.1%} | {c['mean_log']:+.3f} | {c['ae_bsp']:.3f} |")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 30")
