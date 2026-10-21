# BBL / WBBL betting model (started 21 Oct 2026)

Team markets (head-to-head, line, total) and player props for the Big Bash, priced ourselves and bet
only when a book's price beats ours by enough. The house standard is `prompts/HOUSE_STANDARD.md` on
branch `afl-props`; it overrides anything here. Separate from the racing, AFL and NBA code: everything
lives in `bbl/`, the `bbl-*` workflows and the `bbl-history` release. No Form King key. No BetMatic
orders. Paper only until the founder says otherwise.

## Layout

| path | what |
|---|---|
| `bbl/data/cricsheet.py`, `inventory.py` | Cricsheet ball-by-ball into parquet; what the pull holds |
| `bbl/model/frame.py` | one row per player per game and per team per game, every feature from before the start |
| `bbl/model/team.py` | win chance and totals, walk-forward, at the open and with teams named |
| `bbl/model/props.py` | runs, sixes and wickets distributions per player |
| `bbl/model/backtest.py` | runs props against a stand-in line (a proxy) |
| `bbl/live/price.py`, `names.py`, `compare.py` | prices for fixtures not yet played; book names to Cricsheet names; a paper list from a saved odds snapshot (no network, nothing sent) |
| `bbl/lines/probe.py` | capped Odds API probe; the cap is the number in `bbl/lines/PROBE_BUDGET` |
| `.github/workflows/bbl-data.yml`, `bbl-model.yml`, `bbl-lines.yml` | pull Cricsheet once; build and report; the probe |

## Where it stands

| Step | What | Status |
|---|---|---|
| 1. Inventory | sources, terms, cost | done: `docs/DATA_INVENTORY.md` |
| Data | Cricsheet: every T20 match (14,686), people register, licence text | on the `bbl-history` release |
| 2. Data layer | player and team rows, leakage tests on made-up and real data | done: `docs/MODEL_STEPS_2_5.md` |
| 3. Team model | head-to-head near a coin flip (BBL 0.06 bits on the choose seasons, below zero on 2024/25); totals from the ground's average (BBL) or a model (WBBL) | done |
| 4. Props | runs, sixes, wickets; beats the last-10 average everywhere; sixes run high | done |
| 5. Backtest | runs vs STAND-IN line: BBL 2024/25 +13% (-5% to +28%), WBBL +17% (+9% to +27%); an upper bound | done; real lines need odds |
| 6. Team news | repricing after team announcements | needs recorded prices |
| 7. Paper season | pricer, name matcher, paper comparer built | needs odds; WBBL 2026/27 could be first |
| Odds probe | free calls, then up to 300 credits on your OK | blocked: `ODDS_API_KEY` secret not set in Fk-model |
| Final score | 2025/26 held back | when every choice is frozen |
