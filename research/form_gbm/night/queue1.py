"""Queue 1: training settings, the blanked copy, feature pruning and family ablations for the stage-1 trees.
    python3.13 queue1.py            (skips arms already in results.jsonl, so it can be stopped and restarted)"""
import os, sys, numpy as np
import nl, lab

F, NM = nl.F, nl.NM
Fb = lab.augmented(F, NM, share=1.0, seed=99)    # every gap column blanked: what a pull without benchmarks looks like
SM = ("early_pos", "early_x_tempo", "tempo_max", "tempo_min", "style_x_tempo", "map_vs_habit", "no_cover", "path_width", "wide_back")
PM = ("mkt_class", "beat_market", "beat_market_last", "raw_beat_market", "raw_beat_market_last")
gapc = set(lab.gap_cols(F, NM))
FAM = {
    "gear_detail": lambda n: n.startswith("gd_"),
    "price_moves": lambda n: n.startswith("fl_"),
    "bias": lambda n: n.startswith("bias_"),
    "track_surface_going": lambda n: n.startswith("tsg_"),
    "sire": lambda n: n.startswith(("sire_", "damsire_")),
    "head_to_head": lambda n: n.startswith("h_"),
    "speedmap": lambda n: n.startswith("sm_") or n in SM,
    "trials_sections": lambda n: n.startswith(("tr_", "sec_")),
    "our_encodings": lambda n: n.startswith(("trainer_", "jockey_", "jt_", "loc_")),
    "fk_jockey_trainer": lambda n: n.startswith(("jockeyForm_", "trainerForm_")),
    "past_market": lambda n: n.startswith(("e_lbsp", "x_pastp", "x_sp_bsp", "x_beat_price", "raw_mkt_class")) or n in PM,
    "field_relative": lambda n: "__" in n,
    "fk_form_records": lambda n: n.startswith("f_"),
    "neural": lambda n: "neural" in n,
    "speed_sectionals": lambda n: NM.index(n) in gapc,
}
# BSP book per race: a thin Betfair market sums far from 1
inv = np.where(np.isfinite(nl.bs) & (nl.bs > 1), 1 / np.where(nl.bs > 1, nl.bs, 2.0), 0.0)
book = np.bincount(nl.ri, weights=inv, minlength=nl.nR)
wbook = np.clip(1 - 4 * np.abs(book - 1), 0.25, 1.0)[nl.ri]

EXP = [("base", {}, "live settings, seeds 0-2")]
EXP += [(f"base_s{s}", dict(seeds=(s, s + 1, s + 2)), "noise floor: the same model on other seeds") for s in (10, 20)]
EXP += [("aug_none", dict(aug=False), "no blanked copy"), ("aug_40", dict(aug_share=0.4), "blanked copy on 40% of runners, not 80%")]
EXP += [(f"md{v}", dict(params=dict(min_data_in_leaf=v)), f"min_data_in_leaf {v} (live 100)") for v in (50, 200, 400)]
EXP += [(f"top{k}", dict(top=k), f"only the {k} inputs with the most gain in the base model of the same fold") for k in (400, 200)]
EXP += [(f"drop_{k}", dict(drop=k), f"without the {k} inputs") for k in FAM]
EXP += [("l2_1", dict(params=dict(lambda_l2=1.0)), "lambda_l2 1 (live 10)"), ("l2_50", dict(params=dict(lambda_l2=50.0)), "lambda_l2 50"),
        ("nl7", dict(params=dict(num_leaves=7)), "num_leaves 7 (live 15)"), ("nl31", dict(params=dict(num_leaves=31)), "num_leaves 31"),
        ("r2000", dict(rounds=2000), "2000 rounds (live 4000)"), ("r6000", dict(rounds=6000), "6000 rounds"),
        ("lr03_r8000", dict(rounds=8000, params=dict(learning_rate=0.03)), "learning rate 0.03, 8000 rounds"),
        ("ff10", dict(params=dict(feature_fraction=0.1)), "feature_fraction 0.1 (live 0.2)"), ("ff35", dict(params=dict(feature_fraction=0.35)), "feature_fraction 0.35"),
        ("bag60", dict(params=dict(bagging_fraction=0.6)), "bagging 0.6 (live 0.8)"), ("no_extra", dict(params=dict(extra_trees=False)), "extra_trees off"),
        ("w_book", dict(weight=wbook), "races weighted by how close the BSP book is to 100% (thin markets count less)"),
        ("seeds8", dict(seeds=tuple(range(8))), "8 seeds averaged (live 5, tests 3)")]
only = set(sys.argv[1:])
for name, kw, note in EXP:
    if only and name not in only: continue
    for fold in ("A", "B"):
        if nl.done(name, fold): continue
        kw2 = dict(kw); cols = list(range(len(NM)))
        if "drop" in kw2:
            pred = FAM[kw2.pop("drop")]; cols = [j for j, n in enumerate(NM) if not pred(n)]
        if "top" in kw2:
            k = kw2.pop("top"); g = np.load(f"gain_{fold}.npy"); cols = sorted(np.argsort(-g)[:k].tolist())
        names = [NM[j] for j in cols]; FF = F[:, cols]
        p, bst = nl.fit(FF, names, fold, **kw2)
        if name == "base": np.save(f"gain_{fold}.npy", bst.feature_importance("gain"))
        hm = nl.date >= nl.FOLDS[fold][1]; hm &= nl.date < nl.FOLDS[fold][2]
        ex = dict(inputs=len(cols))
        if name in ("base", "aug_none", "aug_40"):   # the same trees on a pull with the benchmark figures missing
            pb = nl.b.softmax_races(bst.predict(Fb[:, cols])); ex["kl_blank_1seed"] = nl.kl(pb, hm)
            ex["kl_full_1seed"] = nl.kl(nl.b.softmax_races(bst.predict(FF)), hm)
        nl.record(name, fold, p, note, ex)
print("queue 1 done")
