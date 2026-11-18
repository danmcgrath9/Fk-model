"""Test 9: can a form price beat TAB's first price without any TAB price, and does adding TAB's price then win?
(18 Nov 2026, founder: "I want to create a model that beats tab without its prices and then if we price tab in can we
win".)

    python research/harness/bw_form.py BETFAIR_DIR BETWATCH_DIR LABEL

Counts and scores only (Betwatch data is for our own use: nothing per runner is printed, committed or uploaded).

Same races and splits as Test 8 (bw_model.py), restricted to races where every runner has a TAB first price, so every
price is scored on the same races. Prices:
- people (Test 8): market history + driver, trainer, class, condition;
- form+: people + each horse's Betwatch record (finishing positions in every Betwatch race, its rating at PAST TAB
  prices and how those moved), stable and driver form over the last 60 days, class and handicap change, and every key
  rating against the race (minus the race mean, and rank);
- pure form: form+ with every input built from any price removed (past BSP, past TAB, in-running prices, and records
  measured against a price): the strictest reading of "without its prices";
- stage 2 (Benter) for form+ and for pure form: log p = a log(form price) + b log(TAB first price), fitted on validation.
The form prices never see a price from the race being priced. TAB's first price is the first Betwatch recorded that
day: usually near the open, not guaranteed to be it.
"""
import os, re, sys
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hx_data import load, history, FEATURES_V3, CATS
from hx_model import fit, winner_ll, kl_to_bsp
from bw_data import load_betwatch, add_bw_history, join, add_people, add_form_plus, PEOPLE, PEOPLE_CATS, FORM_PLUS
from bw_model import START, TRAIN_END, VALID_END, COMMISSION, stage2, roi_table

# driver_up is built from driver_resid (a record against BSP) and class_move from rivals_mr (BSP ratings)
PRICE_BUILT = re.compile(r"p_last|p_mean|ae|inplay|close|bsp|vol|mr|perf|p_place|resid|move|driver_up")


def pure(feats):
    """Inputs not built from any price (past BSP, past TAB, in-running, or a record measured against a price)."""
    return [f for f in feats if not PRICE_BUILT.search(f)]


def band_table(h, chance, edge):
    print(f"\n### Back at TAB's first price where {chance} x price >= {1 + edge:.2f}, by TAB first price\n")
    print("| TAB first price | half | bets | winners | ROI | ROI without the 10 biggest wins | A/E (winners / chances) |\n"
          "|---|---|---|---|---|---|---|")
    bands = [(1, 3), (3, 5), (5, 10), (10, 20), (20, 1e9)]
    for lo, hi in bands:
        for half, s in h.groupby("half"):
            b = s[(s[chance] * s.tab_open >= 1 + edge) & (s.tab_open > lo) & (s.tab_open <= hi)]
            if not len(b):
                print(f"| ${lo:g} to {'' if hi > 1e8 else f'${hi:g}'} | {half} | 0 | | | | |"); continue
            ret = np.where(b.won == 1, b.tab_open - 1, -1.0)
            trim = np.sort(ret)[:-10].mean() if len(ret) > 50 else float("nan")
            print(f"| ${lo:g} to {'' if hi > 1e8 else f'${hi:g}'} | {half} | {len(b):,} | {int(b.won.sum()):,} | "
                  f"{ret.mean():+.1%} | {trim:+.1%} | {b.won.sum() / b[chance].sum():.2f} |")


def clv_table(h, chance, edges):
    """Closing-line value of the bets backed at TAB's first price: did the market come to them? Results swing on a few
    long winners; whether TAB's price SHORTENED after the bet does not, so it is the steadier read of a real edge.
    CLV = mean log(TAB first / TAB last before the start): positive = we got a bigger price than TAB ended at. Then the
    same bets at TAB's last price and at BSP (8% commission), and wins against BSP's chances (A/E)."""
    print(f"\n### Closing-line value: {chance} bets at TAB's first price\n")
    print("| edge at least | half | bets | TAB price shortened after the bet | drifted | mean CLV (log first / last) | "
          "ROI at TAB first | ROI at TAB last | ROI at BSP, 8% commission | A/E against BSP |\n"
          "|---|---|---|---|---|---|---|---|---|---|")
    for e in edges:
        for half, s in h.groupby("half"):
            b = s[(s[chance] * s.tab_open >= 1 + e) & (s.tab_open > 1) & (s.tab_last > 1)]
            if not len(b):
                continue
            clv = np.log(b.tab_open / b.tab_last)
            r_open = np.where(b.won == 1, b.tab_open - 1, -1.0).mean()
            r_last = np.where(b.won == 1, b.tab_last - 1, -1.0).mean()
            r_bsp = np.where(b.won == 1, (b.WIN_BSP - 1) * (1 - COMMISSION), -1.0).mean()
            print(f"| {e:.0%} | {half} | {len(b):,} | {(b.tab_last < b.tab_open).mean():.0%} | "
                  f"{(b.tab_last > b.tab_open).mean():.0%} | {clv.mean():+.3f} | {r_open:+.1%} | {r_last:+.1%} | "
                  f"{r_bsp:+.1%} | {b.won.sum() / b.p_bsp.sum():.2f} |")
    s = h[(h.tab_open > 1) & (h.tab_last > 1)]
    print(f"| every runner (baseline) | both | {len(s):,} | {(s.tab_last < s.tab_open).mean():.0%} | "
          f"{(s.tab_last > s.tab_open).mean():.0%} | {np.log(s.tab_open / s.tab_last).mean():+.3f} | "
          f"{np.where(s.won == 1, s.tab_open - 1, -1.0).mean():+.1%} | "
          f"{np.where(s.won == 1, s.tab_last - 1, -1.0).mean():+.1%} | "
          f"{np.where(s.won == 1, (s.WIN_BSP - 1) * (1 - COMMISSION), -1.0).mean():+.1%} | "
          f"{s.won.sum() / s.p_bsp.sum():.2f} |")


def main(bf_dir, bw_dir, label):
    bw = add_bw_history(load_betwatch(bw_dir))
    df, _ = join(history(load(bf_dir)), bw)
    df = add_form_plus(add_people(df))
    df = df[(df.STATE_CODE != "NZ") & (df.date >= START)]
    g = df.groupby("race")
    ok = (g.WIN_BSP.transform(lambda s: (s > 1).all()) & (g.won.transform("sum") == 1) & (df.field >= 4)
          & g.bw_race.transform(lambda s: s.notna().all()) & g.p_tab_open.transform(lambda s: s.notna().all()))
    df = df[ok].copy()
    for col in CATS + PEOPLE_CATS:
        df[col] = df[col].astype("category")
    tr = df[df.date < TRAIN_END]; va = df[(df.date >= TRAIN_END) & (df.date < VALID_END)]; ho = df[df.date >= VALID_END]
    people = FEATURES_V3 + PEOPLE
    plus = people + FORM_PLUS
    pf = pure(plus)
    print(f"# {label}: Test 9, a form price against TAB's first price\n")
    print(f"races (every runner joined and TAB-priced): train {tr.race.nunique():,}, validation {va.race.nunique():,}, "
          f"holdout {ho.race.nunique():,} ({ho.date.min():%Y-%m-%d} to {ho.date.max():%Y-%m-%d}); runners with a "
          f"Betwatch history (at least one earlier Betwatch run) {(df.bwh_runs > 0).mean():.1%}\n")
    print(f"inputs: people {len(people)}, form+ {len(plus)}, pure form {len(pf)} (no input built from any price)\n")

    keyc = ["race", "horse"]
    fits = {}
    for name, feats in (("people", people), ("form+", plus), ("pure form", pf)):
        va_, ho_, m, _ = fit(tr, va, ho, feats, CATS + PEOPLE_CATS)
        fits[name] = (va_, ho_, m, feats)
    h = fits["form+"][1][keyc + ["date", "won", "field", "p_bsp", "p_tab_open", "p_tab_last", "tab_open", "tab_last",
                                 "WIN_BSP"]]
    v = fits["form+"][0][keyc + ["won", "p_tab_open"]]
    for name, col in (("people", "p_people"), ("form+", "p_plus"), ("pure form", "p_pure")):
        h = h.merge(fits[name][1][keyc + ["p_model"]].rename(columns={"p_model": col}), on=keyc)
        v = v.merge(fits[name][0][keyc + ["p_model"]].rename(columns={"p_model": col}), on=keyc)
    a, b = stage2(v, h, "p_plus", "p_tab_open"); h["p_s2_plus"] = h.pop("p_stage2"); v["p_s2_plus"] = v.pop("p_stage2")
    a2, b2 = stage2(v, h, "p_pure", "p_tab_open"); h["p_s2_pure"] = h.pop("p_stage2")
    print(f"\nstage 2 on validation: log p = {a:.2f} log(form+) + {b:.2f} log(TAB first); "
          f"pure form: {a2:.2f} log(pure form) + {b2:.2f} log(TAB first)")
    h["p_equal"] = 1 / h.field
    dates = np.sort(h.date.unique()); cut = dates[len(dates) // 2]
    h["half"] = np.where(h.date < cut, "1st half", "2nd half")

    print(f"\n## Holdout ({h.race.nunique():,} races), split at {pd.Timestamp(cut):%Y-%m-%d}\n")
    print("| price | LL 1st half | LL 2nd half | KL to BSP 1st half | KL 2nd half | gap to BSP closed | beats TAB first "
          "price on log loss? |\n|---|---|---|---|---|---|---|")
    le, lb = winner_ll(h.p_equal, h.won, h.race), winner_ll(h.p_bsp, h.won, h.race)
    tab = [winner_ll(h[h.half == x].p_tab_open, h[h.half == x].won, h[h.half == x].race) for x in ("1st half", "2nd half")]
    for name, col in (("equal chances", "p_equal"), ("people (Test 8)", "p_people"), ("form+", "p_plus"),
                      ("pure form (no input built from any price)", "p_pure"), ("TAB first price", "p_tab_open"),
                      ("stage 2: form+ with TAB first", "p_s2_plus"), ("stage 2: pure form with TAB first", "p_s2_pure"),
                      ("TAB last price", "p_tab_last"), ("BSP", "p_bsp")):
        s = h[h.groupby("race")[col].transform(lambda x: x.notna().all())]
        r = [winner_ll(s[s.half == x][col], s[s.half == x].won, s[s.half == x].race) for x in ("1st half", "2nd half")]
        k = [kl_to_bsp(s[s.half == x][col], s[s.half == x].p_bsp, s[s.half == x].race) for x in ("1st half", "2nd half")]
        lm = winner_ll(s[col], s.won, s.race)
        beat = "" if col == "p_tab_open" else ("yes, both halves" if r[0] < tab[0] and r[1] < tab[1] else
                                              "one half" if r[0] < tab[0] or r[1] < tab[1] else "no")
        print(f"| {name} | {r[0]:.4f} | {r[1]:.4f} | {k[0]:.4f} | {k[1]:.4f} | {(le - lm) / (le - lb):.1%} | {beat} |")

    for name in ("form+", "pure form"):
        _, _, m, feats = fits[name]
        X = feats + CATS + PEOPLE_CATS
        imp = pd.Series(m.booster_.feature_importance("gain"), index=X).sort_values(ascending=False)
        print(f"\n## {name}: tree inputs by gain (top 20)\n")
        for k_, val in (imp / imp.sum()).head(20).items():
            print(f"- {k_}: {val:.1%}")

    print("\n## Paper bets at TAB's first price on the holdout (no money staked, no commission)\n")
    print("TAB's first price here is the first Betwatch recorded (not guaranteed to be the open), at a bookmaker that "
          "limits winning accounts: an upper bound on what could be got.")
    for col, title in (("p_s2_plus", "stage 2, form+ with TAB first"), ("p_s2_pure", "stage 2, pure form with TAB first"),
                       ("p_plus", "form+ alone")):
        roi_table(h, f"Back at TAB's first price: {title} chance x price", col, "tab_open", 0, (0.05, 0.10, 0.20, 0.40))
    band_table(h, "p_s2_plus", 0.10)
    clv_table(h, "p_s2_plus", (0.05, 0.10, 0.20))
    clv_table(h, "p_s2_pure", (0.05, 0.10, 0.20))
    roi_table(h, "Back at BSP: form+ chance x BSP, 8% commission", "p_plus", "WIN_BSP", COMMISSION, (0.10, 0.20, 0.40))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "harness")
