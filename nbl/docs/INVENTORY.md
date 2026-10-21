# NBL step 1: data inventory (21 Oct 2026)

Every figure below comes from the files themselves, read on 21 Oct 2026 (nbl/data/mirror.py and the
checks in this session), or from a workflow run named beside it. Nothing here is built on yet.

## What we have, what we don't

| Need | Source | Holds | Seasons | Terms | Cost |
|---|---|---|---|---|---|
| Player box scores | nblR's GitHub copy (JaseZiv/nblr_data releases) | one row per player per game, 50 columns: minutes, points, rebounds (off/def), assists, threes made/attempted, FG/FT, steals, blocks, turnovers, fouls, starter, plus/minus (from 2025-26) | 2015-16 to now (37,922 rows; 2026-27: 36 games to 18 Oct) | nblR is GPL-3; nblr_data has no licence file. We copy his files, never the NBL's site | free |
| Team box scores | same | one row per team per game, 67 columns incl. quarter scores, possessions-type stats (FGA, FTA, TO, OREB) | 2015-16 to now (3,240 rows) | same | free |
| Results and fixture | same | every game since 1979: teams, score, venue, round, regular/finals, tip time UTC, attendance; the rest of 2026-27 as SCHEDULED | 1979 to now (8,079 games; 129 still to play this season) | same | free |
| Play-by-play | same | every event (999,579 rows, 33 columns): shots with x/y, substitutions, fouls, scores, game clock and shot clock | 2015-16 to now (1,612 games) | same | free |
| Shot locations | same | x/y, made/missed, shooter | 2015-16, 2017-18 to 2024-25 (none for 2016-17, 2025-26, 2026-27) | same | free |
| Line-ups / team news | none found | | | | |
| Injury lists | none found | | | | |
| Who dressed and didn't play | box scores: 0:00 rows | the 12-man game-day squad incl. players who sat | 2015-16 on (2015-16 to 2017-18 write the minutes as a bare "0") | | free |
| Weather | not needed | the NBL is indoors | | | |
| Travel, rest, back-to-backs | derived from results | venue and tip time per game | 1979 on | | free |
| Betting odds | The Odds API | to be confirmed by the probe (see below) | | paid plan already held | from the 60,000-credit NBL budget |
| Betting odds (history) | Australia Sports Betting (aussportsbetting.com) | NBL spreadsheet: opening, min, max and closing odds for head-to-head, line and total, 2012-13 on (per a search snippet, not yet read) | 2012-13 on | robots.txt allows everything except AI training (`search=yes, ai-train=no`); its pages answer 403 to GitHub's runners, so the spreadsheet would be one download by you in a browser, after reading the conditions on that page | free |

## What came back from nblR's copy

Games per season, and player rows (box scores start 2015-16):

| season | games (results) | games with box scores | player rows | players listed per team-game (median) |
|---|---|---|---|---|
| 2015-16 | 120 | 120 | 2,597 | 10 |
| 2016-17 | 120 | 119 | 2,741 | 12 |
| 2017-18 | 121 | 121 | 2,774 | 12 |
| 2018-19 | 120 | 120 | 2,789 | 12 |
| 2019-20 | 135 | 134 | 3,159 | 12 |
| 2020-21 | 171 | 171 | 3,872 | 11 |
| 2021-22 | 148 | 148 | 3,555 | 12 |
| 2022-23 | 154 | 154 | 3,666 | 12 |
| 2023-24 | 154 | 154 | 3,792 | 12 |
| 2024-25 | 159 | 159 | 3,828 | 12 |
| 2025-26 | 179 | 179 | 4,278 | 12 |
| 2026-27 (so far) | 36 of 165 | 36 | 871 | 12 |

That is 1,615 games and 37,922 player-games: about a quarter of the AFL work's 138,255. Every
prop result will carry wide intervals, and the backtest will say so.

### Things in the data that will bite if ignored

1. **The source changed in 2025-26.** Game ids switch from numbers to long text ids, the tip time
   moves to a different column format, finals rounds are labelled by series ("SYD 2-1 ADL") instead of
   "FINALS", short team names go blank and opponent codes appear. Everything still joins (every box
   score row matches a game), but the reader has to handle both shapes.
2. **No player id before 2025-26.** Players are named only (first and family name). Across 2015-26
   there are 641 players who played; 211 of them played for two or more teams. Name is the key, with a
   check for two players sharing a name (none share one inside a team-game).
3. **Team names drift**: "NZ Breakers" and "New Zealand Breakers", "The Hawks" and "Illawarra Hawks",
   Townsville Crocodiles (gone after 2015-16). One mapping table.
4. **2020-21 ran January to June** (COVID hub season) and 2021-22 started in December. The league went from 8 teams
   to 10 (9 in 2019-20 and 2020-21), and a team's regular season from 28 games to 36 (2020-21) and 33 (2025-26 on). Rolling form needs games, not dates.
5. **Who sat is known from 2015-16.** A player listed at 0:00 (or "0" in 2015-16 to 2017-18) dressed and did not
   play; that is the closest thing to "named then out" we have.
6. **nblR is one person's project.** His scheduled updater still points at the 2024-25 season; the
   2025-26 and 2026-27 files come from a separate folder (update-26) and are current to 18 Oct 2026.
   If he stops, in-season updates stop. Fallback: the NBL's stats feed directly (Genius Sports /
   FIBA LiveStats, which nblR itself reads) once its terms are checked.

## Odds: The Odds API

The probe (`nbl/lines/probe.py`, at most 300 credits) is written and runs once from the `nbl lines`
workflow. **It has not run: the repository has no `ODDS_API_KEY` secret** (the AFL probe stopped on the
same thing at 01:16 UTC today). No credits were spent.

What the probe asks: whether the archive holds NBL games one Friday per season from 2020-21; which
Australian books price head-to-head, line and total; whether points, rebounds, assists, threes and
points+rebounds+assists props exist in 2025-26 and 2026-27, from which books and for how many players;
and how many days before the tip those lines first appear.

Search snippets disagree on how far NBL history goes: The Odds API's own NBL page was quoted as
"featured markets from September 2024, other markets (props) from late September 2026", against its
general "from June 2020" for featured markets. If the NBL page is right, there is **no prop history to
backtest against**, only this season's openers recorded from now on, and team-market history starts with
2024-25. The probe settles it.

## Terms, as recorded (nbl data run 1, `terms.md` on the nbl-history release)

| Site | robots.txt | Terms page |
|---|---|---|
| nbl.com.au | allows everything except tipping and test pages | not at /terms-and-conditions or /terms-of-use (404). We do not request anything from this site |
| Genius Sports / FIBA LiveStats (the feed nblR reads) | none | not found at the guessed address. We do not request anything from it while nblR's copy is current |
| aussportsbetting.com | everything allowed except AI training | page blocked to GitHub's runners (403); to be read in a browser |
| BetExplorer | game pages allowed, query-string pages disallowed | not found; not proposed as a source |

## Not found

- **History of announced teams** (named and then withdrawn): nothing found. The NBL does not publish
  pre-game squads in a form anyone archives. Fallback, as the brief allows: build from who actually
  dressed (0:00 rows, 2015-16 on) and who played.
- **Historical injury lists**: nothing found. Same fallback. Going forward, team news can be recorded
  as it is published.
