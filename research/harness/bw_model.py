"""Harness model with Betwatch's driver, trainer, barrier, class and TAB prices, scored against BSP (18 Nov 2026).

    python research/harness/bw_model.py BETFAIR_DIR BETWATCH_DIR LABEL

Prints counts and scores only: Betwatch data is for our own use and is never printed, committed or uploaded.

Races: Australian, every starter with a BSP, one winner, field of 4+, from 2023-01-01 (two months of driver and
trainer history first), and every starter joined to Betwatch. Train to 2025-06-30, validation (early stopping, blend
weights, the stage-2 fit) 2025-07-01 to 2025-12-31, holdout 2026-01-01 on, scored in two date halves.

Prices compared on the same holdout races (those where every runner has a TAB first price):
- v3: the market-history model of Tests 3 and 6 (Betfair only), refitted on these races;
- v3 + people: v3 plus driver, trainer, driver x trainer, driver at the track, driver change, barrier, class, track
  condition; still no price from the race being scored, so it is a form price;
- v3 + people + TAB open: the same plus TAB's first price as an input, the price you could have in the morning;
- stage 2 (Benter): log p = a log(v3 + people) + b log(TAB open), a and b fitted on validation;
- TAB open, TAB last (before the start), pre-play WAP, BSP.
Then paper bets on the holdout: back at TAB's first price where the price's chance x that price clears a margin, and
back at BSP (8% commission on winnings) where the form price's chance x BSP clears one. Each table shows the result
without the group's 10 biggest wins, because a few long winners carry most small samples.
"""
import os, sys
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hx_data import load, history, FEATURES_V3, CATS, renorm
from hx_model import fit, winner_ll, kl_to_bsp
from bw_data import load_betwatch, join, add_people, PEOPLE, PEOPLE_CATS

START, TRAIN_END, VALID_END = "2023-01-01", "2025-07-01", "2026-01-01"
COMMISSION = 0.08


BARRIER = ["barrier", "barrier_rel", "bar_ae", "bar_runs"]


def leak_check(df):
    """Counts only. Test 8's first run beat BSP, so before any score is believed: does Betwatch's barrier (or any
    input) carry the result? A barrier that matches the finishing position, or a win rate by barrier far steeper than
    by TAB number, would mean it does."""
    j = df[df.bw_race.notna()]
    print("\n## Leak check (counts only)\n")
    print(f"- barrier = TAB number on {(j.barrier == j.TAB_NUMBER).mean():.1%} of joined runners; barrier = Betwatch "
          f"finishing position on {(j.barrier == j.bw_pos).mean():.1%}; winners with barrier 1: "
          f"{((j.won == 1) & (j.barrier == 1)).sum() / max((j.won == 1).sum(), 1):.1%}")
    print(f"- rank correlation with the finishing position: barrier {j.barrier.corr(j.bw_pos, method='spearman'):.3f}, "
          f"TAB number {j.TAB_NUMBER.corr(j.bw_pos, method='spearman'):.3f}")
    print("\n| value | runners with this barrier | win rate | runners with this TAB number | win rate |\n|---|---|---|---|---|")
    for v in range(1, 13):
        b, t = j[j.barrier == v], j[j.TAB_NUMBER == v]
        print(f"| {v} | {len(b):,} | {b.won.mean() if len(b) else float('nan'):.1%} | {len(t):,} | "
              f"{t.won.mean() if len(t) else float('nan'):.1%} |")
    print(f"| other | {(~j.barrier.between(1, 12)).sum():,} | | | |")
    o = df[df.bw_race.notna()].sort_values(["start", "race"])
    d = o.groupby(["TRACK", "trot", "barrier"], sort=False).start.transform(lambda s: s.diff().dt.total_seconds())
    print(f"- bar_ae rows whose previous same-key race started at the same time as this one: {(d == 0).mean():.2%}")


def stage2(va, ho, base, mkt):
    """Benter's second stage: weights on log(model) and log(market), fitted on validation log loss."""
    grid = np.arange(0, 1.51, 0.05)
    best = min(((a, b) for a in grid for b in grid if a + b > 0), key=lambda ab: winner_ll(
        renorm(np.exp(ab[0] * np.log(va[base]) + ab[1] * np.log(va[mkt])), va.race), va.won, va.race))
    for part in (va, ho):
        part["p_stage2"] = renorm(np.exp(best[0] * np.log(part[base]) + best[1] * np.log(part[mkt])), part.race)
    return best


def roi_table(h, title, chance, price, comm, cuts):
    print(f"\n### {title}\n")
    print("| edge at least | half | bets | winners | staked | profit | ROI | ROI without the 10 biggest wins |\n"
          "|---|---|---|---|---|---|---|---|")
    for e in cuts:
        for half, s in h.groupby("half"):
            b = s[(s[chance] * s[price] >= 1 + e) & (s[price] > 1)]
            ret = np.where(b.won == 1, (b[price] - 1) * (1 - comm), -1.0)
            if len(b) == 0:
                print(f"| {e:.0%} | {half} | 0 | | | | | |"); continue
            trim = np.sort(ret)[:-10].mean() if len(ret) > 50 else float("nan")   # as Test 4: those bets dropped
            print(f"| {e:.0%} | {half} | {len(b):,} | {int(b.won.sum()):,} | {len(b):,} | {ret.sum():+,.1f} | "
                  f"{ret.sum() / len(b):+.1%} | {trim:+.1%} |")


def main(bf_dir, bw_dir, label):
    bw = load_betwatch(bw_dir)
    print(f"# {label}: Betwatch + Betfair harness model v BSP\n")
    print(f"Betwatch month files: {bw.attrs['months']}; not complete: {', '.join(bw.attrs['incomplete']) or 'none'}; "
          f"dates {bw.bw_date.min()} to {bw.bw_date.max()}\n")
    df, c = join(history(load(bf_dir)), bw)
    print("## The join\n")
    print(f"- Betwatch: {c['bw_races']:,} races, {c['bw_runners']:,} runners not scratched; races with a Betfair win "
          f"market id {c['bw_races_mapped']:,} ({c['bw_races_mapped'] / max(c['bw_races'], 1):.1%}); runners with a "
          f"Betfair selection id {c['bw_runners_with_bf_id']:,}; races whose results could be read "
          f"{c['bw_races_with_results']:,}")
    print(f"- Betfair, Australian, inside Betwatch's dates: {c['bf_au_races_in_span']:,} races, "
          f"{c['bf_au_runners_in_span']:,} runners; joined {c['bf_au_races_joined']:,} races "
          f"({c['bf_au_races_joined'] / max(c['bf_au_races_in_span'], 1):.1%}), {c['bf_au_runners_joined']:,} runners "
          f"({c['bf_au_runners_joined'] / max(c['bf_au_runners_in_span'], 1):.1%})")
    print(f"- Betfair winners also first in Betwatch's results: {c['winner_agree']:,} of {c['winner_checks']:,}; "
          f"Betwatch runner number = Betfair TAB number on {c['tab_number_agree']:.1%} of joined runners")

    df = add_people(df)
    df = df[(df.STATE_CODE != "NZ") & (df.date >= START)]
    g = df.groupby("race")
    ok = (g.WIN_BSP.transform(lambda s: (s > 1).all()) & (g.won.transform("sum") == 1) & (df.field >= 4)
          & g.bw_race.transform(lambda s: s.notna().all()))
    df = df[ok].copy()
    print(f"- model races (every starter joined): {df.race.nunique():,}; runners with a driver "
          f"{df.driver.notna().mean():.1%}, a trainer {df.trainer.notna().mean():.1%}, a barrier "
          f"{df.barrier.notna().mean():.1%}, a class {df['class'].notna().mean():.1%}, a track condition "
          f"{df.track_condition.notna().mean():.1%}; races with a TAB first price on every runner "
          f"{df.groupby('race').p_tab_open.apply(lambda s: s.notna().all()).mean():.1%}")
    df["log_tab_open"] = np.log(df.p_tab_open)
    for col in CATS + PEOPLE_CATS:
        df[col] = df[col].astype("category")
    tr = df[df.date < TRAIN_END]; va = df[(df.date >= TRAIN_END) & (df.date < VALID_END)]; ho = df[df.date >= VALID_END]
    print(f"\nraces: train {tr.race.nunique():,} ({START} to {TRAIN_END}), validation {va.race.nunique():,}, holdout "
          f"{ho.race.nunique():,} ({ho.date.min():%Y-%m-%d} to {ho.date.max():%Y-%m-%d})\n")

    leak_check(df)
    people = FEATURES_V3 + PEOPLE
    va1, ho1, _, _ = fit(tr, va, ho, FEATURES_V3)
    va2, ho2, m2, _ = fit(tr, va, ho, people, CATS + PEOPLE_CATS)
    no_bar = [f for f in people if f not in BARRIER]
    _, ho2b, m2b, _ = fit(tr, va, ho, no_bar, CATS + PEOPLE_CATS)
    has = lambda d: d[d.groupby("race").p_tab_open.transform(lambda s: s.notna().all())]
    va3, ho3, m3, _ = fit(has(tr), has(va), has(ho), people + ["log_tab_open", "tab_open_hours"], CATS + PEOPLE_CATS)

    keyc = ["race", "horse"]
    h = ho3[keyc + ["date", "won", "field", "p_bsp", "p_wap", "p_tab_open", "p_tab_last", "WIN_BSP", "tab_open",
                    "p_model"]].rename(columns={"p_model": "p_open_model"})
    h = h.merge(ho1[keyc + ["p_model"]].rename(columns={"p_model": "p_v3"}), on=keyc)
    h = h.merge(ho2[keyc + ["p_model"]].rename(columns={"p_model": "p_people"}), on=keyc)
    h = h.merge(ho2b[keyc + ["p_model"]].rename(columns={"p_model": "p_people_nobar"}), on=keyc)
    v = va3[keyc + ["won", "p_tab_open"]].merge(va2[keyc + ["p_model"]].rename(columns={"p_model": "p_people"}), on=keyc)
    a, b = stage2(v, h, "p_people", "p_tab_open")
    print(f"stage 2 on validation: log p = {a:.2f} log(v3 + people) + {b:.2f} log(TAB open)")
    h["p_equal"] = 1 / h.field
    h["p_wap"] = h.p_wap.where(h.p_wap.notna().groupby(h.race).transform("all"))
    dates = np.sort(h.date.unique()); cut = dates[len(dates) // 2]
    h["half"] = np.where(h.date < cut, "1st half", "2nd half")

    print(f"\n## Holdout, races with a TAB first price on every runner ({h.race.nunique():,}), split at "
          f"{pd.Timestamp(cut):%Y-%m-%d}\n")
    print("| price | LL 1st half | LL 2nd half | KL to BSP 1st half | KL 2nd half | share of the equal-to-BSP gap "
          "closed |\n|---|---|---|---|---|---|")
    le, lb = winner_ll(h.p_equal, h.won, h.race), winner_ll(h.p_bsp, h.won, h.race)
    for name, col in (("equal chances", "p_equal"), ("v3 (market history)", "p_v3"), ("v3 + people", "p_people"),
                      ("v3 + people, no barrier inputs", "p_people_nobar"),
                      ("v3 + people + TAB open", "p_open_model"), ("stage 2", "p_stage2"), ("TAB open", "p_tab_open"),
                      ("TAB last", "p_tab_last"), ("pre-play WAP", "p_wap"), ("BSP", "p_bsp")):
        s = h[h.groupby("race")[col].transform(lambda x: x.notna().all())]
        r = [winner_ll(s[s.half == x][col], s[s.half == x].won, s[s.half == x].race) for x in ("1st half", "2nd half")]
        k = [kl_to_bsp(s[s.half == x][col], s[s.half == x].p_bsp, s[s.half == x].race) for x in ("1st half", "2nd half")]
        lm = winner_ll(s[col], s.won, s.race)
        note = "" if len(s) == len(h) else f" ({s.race.nunique():,} races)"
        print(f"| {name}{note} | {r[0]:.4f} | {r[1]:.4f} | {k[0]:.4f} | {k[1]:.4f} | {(le - lm) / (le - lb):.1%} |")

    for name, m, X in (("v3 + people", m2, people + CATS + PEOPLE_CATS),
                       ("v3 + people, no barrier inputs", m2b, no_bar + CATS + PEOPLE_CATS),
                       ("v3 + people + TAB open", m3, people + ["log_tab_open", "tab_open_hours"] + CATS + PEOPLE_CATS)):
        imp = pd.Series(m.booster_.feature_importance("gain"), index=X).sort_values(ascending=False)
        print(f"\n## {name}: tree inputs by gain (top 15)\n")
        for k_, val in (imp / imp.sum()).head(15).items():
            print(f"- {k_}: {val:.1%}")

    print("\n## Paper bets on the holdout (no money staked)\n")
    print("TAB's first price is the first Betwatch recorded, which may not be the true open, and TAB limits winning "
          "accounts, so the TAB tables are an upper bound on what could be got.")
    h["tab_open_price"] = h.tab_open
    roi_table(h, "Back at TAB's first price: stage-2 chance x TAB first price", "p_stage2", "tab_open_price", 0,
              (0.05, 0.10, 0.20))
    roi_table(h, "Back at TAB's first price: v3 + people + TAB open chance x TAB first price", "p_open_model",
              "tab_open_price", 0, (0.05, 0.10, 0.20))
    roi_table(h, "Back at BSP: v3 + people (form only) chance x BSP, 8% commission", "p_people", "WIN_BSP",
              COMMISSION, (0.10, 0.20, 0.40))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "harness")
