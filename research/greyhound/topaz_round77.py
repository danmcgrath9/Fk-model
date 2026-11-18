"""Round 77: the running line, and today's draw against it, in our own price (18 Nov 2026, founder: "Can we get our
open pricing sharper without TAB prices? ... if it draws 1, it can't win today, but was box 6 in that price"; "make
it as complicated as possible")

Our own price (ours with Isolynx, the night before, no TAB price in it) has never seen a dog's running line against
today's box: the one input meant for it (topaz_v2's map_rail_vs_box) reads a column nothing builds, and the stewards'
comments have never been read. topaz_lines.add_lines builds both. This round walks ours with Isolynx again with them
added, the same way and on the same refit dates as the saved walk (WALK_ISO_USE), and, stated before the run, from
February 2025 on:

  - what was found: the stewards' codes, GRV's run-line and jump codes, each run-line code in metres from the rail,
    the tracked rail distances, and the share of runners with a running line
  - the distance to BSP and the winners' log loss on clean races: TAB's first book, ours as saved, ours with the
    lines
  - actual wins against expected for the dogs the lines pick out (a wide runner drawn inside, a railer drawn wide,
    squeezed, crossed, a slow beginner with a clash): against ours as saved, ours with the lines, TAB's first book and
    the corrected BSP
  - the order sheet with no TAB price (round 76's rules: TAB's first price at least 1.1x, 1.2x, 1.3x or 1.5x our fair
    price, $2 to $15, flat; and the 2-point margin at a quarter of Kelly on Test 88's scale), ours as saved against
    ours with the lines, by half
  - the bets by track, for the sheet at 1.2x and for the two models that need TAB's book (Test 88's fit, the corrected
    blend at 1.1x): is Healesville special (founder: "Healsville is the only one we would of had bets for today?")

The new walk is saved to the walk cache under its signature (printed), so later rounds can name it.

    python research/greyhound/topaz_round77.py DIR LABEL    (as round 76; needs ISOLYNX_DIR)

Counts, sums and rates only: no race, dog or price is printed. The model's inputs, the stewards' codes and the tracks
are named.
"""
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_lines as L           # noqa: E402
import topaz_round50 as R50       # noqa: E402
import topaz_round58 as R58       # noqa: E402
import topaz_round62 as R62       # noqa: E402
import topaz_round63 as R63       # noqa: E402
import topaz_round64 as R64       # noqa: E402
import topaz_round67 as R67       # noqa: E402
import topaz_round68 as R68       # noqa: E402
import topaz_round73 as R73       # noqa: E402
import topaz_round76 as R76       # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402

OLD, NEW = "ours as saved", "ours with the lines"
SHEET = (1.1, 1.2, 1.3, 1.5)


def groups(t: pd.DataFrame) -> list:
    """The dogs the lines pick out: (name, mask)."""
    g = lambda c: t[c].values.astype(float) if c in t else np.full(len(t), np.nan)    # noqa: E731
    sc = g("lm_slow_clash")
    hi = np.nanquantile(sc, 0.9) if np.isfinite(sc).any() else np.inf
    return [("a wide runner drawn inside (clash 3 or more)", g("lm_clash") >= 3),
            ("wider than drawn (clash 1 or 2)", (g("lm_clash") >= 1) & (g("lm_clash") < 3)),
            ("drawn about where it runs (clash -0.5 to 0.5)", np.abs(g("lm_clash")) <= 0.5),
            ("a railer drawn wide (clash -3 or less)", g("lm_clash") <= -3),
            ("squeezed by a neighbour (squeeze over 1)", g("lm_squeeze") > 1),
            ("two or more quicker dogs inside run wider (crossers_in 2+)", g("lm_crossers_in") >= 2),
            ("two or more quicker dogs want its lane (contention 2+)", g("lm_contention") >= 2),
            ("a slow beginner with a clash (top tenth of slow_clash)", (sc >= hi) & (sc > 0)),
            ("no running line known", ~np.isfinite(g("line_any")))]


def main(d, label):
    t0 = time.monotonic()
    bdir, iso_dir = os.environ.get("BETWATCH_DIR", ""), os.environ.get("ISOLYNX_DIR", "")
    print(f"# {label}: round 77, the running line, and today's draw against it, in our own price\n")
    if not bdir or not os.path.isdir(bdir) or not iso_dir or not os.path.isdir(iso_dir):
        print("Betwatch (BETWATCH_DIR) and Isolynx (ISOLYNX_DIR) are both needed: nothing to test")
        return 1
    from greyhound.isolynx import table
    orig, memo = R50.base, {}

    def base_lines(dd):
        if "v" not in memo:
            df, num, rel, note = orig(dd)
            df, feats, lnote = L.add_lines(df, table(iso_dir))
            memo["v"] = (df, num, rel, note, feats, lnote)
        df, num, rel, note, _, _ = memo["v"]
        return df.copy(), list(num), list(rel), note

    R50.base = base_lines
    try:
        x, R, _, _ = R62.field(d, t0)
    finally:
        R50.base = orig
    df, num, rel, _, feats, lnote = memo["v"]
    print(f"## 1. What was found\n\n{lnote}\n\nNew inputs: {len(feats)} ({', '.join(feats)}). "
          f"{(time.monotonic() - t0) / 60:.0f} minutes in.\n")

    num2 = list(dict.fromkeys(list(num) + feats))
    first = pd.Period(R50.FIRST, "M")
    use = os.environ.pop("WALK_CACHE_USE", None)
    try:
        b, log = W.walk_cached(df.copy(), num2, rel, first, t0, 6)
        sig = W.walk_signature(df, num2, rel, first, 6)
    finally:
        if use:
            os.environ["WALK_CACHE_USE"] = use
    print("## 2. The walk, ours with Isolynx and the lines\n\n" + "; ".join(f"{m}: {s}" for m, s in log
                                                                         if "priced by" not in s)
          + f"\n\nSaved as walk_{sig} in the walk cache. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")

    k = b[["race_id", "dog", "p_a"]].assign(race_id=b.race_id.astype("int64"), dog=b.dog.astype(str))
    ran = x.is_ran.astype(bool).values
    m = pd.DataFrame({"race_id": x.race_id.values.astype("int64"), "dog": x.dog.values.astype(str)}).merge(
        k.drop_duplicates(["race_id", "dog"]), on=["race_id", "dog"], how="left")
    x["p_new_bet"] = np.where(ran, m.p_a.values * (1 - x.s_later.fillna(0).values), x.p_book.values)
    has88 = R67.read_saved(x, "r70", "c_f")
    hascb = R63.read_corrections(x)
    t = x[ran].reset_index(drop=True)
    t["q_bsp"], _ = R58.corrected_bsp(t)
    tq = t.assign(p_bsp=t.q_bsp)
    since = R63.R36.in_period(t, R63.SINCE, None)
    print(f"Runners that ran at TAB's first price: {len(t):,} in {t.race_id.nunique():,} races; ours with the lines "
          f"for {np.isfinite(t.p_new_bet.values).mean():.0%} of them.\n")

    # 3. Distance to BSP, the runners that ran (R), clean races, February 2025 on
    race, dates = R.race_id.values, R.date.values.astype("datetime64[ns]")
    q, full, _ = R62.bsp_label(R, *R62.LABEL_FIT)
    rk = pd.DataFrame({"race_id": R.race_id.values.astype("int64"), "dog": R.dog.values.astype(str)})
    chance = {}
    for nm, col in ((OLD, "p_i_bet"), (NEW, "p_new_bet")):
        pm = R64.ran_share(t[col].values.astype(float), t.race_id.values)
        kk = pd.DataFrame({"race_id": t.race_id.values.astype("int64"), "dog": t.dog.values.astype(str), "pm": pm})
        chance[nm] = rk.merge(kk.drop_duplicates(["race_id", "dog"]), on=["race_id", "dog"], how="left").pm.values
    tab = R64.ran_share(R.p_book.values, race)
    ok = full.astype(bool) & (R.n_later.fillna(0).values == 0) & (dates >= np.datetime64(R64.SPLIT))
    for v in chance.values():
        ok &= np.isfinite(v)
    won = R.won.values
    tab_d = R64.distance(tab[ok], q[ok], race[ok])
    print(f"## 3. Distance to BSP, Feb 2025 on, clean races ({int(ok.sum()):,} runners in {pd.unique(race[ok]).size:,} "
          "races)\n\n| price | distance to BSP (thousandths) | of TAB's distance closed | winners' log loss |\n"
          "|---|---|---|---|")
    print(f"| TAB's first book | {tab_d:.2f} | | {V1.ll(tab[ok], won[ok]):.4f} |")
    for nm, v in chance.items():
        dd = R64.distance(v[ok], q[ok], race[ok])
        print(f"| {nm} | {dd:.2f} | {1 - dd / tab_d:+.1%} | {V1.ll(v[ok], won[ok]):.4f} |")

    # 4. Actual wins against expected, for the dogs the lines pick out
    po = R64.ran_share(t.p_i_bet.values.astype(float), t.race_id.values)
    pn = R64.ran_share(t.p_new_bet.values.astype(float), t.race_id.values)
    pt = R64.ran_share(t.p_book.values.astype(float), t.race_id.values)
    y = since & t.q_bsp.notna().values & np.isfinite(pn) & np.isfinite(po)
    w = t.won.values.astype(float)
    print("\n## 4. Actual wins against expected, February 2025 on (runners with a corrected BSP)\n\n"
          f"| dogs | runners | wins | win % | A/E vs {OLD} | A/E vs {NEW} | A/E vs TAB's first book | "
          "A/E vs the corrected BSP | SE |\n|---|---|---|---|---|---|---|---|---|")
    for nm, g in groups(t):
        z = y & g
        n = int(z.sum())
        if n < 50:
            print(f"| {nm} | {n:,} | | | | | | | |")
            continue
        wins = w[z].sum()
        print(f"| {nm} | {n:,} | {int(wins):,} | {wins / n:.1%} | {wins / po[z].sum():.3f} | {wins / pn[z].sum():.3f} | "
              f"{wins / pt[z].sum():.3f} | {wins / t.q_bsp.values[z].sum():.3f} | {1 / np.sqrt(max(wins, 1)):.3f} |")

    # 5. The order sheet with no TAB price, ours as saved against ours with the lines
    paid = R68.paid_price(t)
    scale = None
    if has88:
        p88 = R67.model_chance(t, "c_f")
        m88 = R68.margin_bets(t, p88, 0.02)
        raw88 = R73.raw_kelly(p88, paid)
        scale = raw88[m88 & since].mean()
    flat = np.ones(len(t))
    rules = []
    for nm, col in ((OLD, "p_i_bet"), (NEW, "p_new_bet")):
        for r in SHEET:
            rules.append((f"{nm}, {r:g}x, flat", R63.bets(t, col, t.price.values, r)[0], flat))
        if scale:
            p = t[col].values.astype(float)
            u = R73.raw_kelly(p, paid) / scale
            rules.append((f"{nm}, 2 points, quarter Kelly", R68.margin_bets(t, p, 0.02) & (u > 0), u))
    periods = [("Feb 2025 on", R63.SINCE, None)] + R63.HALVES
    print(f"\n## 5. The order sheet with no TAB price, at TAB's first price after its deduction "
          f"({(time.monotonic() - t0) / 60:.0f} minutes in)\n")
    print("| sheet | period | bets | a month | units staked | corrected BSP per unit staked (SE) | corrected BSP units | "
          "realised units | deepest fall, realised | losing months |\n|" + "---|" * 10)
    for nm, mm, u in rules:
        for lab, lo, hi in periods:
            per = R63.R36.in_period(t, lo, hi)
            print(f"| {nm} | {lab} | " + R76.row(t, tq, mm & per, paid, u, R67.months_in(t, per)) + " |")

    # 6. By track
    trk = t.get("track_name", t.get("track", pd.Series("", index=t.index))).fillna("").astype(str).str.upper().values
    by = [(f"{OLD}, 1.2x", R63.bets(t, "p_i_bet", t.price.values, 1.2)[0], flat),
          (f"{NEW}, 1.2x", R63.bets(t, "p_new_bet", t.price.values, 1.2)[0], flat)]
    if has88:
        by.append(("Test 88's fit, 2 points, quarter Kelly", m88 & (raw88 > 0), raw88 / scale))
    if hascb:
        by.append(("the corrected blend, 1.1x, flat", R63.bets(t, "c_q", t.price.values, 1.1)[0], flat))
    names = [b_[0] for b_ in by]
    print("\n## 6. By track, February 2025 on: bets / corrected BSP units / realised units (tracked tracks marked *)\n")
    print("| track | races | " + " | ".join(names) + " |\n|" + "---|" * (len(names) + 2))
    from greyhound.isolynx import TRACKED
    for tr in sorted(set(trk[since]), key=lambda s: -int(((trk == s) & since).sum())):
        here = (trk == tr) & since
        cells = []
        for _, mm, u in by:
            s = R68.staked(tq, mm & here, paid, u)
            cells.append(f"{s['n']:,} / {s['units']:+,.1f} / {s['real']:+,.1f}" if s["n"] else "0")
        star = "*" if any(k in tr for k in TRACKED) else ""
        print(f"| {tr.title()}{star} | {pd.unique(t.race_id.values[here]).size:,} | " + " | ".join(cells) + " |")
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 77")
