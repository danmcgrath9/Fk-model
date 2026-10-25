"""How sharp is Betfair's win BSP for harness? (25 Oct 2026, founder's question.) Measured on Betfair's free ANZ files,
with thoroughbreds run the same way as a yardstick.

    python research/harness/t_bsp_sharp.py DIR LABEL

Race kept when: at least 4 runners carry a BSP above 1, exactly one WINNER, and the winner carries a BSP (runners with
no BSP are taken as scratched or not offered and left out). A duplicate (market, selection) row counts once.
Chance from BSP = (1/BSP) renormalised over the race's runners. Reported:
- calibration by BSP band: runners, wins, expected wins (sum of 1/BSP, NOT renormalised: what a back bet at BSP is
  actually priced at), A/E, flat 1-unit back ROI at BSP BEFORE commission (a lay makes minus that per $1 of the backer's stake);
- winner log loss of BSP v the pre-play weighted average price (WAP) and the best back at the scheduled off, each
  renormalised per race (lower = sharper);
- the same by year and state, and by the race's BSP volume, and in two date halves.
Back ROI at BSP before commission is the market's own error; commission (charged on net market winnings) comes off it."""
import io, os, sys, zipfile
import numpy as np, pandas as pd

BANDS = [1, 2, 3, 4, 6, 8, 11, 16, 21, 31, 51, 1001]


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
    return df


def races(df):
    df = df.copy()
    for c in ("WIN_BSP", "WIN_PREPLAY_WEIGHTED_AVERAGE_PRICE_TAKEN", "BEST_AVAIL_BACK_AT_SCHEDULED_OFF", "WIN_BSP_VOLUME"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["won"] = (df.WIN_RESULT == "WINNER").astype(int)
    df = df[df.WIN_BSP > 1]
    g = df.groupby("WIN_MARKET_ID")
    keep = (g.won.transform("sum") == 1) & (g.WIN_BSP.transform("size") >= 4)
    df = df[keep].copy()
    for src, col in (("bsp", "WIN_BSP"), ("wap", "WIN_PREPLAY_WEIGHTED_AVERAGE_PRICE_TAKEN"),
                     ("off", "BEST_AVAIL_BACK_AT_SCHEDULED_OFF")):
        inv = 1 / df[col].where(df[col] > 1)
        df[f"p_{src}"] = inv / inv.groupby(df.WIN_MARKET_ID).transform("sum")
    df["book"] = (1 / df.WIN_BSP).groupby(df.WIN_MARKET_ID).transform("sum")
    df["race_vol"] = df.WIN_BSP_VOLUME.groupby(df.WIN_MARKET_ID).transform("sum")
    return df


def ll(w, col):
    """Winner log loss over races where every kept runner has this price."""
    ok = w[col].notna().groupby(w.WIN_MARKET_ID).transform("all")
    x = w[ok & (w.won == 1)][col]
    return -np.log(x.clip(1e-6)).mean(), len(x)


def calib(df):
    df = df.assign(band=pd.cut(df.WIN_BSP, BANDS, right=False))
    rows = []
    for b, g in df.groupby("band", observed=True):
        n, wins, exp = len(g), g.won.sum(), (1 / g.WIN_BSP).sum()
        back = (g.won * (g.WIN_BSP - 1) - (1 - g.won)).sum() / n
        rows.append((f"${b.left:g}-${b.right:g}", n, wins, exp, wins / exp, back))
    return rows


def main(d, label):
    df = races(load(d))
    au = df[df.STATE_CODE != "NZ"]
    print(f"# {label}: BSP sharpness\n")
    print(f"races kept: {df.WIN_MARKET_ID.nunique():,} ({au.WIN_MARKET_ID.nunique():,} Australian), "
          f"runners {len(df):,}, {df.date.min():%Y-%m-%d} to {df.date.max():%Y-%m-%d}")
    print(f"median BSP book (sum of 1/BSP per race): {df.groupby('WIN_MARKET_ID').book.first().median():.3f}")
    for name, part in (("Australia", au), ("NZ", df[df.STATE_CODE == "NZ"])):
        if not len(part):
            continue
        print(f"\n## Calibration at BSP, {name} (before commission)\n")
        print("| BSP band | runners | wins | expected (1/BSP) | A/E | back ROI |\n|---|---|---|---|---|---|")
        for r in calib(part):
            print(f"| {r[0]} | {r[1]:,} | {r[2]:,} | {r[3]:,.1f} | {r[4]:.3f} | {r[5]:+.1%} |")
        n, wins, exp = len(part), part.won.sum(), (1 / part.WIN_BSP).sum()
        back = (part.won * (part.WIN_BSP - 1) - (1 - part.won)).sum() / n
        print(f"| all | {n:,} | {wins:,} | {exp:,.1f} | {wins/exp:.3f} | {back:+.1%} |")
        print("\nA lay at BSP makes minus the back ROI per $1 of the backer's stake, before commission.")
    print("\n## Winner log loss, Australia (lower = sharper; each price renormalised per race)\n")
    print("| price | log loss | races |\n|---|---|---|")
    for src in ("bsp", "wap", "off"):
        v, n = ll(au, f"p_{src}")
        print(f"| {dict(bsp='BSP', wap='pre-play WAP', off='best back at scheduled off')[src]} | {v:.4f} | {n:,} |")
    # a fair comparison: the same races for all three
    ok = au[["p_bsp", "p_wap", "p_off"]].notna().all(axis=1).groupby(au.WIN_MARKET_ID).transform("all")
    s = au[ok]
    print(f"\nsame {s.WIN_MARKET_ID.nunique():,} races for all three: " + ", ".join(
        f"{k} {ll(s, 'p_' + k)[0]:.4f}" for k in ("bsp", "wap", "off")))
    for key, title in (("year", "year"), ("STATE_CODE", "state"), ("vol", "race BSP volume (terciles)"),
                       ("half", "date half")):
        a = au.copy()
        a["year"] = a.date.dt.year
        a["half"] = np.where(a.date < a.date.quantile(0.5), "first half", "second half")
        a["vol"] = pd.qcut(a.race_vol, 3, labels=["low", "mid", "high"])
        print(f"\n## By {title}, Australia\n")
        print("| group | races | A/E all | back ROI | A/E under $4 | A/E $21+ | log loss BSP | log loss WAP |\n"
              "|---|---|---|---|---|---|---|---|")
        for k, g in a.groupby(key, observed=True):
            ae = g.won.sum() / (1 / g.WIN_BSP).sum()
            back = (g.won * (g.WIN_BSP - 1) - (1 - g.won)).sum() / len(g)
            lo, hi = g[g.WIN_BSP < 4], g[g.WIN_BSP >= 21]
            ae_lo = lo.won.sum() / (1 / lo.WIN_BSP).sum() if len(lo) else float("nan")
            ae_hi = hi.won.sum() / (1 / hi.WIN_BSP).sum() if len(hi) else float("nan")
            print(f"| {k} | {g.WIN_MARKET_ID.nunique():,} | {ae:.3f} | {back:+.1%} | {ae_lo:.3f} | {ae_hi:.3f} | "
                  f"{ll(g, 'p_bsp')[0]:.4f} | {ll(g, 'p_wap')[0]:.4f} |")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
