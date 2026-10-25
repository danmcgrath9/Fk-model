"""Box bias on Australian greyhound tracks, and whether the market already prices it (25 Oct 2026, founder: "Yep" to
measuring it before the Topaz key arrives). Betfair's free ANZ greyhound files: box, track, distance, result, BSP.

    python research/greyhound/t_box_bias.py DIR LABEL

Kept: Australian win markets with 4+ runners carrying a BSP above 1 and exactly one winner; one row per (market,
selection). A runner with TAB number 9 or 10 is a reserve that took a scratched dog's box, so its real box is unknown:
it stays in its race (it was a runner) but never counts toward a box's rates.

1. Raw: win rate by box against the field-size share, Australia-wide, and A/E at BSP by box (does BSP already price
   the box?), in two date halves.
2. Point-in-time box rate per track and distance: for each race, box b's wins / starts at that track and distance from
   races BEFORE that day only, shrunk toward the national rate for box b with a prior of PRIOR starts, divided by the
   national all-box rate. No race uses its own day.
3. Does the box rate add to BSP? A two-parameter conditional logit, chance proportional to
   (1/BSP)^a x box_ratio^b, fitted on the first date half and scored on the second, against BSP alone (a only).
   b near 0 = the market already has it. Winner log loss, lower is sharper.
Nothing here is a bet; it measures one feature."""
import io, os, sys, zipfile
import numpy as np, pandas as pd
from scipy.optimize import minimize

PRIOR = 200


def load(d):
    fs = []
    for name in sorted(os.listdir(d)):
        p = os.path.join(d, name)
        if name.endswith(".zip"):
            with zipfile.ZipFile(p) as z:
                fs += [pd.read_csv(io.BytesIO(z.read(m)), low_memory=False) for m in z.namelist() if m.endswith(".csv")]
        elif name.endswith(".csv"):
            fs.append(pd.read_csv(p, low_memory=False))
    df = pd.concat(fs, ignore_index=True).drop_duplicates(["WIN_MARKET_ID", "SELECTION_ID"])
    raw = df.LOCAL_MEETING_DATE.astype(str).str.strip()
    df["date"] = pd.to_datetime(raw, errors="coerce", format="%d/%m/%Y").fillna(
        pd.to_datetime(raw.str[:10], errors="coerce", format="%Y-%m-%d"))
    df["WIN_BSP"] = pd.to_numeric(df.WIN_BSP, errors="coerce")
    df["box"] = pd.to_numeric(df.TAB_NUMBER, errors="coerce")
    df["won"] = (df.WIN_RESULT == "WINNER").astype(int)
    df = df[(df.STATE_CODE != "NZ") & (df.WIN_BSP > 1) & df.date.notna()]
    g = df.groupby("WIN_MARKET_ID")
    df = df[(g.won.transform("sum") == 1) & (g.WIN_BSP.transform("size") >= 4)].copy()
    df["field"] = df.groupby("WIN_MARKET_ID").WIN_BSP.transform("size")
    df["real_box"] = df.box.between(1, 8)
    df["dist"] = pd.to_numeric(df.DISTANCE, errors="coerce").round().astype("Int64")
    df["td"] = df.TRACK.astype(str) + " " + df.dist.astype(str) + "m"
    df["p_bsp"] = (1 / df.WIN_BSP) / (1 / df.WIN_BSP).groupby(df.WIN_MARKET_ID).transform("sum")
    return df.sort_values(["date", "WIN_MARKET_ID"]).reset_index(drop=True)


def raw_tables(df):
    b = df[df.real_box]
    half = b.date < df.date.quantile(0.5)
    print("## 1. Box, Australia-wide (runners in boxes 1-8)\n")
    print("| box | runners | win rate | field-size share | wins / share | A/E at BSP | A/E first half | A/E second half |")
    print("|---|---|---|---|---|---|---|---|")
    for k, g in b.groupby("box"):
        share = (1 / g.field).mean()
        ae = lambda x: x.won.sum() / (1 / x.WIN_BSP).sum()
        print(f"| {int(k)} | {len(g):,} | {g.won.mean():.1%} | {share:.1%} | {g.won.mean() / share:.2f} | {ae(g):.3f} | "
              f"{ae(g[half[g.index]]):.3f} | {ae(g[~half[g.index]]):.3f} |")
    print(f"\nreserves (TAB 9-10, real box unknown) left out of the box rates: {(~df.real_box).sum():,} runners")


def point_in_time_ratio(df):
    """box_ratio for every runner from races at its track and distance on EARLIER days only."""
    b = df[df.real_box]
    early = b[b.date < df.date.quantile(0.5)]                         # the prior's centre comes from the first half only,
    nat = early.groupby("box").won.mean()                             # so nothing in the scored second half leaks into it
    allbox = early.won.mean()
    # cumulative wins and starts per (td, box) through each day, then shifted to the PREVIOUS day
    day = b.groupby(["td", "box", "date"]).agg(w=("won", "sum"), n=("won", "size")).reset_index()
    day = day.sort_values(["td", "box", "date"])
    day[["cw", "cn"]] = day.groupby(["td", "box"])[["w", "n"]].cumsum()
    day["cw_prev"] = day.cw - day.w
    day["cn_prev"] = day.cn - day.n
    out = df.merge(day[["td", "box", "date", "cw_prev", "cn_prev"]], on=["td", "box", "date"], how="left")
    prior = out.box.map(nat).fillna(allbox)
    rate = (out.cw_prev.fillna(0) + PRIOR * prior) / (out.cn_prev.fillna(0) + PRIOR)
    out["box_ratio"] = np.where(out.real_box, rate / allbox, 1.0)    # a reserve gets no box information
    out["prev_starts"] = out.cn_prev.fillna(0)
    return out


def nll(params, d, use_box):
    a = params[0]; b = params[1] if use_box else 0.0
    s = a * np.log(d.p_bsp.values) + b * np.log(d.box_ratio.values)
    s = pd.Series(s, index=d.index)
    m = s.groupby(d.WIN_MARKET_ID).transform("max")
    e = np.exp(s - m)
    p = e / e.groupby(d.WIN_MARKET_ID).transform("sum")
    return -np.log(p[d.won == 1].clip(1e-12)).mean()


def blend(df):
    bad = pd.Series(False, index=df.index)
    for c in ("p_bsp", "box_ratio"):
        nf = ~np.isfinite(np.log(df[c].astype(float).where(df[c] > 0)))
        if nf.any():
            print(f"\n{c}: {nf.sum():,} runners with a zero or missing value (e.g. "
                  f"{df.loc[nf, ['TRACK', 'td', 'box', c]].head(3).to_dict('records')}); their races are left out")
        bad |= nf
    df = df[~bad.groupby(df.WIN_MARKET_ID).transform("any")]
    cut = df.date.quantile(0.5)
    tr, te = df[df.date < cut], df[df.date >= cut]
    print(f"\n## 3. Does the point-in-time box rate add to BSP? (fit before {cut:%Y-%m-%d}, score after)\n")
    f0 = minimize(lambda x: nll(x, tr, False), [1.0], method="Nelder-Mead")
    f1 = minimize(lambda x: nll(x, tr, True), [1.0, 0.0], method="Nelder-Mead")
    print("| model | a (BSP) | b (box) | train log loss | test log loss | test races |\n|---|---|---|---|---|---|")
    for name, f, ub in (("BSP alone", f0, False), ("BSP + box rate", f1, True)):
        a = f.x[0]; b = f.x[1] if ub else 0.0
        print(f"| {name} | {a:.3f} | {b:+.3f} | {nll(f.x, tr, ub):.5f} | {nll(f.x, te, ub):.5f} | {te.WIN_MARKET_ID.nunique():,} |")
    raw = -np.log(te[te.won == 1].p_bsp).mean()
    print(f"\nBSP as is (a = 1): test log loss {raw:.5f}. A gain under about 0.0005 is noise at this sample size.")
    # box-only skill, for scale: chance proportional to box_ratio within each race
    s = te.box_ratio / te.box_ratio.groupby(te.WIN_MARKET_ID).transform("sum")
    uni = -np.log(1 / te[te.won == 1].field).mean()
    print(f"box rate alone (no prices): test log loss {-np.log(s[te.won == 1]).mean():.5f} against "
          f"{uni:.5f} for equal chances")


def tracks(df):
    print("\n## 2. Track and distance: box 1 and box 8 against the field-size share (2,000+ races)\n")
    b = df[df.real_box]
    rows = []
    for td, g in b.groupby("td"):
        if g.WIN_MARKET_ID.nunique() < 2000:
            continue
        r = {"td": td, "races": g.WIN_MARKET_ID.nunique()}
        for k in (1, 8):
            x = g[g.box == k]
            r[k] = x.won.mean() / (1 / x.field).mean() if len(x) else np.nan
            r[f"ae{k}"] = x.won.sum() / (1 / x.WIN_BSP).sum() if len(x) else np.nan
        rows.append(r)
    print("| track distance | races | box 1 wins/share | box 1 A/E at BSP | box 8 wins/share | box 8 A/E at BSP |")
    print("|---|---|---|---|---|---|")
    for r in sorted(rows, key=lambda r: -r[1]):
        print(f"| {r['td']} | {r['races']:,} | {r[1]:.2f} | {r['ae1']:.3f} | {r[8]:.2f} | {r['ae8']:.3f} |")


def main(d, label):
    df = load(d)
    print(f"# {label}: box bias\n\nraces {df.WIN_MARKET_ID.nunique():,}, runners {len(df):,}, "
          f"{df.date.min():%Y-%m-%d} to {df.date.max():%Y-%m-%d}; track-distances {df.td.nunique()}\n")
    raw_tables(df)
    tracks(df)
    blend(point_in_time_ratio(df))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "greyhounds")
