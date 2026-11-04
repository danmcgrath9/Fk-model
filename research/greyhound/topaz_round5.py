"""Round 5: new information to get closer to BSP (4 Nov 2026, founder: "surely we can get a sharper model and just
try and get closer to bsp and we beat open comfortably").

    python research/greyhound/topaz_round5.py DIR LABEL     (DIR also holds trials_<STATE>_<YYYY-MM>.json.gz when
                                                              the run pulled trials; BETFAIR_DIR as before)

Round 2 showed more capacity does not help (Test 10), so every row here adds information the model has not had,
each from EARLIER days only:
  C0  round 3's B2 (recent years weighted more, BSP chances): the baseline, +0.127 behind BSP in Test 11
  C1  + the stewards' comments: the 40 commonest words in GRV's run comments (CHECKED, CROWDED, SLOW AWAY ... as GRV
        writes them), each as "in the dog's last run" and "how often in its last 5"; a dog that was checked ran
        worse than it is, which the market knows and the ratings did not
  C2  + trials (GRV's /trialresult, which the bulk runs leave out): days since its last trial, the trial's speed
        against that track and distance's usual trial time, its margin and outcome, trials in the last 60 days, and
        whether it has trialled since its last race (the only form a first starter or a dog back from a spell has)
  C3  + the box's win rate at the track and distance over the last 60 days against its long run (track bias moves)
Scored on the same 22,841 races as Tests 9-12, against BSP, both halves; the best row chosen on the early-stopping
months is then staked as Test 12 was (rules chosen on those months, scored once), at GRV's SP and at BSP.
"""
import gzip
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import topaz_round3 as R3    # noqa: E402
import topaz_round4 as R4    # noqa: E402
import topaz_theories as T   # noqa: E402
import topaz_v1 as V1        # noqa: E402


def comment_features(df, n_words=40):
    text = df.get("comment", pd.Series("", index=df.index)).fillna("").astype(str).str.upper()
    words = text.str.findall(r"[A-Z]{2,}")
    counts = pd.Series([w for ws in words for w in set(ws)]).value_counts()
    top = [w for w in counts.index if counts[w] >= 0.003 * len(df)][:n_words]
    feats = []
    sets = words.map(set)
    for w in top:
        col = f"_cw_{w}"
        df[col] = sets.map(lambda s, w=w: float(w in s))
        df[f"cmt_last_{w}"] = T.prev_day_values(df, ["dog"], col)
        df[f"cmt_rate5_{w}"] = T.V2.history_mean(df, col, 5)
        feats += [f"cmt_last_{w}", f"cmt_rate5_{w}"]
    df = df.drop(columns=[c for c in df.columns if c.startswith("_cw_")])
    return df, feats, top


def load_trials(d):
    rows = []
    for f in sorted(Path(d).glob("trials_*_*.json.gz")):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            rows.extend(json.load(fh))
    if not rows:
        return None
    t = pd.DataFrame(rows)
    t["date"] = pd.to_datetime(t.trialDate.astype(str).str[:10], errors="coerce")
    t["dog"] = pd.to_numeric(t.dogId, errors="coerce").astype("Int64").astype(str)
    for c in ("distance", "winTime", "margin", "boxNumber", "weight"):
        t[c] = pd.to_numeric(t.get(c), errors="coerce")
    t["outcome"] = pd.to_numeric(t.get("trialOutcomeCode", pd.Series(np.nan, index=t.index)).astype(str)
                                 .str.extract(r"(\d+)")[0], errors="coerce")
    t = t.dropna(subset=["date"]).sort_values("date")
    # the usual trial time at a track and distance, from EARLIER trials only (median of winning times)
    g = t.groupby(["trackCode", "distance"])
    t["_par"] = g.winTime.transform(lambda s: s.expanding().median().shift())
    t["trial_speed"] = (t._par - t.winTime) / 0.0671           # lengths quicker than the usual trial (Test 11's spl)
    return t


def trial_features(df, t):
    if t is None:
        return df, [], "no trial files: C2 skipped"
    t = t.sort_values("date")
    t["trials_60d"] = t.groupby("dog").date.transform(
        lambda s: pd.Series(1, index=s.values).rolling("60D").sum().values)
    last = t[["dog", "date", "trial_speed", "margin", "outcome", "boxNumber", "trials_60d"]].rename(
        columns={"date": "trial_date", "margin": "trial_margin", "outcome": "trial_outcome", "boxNumber": "trial_box"})
    left = df[["dog", "date"]].reset_index().sort_values("date")
    m = pd.merge_asof(left, last.sort_values("trial_date"), left_on="date", right_on="trial_date", by="dog",
                      allow_exact_matches=False).set_index("index").reindex(df.index)
    df["trial_days"] = (df.date - m.trial_date).dt.days
    for c in ("trial_speed", "trial_margin", "trial_outcome", "trial_box", "trials_60d"):
        df[c] = m[c].values
    last_race = df.date - pd.to_timedelta(df.days_since, unit="D")
    df["trialled_since_race"] = ((m.trial_date > last_race) | df.days_since.isna() & m.trial_date.notna()).astype(float)
    feats = ["trial_days", "trial_speed", "trial_margin", "trial_outcome", "trial_box", "trials_60d",
             "trialled_since_race"]
    return df, feats, f"trials: {len(t):,} trial runs from {t.date.min():%Y-%m-%d}; a trial before the race for " \
                      f"{df.trial_days.notna().mean():.0%} of runners"


def recent_bias(df):
    key = df.track.astype(str) + "|" + df.distance.astype(str) + "|" + df.box.astype(str)
    df["_k"] = key
    df["_share"] = 1 / df.field
    w = T.rolling_prior(df, "_k", "won", "60D")
    s = T.rolling_prior(df, "_k", "_share", "60D")
    df["box_ratio_60d"] = w / s
    df["box_ratio_60d_vs_long"] = df.box_ratio_60d - df.box_ratio
    return df.drop(columns=["_k", "_share"]), ["box_ratio_60d", "box_ratio_60d_vs_long"]


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
    df, fnew, _ = R3.new_features(df)
    df, fc, words = comment_features(df)
    df, ft, trial_note = trial_features(df, load_trials(d))
    df, fb = recent_bias(df)
    df = df.copy()
    print(f"# {label}: round 5, new information against BSP\n\n{bsp_note}\n{trial_note}\n"
          f"comment words used ({len(words)}): {', '.join(words)}\n")

    q75 = df.date.quantile(0.75)
    span = q75 - df.date.min()
    es_start = q75 - min(pd.Timedelta(days=183), span / 4)
    pre, te = df[df.date < q75], df[df.date >= q75].copy()
    fp, es = pre[pre.date < es_start], pre[pre.date >= es_start].copy()
    hb, hb_es = te.p_bsp.notna().values, es.p_bsp.notna().values
    h = (te.date < te.date.quantile(0.5)).values
    w_te = te.won.values
    bsp_all = V1.ll(te.p_bsp.values[hb], w_te[hb])
    b1, b2 = V1.ll(te.p_bsp.values[hb & h], w_te[hb & h]), V1.ll(te.p_bsp.values[hb & ~h], w_te[hb & ~h])
    recency = 0.5 ** (((es_start - fp.date).dt.days / 365.25).values / 3.0)
    base = list(dict.fromkeys(V1.NUM + f2 + f3 + f4 + f5 + f6 + fnew))
    rel_base = V1.REL + [f for f in ["style_early", "style_led_rate", "style_gain", "dog_place_91D", "dog_won_91D",
                                     "trainer_id_won_91D", "box_vacancy_ratio", "last5_mean", "mkt_lsp_mean5",
                                     "mkt_prev_lsp", "time_rating_mean5_trk", "time_rating_ewm", "split_rating_ewm",
                                     "class_step"] if f in base]
    print(f"scored: {te[hb].race_id.nunique():,} races from {q75:%Y-%m-%d}, BSP {bsp_all:.4f} (halves {b1:.4f} / "
          f"{b2:.4f})\n")
    print("| row | features | rounds | early-stopping log loss | scored log loss | gap to BSP | 1st half | 2nd half |")
    print("|---|---|---|---|---|---|---|---|")
    rows = [("C0 round 3's B2", base, rel_base), ("C1 + stewards' comments", base + fc, rel_base),
            ("C2 + trials", base + fc + ft, rel_base + [f for f in ("trial_speed",) if ft]),
            ("C3 + recent box bias", base + fc + ft + fb, rel_base + [f for f in ("trial_speed",) if ft])]
    best = None
    for name, num, rel in rows:
        if name.startswith("C2") and not ft:
            continue
        Xf, Xe, Xt = T.features(fp, num, rel), T.features(es, num, rel), T.features(te, num, rel)
        bst, k, _ = R3.fit_weighted(Xf, fp.p_mkt.values.astype(float), fp.race_id, Xe, es.won.values,
                                    es.race_id.values, recency)
        pe = V1.race_softmax(bst.predict(Xe, num_iteration=k, raw_score=True), es.race_id.values)
        pt = V1.race_softmax(bst.predict(Xt, num_iteration=k, raw_score=True), te.race_id.values)
        le = V1.ll(pe[hb_es], es.won.values[hb_es])
        l, l1, l2 = V1.ll(pt[hb], w_te[hb]), V1.ll(pt[hb & h], w_te[hb & h]), V1.ll(pt[hb & ~h], w_te[hb & ~h])
        print(f"| {name} | {Xf.shape[1]} | {k} | {le:.4f} | {l:.4f} | {l - bsp_all:+.4f} | {l1 - b1:+.4f} | "
              f"{l2 - b2:+.4f} |")
        if best is None or le < best[0]:
            best = (le, name, pe, pt, bst, Xf.columns)
    _, name, pe, pt, bst, cols = best
    imp = pd.Series(bst.feature_importance("gain"), index=cols).sort_values(ascending=False)
    print(f"\nChosen on the early-stopping months: **{name}**. Top inputs: " +
          ", ".join(f"{i} {v / imp.sum():.0%}" for i, v in imp.head(15).items()))
    new = imp[[c for c in imp.index if c.startswith(("cmt_", "trial_days", "trial_speed", "trial_margin", "trial_outcome",
                                                     "trial_box", "trials_60d", "trialled", "box_ratio_60d"))]]
    if len(new):
        print("Top new inputs: " + ", ".join(f"{i} {v / imp.sum():.1%}" for i, v in new.head(12).items()))

    # staking, as Test 12: rules chosen on the early-stopping months, scored once
    for pname, col, comm in (("GRV's SP, no commission", "start_price", 0.0), ("BSP, 8% commission", "bsp", 0.08)):
        cands = []
        for one in (False, True):
            for band in R4.BANDS:
                for e in R4.EDGES:
                    m, o = R4.selections(es, pe, es[col].values, comm, e, band, one)
                    r = R4.result(es, m, o, pe, 0, es[col].values)
                    if r["n"] >= 300:
                        cands.append((r["roi"], one, band, e, r["n"]))
        if not cands:
            continue
        cands.sort(reverse=True)
        roi_es, one, band, e, n_es = cands[0]
        print(f"\n## Staking at {pname}\n\nChosen on the early-stopping months: one a race {'yes' if one else 'no'}, "
              f"${band[0]:g}-${band[1]:g}, edge {e:.0%} ({n_es:,} bets there, {roi_es:+.1%}). Scored:\n")
        print("| half | bets | winners | A/E | flat ROI | worst drawdown at 0.5% a bet | longest losing run |")
        print("|---|---|---|---|---|---|---|")
        for hn, hm in (("1st", h), ("2nd", ~h)):
            sub = te[hm]
            m, o = R4.selections(sub, pt[hm], sub[col].values, comm, e, band, one)
            r = R4.result(sub, m, o, pt[hm], 0, sub[col].values)
            if r["n"]:
                idx = np.flatnonzero(m)
                idx = idx[np.argsort(sub.date.values[idx], kind="stable")]
                bank, peak, dd = 1.0, 1.0, 0.0
                for i in idx:
                    bank *= 1 + 0.005 * ((o[i] - 1) if sub.won.values[i] else -1)
                    peak, dd = max(peak, bank), max(dd, 1 - bank / peak)
                print(f"| {hn} | {r['n']:,} | {r['w']:,} | {r['ae']:.3f} | {r['roi']:+.1%} | {dd:.0%} | {r['run']} |")
        m, o = R4.selections(te, pt, te[col].values, comm, e, band, one)
        t = te[m].assign(ret=np.where(te.won.values[m] == 1, o[m] - 1, -1))
        bym = t.groupby(t.date.dt.to_period("M")).ret.mean()
        print(f"\nMonths in profit: {(bym > 0).sum()} of {len(bym)}; last 6 months: " +
              ", ".join(f"{p}: {v:+.0%}" for p, v in bym.tail(6).items()))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 5")
