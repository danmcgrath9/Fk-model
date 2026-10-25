"""Betting angles at Betfair SP for harness, every one split into two date halves (25 Oct 2026, founder: "And betting
angles"). Run after hx_model.py, which leaves DIR/hx_preds.parquet.

    python research/harness/hx_angles.py DIR LABEL

Betfair SP is the only price in these files, so every angle is a back or a lay at BSP. 8% commission on winnings (the
figure the gallops tests use). Per 1-unit bet: back = won ? (BSP-1)*0.92 : -1; lay (1 unit of the backer's stake) =
won ? -(BSP-1) : 0.92. A/E = wins / sum of 1/BSP. An angle counts only if it makes money in BOTH halves; with this many
angles tried, a few will pass one half by chance, so the size of the sample matters as much as the sign.

Part 1, no model: market-structure and form angles from Betfair's own record, over 2021-2026 (2020 is spent building
each horse's history). Part 2, with the market-history model: back or lay where it disagrees with BSP, on the model's
holdout (2025 on) only. Part 3: the place market at place BSP, by price band."""
import os, sys
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hx_data import load, history

COMM = 0.08


def pl(s, kind, price="WIN_BSP", res="won"):
    b, w = s[price].to_numpy(), s[res].to_numpy() == 1
    if kind == "back":
        return np.where(w, (b - 1) * (1 - COMM), -1.0)
    return np.where(w, -(b - 1), 1 - COMM)


def table(title, angles, df, price="WIN_BSP", res="won"):
    print(f"\n## {title}\n")
    print("| angle | half | bets | wins | A/E | back ROI | lay ROI |\n|---|---|---|---|---|---|---|")
    held = []
    for name, mask in angles:
        signs = {}
        for h in ("first half", "second half"):
            s = df[mask & (df.half == h)]
            if not len(s):
                continue
            exp = (1 / s[price]).sum()
            bk, ly = pl(s, "back", price, res).mean(), pl(s, "lay", price, res).mean()
            signs[h] = (bk, ly)
            print(f"| {name} | {h} | {len(s):,} | {int(s[res].sum()):,} | {s[res].sum() / exp:.3f} | {bk:+.1%} | {ly:+.1%} |")
        if len(signs) == 2:
            for k, side in ((0, "back"), (1, "lay")):
                if all(v[k] > 0 for v in signs.values()):
                    held.append(f"{name}: {side} ({signs['first half'][k]:+.1%}, {signs['second half'][k]:+.1%})")
    print("\nprofitable in both halves after commission: " + ("; ".join(held) if held else "none"))


def band(s, lo, hi, price="WIN_BSP"):
    return (s[price] >= lo) & (s[price] < hi)


def main(d, label):
    df = history(load(d))
    df = df[df.STATE_CODE != "NZ"]
    g = df.groupby("race")
    df = df[g.WIN_BSP.transform(lambda s: (s > 1).all()) & (g.won.transform("sum") == 1) & (df.field >= 4)].copy()
    df = df[df.date >= "2021-01-01"].copy()
    dates = np.sort(df.date.unique()); cut = dates[len(dates) // 2]
    df["half"] = np.where(df.date < cut, "first half", "second half")
    vol_lo = df.race_vol <= df.groupby("race").race_vol.first().quantile(1 / 3)
    print(f"# {label}: angles at BSP\n")
    print(f"Part 1 and 3: {df.race.nunique():,} Australian races, {df.date.min():%Y-%m-%d} to {df.date.max():%Y-%m-%d}, "
          f"halves split at {pd.Timestamp(cut):%Y-%m-%d}. 8% commission.")
    fav = df.bsp_rank == 1
    angles = [
        ("every runner", df.won >= 0),
        ("favourite", fav),
        ("favourite, low-volume race (bottom third)", fav & vol_lo),
        ("favourite, field 10+", fav & (df.field >= 10)),
        ("$21-$51", band(df, 21, 51)),
        ("$51+", band(df, 51, 10000)),
        ("TAB 1, pacers", (df.TAB_NUMBER == 1) & (df.trot == 0)),
        ("TAB 1, trotters", (df.TAB_NUMBER == 1) & (df.trot == 1)),
        ("TAB 2", df.TAB_NUMBER == 2),
        ("TAB 10+", df.TAB_NUMBER >= 10),
        ("trotters, under $6", (df.trot == 1) & band(df, 1, 6)),
        ("first up (60+ days), under $6", (df.days_since > 60) & band(df, 1, 6)),
        ("first up (60+ days), $6+", (df.days_since > 60) & band(df, 6, 10000)),
        ("backed up within 7 days, under $6", (df.days_since <= 7) & band(df, 1, 6)),
        ("last start traded $1.50 or less and lost", df.last_close_lost == 1),
        ("last start traded $1.50 or less and lost, under $6", (df.last_close_lost == 1) & band(df, 1, 6)),
        ("beaten favourite last start", (df.last_bsp_rank == 1) & (df.last_won == 0)),
        ("won last start at $11+", (df.last_won == 1) & (df.p_last1 < 1 / 11)),
        ("switching gait", df.gait_change == 1),
        ("beat BSP's expectation 1.5x over 5+ runs", (df.ae_prev >= 1.5) & (df.n_prev >= 5)),
        ("lost to BSP's expectation (0.5x) over 10+ runs, under $6", (df.ae_prev <= 0.5) & (df.n_prev >= 10) & band(df, 1, 6)),
    ]
    table("Part 1: no model, win at BSP", angles, df)

    pf = os.path.join(d, "hx_preds.parquet")
    if os.path.exists(pf):
        ho = pd.read_parquet(pf)
        ho = ho[ho.half != "validation"].copy()
        ho["ratio"] = ho.p_model / ho.p_bsp
        print(f"\nPart 2: holdout {ho.race.nunique():,} races from {ho.date.min():%Y-%m-%d}; ratio = model chance / BSP chance.")
        rows = []
        for lo, hi in ((1, 4), (4, 8), (8, 15), (15, 30), (30, 50), (50, 10000)):
            rows.append((f"lay, ratio <= 0.625, ${lo}-${hi}", (ho.ratio <= 0.625) & band(ho, lo, hi)))
        for lo, hi in ((1, 4), (4, 8), (8, 15), (15, 30), (30, 10000)):
            rows.append((f"back, ratio >= 1.5, ${lo}-${hi}", (ho.ratio >= 1.5) & band(ho, lo, hi)))
        for lo, hi in ((0, 0.5), (0.5, 0.625), (0.625, 0.8), (0.8, 1.25), (1.25, 1.5), (1.5, 2), (2, 99)):
            rows.append((f"ratio {lo}-{hi}, all prices", (ho.ratio >= lo) & (ho.ratio < hi)))
        table("Part 2: where the market-history model disagrees with BSP", rows, ho)
    else:
        print("\nPart 2 skipped: run hx_model.py first")

    pdf = df[(df.PLACE_BSP > 1) & df.placed.notna()]
    rows = [(f"place ${lo}-${hi}", band(pdf, lo, hi, "PLACE_BSP")) for lo, hi in
            ((1, 1.5), (1.5, 2), (2, 3), (3, 5), (5, 10), (10, 10000))]
    rows += [("place, win favourite", pdf.bsp_rank == 1), ("place, win $21+", band(pdf, 21, 10000))]
    print(f"\nPart 3: {pdf.race.nunique():,} races with a place BSP.")
    table("Part 3: the place market at place BSP", rows, pdf, "PLACE_BSP", "placed")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "harness")
