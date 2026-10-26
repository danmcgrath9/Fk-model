"""Harness price from the market's own history of each horse, scored against BSP (25 Oct 2026).

    python research/harness/hx_model.py DIR LABEL      (DIR = Betfair's free ANZ harness files)

What it may use: only what hx_data.history() builds from races that started BEFORE this one (the horse's past BSP
chances, results, in-running lows, days since, changes of distance/track/gait) plus what is on the field (track,
distance, gait, TAB number, field size). No current-race price, volume or result. No driver, trainer, margin or time:
Betfair does not carry them.

Recipe, as the gallops model (research/form_gbm): LightGBM trees plus a logistic regression, each renormalised per race,
blended with a weight chosen on the validation months. Train: races to 2024-06-30. Validation (early stopping, blend
weight): 2024-07-01 to 2024-12-31. Holdout, never seen in fitting: 2025-01-01 on, split into two date halves.
Australian races only, each with a BSP on every starter and exactly one winner.

Scores (lower = better): winner log loss, and KL from BSP to the price (how far the price is from BSP), each by month
and by half, against equal chances, the pre-play WAP and BSP itself. A price that is "close to BSP" has a small KL.
Writes DIR/hx_preds.parquet (holdout and validation runners with every price) for hx_angles.py."""
import os, sys
import numpy as np, pandas as pd
import lightgbm as lgb
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hx_data import load, history, FEATURES, FEATURES_V2, FEATURES_V3, CATS, renorm

TRAIN_END, VALID_END = "2024-07-01", "2025-01-01"


def winner_ll(p, won, race):
    x = pd.Series(p)[np.asarray(won) == 1]
    return float(-np.log(np.clip(x, 1e-6, 1)).mean())


def kl_to_bsp(p, q, race):
    """Mean over races of sum q*log(q/p): q = BSP chance, p = the price being scored."""
    t = pd.Series(np.asarray(q) * np.log(np.clip(q, 1e-9, 1) / np.clip(p, 1e-9, 1)))
    return float(t.groupby(np.asarray(race)).sum().mean())


def fit(tr, va, ho, feats):
    """Trees and a logistic regression on these inputs, each renormalised per race, blended on validation log loss."""
    X = feats + CATS
    m = lgb.LGBMClassifier(n_estimators=3000, learning_rate=0.03, num_leaves=63, min_child_samples=200,
                           subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0, verbose=-1)
    m.fit(tr[X], tr.won, eval_set=[(va[X], va.won)], callbacks=[lgb.early_stopping(100, verbose=False)])
    lr = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(max_iter=2000, C=0.5))
    lr.fit(tr[feats], tr.won)
    out = []
    for part in (va, ho):
        part = part.copy()
        part["p_tree"] = renorm(m.predict_proba(part[X], num_iteration=m.best_iteration_)[:, 1], part.race)
        part["p_lr"] = renorm(lr.predict_proba(part[feats])[:, 1], part.race)
        out.append(part)
    va, ho = out
    best = min(np.arange(0, 1.01, 0.1), key=lambda w: winner_ll(
        renorm(np.exp(w * np.log(va.p_tree) + (1 - w) * np.log(va.p_lr)), va.race), va.won, va.race))
    for part in (va, ho):
        part["p_model"] = renorm(np.exp(best * np.log(part.p_tree) + (1 - best) * np.log(part.p_lr)), part.race)
        part["p_equal"] = 1 / part.field
    print(f"{len(feats)} inputs: trees {m.best_iteration_} rounds; blend {best:.1f} trees + {1 - best:.1f} logistic")
    return va, ho, m, best


def softmax_race(score, race, t):
    e = pd.Series(np.exp(t * (np.asarray(score) - pd.Series(score).groupby(np.asarray(race)).transform("max").to_numpy())))
    return (e / e.groupby(np.asarray(race)).transform("sum")).to_numpy()


def fit_rank(tr, va, ho, feats):
    """A ranking model per race (LightGBM lambdarank; winner 2, placed 1, the rest 0), turned into chances with a
    per-race softmax whose temperature is fitted on validation log loss. Uses the place result the win model ignores."""
    X = feats + CATS
    rel = lambda d: (d.won + d.placed).clip(upper=2).astype(int)
    grp = lambda d: d.groupby("race", sort=False).size().to_numpy()
    m = lgb.LGBMRanker(objective="lambdarank", n_estimators=3000, learning_rate=0.03, num_leaves=63,
                       min_child_samples=200, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, verbose=-1)
    m.fit(tr[X], rel(tr), group=grp(tr), eval_set=[(va[X], rel(va))], eval_group=[grp(va)], eval_at=[1, 3],
          callbacks=[lgb.early_stopping(100, verbose=False)])
    out = []
    for part in (va, ho):
        part = part.copy(); part["score"] = m.predict(part[X], num_iteration=m.best_iteration_); out.append(part)
    va, ho = out
    t = min(np.arange(0.2, 5.01, 0.1), key=lambda t: winner_ll(softmax_race(va.score, va.race, t), va.won, va.race))
    for part in (va, ho):
        part["p_model"] = softmax_race(part.score, part.race, t); part["p_equal"] = 1 / part.field
        part["p_tree"] = part.p_model; part["p_lr"] = part.p_model
    print(f"{len(feats)} inputs, ranking: {m.best_iteration_} rounds, softmax temperature {t:.1f}")
    return va, ho, m, t


def main(d, label):
    df = history(load(d))
    df = df[df.STATE_CODE != "NZ"]
    g = df.groupby("race")
    ok = g.WIN_BSP.transform(lambda s: (s > 1).all()) & (g.won.transform("sum") == 1) & (df.field >= 4)
    df = df[ok].copy()
    for c in CATS:
        df[c] = df[c].astype("category")
    tr, va, ho = df[df.date < TRAIN_END], df[(df.date >= TRAIN_END) & (df.date < VALID_END)], df[df.date >= VALID_END]
    print(f"# {label}: market-history model v BSP\n")
    print(f"races: train {tr.race.nunique():,} (to {TRAIN_END}), validation {va.race.nunique():,}, "
          f"holdout {ho.race.nunique():,} ({ho.date.min():%Y-%m-%d} to {ho.date.max():%Y-%m-%d})")
    results = {}
    for name, feats in (("v1", FEATURES), ("v2", FEATURES_V2), ("v3", FEATURES_V3)):
        results[name] = fit(tr, va, ho, feats)
    results["v3, ranking"] = fit_rank(tr, va, ho, FEATURES_V3)
    dates = np.sort(ho.date.unique()); cut = dates[len(dates) // 2]
    print(f"\n## v1, v2, v3 on the holdout, split at {pd.Timestamp(cut):%Y-%m-%d}\n")
    print("| inputs | LL 1st half | LL 2nd half | KL to BSP 1st half | KL 2nd half | gap closed, all holdout |\n"
          "|---|---|---|---|---|---|")
    for name, (_, h, _, _) in results.items():
        h1, h2 = h[h.date < cut], h[h.date >= cut]
        le, lm, lb = (winner_ll(h[c], h.won, h.race) for c in ("p_equal", "p_model", "p_bsp"))
        print(f"| {name} | {winner_ll(h1.p_model, h1.won, h1.race):.4f} | {winner_ll(h2.p_model, h2.won, h2.race):.4f} | "
              f"{kl_to_bsp(h1.p_model, h1.p_bsp, h1.race):.4f} | {kl_to_bsp(h2.p_model, h2.p_bsp, h2.race):.4f} | "
              f"{(le - lm) / (le - lb):.1%} |")
    pick = min(results, key=lambda k: winner_ll(results[k][0].p_model, results[k][0].won, results[k][0].race))
    va, ho, m, best = results[pick]
    X = (FEATURES_V3 if pick.startswith("v3") else FEATURES_V2 if pick == "v2" else FEATURES) + CATS
    print(f"\nDetail below is {pick}, the best on VALIDATION log loss (chosen before the holdout is looked at).\n")
    ho = ho.copy()
    ho["p_wap"] = ho.p_wap.where(ho.p_wap.notna().groupby(ho.race).transform("all"))
    ho["half"] = np.where(ho.date < cut, "first half", "second half")
    ho["month"] = ho.date.dt.strftime("%Y-%m")
    cols = [("equal chances", "p_equal"), ("trees", "p_tree"), ("logistic", "p_lr"), ("model (blend)", "p_model")]
    print(f"## Holdout, split at {pd.Timestamp(cut):%Y-%m-%d}\n")
    print("| price | winner log loss: 1st half | 2nd half | KL to BSP: 1st half | 2nd half |\n|---|---|---|---|---|")
    for name, c in cols + [("pre-play WAP", "p_wap"), ("BSP", "p_bsp")]:
        r = []
        for h in ("first half", "second half"):
            s = ho[ho.half == h]
            if c == "p_wap":
                s = s[s.p_wap.notna()]
            r.append(winner_ll(s[c], s.won, s.race))
        k = [kl_to_bsp(ho[(ho.half == h) & ho[c].notna()][c], ho[(ho.half == h) & ho[c].notna()].p_bsp,
                       ho[(ho.half == h) & ho[c].notna()].race) for h in ("first half", "second half")]
        print(f"| {name} | {r[0]:.4f} | {r[1]:.4f} | {k[0]:.4f} | {k[1]:.4f} |")
    print("\n## By month (holdout)\n")
    print("| month | races | LL equal | LL model | LL BSP | KL model to BSP | share of the equal-to-BSP gap closed |\n"
          "|---|---|---|---|---|---|---|")
    for mo, s in ho.groupby("month"):
        le, lm, lb = winner_ll(s.p_equal, s.won, s.race), winner_ll(s.p_model, s.won, s.race), winner_ll(s.p_bsp, s.won, s.race)
        print(f"| {mo} | {s.race.nunique():,} | {le:.4f} | {lm:.4f} | {lb:.4f} | {kl_to_bsp(s.p_model, s.p_bsp, s.race):.4f} | "
              f"{(le - lm) / (le - lb):.0%} |")
    imp = pd.Series(m.booster_.feature_importance("gain"), index=X).sort_values(ascending=False)
    print("\n## Tree inputs by gain (top 15)\n")
    for k, v in (imp / imp.sum()).head(15).items():
        print(f"- {k}: {v:.1%}")
    keep = ["race", "date", "half", "month", "horse", "TRACK", "STATE_CODE", "trot", "TAB_NUMBER", "field", "won",
            "placed", "WIN_BSP", "PLACE_BSP", "p_bsp", "p_wap", "p_model", "p_tree", "p_lr", "bsp_rank", "race_vol",
            "n_prev", "days_since", "last_close_lost", "last_won", "last_bsp_rank", "p_last1", "gait_change"]
    va = va.assign(half="validation", month=va.date.dt.strftime("%Y-%m"))
    pd.concat([va[keep], ho[keep]]).to_parquet(os.path.join(d, "hx_preds.parquet"))
    print(f"\nwrote {os.path.join(d, 'hx_preds.parquet')}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "harness")
