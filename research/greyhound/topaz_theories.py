"""Which theories get our price closest to the starting price? One run, one split, every theory side by side
(4 Nov 2026, founder: "lets test a bunch of theories and how we can gets closest to BSP or SP").

    python research/greyhound/topaz_theories.py DIR LABEL     (as topaz_v1.py; results only)

Each row adds one group of features to the row above and is fitted the same way (LightGBM, softmax in the race,
trained on SP chances, rounds chosen on the middle quarter) and scored once on the last quarter, in two halves:

  T1  our ratings engine and race card (topaz_v1)
  T2  + run style and the speed map (topaz_v2)
  T3  + rolling 28/91/365-day form of the dog, trainer, sire and dam (Betfair's Topaz tutorial)
  T4  + vacant boxes beside the dog, and the box's win rate given its vacancies (Betfair's tutorial)
  T5  + GRV's own fields (rating, last5, totalFormCount, careerPrizeMoney), each only if a leak check here shows it
      was known before the race
  T6  + the market's past view of the dog: its previous SPs and how it ran against them (Benter's market history)
  T7  the T6 features trained on BSP chances where Betfair has the race (SP chances where it does not)
Then the last row trained on winners instead, and Benter's stage 2 blend of the best row with the SP.

BSP (founder, 4 Nov: "BSP is the sharpest tool out there ... lets see how close we can get to BSP"): when the
environment variable BETFAIR_DIR holds Betfair's free ANZ_Greyhounds files (2020 on), each Topaz runner is matched to
Betfair by Sydney date and dog name (a dog runs at most once a day), and every row is also scored against BSP on the
last-quarter races where every runner was matched.

Every feature is from EARLIER days only. The gap to the SP is the number that matters: winner log loss of the
model less the SP's, on the same races (negative = better than the SP).
"""
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import topaz_v1 as V1   # noqa: E402
import topaz_v2 as V2   # noqa: E402


def prev_day_values(df, keys, col, how="mean"):
    """`col` aggregated per (keys, day), then taken from the previous day the keys appear (strictly earlier)."""
    day = df.groupby(keys + ["date"])[col].agg(how).reset_index().sort_values(keys + ["date"])
    day["prev"] = day.groupby(keys)[col].shift()
    return df[keys + ["date"]].merge(day[keys + ["date", "prev"]], on=keys + ["date"], how="left").prev.values


def rolling_prior(df, key, col, window):
    """Mean of `col` for `key` over the `window` (e.g. '91D') before each day, the day itself excluded."""
    day = df.groupby([key, "date"])[col].agg(["sum", "count"]).reset_index().sort_values([key, "date"])
    r = (day.set_index("date").groupby(key)[["sum", "count"]].rolling(window, closed="left").sum()
         .reset_index())
    r["m"] = r["sum"] / r["count"]
    return df[[key, "date"]].merge(r[[key, "date", "m"]], on=[key, "date"], how="left").m.values


def t3(df):
    feats = []
    df["_place"] = df.finish
    df["_tr"] = df.time_rating if "time_rating" in df else np.nan
    for key in ("dog", "trainer_id", "sire_id", "dam_id"):
        if key not in df or df[key].isna().all():
            continue
        for col in ("_place", "won"):
            for w in ("28D", "91D", "365D"):
                if key in ("sire_id", "dam_id") and w == "28D":
                    continue
                name = f"{key}_{col.strip('_')}_{w}"
                df[name] = rolling_prior(df, key, col, w)
                feats.append(name)
    return df.drop(columns=["_place", "_tr"]), feats


def t4(df):
    boxes = df.groupby("race_id").box.apply(set)
    occ = df.race_id.map(boxes)
    left = np.array([(b - 1) in s for b, s in zip(df.box, occ)])
    right = np.array([(b + 1) in s for b, s in zip(df.box, occ)])
    df["vacant_left"] = ((df.box > 1) & ~left).astype(float)
    df["vacant_right"] = ((df.box < 8) & ~right).astype(float)
    df["vacant_any"] = ((df.vacant_left + df.vacant_right) > 0).astype(float)
    w, n = V1.prior_rate(df, ["track", "distance", "box", "vacant_any"], df.won.values)
    share = V1.prior_rate(df, ["track", "distance", "box", "vacant_any"], (1 / df.field).values)[0]
    df["box_vacancy_ratio"] = np.where(n >= 50, w / np.maximum(share, 1e-9), np.nan)
    return df, ["vacant_left", "vacant_right", "vacant_any", "box_vacancy_ratio"]


def t5(df, raw_cols):
    """GRV fields, each through a leak check: a pre-race field cannot track THIS run's result better than the last."""
    feats, notes = [], []
    srt = df.sort_values(["dog", "date", "race_id"])
    if "topaz_rating" in df and df.topaz_rating.notna().mean() > 0.5:
        d_now = srt.groupby("dog").topaz_rating.diff()                     # rating now less rating last run
        d_next = srt.groupby("dog").topaz_rating.shift(-1) - srt.topaz_rating
        c_now, c_next = np.corrcoef(*_clean(d_now, srt.won))[0, 1], np.corrcoef(*_clean(d_next, srt.won))[0, 1]
        ok = abs(c_next) >= 0.05 and abs(c_now) < 0.5 * abs(c_next)    # evidence it moves AFTER the run
        notes.append(f"rating: change INTO this run vs this run's win r = {c_now:+.3f}, change AFTER it r = "
                     f"{c_next:+.3f}: {'pre-race, used' if ok else 'not shown to be pre-race, NOT used'}")
        if ok:
            feats.append("topaz_rating")
    if "total_form" in df and df.total_form.notna().mean() > 0.5:
        prior_runs = srt.groupby("dog").cumcount()
        same = (srt.total_form == prior_runs).mean()
        plus1 = (srt.total_form == prior_runs + 1).mean()
        ok = same >= 0.5 and same > plus1
        notes.append(f"totalFormCount: equals runs before this one on {same:.0%}, runs including it on {plus1:.0%}: "
                     f"{'pre-race, used' if ok else 'not shown to be pre-race, NOT used'}")
        if ok:
            feats.append("total_form")
    if "career_prize" in df and df.career_prize.notna().mean() > 0.5:
        prev = srt.groupby("dog").career_prize.shift()
        prevp = srt.groupby("dog").prize.shift()
        pre = np.isclose(srt.career_prize, prev + prevp, atol=1).mean()
        post = np.isclose(srt.career_prize, prev + srt.prize, atol=1).mean()
        ok = pre >= 0.5 and pre > post
        notes.append(f"careerPrizeMoney: matches last total + last prize on {pre:.0%}, + this prize on {post:.0%}: "
                     f"{'pre-race, used' if ok else 'not shown to be pre-race, NOT used'}")
        if ok:
            feats.append("career_prize")
    if "last5" in df and df.last5.notna().mean() > 0.5:
        s = srt.last5.fillna("").astype(str).str.replace(r"[^0-9]", "", regex=True)
        prev_place = srt.groupby("dog").finish.shift()
        for end, pick in (("first", s.str[:1]), ("last", s.str[-1:])):
            v = pd.to_numeric(pick, errors="coerce")
            notes.append(f"last5 {end} digit: equals the previous run's place on {(v == prev_place).mean():.0%}, "
                         f"this run's on {(v == srt.finish).mean():.0%}")
        lastd = pd.to_numeric(s.str[-1:], errors="coerce")
        firstd = pd.to_numeric(s.str[:1], errors="coerce")
        pre = max((lastd == prev_place).mean(), (firstd == prev_place).mean())
        post = max((lastd == srt.finish).mean(), (firstd == srt.finish).mean())
        if pre >= 0.5 and pre > post:
            digits = s.map(lambda x: [int(c) for c in x if c != "0"])
            df.loc[srt.index, "last5_win_rate"] = digits.map(lambda x: np.mean([c == 1 for c in x]) if x else np.nan).values
            df.loc[srt.index, "last5_mean"] = digits.map(lambda x: np.mean(x) if x else np.nan).values
            feats += ["last5_win_rate", "last5_mean"]
            notes.append("last5: pre-race, used")
        else:
            notes.append("last5: not shown to be pre-race, NOT used")
    return df, feats, notes


def _clean(a, b):
    m = a.notna() & b.notna()
    return a[m].values, b[m].values.astype(float)


def t6(df):
    df["_lsp"] = np.log(df.start_price)
    df["_surprise"] = df.won - 1 / df.start_price
    df["mkt_prev_lsp"] = prev_day_values(df, ["dog"], "_lsp")
    df["mkt_lsp_mean5"] = V2.history_mean(df, "_lsp", 5)
    df["mkt_surprise5"] = V2.history_mean(df, "_surprise", 5)
    return df.drop(columns=["_lsp", "_surprise"]), ["mkt_prev_lsp", "mkt_lsp_mean5", "mkt_surprise5"]


def add_bsp(df):
    """BSP from Betfair's free files by (date, normalised dog name); p_bsp on races where every runner matched."""
    bdir = os.environ.get("BETFAIR_DIR", "")
    if not bdir or not os.path.isdir(bdir):
        return df, "no Betfair files given (BETFAIR_DIR): BSP comparison skipped"
    import gbm_v0
    bf = gbm_v0.load(bdir)
    bf = bf[(bf.STATE_CODE == "VIC") & (bf.WIN_BSP > 1)][["date", "dog", "WIN_BSP"]]
    bf = bf.drop_duplicates(["date", "dog"], keep=False)
    df["_dn"] = gbm_v0.norm_name(df.dog_name)
    df = df.merge(bf.rename(columns={"dog": "_dn", "WIN_BSP": "bsp"}), on=["date", "_dn"], how="left").drop(columns="_dn")
    full = df.bsp.notna().groupby(df.race_id).transform("all")
    inv = (1 / df.bsp).where(full)
    df["p_bsp"] = inv / inv.groupby(df.race_id).transform("sum")
    since = df[df.date >= bf.date.min()]
    note = (f"BSP matched on {df.bsp.notna().sum():,} runners; {df[full].race_id.nunique():,} races fully matched "
            f"({since[full.loc[since.index]].race_id.nunique() / max(since.race_id.nunique(), 1):.0%} of races since "
            f"{bf.date.min():%Y-%m-%d})")
    return df, note


def features(df, num, rel):
    X = df[num].astype(float).copy()
    for c in rel:
        if c in X:
            X[f"{c}_rel"] = X[c] - X[c].groupby(df.race_id).transform("mean")
    for c in V1.CAT:
        X[c] = df[c].astype("category")
    return X


def main(d, label):
    df = V1.build(d)
    m = re.search(r"since=(\d{4}-\d{2}-\d{2})", label)
    if m:
        df = df[df.date >= m.group(1)].reset_index(drop=True)
    # GRV fields for T5 (kept by topaz_to_runs under these names when present)
    for src, dst in (("rating", "topaz_rating"), ("totalFormCount", "total_form"), ("careerPrizeMoney", "career_prize"),
                     ("prizeMoney", "prize"), ("last5", "last5")):
        if dst not in df and src in df:
            df[dst] = df[src]
    df, f2 = V2.add_map(df)
    df = df.reset_index(drop=True)
    df, f3 = t3(df)
    df, f4 = t4(df)
    df, f5, notes = t5(df, df.columns)
    df, f6 = t6(df)
    df, bsp_note = add_bsp(df)
    df = df.sort_values(["date", "race_id", "box"]).reset_index(drop=True)
    df["p_mkt"] = df.p_bsp.fillna(df.p_sp) if "p_bsp" in df else df.p_sp

    q50, q75 = df.date.quantile(0.5), df.date.quantile(0.75)
    tr, va, te = df[df.date < q50], df[(df.date >= q50) & (df.date < q75)].copy(), df[df.date >= q75].copy()
    mid = te.date.quantile(0.5)
    h = (te.date < mid).values
    sp_ll = (V1.ll(te.p_sp, te.won), V1.ll(te.p_sp[h], te.won[h]), V1.ll(te.p_sp[~h], te.won[~h]))
    print(f"# {label}: theories against the starting price\n\n{df.race_id.nunique():,} races; fit before "
          f"{q50:%Y-%m-%d}, choose and blend to {q75:%Y-%m-%d}, score {te.race_id.nunique():,} races from "
          f"{q75:%Y-%m-%d} (halves split {mid:%Y-%m-%d})\n")
    print("Leak checks on GRV's own fields:\n" + "\n".join(f"- {n}" for n in notes) + "\n")
    print(f"GRV starting price on the scored races: {sp_ll[0]:.4f} (halves {sp_ll[1]:.4f} / {sp_ll[2]:.4f})")
    print(bsp_note)
    hb = te.p_bsp.notna().values if "p_bsp" in te else np.zeros(len(te), bool)
    if hb.any():
        bsp_ll = V1.ll(te.p_bsp[hb], te.won[hb])
        print(f"On the {te[hb].race_id.nunique():,} scored races Betfair fully priced: BSP {bsp_ll:.4f}, "
              f"GRV SP {V1.ll(te.p_sp[hb], te.won[hb]):.4f}")
    print("\n| theory | features | trained on | log loss | gap to SP (all) | gap 1st half | gap 2nd half | gap to BSP |")
    print("|---|---|---|---|---|---|---|---|")

    rel_extra = ["style_early", "style_led_rate", "style_gain", "dog_place_91D", "dog_won_91D", "trainer_id_won_91D",
                 "box_vacancy_ratio", "topaz_rating", "last5_mean", "mkt_lsp_mean5", "mkt_prev_lsp"]
    steps = [("T1 ratings engine + race card", []), ("T2 + run style and map", f2), ("T3 + dog/trainer/sire/dam windows", f3),
             ("T4 + vacant boxes", f4), ("T5 + GRV fields that pass the leak check", f5),
             ("T6 + market history", f6), ("T7 the same, trained on BSP chances", [])]
    num, best = list(V1.NUM), None
    for name, add in steps:
        num += [f for f in add if f not in num]
        rel = V1.REL + [f for f in rel_extra if f in num]
        Xtr, Xva, Xte = features(tr, num, rel), features(va, num, rel), features(te, num, rel)
        targets = (["p_mkt", "won"] if name.startswith("T7") else ["p_sp"])
        if name.startswith("T7") and not hb.any():
            continue
        for target in targets:
            bst, k = V1.fit(Xtr, tr[target].values.astype(float), tr.race_id, Xva, va.won.values, va.race_id.values)
            pv = V1.race_softmax(bst.predict(Xva, num_iteration=k, raw_score=True), va.race_id.values)
            pt = V1.race_softmax(bst.predict(Xte, num_iteration=k, raw_score=True), te.race_id.values)
            l = (V1.ll(pt, te.won), V1.ll(pt[h], te.won.values[h]), V1.ll(pt[~h], te.won.values[~h]))
            gb = f"{V1.ll(pt[hb], te.won.values[hb]) - bsp_ll:+.4f}" if hb.any() else ""
            tname = {"p_sp": "SP chances", "p_mkt": "BSP chances", "won": "winners"}[target]
            print(f"| {name} | {Xtr.shape[1]} | {tname} | {l[0]:.4f} | "
                  f"{l[0] - sp_ll[0]:+.4f} | {l[1] - sp_ll[1]:+.4f} | {l[2] - sp_ll[2]:+.4f} | {gb} |")
            if best is None or l[0] < best[0]:
                best = (l[0], name, target, pv, pt, bst, Xtr.columns)
    va["p_best"], te["p_best"] = best[3], best[4]
    w, _ = V1.blend(["p_best", "p_sp"], va)
    _, p = V1.blend(["p_best", "p_sp"], te, w)
    l = (V1.ll(p, te.won), V1.ll(p[h], te.won.values[h]), V1.ll(p[~h], te.won.values[~h]))
    print(f"\nBenter stage 2, best row ({best[1]}, {best[2]}) blended with the SP, weights {w[0]:.3f} / {w[1]:.3f}: "
          f"{l[0]:.4f}, gap to SP {l[0] - sp_ll[0]:+.4f} (halves {l[1] - sp_ll[1]:+.4f} / {l[2] - sp_ll[2]:+.4f})")
    if hb.any():
        vb, tb = va[va.p_bsp.notna()].copy(), te[te.p_bsp.notna()].copy()
        w, _ = V1.blend(["p_best", "p_bsp"], vb)
        _, p = V1.blend(["p_best", "p_bsp"], tb, w)
        print(f"Benter stage 2 with the BSP, weights {w[0]:.3f} / {w[1]:.3f}: {V1.ll(p, tb.won):.4f}, gap to BSP "
              f"{V1.ll(p, tb.won) - bsp_ll:+.4f}")
    imp = pd.Series(best[5].feature_importance("gain"), index=best[6]).sort_values(ascending=False)
    print("\nBest row's top inputs: " + ", ".join(f"{i} {v / imp.sum():.0%}" for i, v in imp.head(12).items()))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz theories")
