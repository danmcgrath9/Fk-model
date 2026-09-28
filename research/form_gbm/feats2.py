import numpy as np, bench as b, feats
import warnings; warnings.filterwarnings("ignore")

def extra():
    D = b.D; P = D["P"].astype(float); f = {n: i for i, n in enumerate(D["past_fields"])}; c = D["colidx"]
    ri = D["race_idx"]; X = D["X"]
    col = lambda n: P[:, :, f[n]].copy(); trial = col("trial") == 1
    race = lambda n: np.where(trial, np.nan, col(n))
    out = {}
    # race context, same for every runner in the race (trees use it to switch behaviour)
    out["c_field"] = D["field"][ri].astype(float); out["c_dist"] = D["distance"][ri]; out["c_lws"] = D["lws"][ri]
    out["c_going"] = D["going"][ri]
    mon = np.array([int(d[5:7]) for d in D["date"]]); out["c_month"] = mon[ri].astype(float)
    out["c_prize"] = np.log1p(X[:, c["raw_prize_log"]]) if "raw_prize_log" in c else np.nan
    trk = {t: i for i, t in enumerate(sorted(set(D["track"])))}; out["c_track"] = np.array([trk[t] for t in D["track"]])[ri].astype(float)
    starts = X[:, c["f_careerForm_s"]]
    out["c_maiden_field"] = np.bincount(ri, weights=np.nan_to_num(X[:, c["f_careerForm_w"]]) == 0, minlength=D["n_races"])[ri] / D["field"][ri]
    R = race("rating"); fs = race("field_strength"); prize = race("prize")
    out["x_class_change"] = D["lws"][ri] - feats.recency(fs)
    out["x_prize_change"] = np.log1p(np.nan_to_num(X[:, c["averagePrizeMoney"]])) - np.log1p(feats.nanfirst(prize))
    w_today = X[:, c["weight"]]; w_past = race("weight")
    out["x_rat_wadj_last"] = feats.nanfirst(R) + (feats.nanfirst(w_past) - w_today) * 1.5
    out["x_rat_wadj_max5"] = feats.firstk(R + (w_past - w_today[:, None]) * 1.5, 5, np.nanmax)
    days = race("days_before")
    gaps = np.diff(np.concatenate([np.zeros((len(days), 1)), days], 1), axis=1)  # gap before each run (newest first: days_i - days_{i-1})
    first_up_run = np.zeros_like(days, dtype=bool)
    older = np.concatenate([days[:, 1:], np.full((len(days), 1), np.nan)], 1)
    first_up_run = (older - days) >= 60
    out["x_rat_firstup_max"] = np.nanmax(np.where(first_up_run, R, np.nan), 1)
    out["x_n_firstup"] = first_up_run.sum(1)
    today_gap = feats.nanfirst(days)
    out["x_is_firstup"] = (today_gap >= 60).astype(float)
    # runs this campaign: consecutive runs from newest with gaps < 60
    camp = np.zeros(len(days))
    for i in range(len(days)):
        if not (today_gap[i] < 60): continue
        k = 1
        for j in range(1, 10):
            if np.isnan(days[i, j]) or days[i, j] - days[i, j - 1] >= 60: break
            k += 1
        camp[i] = k
    out["x_runs_this_prep"] = camp
    best = feats.firstk(R, 10, np.nanmax)
    out["x_consist"] = feats.firstk(np.where(np.isnan(R), np.nan, (R >= best[:, None] - 3).astype(float)), 10, np.nanmean)
    fin, run = race("finish"), race("runners")
    share = (fin - 1) / np.maximum(run - 1, 1)
    out["x_fin_share_mean3"] = feats.firstk(share, 3, np.nanmean); out["x_top3_last3"] = feats.firstk(np.where(np.isnan(fin), np.nan, (fin <= 3) * 1.0), 3, np.nanmean)
    bsp = race("bsp"); lp = 1 / bsp  # implied chance in past race
    out["x_pastp_rw"] = feats.recency(lp); out["x_pastp_max5"] = feats.firstk(lp, 5, np.nanmax)
    # ran to its price: finish share vs price rank proxy
    out["x_beat_price_share"] = feats.recency(np.where(np.isnan(lp) | np.isnan(share), np.nan, (1 - share) - lp * run))
    out["x_days_best"] = np.take_along_axis(days, np.nan_to_num(np.nanargmax(np.where(np.isnan(R), -1e9, R), 1)).astype(int)[:, None], 1)[:, 0]
    out["x_trial_last_fin"] = feats.nanfirst(np.where(trial, col("finish"), np.nan))
    out["x_trial_last_margin"] = feats.nanfirst(np.where(trial, col("margin"), np.nan))
    sp = race("sp"); out["x_sp_bsp_ratio_rw"] = feats.recency(np.log(sp / bsp))   # bookmaker vs exchange view
    return out

def build():
    F, names = np.load("F2.npy"), open("F2_names.txt").read().split("\n")
    E = extra(); cols = [F]; nm = list(names)
    for k, v in E.items():
        v = np.asarray(v, float); cols.append(v[:, None]); nm.append(k)
        if k.startswith("x_") and k not in ("x_is_firstup", "x_n_firstup", "x_runs_this_prep"):
            a, m, r = feats.relative(v); cols += [a[:, None], m[:, None], r[:, None]]; nm += [f"{k}__vmax", f"{k}__vmean", f"{k}__rank"]
    F3 = np.hstack(cols).astype(np.float32); F3[~np.isfinite(F3)] = np.nan
    return F3, nm
