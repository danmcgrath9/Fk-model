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
| 1. Inventory | one look at each candidate source and its terms (`aleague data`) | done, see `docs/INVENTORY.md` |
| 1. Inventory | The Odds API probe, capped at 300 of the 20,000 A-League credits (`aleague lines`) | blocked: `ODDS_API_KEY` secret not set; 0 credits spent |
| 2. Data layer | one row per player per game and per team per game, leak-tested | waits on step 1 |
| 3-7 | team model, props, backtest, team-news test, paper season | not started |

## Sources being checked (step 1)

| Source | Lead | How it is checked |
|---|---|---|
| The Odds API | team markets from mid-2020, props from May 2023 if A-League has any | capped probe |
| football-data.co.uk | A-League results with closing odds (best, average, Pinnacle) from 2012-13, offered as a CSV download | one file |
| FBref | fixtures, lineups, per-player minutes, goals, shots, cards; its Opta advanced stats (xG) were withdrawn in Jan 2026 | 3 pages + 2 match reports, 8 s apart |
| ESPN public JSON | fixtures, lineups, per-player match stats | 4 scoreboards + 2 summaries |
| worldfootballR_data (GitHub) | FBref A-League results mirror, results only, no player stats | read locally |
| Open-Meteo | historical hourly weather | one call |
| FotMob, Sofascore, KeepUp, Ultimate A-League, Transfermarkt | player stats, lineups | robots.txt and terms only, no data |
| API-Football | paid API (free tier 100 calls a day) with per-player fixture stats | not called; needs an account, ask first |
