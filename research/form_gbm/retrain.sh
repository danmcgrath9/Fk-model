#!/usr/bin/env bash
# Full v5 retrain on the dataset in ds/model_ds.npz (run from research/form_gbm). Writes the
# stage-1 models (all9_sm*, all9_rg*, cb_all9.cbm), stage 2 (stage2e_*), the OOF blend and
# holdout.txt with the stage-2 holdout KL that the deploy gate compares.
set -euo pipefail
python3 -c "import numpy as np; z=np.load('ds/model_ds.npz',allow_pickle=True); np.save('S_hist.npy',z['S']); np.save('S_fields.npy',z['sec_fields']); print('races',len(z['race_id']),'to',max(z['date']))"
python3 build_f9.py
python3 oof_trees.py
python3 oof2_f9.py nn
python3 oof2_f9.py cb
python3 blend_f9.py
python3 t_b9_s2.py | tee t_b9_s2.out | tail -2
grep "stage-2 v4" t_b9_s2.out | sed -E 's/.*KL ([0-9.]+).*/\1/' > holdout.txt
python3 stage2e_train.py p_oof_blend9.npy 400
python3 stage2f_train.py p_oof_blend9.npy 400
python3 train_all_f9.py
python3 cb_all_f9.py
echo "holdout KL $(cat holdout.txt)"
