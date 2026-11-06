"""Walk-forward: retrain every month, and choose every month's betting rule on the months before it
(4 Nov 2026, founder: "Retrain every months, find a way to be profitable").

    python research/greyhound/topaz_walk.py DIR LABEL      (BETFAIR_DIR as for topaz_theories.py; results only)

THE MODEL is round 3's B2 (the ratings engine, run style and map, dog/trainer/sire/dam windows, vacant boxes, last5,
market history, class, recent form; recent years weighted more; trained on BSP chances), and a twin trained on
winners. For every month from six months before the scored quarter to now, both are refitted on EVERY race before
that month and price that month's races, so no prediction comes from a model that has seen its race or anything
after it. The month's log loss is reported against the SP and BSP (Tests 11-13 priced the same races with a model
frozen at Dec 2023 and lost in the latest months; Test 14 says a fresh model holds).

Since Test 14 the model also carries the ratings upgrades (Test 16) and this race's GRV preview (Test 15), and:
  ISOLYNX_DIR         when set, the Isolynx tracking ratings of each dog's earlier tracked runs (topaz_round6.py)
  RACES_DIR           when set, GRV's tips for this race from the race records (greyhound/races.py, round 8)
  WALK_GRV_RATING=yes GRV's own rating for this race (ONLY once the preview compare shows it unchanged after the race)
  WALK_REFIT_EVERY=k  refit every k months instead of every month (the 181-input model does not fit 36 refits in the
                      job's 350 minutes; between refits the last fitted pair prices the month)
  WALK_ROUNDS_A=n     rounds for the BSP-chance model (3,000 by default; Test 19 found early stopping choosing 4,139
                      once the cap was lifted, at about a third more time a refit)
  WALK_RELIABLE=yes   the reliable-beginner inputs (Test 23: split spread, worst split, missed-start rate, early spread)
  WALK_LEAD=yes       the lead model's chance of leading at the first point (Test 26), FORWARD-CHAINED: each half-year
                      of rows gets its chance from a lead model fitted only on races before that half-year (fixed
                      LEAD_ROUNDS), so neither the win model's training rows nor its priced rows see their own result
  WALK_DRIFT=yes      Betfair's shortest pre-play price, for the drift guard on the bets (Test 25); needs BETFAIR_DIR
  WALK_RULE_ENSEMBLE=yes  the 1.3x rule at GRV's SP a second time, with the ensemble as ours (Test 31)
  WALK_SP_WEIGHT=w    the BSP-chance model's races without a BSP on every runner at weight w (Test 32; default 1)

THE BETS are chosen the same way. For each month from the scored quarter on, the rule (signal: the model, the
ensemble, or Benter's blend of the model with the market; one bet a race or every qualifier; price band; edge) is the
one with the best flat ROI over the PREVIOUS six months of walk-forward predictions, with at least 300 bets there, and
is then applied to the month. Two fixed rules from Tests 12 and 13 ride alongside. At GRV's SP (no commission) and at
BSP (8% on winnings). Flat stakes; drawdown at 0.5% of the bank a bet.

THE GALLOPS VALUE RULE (Test 21) rides alongside too, with its Benter blend refitted each month on the six months
before: a bet when the price is at least 1.3x the blended price, our price $2-$15, Kelly x75 units on the chance halfway
between the blend and the market, cap 4; and, with WALK_DRIFT, the same rule without the dogs that drifted 1.3x or more
from their shortest Betfair price before the off (Test 25's guard, measured to the off).
"""
import os
import sys
import time

import numpy as np
import pandas as pd
import lightgbm as lgb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_preview_test as PT   # noqa: E402
import topaz_round2 as R2    # noqa: E402
import topaz_round3 as R3    # noqa: E402
import topaz_round4 as R4    # noqa: E402
import topaz_theories as T   # noqa: E402
import topaz_v1 as V1        # noqa: E402

ROUNDS_A = int(os.environ.get("WALK_ROUNDS_A", "3000") or 3000)   # Tests 10 and 11 chose the 3,000 cap; Test 19 chose 4,139 at 6,000
ROUNDS_B = 400                                                      # what early stopping chose for the winners twin (385)
EDGES = [0.02, 0.05, 0.10, 0.20, 0.30, 0.50]
TIME_GUARD_MIN = 285
LEAD_ROUNDS = 300                          # what early stopping chose for the lead model in Test 26 (186-409 by fold)
DRIFT_CAP = 1.3
MIN_TRAIN_RACES = 1500                    # stop refitting past this and report what there is (the job dies at 350)


def fit_fixed(X, y, race, weight, rounds):
    groups = race.groupby(race.values, sort=False).size().values
    starts = np.r_[0, np.cumsum(groups)[:-1]]
    w = np.asarray(weight, dtype=float)

    def obj(preds, data):
        yy = data.get_label()
        e = np.exp(preds - np.repeat(np.maximum.reduceat(preds, starts), groups))
        p = e / np.repeat(np.add.reduceat(e, starts), groups)
        return w * (p - yy), w * np.maximum(p * (1 - p), 1e-6)
    params = dict(R2.SMALL, objective=obj, metric="None", verbose=-1, seed=1)
    return lgb.train(params, lgb.Dataset(X, y, categorical_feature=V1.CAT, free_raw_data=False), num_boost_round=rounds)


def build(d, keep_unresulted=False):
    df = V1.build(d, keep_unresulted=keep_unresulted)
    for src, dst in (("rating", "topaz_rating"), ("totalFormCount", "total_form"), ("careerPrizeMoney", "career_prize"),
                     ("prizeMoney", "prize"), ("last5", "last5")):
        if dst not in df and src in df:
            df[dst] = df[src]
    df, f2 = T.V2.add_map(df)
    df = df.reset_index(drop=True)
    df, f3 = T.t3(df)
    df, f4 = T.t4(df)
    df, f5, _ = T.t5(df, df.columns)
    df, f6 = T.t6(df)
    df, bsp_note = T.add_bsp(df)
    df = df.sort_values(["date", "race_id", "box"]).reset_index(drop=True)
    df["p_mkt"] = df.p_bsp.fillna(df.p_sp) if "p_bsp" in df else df.p_sp
    df, fnew, _ = R3.new_features(df)
    df = df.copy()
    num = list(dict.fromkeys(V1.NUM + f2 + f3 + f4 + f5 + f6 + fnew))
    rel = V1.REL + [f for f in ["style_early", "style_led_rate", "style_gain", "dog_place_91D", "dog_won_91D",
                                "trainer_id_won_91D", "box_vacancy_ratio", "last5_mean", "mkt_lsp_mean5",
                                "mkt_prev_lsp", "time_rating_mean5_trk", "time_rating_ewm", "split_rating_ewm",
                                "class_step"] if f in num]
    return df, num, rel, bsp_note


def build_full(d, keep_unresulted=False):
    """build() plus this race's preview, and the Isolynx ratings and GRV's rating when switched on (see the docstring)."""
    df, num, rel, bsp_note = build(d, keep_unresulted=keep_unresulted)
    if "is_best_bet" not in df and "isBestBet" in df:
        df["is_best_bet"] = df.isBestBet
    df, fpv, _ = PT.preview_features(df)
    notes = [bsp_note, f"preview: {len(fpv)} inputs"]
    iso_dir = os.environ.get("ISOLYNX_DIR", "")
    fiso = []
    if iso_dir and os.path.isdir(iso_dir):
        import topaz_round6 as R6      # here, not at the top: topaz_round6 imports this module
        df, fiso, iso_note = R6.isolynx_features(df, iso_dir)
        notes.append(iso_note)
    ftip = []
    races_dir = os.environ.get("RACES_DIR", "")
    if races_dir and os.path.isdir(races_dir):
        from greyhound.races import load_races, tip_features
        races = load_races(races_dir)
        df, ftip = tip_features(df, races)
        notes.append(f"tips: {len(races):,} race records, a tips record for {df.tip_rank.notna().mean():.0%} of runners")
    fgrv = []
    if os.environ.get("WALK_GRV_RATING", "").strip().lower() == "yes":
        if "topaz_rating" in df and df.topaz_rating.notna().mean() > 0.5:
            df["grv_rating"] = df.topaz_rating.astype(float)
            fgrv = ["grv_rating"]
            notes.append("GRV's rating IN (valid only if the preview compare cleared it)")
        else:
            notes.append("GRV's rating asked for but not filled; left out")
    frel, frel_rel = [], []
    if os.environ.get("WALK_RELIABLE", "").strip().lower() == "yes":
        import topaz_round11 as R11    # here: it imports this module
        df = R11.reliable_features(df)
        frel, frel_rel = list(R11.RELIABLE), ["split_sd10", "missed_rate10"]
        notes.append("reliable-beginner inputs IN (Test 23)")
    df = df.copy()
    num = list(dict.fromkeys(num + fpv + fiso + ftip + fgrv + frel))
    rel = rel + [f for f in fiso if f.endswith("_m3")] + fgrv + frel_rel
    if os.environ.get("WALK_LEAD", "").strip().lower() == "yes":
        saved = os.environ.get("WALK_LEAD_MODEL", "").strip()
        if saved:
            # the nightly price run: a lead model saved by the weekly train, or no lead chance at all (never 27 fits a
            # night); the weekly train itself never sets this, so its training rows are always forward-chained
            if os.path.exists(saved):
                df = lead_from_saved(df, num, rel, saved)
                num, rel = num + ["p_lead", "lead_rank"], rel + ["p_lead"]
                notes.append(f"lead chance IN from the saved lead model ({saved})")
            else:
                notes.append(f"lead chance asked for but no saved lead model at {saved}; left out")
        else:
            df, n_fits = lead_forward(df, num, rel)
            num, rel = num + ["p_lead", "lead_rank"], rel + ["p_lead"]
            notes.append(f"lead chance IN (Test 26): forward-chained by half-year, {n_fits} lead fits of {LEAD_ROUNDS} rounds")
    if os.environ.get("WALK_DRIFT", "").strip().lower() == "yes":
        import topaz_round12 as R12
        import topaz_round13 as R13
        R12.EXTRA[:] = [R13.MIN, R13.MAX]
        df, have = R12.add_betfair_extra(df)
        if R13.MIN in have:
            df = R13.drift_columns(df)
            notes.append(f"drift IN (Test 25): filled on {df.drift[df.p_bsp.notna()].notna().mean():.0%} of BSP runners")
        else:
            notes.append("drift asked for but Betfair's files carry no pre-play min price; left out")
    return df, num, rel, "\n".join(notes)


def label_weight(df) -> np.ndarray:
    """Row weights for the BSP-chance model's label (Test 32): races without a BSP on every runner, whose label is
    GRV's SP chance in whole or part, at WALK_SP_WEIGHT (1 = as before, the default)."""
    w = float(os.environ.get("WALK_SP_WEIGHT", "1") or 1)
    if w == 1.0 or "p_bsp" not in df:
        return np.ones(len(df))
    full = df.p_bsp.notna().groupby(df.race_id.values).transform("all").values
    return np.where(full, 1.0, w)


def lead_inputs(num, rel):
    """The inputs the lead model is fitted on: the win model's, without the lead chance itself."""
    return [c for c in num if c not in ("p_lead", "lead_rank")], [c for c in rel if c != "p_lead"]


def fit_lead_all(df, num, rel, rounds=None):
    """One lead model on every one-leader race (the weekly train's, saved for the nightly price run); (booster, cols)."""
    import topaz_round14 as R14
    if "led" not in df:
        df = R14.lead_label(df)
    n, r = lead_inputs(num, rel)
    X = T.features(df, n, r)
    m = df.one_leader.values & df.led.notna().values
    today = df.date.max()
    rec = 0.5 ** ((((today - df.date[m]).dt.days) / 365.25).values / 3.0)
    bst = fit_fixed(X[m], df.led.values[m].astype(float), df.race_id[m], rec, rounds or LEAD_ROUNDS)
    return bst, list(X.columns)


def lead_from_saved(df, num, rel, path):
    """p_lead and lead_rank for every row from a saved lead model (path, with its input list at path + '.json')."""
    import json
    bst = lgb.Booster(model_file=path)
    cols = json.load(open(path + ".json"))["cols"]
    n, r = lead_inputs(num, rel)
    X = T.features(df, n, r).reindex(columns=cols)
    for c in V1.CAT:
        if c in X:
            X[c] = X[c].astype("category")
    df["p_lead"] = V1.race_softmax(bst.predict(X, raw_score=True), df.race_id.values)
    df["lead_rank"] = df.p_lead.groupby(df.race_id.values).rank(ascending=False, method="min")
    return df


def lead_forward(df, num, rel, fit=None, rounds=None):
    """p_lead and lead_rank for every row, each half-year from a lead model fitted only on the one-leader races before
    that half-year began; rows with nothing before them stay NaN. Returns (df, number of fits)."""
    import topaz_round14 as R14        # here: it imports this module
    fit = fit or fit_fixed
    rounds = rounds or LEAD_ROUNDS
    df = R14.lead_label(df)
    X = T.features(df, num, rel)
    df["p_lead"] = np.nan
    halves = df.date.dt.year * 2 + (df.date.dt.month > 6)
    fits = 0
    for hv in sorted(halves.unique()):
        cur = (halves == hv).values
        start = df.date[cur].min()
        tr = ((df.date < start) & df.one_leader).values
        if df.race_id[tr].nunique() < MIN_TRAIN_RACES:
            continue
        rec = 0.5 ** ((((start - df.date[tr]).dt.days) / 365.25).values / 3.0)
        bst = fit(X[tr], df.led.values[tr].astype(float), df.race_id[tr], rec, rounds)
        df.loc[cur, "p_lead"] = V1.race_softmax(bst.predict(X[cur], raw_score=True), df.race_id.values[cur])
        fits += 1
    df["lead_rank"] = df.p_lead.groupby(df.race_id.values).rank(ascending=False, method="min")
    return df, fits


def walk(df, num, rel, first_pred, t0, every=1, fit=None):
    """Out-of-sample p_a (BSP-chance model) and p_b (winners model) for every race from first_pred on.

    `every`: refit every that many months; in between, the pair fitted at the last refit prices the month (still on
    nothing at or after the month, because the last refit saw only races before ITS month). `fit` is fit_fixed, or a
    test's stand-in with the same signature."""
    fit = fit or fit_fixed
    df["p_a"], df["p_b"] = np.nan, np.nan
    months = pd.period_range(first_pred, df.date.max().to_period("M"), freq="M")
    X_all = T.features(df, num, rel)
    log, ba, bb, fitted = [], None, None, None
    for M in months:
        start, end = M.start_time, (M + 1).start_time
        pr = ((df.date >= start) & (df.date < end)).values
        if pr.sum() == 0:
            continue
        due = ba is None or (M - fitted).n >= every
        if due and (time.monotonic() - t0) / 60 > TIME_GUARD_MIN:
            log.append((str(M), "skipped: time guard"))
            break
        if due:
            tr = (df.date < start).values
            race_tr = df.race_id[tr]
            if race_tr.nunique() < MIN_TRAIN_RACES:
                log.append((str(M), f"skipped: only {race_tr.nunique():,} races before it"))
                continue
            rec = 0.5 ** ((((start - df.date[tr]).dt.days) / 365.25).values / 3.0)
            ba = fit(X_all[tr], df.p_mkt.values[tr].astype(float), race_tr, rec * label_weight(df[tr]), ROUNDS_A)
            bb = fit(X_all[tr], df.won.values[tr].astype(float), race_tr, rec, ROUNDS_B)
            fitted = M
            log.append((str(M), f"{df.race_id[pr].nunique():,} races, fit on {race_tr.nunique():,}, "
                                f"{(time.monotonic() - t0) / 60:.0f} min in"))
        else:
            log.append((str(M), f"{df.race_id[pr].nunique():,} races, priced by the {fitted} fit"))
        df.loc[pr, "p_a"] = V1.race_softmax(ba.predict(X_all[pr], raw_score=True), df.race_id.values[pr])
        df.loc[pr, "p_b"] = V1.race_softmax(bb.predict(X_all[pr], raw_score=True), df.race_id.values[pr])
    return df, log


def month_table(df, first_bet):
    print("\n## Walk-forward log loss by month (every race priced by a model refitted before that month)\n")
    print("| month | races | model | ensemble | GRV SP | BSP (races matched) | model gap to SP | gap to BSP |")
    print("|---|---|---|---|---|---|---|---|")
    d = df[df.p_a.notna()]
    tot = []
    for M, g in d.groupby(d.date.dt.to_period("M")):
        hb = g.p_bsp.notna().values
        la, le = V1.ll(g.p_a, g.won), V1.ll(g.p_ens, g.won)
        ls = V1.ll(g.p_sp, g.won)
        lb = V1.ll(g.p_bsp.values[hb], g.won.values[hb]) if hb.any() else np.nan
        lab = V1.ll(g.p_a.values[hb], g.won.values[hb]) if hb.any() else np.nan
        print(f"| {M} | {g.race_id.nunique():,} | {la:.4f} | {le:.4f} | {ls:.4f} | {lb:.4f} ({g[hb].race_id.nunique():,}) "
              f"| {la - ls:+.4f} | {lab - lb:+.4f} |")
        if M >= first_bet:
            tot.append(g)
    s = pd.concat(tot)
    hb = s.p_bsp.notna().values
    print(f"\nScored quarter as a whole ({s.race_id.nunique():,} races): model {V1.ll(s.p_a, s.won):.4f}, ensemble "
          f"{V1.ll(s.p_ens, s.won):.4f}, SP {V1.ll(s.p_sp, s.won):.4f}; on the {s[hb].race_id.nunique():,} BSP-matched: "
          f"model {V1.ll(s.p_a.values[hb], s.won.values[hb]):.4f}, BSP {V1.ll(s.p_bsp.values[hb], s.won.values[hb]):.4f}, "
          f"gap {V1.ll(s.p_a.values[hb], s.won.values[hb]) - V1.ll(s.p_bsp.values[hb], s.won.values[hb]):+.4f} "
          f"(Test 11's frozen model: +0.1267)")


def sequential_bets(df, first_bet, price_col, p_mkt_col, comm, title):
    """Each month's rule chosen on the previous 6 months of walk-forward predictions; the month then bet."""
    d = df[df.p_a.notna() & df[price_col].notna() & (df[price_col] > 1)].copy()
    months = [M for M in pd.period_range(first_bet, d.date.max().to_period("M"), freq="M")]
    print(f"\n## {title}\n")
    print("| month | rule chosen on the 6 months before (bets, ROI there) | bets | winners | A/E | flat ROI | "
          "cumulative units |")
    print("|---|---|---|---|---|---|---|")
    picks, cum = [], 0.0
    fixed = {"Test 12 rule: all, $8-$13, 50%": ("model", False, (8, 13), 0.50),
             "Test 13 rule: one a race, $5-$8, 50%": ("model", True, (5, 8), 0.50)}
    fixed_bets = {k: [] for k in fixed}
    for M in months:
        W = d[(d.date >= (M - 6).start_time) & (d.date < M.start_time)]
        cur = d[(d.date >= M.start_time) & (d.date < (M + 1).start_time)]
        if len(W) < 1000 or len(cur) == 0:
            continue
        # signals for the window and the month, every weight fitted on the window only
        we, _ = V1.blend(["p_a", "p_b"], W)
        wb, _ = V1.blend(["p_a", p_mkt_col], W)
        sig_W = {"model": W.p_a.values, "ensemble": V1.blend(["p_a", "p_b"], W, we)[1],
                 "blend": V1.blend(["p_a", p_mkt_col], W, wb)[1]}
        sig_M = {"model": cur.p_a.values, "ensemble": V1.blend(["p_a", "p_b"], cur, we)[1],
                 "blend": V1.blend(["p_a", p_mkt_col], cur, wb)[1]}
        cands = []
        for sname, pW in sig_W.items():
            for one in (False, True):
                for band in R4.BANDS:
                    for e in EDGES:
                        m, o = R4.selections(W, pW, W[price_col].values, comm, e, band, one)
                        r = R4.result(W, m, o, pW, 0, W[price_col].values)
                        if r["n"] >= 300:
                            cands.append((r["roi"], sname, one, band, e, r["n"]))
        if not cands:
            print(f"| {M} | no rule had 300 bets | | | | | |")
            continue
        cands.sort(reverse=True)
        roi_w, sname, one, band, e, n_w = cands[0]
        m, o = R4.selections(cur, sig_M[sname], cur[price_col].values, comm, e, band, one)
        r = R4.result(cur, m, o, sig_M[sname], 0, cur[price_col].values)
        if r["n"]:
            cum += r["roi"] * r["n"]
            picks.append(cur[m].assign(ret=np.where(cur.won.values[m] == 1, o[m] - 1, -1)))
        rule = f"{sname}, {'one a race' if one else 'all'}, ${band[0]:g}-${band[1]:g}, {e:.0%} ({n_w:,}, {roi_w:+.0%})"
        print(f"| {M} | {rule} | {r['n']:,} | {r.get('w', 0):,} | {r.get('ae', float('nan')):.3f} | "
              f"{r.get('roi', float('nan')):+.1%} | {cum:+,.0f} |")
        for k, (sn, one_f, band_f, e_f) in fixed.items():
            m, o = R4.selections(cur, sig_M[sn], cur[price_col].values, comm, e_f, band_f, one_f)
            if m.any():
                fixed_bets[k].append(cur[m].assign(ret=np.where(cur.won.values[m] == 1, o[m] - 1, -1),
                                                   p=sig_M[sn][m]))
    if not picks:
        print("\nno bets")
        return
    allb = pd.concat(picks).sort_values("date")
    summarise("Sequential rule", allb, price_col)
    for k, v in fixed_bets.items():
        if v:
            summarise(k, pd.concat(v).sort_values("date"), price_col)


def summarise(name, b, price_col):
    mid = b.date.quantile(0.5)
    out = []
    for hn, hm in (("1st half", b.date < mid), ("2nd half", b.date >= mid), ("all", b.date.notna())):
        x = b[hm]
        ae = x.won.sum() / (1 / x[price_col]).sum()
        bank, peak, dd, run, worst = 1.0, 1.0, 0.0, 0, 0
        for r in x.ret.values:
            bank *= 1 + 0.005 * r
            peak, dd = max(peak, bank), max(dd, 1 - bank / peak)
            run = run + 1 if r < 0 else 0
            worst = max(worst, run)
        out.append(f"{hn}: {len(x):,} bets, A/E {ae:.3f}, flat ROI {x.ret.mean():+.1%}, bank x{bank:.2f} at 0.5% a bet, "
                   f"worst drawdown {dd:.0%}, longest losing run {worst}")
    bym = b.groupby(b.date.dt.to_period("M")).ret.agg(["size", "mean"])
    print(f"\n**{name}**\n- " + "\n- ".join(out))
    print(f"- months in profit {(bym['mean'] > 0).sum()} of {len(bym)}; last 6: " +
          ", ".join(f"{p} {r['mean']:+.0%} ({int(r['size'])})" for p, r in bym.tail(6).iterrows()))


def main(d, label):
    t0 = time.monotonic()
    df, num, rel, note = build_full(d)
    every = max(1, int(os.environ.get("WALK_REFIT_EVERY", "1") or 1))
    q75 = df.date.quantile(0.75)
    first_bet = q75.to_period("M")
    first_pred = first_bet - 6
    print(f"# {label}: walk-forward\n\n{note}\nrefit every {every} month(s) from {first_pred} (bets from {first_bet}); "
          f"inputs {len(num)} plus {len(rel)} within-race relatives; {ROUNDS_A} rounds on BSP chances and {ROUNDS_B} on "
          f"winners, recent years weighted more (half-life 3 years)\n")
    df, log = walk(df, num, rel, first_pred, t0, every)
    print("Refits: " + "; ".join(f"{m}: {s}" for m, s in log))
    df = df[df.p_a.notna()].copy()
    # a fixed-weight ensemble for the log-loss table (weights from the first six predicted months)
    W0 = df[df.date < first_bet.start_time]
    we, _ = V1.blend(["p_a", "p_b"], W0)
    df["p_ens"] = V1.blend(["p_a", "p_b"], df, we)[1]
    month_table(df, first_bet)
    sequential_bets(df, first_bet, "start_price", "p_sp", 0.0, "Bets at GRV's SP, no commission")
    if "bsp" in df:
        sequential_bets(df, first_bet, "bsp", "p_bsp", 0.08, "Bets at BSP, 8% commission on winnings")
    horse_rule(df, first_bet, "start_price", "p_sp", 0.0, "The 1.3x rule at GRV's SP, no commission")
    if os.environ.get("WALK_RULE_ENSEMBLE", "").strip().lower() == "yes":
        # Test 31: the same rule with the ensemble (the model and its winners twin) as ours
        horse_rule(df, first_bet, "start_price", "p_sp", 0.0,
                   "The 1.3x rule at GRV's SP on the ensemble (the model and its winners twin), no commission", sig="p_ens")
    if "bsp" in df:
        horse_rule(df, first_bet, "bsp", "p_bsp", 0.08, "The 1.3x rule at BSP, 8% commission on winnings")


def horse_rule(df, first_bet, price_col, p_mkt_col, comm, title, sig="p_a"):
    """Test 21's rule month by month, the Benter blend of `sig` (ours: the model p_a, or the ensemble p_ens) with the
    market refitted on the six months before each month; with the drift guard (Test 25) beside it when the drift column
    is there."""
    import topaz_round9 as R9           # here: it imports this module
    d = df[df[sig].notna() & df[p_mkt_col].notna() & df[price_col].notna() & (df[price_col] > 1)]
    months = pd.period_range(first_bet, d.date.max().to_period("M"), freq="M")
    rows = {"no guard": [], f"drift guard {DRIFT_CAP:g}x": []} if "drift" in d else {"no guard": []}
    weights = []
    for M in months:
        W = d[(d.date >= (M - 6).start_time) & (d.date < M.start_time)]
        cur = d[(d.date >= M.start_time) & (d.date < (M + 1).start_time)]
        if len(W) < 1000 or len(cur) == 0:
            continue
        wb, _ = V1.blend([sig, p_mkt_col], W)
        weights.append(wb)
        pb = V1.blend([sig, p_mkt_col], cur, wb)[1]
        price = cur[price_col].astype(float).values
        m, o, u = R9.horse_bets(cur, pb, cur[p_mkt_col].values, price, comm, 1.3, (2, 15))
        for name in rows:
            mm = m & ~(cur.drift >= DRIFT_CAP).values if name != "no guard" else m
            if mm.any():
                rows[name].append(cur[mm].assign(ret=np.where(cur.won.values[mm] == 1, o[mm] - 1, -1.0), units=u[mm],
                                                  odds=o[mm]))
    w = np.array(weights)
    print(f"\n## {title}\n\nBlend weights (ours, market) refitted each month: ours {w[:, 0].min():.2f} to {w[:, 0].max():.2f}, "
          f"market {w[:, 1].min():.2f} to {w[:, 1].max():.2f}\n" if len(w) else f"\n## {title}\n\nno months to bet\n")
    print("| rule | half | bets | winners | A/E | flat ROI | units staked | Kelly ROI | units won | worst drawdown (units) | "
          "months in profit |\n|---|---|---|---|---|---|---|---|---|---|---|")
    for name, parts in rows.items():
        if not parts:
            print(f"| {name} | all | 0 | | | | | | | | |")
            continue
        b = pd.concat(parts).sort_values("date")
        mid = b.date.quantile(0.5)
        for hn, hm in (("1st", b.date < mid), ("2nd", b.date >= mid), ("all", b.date.notna())):
            x = b[hm]
            kret = x.units * x.ret
            cum = np.r_[0, np.cumsum(kret.values)]
            dd = float((np.maximum.accumulate(cum) - cum).max())
            bym = kret.groupby(x.date.dt.to_period("M")).sum()
            ae = x.won.sum() / (1 / x[price_col]).sum()
            print(f"| {name} | {hn} | {len(x):,} | {int(x.won.sum()):,} | {ae:.3f} | {x.ret.mean():+.1%} | {x.units.sum():,.0f} | "
                  f"{kret.sum() / x.units.sum():+.1%} | {kret.sum():+,.0f} | {dd:,.0f} | {(bym > 0).sum()} of {len(bym)} |")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz walk-forward")
