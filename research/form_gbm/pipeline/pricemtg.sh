#!/bin/bash
# pricemtg.sh DAYPREFIX GTAG NPZ SCR_OUTPUT.md ENTRY_NUMBERS.txt "# prices header" "TITLE"
# The whole morning for one meeting: prices file on the final field (mkprices.py), the model (meeting.sh), the BetMatic
# orders on the final field (betmatic_orders.py) and the page's "take at" from the order sheet (page_takeat.py).
# Example: bash pricemtg.sh 2026-11-11-ballarat s6w $S/up_ballarat.npz $S/nov/scr_ballarat.md $S/nov/nums_ballarat.txt \
#          "# Ballarat Wed 11 Nov, Good 4" "Ballarat Wed 11 Nov"
S=$(cd "$(dirname "$0")" && pwd); L=/home/user/fk-model/data/live_bets; R=/home/user/fk-model/research/form_gbm
P=$1; G=$2; NPZ=$3; SCR=$4; NUMS=$5; HEAD=$6; TITLE=$7; TAG=$(echo $P | tr -d -)
cp $NUMS $L/$P-entry-numbers.txt
python3.13 $S/mkprices.py $SCR $NUMS $L/$P-prices.txt "$HEAD" || exit 1
bash $S/meeting.sh $TAG $NPZ $P $G "$TITLE" "" | grep -E "v6 ok|first starters|missing|STOP|removing|fields now|meeting done"
cd $R && python3.13 betmatic_orders.py $P $G $L/$P-$G-orders-all.csv | tail -1
python3.13 page_takeat.py $S/pages/$TAG-market.html $L/$P-$G-orders-all.csv $P $G
cp $L/$P-$G-orders-all.csv $L/$P-$G-orders.csv
python3.13 - "$L/$P-$G-orders.csv" <<'PY'
import csv, sys
rows = list(csv.DictReader(open(sys.argv[1])))
horses = {(r["race"], r["horse"]) for r in rows}
print(f"{sys.argv[1].split('/')[-1]}: {len(horses)} horses, {sum(float(r['stake_units']) for r in rows):.2f}u if every order fires")
PY
