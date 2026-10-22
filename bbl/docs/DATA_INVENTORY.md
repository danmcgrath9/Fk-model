# BBL data inventory (21 Oct 2026; collection added 22 Oct)

What each source holds, from what season, its terms and its cost. Every figure about Cricsheet is
counted from the pull on the `bbl-history` release (bbl-data run of 21 Oct 2026, zip downloaded
05:17 UTC); the full machine report is `INVENTORY.md` on the release.

## Sources

| need | source | holds | from | terms | cost | status |
|---|---|---|---|---|---|---|
| ball-by-ball, results, toss, XI, venue | Cricsheet `all_json.zip` | every T20 match: 14,686 (3.35m balls) | BBL 2011/12, WBBL 2015/16 | ODC-BY 1.0 (match data since 7 Oct 2026; register always): use freely, credit Cricsheet on any public use. robots.txt only bars indexing `/data/` | free | **pulled**, on the release |
| player identity across sites | Cricsheet people register | 18,651 people, keys for Cricinfo, BBL, Cricbuzz, Opta and 15 others | | ODC-BY 1.0 | free | **pulled** |
| one name per ground | Cricsheet venue register (new, 7 Oct 2026) | `venues.csv`, `venue_names.csv`; Cricsheet says it is still "limited" | | ODC-BY 1.0 | free | **pulled** 22 Oct; our own map stays (the Gabba is under 3 names) |
| bookmaker odds, team markets | The Odds API, `cricket_big_bash` | listed with history from Nov 2020 (their cricket page); h2h is "mainly covered" | 2020/21 | our subscription | shared credits, BBL budget 20,000 | **blocked: `ODDS_API_KEY` secret is not set in Fk-model** |
| player props (runs, sixes, top batter) | The Odds API | unknown: their cricket page lists no props | | | | probe decides |
| live prices through the week | BetMatic odds watch | whatever BetMatic shows for BBL | from the 2026/27 season | ours | none extra | not set up; recording only |
| contracted squads | Wikipedia season pages, API | each club's squad with captain and overseas country: BBL 2014/15, 2023/24 to 2026/27 and WBBL 2026/27 in full (BBL\|16 119 players, WBBL\|12 109); other seasons laid out differently, unparsed | 2014/15 | CC BY-SA, attribute with page and revision | free | **pulled**; announced XIs and late changes still have no archive: record from the paper season on |
| injuries | none found | | | | | **gap** |
| weather and dew | NASA POWER hourly, at each ground | temperature, dew point, humidity, rain, wind at 2 m, every summer each ground was used, and the coming one | 2011 | "no restrictions on the use, access, and/or download" (NASA, CC BY 4.0); credit the POWER Project | free | **pulled**, resumable: weather for 657 of 662 BBL games and 401 of 519 WBBL (nearly all the WBBL gaps are games with no recorded start time) |
| ground coordinates | the Wikipedia article named for each ground, then its Wikidata item (P625) | 133 of 154 venue names placed; 14 of 1,181 games at a ground still unplaced | | CC BY-SA / CC0 | free | **pulled**; a first pass by search was wrong (SCG for the Gabba, Cape Town for the WACA) and was replaced |
| team news, scorecards | cricket.com.au, ESPNcricinfo | | | cricket.com.au bars copying or reproducing its content; Cricinfo's terms not confirmed | | **not collected** |
| historical odds | Betfair BASIC (free), OddsPapi and odds-api.io free tiers | exchange and bookmaker prices | varies | each needs the founder's own account or key | free to paid | **needs the founder** |
| start times, day/night, home side, attendance, coming fixtures | Wikipedia season pages, API | every BBL and WBBL match since 2011/12 with date, local start time, the home side where marked, venue, attendance, toss, result and its Cricinfo id; the full WBBL\|12 and BBL\|16 fixture lists | 2011/12 | CC BY-SA | free | **pulled**: 1,175 of 1,181 Cricsheet games join exactly on the Cricinfo id |

## Cricsheet: what came back

**BBL**, by season (all 15 seasons present; no team-games missing a registry id):

| season | matches | first | last | no result | rain rule | super over |
|---|---|---|---|---|---|---|
| 2011/12 | 27 | 2011-12-16 | 2012-01-28 | 0 | 1 | 0 |
| 2012/13 | 28 | 2012-12-07 | 2013-01-19 | 0 | 3 | 0 |
| 2013/14 | 34 | 2013-12-20 | 2014-02-07 | 1 | 1 | 1 |
| 2014/15 | 34 | 2014-12-18 | 2015-01-28 | 1 | 0 | 1 |
| 2015/16 | 32 | 2015-12-18 | 2016-01-24 | 0 | 0 | 0 |
| 2016/17 | 35 | 2016-12-20 | 2017-01-28 | 0 | 1 | 1 |
| 2017/18 | 43 | 2017-12-19 | 2018-02-04 | 0 | 1 | 0 |
| 2018/19 | 59 | 2018-12-19 | 2019-02-17 | 1 | 4 | 0 |
| 2019/20 | 61 | 2019-12-17 | 2020-02-08 | 2 | 7 | 1 |
| 2020/21 | 61 | 2020-12-10 | 2021-02-06 | 1 | 4 | 0 |
| 2021/22 | 60 | 2021-12-05 | 2022-01-28 | 0 | 3 | 0 |
| 2022/23 | 61 | 2022-12-13 | 2023-02-04 | 1 | 1 | 0 |
| 2023/24 | 41 | 2023-12-07 | 2024-01-24 | 2 | 3 | 0 |
| 2024/25 | 42 | 2024-12-15 | 2025-01-27 | 1 | 1 | 0 |
| 2025/26 | 44 | 2025-12-14 | 2026-01-25 | 1 | 2 | 0 |

- **Gaps:** games abandoned without a ball are not in the file. Missing league match numbers: 2023/24 #3 and #22 (and #40 if that season had 40), 2024/25 #21 and #27. Cricsheet's "Missing" page lists what it lacks; to be checked against it.
- **Power Surge** is recorded: a second powerplay of type `batting` in every season from 2020/21 (in WBBL from 2022/23).
- **X-factor** is recorded as substitutions of reason `supersub`: 25 in 2020/21, 17 in 2021/22, none after (and 47 BBL team-games list 12 players). Concussion substitutes are recorded too.
- Toss winner and decision present in every match. Venue names vary for the same ground and need one map.

**WBBL**: 11 seasons, 2015/16 to 2025/26, 519 matches (10 in 2015/16, then 42 to 58 a season), played October to early December.

**The T20 pool for player history**: 811 players have played BBL or WBBL; the file holds 8,686 other T20 matches they played in (61,498 player-games): IPL (1,243 matches), the Blast, SMAT, BPL, CPL, PSL, Super Smash, The Hundred (5-ball overs, flagged by `balls_per_over`), SA20, ILT20, MLC, internationals and more. Internationals in the same zip (ODIs, Tests) show when a player was away on national duty.

## The Odds API: blocked on the key

The probe (`bbl/lines/probe.py`) ran on push at its committed budget of 0 credits and stopped before any call: `ODDS_API_KEY secret is not set`. The AFL probe's only run failed the same way, so the secret has not been set in this repository yet. Once it is, the free calls run on their own (cricket sport keys including the exact WBBL key, fixtures listed now); the paid stages need the founder's OK and a commit changing `bbl/lines/PROBE_BUDGET` from 0 to 300. Against a fake API charging the documented costs, the paid probe asks for about 200 to 260 credits.

## What this means for the build

- Team model and player projections can start now: everything needed is in hand and free.
- "Teams named" for history = the XI that played (named at the toss). "At the open" = expected XI from the squad's recent games. No announced-squad history exists to test against.
- Weather: decide between Open-Meteo paid (hourly, dew) and BOM free (daily). Dew matters for night games, which needs hourly.
- Props are in or out on the probe's answer alone.


## Collected 22 Oct (bbl-collect workflow; every source pulled once, raw responses on the release)

| table | rows | what it adds | how it joins |
|---|---|---|---|
| `wiki_fixtures.csv` | 1,400 matches | date, local start time, night, marked home side, venue, attendance, toss, result, Cricinfo id | Cricinfo id = Cricsheet's file name: 1,175 of 1,181 exact; 4 dates disagree with Cricsheet (start time dropped for those) |
| `match_context.parquet` | 1,181 | start time for 1,071, marked home side for 465 | match_id |
| `match_weather.parquet` | 1,181 | temperature, dew point, humidity, rain, wind from the start to three hours on; dew-point gap at the end | ground coordinates + start time in the ground's own time zone |
| `wiki_squads.csv` | 854 player-club-seasons | contracted squads with captain and overseas country | names matched to Cricsheet within the club first (`bbl/live/price.py`) |
| `fixtures_2026_27.csv` | 80 priceable (40 WBBL\|12 from 29 Oct, 40 BBL\|16 from 12 Dec) | the pricer's input; finals stay out until their teams are known | |

What it showed (`python -m bbl.research.measure`, sections 5 to 7 of MEASURE.md): BBL day games were won by
the chasing side 34% of the time (47 games) against 55% at night (500); the marked home side won 52.6% of
435 BBL games; and in the BBL the chasing side wins more often the closer the air is to its dew point at the
end of the game (57.6% under a 3C gap, 50.8% over 6C; slope p = 0.02 by permutation over 611 games:
promising, not proven, and only usable after the toss with a forecast). Weather does not predict
first-innings runs (every correlation under 0.1).
