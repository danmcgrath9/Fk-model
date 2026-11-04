"""Round 3: everything left to try for BSP, then staking and ROI (4 Nov 2026, founder: "do it all think of everything
and then we have to get staking and ROI").

    python research/greyhound/topaz_round3.py DIR LABEL     (BETFAIR_DIR as for topaz_theories.py; results only)

PART 1, RATINGS CHECK: how well each pre-race rating predicts the dog's OWN time rating in the race (correlation, later
half), and the seconds per length at each track and distance measured from Topaz's two margins (seconds and lengths).

PART 2, NEW INFORMATION, each fitted as round 2's R1 (all history before the scored quarter, early stopping on its
last 6 months, BSP chances) and scored on the same races:
  B0  round 2's R1 (the baseline, +0.137 behind BSP in Test 10)
  B1  + ratings re-scaled by each track's own seconds per length, a recency-weighted time rating (half-life 3 runs),
        form trend (last run against the mean of 5), a class scale from the race type (Maiden to Free For All), the
        dog's class step since its last run and its usual class, the race's prize money, and interactions the map
        should carry (early-speed rank by box, usual leader by box)
  B2  B1 with recent years weighted more (half-life 3 years)
  B3  an ensemble: B2 blended with the same features trained on winners (weights from the early-stopping months)
The best of these is chosen on the EARLY-STOPPING months, never on the scored races.

PART 3, STAKING AND ROI with the chosen model, scored races only, both halves, odds capped at $21:
  - back at BSP when our chance x the BSP after 8% commission beats 1 by 5%, 10%, 20%;
  - back at GRV's SP (no commission) on the same rule;
each flat (1 unit) and quarter-Kelly (stake capped at 2% of the bank), with bets, winners, A/E, ROI, the bank's growth
and its worst drawdown. Both prices are set at the jump, so these are tests of the price, not bets we could place:
the bet we can place is at the open, and that test waits for recorded opens.
"""
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round2 as R2    # noqa: E402
import topaz_theories as T   # noqa: E402
import topaz_v1 as V1        # noqa: E402
from greyhound import ratings as GR   # noqa: E402

COMM = 0.08


def race_class(race_type: pd.Series) -> pd.Series:
    """GRV race type text to a class number: lower is better (Free For All 1 ... Grade 7 7, Maiden 8). Mixed grades
    take the middle; heats, finals and 'Rank Limit' keep their grade; Restricted Win sits at 4, Novice at 7."""
    t = race_type.fillna("").astype(str).str.lower()
    out = pd.Series(np.nan, index=t.index)
    g = t.str.extract(r"grade\s*(\d)")[0].astype(float)
    mixed = t.str.extract(r"mixed\s*(\d)\s*/\s*(\d)").astype(float)
    out = out.fillna(g).fillna((mixed[0] + mixed[1]) / 2)
    for word, v in (("free for all", 1.0), ("restricted win", 4.0), ("novice", 7.0), ("maiden", 8.0)):
        out = out.where(out.notna() | ~t.str.contains(word), v)
    return out


def secs_per_length(df: pd.DataFrame) -> tuple[pd.Series, str]:
    """Seconds per length at each track and distance, from Topaz's margin in seconds and its margin in lengths text,
    on placegetters at least half a length behind; the overall median where a track has fewer than 200."""
    if "margin_lengths_text" not in df:
        return pd.Series(GR.SEC_PER_LENGTH, index=df.index), "no margin-in-lengths text: 0.07 s a length everywhere"
    L = pd.to_numeric(df.margin_lengths_text.astype(str).str.extract(r"([\d.]+)\s*[Ll]")[0], errors="coerce")
    sec = df.margin * GR.SEC_PER_LENGTH                      # topaz_to_runs stored seconds / 0.07
    ok = (df.finish > 1) & (L >= 0.5) & (sec > 0)
    r = (sec / L)[ok]
    overall = float(r.median()) if ok.any() else GR.SEC_PER_LENGTH
    g = r.groupby([df.track[ok], df.distance[ok]])
    per = g.median()[g.size() >= 200]
    key = pd.MultiIndex.from_arrays([df.track, df.distance])
    spl = pd.Series(per.reindex(key).values, index=df.index).fillna(overall)
    note = (f"seconds per length: overall median {overall:.4f}; {len(per)} track-distances measured, from "
            f"{per.min():.4f} to {per.max():.4f}" if len(per) else f"seconds per length: overall {overall:.4f}")
    return spl, note


def history_ewm(df, col, halflife=3.0):
    """Exponentially weighted mean of `col` over the dog's runs on EARLIER days (half-life in runs)."""
    x = df[["dog", "date", col]].copy()
    x["_i"] = np.arange(len(x))
    x = x.sort_values(["dog", "date", "_i"])
    x["_m"] = x.groupby("dog")[col].transform(lambda s: s.ewm(halflife=halflife, ignore_na=True).mean())
    day = x.groupby(["dog", "date"])._m.last().reset_index()
    day["prev"] = day.groupby("dog")._m.shift()
    return df[["dog", "date"]].merge(day[["dog", "date", "prev"]], on=["dog", "date"], how="left").prev.values


def new_features(df):
    notes, feats = [], []
    rated = GR.run_ratings(df)                                # this run's own ratings (for history and the check)
    df["own_time_rating"], df["own_split_rating"] = rated.time_rating.values, rated.split_rating.values
    spl, note = secs_per_length(df)
    notes.append(note)
    for c in ("time_rating_last", "time_rating_mean5", "time_rating_best5"):
        df[f"{c}_trk"] = df[c] * GR.SEC_PER_LENGTH / spl
        feats.append(f"{c}_trk")
    df["time_rating_ewm"] = history_ewm(df, "own_time_rating")
    df["split_rating_ewm"] = history_ewm(df, "own_split_rating")
    df["form_trend"] = df.time_rating_last - df.time_rating_mean5
    df["race_class"] = race_class(df.get("race_type", pd.Series(np.nan, index=df.index)))
    df["_cls"] = df.race_class
    df["dog_prev_class"] = T.prev_day_values(df, ["dog"], "_cls")
    df["class_step"] = df.race_class - df.dog_prev_class        # positive: dropping to an easier class
    df["dog_class_mean5"] = R2.T.V2.history_mean(df, "_cls", 5)
    df["race_prize_log"] = np.log1p(df.groupby("race_id").prize.transform("max")) if "prize" in df else np.nan
    df["speed_rank_x_box"] = df.map_speed_rank * df.box
    df["leader_x_box"] = df.style_led_rate / df.box
    feats += ["time_rating_ewm", "split_rating_ewm", "form_trend", "race_class", "dog_prev_class", "class_step",
              "dog_class_mean5", "race_prize_log", "speed_rank_x_box", "leader_x_box"]
    return df.drop(columns=["_cls"]), feats, notes


def ratings_check(df):
    late = df[df.date >= df.date.quantile(0.5)]
    print("## Part 1: the ratings check\n")
    print("How well each pre-race rating predicts the dog's own time rating in the race (later half; higher is "
          "better):\n\n| pre-race rating | runners | correlation |\n|---|---|---|")
    for c in ("time_rating_last", "time_rating_mean5", "time_rating_best5", "time_rating_ewm", "time_rating_mean5_trk",
              "split_rating_mean5", "split_rating_ewm", "elo", "finish_mean5"):
        if c in late:
            ok = late[c].notna() & late.own_time_rating.notna()
            r = np.corrcoef(late[c][ok], late.own_time_rating[ok])[0, 1] if ok.sum() > 100 else np.nan
            print(f"| {c} | {int(ok.sum()):,} | {r:+.3f} |")


def stake(te, p, price, comm, edges, label, h):
    print(f"\n### {label}\n")
    print("| edge at least | half | bets | winners | A/E | flat ROI | quarter-Kelly bank x | worst drawdown |")
    print("|---|---|---|---|---|---|---|---|")
    o = 1 + (price - 1) * (1 - comm)
    order = np.argsort(te.date.values, kind="stable")
    for e in edges:
        sel = (p * o >= 1 + e) & (price <= 21) & np.isfinite(price) & (price > 1)
        for hn, hm in (("1st", h), ("2nd", ~h)):
            m = sel & hm
            idx = order[m[order]]
            n = len(idx)
            if not n:
                print(f"| {e:.0%} | {hn} | 0 | | | | | |")
                continue
            won = te.won.values[idx]
            ae = won.sum() / (1 / price[idx]).sum()
            roi = np.where(won == 1, o[idx] - 1, -1).mean()
            bank, peak, dd = 1.0, 1.0, 0.0
            for i, w in zip(idx, won):
                f = min(0.25 * (p[i] * o[i] - 1) / (o[i] - 1), 0.02)
                bank *= 1 + f * ((o[i] - 1) if w else -1)
                peak = max(peak, bank)
                dd = max(dd, 1 - bank / peak)
            print(f"| {e:.0%} | {hn} | {n:,} | {int(won.sum()):,} | {ae:.3f} | {roi:+.1%} | {bank:.2f} | {dd:.0%} |")


def main(d, label):
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
    df, fnew, notes = new_features(df)
    df = df.copy()
    print(f"# {label}: round 3\n\n{bsp_note}\n" + "\n".join(notes) + "\n")
    ratings_check(df)

    q75 = df.date.quantile(0.75)
    span = q75 - df.date.min()
    es_start = q75 - min(pd.Timedelta(days=183), span / 4)
    pre, te = df[df.date < q75], df[df.date >= q75].copy()
    fp, es = pre[pre.date < es_start], pre[pre.date >= es_start].copy()
    hb = te.p_bsp.notna().values
    h = (te.date < te.date.quantile(0.5)).values
    w_te = te.won.values
    bsp_all = V1.ll(te.p_bsp.values[hb], w_te[hb])
    hb_es = es.p_bsp.notna().values

    base = list(dict.fromkeys(V1.NUM + f2 + f3 + f4 + f5 + f6))
    rel = V1.REL + [f for f in ["style_early", "style_led_rate", "style_gain", "dog_place_91D", "dog_won_91D",
                                "trainer_id_won_91D", "box_vacancy_ratio", "last5_mean", "mkt_lsp_mean5",
                                "mkt_prev_lsp", "time_rating_mean5_trk", "time_rating_ewm", "split_rating_ewm",
                                "class_step"] if f in base + fnew]
    years = ((es_start - fp.date).dt.days / 365.25).values
    recency = 0.5 ** (years / 3.0)

    print(f"\n## Part 2: new information against BSP\n\nscored: {te[hb].race_id.nunique():,} races from "
          f"{q75:%Y-%m-%d}, BSP {bsp_all:.4f}; chosen on the early-stopping months ({es.race_id.nunique():,} races)\n")
    print("| row | features | rounds | early-stopping months: log loss | scored: log loss | gap to BSP | 1st half | "
          "2nd half |\n|---|---|---|---|---|---|---|---|")
    results = {}

    def run(name, num, target="p_mkt", weight=None):
        Xf, Xe, Xt = T.features(fp, num, rel), T.features(es, num, rel), T.features(te, num, rel)
        y = fp[target].values.astype(float)
        bst, k, _ = fit_weighted(Xf, y, fp.race_id, Xe, es.won.values, es.race_id.values, weight)
        pe = V1.race_softmax(bst.predict(Xe, num_iteration=k, raw_score=True), es.race_id.values)
        pt = V1.race_softmax(bst.predict(Xt, num_iteration=k, raw_score=True), te.race_id.values)
        results[name] = (pe, pt, bst, Xf.columns)
        report(name, Xf.shape[1], k, pe, pt)

    def report(name, nf, k, pe, pt):
        le = V1.ll(pe[hb_es], es.won.values[hb_es]) if hb_es.any() else V1.ll(pe, es.won.values)
        l, l1, l2 = V1.ll(pt[hb], w_te[hb]), V1.ll(pt[hb & h], w_te[hb & h]), V1.ll(pt[hb & ~h], w_te[hb & ~h])
        b1, b2 = V1.ll(te.p_bsp.values[hb & h], w_te[hb & h]), V1.ll(te.p_bsp.values[hb & ~h], w_te[hb & ~h])
        print(f"| {name} | {nf} | {k} | {le:.4f} | {l:.4f} | {l - bsp_all:+.4f} | {l1 - b1:+.4f} | {l2 - b2:+.4f} |")

    run("B0 round 2's R1", base)
    run("B1 + track lengths, recent form, class, prize, interactions", base + fnew)
    run("B2 B1 with recent years weighted more", base + fnew, weight=recency)
    run("B2w the same, trained on winners", base + fnew, target="won", weight=recency)
    es["a"], es["b"] = results["B2 B1 with recent years weighted more"][0], results["B2w the same, trained on winners"][0]
    te["a"], te["b"] = results["B2 B1 with recent years weighted more"][1], results["B2w the same, trained on winners"][1]
    wts, pe3 = V1.blend(["a", "b"], es)
    _, pt3 = V1.blend(["a", "b"], te, wts)
    results["B3 ensemble of B2 and B2w"] = (pe3, pt3, None, None)
    report(f"B3 ensemble of B2 and B2w ({wts[0]:.2f} / {wts[1]:.2f})", 0, 0, pe3, pt3)

    def es_ll(v):
        pe = v[0]
        return V1.ll(pe[hb_es], es.won.values[hb_es]) if hb_es.any() else V1.ll(pe, es.won.values)
    chosen = min(results, key=lambda k: es_ll(results[k]))
    p = results[chosen][1]
    bst = results[chosen][2]
    if bst is not None:
        imp = pd.Series(bst.feature_importance("gain"), index=results[chosen][3]).sort_values(ascending=False)
        print("\nChosen model's top inputs: " + ", ".join(f"{i} {v / imp.sum():.0%}" for i, v in imp.head(15).items()))
    print(f"\nChosen on the early-stopping months: **{chosen}**, scored {V1.ll(p[hb], w_te[hb]):.4f}, gap to BSP "
          f"{V1.ll(p[hb], w_te[hb]) - bsp_all:+.4f}")

    print("\n## Part 3: staking and ROI with the chosen model (scored races only, odds to $21)")
    bsp = te.bsp.values if "bsp" in te else np.full(len(te), np.nan)
    stake(te, p, bsp, COMM, (0.05, 0.10, 0.20), "Back at BSP, 8% commission on winnings", h)
    stake(te, p, te.start_price.values, 0.0, (0.05, 0.10, 0.20), "Back at GRV's SP, no commission", h)


def fit_weighted(Xtr, ytr, rtr, Xes, wes, res, weight):
    """R2.fit_es with optional row weights applied inside the race-softmax objective."""
    if weight is None:
        return R2.fit_es(Xtr, ytr, rtr, Xes, wes, res, R2.SMALL, 3000)
    import lightgbm as lgb
    groups = rtr.groupby(rtr.values, sort=False).size().values
    starts = np.r_[0, np.cumsum(groups)[:-1]]
    w = np.asarray(weight, dtype=float)

    def obj(preds, data):
        y = data.get_label()
        e = np.exp(preds - np.repeat(np.maximum.reduceat(preds, starts), groups))
        p = e / np.repeat(np.add.reduceat(e, starts), groups)
        return w * (p - y), w * np.maximum(p * (1 - p), 1e-6)
    params = dict(R2.SMALL, objective=obj, metric="None", verbose=-1, seed=1)
    score = R2.fast_race_ll(res)
    won = np.asarray(wes)
    dtr = lgb.Dataset(Xtr, ytr, categorical_feature=V1.CAT, free_raw_data=False)
    des = lgb.Dataset(Xes, won.astype(float), reference=dtr, categorical_feature=V1.CAT, free_raw_data=False)
    bst = lgb.train(params, dtr, num_boost_round=3000, valid_sets=[des],
                    feval=lambda pr, data: ("race_ll", score(pr, won), False),
                    callbacks=[lgb.early_stopping(300, verbose=False)])
    return bst, bst.best_iteration, bst.best_score["valid_0"]["race_ll"]


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 3")
