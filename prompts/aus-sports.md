# Prompts: Australian sports models (team betting + player props)

Paste the **Shared** block, then one sport's block, into a new session. One session per sport.
AFL already exists on branch `afl-props` (folder `afl/`); its block below continues that work rather
than starting again.

---

## Shared (paste first, every time)

I want to build a betting model for [SPORT], the same way we built my horse-racing model and the AFL
props model: team betting (head-to-head, line, total) AND individual player props. Work in my GitHub
repo danmcgrath9/Fk-model (attach it), in the sport's own folder on its own branch (named in the sport
block). Keep it separate from everything else: don't change anything under research/form_gbm,
data/live_bets, nba/, afl/ (unless this is the AFL session) or the racing workflows. Any GitHub
workflow is new, named after the sport (e.g. nrl-data.yml), with its own concurrency group, never an
fk-*, nba-* or another sport's workflow, so nothing queues behind or blocks the racing pulls and
BetMatic orders. Don't use the Form King key or credits (racing only). BetMatic is fine for its odds
watch (recording prices); orders only after my OK on the exact list, same as racing.

### Who I am and how we work
- I'm Dan, the founder. I run a horse-racing model (Form King data, BetMatic for automated betting at
  the open, TAB account, Mercer Tipping on Twitter). Our racing edge is beating the OPENING price: the
  backtest makes about +46% at the open and loses at Betfair SP, so getting on early is the whole game.
  Assume the same is true here until the data says otherwise: the test that matters is the opening line.
- Talk to me in plain English, short answers, tables where they help. Facts from the data, not guesses.
  Flag risks loudly. I'd rather you refuse than guess. Every number must trace to code you ran.

### Hard rules
- Never paste or ask for API keys or passwords. Secrets live only in GitHub secrets, never in chat or the repo.
- No bets of any kind, and nothing sent to BetMatic, without my OK in chat on the exact list. Paper only until I say otherwise.
- Never send a message or email on my behalf without showing me the exact final draft first.
- Check each data source's terms before pulling. Don't bulk-scrape sites that forbid it. Prefer a
  maintained copy on GitHub over scraping the site itself. Pull history once, cache it (parquet on a
  GitHub release named for the sport, e.g. `nrl-history`), throttle, and never re-pull what we hold.
- Don't put model or AI identifiers in commit messages.
- Commit and push your work to the branch; don't open a PR unless I ask.
- Tell me what anything costs BEFORE paying for it.

### Betting odds: The Odds API (shared with every sport)
- One subscription for all sports; the key is the GitHub secret `ODDS_API_KEY` in Fk-model. Credits are
  shared, so every pull has its own hard cap (`MAX_CREDITS`) read from the provider's x-requests-used
  header, and this sport's budget is in its block. Raw responses go to the sport's release so nothing is
  bought twice. Check `afl/lines/probe.py` on branch `afl-props` for a working, capped probe.
- Verified from their v4 docs: historical event odds (props) exist from 2023-05-03; snapshots every 5
  minutes; cost = 10 x markets x regions per call; historical events list costs 1 (0 if empty);
  /v4/sports is free (use `all=true` for the exact sport key). Featured markets (h2h, spreads, totals)
  go back to mid-2020 and one call prices a whole round.
- First job on odds: a probe of at most 300 credits that confirms, from real responses, which markets
  exist for this sport in the AU region (h2h, spreads, totals and each player prop), which books, how
  many players per game, from which season, and how many days before the start lines first appear.
  Do not assume a prop market exists because another sport has it.

### What to build, in order
1. **Data inventory first.** List every source (stats, results, lineups/team news, weather, odds), what
   it holds and from what season, its terms, and cost. Show me before building.
2. **Data layer.** One row per player per game and one row per team per game, every feature known
   before the start (shift every rolling figure one game; a test that changes a game's stats and checks
   its features don't move). Clean time split by season.
3. **Team model.** Predicted margin and total, priced into h2h / line / total. Two versions: "at the
   open" (what was knowable when books open the round: expected team, no team news) and "teams named"
   (confirmed line-ups). Benchmark against any public models and the market.
4. **Player props.** A projection per player per market (minutes or time on field x per-minute rate,
   adjusted for role, teammates in and out, opponent, venue, weather, expected margin), turned into a
   distribution (count model, not just a mean) and priced over/under at each line.
5. **Backtest.** Out-of-sample only. Against real opening and closing lines once pulled: ROI at the open,
   ROI at the close, closing line value, by market, line size and book. Before real lines exist, a
   stand-in line (the player's recent average, tuned so a blind over wins half the time) is allowed,
   labelled as a proxy, never as a market test. Bootstrap the profit by round; say when a sample is too
   small. Test angles on the oldest seasons, confirm on the next, final check on the newest, untouched
   until the end: anything that only works on one season gets dropped.
6. **Team-news angle.** Do books reprice fast enough after team announcements and late changes
   (a key player out: his team's line and his teammates' props should move)? Measurable from recorded
   prices.
7. **Paper season.** Record openers (BetMatic odds watch and/or The Odds API), compare with our numbers
   and the close, then talk to me about small real stakes.

### Risks to keep in front of us
- Limits: books restrict winning accounts across every sport at once; an edge is worth only what can be staked.
- Late outs, subs and voids: check each book's rule for a player who doesn't start or is replaced.
- Small markets move on small money; the opening line may be soft but the stake allowed small.

Start with step 1: tell me in a few lines what you'll build and what (if anything) costs money, then get going.

---

## NRL (paste after Shared)

Sport: NRL (men's). Folder `nrl/`, branch `nrl-model`, workflows `nrl-*.yml`, release `nrl-history`.
Odds API budget: 60,000 credits.

What we know (21 Oct 2026):
- Season March to early October; off-season now, about five months to build before round 1 2027.
- Teams named Tuesday afternoon for the round, with late changes up to an hour before kick-off.
  Opening lines usually appear before teams are named, so the open-vs-named gap is the team-news angle.
- Main props: anytime try scorer (the big one), first try scorer, try scorer 2+, plus run metres,
  tackles and points where offered. Team markets: h2h, line, total, margin bands.
- Data leads to check (terms first):
  - `uselessnrlstats/uselessnrlstats` on GitHub: Rugby League Project data, cleaned, every NRL match with
    per-player tries, goals, field goals, points, positions, sin bins (match_data and player_match_data,
    1908 to mid-2026). No run metres or tackles. Read it once from GitHub instead of scraping RLP.
  - `nrlR` (CRAN, DanielTomaro13/nrlR): fixtures, results, ladders, and match stats from Champion Data's
    match-centre feed (run metres, tackles, etc.) for recent seasons. Check that feed's terms before
    relying on it.
  - Try scoring is position-driven (wingers, centres, fullback) and game-script-driven (expected total
    and margin), so the team model's predicted total feeds the try-scorer model directly.
- Weather: BOM (free) before Open-Meteo (may need a paid plan for this use).

---

## NBL (paste after Shared)

Sport: NBL (Australian men's basketball). Folder `nbl/`, branch `nbl-model`, workflows `nbl-*.yml`,
release `nbl-history`. Odds API budget: 60,000 credits.

What we know (21 Oct 2026):
- Season September to March: it is ON NOW, so recorded openers can start this season.
- Props to check for: points, rebounds, assists, threes, points+rebounds+assists. Team: h2h, line, total.
- Data leads (terms first): `nblR` (CRAN, JaseZiv/nblR): player and team box scores, play-by-play and
  shot locations from 2015-16, results since 1979.
- Minutes drive everything: projected minutes x per-minute rates, with rotation changes, injuries,
  back-to-backs and import players (who change teams often) handled explicitly.
- Our NBA work lives in nba/ (don't touch it); borrow ideas, not code.

---

## Big Bash (paste after Shared)

Sport: BBL (and WBBL if markets exist). Folder `bbl/`, branch `bbl-model`, workflows `bbl-*.yml`,
release `bbl-history`. Odds API budget: 20,000 credits.

What we know (21 Oct 2026):
- Season mid-December to late January; about seven weeks to build before it starts.
- Data lead: Cricsheet (cricsheet.org): ball-by-ball for every BBL match (about 660) and WBBL, as bulk
  downloads. Check its licence (believed to be open with attribution; confirm). The `cricketdata` R
  package reads it.
- Markets to check for: h2h, total runs, top team batter/bowler, player runs over/under, sixes.
  Prop coverage on The Odds API is unconfirmed for cricket: the probe decides whether props are in scope.
- Drivers: toss and batting order, venue (scoring rates differ hugely by ground), weather and dew, overseas
  players arriving and leaving mid-season (national duty), and the Power Surge/bash boost rules.
- Small sample: a season is about 44 games, so props models lean on player history across all T20
  leagues in Cricsheet, not BBL alone.

---

## A-League (paste after Shared)

Sport: A-League Men. Folder `aleague/`, branch `aleague-model`, workflows `aleague-*.yml`,
release `aleague-history`. Odds API budget: 20,000 credits.

What we know (21 Oct 2026):
- Season October to May: ON NOW.
- Team markets: h2h (three-way), totals, both teams to score, handicap. Props to check for: anytime
  goal scorer, shots, cards. Prop coverage on The Odds API is unconfirmed: the probe decides.
- Data: no source found yet. Find one with per-player match stats (minutes, shots, xG if possible) and
  check its terms; tell me what exists before building anything.
- Soccer team markets are sharp worldwide; the A-League's chance is that it is a small league books pay
  less attention to. Prove it on opening lines before believing it.

---

## AFL (continue the existing work; paste after Shared)

Sport: AFL. Folder `afl/`, branch `afl-props` (already built; read afl/README.md first), workflows
`afl-*.yml`, release `afl-history`. Odds API budget: 60,000 credits.

Where it stands (21 Oct 2026): disposals projection and stand-in-line backtest done
(afl/docs/DISPOSALS_STEP1.md); team model first cut scored against Squiggle's models incl. Wheelo and
the market (afl/docs/TEAM_STEP1.md); data on the afl-history release (AFL Tables, Footywire, Fryzigg
2012-2025 with AFL Player Ratings, Squiggle tips); capped Odds API probe written (afl/lines/probe.py,
waits on the ODDS_API_KEY secret).

Next: run the probe; pull real disposal lines (open and close) and team markets; rebuild the team
model's lineup strength on AFL Player Ratings with a proper expected 22 at the open; goals, marks and
tackles props; then every angle against real opening lines (open vs close, by book, line size,
team-news repricing).
