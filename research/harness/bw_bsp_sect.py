"""Test 11: with sectionals, how close is the price to BSP, and does it profit at TAB's first price? (19 Nov 2026,
founder: "we also want to get close to BSP and make a profit on tabs opening price".)

    python research/harness/bw_bsp_sect.py BETFAIR_DIR BETWATCH_DIR LABEL      (RQ files from $RQ_DIR, default rq-cache)

Test 9's Betfair-joined form+ (market history, driver, trainer, class, Betwatch record, race-relative ratings) with
and without Racing Queensland's sectional records (rq_join.attach), scored on the QUEENSLAND races of 2026 against BSP:
winner log loss, KL to BSP and the share of the equal-to-BSP gap closed, for the form price alone, stage 2 with TAB's
first price (fitted on Queensland validation), TAB's first and last price, WAP and BSP. Then paper bets at TAB's first
price (and the same bets at BSP after 8% commission) by edge and half. Counts and scores only.
"""
import os, sys
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hx_data import load, history, FEATURES_V3, CATS
from hx_model import fit, winner_ll, kl_to_bsp
from bw_data import load_betwatch, add_bw_history, join, add_people, add_form_plus, PEOPLE, PEOPLE_CATS, FORM_PLUS
from bw_model import START, TRAIN_END, VALID_END, COMMISSION, stage2
from rq_join import load_dir, run_features, attach, add_vs, SECT_ALL


def main(bf_dir, bw_dir, label):
    bw = add_bw_history(load_betwatch(bw_dir))
    df, _ = join(history(load(bf_dir)), bw)
    df = add_form_plus(add_people(df))
    df["today"] = False
    df = add_vs(attach(df, run_features(load_dir(os.environ.get("RQ_DIR", "rq-cache")))))
    df = df[(df.STATE_CODE != "NZ") & (df.date >= START)]
    g = df.groupby("race")
    ok = (g.WIN_BSP.transform(lambda s: (s > 1).all()) & (g.won.transform("sum") == 1) & (df.field >= 4)
          & g.bw_race.transform(lambda s: s.notna().all()) & g.p_tab_open.transform(lambda s: s.notna().all()))
    df = df[ok].copy()
    df["qld"] = df.rq_track & df.groupby("race").sec_runs.transform(lambda s: s.notna().any())
    for col in CATS + PEOPLE_CATS:
        df[col] = df[col].astype("category")
    if os.environ.get("QLD_ONLY"):
        df = df[df.qld].copy()                  # train, validate and score on Queensland races with sectionals only
        label += " (trained on Queensland races only)"
    tr = df[df.date < TRAIN_END]; va = df[(df.date >= TRAIN_END) & (df.date < VALID_END)]; ho = df[df.date >= VALID_END]
    plus = FEATURES_V3 + PEOPLE + FORM_PLUS
    print(f"# {label}: Test 11, sectionals against BSP and TAB's first price (Queensland)\n")
    print(f"races: train {tr.race.nunique():,} (Queensland with sectionals {tr[tr.qld].race.nunique():,}), validation "
          f"{va.race.nunique():,} ({va[va.qld].race.nunique():,}), 2026 {ho.race.nunique():,} "
          f"({ho[ho.qld].race.nunique():,})\n")
    keyc = ["race", "horse"]
    res = {}
    for name, feats in (("form+", plus), ("form+ + sectionals", plus + SECT_ALL)):
        v_, h_, m, _ = fit(tr, va, ho, feats, CATS + PEOPLE_CATS)
        v_, h_ = v_[v_.qld].copy(), h_[h_.qld].copy()
        a, b = stage2(v_, h_, "p_model", "p_tab_open")
        res[name] = (h_, a, b)
        print(f"{name}: stage 2 on Queensland validation: {a:.2f} log(form) + {b:.2f} log(TAB first)")
    h0, _, _ = res["form+"]
    h1, _, _ = res["form+ + sectionals"]
    h = h0[keyc + ["date", "won", "field", "p_bsp", "p_wap", "p_tab_open", "p_tab_last", "tab_open", "tab_last",
                   "WIN_BSP", "p_model", "p_stage2"]].rename(columns={"p_model": "p_plus", "p_stage2": "p_s2_plus"})
    h = h.merge(h1[keyc + ["p_model", "p_stage2"]].rename(columns={"p_model": "p_sect", "p_stage2": "p_s2_sect"}),
                on=keyc)
    h["p_equal"] = 1 / h.field
    h["p_wap"] = h.p_wap.where(h.p_wap.notna().groupby(h.race).transform("all"))
    dates = np.sort(h.date.unique()); cut = dates[len(dates) // 2]
    h["half"] = np.where(h.date < cut, "1st half", "2nd half")
    print(f"\n## Queensland 2026 ({h.race.nunique():,} races), split at {pd.Timestamp(cut):%Y-%m-%d}\n")
    print("| price | LL 1st half | LL 2nd half | KL to BSP 1st half | KL 2nd half | gap to BSP closed |\n"
          "|---|---|---|---|---|---|")
    le, lb = winner_ll(h.p_equal, h.won, h.race), winner_ll(h.p_bsp, h.won, h.race)
    for n, c in (("equal chances", "p_equal"), ("form+", "p_plus"), ("form+ + sectionals", "p_sect"),
                 ("TAB first price", "p_tab_open"), ("stage 2: form+ with TAB first", "p_s2_plus"),
                 ("stage 2: form+ + sectionals with TAB first", "p_s2_sect"), ("TAB last price", "p_tab_last"),
                 ("pre-play WAP", "p_wap"), ("BSP", "p_bsp")):
        s = h[h.groupby("race")[c].transform(lambda x: x.notna().all())]
        r = [winner_ll(s[s.half == x][c], s[s.half == x].won, s[s.half == x].race) for x in ("1st half", "2nd half")]
        k = [kl_to_bsp(s[s.half == x][c], s[s.half == x].p_bsp, s[s.half == x].race) for x in ("1st half", "2nd half")]
        lm = winner_ll(s[c], s.won, s.race)
        print(f"| {n} | {r[0]:.4f} | {r[1]:.4f} | {k[0]:.4f} | {k[1]:.4f} | {(le - lm) / (le - lb):.1%} |")
    for col, title in (("p_s2_plus", "stage 2 without sectionals"), ("p_s2_sect", "stage 2 with sectionals")):
        print(f"\n### Paper bets at TAB's first price, {title} (Queensland 2026)\n")
        print("| edge | half | bets | winners | ROI at TAB first | shortened after | ROI at TAB last | "
              "ROI at BSP, 8% comm. | A/E v BSP |\n|---|---|---|---|---|---|---|---|---|")
        for e in (0.05, 0.10, 0.20):
            for half, s in h.groupby("half"):
                b = s[(s[col] * s.tab_open >= 1 + e) & (s.tab_last > 1)]
                if not len(b):
                    continue
                print(f"| {e:.0%} | {half} | {len(b):,} | {int(b.won.sum())} | "
                      f"{np.where(b.won == 1, b.tab_open - 1, -1.0).mean():+.1%} | {(b.tab_last < b.tab_open).mean():.0%} | "
                      f"{np.where(b.won == 1, b.tab_last - 1, -1.0).mean():+.1%} | "
                      f"{np.where(b.won == 1, (b.WIN_BSP - 1) * (1 - COMMISSION), -1.0).mean():+.1%} | "
                      f"{b.won.sum() / b.p_bsp.sum():.2f} |")
    print("\n### Back at BSP where the form+ + sectionals price x BSP clears the edge (8% commission)\n")
    print("| edge | half | bets | winners | ROI | A/E v BSP |\n|---|---|---|---|---|---|")
    for e in (0.10, 0.20, 0.40):
        for half, s in h.groupby("half"):
            b = s[s.p_sect * s.WIN_BSP >= 1 + e]
            if len(b):
                print(f"| {e:.0%} | {half} | {len(b):,} | {int(b.won.sum())} | "
                      f"{np.where(b.won == 1, (b.WIN_BSP - 1) * (1 - COMMISSION), -1.0).mean():+.1%} | "
                      f"{b.won.sum() / b.p_bsp.sum():.2f} |")


if __name__ == "__main__":
    main(*sys.argv[1:4])
