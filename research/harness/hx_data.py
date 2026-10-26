"""Shared loader for the harness research on Betfair's free ANZ files (25 Oct 2026).

load(dir) reads every published file, drops duplicate (market, selection) rows (the 2021-22 files overlap), reads the
meeting date in both formats Betfair uses, and returns one row per runner with:
- the race: market id, date, start (date + scheduled time), track, state, distance, gait, the market name's last word
  (which may encode the start type), field (runners with a win BSP above $1);
- the runner: horse id (Betfair's selection id, which stays with the horse across markets), name, TAB number, result,
  win and place BSP, pre-play WAP, in-play lowest price, BSP volume;
- p_bsp: 1/BSP renormalised over the race's runners that have one.
history(df) adds each horse's form from Betfair's own record, using ONLY races that started before this one: runs, days
since, its last BSP chances, wins and places, how its results compared with what BSP expected, how low it traded
in-running last time, and what changed (distance, track, gait). No feature reads the current race's prices or result.
"""
import io, os, zipfile
import numpy as np, pandas as pd

NUM = ["WIN_BSP", "PLACE_BSP", "WIN_PREPLAY_WEIGHTED_AVERAGE_PRICE_TAKEN", "WIN_INPLAY_MIN_PRICE_TAKEN",
       "WIN_BSP_VOLUME", "DISTANCE", "TAB_NUMBER", "BEST_AVAIL_BACK_AT_SCHEDULED_OFF"]


def read_all(d):
    fs = []
    for name in sorted(os.listdir(d)):
        p = os.path.join(d, name)
        if name.endswith(".zip"):
            with zipfile.ZipFile(p) as z:
                fs += [pd.read_csv(io.BytesIO(z.read(m)), low_memory=False) for m in z.namelist() if m.endswith(".csv")]
        elif name.endswith(".csv"):
            fs.append(pd.read_csv(p, low_memory=False))
    return pd.concat(fs, ignore_index=True)


def load(d):
    df = read_all(d).drop_duplicates(["WIN_MARKET_ID", "SELECTION_ID"]).copy()
    raw = df.LOCAL_MEETING_DATE.astype(str).str.strip()
    df["date"] = pd.to_datetime(raw, errors="coerce", format="%d/%m/%Y").fillna(
        pd.to_datetime(raw.str[:10], errors="coerce", format="%Y-%m-%d"))
    t = pd.to_datetime(df.SCHEDULED_RACE_TIME.astype(str).str.strip(), errors="coerce", format="%I:%M:%S %p")
    df["start"] = df.date + pd.to_timedelta(t.dt.hour.fillna(0) * 3600 + t.dt.minute.fillna(0) * 60, unit="s")
    for c in NUM:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df[df.date.notna()].copy()
    # A row is a runner that STARTED if it won, carries a BSP, or traded in-running; the rest are scratchings (or
    # markets with no BSP and no in-play trade), which must not count as runs in a horse's history.
    started = (df.WIN_RESULT == "WINNER") | (df.WIN_BSP > 1) | df.WIN_INPLAY_MIN_PRICE_TAKEN.notna()
    df = df[started].copy()
    df["race"] = df.WIN_MARKET_ID.astype("int64")
    df["horse"] = df.SELECTION_ID.astype("int64")
    df["won"] = (df.WIN_RESULT == "WINNER").astype(int)
    df["placed"] = (df.PLACE_RESULT == "WINNER").astype(int)
    df["trot"] = (df.RACE_TYPE == "Trot").astype(int)
    df["name_tag"] = df.WIN_MARKET_NAME.astype(str).str.split().str[-1].where(lambda s: s.str.len() <= 4, "other")
    has = df.WIN_BSP > 1
    df["field"] = has.groupby(df.race).transform("sum")
    inv = (1 / df.WIN_BSP).where(has)
    df["p_bsp"] = inv / inv.groupby(df.race).transform("sum")
    inv = (1 / df.WIN_PREPLAY_WEIGHTED_AVERAGE_PRICE_TAKEN).where(df.WIN_PREPLAY_WEIGHTED_AVERAGE_PRICE_TAKEN > 1)
    df["p_wap"] = inv / inv.groupby(df.race).transform("sum")
    df["bsp_rank"] = df.WIN_BSP.where(has).groupby(df.race).rank(method="min")
    df["race_vol"] = df.WIN_BSP_VOLUME.groupby(df.race).transform("sum")
    return df.sort_values(["start", "race", "TAB_NUMBER"]).reset_index(drop=True)


def history(df):
    """Point-in-time form per horse from earlier races only (shifted within the horse's own sorted runs)."""
    df = df.sort_values(["horse", "start", "race"]).copy()
    g = df.groupby("horse", sort=False)
    prev = lambda c: g[c].shift(1)
    df["n_prev"] = g.cumcount()
    df["days_since"] = (df.start - prev("start")).dt.total_seconds() / 86400
    for k in (1, 2, 3):
        df[f"p_last{k}"] = g["p_bsp"].shift(k)
    df["p_mean5"] = g["p_bsp"].transform(lambda s: s.shift(1).rolling(5, min_periods=1).mean())
    cw = g["won"].cumsum() - df.won
    cp = g["placed"].cumsum() - df.placed
    ce = g["p_bsp"].transform(lambda s: s.fillna(0).cumsum()) - df.p_bsp.fillna(0)
    df["wins_prev"], df["places_prev"] = cw, cp
    df["win_rate"] = (cw + 0.1) / (df.n_prev + 1)
    df["place_rate"] = (cp + 0.3) / (df.n_prev + 1)
    df["ae_prev"] = (cw + 1) / (ce + 1)                       # wins against what BSP expected, shrunk to 1
    df["last_won"], df["last_placed"] = prev("won"), prev("placed")
    df["last_inplay_min"] = np.log(prev("WIN_INPLAY_MIN_PRICE_TAKEN"))
    df["last_close_lost"] = ((prev("WIN_INPLAY_MIN_PRICE_TAKEN") <= 1.5) & (prev("won") == 0)).astype(float)
    df.loc[df.n_prev == 0, "last_close_lost"] = np.nan
    df["last_bsp_rank"] = prev("bsp_rank")
    df["dist_change"] = df.DISTANCE - prev("DISTANCE")
    df["same_track"] = (df.TRACK == prev("TRACK")).astype(float).where(df.n_prev > 0)
    df["gait_change"] = (df.trot != prev("trot")).astype(float).where(df.n_prev > 0)
    df["last_tab"] = prev("TAB_NUMBER")
    df["last_field"] = prev("field")
    df["log_vol_prev"] = np.log1p(g["race_vol"].transform(lambda s: s.shift(1).rolling(5, min_periods=1).mean()))
    df["tab_rel"] = df.TAB_NUMBER / df.field.where(df.field > 0)
    df = add_v2(df, g)
    return df.sort_values(["start", "race", "TAB_NUMBER"]).reset_index(drop=True)


def add_v2(df, g):
    """v2 inputs (26 Oct 2026), still only from earlier races:
    - a market rating per run, mr = log(BSP chance x field): 0 is an average runner whatever the field size, so runs in
      fields of 6 and 12 compare; the horse's smoothed rating (EWMA, alpha 0.3), its best of the last five and its trend;
    - how it ran against that rating: won minus its BSP chance, smoothed; and how close it got in running (log of its
      lowest in-play price), smoothed;
    - the race it meets today: each runner's smoothed rating against the mean of its rivals' and its rank in the field
      (no other input says who it is racing against);
    - the draw: point-in-time win rate, and wins against what BSP expected, for this TAB number at this track and gait,
      from every earlier race there."""
    df["mr"] = np.log((df.p_bsp * df.field).where(df.p_bsp > 0))
    df["perf"] = (df.won - df.p_bsp).where(df.p_bsp.notna())
    df["close"] = np.log(df.WIN_INPLAY_MIN_PRICE_TAKEN)
    ewm = lambda c: g[c].transform(lambda x: x.shift(1).ewm(alpha=0.3, ignore_na=True).mean())
    df["mr_ewm"], df["perf_ewm"], df["close_ewm"] = ewm("mr"), ewm("perf"), ewm("close")
    df["mr_best5"] = g["mr"].transform(lambda x: x.shift(1).rolling(5, min_periods=1).max())
    df["mr_trend"] = g["mr"].shift(1) - df.mr_ewm.where(df.n_prev >= 2)
    # today's rivals: mean smoothed rating of the others in the race (a first starter counts as the field's median)
    base = df.mr_ewm.fillna(df.mr_ewm.median())
    tot, cnt = base.groupby(df.race).transform("sum"), base.groupby(df.race).transform("size")
    df["rivals_mr"] = (tot - base) / (cnt - 1).where(cnt > 1)
    df["mr_vs_rivals"] = df.mr_ewm - df.rivals_mr
    df["mr_rank"] = df.mr_ewm.groupby(df.race).rank(ascending=False, method="min")
    # the draw at this track and gait, from earlier races only
    o = df.sort_values(["start", "race"])
    key = [o.TRACK, o.trot, o.TAB_NUMBER]
    k = o.groupby(key, sort=False)
    runs = k.cumcount()
    wins = k.won.cumsum() - o.won
    exp = k.p_bsp.transform(lambda x: x.fillna(0).cumsum()) - o.p_bsp.fillna(0)
    df.loc[o.index, "draw_win_rate"] = (wins + 1) / (runs + 10)
    df.loc[o.index, "draw_ae"] = (wins + 5) / (exp + 5)
    df.loc[o.index, "draw_runs"] = runs
    return df


FEATURES = ["DISTANCE", "trot", "TAB_NUMBER", "tab_rel", "field", "n_prev", "days_since", "p_last1", "p_last2",
            "p_last3", "p_mean5", "wins_prev", "places_prev", "win_rate", "place_rate", "ae_prev", "last_won",
            "last_placed", "last_inplay_min", "last_close_lost", "last_bsp_rank", "dist_change", "same_track",
            "gait_change", "last_tab", "last_field", "log_vol_prev"]
CATS = ["STATE_CODE", "TRACK", "name_tag"]
FEATURES_V2 = FEATURES + ["mr_ewm", "mr_best5", "mr_trend", "perf_ewm", "close_ewm", "rivals_mr", "mr_vs_rivals",
                          "mr_rank", "draw_win_rate", "draw_ae", "draw_runs"]


def renorm(p, race):
    p = pd.Series(np.asarray(p, float))
    return (p / p.groupby(np.asarray(race)).transform("sum")).to_numpy()
