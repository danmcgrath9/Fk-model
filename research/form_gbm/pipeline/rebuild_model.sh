#!/bin/bash
# rebuild_model.sh SCRATCH: rebuild the model work folder after a restart, on the LIVE model.
# THE LIVE MODEL IS v10, the challenger retrained 15 Oct 2026 (trained through 14 Oct, 809 inputs; live from Bendigo
# 17 Oct, research/form_gbm/README.md "v10 LIVE"). The models branch ROOT still holds the old v9 copy and the branch is
# force-pushed every night, so the live files are only in commit 9d6fdfc (its challenger/ folder), which no branch points
# at any more: GitHub still serves it by its full SHA (fetched 10 Nov), but an unreferenced commit is not guaranteed.
# Rebuilding from the branch root prices on v9: on 10 Nov that moved Seymour's prices by a median 8% before it was caught.
# Check after a rebuild: re-price a meeting already priced on the live model; every price must match to the digit.
set -e
S=${1:?usage: rebuild_model.sh SCRATCH}; R=/home/user/fk-model/research/form_gbm; C=9d6fdfc2cd2d5aef89a06a9386257bc1e80fd53c
cd /home/user/fk-model
git cat-file -e $C 2>/dev/null || git fetch -q origin $C
mkdir -p $S/model/ds
cp $R/*.py $R/*_names.txt $R/models/drift_* $S/model/
cp $R/pipeline/F9_names_live.txt $S/model/F9_names.txt; cp $R/pipeline/late_feats.py $S/model/
cp $R/pipeline/*.sh $R/pipeline/*.py $R/pipeline/*.js $S/
for f in $(git ls-tree -r --name-only $C challenger/); do git show $C:$f > $S/model/${f#challenger/}; done
cd $S/model && gunzip -f all9_*.txt.gz S_hist.npy.gz model_ds.npz.gz && mv -f model_ds.npz ds/model_ds.npz
python3.13 -c "import lightgbm, catboost, torch" 2>/dev/null || python3.13 -m pip install -q lightgbm catboost torch
python3.13 late_feats.py
python3.13 -c "
import numpy as np, lightgbm as lgb, json
h=np.load('ds/model_ds.npz',allow_pickle=True); n=len(open('F9_names.txt').read().split(chr(10)))
print('model folder:', json.load(open('metrics.json'))['trained_through'], 'trees take', lgb.Booster(model_file='all9_rg0.txt').num_feature(),
      'inputs, name list', n, ', history', len(h['race_idx']), 'runners to', max(h['date'].astype(str)))"
