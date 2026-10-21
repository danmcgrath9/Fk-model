# NBL betting model (started 21 Oct 2026)

Team markets (head-to-head, line, total) and player props (points, rebounds, assists, threes,
points+rebounds+assists) for the NBL, priced ourselves and bet only when a book's price beats ours by
enough. House standard: `prompts/HOUSE_STANDARD.md` on branch `afl-props`. Separate from the racing,
NBA and AFL code: everything lives in `nbl/` and the `nbl-*` workflows, with its own data release
(`nbl-history`). No Form King key, no BetMatic orders. Paper only until the founder says otherwise.

## Where it stands

| Step | What | Status |
|---|---|---|
| 1. Data inventory | every source, what it holds, terms, cost | `docs/INVENTORY.md` |
| Data | nblR's GitHub copy of NBL results and box scores | `nbl data` workflow copies it to `nbl-history` |
| Odds | The Odds API probe, capped at 300 credits | written; waiting on the `ODDS_API_KEY` repository secret (not set: 0 credits spent) |
| 2-7 | data layer, team model, props, backtest, team news, paper season | not started: waiting on the inventory review |

## Running it

```
pip install pandas pyarrow pyreadr requests
python nbl/data/mirror.py --out nbl/cache     # or download the parquet files from the nbl-history release
```
