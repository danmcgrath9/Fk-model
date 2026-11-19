"""Test 10: does Racing Queensland's sectional speed lift the form price? (19 Nov 2026)

    python research/harness/bw_sect.py BETFAIR_DIR BETWATCH_DIR LABEL      (RQ files from $RQ_DIR, default rq-cache)

The live model (bw_live.py: Betwatch-only pure form) with and without each horse's sectional record from Racing
Queensland's files (rq_join.py: last-half, last-quarter, first-half and lead-time speed, top speed, each against the
race, ground covered beyond the shortest route, position at the quarters; earlier runs only). Same splits as bw_live
(train to 30 Jun 2025, validation Jul-Dec 2025, holdout 2026), scored on the QUEENSLAND races of 2026 (the only ones
RQ times). Stage 2 with TAB's first price is fitted on Queensland validation races for both, so they compare fairly.
Counts and scores only: no horse, time or price is printed (RQ: personal use; Betwatch: own use).
"""
import os, sys
from datetime import date
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hx_model import fit, winner_ll
from bw_data import load_betwatch
from bw_live import frame, stage2_fit, apply2, FEATS, CATS, TRAIN_END, VALID_END, TEST_START
from rq_join import load_dir, run_features, horse_history, norm_track, norm_name, SEC_FEATS

EDGES = (0.05, 0.10, 0.20)
VS = ["sec_ewm_v_last_half_rel", "sec_ewm_v_lead_rel", "sec_ewm_v_last_half", "sec_best5_v_last_half",
      "sec_ewm_top_speed", "sec_ewm_q1_pos"]


def bets(h, col, title):
    print(f"\n### {title}: back at TAB's first price where chance x price clears the edge\n")
    print("| edge | half | bets | winners | ROI at TAB first | TAB price shortened after | ROI at TAB last |\n"
          "|---|---|---|---|---|---|---|")
    for e in EDGES:
        for half, s in h.groupby("half"):
            b = s[(s[col] * s.tab_open >= 1 + e) & (s.tab_last > 1)]
            if not len(b):
                print(f"| {e:.0%} | {half} | 0 | | | | |"); continue
            print(f"| {e:.0%} | {half} | {len(b):,} | {int(b.won.sum())} | "
                  f"{np.where(b.won == 1, b.tab_open - 1, -1.0).mean():+.1%} | {(b.tab_last < b.tab_open).mean():.0%} | "
                  f"{np.where(b.won == 1, b.tab_last - 1, -1.0).mean():+.1%} |")


def main(_bf, bw_dir, label):
    df = frame(load_betwatch(bw_dir), date(2100, 1, 1))
    runs = run_features(load_dir(os.environ.get("RQ_DIR", "rq-cache")))
    hist = horse_history(runs)
    print(f"# {label}: Test 10, Racing Queensland sectionals in the form price\n")
    print(f"RQ: {len(runs):,} runner rows in {runs.groupby(['date', 'track', 'race_number']).ngroups:,} races, "
          f"{runs.date.min():%Y-%m-%d} to {runs.date.max():%Y-%m-%d}; speeds read on "
          f"{runs.v_last_half.notna().mean():.0%} (last half), {runs.v_lead.notna().mean():.0%} (lead time), "
          f"{runs.top_speed.notna().mean():.0%} (top speed) of rows")
    df["k_track"], df["k_name"] = df.TRACK.astype(str).map(norm_track), df.horse_name.map(norm_name)
    df["race_number"] = pd.to_numeric(df.race_number, errors="coerce").astype(float)
    hist = hist.rename(columns={"track": "k_track", "name": "k_name", "date": "k_date"}).drop_duplicates(
        ["k_date", "k_track", "race_number", "k_name"])
    df["k_date"] = df.date
    df = df.merge(hist, on=["k_date", "k_track", "race_number", "k_name"], how="left")
    rq_tracks = set(hist.k_track)
    span = (df.date >= runs.date.min()) & (df.date <= runs.date.max()) & df.k_track.isin(rq_tracks)
    j = df[span]
    print(f"- Betwatch runners at RQ's tracks inside RQ's dates: {len(j):,}; joined to an RQ row {j.sec_runs.notna().mean():.1%}; "
          f"RQ winner = Betwatch winner on {((j['rank'] == 1) == (j.won == 1))[j['rank'].notna() & j.res].mean():.1%} "
          f"of joined runners; RQ TAB number = Betwatch number on {(j.tab == j.TAB_NUMBER)[j.tab.notna()].mean():.1%}")
    for c in VS:
        x = df[c].astype(float)
        df[f"{c}_vs_race"] = x - x.groupby(df.race).transform("mean")
        df[f"{c}_rank"] = x.groupby(df.race).rank(ascending=(c == "sec_ewm_q1_pos"), method="min")
    sect = FEATS + SEC_FEATS + [f"{c}_vs_race" for c in VS] + [f"{c}_rank" for c in VS]

    past = df[df.res]
    g = past.groupby("race")
    past = past[(g.won.transform("sum") == 1) & (past.field >= 4) & g.p_tab_open.transform(lambda s: s.notna().all())
                & (past.date >= "2023-01-01")].copy()
    past["qld"] = past.groupby("race").sec_runs.transform(lambda s: s.notna().any()) & past.k_track.isin(rq_tracks)
    tr, va = past[past.date < TRAIN_END], past[(past.date >= TRAIN_END) & (past.date < VALID_END)]
    te = past[past.date >= TEST_START]
    print(f"- races: train {tr.race.nunique():,} (Queensland with sectionals {tr[tr.qld].race.nunique():,}), "
          f"validation {va.race.nunique():,} ({va[va.qld].race.nunique():,}), 2026 {te.race.nunique():,} "
          f"({te[te.qld].race.nunique():,}); Queensland 2026 runners with at least one earlier sectional run "
          f"{(te[te.qld].sec_runs > 0).mean():.0%}\n")
    out = {}
    for name, feats in (("form", FEATS), ("form + sectionals", sect)):
        v_, t_, m, _ = fit(tr, va, te, feats, CATS)
        vq = v_[v_.qld]
        a, b = stage2_fit(vq)
        t_ = t_[t_.qld].copy()
        t_["p_s2"] = apply2(t_, a, b)
        out[name] = (t_, a, b, m, feats)
        print(f"{name}: stage 2 on Queensland validation: {a:.2f} log(form) + {b:.2f} log(TAB first)")
    base, a0, b0, _, _ = out["form"]
    sec, a1, b1, m1, f1 = out["form + sectionals"]
    h = base[["race", "horse_bw", "date", "won", "field", "tab_open", "tab_last", "p_tab_open", "p_model", "p_s2"]]
    h = h.rename(columns={"p_model": "p_form", "p_s2": "p_s2_form"}).reset_index(drop=True)
    h["p_sect"], h["p_s2_sect"] = sec.p_model.to_numpy(), sec.p_s2.to_numpy()
    h["p_equal"] = 1 / h.field
    inv = (1 / h.tab_last).where(h.tab_last > 1)
    h["p_tab_last"] = (inv / inv.groupby(h.race).transform("sum")).where(inv.notna().groupby(h.race).transform("all"))
    dates = np.sort(h.date.unique()); cut = dates[len(dates) // 2]
    h["half"] = np.where(h.date < cut, "1st half", "2nd half")
    print(f"\n## Queensland 2026 ({h.race.nunique():,} races), split at {pd.Timestamp(cut):%Y-%m-%d}\n")
    print("| price | LL 1st half | LL 2nd half | beats TAB first? |\n|---|---|---|---|")
    tab = [winner_ll(h[h.half == x].p_tab_open, h[h.half == x].won, h[h.half == x].race) for x in ("1st half", "2nd half")]
    for n, c in (("equal chances", "p_equal"), ("form", "p_form"), ("form + sectionals", "p_sect"),
                 ("TAB first price", "p_tab_open"), ("stage 2: form + TAB first", "p_s2_form"),
                 ("stage 2: form + sectionals + TAB first", "p_s2_sect"), ("TAB last price", "p_tab_last")):
        s = h[h.groupby("race")[c].transform(lambda x: x.notna().all())]
        r = [winner_ll(s[s.half == x][c], s[s.half == x].won, s[s.half == x].race) for x in ("1st half", "2nd half")]
        beat = "" if c == "p_tab_open" else ("yes, both halves" if r[0] < tab[0] and r[1] < tab[1] else
                                            "one half" if r[0] < tab[0] or r[1] < tab[1] else "no")
        print(f"| {n} | {r[0]:.4f} | {r[1]:.4f} | {beat} |")
    imp = pd.Series(m1.booster_.feature_importance("gain"), index=f1 + CATS).sort_values(ascending=False)
    print("\n## form + sectionals: tree inputs by gain (top 20; sectional inputs start sec_)\n")
    for k, v in (imp / imp.sum()).head(20).items():
        print(f"- {k}: {v:.1%}")
    print(f"\nsectional inputs' share of all gain: {(imp[[i for i in imp.index if i.startswith('sec_')]].sum() / imp.sum()):.1%}")
    bets(h, "p_s2_form", "Stage 2 without sectionals (Queensland 2026)")
    bets(h, "p_s2_sect", "Stage 2 with sectionals (Queensland 2026)")


if __name__ == "__main__":
    main(*sys.argv[1:4])
