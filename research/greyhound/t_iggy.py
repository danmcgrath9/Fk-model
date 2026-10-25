"""Betfair's Iggy greyhound model scored against BSP on the same races (25 Oct 2026). Iggy is the best free Australian
greyhound model (Betfair's data scientists; rated prices from sectionals, box, market prices and more). Its daily
results files sit on the same free data listing as the ANZ files: version 1 to Aug 2024, version 2 from Aug 2024.

    python research/greyhound/t_iggy.py DIR LABEL

DIR holds both the ANZ_Greyhounds files and the Iggy_Model*_Results files. The Iggy columns are not documented, so
the script prints them and picks the market id, selection id and rated price (or probability) by name; if it cannot,
it stops and says so rather than guessing.

Races: Australian, 4+ runners with a BSP above 1, exactly one winner, every kept runner carrying an Iggy price.
1. Winner log loss on the same races: Iggy, BSP, pre-play WAP (each renormalised per race), by version and year.
2. Calibration: A/E by Iggy price band (wins against Iggy's own chances).
3. Does Iggy add to BSP? chance proportional to (1/BSP)^a x (Iggy chance)^b, fitted on the first date half, scored on
   the second, against BSP alone.
4. Value at BSP: back where BSP >= k x Iggy's price (k = 1.2, 1.5, 2), flat 1 unit, ROI before commission and after an
   assumed 8% commission on each winning bet's profit, in both date halves. Not a bet list; a measurement."""
import io, os, re, sys, zipfile
import numpy as np, pandas as pd
from scipy.optimize import minimize

COMMISSION = 0.08


def read_all(d, pattern):
    fs = []
    for name in sorted(os.listdir(d)):
        if not re.search(pattern, name):
            continue
        p = os.path.join(d, name)
        if name.endswith(".zip"):
            with zipfile.ZipFile(p) as z:
                fs += [pd.read_csv(io.BytesIO(z.read(m)), low_memory=False).assign(_file=m)
                       for m in z.namelist() if m.endswith(".csv")]
        elif name.endswith(".csv"):
            fs.append(pd.read_csv(p, low_memory=False).assign(_file=name))
    return fs


def pick(cols, *alts):
    """The first column whose lower-cased name contains every word of one of the alternatives."""
    for words in alts:
        for c in cols:
            if all(w in c.lower() for w in words):
                return c
    return None


def load_iggy(d):
    fs = read_all(d, r"^Iggy_Model")
    if not fs:
        sys.exit("no Iggy_Model files in " + d)
    print("## Iggy files\n")
    for f in fs:
        print(f"- {f._file.iloc[0]}: {len(f):,} rows; columns: {', '.join(c for c in f.columns if c != '_file')}")
    out = []
    for f in fs:
        cols = [c for c in f.columns if c != "_file"]
        m = pick(cols, ("market", "id"))
        s = pick(cols, ("selection", "id"), ("runner", "id"))
        price = pick(cols, ("rated", "price"), ("model", "price"), ("rating",), ("price",))
        prob = pick(cols, ("prob",), ("chance",))
        if not m or not s or not (price or prob):
            sys.exit(f"cannot find market id / selection id / price in {f._file.iloc[0]} (columns {cols}); "
                     "add the names to t_iggy.py rather than guess")
        g = pd.DataFrame({"WIN_MARKET_ID": pd.to_numeric(f[m], errors="coerce"),
                          "SELECTION_ID": pd.to_numeric(f[s], errors="coerce"),
                          "iggy_price": pd.to_numeric(f[price], errors="coerce") if price else np.nan,
                          "iggy_prob": pd.to_numeric(f[prob], errors="coerce") if prob else np.nan,
                          "version": "V2" if "V2" in f._file.iloc[0] else "V1"})
        print(f"  {f._file.iloc[0]}: market={m}, selection={s}, price={price}, prob={prob}")
        out.append(g)
    ig = pd.concat(out, ignore_index=True).dropna(subset=["WIN_MARKET_ID", "SELECTION_ID"])
    ig = ig.drop_duplicates(["WIN_MARKET_ID", "SELECTION_ID"], keep="last")
    ig["iggy_raw"] = np.where(ig.iggy_prob.notna() & (ig.iggy_prob > 0), ig.iggy_prob,
                              np.where(ig.iggy_price > 1, 1 / ig.iggy_price, np.nan))
    return ig


def load_anz(d):
    fs = read_all(d, r"^ANZ_Greyhounds")
    df = pd.concat(fs, ignore_index=True).drop_duplicates(["WIN_MARKET_ID", "SELECTION_ID"])
    raw = df.LOCAL_MEETING_DATE.astype(str).str.strip()
    df["date"] = pd.to_datetime(raw, errors="coerce", format="%d/%m/%Y").fillna(
        pd.to_datetime(raw.str[:10], errors="coerce", format="%Y-%m-%d"))
    for c in ("WIN_BSP", "WIN_PREPLAY_WEIGHTED_AVERAGE_PRICE_TAKEN", "WIN_MARKET_ID", "SELECTION_ID"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["won"] = (df.WIN_RESULT == "WINNER").astype(int)
    return df[(df.STATE_CODE != "NZ") & (df.WIN_BSP > 1)]


def ll(d, col):
    return -np.log(d.loc[d.won == 1, col].clip(1e-12)).mean()


def blend_nll(x, d, use):
    s = x[0] * np.log(d.p_bsp.values) + (x[1] * np.log(d.p_iggy.values) if use else 0.0)
    s = pd.Series(s, index=d.index)
    e = np.exp(s - s.groupby(d.WIN_MARKET_ID).transform("max"))
    p = e / e.groupby(d.WIN_MARKET_ID).transform("sum")
    return -np.log(p[d.won == 1].clip(1e-12)).mean()


def main(d, label):
    ig = load_iggy(d)
    anz = load_anz(d)
    runners = anz.groupby("WIN_MARKET_ID").size().rename("bsp_runners")
    df = anz.merge(ig, on=["WIN_MARKET_ID", "SELECTION_ID"], how="inner")
    df = df[df.iggy_raw.notna()].join(runners, on="WIN_MARKET_ID")
    df = df[df.groupby("WIN_MARKET_ID").WIN_BSP.transform("size") == df.bsp_runners]   # Iggy priced every runner
    g = df.groupby("WIN_MARKET_ID")
    df = df[(g.won.transform("sum") == 1) & (g.WIN_BSP.transform("size") >= 4)].copy()
    for src, col in (("bsp", "WIN_BSP"), ("wap", "WIN_PREPLAY_WEIGHTED_AVERAGE_PRICE_TAKEN")):
        inv = 1 / df[col].where(df[col] > 1)
        df[f"p_{src}"] = inv / inv.groupby(df.WIN_MARKET_ID).transform("sum")
    df["p_iggy"] = df.iggy_raw / df.iggy_raw.groupby(df.WIN_MARKET_ID).transform("sum")
    df["iggy_fair"] = 1 / df.p_iggy
    print(f"\n# {label}: Iggy against BSP\n\nraces with an Iggy price on every runner: {df.WIN_MARKET_ID.nunique():,} "
          f"({df.date.min():%Y-%m-%d} to {df.date.max():%Y-%m-%d}), runners {len(df):,}")

    print("\n## 1. Winner log loss on the same races (lower is sharper)\n")
    print("| group | races | Iggy | BSP | pre-play WAP |\n|---|---|---|---|---|")
    ok = df.p_wap.notna().groupby(df.WIN_MARKET_ID).transform("all")
    for k, x in [("all", df[ok])] + [(f"{v}", y) for v, y in df[ok].groupby("version")] + \
            [(str(yr), y) for yr, y in df[ok].groupby(df[ok].date.dt.year)]:
        print(f"| {k} | {x.WIN_MARKET_ID.nunique():,} | {ll(x, 'p_iggy'):.4f} | {ll(x, 'p_bsp'):.4f} | {ll(x, 'p_wap'):.4f} |")

    print("\n## 2. Iggy's calibration (wins against Iggy's own chances)\n")
    print("| Iggy fair price | runners | wins | expected | A/E |\n|---|---|---|---|---|")
    for b, x in df.groupby(pd.cut(df.iggy_fair, [1, 2, 3, 4, 6, 8, 11, 16, 21, 31, 51, 1e9], right=False), observed=True):
        print(f"| ${b.left:g}-${b.right:g} | {len(x):,} | {x.won.sum():,} | {x.p_iggy.sum():,.1f} | "
              f"{x.won.sum() / x.p_iggy.sum():.3f} |")

    cut = df.date.quantile(0.5)
    tr, te = df[df.date < cut], df[df.date >= cut]
    print(f"\n## 3. Does Iggy add to BSP? (fit before {cut:%Y-%m-%d}, score after; {te.WIN_MARKET_ID.nunique():,} test races)\n")
    f0 = minimize(lambda x: blend_nll(x, tr, False), [1.0, 0.0], method="Nelder-Mead")
    f1 = minimize(lambda x: blend_nll(x, tr, True), [1.0, 0.0], method="Nelder-Mead")
    print("| model | a (BSP) | b (Iggy) | test log loss |\n|---|---|---|---|")
    print(f"| BSP alone | {f0.x[0]:.3f} | - | {blend_nll(f0.x, te, False):.5f} |")
    print(f"| BSP + Iggy | {f1.x[0]:.3f} | {f1.x[1]:+.3f} | {blend_nll(f1.x, te, True):.5f} |")

    print(f"\n## 4. Back at BSP where BSP >= k x Iggy's fair price (flat 1 unit)\n")
    print("| k | half | bets | wins | A/E at BSP | ROI before commission | ROI after 8% |\n|---|---|---|---|---|---|---|")
    for k in (1.2, 1.5, 2.0):
        for hname, h in (("first", tr), ("second", te)):
            x = h[h.WIN_BSP >= k * h.iggy_fair]
            if not len(x):
                continue
            prof = np.where(x.won == 1, x.WIN_BSP - 1, -1.0)
            after = np.where(x.won == 1, (x.WIN_BSP - 1) * (1 - COMMISSION), -1.0)
            print(f"| {k} | {hname} | {len(x):,} | {x.won.sum():,} | {x.won.sum() / (1 / x.WIN_BSP).sum():.3f} | "
                  f"{prof.mean():+.1%} | {after.mean():+.1%} |")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "greyhounds")
