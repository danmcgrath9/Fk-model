# Session helpers (10 Nov 2026)
The cloud session's machine restarted on 10 Nov and wiped its scratch folder, which held these helpers, the pricing
work folder and the live model files. The models are on the `models` branch; these helpers are kept here so a restart
can't lose them again. Copy them into the session's scratch folder (they expect /home/user/fk-model as the clone).
- waitexp.sh OUT: wait for the newest fk-experiment run, save its output. waitpull.sh / waithorse.sh: wait for a pull.
- getnpz.sh OUT TRACK: wait for fk-export, fetch upcoming.npz, check the track.
- shot_card.js HTML OUT.png [w] [h]: screenshot a card's HTML through the Node browser (the Python one may be missing).
Still to rebuild after a restart: the pricing work folder (research/form_gbm scripts + the models branch files),
mkprices.py, meeting.sh and pricemtg.sh.
