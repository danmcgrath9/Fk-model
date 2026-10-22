# NBL betting model (started 21 Oct 2026)

Team markets (head-to-head, line, total) and player props (points, rebounds, assists, threes,
points+rebounds+assists) for the NBL, priced ourselves and bet only when a book's price beats ours by
enough. House standard: `prompts/HOUSE_STANDARD.md` on branch `afl-props`. Separate from the racing,
NBA and AFL code: everything lives in `nbl/` and the `nbl-*` workflows, with its own data release
(`nbl-history`). No Form King key, no BetMatic orders. Paper only until the founder says otherwise.

## Where it stands

| Step | What | Status |
|---|---|---|
| 1. Data inventory | every source, what it holds, terms, cost | done: `docs/INVENTORY.md` |
| Data | nblR's GitHub copy of NBL results, box scores, play-by-play, 2015-16 to now | on `nbl-history` (`nbl data` workflow) |
| Odds | The Odds API probe, capped at 300 credits | written; waits for the `ODDS_API_KEY` repository secret (0 credits spent) |
| 2. Data layer | one row per player per game and per team per game, pre-game features only, leakage test | done: `model/frame.py`, `tests/` |
| 3. Team model | margin and total, at the open and with squads named, priced h2h / line / total; on-court player ratings | done: `docs/TEAM_STEP1.md`, `model/onoff.py` |
| 4. Player props | minutes x rate and a direct model, negative binomial prices at any line | done: `docs/PROPS_STEP1.md` |
| 5. Backtest | against stand-in lines only (proxy, not a market test) | done; real lines needed for the real test |
| 6. Team-news angle | do books reprice after outs? | needs recorded prices |
| Research | Voulgaris angles: NBL first halves outscore second halves every season (50.8% of points), team tendencies do not last, first-half pace does not predict the second half; half totals now priced, graded and recorded; per-stat memory and projection-dependent spreads adopted; redistribution, adjusted efficiency, early-season weights rejected; starters the biggest gain found | `docs/RESEARCH.md`, `research/` |
| 7. Paper season | our prices for the next 8 days, kept on the release, and graded against results every run | `model/price_round.py`, `model/grade.py`, `nbl prices` workflow (`paper_scorecard.md` on the release) |
| Line recorder | books' prices from open to close, capped per run and per season (60,000 credits), ledger on the release | `lines/record.py`, `nbl record lines` workflow; idle until `ODDS_API_KEY` exists |
| Book rules | void rules for a player who does not play | `docs/BOOK_RULES.md` (TAB not found) |

## Team model

Scored on seasons it never saw (squads named; log loss, lower is better, a coin flip is 0.693):

| season | games | ours, squads named | ours, at the open | results-only rating (Elo) | always the home team |
|---|---|---|---|---|---|
| 2023-24 | 154 | 0.676 | 0.681 | 0.674 | 0.676 |
| 2024-25 | 159 | 0.653 | 0.656 | 0.657 | 0.686 |
| 2025-26 | 179 | 0.616 | 0.616 | 0.609 | 0.694 |
| 2026-27 so far | 36 | 0.735 | 0.742 | 0.745 | 0.672 |

**Plainly: level with a results-only rating, and probably behind the market.** The squad ratings that
help are on-court plus/minus from the play-by-play (`model/onoff.py`: 54,655 stints rebuilt from 1,587
games), which beat box-score efficiency for valuing a squad. With them the named squad beats the open
squad slightly, most where team news moved our number (2 to 4 points: miss 9.5 against 10.4, but only 7
games). Totals beat the league average by 1 to 3.5 points a game. The final-check seasons have been
looked at three times while the model was built (`docs/TEAM_STEP1.md` says how); every setting was chosen
on 2016-17 to 2022-23 only. Early season is the weak spot: a third of last season's regulars are gone.

## Player props

Projection accuracy and every table are in `docs/PROPS_STEP1.md`; what was tried to improve them, and what
worked, is in `docs/RESEARCH.md`.

Against a **naive stand-in book** (lines from the last-10 average, both sides priced from that average,
7% overround), betting at 3%+ edge:

| market | 2023-24 and 2024-25 | 2025-26 and 2026-27 so far (final check) |
|---|---|---|
| points | +13.9% (1,807 bets) | +16.2% (1,285) |
| rebounds | +19.0% (2,468 bets) | +13.5% (1,605) |
| assists | +12.3% (1,634 bets) | +14.5% (1,148) |
| threes | +20.0% (2,687 bets) | +20.1% (1,759) |
| points+rebounds+assists | +12.9% (1,996 bets) | +17.1% (1,455) |

**Read this as an upper bound, not an edge.** It holds across seasons, and shuffled projections lose
(so the test is not broken), but a plain projection (half the recent average, half per-minute rate x
usual minutes) wins about as much on fewer bets: the "edge" is mostly regressing a hot or cold recent
average, which any decent book already does. Threes are flattered: even shuffled projections roughly
break even there, so the stand-in book misprices threes. The test that matters is against recorded
lines. Same conclusion as the AFL disposals work.

## Running it

```
pip install -r nbl/requirements.txt
python nbl/data/mirror.py --out nbl/cache          # or download the parquet files from the nbl-history release
python -m nbl.model.frame nbl/cache                # players.parquet, teams.parquet
python -m nbl.model.onoff nbl/cache                # stints and on-court ratings (needs pbp.parquet)
python -m nbl.model.team nbl/cache nbl/docs/TEAM_STEP1.md
python -m nbl.model.props nbl/cache nbl/docs/PROPS_STEP1.md        # NBL_FINAL=1 to include 2025-26 and 2026-27
python -m nbl.model.price_round nbl/cache nbl/out 8                # our prices for the next 8 days
python -m nbl.model.grade nbl/cache <dir of prices_*.csv> scorecard.md   # grade saved sheets against results
python -m pytest nbl/tests                         # leakage and unit tests (some need nbl/cache)
```

## Risks to keep in front of us

- **Small league, small sample.** 1,615 games since 2015-16, about a quarter of the AFL work's
  player-games. Intervals are wide and the final check is only 1.2 seasons.
- **Limits.** NBL prop markets are small; books restrict winning accounts across every sport at once.
- **Void rules.** A player who does not take the court voids his props at Australian books; one who
  plays two minutes does not. The price sheet uses each team's last squad: re-run after team news.
- **One volunteer's data.** nblR is maintained by one person; if updates stop, so does in-season data.
- **Stand-in lines only.** Nothing here has been tested against a real price.
