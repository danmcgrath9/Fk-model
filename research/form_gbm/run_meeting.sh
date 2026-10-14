#!/bin/bash
# One meeting, end to end, on the LIVE model (v9, this directory): final field -> prices -> order file.
# usage: run_meeting.sh PREFIX GTAG UP_NPZ      e.g. run_meeting.sh 2026-10-17-bendigo g4 up17/bendigo.npz
# FK_MODEL_DIR = the directory holding the live (v9) models, name lists and training set; LOUT = write to a test directory instead
# needs data/live_bets/PREFIX-prices-fields.txt (mkfields.py) and PREFIX-entry-numbers.txt (entry_numbers.py)
set -euo pipefail
P=$1; G=$2; U=$3
S=${FK_MODEL_DIR:?set FK_MODEL_DIR to the live model directory (v9 models, ds/model_ds.npz)}; L=${LOUT:-/home/user/fk-model/data/live_bets}; LF=/home/user/fk-model/data/live_bets; R=/home/user/fk-model/research/form_gbm
B=$L/$P-$G; US=${U%.npz}_s.npz
cd $S
test -f $LF/$P-prices-fields.txt || { echo "no $P-prices-fields.txt"; exit 1; }
python3.13 drop_scr.py $U $LF/$P-prices-fields.txt $US | tail -1
# jockeys and gear land after the fields (15 Oct 2026): name every runner still without a rider before pricing
python3.13 -c "
import numpy as np,sys; U=np.load('$US',allow_pickle=True); j=U['jockey'].astype(str); r=U['race_number'][U['race_idx']]
g=U['X'][:,list(U['cols']).index('gear_changes')]; b=[f'R{int(x)} {n}' for x,n,jj in zip(r,U['name'],j) if not jj.strip()]
print(f'jockeys: {len(j)-len(b)} of {len(j)} runners have one; gear changes posted on {int((g>0).sum())}'); b and print('  no jockey: '+', '.join(b))"
python3.13 price_day3.py $US $B-v5s1.json > ${U%.npz}_pd3.log 2>&1 || { tail -5 ${U%.npz}_pd3.log; exit 1; }
grep -E "missing a last-start|rows" ${U%.npz}_pd3.log
python3.13 apply_stage2f.py $B-v5s1.json $US $B-v6.json p_oof_blend9.npy > ${U%.npz}_s2.log 2>&1 || { tail -5 ${U%.npz}_s2.log; exit 1; }
python3.13 shade_back.py $B-v6.json $US | tail -1
python3.13 angles_day.py $US $B-angles.json | tail -1
python3.13 fs_json.py $US $B-first-starters.json
python3.13 fu_json.py $US $B-first-up-blocks.json > ${U%.npz}_fu.log; head -1 ${U%.npz}_fu.log
[ -n "${LOUT:-}" ] && exit 0; cd $R && python3.13 betmatic_orders.py $P $G $L/$P-betmatic-preopen.csv | tail -4
