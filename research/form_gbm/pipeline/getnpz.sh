#!/bin/bash
# getnpz.sh OUT.npz EXPECT_TRACK : wait for the newest fk-export run to finish, fetch upcoming.npz, check the track
for i in $(seq 1 100); do r=$(curl -s "https://api.github.com/repos/danmcgrath9/Fk-model/actions/workflows/fk-export.yml/runs?per_page=1" | /usr/bin/python3.13 -c "import sys,json;r=json.load(sys.stdin)['workflow_runs'][0];print(r['status'],r['conclusion'])" 2>/dev/null); case "$r" in completed*) break;; esac; sleep 6; done
cd /home/user/fk-model && git fetch -q origin upcoming && git show origin/upcoming:upcoming.npz > $1
/usr/bin/python3.13 -c "
import numpy as np,sys
z=np.load('$1',allow_pickle=True); t=set(map(str,z['track'])); print('$r', t, set(map(str,z['going'])), len(z['race_idx']), set(map(str,z['date'])))
sys.exit(0 if any('$2'.lower() in x.lower() for x in t) else 3)" 2>&1 | grep -v -E "distutils|Remainder|ModuleNotFound|_distutils_hack|line 201|frozen site"
