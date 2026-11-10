#!/bin/bash
# waithorse.sh : wait for the newest fk-horse run to finish
sleep 8
id=$(curl -s "https://api.github.com/repos/danmcgrath9/Fk-model/actions/workflows/fk-horse.yml/runs?per_page=1" | python3 -I -c "import sys,json; print(json.load(sys.stdin)['workflow_runs'][0]['id'])" 2>/dev/null)
for i in $(seq 1 60); do s=$(curl -s "https://api.github.com/repos/danmcgrath9/Fk-model/actions/runs/$id" | python3 -I -c "import sys,json; r=json.load(sys.stdin); print(r['status'], r.get('conclusion'))" 2>/dev/null); echo "$s" | grep -q completed && break; sleep 8; done
echo "run $id: $s"
