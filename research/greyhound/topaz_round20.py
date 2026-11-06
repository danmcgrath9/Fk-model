"""Round 20: track character (6 Nov 2026, founder: "track dimensions ... tight tracks, big tracks, straight tracks";
then "1 is fine now, would just be a small amount of cases, a dog transferring for the first time etc").

    python research/greyhound/topaz_round20.py DIR LABEL    (BETFAIR_DIR, RACES_DIR; WALK_GRV_RATING / WALK_RELIABLE /
                                                             WALK_LEAD / WALK_DRIFT as the weekly train sets them)

No dimensions (Topaz carries none). Each track and distance is measured from its own earlier results instead, as of
the end of the day before (at least MIN_RACES races, else blank):
  trk_lead_win   share of races won by the dog that led at the first point   (high: a speed track)
  trk_closer_win share won by a dog 4th or worse at the first point          (high: a track you can come from behind)
  trk_margin     mean winning margin, lengths                               (wide: a galloping, spread-out track)
  trk_inside     share won from boxes 1-2 over the share won from boxes 7-8
and each dog's form at tracks of the SAME kind as today's: a track is a "speed track" when its trk_lead_win is above the
median over the training rows, and the dog's form is how far it beat the market (won less its market chance) on
average in its earlier runs at speed tracks, or at the others:
  dog_type_surprise, dog_type_runs   at today's kind of track
  dog_other_surprise                 at the other kind
The production inputs, the standard split; F0 the production model, F1 + track character and the dog's form by kind of
track. Scored on the last quarter, both halves: log loss and gap to BSP, the races with a dog at the track for the first
time, A/E of those first-timers against both models, BSP and GRV's SP, and the 1.3x rule at GRV's SP.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round3 as R3         # noqa: E402
import topaz_round9 as R9         # noqa: E402
import topaz_round11 as R11       # noqa: E402
import topaz_theories as T        # noqa: E402
import topaz_v1 as V1             # noqa: E402
import topaz_walk as W            # noqa: E402
from topaz_v2 import pir_positions  # noqa: E402

MIN_RACES = 30
DRIFT_CAP = 1.3
TRACK_COLS = ["trk_lead_win", "trk_closer_win", "trk_margin", "trk_inside"]
DOG_COLS = ["dog_type_surprise", "dog_type_runs", "dog_other_surprise"]


def track_character(df: pd.DataFrame) -> pd.DataFrame:
    """TRACK_COLS for every row, from the track and distance's races on EARLIER days (winners' rows carry the race)."""
    first, _ = pir_positions(df.get("pir", pd.Series(np.nan, index=df.index)))
    win = (df.finish == 1).values
    second_margin = df.margin.where(df.finish == 2).groupby(df.race_id).transform("max")
    box = pd.to_numeric(df.box, errors="coerce")
    df = df.assign(_led=np.where(win, (first == 1).astype(float).where(first.notna()), np.nan),
                   _closer=np.where(win, (first >= 4).astype(float).where(first.notna()), np.nan),
                   _wmargin=np.where(win, second_margin, np.nan),
                   _in=np.where(win, (box <= 2).astype(float), np.nan),
                   _out=np.where(win, (box >= 7).astype(float), np.nan),
                   _one=np.where(win, 1.0, np.nan))
    keys = ["track", "distance"]
    _, n = R11._prev_sum_count(df, keys, "_one")
    for col, src in (("trk_lead_win", "_led"), ("trk_closer_win", "_closer"), ("trk_margin", "_wmargin")):
        s, c = R11._prev_sum_count(df, keys, src)
        df[col] = np.where(c >= MIN_RACES, s / np.maximum(c, 1), np.nan)
    si, ci = R11._prev_sum_count(df, keys, "_in")
    so, co = R11._prev_sum_count(df, keys, "_out")
    ok = (ci >= MIN_RACES) & (so > 0)
    df["trk_inside"] = np.where(ok, (si / np.maximum(ci, 1)) / np.maximum(so / np.maximum(co, 1), 1e-9), np.nan)
    return df.drop(columns=["_led", "_closer", "_wmargin", "_in", "_out", "_one"])


def dog_type_form(df: pd.DataFrame, cut: float) -> pd.DataFrame:
    """DOG_COLS: the dog's mean (won - market chance) in earlier runs at speed tracks (trk_lead_win >= cut) or the
    rest, for today's kind of track and the other kind."""
    kind = np.where(df.trk_lead_win.isna(), np.nan, (df.trk_lead_win >= cut).astype(float))
    df = df.assign(_kind=kind, _surp=(df.won - df.p_mkt).where(df.p_mkt.notna()))
    df["_surp_k"] = df._surp.where(df._kind.notna())
    s_all, c_all = R11._prev_sum_count(df, ["dog"], "_surp_k")
    s_t, c_t = R11._prev_sum_count(df.assign(_k=df._kind.fillna(-1)), ["dog", "_k"], "_surp_k")
    has = df._kind.notna().values
    df["dog_type_surprise"] = np.where(has & (c_t > 0), s_t / np.maximum(c_t, 1), np.nan)
    df["dog_type_runs"] = np.where(has, c_t, np.nan)
    c_o = c_all - c_t
    df["dog_other_surprise"] = np.where(has & (c_o > 0), (s_all - s_t) / np.maximum(c_o, 1), np.nan)
    return df.drop(columns=["_kind", "_surp", "_surp_k"])


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    df, num, rel, note = W.build_full(d)
    print(f"# {label}: round 20, track character\n\n{note}\n")
    df = track_character(df)
    q75 = df.date.quantile(0.75)
    es_start = q75 - min(pd.Timedelta(days=183), (q75 - df.date.min()) / 4)
    cut = float(df.trk_lead_win[df.date < es_start].median())
    df = dog_type_form(df, cut)
    tracks = df[df.trk_lead_win.notna()].groupby("track").trk_lead_win.last().sort_values()
    print(f"Speed tracks: the leader wins {cut:.1%} or more (the training rows' median). Leader's win share by track, "
          f"latest: " + ", ".join(f"{t} {v:.0%}" for t, v in tracks.items()) + "\n")
    pre, te = df[df.date < q75], df[df.date >= q75].copy()
    fp, es = pre[pre.date < es_start].copy(), pre[pre.date >= es_start].copy()
    recency = 0.5 ** (((es_start - fp.date).dt.days / 365.25).values / 3.0)
    first_time = ((te.runs_track == 0) & (te.runs > 0)).values
    race_ft = pd.Series(first_time).groupby(te.race_id.values).transform("max").values
    h = (te.date < te.date.quantile(0.5)).values
    w = te.won.values
    hb = te.p_bsp.notna().values
    b_all, b1, b2, bft = (V1.ll(te.p_bsp.values[m], w[m]) for m in (hb, hb & h, hb & ~h, hb & race_ft))
    print(f"Scored: {te[hb].race_id.nunique():,} races with BSP (BSP {b_all:.4f}); {first_time.sum():,} runners at the "
          f"track for the first time (not debut), in {te.race_id[race_ft & hb].nunique():,} of those races\n")
    print("| row | inputs | rounds | log loss | gap to BSP | 1st half | 2nd half | gap, races with a first-timer |\n"
          "|---|---|---|---|---|---|---|---|")
    rows = (("F0 the production model", num, rel), ("F1 + track character and form by kind of track",
                                                   num + TRACK_COLS + DOG_COLS, rel + ["dog_type_surprise"]))
    for name, cols, rels in rows:
        Xf, Xe, Xt = T.features(fp, cols, rels), T.features(es, cols, rels), T.features(te, cols, rels)
        bst, k, _ = R3.fit_weighted(Xf, fp.p_mkt.values.astype(float), fp.race_id, Xe, es.won.values,
                                    es.race_id.values, recency, rounds=6000)
        col = "p_" + name[:2]
        es[col] = V1.race_softmax(bst.predict(Xe, num_iteration=k, raw_score=True), es.race_id.values)
        te[col] = V1.race_softmax(bst.predict(Xt, num_iteration=k, raw_score=True), te.race_id.values)
        p = te[col].values
        g = [V1.ll(p[m], w[m]) - b for m, b in ((hb, b_all), (hb & h, b1), (hb & ~h, b2), (hb & race_ft, bft))]
        print(f"| {name} | {len(cols)} | {k} | {V1.ll(p[hb], w[hb]):.4f} | {g[0]:+.4f} | {g[1]:+.4f} | {g[2]:+.4f} | "
              f"{g[3]:+.4f} |")

    t = te[hb]
    ft = ((t.runs_track == 0) & (t.runs > 0)).values
    print("\n| runners (races with BSP) | runners | wins | A/E vs F0 | A/E vs F1 | A/E vs BSP | A/E vs GRV's SP |\n"
          "|---|---|---|---|---|---|---|")
    groups = (("first time at the track", ft), ("first time, a speed track, form there good",
                                                ft & (t.trk_lead_win >= cut).values & (t.dog_type_surprise > 0).values),
              ("first time, form at this kind of track poor", ft & (t.dog_type_surprise < 0).values),
              ("raced here before", (t.runs_track > 0).values))
    for name, m in groups:
        if m.sum() < 300:
            continue
        g = t[m]
        wn = g.won.sum()
        print(f"| {name} | {m.sum():,} | {int(wn):,} | {wn / g.p_F0.sum():.3f} | {wn / g.p_F1.sum():.3f} | "
              f"{wn / g.p_bsp.sum():.3f} | {wn / g.p_sp.sum():.3f} |")

    e_ok, t_ok = es.p_sp.notna().values, te.p_sp.notna().values
    t2 = te[t_ok].copy()
    h2 = (t2.date < t2.date.quantile(0.5)).values
    price = t2.start_price.astype(float).values
    print("\n## The 1.3x rule at GRV's SP (our price $2-$15, Kelly x75 cap 4, no commission)\n")
    print("| row | guard | half | bets | winners | A/E | flat ROI | units staked | Kelly ROI | units won |\n"
          "|---|---|---|---|---|---|---|---|---|---|")
    for name, *_ in rows:
        col = "p_" + name[:2]
        bw, _ = V1.blend([col, "p_sp"], es[e_ok])
        pb = V1.blend([col, "p_sp"], t2, bw)[1]
        m, o, u = R9.horse_bets(t2, pb, t2.p_sp.values, price, 0.0, 1.3, (2, 15))
        guards = [("none", np.ones(len(t2), bool))]
        if "drift" in t2:
            guards.append((f"drift under {DRIFT_CAP:g}x", ~(t2.drift >= DRIFT_CAP).values))
        for gname, keep in guards:
            for hn, hm in (("1st", h2), ("2nd", ~h2), ("all", np.ones(len(t2), bool))):
                r = R9.summary(t2, m & keep & hm, o, u, price)
                if r["n"]:
                    print(f"| {name[:2]} | {gname} | {hn} | {r['n']:,} | {r['w']:,} | {r['ae']:.3f} | {r['flat']:+.1%} | "
                          f"{r['staked']:,.0f} | {r['kroi']:+.1%} | {r['kunits']:+,.0f} |")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 20")
