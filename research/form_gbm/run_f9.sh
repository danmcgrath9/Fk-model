set -e
python3 oof2_f9.py nn
python3 oof2_f9.py cb
python3 blend_f9.py
sed 's/p_oof_blend3.npy/p_oof_blend9.npy/' t_trial_s2.py | sed 's/"stage-2 v3 (sections)"/"blend9 + stage-2 v3"/; s/"+ trial form"/"blend9 + stage-2 v4"/' > t_b9_s2.py
python3 t_b9_s2.py | tail -2
python3 train_all_f9.py
python3 cb_all_f9.py
echo ALLDONE
