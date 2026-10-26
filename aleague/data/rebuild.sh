#!/usr/bin/env bash
# Rebuild every A-League table from what the aleague-history release holds, and upload them.
# "refresh" first re-reads this season's Wikipedia pages (a dozen requests). Used by the aleague-data
# and aleague-lineups workflows, so a line-up top-up is followed by fresh tables in the same run.
set -euo pipefail
R=aleague-history
C=aleague/cache
rm -rf "$C/raw" "$C/tables" && mkdir -p "$C/tables" "$C/ual"
gh release download $R --pattern results_raw_v1.tar.gz --dir "$C" --clobber
tar xzf "$C/results_raw_v1.tar.gz" -C "$C"
if [ "${1:-}" = "refresh" ]; then
  cur=$(python -c "import datetime as d; t=d.date.today(); y=t.year if t.month>=7 else t.year-1; print(f'{y}–{str(y+1)[2:]}')")
  python aleague/data/wiki_fetch.py --out "$C/raw/wiki" --seasons "$cur"
fi
python -m aleague.data.build "$C/raw" "$C/tables"
gh release download $R --pattern 'ual_20??-??.tar.gz' --dir "$C/ual" --clobber || true
if ls "$C"/ual/ual_*.tar.gz >/dev/null 2>&1; then
  # the player tables, then this season's missing scores from Ultimate A-League (faster than Wikipedia)
  python -m aleague.data.ual_build "$C/ual" "$C/tables" --fill-scores
fi
python -m aleague.data.team_games "$C/tables"
python -m pytest -q aleague/tests | tail -3
for f in matches.parquet goals.parquet team_games.parquet BUILD.md ual_matches.parquet player_games.parquet ual_events.parquet UAL_BUILD.md; do
  [ -f "$C/tables/$f" ] && gh release upload $R "$C/tables/$f" --clobber
done
echo "tables rebuilt $(date -u +%FT%TZ)"
