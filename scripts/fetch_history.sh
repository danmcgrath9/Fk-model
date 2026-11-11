#!/usr/bin/env bash
# Download every history file from a release into a folder, retrying, because GitHub's asset download answers 500
# now and then and one bad asset used to fail the run. --skip-existing means each retry only fetches what is still
# missing. Exits 1 if the count is still short after the retries (each attempt is cut off at ten minutes: a hung
# download once held a job for the whole of its time limit): a back-test over a partial history is not the back-test.
#   scripts/fetch_history.sh                                  the "history" release into ./history (Victoria)
#   scripts/fetch_history.sh history-states history_states    the other states, from the archive (11 Nov 2026)
set -u
REL="${1:-history}"; DIR="${2:-history}"
mkdir -p "$DIR"
# day files only: the release also carries moved.json (scripts/db_to_history.py), which no fit reads
N=$(gh release view "$REL" --json assets --jq '[.assets[] | select(.name | endswith(".jsonl.gz"))] | length' 2>/dev/null || echo 0)
if [ "$N" -eq 0 ]; then echo "$REL files: 0 (no release yet)"; exit 0; fi
for attempt in 1 2 3 4 5; do
  timeout 600 gh release download "$REL" --dir "$DIR" --pattern '*.jsonl.gz' --skip-existing && break
  echo "download attempt $attempt failed; $(ls "$DIR"/*.jsonl.gz 2>/dev/null | wc -l) of $N files so far"
  sleep $((attempt * 15))
done
HAVE=$(ls "$DIR"/*.jsonl.gz 2>/dev/null | wc -l)
echo "$REL files: $HAVE of $N, $(du -sh "$DIR" | cut -f1)"
[ "$HAVE" -ge "$N" ] || { echo "still short of the release after five attempts"; exit 1; }
