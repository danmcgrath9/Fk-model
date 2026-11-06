"""Round 29: the bench, many market angles at once under one set of rules (7 Nov 2026, founder: "There would be lots of
different things you could test").

    python research/greyhound/topaz_round29.py DIR LABEL    (BETFAIR_DIR, RACES_DIR, ISOLYNX_DIR; WALK_GRV_RATING /
                                                             WALK_RELIABLE / WALK_LEAD as the weekly train; BSP_COMM)

No model: the market against itself, on every Victorian race since 2020 with a BSP on every runner. A rule is
  a segment (one value of one thing about the runner or the race, below)
  x a price band ($1.50-$3, $3-$5, $5-$8, $8-$15, $15-$40, $40-$100)
  x a bet: BACK at BSP or LAY at BSP (commission on winnings), or BACK at GRV's SP (no commission)
The price band for a BSP bet is Betfair's last pre-play traded price (known before the off, unlike BSP itself); for an
SP bet, GRV's SP. The segments:
  box; track; distance; grade; field size; Betfair's scheduled start (before 6pm, 6pm on); starts before (debut, 1-3,
  4-10, 11+); days since the last start; won last start; GRV's SP favourite last start; first time at the track;
  GRV's tip; a tracked run before / checked last time / clean last time; the trainer's second runner in the race; the
  late move (last pre-play price against the pre-play average: firmed 15%+, steady, drifted 15%+); and the race's
  pre-play volume (thin, middling, deep: terciles of the choosing years)
The rules:
  1. CHOSEN on the first 60% of race days (300+ bets and a profit), scored ONCE on the last 40%, in halves
  2. each chosen rule's score, z = return / its standard error; with no edge, about 2.3% of chosen rules reach z >= 2
     by luck, so the count of z >= 2 is set against that number
  3. RE-CHOSEN every month of the last 40% on the 12 months before it (150+ bets and a profit), then bet the month
     (a runner once per bet type, however many rules pick it), as Test 42 did
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round12 as R12       # noqa: E402
import topaz_round18 as R18       # noqa: E402
import topaz_walk as W            # noqa: E402

COMM = float(os.environ.get("BSP_COMM", "0.08") or 0.08)
BANDS = [(1.5, 3), (3, 5), (5, 8), (8, 15), (15, 40), (40, 100)]
BETS = ("back at BSP", "lay at BSP", "back at GRV's SP")
MIN_CHOOSE, MIN_MONTHLY, WINDOW = 300, 150, 12
LTP, WAP, PVOL = "WIN_PREPLAY_LAST_PRICE_TAKEN", "WIN_PREPLAY_WEIGHTED_AVERAGE_PRICE_TAKEN", "WIN_PREPLAY_VOLUME"


def betfair_extras(df: pd.DataFrame, bdir: str) -> pd.DataFrame:
    """Betfair's last and average pre-play prices, pre-play volume and scheduled start, by (date, dog name)."""
    import gbm_v0
    bf = gbm_v0.load(bdir)
    keep = [c for c in (LTP, WAP, PVOL) if c in bf]
    for c in keep:
        bf[c] = pd.to_numeric(bf[c], errors="coerce")
    bf = bf[(bf.STATE_CODE == "VIC") & (pd.to_numeric(bf.WIN_BSP, errors="coerce") > 1)]
    bf = bf.assign(bf_hour=pd.to_datetime(bf.t.astype(str), format="%H:%M:%S", errors="coerce").dt.hour)
    bf = bf[["date", "dog", "bf_hour"] + keep].drop_duplicates(["date", "dog"], keep=False)
    df = df.assign(_dn=gbm_v0.norm_name(df.dog_name))
    return df.merge(bf.rename(columns={"dog": "_dn"}), on=["date", "_dn"], how="left").drop(columns="_dn")


def returns(bet: str, won, price, comm=COMM) -> np.ndarray:
    won, price = np.asarray(won), np.asarray(price, float)
    if bet == "back at BSP":
        return np.where(won == 1, (price - 1) * (1 - comm), -1.0)
    if bet == "lay at BSP":
        return np.where(won == 1, -(price - 1), 1 - comm)
    return np.where(won == 1, price - 1, -1.0)


def segments(t: pd.DataFrame, vol_cuts=None, tracks=None) -> dict:
    """name -> boolean mask, one value of one thing about the runner or the race; a thing the data lacks is skipped.
    `tracks`: the track codes to give a segment each, the same list in every period (a track that stopped racing, like
    Cranbourne in 2022, still gets its segment, empty)."""
    out = {}
    box = pd.to_numeric(t.box, errors="coerce")
    for b in range(1, 9):
        out[f"box {b}"] = (box == b).values
    for trk in (tracks if tracks is not None else sorted(t.track.astype(str).unique())):
        out[f"track {trk}"] = (t.track.astype(str) == trk).values
    dist = t.distance.astype(float)
    for lo, hi, name in ((0, 350, "under 350 m"), (350, 420, "350-419 m"), (420, 520, "420-519 m"),
                         (520, 620, "520-619 m"), (620, 9999, "620 m+")):
        out[f"distance {name}"] = ((dist >= lo) & (dist < hi)).values
    if "grade" in t:
        g = t.grade.astype(str).str.strip()
        for v in ("Maiden", "5", "6", "7", "4"):
            out[f"grade {v}"] = (g == v).values
        out["grade 1-3"] = g.isin(["1", "2", "3"]).values
    field = t.field.astype(float)
    out["field 6 or fewer"], out["field 7"], out["field 8+"] = (field <= 6).values, (field == 7).values, (field >= 8).values
    if "bf_hour" in t:
        out["start before 6pm (Betfair's schedule)"] = (t.bf_hour < 18).values
        out["start 6pm on (Betfair's schedule)"] = (t.bf_hour >= 18).values
    runs = t.runs.astype(float)
    out["debut"], out["1-3 starts"] = (runs == 0).values, ((runs >= 1) & (runs <= 3)).values
    out["4-10 starts"], out["11+ starts"] = ((runs >= 4) & (runs <= 10)).values, (runs >= 11).values
    ds = t.days_since.astype(float)
    for lo, hi, name in ((0, 5, "up to 4 days"), (5, 9, "5-8 days"), (9, 16, "9-15 days"), (16, 30, "16-29 days"),
                         (30, 10000, "30+ days")):
        out[f"last start {name} ago"] = ((ds >= lo) & (ds < hi)).values
    if "prev_won" in t:
        out["won last start"] = (t.prev_won == 1).values
    if "prev_fav" in t:
        out["SP favourite last start"] = (t.prev_fav == 1).values
    if "track_runs" in t:
        out["first time at the track"] = ((t.track_runs == 0) & (runs > 0)).values
    if "tip_rank" in t:
        tr = t.tip_rank.fillna(0)
        for v in (1, 2, 3, 4):
            out[f"GRV tip {v}"] = (tr == v).values
        out["GRV did not tip it"] = (tr == 0).values
    if "iso_runs" in t:
        out["no tracked run"] = (t.iso_runs.fillna(0) == 0).values
    if "chk_last" in t:
        out["checked last tracked run"] = (t.chk_last == 1).values
        out["clean last tracked run"] = (t.chk_last == 0).values
    if "trainer_runners" in t:
        out["trainer has 2+ in the race"] = (t.trainer_runners >= 2).values
    if LTP in t and WAP in t:
        mv = t[LTP] / t[WAP]
        out["firmed late (last 15%+ under the average)"] = (mv <= 1 / 1.15).values
        out["steady late"] = ((mv > 1 / 1.15) & (mv < 1.15)).values
        out["drifted late (last 15%+ over the average)"] = (mv >= 1.15).values
    if PVOL in t and vol_cuts is not None:
        v = t.groupby("race_id")[PVOL].transform("sum")
        out["thin market"] = (v < vol_cuts[0]).values
        out["middling market"] = ((v >= vol_cuts[0]) & (v < vol_cuts[1])).values
        out["deep market"] = (v >= vol_cuts[1]).values
    return out


def band_price(t: pd.DataFrame, bet: str) -> np.ndarray:
    """The price that sets a rule's band, known before the bet: GRV's SP for SP bets; Betfair's last pre-play price
    (BSP where none traded) for BSP bets."""
    if bet == "back at GRV's SP":
        return t.start_price.values.astype(float)
    ltp = t[LTP].values.astype(float) if LTP in t else np.full(len(t), np.nan)
    return np.where(ltp > 1, ltp, t.bsp.values.astype(float))


def paid_price(t: pd.DataFrame, bet: str) -> np.ndarray:
    return t.start_price.values.astype(float) if bet == "back at GRV's SP" else t.bsp.values.astype(float)


def stats(r: np.ndarray) -> tuple:
    """(bets, return per bet, z): z is the mean over its standard error, 0 with fewer than 2 bets."""
    n = len(r)
    if n < 2:
        return n, (float(r.mean()) if n else np.nan), 0.0
    sd = r.std(ddof=1)
    return n, float(r.mean()), float(r.mean() / (sd / np.sqrt(n))) if sd > 0 else 0.0


def all_rules(t: pd.DataFrame, seg: dict):
    """Every (segment, band, bet) with its mask and returns."""
    for bet in BETS:
        bp, ret = band_price(t, bet), returns(bet, t.won.values, paid_price(t, bet))
        for name, m in seg.items():
            for lo, hi in BANDS:
                yield (name, lo, hi, bet), m & (bp >= lo) & (bp < hi), ret


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    df, num, rel, note = W.build_full(d)
    df, _, _ = R18.check_features(df, os.environ.get("ISOLYNX_DIR", ""))
    df = R12.tale_columns(df)
    bdir = os.environ.get("BETFAIR_DIR", "")
    if bdir and os.path.isdir(bdir):
        df = betfair_extras(df, bdir)
    print(f"# {label}: round 29, the bench ({COMM:.0%} commission at BSP)\n\n{note}\n")
    full = df.p_bsp.notna().groupby(df.race_id).transform("all").values
    t = df[full & (df.bsp > 1) & (df.start_price > 1)].copy().reset_index(drop=True)
    days = np.sort(t.date.unique())
    cut = pd.Timestamp(days[int(len(days) * 0.6)])
    ch, te = t[t.date < cut].reset_index(drop=True), t[t.date >= cut].reset_index(drop=True)
    mid = te.date.quantile(0.5)
    vol_cuts = None
    if PVOL in t:
        rv = ch.groupby("race_id")[PVOL].sum()
        vol_cuts = (float(rv.quantile(1 / 3)), float(rv.quantile(2 / 3)))
    print(f"{t.race_id.nunique():,} races, {len(t):,} runners with a BSP on every runner and GRV's SP: choosing on "
          f"{ch.date.min():%Y-%m-%d} to {ch.date.max():%Y-%m-%d} ({ch.race_id.nunique():,} races), scored once on "
          f"{te.date.min():%Y-%m-%d} to {te.date.max():%Y-%m-%d} ({te.race_id.nunique():,} races), halves split at "
          f"{mid:%Y-%m-%d}. Betfair's pre-play prices on {t[LTP].notna().mean() if LTP in t else 0:.0%} of runners.\n")
    if "bf_hour" in t:
        hrs = t.drop_duplicates("race_id").bf_hour.value_counts().sort_index()
        print("Races by Betfair's scheduled hour (a check that it is Melbourne's clock): "
              + ", ".join(f"{int(k)}h {v:,}" for k, v in hrs.items()) + "\n")

    # 1-2. chosen once, scored once
    tracks = sorted(t.track.astype(str).unique())
    sc, st = segments(ch, vol_cuts, tracks), segments(te, vol_cuts, tracks)
    h = (te.date < mid).values
    tried, chosen = 0, []
    test_rules = {k: (m, r) for k, m, r in all_rules(te, st)}
    for key, m, r in all_rules(ch, sc):
        if m.sum() < MIN_CHOOSE:
            continue
        tried += 1
        n, roi, z = stats(r[m])
        if roi > 0:
            chosen.append((key, n, roi, z))
    rows = []
    for key, n_c, roi_c, z_c in chosen:
        mt, rt = test_rules[key]
        n, roi, z = stats(rt[mt])
        r1, r2 = stats(rt[mt & h]), stats(rt[mt & ~h])
        price = paid_price(te, key[3])
        ae = te.won.values[mt].sum() / (1 / price[mt]).sum() if mt.any() else np.nan
        rows.append((key, n_c, roi_c, z_c, n, roi, z, r1, r2, ae))
    by_bet = {b: [r for r in rows if r[0][3] == b] for b in BETS}
    print("| bet | rules with 300+ bets on the choosing years | chosen (a profit there) | chosen, profit in the scored "
          "years | chosen, profit in both halves | chosen, z >= 2 on the scored years | z >= 2 expected by luck |\n"
          "|---|---|---|---|---|---|---|")
    tried_by = {b: 0 for b in BETS}
    for key, m, r in all_rules(ch, sc):
        tried_by[key[3]] += int(m.sum() >= MIN_CHOOSE)
    for b in BETS:
        rr = by_bet[b]
        print(f"| {b} | {tried_by[b]:,} | {len(rr):,} | {sum(r[5] > 0 for r in rr if r[4]):,} | "
              f"{sum(1 for r in rr if r[7][0] and r[8][0] and r[7][1] > 0 and r[8][1] > 0):,} | "
              f"{sum(r[6] >= 2 for r in rr):,} | {0.023 * len(rr):.1f} |")
    print(f"\nAll bets: {tried:,} rules tried, {len(chosen):,} chosen.\n")
    print("Every chosen rule with z >= 1.5 on the scored years, best first:\n")
    print("| rule | choosing years: bets, return, z | scored 1st half: bets, return | 2nd half: bets, return | "
          "scored: bets, A/E vs the price paid, return, z |\n|---|---|---|---|---|")
    for key, n_c, roi_c, z_c, n, roi, z, r1, r2, ae in sorted(rows, key=lambda r: -r[6]):
        if z < 1.5:
            break
        name, lo, hi, bet = key
        both = r1[0] and r2[0] and r1[1] > 0 and r2[1] > 0
        print(f"| {bet}: {name}, ${lo:g}-${hi:g} | {n_c:,}, {roi_c:+.1%}, {z_c:+.1f} | {r1[0]:,}, {r1[1]:+.1%} | "
              f"{r2[0]:,}, {r2[1]:+.1%} | {n:,}, {ae:.3f}, {roi:+.1%}, {z:+.1f}{' **both halves**' if both else ''} |")

    # 3. re-chosen every month
    months = pd.period_range(cut.to_period("M"), t.date.max().to_period("M"), freq="M")
    bets = {b: [] for b in BETS}
    picked = {b: [] for b in BETS}
    for M in months:
        w = t[(t.date >= (M - WINDOW).start_time) & (t.date < M.start_time)].reset_index(drop=True)
        cur = t[(t.date >= max(M.start_time, cut)) & (t.date < (M + 1).start_time)].reset_index(drop=True)
        if cur.empty or w.empty:
            continue
        sw, sm = segments(w, vol_cuts, tracks), segments(cur, vol_cuts, tracks)
        cur_rules = {k: (m, r) for k, m, r in all_rules(cur, sm)}
        hit = {b: np.zeros(len(cur), bool) for b in BETS}
        n_rules = {b: 0 for b in BETS}
        for key, m, r in all_rules(w, sw):
            if m.sum() >= MIN_MONTHLY and r[m].mean() > 0:
                hit[key[3]] |= cur_rules[key][0]
                n_rules[key[3]] += 1
        for b in BETS:
            ret = returns(b, cur.won.values, paid_price(cur, b))
            bets[b].append(cur[hit[b]].assign(ret=ret[hit[b]], price=paid_price(cur, b)[hit[b]]))
            picked[b].append(n_rules[b])
    print(f"\n## Re-chosen every month on the {WINDOW} months before ({MIN_MONTHLY}+ bets and a profit there), then bet\n")
    print("| bet | rules chosen a month | half | bets | winners | A/E vs the price paid | return | units | months in profit |\n"
          "|---|---|---|---|---|---|---|---|---|")
    for b in BETS:
        allb = pd.concat(bets[b]) if bets[b] else pd.DataFrame()
        if allb.empty:
            print(f"| {b} | {min(picked[b], default=0)}-{max(picked[b], default=0)} | all | 0 | | | | | |")
            continue
        for hn, hm in (("1st", allb.date < mid), ("2nd", allb.date >= mid), ("all", allb.date.notna())):
            x = allb[hm]
            if x.empty:
                continue
            bym = x.groupby(x.date.dt.to_period("M")).ret.sum()
            print(f"| {b} | {min(picked[b])}-{max(picked[b])} | {hn} | {len(x):,} | {int(x.won.sum()):,} | "
                  f"{x.won.sum() / (1 / x.price).sum():.3f} | {x.ret.mean():+.1%} | {x.ret.sum():+,.0f} | "
                  f"{(bym > 0).sum()} of {len(bym)} |")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 29")
