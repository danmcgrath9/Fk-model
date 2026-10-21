# BBL / WBBL betting model (started 21 Oct 2026)

Team markets (head-to-head, line, total) and player props for the Big Bash, priced ourselves and bet
only when a book's price beats ours by enough. The house standard is `prompts/HOUSE_STANDARD.md` on
branch `afl-props`; it overrides anything here. Separate from the racing, AFL and NBA code: everything
lives in `bbl/`, the `bbl-*` workflows and the `bbl-history` release. No Form King key. No BetMatic
orders. Paper only until the founder says otherwise.

## Layout

| path | what |
|---|---|
| `bbl/data/cricsheet.py` | Cricsheet ball-by-ball JSON (every T20 match, both genders, all leagues) into parquet |
| `bbl/data/inventory.py` | what the pull holds: seasons, rows, columns, gaps, rules fields; writes INVENTORY.md |
| `bbl/lines/probe.py` | capped Odds API probe; the cap is the number in `bbl/lines/PROBE_BUDGET` |
| `.github/workflows/bbl-data.yml` | pulls Cricsheet once, records its licence text and robots.txt, uploads to `bbl-history` |
| `.github/workflows/bbl-lines.yml` | runs the probe; a paid run happens once and its raw responses go to the release |

## Where it stands

| Step | What | Status |
|---|---|---|
| 1. Inventory | sources, what they hold, terms, cost | in progress: see `docs/DATA_INVENTORY.md` |
| 1. Odds probe | free calls (sport keys, fixtures now) | budget 0, runs on push |
| 1. Odds probe | paid calls (archive coverage, markets, props, opening), at most 300 of the 20,000 credits | waiting on the founder's OK |
| 2-7 | data layer, team model, props, backtest, team-news angle, paper season | not started |
