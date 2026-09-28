import numpy as np, bench as b
import warnings; warnings.filterwarnings("ignore")

def nanfirst(A):
    """first non-NaN along axis 1."""
    ok = ~np.isnan(A); idx = np.where(ok.any(1), ok.argmax(1), 0)
    v = A[np.arange(len(A)), idx]; v[~ok.any(1)] = np.nan; return v

def firstk(A, k, fn):
    """fn over the first k non-NaN values per row."""
    out = np.full(len(A), np.nan)
    ok = ~np.isnan(A)
    rank = np.cumsum(ok, 1)
    M = np.where(ok & (rank <= k), A, np.nan)
    with np.errstate(all="ignore"):
        out = fn(M, axis=1)
    return out

def recency(A, decay=0.8, k=4):
    ok = ~np.isnan(A); rank = np.cumsum(ok, 1)
    use = ok & (rank <= k)
    w = np.where(use, decay ** (rank - 1), 0.0)
    s = (np.where(use, A, 0) * w).sum(1); ws = w.sum(1)
    return np.where(ws > 0, s / np.maximum(ws, 1e-12), np.nan)

def engineered():
    D = b.D; P = D["P"].astype(float); f = {n: i for i, n in enumerate(D["past_fields"])}
    col = lambda n: P[:, :, f[n]].copy()
    trial = col("trial") == 1
    race = lambda n: np.where(trial, np.nan, col(n))      # race runs only
    ri = D["race_idx"]
    out = {}
    R = race("rating")
    out["e_rat_last"] = nanfirst(R); out["e_rat_mean3"] = firstk(R, 3, np.nanmean)
    out["e_rat_max5"] = firstk(R, 5, np.nanmax); out["e_rat_max10"] = firstk(R, 10, np.nanmax)
    out["e_rat_rw"] = recency(R); out["e_rat_n"] = (~np.isnan(R)).sum(1)
    out["e_rat_trend"] = out["e_rat_last"] - firstk(R, 5, np.nanmean)
    out["e_rat_std5"] = firstk(R, 5, np.nanstd)
    for n in ("wfaRat", "raceRating", "vsClass", "vsAllAvg", "vsTrack", "speedRating", "finishingSpeed", "last600", "to600", "expected"):
        A = race(n); out[f"e_{n}_last"] = nanfirst(A); out[f"e_{n}_rw"] = recency(A); out[f"e_{n}_max5"] = firstk(A, 5, np.nanmax)
    fin, run = race("finish"), race("runners")
    share = (fin - 1) / np.maximum(run - 1, 1)
    out["e_fin_share_last"] = nanfirst(share); out["e_fin_share_rw"] = recency(share)
    out["e_win_rate10"] = firstk(np.where(np.isnan(fin), np.nan, (fin == 1).astype(float)), 10, np.nanmean)
    out["e_place_rate10"] = firstk(np.where(np.isnan(fin), np.nan, (fin <= 3).astype(float)), 10, np.nanmean)
    mar = np.minimum(race("margin"), 20)
    out["e_margin_last"] = nanfirst(mar); out["e_margin_rw"] = recency(mar)
    bsp = race("bsp"); lb = -np.log(bsp)
    out["e_lbsp_last"] = nanfirst(lb); out["e_lbsp_rw"] = recency(lb); out["e_lbsp_max5"] = firstk(lb, 5, np.nanmax)
    out["e_lbsp_mean10"] = firstk(lb, 10, np.nanmean)
    beat = np.where(np.isnan(fin) | np.isnan(bsp), np.nan, (fin == 1) - 1 / bsp)
    out["e_beat_rw"] = recency(beat); out["e_beat_sum10"] = firstk(beat, 10, np.nansum)
    # rating relative to its own price: ran above or below what the market expected
    days = col("days_before")
    out["e_days_last"] = nanfirst(np.where(trial, np.nan, days))
    out["e_days_any"] = nanfirst(days)
    d2 = np.sort(np.where(trial, np.nan, days), 1)
    out["e_gap_prev"] = d2[:, 1] - d2[:, 0]
    out["e_runs_90"] = ((days <= 90) & ~trial).sum(1); out["e_runs_365"] = ((days <= 365) & ~trial).sum(1)
    out["e_trials_60"] = ((days <= 60) & trial).sum(1)
    tdays = np.where(trial, days, np.nan); out["e_days_trial"] = np.nanmin(tdays, 1)
    dist_today = D["distance"][ri]
    dist = race("distance")
    out["e_dist_change"] = dist_today - nanfirst(dist)
    near = np.abs(dist - dist_today[:, None]) <= 200
    out["e_rat_at_dist_max"] = np.nanmax(np.where(near, R, np.nan), 1)
    out["e_n_at_dist"] = (near & ~np.isnan(R)).sum(1)
    gb = race("going_band"); gt = D["going"][ri]
    same_g = gb == gt[:, None]
    out["e_rat_at_going_max"] = np.nanmax(np.where(same_g, R, np.nan), 1)
    out["e_n_at_going"] = (same_g & ~np.isnan(R)).sum(1)
    st = race("same_track") == 1
    out["e_rat_at_track_max"] = np.nanmax(np.where(st, R, np.nan), 1); out["e_n_at_track"] = (st & ~np.isnan(R)).sum(1)
    settle = (race("settle") - 1) / np.maximum(run - 1, 1)
    out["e_settle_rw"] = recency(settle); out["e_settle_last"] = nanfirst(settle)
    p4 = (race("pos400") - 1) / np.maximum(run - 1, 1)
    out["e_gain_rw"] = recency(settle - share)
    out["e_weight_change"] = D["X"][:, D["colidx"]["weight"]] - nanfirst(race("weight"))
    out["e_prize_last"] = np.log1p(nanfirst(race("prize"))); out["e_fs_rw"] = recency(race("field_strength"))
    out["e_rat_minus_lws"] = out["e_rat_max5"] - D["lws"][ri]
    return out

def relative(v):
    """v minus race max, v minus race mean, rank share within race (0 = best)."""
    D = b.D; ri = D["race_idx"]; nR = D["n_races"]
    ok = ~np.isnan(v)
    mx = np.full(nR, -np.inf); np.maximum.at(mx, ri[ok], v[ok]); mx[np.isinf(mx)] = np.nan
    s = np.bincount(ri, weights=np.where(ok, v, 0), minlength=nR); c = np.bincount(ri, weights=ok, minlength=nR)
    mean = np.where(c > 0, s / np.maximum(c, 1), np.nan)
    # rank: order by race then value desc
    order = np.lexsort((-np.nan_to_num(v, nan=-1e9), ri))
    rank = np.empty(len(v)); pos = np.arange(len(v)) - D["starts"][ri[order]]
    rank[order] = pos
    n = D["ends"] - D["starts"]
    rk = rank / np.maximum(n[ri] - 1, 1); rk[~ok] = np.nan
    return v - mx[ri], v - mean[ri], rk

def build(rel_keys=None):
    D = b.D
    E = engineered()
    names = list(D["cols"]); cols = [D["X"].astype(float)]
    for k, v in E.items(): names.append(k); cols.append(v[:, None])
    rel_src = rel_keys if rel_keys is not None else [k for k in E if not k.startswith("e_n_") and not k.startswith("e_runs") and not k.startswith("e_trials")] + \
        [c for c in ("raw_neural", "rating_neural", "rating_peak", "rating_peak12m", "raw_mkt_class", "jockeyForm_lastTwelveMonthWinPercentage",
                     "trainerForm_lastTwelveMonthWinPercentage", "sm_early_speed", "weight", "raw_speed") if c in D["colidx"]]
    for k in rel_src:
        v = E[k] if k in E else D["X"][:, D["colidx"][k]].astype(float)
        a, m, r = relative(v)
        names += [f"{k}__vmax", f"{k}__vmean", f"{k}__rank"]; cols += [a[:, None], m[:, None], r[:, None]]
    F = np.hstack(cols).astype(np.float32)
    F[~np.isfinite(F)] = np.nan
    return F, names
