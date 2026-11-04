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
  WALK_GRV_RATING=yes GRV's own rating for this race (ONLY once the preview compare shows it unchanged after the race)
  WALK_REFIT_EVERY=k  refit every k months instead of every month (the 181-input model does not fit 36 refits in the
                      job's 350 minutes; between refits the last fitted pair prices the month)

THE BETS are chosen the same way. For each month from the scored quarter on, the rule (signal: the model, the
ensemble, or Benter's blend of the model with the market; one bet a race or every qualifier; price band; edge) is the
one with the best flat ROI over the PREVIOUS six months of walk-forward predictions, with at least 300 bets there, and
is then applied to the month. Two fixed rules from Tests 12 and 13 ride alongside. At GRV's SP (no commission) and at
BSP (8% on winnings). Flat stakes; drawdown at 0.5% of the bank a bet.
"""
import os
import sys
import time

import numpy as np
import pandas as pd
import lightgbm as lgb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import topaz_preview_test as PT   # noqa: E402
import topaz_round2 as R2    # noqa: E402
import topaz_round3 as R3    # noqa: E402
import topaz_round4 as R4    # noqa: E402
import topaz_theories as T   # noqa: E402
import topaz_v1 as V1        # noqa: E402

ROUNDS_A, ROUNDS_B = 3000, 400          # what early stopping chose in Tests 10 and 11 (the cap, and 385)
EDGES = [0.02, 0.05, 0.10, 0.20, 0.30, 0.50]
TIME_GUARD_MIN = 285
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


def build(d):
    df = V1.build(d)
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


def build_full(d):
    """build() plus this race's preview, and the Isolynx ratings and GRV's rating when switched on (see the docstring)."""
    df, num, rel, bsp_note = build(d)
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
    fgrv = []
    if os.environ.get("WALK_GRV_RATING", "").strip().lower() == "yes":
        if "topaz_rating" in df and df.topaz_rating.notna().mean() > 0.5:
            df["grv_rating"] = df.topaz_rating.astype(float)
            fgrv = ["grv_rating"]
            notes.append("GRV's rating IN (valid only if the preview compare cleared it)")
        else:
            notes.append("GRV's rating asked for but not filled; left out")
    df = df.copy()
    num = list(dict.fromkeys(num + fpv + fiso + fgrv))
    rel = rel + [f for f in fiso if f.endswith("_m3")] + fgrv
    return df, num, rel, "\n".join(notes)


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
            ba = fit(X_all[tr], df.p_mkt.values[tr].astype(float), race_tr, rec, ROUNDS_A)
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


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz walk-forward")
