# Session helpers (10 Nov 2026)
The cloud session's machine restarted on 10 Nov and wiped its scratch folder, which held these helpers, the pricing
work folder and the live model files. The models are on the `models` branch; these helpers are kept here so a restart
can't lose them again. Copy them into the session's scratch folder (they expect /home/user/fk-model as the clone).
- waitexp.sh OUT: wait for the newest fk-experiment run, save its output. waitpull.sh / waithorse.sh: wait for a pull.
- getnpz.sh OUT TRACK: wait for fk-export, fetch upcoming.npz, check the track.
- shot_card.js HTML OUT.png [w] [h]: screenshot a card's HTML through the Node browser (the Python one may be missing).
- mkprices.py SCR NUMS OUT "HEADER": the prices file on the FINAL field (emergencies SCR unless it is race morning and
  Form King still has them in; anything the entry numbers scratch is SCR).
- meeting.sh TAG NPZ DAYPREFIX GTAG "TITLE" "NOTE": drop scratched, v5s1, v6, blend, angles, paper bets, market page, lays.
- pricemtg.sh DAYPREFIX GTAG NPZ SCR NUMS "HEADER" "TITLE": mkprices + meeting + BetMatic orders + page take-at.
- late_feats.py: rebuilds late_feats.npy in the model folder (angles_day.py needs it).

After a restart, rebuild the model work folder before pricing, in one command:
    bash /home/user/fk-model/research/form_gbm/pipeline/rebuild_model.sh <scratch>
It puts these helpers in <scratch>, the LIVE model in <scratch>/model (v10, the 15 Oct retrain, from commit 9d6fdfc's
challenger/ folder), installs lightgbm/catboost/torch if missing and rebuilds late_feats.npy. NOT the models branch root:
that is the old v9 copy, and pricing on it moved Seymour 12 Nov by a median 8% in the 10 Nov test before it was caught.
Check after any rebuild: re-price a meeting already priced on the live model (meeting.sh with a throwaway GTAG) and
compare the v5s1/v6 files; on 10 Nov every price matched Seymour s6k exactly. Delete the throwaway files after.
F9_names_live.txt is the live model's input list (809, the same as research/form_gbm/F9_names.txt today); meeting.sh copies
it into the model folder every run so a change to the repo list cannot reach the live pricer by accident.

## The fast pricing run (12 Nov 2026, founder: "the run takes an hour? Thats way to fkn long")
`python3.13 price_run.py` does the morning in one command: one GitHub run (fk price run: pulls, every input script,
one export per date, about 2 minutes), then one price_day3 call for every new meeting together (its five networks
train on the whole history, about 2.5 minutes, so once a run instead of once a meeting), then the rest of each meeting
side by side (about 15 seconds each). Measured on Dunkeld, Yea, Donald and Moe: 2.7 minutes locally, about 5 minutes
in all, against about an hour by hand. Running the meetings side by side with one thread each was SLOWER (26 minutes
and not finished): price_day3 needs every core. Pricing the meetings together against pricing Moe alone on the same
inputs: median price change 0.2%, the largest 3.5% (the network's share), less than a rider change moves a price.
`--test` writes everything under <prefix>-test and never touches a real sheet or day page.
