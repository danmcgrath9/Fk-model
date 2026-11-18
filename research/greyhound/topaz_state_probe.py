"""What a state's pulled data holds (18 Nov 2026, founder: "try NSW if it works")

Run on a state's pull (gh topaz mode=run, states=NSW): the months, races and runners Topaz gave, by year; the tracks;
how many runs carry a stewards' comment, a run-line code, a first-split position and GRV's rating; the race records
(tips) when RACES_DIR has them; and how many races Betfair's free ANZ files price at BSP, by the same join the walk
uses. Counts and rates only: no race, dog or price is printed (tracks are named).

    python research/greyhound/topaz_state_probe.py DIR LABEL
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def main(d, label):
    from greyhound.ratings import load_topaz
    print(f"# {label}: what the pull holds\n")
    try:
        runs = load_topaz(d)
    except FileNotFoundError as e:
        print(f"Nothing pulled: {e}")
        return 1
    runs["date"] = pd.to_datetime(runs.date, errors="coerce")
    print(f"Runs: {len(runs):,} in {runs.race_id.nunique():,} races, {runs.date.min():%Y-%m-%d} to "
          f"{runs.date.max():%Y-%m-%d}\n")
    y = runs.assign(year=runs.date.dt.year).groupby("year")
    print("| year | races | runners | tracks |\n|---|---|---|---|")
    for yr, g in y:
        print(f"| {yr} | {g.race_id.nunique():,} | {len(g):,} | {g.get('track_name', g.get('track')).nunique()} |")
    trk = runs.get("track_name", runs.get("track")).fillna("").astype(str)
    top = trk.value_counts()
    print("\nTracks, by runners since 2025: " + ", ".join(
        f"{t} {n:,}" for t, n in trk[runs.date >= "2025-01-01"].value_counts().head(25).items()) + "\n")
    fills = {c: float(runs[c].notna().mean() if runs[c].dtype != object else
                      runs[c].fillna("").astype(str).str.strip().ne("").mean())
             for c in ("comment", "run_line", "jump", "split_pos", "pir", "topaz_rating", "start_price", "box")
             if c in runs}
    print("Filled, share of runs: " + ", ".join(f"{c} {v:.0%}" for c, v in fills.items()) + "\n")
    rd = os.environ.get("RACES_DIR", "")
    if rd and os.path.isdir(rd):
        from greyhound.races import load_races
        races = load_races(rd)
        print(f"Race records (tips): {len(races):,}\n")
    bf = os.environ.get("BETFAIR_DIR", "")
    if bf and os.path.isdir(bf):
        import topaz_walk as W
        try:
            df, _, _, note = W.build(d)
            ok = df.p_mkt.notna() if "p_mkt" in df else pd.Series(False, index=df.index)
            full = ok.groupby(df.race_id).transform("all")
            print(f"{note}\nRunners with a BSP: {ok.mean():.0%}; races with every runner priced: "
                  f"{full.groupby(df.race_id).first().mean():.0%}\n")
        except Exception as e:     # the walk's build is Victorian by habit; say where it stops, never the data
            print(f"The walk's build stopped: {type(e).__name__} in topaz_walk.build\n")
    print(f"{len(top):,} tracks in all")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz state probe"))
