"""Greyhound betting angles at BSP, every one in two date halves and after commission (26 Oct 2026, founder: "find
betting angles like our horse bets where we can send pre market slips to betmatic").

    python research/greyhound/t_angles.py DIR LABEL        (DIR: the ANZ_Greyhounds files and the Iggy files)

WHY BSP: no history of TAB's greyhound opening price exists, and the angles that go to BetMatic fire at the open. BSP is
the sharpest price there is (Test 1), so an angle that holds at BSP is a candidate for the open; one that fails at BSP
can still work at a softer open, and that test waits for recorded opens. Nothing here is a bet list.

THE RULES (the brief's): an angle is believed only if it is positive after commission in BOTH date halves; A/E is shown
beside ROI; every angle tried is printed, including the ones that fail, because this file tests many and a few will
look good by chance. Backs: flat 1 unit at BSP, commission COMM on each winning bet's profit. Lays: 1 unit of the
backer's stake at BSP, commission on each winning lay's 1-unit profit; ROI is per unit of backer's stake (liability is
BSP - 1 per bet, so a lay ROI is not comparable to a back ROI one for one).

MODEL ANGLES use v0 + Elo (the best model so far, Test 5) and the stage-1 form-only model (Test 6), fitted before the
50th percentile date, scored on the last quarter only, halves inside it. STRUCTURAL ANGLES need no fitting (the box
rate and the Elo are point-in-time) and are scored over the whole period, halves at the median date.
"""
import os, re, sys
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gbm_v0 import build, features as v0_features, fit, race_softmax          # noqa: E402
from gbm_benter import FUND, features as b_features                           # noqa: E402

COMM = 0.08


def back(x):
    w = x.won == 1
    return np.where(w, (x.WIN_BSP - 1) * (1 - COMM), -1.0)


def lay(x):
    w = x.won == 1
    return np.where(w, -(x.WIN_BSP - 1), 1 - COMM)


def table(title, angles, df, half_col):
    print(f"\n## {title}\n")
    print("| angle | side | bets 1st / 2nd half | A/E 1st / 2nd | ROI after commission 1st / 2nd | holds both halves |")
    print("|---|---|---|---|---|---|")
    for name, side, mask in angles:
        x = df[mask]
        cells, rois = [], []
        for h in (True, False):
            y = x[x[half_col] == h]
            if len(y) == 0:
                cells.append((0, np.nan, np.nan)); rois.append(np.nan); continue
            ae = y.won.sum() / (1 / y.WIN_BSP).sum()
            r = (back(y) if side == "back" else lay(y)).mean()
            cells.append((len(y), ae, r)); rois.append(r)
        holds = all(r > 0 for r in rois if not np.isnan(r)) and not any(np.isnan(rois))
        print(f"| {name} | {side} | {cells[0][0]:,} / {cells[1][0]:,} | {cells[0][1]:.3f} / {cells[1][1]:.3f} | "
              f"{cells[0][2]:+.1%} / {cells[1][2]:+.1%} | {'YES' if holds else 'no'} |")


def main(d, label):
    df = build(d)
    df["first_half"] = df.date < df.date.quantile(0.5)
    df["elo_rank"] = df.groupby("WIN_MARKET_ID").elo.rank(ascending=False, method="min")
    df["bsp_rank"] = df.groupby("WIN_MARKET_ID").WIN_BSP.rank(method="min")
    print(f"# {label}: greyhound angles at BSP\n\nraces {df.WIN_MARKET_ID.nunique():,}, runners {len(df):,}, "
          f"{df.date.min():%Y-%m-%d} to {df.date.max():%Y-%m-%d}; commission {COMM:.0%}")

    b = df.WIN_BSP
    strong_b1 = df.box_ratio >= 1.5 * 1.0            # box rate at least 1.5x the all-box average (point-in-time)
    structural = [
        ("all runners", "back", b > 1),
        ("lay every runner over $51", "lay", b > 51),
        ("lay every runner $31-$51", "lay", (b > 31) & (b <= 51)),
        ("lay every runner $21-$31", "lay", (b > 21) & (b <= 31)),
        ("back favourites (BSP rank 1)", "back", df.bsp_rank == 1),
        ("box 1, strong-box track/distance (box rate >= 1.5x)", "back", (df.box == 1) & strong_b1),
        ("lay box 8 at a weak-box-8 track/distance (box rate <= 0.8x)", "lay", (df.box == 8) & (df.box_ratio <= 0.8)),
        ("top Elo in the race, BSP rank 3+", "back", (df.elo_rank == 1) & (df.bsp_rank >= 3) & (df.runs >= 5)),
        ("top Elo, BSP rank 3+, under $11", "back", (df.elo_rank == 1) & (df.bsp_rank >= 3) & (b < 11) & (df.runs >= 5)),
        ("lay BSP favourite with Elo rank 5+", "lay", (df.bsp_rank == 1) & (df.elo_rank >= 5) & (df.runs >= 5)),
        ("first-up after 28+ days, under $6", "back", (df.days_since >= 28) & (b < 6)),
        ("lay first-up after 28+ days, under $4", "lay", (df.days_since >= 28) & (b < 4)),
        ("distance up 100m+", "back", df.dist_change >= 100),
        ("distance down 100m+", "back", df.dist_change <= -100),
        ("first start in the files (no history), under $6", "back", (df.runs == 0) & (b < 6)),
    ]
    table("Structural angles, whole period", structural, df, "first_half")

    # model angles: fit as in Tests 5 and 6, score the last quarter
    q50, q75 = df.date.quantile(0.5), df.date.quantile(0.75)
    tr, va, te = df[df.date < q50], df[(df.date >= q50) & (df.date < q75)], df[df.date >= q75].copy()
    te["half"] = te.date < te.date.quantile(0.5)
    Xtr, Xva, Xte = (v0_features(x, False) for x in (tr, va, te))
    bst, k = fit(Xtr, tr.p_bsp.values, tr.WIN_MARKET_ID, (Xva, va.won.values, va.WIN_MARKET_ID))
    te["p_v0"] = race_softmax(bst.predict(Xte, num_iteration=k, raw_score=True), te.WIN_MARKET_ID)
    Xtr, Xva, Xte = (b_features(x, FUND) for x in (tr, va, te))
    bst, k = fit(Xtr, tr.won.values.astype(float), tr.WIN_MARKET_ID, (Xva, va.won.values, va.WIN_MARKET_ID))
    te["p_form"] = race_softmax(bst.predict(Xte, num_iteration=k, raw_score=True), te.WIN_MARKET_ID)
    print(f"\nmodel angles scored on {te.WIN_MARKET_ID.nunique():,} races from {q75:%Y-%m-%d}")
    model = []
    for col, nm in (("p_v0", "v0 + Elo"), ("p_form", "stage 1 form only")):
        edge = te[col] * te.WIN_BSP                    # our chance x BSP: above 1 = BSP looks too big to us
        for kk, lo, hi in ((1.2, 1, 1e9), (1.5, 1, 1e9), (1.2, 2, 8), (1.5, 2, 8), (1.2, 8, 21)):
            model.append((f"{nm}: back, chance x BSP >= {kk}, BSP ${lo:g}-${hi:g}" if hi < 1e8 else
                          f"{nm}: back, chance x BSP >= {kk}", "back",
                          (edge >= kk) & (te.WIN_BSP >= lo) & (te.WIN_BSP < hi)))
        for kk, lo, hi in ((0.6, 1, 6), (0.5, 1, 11), (0.5, 11, 1e9)):
            model.append((f"{nm}: lay, chance x BSP <= {kk}, BSP ${lo:g}-${hi:g}" if hi < 1e8 else
                          f"{nm}: lay, chance x BSP <= {kk}, BSP ${lo:g}+", "lay",
                          (edge <= kk) & (te.WIN_BSP >= lo) & (te.WIN_BSP < hi)))
    table("Model angles, last quarter", model, te, "half")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "greyhounds")
