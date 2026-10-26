"""Benter-style two-stage greyhound model on the free files (26 Oct 2026, founder: "Are we doing a Benter style model?"
then "Yes" to restructuring). Same data and point-in-time features as gbm_v0.py; what changes is which model sees what.

    python research/greyhound/gbm_benter.py DIR LABEL        (a LABEL containing since=YYYY-MM-DD keeps races from that day)

STAGE 1, FUNDAMENTAL (Benter's multinomial logit, here LightGBM with the race softmax): form only, trained on WHO WON.
  No price of any kind: not the race's, and not the dog's past BSPs. It must stand on its own so that stage 2 can
  measure what it adds to the market. Variants: with and without Iggy's early speed (Jan 2024 on only).
MARKET HISTORY (the brief's stage 2 input): the dog's past BSPs and how it ran against them, alone (with the track,
  state and grade as context), trained on winners.
COPY (the gallops recipe, gbm_v0's "soft"): everything, trained on BSP chances. Kept as a check, not as the model.
STAGE 2 (Benter's second logit): chance proportional to the product of each input's chance raised to a weight, weights
  fitted on the middle quarter and scored once on the last quarter (both halves), against the market alone. The market
  here is BSP and the pre-play WAP; when recorded opens exist, the opening price takes their place.
"""
import os, re, sys
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gbm_v0 import CAT, IGGY, blend_apply, blend_fit, build, fit, ll, race_softmax   # noqa: E402

FUND = ["box", "field", "DISTANCE", "box_ratio", "runs", "wins", "win_rate", "place_rate", "prev_won", "prev_placed",
        "won_s5", "placed_s5", "days_since", "prev_TAB_NUMBER", "dist_change", "same_track", "elo"]
MKT = ["prev_lbsp", "lbsp_m5", "lbsp_min5", "surprise_s5", "runs", "days_since"]
REL = {"elo", "box_ratio", "win_rate", "place_rate", "days_since", "early_speed", "prev_lbsp", "lbsp_m5", "lbsp_min5",
       "surprise_s5"}


def features(df, cols, cats=True):
    cols = list(dict.fromkeys(cols))                       # FUND + MKT share a couple of columns
    X = df[cols].astype(float).copy()
    for c in cols:
        if c in REL:
            X[f"{c}_rel"] = X[c] - X[c].groupby(df.WIN_MARKET_ID).transform("mean")
    if cats:
        for c in CAT:
            X[c] = df[c].astype("category")
    return X


def main(d, label):
    df = build(d)
    m = re.search(r"since=(\d{4}-\d{2}-\d{2})", label)
    if m:
        df = df[df.date >= m.group(1)].reset_index(drop=True)
    has_es = "early_speed" in df and df.early_speed.notna().mean() > 0.5
    q50, q75 = df.date.quantile(0.5), df.date.quantile(0.75)
    tr, va, te = df[df.date < q50], df[(df.date >= q50) & (df.date < q75)].copy(), df[df.date >= q75].copy()
    print(f"# {label}: Benter two-stage\n\nraces {df.WIN_MARKET_ID.nunique():,}; stage 1 fit before {q50:%Y-%m-%d} "
          f"({tr.WIN_MARKET_ID.nunique():,}), stage 2 weights {q50:%Y-%m-%d} to {q75:%Y-%m-%d} "
          f"({va.WIN_MARKET_ID.nunique():,}), scored from {q75:%Y-%m-%d} ({te.WIN_MARKET_ID.nunique():,}); "
          f"early speed {'in' if has_es else 'not available in this window'}\n")

    specs = [("stage 1: form only", FUND, True, "won"),
             ("market history only", MKT, True, "won"),
             ("copy of BSP (check)", FUND + MKT, True, "p_bsp")]
    if has_es:
        specs.insert(1, ("stage 1: form + early speed", FUND + IGGY, True, "won"))
    cols = {}
    for name, fcols, cats, target in specs:
        Xtr, Xva, Xte = (features(x, fcols, cats) for x in (tr, va, te))
        bst, k = fit(Xtr, tr[target].values.astype(float), tr.WIN_MARKET_ID, (Xva, va.won.values, va.WIN_MARKET_ID))
        c = "p_" + re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
        va[c] = race_softmax(bst.predict(Xva, num_iteration=k, raw_score=True), va.WIN_MARKET_ID)
        te[c] = race_softmax(bst.predict(Xte, num_iteration=k, raw_score=True), te.WIN_MARKET_ID)
        cols[name] = c
        imp = pd.Series(bst.feature_importance("gain"), index=Xtr.columns).sort_values(ascending=False)
        print(f"{name}: {k} rounds; top inputs: " + ", ".join(f"{i} {v / imp.sum():.0%}" for i, v in imp.head(6).items()))

    need = ["p_wap"] + (["p_iggy"] if "p_iggy" in te else [])
    ok = pd.Series(True, index=te.index)
    for c in need:
        ok &= te[c].notna().groupby(te.WIN_MARKET_ID).transform("all")
    s = te[ok]
    vok = va["p_wap"].notna().groupby(va.WIN_MARKET_ID).transform("all")
    v = va[vok]
    mid = s.date.quantile(0.5)
    h1, h2 = s[s.date < mid], s[s.date >= mid]

    def row(name, p_all):
        p = pd.Series(p_all, index=s.index)
        return (f"| {name} | {ll(p.values, s.won.values):.4f} | {ll(p[h1.index].values, h1.won.values):.4f} | "
                f"{ll(p[h2.index].values, h2.won.values):.4f} |")

    print(f"\n## Stage 1 alone, last quarter, the same {s.WIN_MARKET_ID.nunique():,} races (winner log loss)\n")
    print("| price | all | first half | second half |\n|---|---|---|---|")
    for name, c in list(cols.items()) + ([("Iggy", "p_iggy")] if "p_iggy" in s else []) + \
            [("pre-play WAP", "p_wap"), ("BSP", "p_bsp")]:
        print(row(name, s[c].values))

    print("\n## Stage 2: blends fitted on the middle quarter, scored on the last\n")
    print("| blend | weights | all | first half | second half | gain on the market alone |\n|---|---|---|---|---|---|")
    f1 = cols.get("stage 1: form + early speed", cols["stage 1: form only"])
    for mkt in ("p_wap", "p_bsp"):
        base = ll(s[mkt].values, s.won.values)
        for parts in ([f1, mkt], [cols["market history only"], mkt], [f1, cols["market history only"], mkt]):
            w = blend_fit(parts, v)
            p = blend_apply(w, parts, s)
            names = " + ".join({c: n for n, c in cols.items()}.get(c, c[2:].upper()) for c in parts)
            r = row(names, p)
            r = r.replace(f"| {names} |", f"| {names} | {' / '.join(f'{x:.3f}' for x in w)} |", 1)
            print(r + f" {base - ll(p, s.won.values):+.4f} |")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "greyhounds")
