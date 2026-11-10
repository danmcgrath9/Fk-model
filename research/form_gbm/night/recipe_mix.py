"""Does mixing RECIPES beat adding seeds? (night of 10 Nov 2026)
Every queue arm that kept all 809 inputs and scored inside the noise of the live settings is a different set of trees.
Averaging them (log prices, renormalised) is an ensemble of settings rather than of seeds. Compared at the same number
of trees models against the live settings on 10 seeds (queue 4), on both folds, alone and inside the full blend.
    python3.13 recipe_mix.py   (night folder, after the queues; reads preds/ only)"""
import itertools, numpy as np
import nl
sm_ = nl.b.softmax_races; L_ = lambda p: np.log(np.maximum(p, 1e-12)); avg = lambda ps: sm_(np.mean([L_(p) for p in ps], 0))
hm = {f: (nl.date >= nl.FOLDS[f][1]) & (nl.date < nl.FOLDS[f][2]) for f in "AB"}
ld = lambda n, f: np.load(f"preds/{n}_{f}.npy").astype(float)
ARMS = ["base", "base_s10", "base_s20", "md50", "md200", "md400", "l2_1", "l2_50", "ff10", "ff35", "bag60", "nl31", "r6000", "lr03_r8000", "aug_40", "w_book"]
SETS = {"live settings, 3 seeds": ["base"], "live settings, 9 seeds (three seed sets)": ["base", "base_s10", "base_s20"],
        "live settings, 10 seeds (queue 4)": ["seeds10"],
        "3 recipes x 3 seeds: live, min leaf 200, feature share 0.35": ["base", "md200", "ff35"],
        "3 recipes x 3 seeds: live, slow, 31 leaves": ["base", "lr03_r8000", "nl31"],
        "6 recipes x 3 seeds: live, slow, 31 leaves, min leaf 50, min leaf 400, feature share 0.1": ["base", "lr03_r8000", "nl31", "md50", "md400", "ff10"],
        "all 14 full-input recipes x 3 seeds": [a for a in ARMS if a not in ("base_s10", "base_s20")],
        "slow, 5 seeds (queue 4)": ["slow5"], "slow 5 seeds + live 10 seeds": ["slow5", "seeds10"],
        "slow 5 + live 10 + 31 leaves + feature share 0.1 + min leaf 400": ["slow5", "seeds10", "nl31", "ff10", "md400"]}
print("| softmax trees | fold A: KL / log loss / profit | fold B: KL / log loss / profit |\n|---|---|---|")
P = {}
for lab_, arms in SETS.items():
    cells = []
    for f in "AB":
        p = avg([ld(a, f) for a in arms]); P[(lab_, f)] = p; cells.append(f"{nl.kl(p, hm[f]):.4f} / {nl.ll(p, hm[f]):.4f} / {nl.run(p, hm[f])[3]:+.0f}u")
    print(f"| {lab_} | " + " | ".join(cells) + " |", flush=True)
# how different are two recipes, against two seed sets of one recipe?
for f in "AB":
    d = lambda a, b_: 100 * np.median(np.abs(np.log(ld(a, f)[hm[f]] / ld(b_, f)[hm[f]])))
    print(f"fold {f}: median runner-by-runner gap between two 3-seed sets of the live settings {d('base', 'base_s10'):.1f}%; live v slow {d('base', 'lr03_r8000'):.1f}%; "
          f"live v 31 leaves {d('base', 'nl31'):.1f}%; live v feature share 0.1 {d('base', 'ff10'):.1f}%; live v min leaf 400 {d('base', 'md400'):.1f}%")
# inside the full blend (regression trees 3 seeds, network 3 seeds, CatBoost 1 seed, live weights)
print("\n| softmax trees inside the full blend | fold A: KL / log loss / profit | fold B |\n|---|---|---|")
for lab_ in ("live settings, 3 seeds", "live settings, 10 seeds (queue 4)", "slow, 5 seeds (queue 4)", "all 14 full-input recipes x 3 seeds", "slow 5 + live 10 + 31 leaves + feature share 0.1 + min leaf 400"):
    cells = []
    for f in "AB":
        t = sm_(0.7 * L_(P[(lab_, f)]) + 0.3 * L_(ld("m_rg", f))); p = sm_(0.5 * L_(t) + 0.3 * L_(ld("m_nn", f)) + 0.2 * L_(ld("m_cb", f)))
        cells.append(f"{nl.kl(p, hm[f]):.4f} / {nl.ll(p, hm[f]):.4f} / {nl.run(p, hm[f])[3]:+.0f}u")
    print(f"| {lab_} | " + " | ".join(cells) + " |", flush=True)
