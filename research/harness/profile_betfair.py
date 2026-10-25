"""Profile Betfair's free ANZ harness CSVs (Automation Hub, betfair-datascientists.github.io/data/dataListing/) before
any modelling (25 Oct 2026): what each file holds, how many races and runners, the date range, and how complete each
column is. Prints a report; nothing is fitted.

    python research/harness/profile_betfair.py DIR

DIR holds the downloaded files as Betfair publishes them (yearly .zip, monthly .csv). The page's only condition on
downloading is its disclaimer: no warranty, use at your own risk."""
import io, os, sys, zipfile
import pandas as pd


def frames(d):
    for name in sorted(os.listdir(d)):
        p = os.path.join(d, name)
        if name.endswith(".zip"):
            with zipfile.ZipFile(p) as z:
                for m in z.namelist():
                    if m.lower().endswith(".csv"):
                        yield f"{name}:{m}", pd.read_csv(io.BytesIO(z.read(m)), low_memory=False)
        elif name.endswith(".csv"):
            yield name, pd.read_csv(p, low_memory=False)


def guess(cols, *words):
    for c in cols:
        if all(w in c.lower() for w in words):
            return c
    return None


def main(d):
    allf = []
    for name, f in frames(d):
        f["_file"] = name
        allf.append(f)
        print(f"{name}: {len(f):,} rows, {len(f.columns)} columns")
    if not allf:
        sys.exit(f"no csv or zip files in {d}")
    cols = sorted(set().union(*[set(f.columns) for f in allf]) - {"_file"})
    same = all(set(f.columns) == set(allf[0].columns) for f in allf)
    print(f"\ncolumns the same in every file: {same}")
    df = pd.concat(allf, ignore_index=True, sort=False)
    print(f"all files: {len(df):,} rows\n")
    print("| column | filled | distinct | example |\n|---|---|---|---|")
    for c in cols:
        s = df[c]; ex = s.dropna()
        print(f"| {c} | {s.notna().mean():.1%} | {s.nunique():,} | {str(ex.iloc[0])[:40] if len(ex) else ''} |")
    date = guess(cols, "date") or guess(cols, "time")
    market = guess(cols, "market", "id") or guess(cols, "event", "id")
    track = guess(cols, "track") or guess(cols, "venue")
    bsp = guess(cols, "bsp")
    print(f"\nread as: date={date} market={market} track={track} bsp={bsp}")
    if date:
        dt = pd.to_datetime(df[date], errors="coerce", utc=True, format="mixed")
        print(f"dates {dt.min()} to {dt.max()}; unparsed {dt.isna().mean():.1%}")
        df["_month"] = dt.dt.strftime("%Y-%m")
    if market and date:
        g = df.groupby("_month").agg(rows=(market, "size"), races=(market, "nunique"))
        if bsp:
            g["bsp_filled"] = df.groupby("_month")[bsp].apply(lambda s: pd.to_numeric(s, errors="coerce").gt(1).mean())
        print("\n| month | runner rows | races | runners with a BSP |\n|---|---|---|---|")
        for m, r in g.iterrows():
            print(f"| {m} | {int(r.rows):,} | {int(r.races):,} | {r.get('bsp_filled', float('nan')):.1%} |")
    if track:
        print(f"\ntracks: {df[track].nunique()}; top 25 by rows:")
        for t, n in df[track].value_counts().head(25).items():
            print(f"- {t}: {n:,}")
    print("\nfirst rows:")
    print(df.drop(columns=[c for c in df.columns if c.startswith("_")]).head(5).to_csv(index=False))


if __name__ == "__main__":
    main(sys.argv[1])
