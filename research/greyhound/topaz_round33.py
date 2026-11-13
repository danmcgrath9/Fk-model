"""Round 33: the rule on the field as it stood when the bet was struck (13 Nov 2026, founder: "Well keep testing and get
better", after Test 50 found the 1.3x rule's value at TAB's first price sat mostly in races with a scratching after it).

    python research/greyhound/topaz_round33.py DIR LABEL    (BETWATCH_DIR, BETFAIR_DIR, RACES_DIR; the weekly train's
                                                             WALK_* settings)

The model prices the field that ran. A bettor at TAB's open bets into the field that was in the market then, dogs
later scratched included, and is paid after TAB's deduction for them. Here, for each bet time (TAB's first price, and
the price standing 30 and 60 minutes after the market opened):
  the field  every runner in TAB's market at that time and not yet scratched, from Betwatch
  TAB's chance  its price at that time over the field's book
  ours  each runner that ran keeps its share of what the dogs scratched later did not take: ours x (1 - their chance in
        TAB's book), and each dog scratched later is put back at TAB's chance for it (we have no price of our own
        for a dog that did not run, so this assumes we would have rated it as TAB did)
  the blend  ours with TAB's chance, fitted on the early-stopping months' races with no scratching after the bet time
             (there the field at the bet is the field that ran), applied over the whole field at the bet
  paid  1 + (price - 1) x (1 - TAB's deduction), the deduction round 32's table (100c over each dog scratched after
        the bet at its price then, rounded down, 75c at most); Kelly stakes as struck
Three versions side by side, on the production model, standard split, last quarter, both halves:
  A. Test 49 as it was: the field that ran, nothing deducted
  B. the field that ran, paid after the deduction (round 32's honest-payout row)
  C. the field at the bet, paid after the deduction: what a bettor at that time would have had
Then C by ratio (1.1-1.5), by races with and without a later scratching, and BSP against the price paid.
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
import topaz_round32 as R32       # noqa: E402
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402

BAND = (2, 15)
TIMES = (0, 30, 60)               # minutes after the market opened; 0 = each runner's first TAB price
RATIOS = (1.1, 1.2, 1.3, 1.5)


def field_rows(r: dict, times=TIMES) -> list:
    """One row per runner in TAB's market at each bet time and not yet scratched: its price then, its chance in TAB's
    book over that field, whether it ran, and the race's share of the book scratched later and TAB's deduction."""
    start = R32.ts(r.get("start"))
    runners = []
    for ru in r.get("runners", []):
        fl = sorted(((float(p), R32.ts(t)) for p, t in ((ru.get("books") or {}).get("Tab") or {}).get("flucs") or []
                     if p and float(p) > 1 and not np.isnan(R32.ts(t))), key=lambda f: f[1])
        if not np.isnan(start):
            fl = [f for f in fl if f[1] <= start]
        st = R32.ts(ru.get("scratched")) if ru.get("scratched") else np.inf
        runners.append((ru, fl, np.inf if np.isnan(st) else st))
    firsts = [fl[0][1] for _, fl, _ in runners if fl]
    if not firsts:
        return []
    open_t = min(firsts)
    rows = []
    for k in times:
        bt = open_t + 60 * k
        if not np.isnan(start) and bt >= start:
            continue
        field = []
        for ru, fl, st in runners:
            if st <= bt or not fl:
                continue
            p = fl[0][0] if k == 0 else R32.price_at(fl, bt)
            if np.isnan(p):
                continue
            field.append((ru, fl, st, p))
        if not field:
            continue
        book = sum(1 / p for *_, p in field)
        later = [(fl, st, p) for _, fl, st, p in field if np.isfinite(st)]
        s = sum((1 / p) / book for _, _, p in later)
        cents = 0
        for fl, st, p in later:
            ps = R32.price_at(fl, st)
            cents += R32.table_cents(p if np.isnan(ps) else ps)
        ded = min(R32.MAX_CENTS, cents) / 100
        for ru, fl, st, p in field:
            rows.append({"bw_race": r.get("id"), "date": r.get("date"), "dog_raw": ru.get("name"), "k": k,
                         "price": p, "p_book": (1 / p) / book, "ran": not np.isfinite(st), "s_later": s,
                         "n_later": len(later), "ded": ded})
    return rows


def load(d: str) -> pd.DataFrame:
    rows = []
    for f in sorted(Path(d).glob("betwatch_VIC_G_*.json.gz")):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for r in json.load(fh).get("races", []):
                rows.extend(field_rows(r))
    fr = pd.DataFrame(rows)
    if fr.empty:
        return fr
    fr["date"] = pd.to_datetime(fr.date, errors="coerce")
    fr["_dn"] = gbm_v0.norm_name(fr.dog_raw)
    return fr.drop(columns="dog_raw")


def at_time(t: pd.DataFrame, fr: pd.DataFrame, k: int) -> pd.DataFrame:
    """The bet-time field for the races in t (runners that ran, from t, with ours; dogs scratched later, from fr, at
    TAB's chance), keeping only races where every runner that ran is in TAB's field then."""
    f = fr[fr.k == k]
    ran = f[f.ran].drop_duplicates(["date", "_dn"], keep=False)
    x = t.assign(_dn=gbm_v0.norm_name(t.dog_name)).merge(
        ran[["date", "_dn", "bw_race", "price", "p_book", "s_later", "n_later", "ded"]], on=["date", "_dn"], how="inner")
    n_x, n_t = x.groupby("race_id").size(), t.groupby("race_id").size()
    whole = n_x.index[(n_x == n_t.reindex(n_x.index)).values]
    one = x.groupby("race_id").bw_race.nunique()
    x = x[x.race_id.isin(whole.intersection(one.index[(one == 1).values]))].copy()
    x["p_x_bet"] = x.p_x * (1 - x.s_later)
    x["is_ran"] = True
    rid = x.drop_duplicates("bw_race").set_index("bw_race").race_id
    later = f[~f.ran & f.bw_race.isin(rid.index)].copy()
    later["race_id"], later["p_x_bet"], later["won"], later["is_ran"] = later.bw_race.map(rid), later.p_book, 0, False
    later["date"] = later.bw_race.map(x.drop_duplicates("bw_race").set_index("bw_race").date)
    return pd.concat([x, later[["race_id", "bw_race", "date", "price", "p_book", "p_x_bet", "won", "is_ran", "s_later",
                                "n_later", "ded"]]], ignore_index=True)


def blend_at(es_f: pd.DataFrame, te_f: pd.DataFrame):
    """Weights fitted on the early-stopping months' races with nothing scratched after the bet; the scored field's
    blended chances (over the whole field at the bet, dogs scratched later included)."""
    clean = es_f[es_f.n_later == 0]
    wb, _ = V1.blend(["p_x_bet", "p_book"], clean)
    return wb, V1.blend(["p_x_bet", "p_book"], te_f, wb)[1]


def final_field(es, te, price):
    """Versions A and B: the field that ran, TAB's price at the bet time over that field's book."""
    es, te = es.copy(), te.copy()
    for t in (es, te):
        inv = 1 / t[price]
        t["p_ff"] = inv / inv.groupby(t.race_id).transform("sum")
    wb, _ = V1.blend(["p_x", "p_ff"], es)
    return te, wb, V1.blend(["p_x", "p_ff"], te, wb)[1]


HEAD = ("| bet time | version | half | bets | winners | A/E vs the price | flat ROI | units staked | Kelly ROI | units won | "
        "months in profit |\n|---|---|---|---|---|---|---|---|---|---|---|")


def rows_out(when, name, t2, m, o, u, price, h_cut):
    h = (t2.date < h_cut).values
    for hn, hm in (("1st", h), ("2nd", ~h), ("all", np.ones(len(t2), bool))):
        r = R9.summary(t2, m & hm, o, u, price)
        if not r["n"]:
            print(f"| {when} | {name} | {hn} | 0 | | | | | | | |")
            continue
        x = m & hm
        bym = pd.Series(np.where(t2.won.values[x] == 1, o[x] - 1, -1) * u[x]).groupby(
            pd.to_datetime(t2.date.values[x]).to_period("M")).sum()
        print(f"| {when} | {name} | {hn} | {r['n']:,} | {r['w']:,} | {r['ae']:.3f} | {r['flat']:+.1%} | "
              f"{r['staked']:,.0f} | {r['kroi']:+.1%} | {r['kunits']:+,.0f} | {(bym > 0).sum()} of {len(bym)} |")


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 33, the rule on the field as it stood when the bet was struck\n")
    fr = load(bdir) if bdir and os.path.isdir(bdir) else pd.DataFrame()
    if fr.empty:
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    df, num, rel, note = W.build_full(d)
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
    print(f"{note}\n\n{k} rounds, {len(num)} inputs. Scored {te.date.min():%Y-%m-%d} to {te.date.max():%Y-%m-%d}, "
          f"halves split at {h_cut:%Y-%m-%d}. Betwatch field rows: {len(fr):,}.\n")
    keep = ["race_id", "date", "dog_name", "won", "p_x"] + (["bsp"] if "bsp" in te else [])
    print(HEAD)
    clv = {}
    for kmin in TIMES:
        when = "TAB's first price" if kmin == 0 else f"{kmin} minutes after the open"
        ef, tf = at_time(es[keep], fr, kmin), at_time(te[keep], fr, kmin)
        if ef[ef.is_ran].race_id.nunique() < 500 or tf[tf.is_ran].race_id.nunique() < 500:
            print(f"| {when} | too few races | | | | | | | | | |")
            continue
        # A and B: the field that ran
        e_r, t_r = ef[ef.is_ran].copy(), tf[tf.is_ran].copy()
        t2, wff, pff = final_field(e_r, t_r, "price")
        price = t2.price.values.astype(float)
        m, o, u = R9.horse_bets(t2, pff, t2.p_ff.values, price, 0.0, 1.3, BAND)
        rows_out(when, f"A. the field that ran, nothing deducted ({wff[0]:.2f} / {wff[1]:.2f})", t2, m, o, u, price, h_cut)
        o_paid = 1 + (o - 1) * (1 - t2.ded.values)
        rows_out(when, "B. the field that ran, after TAB's deduction", t2, m, o_paid, u, price, h_cut)
        # C: the field at the bet
        wb, pb_all = blend_at(ef, tf)
        tf = tf.assign(pb=pb_all)
        t3 = tf[tf.is_ran].reset_index(drop=True)
        price3 = t3.price.values.astype(float)
        for ratio in (1.3,) + tuple(r for r in RATIOS if r != 1.3):
            m3, o3, u3 = R9.horse_bets(t3, t3.pb.values, t3.p_book.values, price3, 0.0, ratio, BAND)
            paid3 = 1 + (o3 - 1) * (1 - t3.ded.values)
            tag = f"C. the field at the bet, after TAB's deduction ({wb[0]:.2f} / {wb[1]:.2f})" if ratio == 1.3 else \
                f"C at {ratio:g}x"
            rows_out(when, tag, t3, m3, paid3, u3, price3, h_cut)
            if ratio == 1.3:
                clean = (t3.n_later == 0).values
                rows_out(when, "C, races with nothing scratched after the bet", t3, m3 & clean, paid3, u3, price3, h_cut)
                rows_out(when, "C, races with a scratching after the bet", t3, m3 & ~clean, paid3, u3, price3, h_cut)
                clv[when] = (t3, m3, price3, 1 + (price3 - 1) * (1 - t3.ded.values))

    print("\n## BSP against the price paid after TAB's deduction, version C at 1.3x\n\n| bet time | half | bets with a BSP | "
          "BSP under the price paid | mean log(price paid / BSP) | A/E vs BSP |\n|---|---|---|---|---|---|")
    for when, (t3, m3, price3, paid) in clv.items():
        if "bsp" not in t3:
            continue
        h = (t3.date < h_cut).values
        for hn, hm in (("1st", h), ("2nd", ~h), ("all", np.ones(len(t3), bool))):
            x = m3 & hm & (t3.bsp > 1).values
            if not x.any():
                continue
            b = t3.bsp.values[x]
            print(f"| {when} | {hn} | {x.sum():,} | {(b < paid[x]).sum():,} ({(b < paid[x]).mean():.1%}) | "
                  f"{np.log(paid[x] / b).mean():+.3f} | {t3.won.values[x].sum() / (1 / b).sum():.3f} |")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 33")
