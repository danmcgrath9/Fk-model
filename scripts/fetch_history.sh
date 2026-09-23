#!/usr/bin/env bash
# Download every history file from the "history" release into ./history, retrying, because
# GitHub's asset download answers 500 now and then and one bad asset used to fail the run.
# --skip-existing means each retry only fetches what is still missing. Exits 1 if the count
# is still short after the retries: a back-test over a partial history is not the back-test.
set -u
mkdir -p history
N=$(gh release view history --json assets --jq '.assets | length' 2>/dev/null || echo 0)
if [ "$N" -eq 0 ]; then echo "history files: 0 (no release yet)"; exit 0; fi
for attempt in 1 2 3 4 5; do
  gh release download history --dir history --pattern '*.jsonl.gz' --skip-existing && break
  echo "download attempt $attempt failed; $(ls history | wc -l) of $N files so far"
  sleep $((attempt * 15))
done
HAVE=$(ls history | wc -l)
echo "history files: $HAVE of $N, $(du -sh history | cut -f1)"
[ "$HAVE" -ge "$N" ] || { echo "still short of the release after five attempts"; exit 1; }
