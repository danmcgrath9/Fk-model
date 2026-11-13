"""Round 34: every rule on the field as it stood when the bet was struck, after TAB's deduction (13 Nov 2026, founder:
"Well keep testing and get better"; Test 51 found the 1.3x rule honest at TAB's open only on the field at the bet).

    python research/greyhound/topaz_round34.py DIR LABEL    (BETWATCH_DIR, BETFAIR_DIR, RACES_DIR; the weekly train's
                                                             WALK_* settings; WALK_REFIT_EVERY, 6 by default;
                                                             BENCH_PAIRS=yes for the pairs)

Ours is the production model refitted every WALK_REFIT_EVERY months from Betwatch's first month on every race before
(topaz_walk.walk, as round 31). Each race is then rebuilt as it stood at TAB's first price (topaz_round33.at_time):
  - the dogs scratched later go back in at TAB's chance for them;
  - ours for the dogs that ran is scaled to make room;
  - the blend with TAB's book is refitted each month on the six months before, on races with nothing scratched after
    the bet, and applied over the whole field at the bet.
"Our top pick" is the top of that whole field; when the top pick was scratched later, the bet is refunded and is not a
bet here. Every return is after TAB's deduction for the dogs scratched after the bet (round 32's table).

Two prices, both struck at the open: TAB's first price, and the best first price of TAB, Sportsbet and Ladbrokes
(valued against the same blend, with the same deduction).

Printed:
  1. log loss on races with nothing scratched after the open (there the field at the bet is the field that ran)
  2. the card's rule (the 1.3x rule, our blended price $2-$15, Kelly x75 cap 4) month by month over every walk-forward
     month, both halves, at both prices
  3. round 31's bench: every segment x price band x bet (every runner, our top pick, the price 1.0-2.0x ours), chosen
     on the first 60% of days and scored once on the rest in halves with the luck count, and re-chosen every month
"""
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import gbm_v0                     # noqa: E402
import topaz_round9 as R9         # noqa: E402
import topaz_round12 as R12       # noqa: E402
import topaz_round18 as R18       # noqa: E402
import topaz_round29 as R29       # noqa: E402
import topaz_round30 as R30       # noqa: E402
import topaz_round31 as R31       # noqa: E402
import topaz_round33 as R33       # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402

PRICES = {"TAB's first price": ("price", "pb"),
          "best first price of TAB, Sportsbet and Ladbrokes": ("best_first", "pb")}
DEDUCTION = {"price": "ded", "best_first": "ded"}
BLEND_MONTHS = 6


def monthly_blend_at(x: pd.DataFrame, months) -> pd.Series:
    """Our blended chance for every row of the field at the bet, the weights refitted each month on the BLEND_MONTHS
    before it, on races with nothing scratched after the bet (there the field at the bet is the field that ran)."""
    out = pd.Series(np.nan, index=x.index)
    for M in months:
        w = x[x.is_ran & (x.n_later == 0) & (x.date >= (M - BLEND_MONTHS).start_time) & (x.date < M.start_time)]
        cur = ((x.date >= M.start_time) & (x.date < (M + 1).start_time)).values
        if w.race_id.nunique() < 300 or not cur.any():
            continue
        wb, _ = V1.blend(["p_x_bet", "p_book"], w)
        out[cur] = V1.blend(["p_x_bet", "p_book"], x[cur], wb)[1]
    return out


def top_of_field(x: pd.DataFrame) -> np.ndarray:
    """True for the top blended chance in each race's whole field at the bet (a dog scratched later can be it)."""
    return x.pb.groupby(x.race_id).rank(ascending=False, method="first").values == 1


def card_rule(t: pd.DataFrame, h_cut) -> None:
    """The card's rule on the walk-forward field at the bet, after TAB's deduction, at both prices."""
    print("| price | half | bets | winners | A/E vs the price | flat ROI | units staked | Kelly ROI | units won | "
          "months in profit |\n|---|---|---|---|---|---|---|---|---|---|")
    for pname, (pcol, bcol) in PRICES.items():
        price = t[pcol].values.astype(float)
        m, o, u = R9.horse_bets(t, t[bcol].values, t.p_book.values, price, 0.0, 1.3, (2, 15))
        paid = 1 + (o - 1) * (1 - t.ded.fillna(0).values)
        h = (t.date < h_cut).values
        for hn, hm in (("1st", h), ("2nd", ~h), ("all", np.ones(len(t), bool))):
            r = R9.summary(t, m & hm, paid, u, price)
            if not r["n"]:
                print(f"| {pname} | {hn} | 0 | | | | | | | |")
                continue
            x = m & hm
            bym = pd.Series(np.where(t.won.values[x] == 1, paid[x] - 1, -1) * u[x]).groupby(
                pd.to_datetime(t.date.values[x]).to_period("M")).sum()
            print(f"| {pname} | {hn} | {r['n']:,} | {r['w']:,} | {r['ae']:.3f} | {r['flat']:+.1%} | {r['staked']:,.0f} | "
                  f"{r['kroi']:+.1%} | {r['kunits']:+,.0f} | {(bym > 0).sum()} of {len(bym)} |")


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 34, every rule on the field as it stood at the bet, after TAB's deduction\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    fr = R33.load(bdir, times=(0,))
    bw = R30.load_betwatch(bdir)
    if fr.empty or bw.empty:
        print("No Betwatch races: nothing to test")
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
          f"{len(num)} inputs.\n")
    df, log = W.walk(df, num, rel, first_pred, t0, every)
    print("Refits: " + "; ".join(f"{m}: {s}" for m, s in log if "priced by" not in s) + "\n")
    df = df[df.p_a.notna()].copy()
    df["p_x"] = df.p_a
    x = R33.at_time(df, fr, 0)
    sb = bw[["date", "_dn", "sportsbet_first", "ladbrokes_first"]]
    x = x.assign(_dn=gbm_v0.norm_name(x.dog_name.fillna(""))).merge(sb, on=["date", "_dn"], how="left")
    x = x.drop(columns="_dn")
    x["tab_first"] = x.price
    x["best_first"] = R31.best_first(x)
    months = pd.period_range(first_pred + BLEND_MONTHS, x.date.max().to_period("M"), freq="M")
    x["pb"] = monthly_blend_at(x, months)
    x["top_pick"] = top_of_field(x)
    ok = pd.Series((x.pb.notna() & (x.price > 1)).values)
    whole = ok.groupby(x.race_id.values).transform("all").values
    t = x[whole & x.is_ran.values].reset_index(drop=True)
    races = t.drop_duplicates("race_id")
    print(f"Field at the bet: {t.race_id.nunique():,} races, {len(t):,} runners that ran, from {t.date.min():%Y-%m-%d} "
          f"to {t.date.max():%Y-%m-%d}; {races.n_later.gt(0).mean():.1%} of races had a dog scratched after the open "
          f"(TAB's deduction there {races.ded[races.n_later > 0].median():.0%}, median). "
          f"{(time.monotonic() - t0) / 60:.0f} minutes in.\n")

    # 1. log loss where the field at the bet is the field that ran
    clean = t[(t.n_later == 0).values]
    books = [("ours", "p_a"), ("ours blended with TAB's first book", "pb"), ("TAB's first book", "p_book"),
             ("GRV's SP", "p_sp"), ("BSP", "p_bsp")]
    books = [(n, c) for n, c in books if c in clean]
    full = np.ones(len(clean), bool)
    for _, c in books:
        full &= clean[c].notna().groupby(clean.race_id).transform("all").values
    w = clean[full & (clean.won == 1).values]
    print(f"## 1. Log loss on the {w.race_id.nunique():,} races with nothing scratched after the open, where every book "
          f"prices every runner (lower is better)\n\n| book | log loss | less TAB's first book |\n|---|---|---|")
    base = float(-np.log(w.p_book.clip(1e-9)).mean())
    for n, c in books:
        ll = float(-np.log(w[c].clip(1e-9)).mean())
        print(f"| {n} | {ll:.4f} | {ll - base:+.4f} |")

    h_cut = t.date.quantile(0.5)
    print(f"\n## 2. The card's rule (1.3x, our blended price $2-$15, Kelly x75 cap 4), after TAB's deduction, every "
          f"walk-forward month (halves split at {h_cut:%Y-%m-%d})\n")
    card_rule(t, h_cut)

    days = np.sort(t.date.unique())
    cut = pd.Timestamp(days[int(len(days) * 0.6)])
    ch, te = t[t.date < cut].reset_index(drop=True), t[t.date >= cut].reset_index(drop=True)
    mid = te.date.quantile(0.5)
    print(f"\n## 3. Every rule: choosing on {ch.date.min():%Y-%m-%d} to {ch.date.max():%Y-%m-%d} "
          f"({ch.race_id.nunique():,} races), scored once on {te.date.min():%Y-%m-%d} to {te.date.max():%Y-%m-%d} "
          f"({te.race_id.nunique():,} races), halves split at {mid:%Y-%m-%d}\n")
    R31.bench(t, ch, te, cut, mid, PRICES, DEDUCTION)
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 34")
