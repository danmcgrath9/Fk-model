#!/bin/bash
# refresh_history.sh MODEL_DIR: bring the day pricer's HISTORY up to date without touching the live models.
# The live model files (trees, CatBoost, stage 2: v10, trained through 14 Oct) stay as they are. What is replaced is the
# history they read while pricing a day: ds/model_ds.npz (every resulted race), S_hist.npy (its section splits) and
# p_oof_blend9.npy (the out-of-fold prices the second stage measures "what did the market think of this horse / trainer
# / jockey last time" against). The nightly retrain (fk-retrain) rebuilds all three through yesterday and puts them in
# the models branch's challenger/ folder; nothing copied them into the pricing folder, so from 15 Oct every live price
# was built on history that stopped at 14 Oct. Replay on 15 Oct - 9 Nov (research/form_gbm/night/replay_stale.py): the
# fresh history is 1.7% closer to BSP overall and 3% closer in weeks three and four (t = 3.1), nothing in the first two.
# The old files are kept beside the new ones as *.stale-YYYYMMDD so the switch can be undone by copying them back.
set -e
M=${1:?usage: refresh_history.sh MODEL_DIR}; cd /home/user/fk-model
git fetch -q origin models
T=$(mktemp -d)
for f in model_ds.npz.gz S_hist.npy.gz p_oof_blend9.npy metrics.json; do git show origin/models:challenger/$f > $T/$f; done
gunzip -f $T/model_ds.npz.gz $T/S_hist.npy.gz
python3.13 - "$T" "$M" <<'PY'
import json, sys, numpy as np
t, m = sys.argv[1:3]
z = np.load(f"{t}/model_ds.npz", allow_pickle=True); s = np.load(f"{t}/S_hist.npy", mmap_mode="r"); p = np.load(f"{t}/p_oof_blend9.npy")
old = np.load(f"{m}/ds/model_ds.npz", allow_pickle=True)
n = len(z["race_idx"]); last = max(z["date"].astype(str)); met = json.load(open(f"{t}/metrics.json"))
assert len(p) == n == s.shape[0], f"history files do not line up: {n} runners, {len(p)} prices, {s.shape[0]} section rows"
assert list(z["cols"]) == list(old["cols"]), "the new history's columns differ from the live folder's: do not refresh, the live model's inputs would change"
assert np.allclose(np.bincount(z["race_idx"], weights=p), 1, atol=1e-5), "out-of-fold prices do not sum to 1 per race"
assert last >= max(old["date"].astype(str)), "the new history is older than the one in the folder"
print(f"history: {len(old['race_idx'])} runners to {max(old['date'].astype(str))}  ->  {n} runners to {last} (retrain of {met['trained_utc']})")
PY
D=$(date +%Y%m%d)
for f in ds/model_ds.npz S_hist.npy p_oof_blend9.npy; do [ -f $M/$f.stale-$D ] || cp $M/$f $M/$f.stale-$D; done
cp $T/model_ds.npz $M/ds/model_ds.npz; cp $T/S_hist.npy $M/S_hist.npy; cp $T/p_oof_blend9.npy $M/p_oof_blend9.npy
(cd $M && python3.13 late_feats.py | tail -1)
rm -rf $T; echo "history refreshed in $M (live model files untouched)"
