#!/usr/bin/env bash
# Rebuild every NRL table, model and report from the nrl-history release, in order.
#   bash nrl/build.sh            dev and confirm seasons only
#   bash nrl/build.sh --final    also the untouched final seasons (run once, when the models are frozen)
# Needs: pip install -r nrl/requirements.txt, and gh (or the files already in nrl/cache).
set -euo pipefail
C=nrl/cache
mkdir -p $C/raw nrl/docs
if command -v gh >/dev/null && [ "${SKIP_DOWNLOAD:-}" != 1 ]; then
  gh release download nrl-history --dir $C --pattern '*.parquet' --pattern 'mirror_source.txt' --skip-existing || true
  gh release download nrl-history --dir $C/raw --pattern 'cd_raw_*.jsonl.gz' --pattern 'teamlists_*.jsonl.gz' --skip-existing || true
fi
python nrl/data/parse_cd.py $C/raw $C
python nrl/data/link_cd.py $C
python nrl/teamlists/parse.py $C $C/raw
python -m nrl.model.player_ratings $C
python -m nrl.model.team_frame $C
python -m nrl.model.player_frame $C
python -m nrl.model.team $C nrl/docs/team_seasons.md "$@"
python -m nrl.model.tries $C nrl/docs/TRIES_STEP1.md "$@"
python -m nrl.model.first_try $C nrl/docs/FIRST_TRY_STEP1.md
python -m nrl.model.counts $C nrl/docs/COUNTS_STEP1.md "$@"
python -m nrl.model.late_changes $C nrl/docs/LATE_CHANGES.md
python -m pytest -q nrl/tests
