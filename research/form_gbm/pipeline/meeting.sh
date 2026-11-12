#!/bin/bash
# meeting.sh TAG NPZ DAYPREFIX GTAG "TITLE" "NOTE"
# Price one meeting on the live model (rebuilt 10 Nov 2026 after the restart; same steps as before it):
#   drop scratched -> v5s1 (price_day3) -> v6 (stage 2f) -> shade (off, keeps p_unshaded) -> blend with the open
#   -> angles, first starters, first-up blocks -> paper bets -> market page -> lay/back sheet on the page.
# Runs from the model work folder: $S/model, built by rebuild_model.sh (the live v10 model, commit 9d6fdfc).
# DAYPREFIX-prices.txt must already be in data/live_bets (pricemtg.sh writes it with mkprices.py).
S=$(cd "$(dirname "$0")" && pwd); L=/home/user/fk-model/data/live_bets; R=/home/user/fk-model/research/form_gbm
TAG=$1; NPZ=$2; P=$3; G=$4; TITLE=$5; NOTE=$6
B=$L/$P-$G; SN=$S/model/$TAG-scr.npz; PR=$L/$P-prices.txt
[ -f "$PR" ] || { echo "STOP: no $PR"; exit 1; }
mkdir -p $S/pages
cd $S/model || { echo "STOP: no $S/model"; exit 1; }
for f in "$R"/*.py; do cp -u "$f" . ; done   # the model folder runs the repo's current scripts
# The live model's input list (v10, 809 names), pinned here so a change to research/form_gbm/F9_names.txt cannot reach
# the live pricer by accident; price_day3 stops if the day's inputs do not match it. The model folder must be the
# live v10 one (rebuild_model.sh), not the models branch root (v9).
cmp -s "$R/pipeline/F9_names_live.txt" F9_names.txt || cp "$R/pipeline/F9_names_live.txt" F9_names.txt   # cmp first: meetings now price side by side (12 Nov)
python3.13 drop_scr.py $NPZ $PR $SN || { echo "STOP: drop_scr"; exit 1; }
python3.13 price_day3.py $SN $B-v5s1.json || { echo "STOP: price_day3"; exit 1; }
python3.13 apply_stage2f.py $B-v5s1.json $SN $B-v6.json p_oof_blend9.npy && echo "v6 ok" || { echo "STOP: stage 2f"; exit 1; }
python3.13 shade_back.py $B-v6.json $SN
python3.13 blend_open.py $B-v6.json $PR
python3.13 angles_day.py $SN $B-angles.json
python3.13 fs_json.py $SN $B-first-starters.json
python3.13 fu_json.py $SN $B-first-up-blocks.json
python3.13 paper_open.py $B-v6.json $PR $B-angles.json $B-bets.csv "" $B-first-starters.json $B-first-up-blocks.json
python3.13 market_sheet.py $SN $B-v6.json $PR $B-angles.json $B-first-starters.json $B-first-up-blocks.json \
  $S/pages/$TAG-market.html "$TITLE" "$NOTE"
python3.13 lay_sheet.py $P $G $SN --html $S/pages/$TAG-market.html > $B-lays.csv
echo "meeting done: $S/pages/$TAG-market.html"
