#!/bin/bash
# waitexp.sh OUTFILE : wait for the newest fk-experiment run to finish and save its experiments-branch output to OUTFILE
sleep 8
until s=$(curl -s "https://api.github.com/repos/danmcgrath9/Fk-model/actions/workflows/fk-experiment.yml/runs?per_page=1" | python3 -I -c "import sys,json; r=json.load(sys.stdin)['workflow_runs'][0]; print(r['status'], r.get('conclusion'), r['id'])" 2>/dev/null) && echo "$s" | grep -q "^completed"; do sleep 8; done
id=${s##* }; echo "$s"
cd /home/user/fk-model && git fetch -q origin experiments && f=$(git ls-tree --name-only origin/experiments | grep -- "-$id.md") && git show origin/experiments:$f > "$1" && head -1 "$1"
