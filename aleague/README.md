# A-League Men: team markets and player props (started 21 Oct 2026)

Price every A-League Men market ourselves (head-to-head three-way, line, total, both teams to score,
and whichever player props Australian books actually post) and bet only where a book's price beats
ours by enough. House standard: `prompts/HOUSE_STANDARD.md` on `afl-props`. Brief: `prompts/aleague.md`.

Separate from everything else: code in `aleague/`, workflows `aleague-*.yml` with their own
concurrency groups, data on the `aleague-history` release. No Form King key, no BetMatic orders.
Paper only until the founder says otherwise.

## Where it stands

| Step | What | Status |
|---|---|---|
| 1. Inventory | one look at each candidate source and its terms | done, `docs/INVENTORY.md` |
| 1. Inventory | The Odds API probe (capped at 300 of 20,000 credits) | waiting for the `ODDS_API_KEY` secret; 0 credits spent |
| 2. Data | matches 2013-14 to now, goals with scorer and minute, one row per team per game, leak-tested | done, on the release |
| 2. Data | one row per player per game (minutes, shots, cards) | no permitted free source; API-Football is the candidate (paid, ask first) |
| 3. Team model | expected goals per side, every team market priced from one score matrix, "at the open"; settings frozen in `model/settings.json` | done, `docs/TEAM_STEP1.md`: beats base rates on head-to-head, level with Elo, no better than base rates on goals markets |
| 3. Team model | "teams named" version | needs line-ups (the same player feed) |
| 4. Props | pricing machinery (scorer, shots, cards as count distributions), tested | done; projections wait for minutes data |
| 5. Backtest | probabilities against base rates and Elo, out of sample | done; against real lines once odds arrive |
| 6. Team-news test | needs recorded prices | after odds |
| 7. Paper season | `price_round` prints our prices for the coming week | first record: `docs/prices_2026-10-21.md` (round 2, before kick-off); needs a book's prices to compare |

## Data (all on the `aleague-history` release)

| File | What | Source |
|---|---|---|
| `matches.parquet` | every league match 2013-14 to the current fixture list: date, kick-off (UTC), teams, 90-minute and final score, stage, ground, neutral flag, crowd | scores to May 2025 from FBref through worldfootballR's GitHub copy; from 2025-26 from Wikipedia |
| `goals.parquet` | every goal: scorer, minute, penalty, own goal | Wikipedia club season pages, attached only where their score matches |
| `team_games.parquet` | one row per team per match, features shifted one match | built from the above |
| `BUILD.md` | counts per season and the cross-check | |
| `results_raw_v1.tar.gz` | the raw sources as pulled | |
| `inventory_v1.tar.gz` | step 1 responses, robots.txt and terms | |

Where both sources hold a match (2013-14 to 2024-25), Wikipedia's score agrees with FBref's on 99.7%.
Wikipedia lags in-season by a few days (two round-1 results of 2026-27 were missing on 21 Oct), so for
paper betting the current week's results should come from The Odds API's scores endpoint once the key is in.

Wikipedia text is CC BY-SA 4.0, by Wikipedia contributors; our tables are derived from it and are
shared on the same terms if ever published. Every pull identifies itself with the repository URL.

## Running it

```
pip install -r aleague/requirements.txt
gh release download aleague-history --pattern '*.parquet' --dir aleague/cache/tables
python -m pytest -q aleague/tests                                     # pricing, props and leakage tests
python -m aleague.model.evaluate aleague/cache/tables report.md       # tune and confirm seasons only
python -m aleague.model.price_round aleague/cache/tables prices.md    # our prices for the next 8 days
```

In season: Actions > aleague data > Run workflow with `refresh_current = yes` re-reads this season's
Wikipedia pages and rebuilds the tables. (Run-workflow buttons only appear for workflows on the default
branch; until this branch is merged, a push to `aleague/data/**` does the same without the refresh.)

## Risks to keep in front of us

- **Soccer team markets are sharp.** The model is level with a plain Elo on head-to-head and no better than
  base rates on totals and both-teams-to-score; that is normal for a goals-only model and says nothing yet
  about beating a book. Only recorded openers answer it.
- **Home advantage looks overrated** in the newest seasons (41% home wins predicted, 38% happened). A
  home edge that changes over time is the first thing to test, on 2026-27 as it is played.
- **Limits.** Books restrict winning accounts across every sport at once.
- **Late outs and voids.** A goal-scorer bet on a player who does not take the field is usually void; one
  who comes off injured usually loses. Each book's rule needs checking.
- **A thin league.** About 160 matches a season, high squad turnover between seasons (the fitted
  season carry-over is low), and one new club (Auckland FC, 2024-25) with little history.
