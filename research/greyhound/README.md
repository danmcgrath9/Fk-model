# Greyhound model: Phase 1, the data question (25 Oct 2026)

Brief: docs/GREYHOUND_MODEL_BRIEF.md. This file answers section 3.1: for each source, what it holds, how far back,
how it is accessed, what the terms allow, and what it costs. **No data has been downloaded and no model code written.**
The founder approves a source before anything is pulled.

## How this was researched, and what that means for the terms

This cloud session cannot open the racing sites directly: grv.org.au, topaz.grv.org.au, fasttrack.grv.org.au,
historicdata.betfair.com, developer.betfair.com, betfair.com.au/hub and betfair-datascientists.github.io all fail
(DNS or proxy refusal). Everything below comes from search-engine extracts of those pages, not from reading the pages
in full. That is good enough to say what each source is and who can get it. It is NOT good enough to say a source's
terms allow our use: no terms page was read end to end. **Before any download, the founder (or a session with those
hosts allowed) reads each terms page in full.** The pages to read are listed under each source.

## The answer in one table

| Source | What it holds | How far back | Access | Terms (as far as seen) | Cost |
|---|---|---|---|---|---|
| **Topaz** (GRV's data API, issued through Betfair AU) | Fields, form and results for every Australian state and NZ (jurisdiction codes VIC, NSW, QLD, SA, WA, TAS, NT, NZ); box, finishing position, start price; bulk pull by jurisdiction and month | January 2020 | API key on request: email automation@betfair.com.au (AU/NZ customers). Two older pages say api@betfair.com.au | Key needs: an active Betfair AU account, a deposit made, bets in **at least 100 markets**, and an intent to use the data **for wagering**. First **3 months** for model building; keeping it needs ongoing wagering. Read-only, non-wagering use goes to GRV instead | No price found; reads as free to eligible customers |
| **GRV direct** (Race Data page and API) | Isolynx tracking data: first, mid and home splits, 50m/300m/last-100m times, distance to rail, cumulative and section splits, at The Meadows, Sandown, Healesville, Traralgon (Cranbourne to follow) | Not stated | CSV/JSON on Google Drive **being discontinued** (GRV, June 2026); replacement is an API by email request to GRV | API is **"for personal use only"**. GRV warns these times can differ from the official FastTrack times (two timing systems) | Not stated |
| **FastTrack / state websites** (fasttrack.grv.org.au, thedogs.com.au and the like) | Fields, form, results, grading | Years | Website | thedogs.com.au (GRNSW): "personal, non-commercial use only", no copying, reproducing or republishing without written permission. **Not a source: no scraping** | Free to view |
| **Betfair Hub CSVs** (Betfair AU data science team) | One row per runner per race: BSP, pre-play and in-play weighted average price, max/min matched price and volume, `BEST_AVAIL_BACK_AT_SCHEDULED_OFF`; place BSP not confirmed | The listing shows yearly ANZ greyhound files 2020-2025 and monthly for 2026; another Hub page says January 2023. Settle by opening the listing | Free download, no login | Not seen | Free |
| **Betfair BSP files** (promo.betfair.com/betfairsp/prices) | BSP per runner, greyhounds from UK, Ireland and Australia | 28 May 2008 | Free CSVs | Not seen | Free |
| **Betfair Historic Data** (historicdata.betfair.com, Stream API format) | Every price change in the market: BASIC = last traded price each minute, no volume; ADVANCED = each second with volume; PRO = 50ms with volume | Many years (check per country) | Buy per month or year; AU/NZ customers are told to contact Betfair AU directly | Data licence on the site, not seen | BASIC free; greyhounds ADVANCED **£49/month or £499/year**, PRO **£150/month or £1,499/year** (from a support page about 16 months old; 12-month bulk discount on request) |
| **Bookmaker opening prices, historical** | Nothing found that sells timestamped bookmaker opens for Australian greyhounds. DynamicOdds shows fluc charts (consumer tool, no export or API found); TxODDS sells odds history "for back-testing" but does not say greyhounds; Sportbex and BetsAPI sell live odds | n/a | Quote on request | Not seen | Unknown |
| **Bookmaker opening prices, recorded forward** | TAB's own price at the open, read by our BetMatic bot session (the odds request already takes the code `"Greyhounds"`, betmatic/API_NOTES.md) | From the day we start | Already built for gallops | Ours | Already paid ($199/month BetMatic) |

## What this means for the brief

1. **Form, fields and results: Topaz is the source**, if the founder qualifies and accepts its terms. It is the only
   official, bulk, all-states route found, it goes back to January 2020 (nearly six years, against a target of twelve
   months), and it is issued for exactly what we do: building a model to bet with. Nothing else found comes close.
   GRV's own API adds sectionals at four Victorian tracks, but only for personal use.

2. **BSP and place BSP: free.** The Hub CSVs and the promo BSP files cover the brief's "results (BSP, place BSP)"
   need at no cost, subject to reading their terms and confirming place BSP is in the Hub file.

3. **The timestamped opening price is the gap, and it is the hard requirement.** No historical bookmaker open for
   dogs was found anywhere. Three ways round it, best first:
   - **Record TAB's open from now**, through BetMatic, for every Victorian greyhound race. This is the price we
     would actually bet at, so it is also the most honest. The gallops README already found that back-filled opens
     and live opens are not the same quantity (+41.9% back-filled against -11.6% live); a forward-recorded open
     avoids that trap. The cost is time: a usable holdout needs months.
   - **Buy the Betfair ADVANCED stream** (£499 a year for greyhounds, if the price still holds) and use the first
     exchange prices after the market forms as a proxy open. Caveat: early exchange markets on Australian dogs are
     thin, so the first exchange price is not a bookmaker's open and may be no market at all. It would measure
     whether early prices are softer than BSP, not whether TAB's open is.
   - **Ask TxODDS for a quote** on Australian greyhound odds history. Unknown whether it exists.

   Which bookmaker opens first for dogs, and when, was not found anywhere; it is a thing to measure by recording.
   One Racing Queensland document refers to greyhound and harness markets opening the day before meetings.

## Questions that are the founder's, before anything is pulled

1. **Topaz eligibility.** Does the founder hold a Betfair AU account, funded, with bets in 100+ markets? Keeping the
   key needs "ongoing wagering", and the brief's betting is at TAB through BetMatic; the BSP lay rule would be
   Betfair wagering. Ask Betfair whether wagering elsewhere counts.
2. **Publishing.** The gallops model posts tips and runs a members' list. Topaz is issued for wagering; GRV's API is
   personal use only; thedogs.com.au forbids republishing. Whether a price we derive from Topaz data may be posted is
   a question to put to Betfair and GRV in writing before any greyhound tip is published.
3. **Race-fields law.** Victoria's Gambling Regulation Act 2003 and NSW's Betting and Racing Act 1998 require
   approval to "use" or "publish" race fields, but they are written for wagering service providers. As a punter and
   tipster we are probably outside them; that is a reading, not advice, and worth one question to a lawyer before
   tips are published.
4. **Start recording TAB greyhound opens now?** It costs nothing extra and every week not recorded is a week of
   holdout lost. Needs a check that BetMatic's TAB bot answers greyhound odds requests.
5. **Buy ADVANCED stream data?** Not yet: only once Topaz is in hand, and only if the forward recording looks too slow.

## Pages to read in full before any download

- Topaz: https://betfair-datascientists.github.io/modelling/topazTutorial/ and the terms issued with the key
- GRV Race Data: https://www.grv.org.au/racedata/ and GRV's site terms
- thedogs.com.au terms: https://www.thedogs.com.au/terms-of-use ; GRNSW race fields: https://www.grnsw.com.au/policies/wagering/race-fields-information-use
- Betfair Hub CSV listing: https://betfair-datascientists.github.io/data/dataListing/ and https://betfair-datascientists.github.io/modelling/dataSources/
- Betfair Historic Data: https://historicdata.betfair.com/ (licence, current prices) and https://support.developer.betfair.com/hc/en-us/articles/360019984158-Are-bulk-purchase-discounts-available
- Betfair BSP files: https://promo.betfair.com/betfairsp/prices

## Not done, on purpose

No canonical tables, no download, no model code (brief section 0 and the founder's instruction). Harness was not
researched: the brief does harness only if greyhounds work. The other states' own data terms (QLD, SA, WA, TAS, NZ)
were not found individually; Topaz covers all of them, so they matter only if Topaz is refused.

## Topaz: chosen 25 Oct 2026 (founder: "Okay let's do topaz"), built and waiting for the key

- **The request, changed the same day (founder: "let's deal with them directly and not using it for betting purposes
  yet, but using it for modeling and potentially betting")**: the key is asked of GRV directly, not Betfair. The
  email was SENT 25 Oct 2026 (about 7pm Melbourne) to racedata@grv.org.au, the address the founder read off the Race Data
  page (masked in every copy reachable from here). It says it is research now and may become betting on the
  founder's own account later, and asks for the terms, whether personal-use access covers that later betting or it
  needs the Betfair-issued key, what data the access includes, and history depth and rate limit. No tips will be
  built on it (founder, 25 Oct 2026), so publishing was taken out of the email. The earlier Betfair draft (automation@betfair.com.au) is held,
  unsent: it is the route if GRV says betting needs it.
- **The code**: `greyhound/topaz.py` (client) and `greyhound/pull.py` (bulk runs, one gzipped JSON per state and
  month, resumable, current and previous month always re-pulled), tested in `tests/test_topaz.py` against a fake
  session (13 tests: key header, key never in a repr or error, 404 = no data, 429/5xx retried with Retry-After,
  401 not retried, budget, resume, atomic writes, the terms guard, probe prints column names and never a row).
- **Endpoints are from the unofficial Topaz-api wrapper** (PyPI 0.0.7, MIT): `/api/health`,
  `/api/bulk/runs/{STATE}/{year}/{month}`, header `X-API-Key`. The official docs (topaz.grv.org.au/docs) could not
  be opened from here, so the first run is `mode=probe`, which checks the server answers and lists one day's columns.
- **Two guards before any call**: the `TOPAZ_API_KEY` repository secret, and the repository variable
  `TOPAZ_TERMS_READ=yes`, which the founder sets only after reading the terms that come with the key.
- **Where the data lives**: the `greyhound-history` release, like AFL and NBL. Never in git (`greyhound/cache/` is
  ignored).

When the key arrives: add it as the secret, read the terms, set the variable, run **Actions > gh topaz** with
mode `probe`, then `pull` for VIC from 2020-01. The column list from the probe decides the canonical tables.

## The GRV Race Data page, as read by the founder (25 Oct 2026)

- The page publishes **Isolynx tracking data** for Victorian tracks with the system installed (Sandown, The Meadows,
  Healesville, Traralgon), per meeting, as CSV files and a data summary. The newest meetings listed in the founder's
  copy are 8 to 15 June, so the page may have stopped updating when GRV announced the change below.
- Measures: approximate beam positions; first, mid and home splits; 50m, 300m and last 100m; average distance to the
  rail; cumulative splits; speed in km/h.
- **GRV's own caveats**: the data can carry occasional errors (flagged where known); it varies between tracks and
  distances; Isolynx times can differ from the official FastTrack times because the tracking unit sits between the
  dog's back and neck; **Isolynx times are not official**. A model built on these has to treat them as a separate
  measure from the official split times, never mix the two in one column.
- **Access**: the PDFs and the Google Drive CSV/JSON copies are to be discontinued; the alternative is an API "for
  personal use only", requested from racedata@grv.org.au. Nothing has been downloaded from the page or the Drive.

## Recording opening prices ourselves (founder, 25 Oct 2026: "let's record it ourselves from now on")

No history of timestamped bookmaker opens exists for Australian dogs, so we build one from now. Built, not yet run.

- **How**: `betmatic/greyhound_opens.py` asks our own BetMatic bot for every bookmaker's price on each upcoming
  Victorian greyhound race (the same odds request the gallops watcher uses, code `Greyhounds`). Read-only: no bet is
  ever placed. Rules in `greyhound/opens.py`, 10 tests in `tests/test_greyhound_opens.py`; a dry run against a fake
  BetMatic exercised the loop end to end before commit.
- **The open is a window, not a guess**: a race is polled every 3 minutes until a bookmaker prices it; the open
  happened after the last answered poll without a price and at or before the first poll with one. Both times are
  kept. A bookmaker already priced the first time we looked is recorded with `open_known` False and must never be
  used as an open: the gallops lesson, back-filled opens +41.9% against live opens -11.6%. A poll BetMatic did not
  answer is never read as "closed", because no answer can mean the bot is off. After TAB opens, a race is polled
  every 20 minutes until the jump to see the price move.
- **One request at a time**: an odds answer does not name its race, and the gallops logs show answers arriving late
  (up to 37 seconds) or twice. So an answer is filed only if it arrives while that race's request is the only one
  open; anything else is logged as unattributed and never filed.
- **Only the next race per venue and number**: an odds request names venue and race number, and BetMatic answers for
  the NEXT such race, so tomorrow's R3 at a track racing today is not polled until today's R3 has run.
- **Output**: per race day `opens-YYYY-MM-DD.csv.gz` (date, venue, race, start, runner, bookie, open_known, closed_at,
  first_seen_at, first_price, last_seen_at, last_price), merged across runs so an open caught earlier is never replaced;
  and a raw log of every message per run. Kept on the `greyhound-history` release, never in git.
- **What the first run settles**: whether BetMatic's TAB bot answers greyhound requests at all; whether it answers
  for a race whose market is not up yet (if it does not, no open window can be caught and the method needs a rethink);
  whether BetMatic's startTime is Sydney time (the run prints a raw sample beside how it was read); when TAB opens
  dogs, and which bookmaker opens first.

### Where it runs: a founder decision

The bot only answers while the bot machine is on with its TAB session running, so recording needs that machine on
from early morning to about 11pm, every day. The recorder itself cannot live on GitHub day to day: a job stops at 6
hours, and recording all day would use roughly 40,000 Actions minutes a month against the 2,000 to 3,000 a private
repo gets free. Options: run the script on the bot machine itself (free; it is on anyway), or a small cloud server
(about $6-10 a month). The `gh greyhound opens` workflow (manual, up to 5.7 hours) is for the first test runs.

## Opening prices from BetMatic's Market Open trigger (founder, 25 Oct 2026: "With betmatic there's a feature to have a script waiting for market open")

The better route, and the one to test first, because it needs no machine kept on: short GitHub jobs send and collect.

- **How**: for every runner, a Market Open instruction to TAB that can never fill: minimum odds $1,000 AND maximum
  odds $1.01 (no price meets both), $1 stake, one attempt, one session, no boosts. When TAB opens the market,
  BetMatic's bot fires it, the odds check refuses it before anything reaches TAB, and BetMatic keeps the refusal with
  `current_odds` (TAB's price the bot saw) and `created_at` (when it fired).
- **Why we know the record shape**: our gallops history already holds 168 such refusals ("Current odds is less than
  the notification odds.", amount 0, submit_time null), and Geelong 21 Oct R5's are stamped 11:45:19, the minute the
  founder saw TAB open that race (2026-10-21-geelong-book-opens.md).
- **What a record is, honestly**: TAB's price when BetMatic fired, which is the open only when BetMatic fired on
  time. It has not always: at the same meeting R3 fired at 4:11pm and R1-R2 never fired (betmatic-book.md). A record
  fired within 2 minutes of our sending it means the market was already up and is marked `open_known` False. Before
  any record is trusted as an open, BetMatic's punctuality on dogs is checked against `betmatic/greyhound_opens.py`
  (our own odds requests) on test days.
- **Code**: `greyhound/open_probe.py` (rules, 7 tests in `tests/test_greyhound_open_probe.py`),
  `betmatic/greyhound_open_probe.py` (send / collect; DRY RUN by default; stops at the first refusal from BetMatic;
  collect stops loudly if any record shows money staked), workflow `gh greyhound probe`. Dry run, real-mode run
  and collect were exercised against a fake BetMatic before commit.
- **Open questions only a live test answers**: whether BetMatic accepts a maximum below the minimum (if it refuses,
  the fallback is the minimum alone, the guard the 168 gallops refusals already prove); whether the refusal message
  is the same for dogs; whether BetMatic objects to a few hundred refused instructions a day.
- **First live test, needs the founder's OK in chat**: one race (limit 8), the next Victorian meeting, then collect
  after it runs.

## Test 1: Betfair's free ANZ greyhound files (25 Oct 2026)

Run: `fk harness betfair` (run 40177722771) with the 15 greyhound files and the harness session's two scripts
unchanged (`research/harness/profile_betfair.py`, `research/harness/t_bsp_sharp.py`); they read the shared ANZ file
layout. Terms: the data listing page's only condition is its disclaimer (no warranty, own risk), read 25 Oct through
`fk read terms` by the harness session. Files downloaded fresh from Betfair inside the run; nothing stored or committed.

### What the files hold

- 2,453,636 runner rows, 2020-01-01 to 2026-09-30; 4,778 duplicate (market, selection) rows, because two monthly
  files overlap a day (2020-03 starts 29 Feb, 2020-08 starts 31 Jul). After removing them: 2,448,858 runners in
  338,996 win markets.
- Races by state: VIC 99,938, NSW 85,588, QLD 48,684, NZ 32,529, SA 32,071, WA 25,943, TAS 10,057, NT 4,186.
  Victoria alone is about 1,200 races a month: the brief's "12+ months of Victorian history" is there many times over.
- Per runner: win and place BSP and BSP volume; pre-play max, min, last and weighted average price (WAP) and volume;
  best back and lay at the scheduled off and the book percentages; win and place result; track, distance, grade
  (RACE_TYPE, 145 spellings that need mapping: Gr5, Mdn, Heat, "Gr4/5" ...), box (TAB_NUMBER), dog name, scheduled
  and actual off time.
- **Not in the files**: any opening price (the earliest price is the pre-play max/min/WAP, not a timestamped open);
  no form, times or splits. In-play columns are empty (no in-play betting on Australian dogs).
- **Gaps**: win BSP is missing on 11-17% of runners from Jan to Oct 2020 (except April), and 0-1% from Nov 2020 on.
  Place BSP is filled on 86% of rows overall.

### How sharp is BSP? (races with 4+ runners priced and exactly one winner)

305,093 Australian races, 2,202,864 runners. Median BSP book 1.003 (sum of 1/BSP per race).

| BSP band | runners | wins | expected (1/BSP) | A/E | back ROI at BSP, before commission |
|---|---|---|---|---|---|
| $1-$2 | 78,790 | 48,118 | 48,308.7 | 0.996 | -0.5% |
| $2-$3 | 147,342 | 59,550 | 59,374.8 | 1.003 | +0.4% |
| $3-$4 | 166,325 | 47,821 | 48,017.5 | 0.996 | -0.5% |
| $4-$6 | 269,919 | 55,191 | 55,558.2 | 0.993 | -0.7% |
| $6-$8 | 198,683 | 28,798 | 28,956.8 | 0.995 | -0.5% |
| $8-$11 | 207,012 | 22,243 | 22,306.4 | 0.997 | -0.2% |
| $11-$16 | 248,519 | 19,151 | 19,149.6 | 1.000 | +0.0% |
| $16-$21 | 151,082 | 8,394 | 8,359.6 | 1.004 | +0.6% |
| $21-$31 | 197,992 | 7,870 | 7,902.7 | 0.996 | -0.3% |
| $31-$51 | 188,706 | 4,752 | 4,857.9 | 0.978 | -2.4% |
| $51+ | 348,481 | 3,205 | 3,369.6 | 0.951 | -9.9% |
| all | 2,202,864 | 305,093 | 306,161.9 | 0.997 | -1.9% |

Winner log loss on the same 303,238 Australian races (lower is sharper): **BSP 1.5044, pre-play WAP 1.5067, best back
at the scheduled off 1.5070.** The two date halves agree (A/E 0.996 and 0.997; BSP log loss 1.5159 and 1.4926).
By state, longshots ($21+) are most over-bet in WA (A/E 0.901) and SA (0.963), and slightly under-bet in NSW (1.022).

### What it means

1. **BSP on Australian dogs is fair from $1 to $21**: A/E within 0.7% of 1.000 in every band, both halves, every year.
   Backing at BSP is the brief's "expect about zero", confirmed before commission and negative after it.
2. **The favourite-longshot bias is at the top end only**: runners over $31 win 2-5% less often than BSP says. A lay
   at BSP over $51 makes +9.9% of the backer's stake before commission; commission comes off every winning lay, so
   most of that goes, and it is a known effect, not a model's edge. Not an angle until a test with commission, in
   two halves, says so.
3. **The model's bar**: BSP's 1.5044. A model is informative where it beats the price it bets into; the open is not in
   these files, so that comparison waits for recorded opens (the BetMatic probe) or the brief's Phase 2.
4. **These files are the results-and-BSP half of the history** (box, grade, distance, track and result for 339,000
   races, free). Form, run times and first splits still need Topaz.

## The repository is public (checked 25 Oct 2026)

fk-model is a public repository, so its releases and Actions artifacts can be downloaded by anyone. Two corrections
follow. (1) The Actions-minutes figure in "Where it runs" above assumed a private repository; Actions are free on a
public one. (2) GRV's API is "for personal use only", so Topaz data must never be stored on a release here:
`gh topaz` now refuses to pull while the repository is public (the probe, which prints only column names and fill
rates, is still allowed). Private storage, or a private repository, has to be chosen before the key arrives.

## Plan: our own base ratings, Form King's job for dogs (founder, 25 Oct 2026: "Yeah nice")

There is no Form King for greyhounds, so the per-run benchmarks the gallops model leans on are built from raw results.
Needs Topaz runs carrying time, first split, margin and in-run positions (the probe confirms); nothing is built first.

| Form King (horses) | Ours (dogs) | Built from |
|---|---|---|
| Par per track, distance, class | Par per track, distance, grade | Winning times of EARLIER races only |
| Track speed on the day | Meeting variant | That meeting's times against par |
| Speed / vs-track rating | Run rating, in lengths | Time against par and the variant |
| Sectional / last-600 benchmarks | First-split rating | First split against the track-distance par (early speed decides most dog races) |
| vs-class rating | Class rating | Who beat whom, updated race by race |
| Peak and recent ratings | Best and recent ratings | The dog's own runs |
| (debut runners) | Trial ratings | Topaz trial results |

Rules carried from the gallops: point-in-time only (a par or variant uses nothing from the race day onward); reset
pars at a track change (resurface, rail move, new distance) rather than averaging across it; Isolynx times kept apart
from official times; stewards' comments used for interference if Topaz carries them. Judged only by whether a model on
these ratings beats the opening price and BSP (winner log loss 1.5044), by month, in both date halves.

## Test 2: box bias, and whether BSP already prices it (25 Oct 2026, `research/greyhound/t_box_bias.py`, run 40182088401)

305,093 Australian races, 2,202,864 runners, 260 track-distances. TAB numbers 9-10 (50,679 reserves who took a
scratched dog's box, real box unknown) stay in their races but out of the box rates.

| box | runners | win rate | field-size share | wins / share | A/E at BSP | A/E first half | A/E second half |
|---|---|---|---|---|---|---|---|
| 1 | 290,717 | 19.1% | 14.1% | 1.35 | 0.988 | 0.984 | 0.992 |
| 2 | 287,760 | 15.8% | 14.1% | 1.12 | 0.993 | 0.986 | 0.999 |
| 3 | 243,246 | 13.1% | 13.4% | 0.98 | 1.007 | 0.997 | 1.016 |
| 4 | 285,341 | 13.3% | 14.1% | 0.95 | 1.000 | 1.002 | 0.998 |
| 5 | 233,501 | 12.3% | 13.7% | 0.90 | 1.010 | 1.007 | 1.014 |
| 6 | 247,680 | 11.9% | 13.6% | 0.88 | 1.010 | 1.012 | 1.008 |
| 7 | 278,182 | 12.4% | 13.9% | 0.89 | 1.009 | 1.016 | 1.003 |
| 8 | 285,758 | 13.5% | 14.1% | 0.96 | 0.970 | 0.981 | 0.959 |

By track and distance (2,000+ races; box 1's wins against its field-size share): from 1.76 at Richmond 401m, 1.71
Albion Park 395m and 1.61 Sandown Park 515m down to 0.95 at Capalaba 366m, where box 8 is the strong box (1.38). The
full table is in the run log. A/E at BSP by box stays mostly within about 0.05-0.15 of 1 per track-distance, noisy at
these sample sizes.

Does a point-in-time box rate (that track and distance, earlier days only, shrunk 200 starts toward the national rate
for the box) add to BSP? Fit before 19 Jun 2023, scored on the 152,470 races after (12 races left out because a
runner's BSP chance was zero: bad BSP rows, e.g. at Capalaba):

| model | BSP weight | box weight | test log loss |
|---|---|---|---|
| BSP alone | 1.004 | - | 1.49255 |
| BSP + box rate | 1.005 | -0.005 | 1.49255 |

The box rate alone, with no prices, is 1.95243 against 1.96646 for equal chances.

**What it means**: the box is real and large (box 1 wins 35% more than its share, 76% more at Richmond 401m), and the
market has priced it completely: at BSP the box adds exactly nothing. Box 1 and box 8 are, if anything, slightly
over-bet at BSP (A/E 0.988 and 0.970, both halves). The box stays in the model as a feature, because the interaction
with a dog's early speed and its neighbours' is where any edge would be, but box on its own is not an angle.

## Test 3: Betfair's Iggy model against BSP (25 Oct 2026, `research/greyhound/t_iggy.py`, run 40181694455)

Iggy's daily results files (free, same data listing; V1 to Aug 2024, V2 since) joined to the ANZ files by market and
selection. Columns: Date, Track, Race Name, Race, MarketId, SelectionId, Rug, Dog, Rated Price, Early Speed,
WIN_RESULT, WIN_BSP, PLACE_RESULT, PLACE_BSP, WIN_VALUE. Kept: 278,526 Australian races (31 Mar 2020 to 30 Sep 2026)
where Iggy priced every runner with a BSP, 4+ runners, one winner. Iggy's rated prices renormalised per race.

Winner log loss on the same 277,455 races (lower is sharper):

| group | races | Iggy | BSP | pre-play WAP |
|---|---|---|---|---|
| all | 277,455 | 1.7023 | 1.5074 | 1.5095 |
| V1 (to Aug 2024) | 188,352 | 1.7260 | 1.5167 | 1.5184 |
| V2 (from Aug 2024) | 89,103 | 1.6524 | 1.4878 | 1.4907 |
| 2025 | 43,346 | 1.6565 | 1.4947 | 1.4965 |
| 2026 | 27,841 | 1.6329 | 1.4639 | 1.4687 |

Iggy's calibration (wins against its own chances): $1-$2 0.820, $2-$3 1.034, $3-$4 1.077, $4-$6 1.051, $6-$8 0.990,
$8-$11 0.938, $11-$16 0.913, $16-$21 0.900, $21-$31 0.887, $31-$51 0.886, $51+ 1.049. It is too sure of its short
favourites and too generous to $8-$51 runners.

Does Iggy add to BSP (fit before 7 Jul 2023, score the 139,186 races after)? BSP alone 1.49680; BSP + Iggy 1.49676,
Iggy's weight -0.028. **Nothing.** Backing at BSP where BSP is at least k times Iggy's fair price, flat 1 unit:

| k | half | bets | wins | A/E at BSP | ROI before commission | after 8% |
|---|---|---|---|---|---|---|
| 1.2 | first | 512,143 | 29,783 | 0.983 | -3.1% | -10.3% |
| 1.2 | second | 524,810 | 29,727 | 0.987 | -4.3% | -11.5% |
| 1.5 | first | 400,473 | 17,760 | 0.976 | -3.4% | -10.8% |
| 1.5 | second | 412,533 | 17,418 | 0.976 | -5.8% | -13.0% |
| 2.0 | first | 280,416 | 8,923 | 0.979 | -4.0% | -11.5% |
| 2.0 | second | 293,285 | 8,579 | 0.965 | -7.0% | -14.2% |

**What it means**: the best free Australian greyhound model is far behind BSP (1.70 against 1.51; V2 1.65 against
1.49), badly calibrated, adds nothing to BSP and loses where it disagrees with it. Iggy is not the bar; BSP is. One
thing in its files is worth keeping: an **Early Speed** rating on every runner since 2020, which no other free source
has. Whether it adds to BSP is a separate test, and it is a candidate feature for the first-bend layer until Topaz's
first splits arrive.

## Test 4: model v0, our own price from the free files only (25 Oct 2026, `research/greyhound/gbm_v0.py`, run 40182657412)

Founder: "we want to build our own model to be better than Iggy and we can bet early." v0 is what the free data can
do before Topaz: no run times, splits, margins or finishing positions (the Betfair files have only win/place results).
Inputs, all from earlier days: the dog's past BSPs, wins, places, results against the market (won minus 1/BSP), days
since its last run, last box, distance change, same track; the race's box, box rate (point-in-time), field size,
distance, track, state, grade; each also relative to the field. LightGBM, softmax within the race, trained on the BSP's
chances (the gallops recipe) and, as a check, on winners. Fit before 19 Jun 2023 (152,611 races), rounds and blend
chosen 19 Jun 2023 to 25 Jan 2025 (75,282), scored once from 25 Jan 2025 (77,200; 68,174 with every price present).

| price (last quarter, same 68,174 races) | log loss | first half | second half |
|---|---|---|---|
| v0, trained on BSP chances | 1.6743 | 1.6868 | 1.6619 |
| v0, trained on winners | 1.6841 | 1.6972 | 1.6713 |
| Iggy (V2 in this window) | 1.6460 | 1.6585 | 1.6338 |
| pre-play WAP | 1.4848 | 1.4991 | 1.4708 |
| BSP | 1.4818 | 1.4975 | 1.4664 |

Blended with the market (weights fitted on the middle quarter): v0 + WAP 1.4844 (+0.0004 on WAP alone), v0 + BSP
1.4817 (+0.0001), with v0's weight slightly negative both times. Every month of the 21 scored: v0 behind Iggy by
0.015 to 0.057, and both far behind BSP. Top inputs: the dog's last-5 average BSP against the field's (28%), place rate
against the field's (19%), win rate (9%), last BSP (7%).

**What it means**: from these files v0 is mostly a summary of the market's past opinion of each dog, and it neither
beats Iggy (1.674 against 1.646) nor adds anything to the market. That is the expected answer and the useful one: the
free files hold no running form, and running form (times, first splits, margins, in-run positions) is exactly what
Iggy uses and what Topaz supplies. Beating Iggy and finding something the early market misses waits on Topaz.

The "+ Iggy early speed" fit in this run is not a test: Iggy's files carry Early Speed only from January 2024 (the
2020-2023 files have no such column), so the training window above never saw it and the fit came out identical to
v0. Rerun on a window starting 1 Jan 2024 (Test 4b).

### Test 4b: the same, from January 2024, with Iggy's early speed (run 40183623864)

127,012 races from 1 Jan 2024 (dog histories still use every earlier run). Fit before 10 May 2025 (62,817), rounds
and blend 10 May 2025 to 13 Jan 2026 (31,745), scored from 13 Jan 2026 (32,450; 26,702 with every price present).
Leak check: the dog Iggy rates fastest early wins 22.4% against a BSP chance of 22.4% (A/E 1.000), so the rating does
not know the result, and the market already prices it exactly.

| price (same 26,702 races) | log loss | first half | second half |
|---|---|---|---|
| v0, BSP chances | 1.6588 | 1.6669 | 1.6507 |
| v0, winners | 1.6731 | 1.6806 | 1.6657 |
| v0 + Iggy early speed | 1.6542 | 1.6612 | 1.6472 |
| Iggy | 1.6346 | 1.6405 | 1.6287 |
| pre-play WAP | 1.4703 | 1.4772 | 1.4634 |
| BSP | 1.4654 | 1.4717 | 1.4593 |

Blends with the market: + WAP 1.4700 (+0.0003), + BSP 1.4653 (+0.0001). Early speed helps v0 a little (1.6588 to
1.6542, both halves) but v0 still trails Iggy in all 9 months and adds nothing to the market. Conclusion unchanged:
the free files cannot build a model worth betting; the next model waits on Topaz (founder, 25 Oct 2026: "V0 has no
data hahaha, let's wait for data").

## Test 5: the ratings engine, and v0 with a who-beat-whom rating (26 Oct 2026, runs 40262271801 and 40262278279)

**The engine** (`greyhound/ratings.py`, ready for Topaz; only `topaz_to_runs()`, the column mapping, waits for the
probe): point-in-time pars per track and distance (median winning time and first split of earlier races), a meeting
going variant (that meeting's winners against par, shrunk 2 pseudo-races toward 0), time and first-split ratings in
lengths (0.07 s a length), an Elo over finishing order (every pair a match; a day's changes land when the day ends),
and each dog's form as it stood at the end of the previous day, trials included. 9 tests in
`tests/test_greyhound_ratings.py`, hand-checked pieces plus a simulation where every dog's true speed is known: the
time ratings recover it at r > 0.85, the going variant beats no variant, split ratings recover early speed at r > 0.85,
and form and Elo rank dogs at r > 0.7 out of sample. That simulation caught a same-day leak (a dog racing twice in a
day saw its first run) in both the form and the Elo; both now use earlier days only.

**v0 + Elo**: the Elo built from the only finishing order the free files hold (winner first, placegetters tied second,
the rest tied behind), added to v0 and relative to the field.

| last quarter | races | v0 before (Test 4/4b) | v0 + Elo | Iggy | pre-play WAP | BSP |
|---|---|---|---|---|---|---|
| 2020-2026 window, scored from Jan 2025 | 68,174 | 1.6743 | **1.6419** | 1.6460 | 1.4848 | 1.4818 |
| first half / second half | | 1.6868 / 1.6619 | 1.6554 / 1.6285 | 1.6585 / 1.6338 | | 1.4975 / 1.4664 |
| 2024-2026 window, with early speed, scored from Jan 2026 | 26,702 | 1.6542 | **1.6228** | 1.6346 | 1.4703 | 1.4654 |
| first half / second half | | 1.6612 / 1.6472 | 1.6305 / 1.6152 | 1.6405 / 1.6287 | | 1.4717 / 1.4593 |

v0 + Elo now beats Iggy in both windows and both halves: by 0.004 over 2025-26 (ahead in 16 of 21 months, behind in
Jan-Mar and Oct-Nov 2025) and by 0.012 in 2026 with early speed (ahead in all 9 months). Blended with the
market it still adds nothing: + WAP +0.0003, + BSP +0.0001, our weight slightly negative. **What it means**: the first
real step beyond Iggy came from the strength rating, from finishing order alone; the market still prices everything v0
knows. The same Elo on Topaz's full finishing order and margins is the next step.

## Test 6: Benter's two stages on the free files (26 Oct 2026, `research/greyhound/gbm_benter.py`, runs 40262967267 and 40262973312)

Stage 1 is the fundamental model: form only (box, field, distance, the box rate, runs, win and place rates, last
start, last five, days since, distance change, same track, Elo), trained on WHO WON, no price of any kind. Beside it, a
model of the dog's market history alone (its past BSPs and how it ran against them) and, as a check, the gallops
recipe (everything, trained on BSP chances). Stage 2 is Benter's second logit: chance proportional to each input's
chance raised to a weight, weights fitted on the middle quarter, scored once on the last quarter.

**Stage 1 alone, winner log loss, last quarter:**

| | 2020-2026, 68,174 races from Jan 2025 (halves) | 2024-2026, 26,702 races from Jan 2026 (halves) |
|---|---|---|
| stage 1: form only | 1.6855 (1.6992 / 1.6721) | 1.6765 (1.6837 / 1.6693) |
| stage 1: form + early speed | not in this window | 1.6723 (1.6784 / 1.6663) |
| market history only | 1.7606 (1.7713 / 1.7500) | 1.7531 (1.7596 / 1.7467) |
| copy of BSP (check) | 1.6409 (1.6545 / 1.6276) | 1.6276 (1.6357 / 1.6196) |
| Iggy | 1.6460 (1.6585 / 1.6338) | 1.6346 (1.6405 / 1.6287) |
| pre-play WAP | 1.4848 | 1.4703 |
| BSP | 1.4818 | 1.4654 |

**Stage 2, gain over the market alone (positive = better):**

| blend | 2020-2026 + WAP / + BSP | 2024-2026 + WAP / + BSP |
|---|---|---|
| stage 1 + market | −0.0000 / −0.0002 | +0.0001 / −0.0000 |
| market history + market | +0.0003 / +0.0001 | +0.0004 / +0.0002 |
| stage 1 + market history + market | +0.0001 / −0.0001 | +0.0004 / +0.0002 |

The weights tell the same story: the market's weight is 1.01 to 1.07 and every model's is near zero or negative
(−0.075 at most), so the fitted blend sharpens the market slightly and gives our models nothing.

**What it means.** (1) Trained on winners, stage 1 is 0.045 worse than the same inputs trained on BSP chances
(1.6855 against 1.6409): with only win/place in the free files, the market's chances are a far less noisy label than
one winner per race, so the copy recipe is the better way to learn from this data, as it was for the gallops.
(2) Stage 2 finds nothing: the market already prices everything the free files hold, form, Elo and the dog's own price
history. Benter's edge came from fundamentals the public was underweighting; on win/place and box alone there is no
such gap at BSP. (3) The structure is right and stays: when Topaz's times, splits and full finishing order arrive,
stage 1 gets the inputs Benter's had, and when recorded opens exist the opening price replaces WAP/BSP as the
market in stage 2, which is the price BetMatic would actually take.

## Test 7: betting angles at BSP (26 Oct 2026, `research/greyhound/t_angles.py`, runs 40264014700 and 40264692031)

Founder: "find betting angles like our horse bets where we can send pre market slips to betmatic and get the best
odds". No greyhound opening-price history exists (TAB's or anyone's), so every angle is tested at BSP, the sharpest
price there is (Test 1): an angle that holds at BSP is a candidate for the open; one that fails at BSP needs a softer
open to work, and that test waits for recorded opens. Rules: positive after 8% commission in BOTH date halves, A/E
beside ROI, every angle printed. Structural angles over the whole period, 305,093 races, halves at the median date.
Model angles on the last quarter (77,200 races from 25 Jan 2025), models fitted before the median date. Lays are
given two ways: ROI per unit of backer's stake, and the return on the money actually at risk (the liability, BSP − 1).

**Structural angles:**

| angle | side | bets 1st / 2nd half | A/E | ROI after commission | return on money at risk | both halves |
|---|---|---|---|---|---|---|
| every runner | back | 1,101,282 / 1,101,582 | 0.996 / 0.997 | −8.3% / −9.0% | | no |
| favourites (BSP rank 1) | back | 153,121 / 153,025 | 0.998 / 1.003 | −4.9% / −4.1% | | no |
| box 1, strong box-1 track and distance (box rate ≥ 1.5×) | back | 23,955 / 29,081 | 0.993 / 1.016 | −7.5% / −6.9% | | no |
| top Elo in the race, BSP rank 3+ | back | 42,346 / 46,658 | 0.962 / 0.945 | −11.8% / −13.8% | | no |
| the same, under $11 | back | 27,307 / 28,457 | 0.969 / 0.958 | −10.4% / −10.8% | | no |
| first-up after 28+ days, under $6 | back | 23,440 / 24,624 | 1.020 / 0.990 | −3.4% / −6.5% | | no |
| distance up 100m+ | back | 63,822 / 57,730 | 1.014 / 1.005 | −6.9% / −10.0% | | no |
| distance down 100m+ | back | 66,238 / 61,224 | 1.011 / 0.990 | −6.7% / −7.2% | | no |
| first start in the files, under $6 | back | 13,306 / 8,512 | 0.988 / 0.992 | −6.7% / −7.1% | | no |
| lay every runner over $101 | lay | 84,266 / 100,026 | 0.872 / 0.881 | +7.6% / +10.1% | +0.04% / +0.00% | yes, worth nothing |
| lay every runner over $51 | lay | 168,290 / 180,173 | 0.953 / 0.950 | +0.9% / +2.9% | +0.01% / +0.00% | yes, worth nothing |
| lay $31-$51 | lay | 93,695 / 94,960 | 0.995 / 0.962 | −7.2% / −3.7% | −0.18% / −0.10% | no |
| lay $21-$31 | lay | 91,967 / 93,460 | 0.990 / 1.006 | −6.9% / −8.2% | −0.28% / −0.33% | no |
| lay box 8 at a weak box-8 track and distance (box rate ≤ 0.8×) | lay | 9,748 / 16,023 | 0.965 / 0.907 | +2.2% / +14.7% | +0.06% / +0.35% | yes, see below |
| the same, under $11 | lay | 4,073 / 6,444 | 0.974 / 0.934 | −3.7% / +0.6% | −0.79% / +0.13% | no |
| the same, $11-$51 | lay | 3,926 / 6,524 | 0.949 / 0.827 | −0.3% / +10.5% | −0.01% / +0.45% | no |
| the same, over $51 | lay | 1,749 / 3,055 | 0.713 / 0.483 | +21.6% / +53.3% | +0.17% / +0.33% | yes |
| box 8 anywhere, over $51 | lay | 20,573 / 22,645 | 0.958 / 0.891 | +2.2% / +9.6% | +0.02% / +0.00% | yes, worth nothing |
| lay the BSP favourite when its Elo ranks 5th or worse | lay | 13,383 / 14,235 | 0.992 / 1.025 | −4.5% / −8.1% | −2.03% / −3.78% | no |
| lay first-up after 28+ days, under $4 | lay | 13,513 / 14,523 | 1.018 / 0.992 | −6.7% / −4.0% | −3.77% / −2.29% | no |

**Model angles** (back where our chance × BSP is 1.2 or 1.5 and up, lay where it is 0.6 or 0.5 and down, in price
bands): all sixteen lose in both halves, for v0 + Elo and for stage 1 form only. The best back is form only, $2-$8,
edge ≥ 1.2: 18,129 / 18,169 bets, A/E 1.001 / 0.985, −6.7% / −8.1%. The best lay is form only, under $6, ≤ 0.6:
A/E 0.984 / 1.000, −3.4% / −5.5% per stake. Our models are 0.16 worse than BSP on log loss (Tests 5-6), so where they
disagree with BSP, BSP is usually right; the A/E of every "value" selection is below 1.

**What it means.** (1) Nothing backs at BSP: every back angle has A/E between 0.94 and 1.02, so before commission
they are at best level, and after 8% they lose. (2) The lays that pass are the favourite-longshot bias, which Test 1
already showed (BSP over $51 wins 5% less than it says): real, but the return on the money at risk is 0.00% to 0.04%,
because laying a $200 shot risks $199 to win 92c. Not worth a bank. The weak-box-8 longshot lay (+0.17% / +0.33% on
risk) rests on few winners (1,749 and 3,055 bets at over $51, where a $51 shot wins about one race in fifty, so a few dozen expected winners a half; the run does not print the counts); it is one cell among 31 tried, and
the box-8-under-$51 cells beside it fail, so it is noise until a third period says otherwise. (3) BetMatic sends to
the TAB, which takes back bets only, so no lay angle could go on a slip anyway. **For BetMatic slips, the only
possible edge left is the price itself: a TAB open above the dog's fair price.** That is the horse approach (a minimum
price on every slip), and it needs two things we do not have yet: recorded TAB opens to measure how often an open
beats BSP, and by how much, and a fair price good enough to trust when it disagrees with the open. On the second,
BSP is the fair price after the fact; the question for the open is whether a TAB open above our pre-race estimate of
BSP (the copy recipe, 1.6409, the best pre-race estimate we have) wins more than its price says. That test is
`t_angles.py`'s model section rerun at the recorded open, and it is the first thing to run once a few weeks of opens
exist.

## Betwatch: a possible source of TAB opening prices (26 Oct 2026, founder: "could you check betwatch")

Betwatch Pty Ltd (betwatch.com, betwatch.com.au redirects there) is an Australian odds-comparison site for
thoroughbreds, harness and greyhounds across 50+ Australian bookmakers; the website is free to sign up. Its API is
GraphQL at api.betwatch.com (key in an `X-Api-Key` header; keys by request to api@betwatch.com; no pricing page).
What the public SDK (github.com/betwatch/betwatch-sdk-python, read 26 Oct) says the API holds: races by date range
and type (`Greyhound` is one), every runner's fixed win and place price per bookmaker (`Tab` is one) with its
**flucs**, the list of price changes each with a timestamp, so the first fluc is that bookmaker's open; and the
runner's Betfair SP and back/lay. NOT known: whether past races can be queried with their flucs, and how far back.
The SDK's examples only ask for the last 2 to 7 days.

Terms (betwatch.com/terms, read through fk read terms, run 40265276223): API data "may not be used for any commercial
purpose without prior consent"; no software or service that competes with Betwatch; high-frequency or abusive use can
be cut off; the data carries no licence for third-party race fields or results. They also offer a browser extension
that fills bookmaker bet slips.

Emailed api@betwatch.com from the founder's Gmail, 26 Oct 2026 (founder: "Yep sounds good to me"), asking how far
back greyhound flucs go (TAB especially), what a key costs and its limits, and whether modelling for his own betting
is fine under the commercial-use clause. If the history goes back a few years, it replaces both BetMatic's $3,000
history and weeks of recording our own opens, and Test 7's model angles are rerun at the TAB open.

## The first open probe: Geelong R1, Tuesday 27 Oct 2026 (runs 40452957805 collect, 40453167880 diagnose)

Eight instructions, one per runner in Geelong R1 (2:42pm AEDT), sent 25 Oct 08:36-08:37 UTC, each min $1,000 /
max stake $1.01, $1, TAB, one attempt, so that BetMatic would refuse it at TAB's open and keep the price and time.

**What happened:**

- **BetMatic did fire at the open.** Every instruction carries `triggered_at` 2026-10-27 07:22:34-35 AEDT, about
  7h20m before the race and two days after it was sent (25 Oct 19:36 AEDT), so this is a genuine market-open trigger
  rather than a fire on sending. TAB opened Geelong R1's market on race morning around 7:22am.
- **The bot then skipped every one before reaching TAB.** The bot's log for each, at 07:22:40-41: "Skipped - Account
  balance is below Min Stake ($) (1)", then "Checked availability — no sessions available for this notification".
  The TAB account held less than $1, so the bot dropped the instruction before checking the price. That is why
  there is no refusal record, no TAB price and no time of fire in the bet records: `collect` reads 8 pending,
  0 usable as an open.
- **Nothing was staked.** No bet record exists for any of the eight.
- Runner 2 was scratched (the race's runner list is 1, 3-8). Result 1/4/3/6. BetMatic's stored race carries the
  Betfair SP of every runner and the tote, but no TAB fixed price.

**What it means.** The mechanism works up to the bot: BetMatic linked all eight to the right race and fired them at
TAB's open. The probe cannot record a price while the TAB account is below the $1 minimum stake, because the bot
filters on balance first. The account needs at least $1 in it, which is the founder's call because it is the same
account the gallops bets use, and the bot's TAB session must be running at the open (about 7:20am on race day for
Victorian dogs). The safety does not change: the instruction still cannot fill (min $1,000, max $1.01). The bot's
log line names the TAB account holder and this repository's Actions logs are public, so `bot_logs` now redacts the
name before printing (`redact_account`, tests in `tests/test_betmatic_redact.py`).

## GRV's answer on Topaz access (30 Oct 2026)

GRV replied on 30 Oct from Jason Adams (Fan Development & Content Lead, Customer & Commercial Development) after a
follow-up on 29 Oct to racedata@grv.org.au, with comments@grv.org.au (the Feedback Office) copied. racedata@ is the
only address on grv.org.au/racedata, so the request went to the right place. His answers, against the four questions:

1. **Terms:** "We have terms of use/agreements in development." Access is currently given to "personal users who bet
   on Victorian greyhound races"; commercial users are "a completely different conversation".
2. **Modelling now, own betting later:** "Yes, personal use for that purpose is fine."
3. **Data:** "everything seen in our results/form guides", plus Isolynx tracking at the handful of tracks with it.
4. **History and pace:** form "goes back a long way", Isolynx only recent years; rate limit "I believe ... 80 per minute".
   `greyhound/pull.py` pauses 2 seconds between calls (30 a minute) by default.

No key yet. The founder's reply (30 Oct) asks for a key, whether access covers other states, and whether a one-off
history pull at under 80 a minute is fine. When the key comes: the founder adds it as the `TOPAZ_API_KEY` Actions
secret (never in chat or a file), reads whatever terms exist and sets `TOPAZ_TERMS_READ=yes`. The data is personal use,
so it cannot sit on this public repository's releases (the pull refuses while the repo is public); private storage
(a separate private repository is the simplest) is the founder's call before the first pull.

## Topaz storage: a private data repository (founder, 3 Nov 2026: "We are keeping it public", then "go ahead with the private repo")

Fk-model stays public: code, workflows and the write-ups (our own results, not GRV's data). The raw Topaz files go to
a separate PRIVATE repository, **danmcgrath9/fk-greyhound-data**, on its `topaz-history` release, and nowhere else.
Cost: nothing (unlimited free private repositories; no workflow runs inside it, so its Actions minutes are unused).

`gh-topaz.yml` mode=pull writes there with the `GREYHOUND_DATA_TOKEN` secret and refuses unless the token is set,
the target is not Fk-model itself, and GitHub reports the target as PRIVATE. The variable `GREYHOUND_DATA_REPO`
overrides the default name. mode=probe (column names and fill rates only) needs none of this. The open-price files
(our own recordings through BetMatic) stay on Fk-model's `greyhound-history` release.

Founder setup, once (this session cannot create repositories: GitHub answered 403):
1. Create the repository `fk-greyhound-data`, **Private**, ticking "Add a README file" (a release needs one commit).
2. Create a fine-grained personal access token: Repository access "Only select repositories" = fk-greyhound-data;
   Permissions: Contents read and write. Nothing else.
3. Add it to Fk-model as the Actions secret `GREYHOUND_DATA_TOKEN`.
4. With `TOPAZ_API_KEY` and the variable `TOPAZ_TERMS_READ=yes` also set: probe first, then pull VIC
   (founder, 3 Nov: "I'm happy with Vic to just test for now").

## The Topaz mapping, written from GRV's published API description (4 Nov 2026)

topaz.grv.org.au/docs/ is a Swagger page over a public description, `/docs/swagger.json` (Topaz API 1.8.1, 79
endpoints, read through fk read terms, run 41746182491). What it settles:

- Our client is already right: `GET /api/bulk/runs/{authority}/{year}/{month}` (and `/{day}`), key in `X-API-Key`.
  Authorities: ACT, NSW, NT, QLD, SA, TAS, VIC, WA, NZ (VIC only for us so far). **Years from 2013**, so the history
  is about 13 years, against six in Betfair's free files.
- Each bulk row (`BulkRunOutput`, 70 fields) holds the race (raceId, meetingId, meetingDate, trackCode,
  distanceInMetres, raceType, grades), the dog (dogId, dogName, sex, whelped, sire, dam, trainer, owner, weight), the
  run (boxNumber, rugNumber, place, resultTime, resultMargin, first to fourth split times and positions, pir, jump and
  run-line codes, comment, abnormalResult, scratched) and **startPrice**.
- Also there: Isolynx splits and positions per race and per dog, trial results (`/trialresult`), fields with late
  scratchings, records, and per-dog form.

`greyhound/ratings.py` `topaz_to_runs()` now maps those fields to the canonical runs table and `load_topaz()` reads the
pull's files; three tests in `tests/test_greyhound_ratings.py` replace the "waits for the probe" placeholder. Three
meanings the spec does not state are handled defensively and are what the first probe has to confirm: resultMargin is
lengths behind the winner (the winner's is set to 0 whatever it holds), resultTime is the dog's own time (win_time is
the winner's), and a trial is a race whose raceType or raceTypeCode says "trial".

The founder submitted the Topaz sign-up on 4 Nov with Jason's email thread attached. Support: topazhelpdesk@grv.org.au.

## First Topaz probe with the founder's key (4 Nov 2026, runs 41758947572 and 41759363894)

GRV approved VIC on 4 Nov (Available Data: VIC ticked) and the founder added `TOPAZ_API_KEY` and
`TOPAZ_TERMS_READ=yes`. Health answered; VIC 28 Oct 2026 returned 372 runs in 51 races (353 ran, 19 scratched),
with exactly the 70 BulkRunOutput fields. Fill: place, resultTime and resultMargin on 345 of 372 (every runner that
finished), first split on 348, second split on 33, third on 3, fourth and startPaceCode on none, startPrice on all 372.

The counts-only mapping check settled the three open meanings:

| question | answer on 51 races | mapping |
|---|---|---|
| winner's resultMargin | 0 of 51 winners hold 0: it is the margin over second | winner's margin set to 0 |
| resultTime | differs between runners in 51 of 51 races: each dog's own time; winner fastest in 51 of 51 | used as is |
| resultMargin unit | r = 1.000 against the time gap, at 0.07 of its size in lengths: **seconds**, not lengths | divided by 0.07 into lengths |
| trials | none of the 15 race types (Grade 5, Rank Limit, Maiden, Mixed, Restricted Win, Free For All, heats, finals) | the "trial" flag stays as a safety net |

The third row was the one wrong assumption: the first cut of `topaz_to_runs` read the margin as lengths, so a dog
0.25 s behind would have been 0.25 lengths behind instead of 3.6. It is fixed and the tests are in seconds now.

## Test 8: the full Victorian history, profiled (4 Nov 2026, gh topaz run 41776231001)

The pull (runs 41762509963 and 41776231001; day by day, 8 at a time under 72 a minute, cached in this repository's
Actions cache, never published) holds **197,101 races and 1,616,034 runners, 52,183 dogs, 15 tracks, 2 Jan 2013 to
3 Nov 2026**, about 1,200 meetings and 14,000 races a year. A runner's own time is filled on 86-93%, the first split
on 81-94% and the starting price on 85-95% (rising year by year). Fields averaged 8.6-8.8 runners to 2018 and 7.7-8.1
since.

GRV's **startPrice is a bookmaker SP** with a median book of 1.187 (19% margin). On 103,799 races priced throughout
with one winner its winner log loss is 1.5570. Book-adjusted it is close to calibrated to $13 (A/E 1.036 at $1-$2 to
0.972 at $8-$13) and then overstates the longshots: A/E 0.908 at $13-$21, 0.697 at $21-$51, 0.489 above $51.

Our point-in-time ratings, later half (102,710 races from Nov 2019; a random runner wins 12.8%): the runner ranked
first by the mean time rating of its last 5 wins 25.4%, best of last 5 25.5%, the Elo 23.8%, the mean of last 5
finishes 21.4%, the first-split rating 19.4%; the SP favourite wins 27.5%.

## Test 9: the theories against GRV's SP and against BSP (4 Nov 2026, same run, `topaz_theories.py`)

Fit before 3 Oct 2021, rounds and blends chosen to 3 Jun 2024, scored once on 25,639 races from 3 Jun 2024 (halves
split 13 Aug 2025). BSP from Betfair's free files matched by date and dog name on 482,662 runners; 22,841 of the scored
races fully matched. On those: **BSP 1.4839, GRV SP 1.5527**.

| theory | features | trained on | log loss | gap to SP | 1st half | 2nd half | gap to BSP |
|---|---|---|---|---|---|---|---|
| T1 ratings engine + race card | 35 | SP chances | 1.6795 | +0.0843 | +0.0707 | +0.0973 | +0.1654 |
| T2 + run style and map | 54 | SP chances | 1.6758 | +0.0805 | +0.0659 | +0.0946 | +0.1618 |
| T3 + dog/trainer/sire/dam windows | 77 | SP chances | 1.6711 | +0.0759 | +0.0621 | +0.0891 | +0.1569 |
| T4 + vacant boxes | 82 | SP chances | 1.6700 | +0.0747 | +0.0610 | +0.0879 | +0.1557 |
| T5 + GRV fields that pass the leak check | 85 | SP chances | 1.6714 | +0.0762 | +0.0621 | +0.0897 | +0.1566 |
| T6 + market history | 90 | SP chances | 1.6700 | +0.0747 | +0.0605 | +0.0883 | +0.1554 |
| T7 the same, trained on BSP chances | 90 | BSP chances | 1.6640 | +0.0688 | +0.0544 | +0.0826 | +0.1497 |
| T7 the same | 90 | winners | 1.6553 | +0.0600 | +0.0402 | +0.0790 | +0.1559 |

Leak checks: GRV's `rating`, `totalFormCount` and `careerPrizeMoney` were NOT shown to be pre-race and were left out;
`last5` was (its first digit is the previous run's place 61% of the time, this run's 15%) and was used.

Benter stage 2: the best row blended with the SP (weights 0.224 / 0.904) beats the SP by 0.022 (halves 0.027 /
0.017); blended with the **BSP** (0.036 / 0.967) it adds **nothing** (-0.0000). Top inputs: Elo, trainer strike rate,
best time rating, track, mean time rating, the dog's past SPs.

**What it means.** Every theory moved the right way and in both halves, 0.016 in all from T1 to T7, but the start is
far off: +0.150 behind BSP at best, about where v0 sat on the free files (+0.160) with no times or splits at all. That
is the suspicious part, and the next round looks at why before trusting it: the fit uses only 2013-2021 (2021-2024
goes to choosing rounds), the learner is set cautiously (min 300 rows a leaf, rounds in steps of 100), and the
ratings are fed as values where a rank within the field may carry more. GRV's SP is beatable (the blend gains 0.022
on it, and it is itself 0.069 behind BSP); BSP is not, yet.

## Test 10: round 2 against BSP (4 Nov 2026, gh topaz run 41779996340, `topaz_round2.py`)

Same features (T7) and the same scored races as Test 9: 22,841 races from 3 Jun 2024 that Betfair fully priced, BSP
1.4839 (halves 1.5020 / 1.4677), GRV SP 1.5527. Test 9 fitted on 51,722 races to Oct 2021; R1 to R4 fit on 73,290
races to 2 Dec 2023, rounds chosen by early stopping on 4,870 races to 2 Jun 2024.

| row | features | learner | target | rounds | log loss | gap to BSP | 1st half | 2nd half | gap to GRV SP |
|---|---|---|---|---|---|---|---|---|---|
| R1 all history before the quarter | 90 | small | BSP chances | 3000 | 1.6208 | +0.1370 | +0.1286 | +0.1444 | +0.0682 |
| R2 + ranks and gaps in the field | 120 | small | BSP chances | 2992 | 1.6213 | +0.1375 | +0.1304 | +0.1438 | +0.0687 |
| R3 + a bigger learner | 120 | big | BSP chances | 3966 | 1.6214 | +0.1376 | +0.1299 | +0.1444 | +0.0688 |
| R4 half BSP chance, half winner | 120 | big | mixed | 924 | 1.6257 | +0.1419 | +0.1346 | +0.1484 | +0.0731 |

Blended with BSP (weights from the early-stopping months) R1 takes a weight of -0.034: it adds nothing to BSP. Top
inputs: Elo, the dog's past SPs, best and mean time ratings, trainer strike rate.

**What it means.** The longer training window was worth 0.013 (Test 9's +0.150 to +0.137), in both halves. Ranks in
the field, a bigger learner and a mixed target gave nothing: the model is at the limit of what these features hold,
and more capacity will not move it. For scale, Betfair's own published Iggy model is 0.169 behind BSP over the 2026
months it covers (Test 4b), so we are 0.03 closer than Betfair's model on the same yardstick, and three quarters of
the way from a random pick to BSP. The rest has to come from new information, not tuning: better ratings (check the
time rating against the dog's next run; track-specific seconds per length; a class and grade scale), interactions the
map should carry (run style by box by track), and Isolynx at the four tracks that have it.

## Test 11: round 3, closer to BSP, then staking and ROI (4 Nov 2026, gh topaz run 41783392368, `topaz_round3.py`)

**Part 1, the ratings check** (later half, the correlation of each pre-race rating with the dog's own time rating in
the race): recency-weighted time rating +0.413, mean of last 5 +0.408, best of last 5 +0.386, last run +0.310, Elo
+0.352, mean finish of last 5 -0.270 (lower is better, so the sign is right); first-split ratings only +0.12 to +0.15
against the run time (they measure early pace, not the whole run). Seconds per length measured from Topaz's two
margins: **0.0671 overall** (59 track-distances, 0.0609 to 0.0675), not the 0.07 assumed; re-scaling by track changed
nothing (the correlation is unchanged because the scale is near constant within a track and distance).

**Part 2** (the same 22,841 scored races Betfair fully priced, BSP 1.4839; chosen on 4,870 early-stopping races):

| row | features | rounds | early-stopping log loss | scored log loss | gap to BSP | 1st half | 2nd half |
|---|---|---|---|---|---|---|---|
| B0 round 2's R1 | 90 | 3000 | 1.6383 | 1.6208 | +0.1370 | +0.1286 | +0.1444 |
| B1 + track lengths, recent form, class, prize, interactions | 107 | 2997 | 1.6299 | 1.6122 | +0.1283 | +0.1208 | +0.1350 |
| B2 B1 with recent years weighted more | 107 | 2970 | 1.6264 | 1.6105 | **+0.1267** | +0.1195 | +0.1331 |
| B2w the same, trained on winners | 107 | 385 | 1.6411 | 1.6279 | +0.1441 | +0.1355 | +0.1517 |
| B3 ensemble of B2 and B2w (0.63 / 0.46) | | | 1.6252 | 1.6112 | +0.1273 | +0.1194 | +0.1343 |

The new information was worth 0.009 and recency 0.002, in both halves: **0.150 (Test 9) to 0.137 (Test 10) to 0.127**.
B3 was chosen on the early-stopping months (1.6252, the lowest there) and is what the staking uses.

**Part 3, staking the chosen model** on the scored races, odds to $21, flat 1 unit, both halves:

| price | edge at least | bets 1st / 2nd | winners 1st / 2nd | A/E 1st / 2nd | flat ROI 1st / 2nd |
|---|---|---|---|---|---|
| BSP, 8% commission | 5% | 22,531 / 22,710 | 3,099 / 3,097 | 1.024 / 1.000 | -4.0% / -7.3% |
| BSP, 8% commission | 10% | 20,360 / 20,584 | 2,644 / 2,718 | 1.009 / 1.010 | -5.3% / -6.7% |
| BSP, 8% commission | 20% | 16,616 / 16,883 | 2,013 / 2,060 | 1.016 / 1.008 | -4.1% / -6.7% |
| GRV SP, no commission | 5% | 22,142 / 22,396 | 3,507 / 3,387 | 1.080 / 1.029 | +5.9% / +1.2% |
| GRV SP, no commission | 10% | 19,899 / 20,205 | 3,099 / 3,013 | 1.093 / 1.046 | +7.6% / +2.7% |
| GRV SP, no commission | 20% | 16,116 / 16,441 | 2,466 / 2,356 | 1.139 / 1.071 | **+10.9% / +5.2%** |

Quarter-Kelly on the model's own chances went to zero at BSP and swung wildly at the SP (drawdowns of 89-100%): with
the model 0.127 behind BSP its chances are not calibrated enough to size bets, so the flat column is the measure.

**What it means.** At BSP the model's selections win about as often as BSP says (A/E 1.00 to 1.02) and lose the 8%
commission: BSP is not beaten. At GRV's SP, a bookmaker price 0.069 behind BSP, the same selections win 3 to 14% more
than the price says and **profit in both halves at every edge**, most at the 20% edge (+10.9% and +5.2% on about
16,000 bets a half; at an average price near $8 one half's standard error is about 2.3%, so both halves are clear of
zero, the first by about 4.7 errors and the second by about 2.3). The second half is weaker than the first at every
edge, which has to be watched. This is the founder's thesis in miniature: the model does not beat the sharpest price,
it beats a weaker one, and the TAB open is weaker again. Both prices here are set at the jump, so these are not bets
we could place; the bet we can place is at the open, which is the test the recorded opens are for.

## Test 12: staking rules chosen out of sample (4 Nov 2026, gh topaz run 41790052101, `topaz_round4.py`)

Model: round 3's B2 + B2w ensemble (scored log loss 1.6112, BSP 1.4839). The calibration power fitted on the
early-stopping months was **1.00**: the model's chances are already calibrated, so Test 11's Kelly blow-ups came from
sizing, not from miscalibration. Rules searched on the early-stopping months (Dec 2023 to Jun 2024, at least 300 bets):
one bet a race or not, six price bands, edges of 10/20/30/50%; the best there was then scored once on Jun 2024 to Nov
2026, in two halves.

**At GRV's SP** the best rule on the early-stopping months was **every runner at $8-$13 with an edge of 50% or more**
(+34.9% there on 1,127 bets; next best the same with one a race, +32.9%, then $5-$8 rules at +24-25%). Scored:

| sizing | half | bets | winners | A/E | flat ROI | bank x | worst drawdown | longest losing run |
|---|---|---|---|---|---|---|---|---|
| 1% of bank | 1st | 3,124 | 389 | 1.243 | **+24.7%** | 419.76 | 56% | 39 |
| 1% of bank | 2nd | 3,082 | 355 | 1.153 | **+14.0%** | 16.94 | 80% | 70 |
| 0.1 Kelly | 1st | 3,124 | 389 | 1.243 | +24.7% | 15876.23 | 51% | 39 |
| 0.1 Kelly | 2nd | 3,082 | 355 | 1.153 | +14.0% | 286.17 | 72% | 70 |
| 0.25 Kelly | 1st | 3,124 | 389 | 1.243 | +24.7% | 12775.72 | 81% | 39 |
| 0.25 Kelly | 2nd | 3,082 | 355 | 1.153 | +14.0% | 27.56 | 96% | 70 |

22 of 30 months in profit (flat). By month: Jun 2024 +5%, Jul +36%, Aug -8%, Sep +7%, Oct +25%, Nov +18%, Dec +28%,
Jan 2025 +19%, Feb +35%, Mar +32%, Apr +3%, May +62%, Jun +20%, Jul +34%, Aug +37%, Sep -4%, Oct -10%, Nov +39%, Dec
+34%, Jan 2026 +40%, Feb +28%, Mar +10%, Apr -15%, May +28%, Jun +51%, Jul +36%, **Aug -1%, Sep -19%, Oct -33%, Nov (16
bets) -38%**.

**At BSP** (8% commission) the same rule was best on the early-stopping months (+4.1%) and lost on the scored quarter:
-7.4% / -4.9%, A/E 0.996 / 1.020, 12 of 29 months in profit.

**What it means.**
- At GRV's SP the edge is real by every test the brief asks for: the rule was chosen on months the scoring never saw,
  it profits in both halves (+24.7% and +14.0%; at about $10 a bet one half's standard error is near 6%, so 4.2 and 2.4
  errors clear of zero), A/E 1.24 and 1.15, 22 months of 30. It sits at $8-$13, where the SP alone runs slightly
  short (Test 8: book-adjusted A/E 0.972), so this is the model picking the right $8-$13 dogs, not a price-band bias.
- At BSP it does not exist: BSP prices those dogs correctly.
- **The last three months lost** (Aug to Oct 2026). The model was trained to Dec 2023, so it is nearly three years
  stale by then; the next test retrains as it goes (walk-forward) to see whether a fresh model holds the edge.
- **Sizing**: even 1% of the bank a bet at $8-$13 drew down 56% and 80%, with losing runs of 39 and 70. A live stake
  should be well under 1% (0.25-0.5%), and the Kelly columns are not usable at this price range.
- **Placeable?** GRV's startPrice is the on-course bookmakers' SP. The TAB's own fixed price near the jump should sit
  close to it, and BetMatic can bet the TAB near the jump with a minimum price; that link has to be measured before it
  is relied on (the open-price probe records TAB's price at the moment it fires).

## Test 13: comments, trials and recent box bias (4 Nov 2026, gh topaz run 41796342169, `topaz_round5.py`)

The run pulled 13 years of VIC trials through `/api/trialresult` (79 minutes, every month, cached beside the runs).
Same scored races as Tests 9-12 (22,841, BSP 1.4839):

| row | features | rounds | early-stopping log loss | scored log loss | gap to BSP | 1st half | 2nd half |
|---|---|---|---|---|---|---|---|
| C0 round 3's B2 | 107 | 2970 | 1.6264 | 1.6105 | +0.1267 | +0.1195 | +0.1331 |
| C1 + comments | 187 | 1781 | 1.6295 | 1.6119 | +0.1280 | +0.1198 | +0.1354 |
| C2 + trials | 195 | 2907 | 1.6289 | 1.6101 | +0.1263 | +0.1183 | +0.1335 |
| C3 + recent box bias | 197 | 2826 | 1.6271 | 1.6108 | +0.1269 | +0.1192 | +0.1339 |

None helps; C0 is chosen on the early-stopping months. Two things the run found that matter more than the table:

1. **The `comment` field is not the stewards' report.** Its commonest words are TO, HERE, CAN, PLACE, EARLY, DANGER,
   DRAW, SAFE, KEEP, NEEDS, THREAT, SPEED, BEST, LUCK, PREFER, LEAD: it is GRV's form-guide preview of the race ("needs
   luck from the draw", "place danger"), written BEFORE the race. As "the last run's comment" it carries nothing, as
   the table shows. As THIS race's preview it is an expert's pre-race opinion, which is legitimate if it is written
   before the race; that needs its own test, with a check that it is not updated afterwards.
2. **The trials feed returned only 14,238 trial runs in 13 years** (a trial before the race for 12% of runners). VIC
   runs thousands of trials a year, so `/trialresult` is giving a small part of them (by access, type or paging);
   worth one question to GRV before building on it.

Staking C0 as Test 12 (rules chosen on the early-stopping months): **at GRV's SP**, one bet a race at $5-$8 with an
edge of 50% or more (552 bets there, +30.5%) scored **+21.7% and +17.7%** (1,373 and 1,490 bets, A/E 1.219 and 1.173,
worst drawdown at 0.5% a bet 16% and 37%, 19 of 30 months in profit). **At BSP** the chosen rule ($8-$13, 50%) lost
-7.0% and -2.8%. Both rules at the SP lose in the most recent months (here Jul to Oct 2026: -38%, -5%, -23%, -6%; Test
12's rule Aug to Oct). A model trained to Dec 2023 is going stale, or the SP has changed; retraining as it goes
(walk-forward) is the test that decides which.

## Test 14: walk-forward, a fresh model every month (4 Nov 2026, gh topaz run 41812672532, `topaz_walk.py`)

Founder: "Retrain every months, find a way to be profitable." Tests 11 to 13 priced every race from June 2024 with a
model frozen at December 2023 and lost in the latest months. This run refits round 3's B2 (the ratings engine, run
style and map, the dog/trainer/sire/dam windows, vacant boxes, last5, market history, class, recent form; recent years
weighted more, half-life 3 years; 3,000 rounds on BSP chances and a twin of 400 rounds on winners, the counts early
stopping chose in Tests 10 and 11) **every month from December 2023 to November 2026, on every race before that
month**, so no race is priced by a model that has seen it or anything after it. 36 refits, 73,238 to 103,730 training
races, 207 minutes. BSP matched on 482,662 runners, 65,285 races fully matched (94% of races since 2020). The preview
(Test 15) and the ratings upgrades (Test 16) were built while this ran and are NOT in it.

### Log loss by month, every race priced by a model refitted before that month

| month | races | model | ensemble | GRV SP | BSP (races matched) | model gap to SP | gap to BSP |
|---|---|---|---|---|---|---|---|
| 2023-12 | 834 | 1.6500 | 1.6414 | 1.5940 | 1.5184 (754) | +0.0561 | +0.1133 |
| 2024-01 | 835 | 1.6522 | 1.6383 | 1.6075 | 1.4931 (723) | +0.0447 | +0.1330 |
| 2024-02 | 715 | 1.6625 | 1.6649 | 1.5765 | 1.5269 (664) | +0.0859 | +0.1258 |
| 2024-03 | 810 | 1.6554 | 1.6432 | 1.6308 | 1.4925 (683) | +0.0246 | +0.1296 |
| 2024-04 | 809 | 1.6737 | 1.6616 | 1.6111 | 1.4883 (705) | +0.0626 | +0.1525 |
| 2024-05 | 882 | 1.6401 | 1.6249 | 1.6492 | 1.5002 (718) | -0.0091 | +0.0926 |
| 2024-06 | 822 | 1.6904 | 1.6634 | 1.6596 | 1.5126 (640) | +0.0308 | +0.1216 |
| 2024-07 | 881 | 1.6847 | 1.6670 | 1.6876 | 1.5288 (723) | -0.0029 | +0.1094 |
| 2024-08 | 900 | 1.6844 | 1.6544 | 1.6499 | 1.4912 (705) | +0.0345 | +0.1232 |
| 2024-09 | 817 | 1.6721 | 1.6549 | 1.6379 | 1.4997 (697) | +0.0342 | +0.1297 |
| 2024-10 | 950 | 1.6342 | 1.6190 | 1.6172 | 1.4742 (835) | +0.0170 | +0.1224 |
| 2024-11 | 876 | 1.6517 | 1.6361 | 1.6091 | 1.5103 (744) | +0.0426 | +0.1000 |
| 2024-12 | 785 | 1.6936 | 1.6713 | 1.6790 | 1.5480 (616) | +0.0145 | +0.0816 |
| 2025-01 | 928 | 1.6329 | 1.6237 | 1.6159 | 1.4845 (831) | +0.0171 | +0.1057 |
| 2025-02 | 791 | 1.6652 | 1.6581 | 1.5999 | 1.5258 (749) | +0.0653 | +0.1213 |
| 2025-03 | 907 | 1.6524 | 1.6462 | 1.5737 | 1.4971 (842) | +0.0787 | +0.1304 |
| 2025-04 | 872 | 1.6418 | 1.6351 | 1.6231 | 1.4916 (774) | +0.0187 | +0.1172 |
| 2025-05 | 942 | 1.6947 | 1.6765 | 1.6700 | 1.5526 (787) | +0.0247 | +0.0970 |
| 2025-06 | 862 | 1.6129 | 1.5891 | 1.6204 | 1.4665 (747) | -0.0075 | +0.1059 |
| 2025-07 | 922 | 1.6408 | 1.6319 | 1.6292 | 1.5074 (815) | +0.0116 | +0.0965 |
| 2025-08 | 818 | 1.5710 | 1.5506 | 1.5227 | 1.4028 (723) | +0.0483 | +0.1297 |
| 2025-09 | 834 | 1.6370 | 1.6227 | 1.5933 | 1.4865 (721) | +0.0437 | +0.1143 |
| 2025-10 | 960 | 1.6396 | 1.6243 | 1.6347 | 1.4952 (821) | +0.0049 | +0.1130 |
| 2025-11 | 753 | 1.6213 | 1.6065 | 1.5705 | 1.4634 (666) | +0.0508 | +0.1249 |
| 2025-12 | 913 | 1.6060 | 1.5829 | 1.6146 | 1.4557 (786) | -0.0086 | +0.1057 |
| 2026-01 | 913 | 1.6425 | 1.6285 | 1.6056 | 1.4824 (824) | +0.0369 | +0.1309 |
| 2026-02 | 879 | 1.6251 | 1.6224 | 1.5675 | 1.4830 (828) | +0.0576 | +0.1186 |
| 2026-03 | 990 | 1.5963 | 1.5986 | 1.5360 | 1.4493 (963) | +0.0603 | +0.1383 |
| 2026-04 | 871 | 1.5650 | 1.5653 | 1.5089 | 1.4717 (860) | +0.0561 | +0.0931 |
| 2026-05 | 908 | 1.6646 | 1.6587 | 1.6255 | 1.5155 (821) | +0.0391 | +0.1181 |
| 2026-06 | 897 | 1.6388 | 1.6308 | 1.6411 | 1.4978 (814) | -0.0023 | +0.1169 |
| 2026-07 | 957 | 1.6172 | 1.6094 | 1.5671 | 1.4622 (886) | +0.0501 | +0.1405 |
| 2026-08 | 866 | 1.5999 | 1.6006 | 1.5156 | 1.4872 (856) | +0.0843 | +0.1101 |
| 2026-09 | 901 | 1.5622 | 1.5679 | 1.4641 | 1.4283 (900) | +0.0981 | +0.1338 |
| 2026-10 | 892 | 1.5353 | 1.5333 | 1.4322 | 1.4030 (892) | +0.1031 | +0.1323 |
| 2026-11 | 69 | 1.6379 | 1.6637 | 1.5317 | none matched | +0.1062 | |

Scored quarter as a whole (25,676 races, Jun 2024 to Nov 2026): model 1.6332, ensemble 1.6216, SP 1.5952; on the
22,866 BSP-matched races: model 1.6009, BSP 1.4838, **gap +0.1171** against the frozen model's +0.1267 (Test 11).
Refitting monthly is worth 0.010 against BSP on the same features. The gap to the SP is the number to watch: it was
near zero through 2024 and 2025 (five months where the model beat the SP outright) and has **widened to +0.08 to
+0.10 from August 2026**, while the gap to BSP has not moved. The SP got sharper, not the model worse: a fresh model
does not close it, so whatever the TAB changed in August it is in the SP and not in the form.

### Bets at GRV's SP, no commission, the rule chosen each month on the six months before it

The rule each month (the signal: the model, the ensemble of the two models, or Benter's blend of the model with the
market price; one bet a race or every qualifier; a price band; an edge) is the one with the best flat ROI over the
PREVIOUS six months of walk-forward predictions with at least 300 bets there. Chosen with nothing from the month it
is then applied to:

| month | rule chosen on the 6 months before (bets, ROI there) | bets | winners | A/E | flat ROI | cumulative units |
|---|---|---|---|---|---|---|
| 2024-06 | blend, one a race, $8-$13, 10% (307, +58%) | 57 | 7 | 1.163 | +8.8% | +5 |
| 2024-07 | blend, all, $1.5-$21, 20% (678, +58%) | 131 | 31 | 1.303 | +55.3% | +78 |
| 2024-08 | blend, one a race, $1.5-$21, 30% (382, +68%) | 67 | 12 | 1.092 | -1.0% | +77 |
| 2024-09 | blend, all, $13-$21, 10% (315, +78%) | 54 | 8 | 2.301 | +117.6% | +140 |
| 2024-10 | blend, one a race, $13-$21, 10% (309, +96%) | 56 | 1 | 0.291 | -73.2% | +99 |
| 2024-11 | blend, one a race, $13-$21, 10% (365, +64%) | 72 | 4 | 0.877 | -15.7% | +88 |
| 2024-12 | blend, one a race, $13-$21, 10% (304, +52%) | 44 | 2 | 0.741 | -30.2% | +75 |
| 2025-01 | blend, one a race, $1.5-$21, 30% (556, +46%) | 138 | 39 | 1.502 | +52.5% | +147 |
| 2025-02 | blend, one a race, $1.5-$21, 30% (526, +45%) | 90 | 16 | 1.113 | +40.1% | +183 |
| 2025-03 | blend, all, $8-$13, 20% (304, +71%) | 33 | 8 | 2.412 | +153.6% | +234 |
| 2025-04 | blend, one a race, $8-$13, 10% (453, +66%) | 77 | 17 | 2.108 | +119.0% | +326 |
| 2025-05 | blend, one a race, $8-$13, 10% (447, +68%) | 75 | 21 | 2.724 | +178.5% | +459 |
| 2025-06 | blend, one a race, $8-$13, 10% (502, +82%) | 88 | 14 | 1.523 | +48.6% | +502 |
| 2025-07 | blend, one a race, $8-$13, 10% (525, +82%) | 87 | 16 | 1.824 | +91.4% | +582 |
| 2025-08 | blend, one a race, $8-$13, 10% (512, +92%) | 63 | 9 | 1.422 | +34.0% | +603 |
| 2025-09 | blend, one a race, $8-$13, 10% (487, +87%) | 75 | 8 | 1.032 | -4.5% | +600 |
| 2025-10 | blend, one a race, $8-$13, 20% (303, +99%) | 44 | 6 | 1.318 | +30.9% | +613 |
| 2025-11 | blend, all, $8-$13, 20% (321, +80%) | 55 | 12 | 2.152 | +116.0% | +677 |
| 2025-12 | blend, one a race, $1.5-$21, 30% (507, +78%) | 98 | 38 | 2.300 | +150.2% | +824 |
| 2026-01 | blend, one a race, $1.5-$21, 30% (511, +94%) | 93 | 26 | 1.633 | +61.2% | +881 |
| 2026-02 | blend, one a race, $1.5-$21, 30% (431, +89%) | 60 | 15 | 1.646 | +47.7% | +910 |
| 2026-03 | blend, one a race, $1.5-$21, 30% (399, +93%) | 86 | 19 | 1.277 | +32.0% | +937 |
| 2026-04 | blend, one a race, $1.5-$21, 30% (375, +85%) | 47 | 8 | 1.136 | +4.3% | +939 |
| 2026-05 | blend, one a race, $1.5-$21, 20% (559, +61%) | 106 | 23 | 1.338 | +47.2% | +989 |
| 2026-06 | blend, one a race, $1.5-$21, 20% (621, +52%) | 117 | 41 | 1.907 | +84.6% | +1,088 |
| 2026-07 | blend, all, $1.5-$21, 20% (654, +53%) | 108 | 23 | 1.318 | +20.8% | +1,111 |
| 2026-08 | blend, all, $1.5-$21, 20% (603, +46%) | 65 | 10 | 0.999 | -12.8% | +1,102 |
| 2026-09 | blend, all, $1.5-$21, 20% (459, +49%) | 59 | 9 | 1.098 | +41.7% | +1,127 |
| 2026-10 | blend, all, $1.5-$21, 20% (309, +42%) | 36 | 3 | 0.639 | -53.1% | +1,108 |
| 2026-11 | blend, all, $1.5-$21, 10% (686, +38%) | 6 | 1 | 1.169 | +66.7% | +1,112 |

- **Sequential rule**, 1st half: 1,091 bets, A/E 1.479, flat ROI **+53.7%**, bank x15.66 at 0.5% a bet, worst
  drawdown 36%, longest losing run 42. 2nd half: 1,096 bets, A/E 1.499, flat ROI **+48.0%**, bank x12.04, worst
  drawdown 14%, longest losing run 23. All: 2,187 bets, A/E 1.490, +50.8%, bank x188.59, drawdown 36%. Months in
  profit 23 of 30; the last six: Jun 2026 +85% (117 bets), Jul +21% (108), Aug -13% (65), Sep +42% (59), Oct -53%
  (36), Nov +67% (6).
- **Test 12's fixed rule** (all qualifiers, $8-$13, 50% edge): +29.7% and +19.0% (2,880 and 2,893 bets, A/E 1.302
  and 1.202, worst drawdown 25% and 43%, longest losing runs 43 and 45; all 5,773 bets +24.3%); 24 of 30 months in
  profit; last six +61%, +66%, -1%, +7%, -41%, +8%. The frozen model scored the same rule +24.7% and +14.0% (Test 16):
  refitting is worth five points of ROI on each half.
- **Test 13's fixed rule** (one a race, $5-$8, 50%): +20.7% and +14.3% (1,349 and 1,350 bets, A/E 1.217 and 1.144,
  drawdown 18% and 40%, losing runs 32 and 39; all 2,699 bets +17.5%); 20 of 30 months; last six +58%, -26%, -28%,
  -33%, +4%, -12%.

The chooser picked Benter's blend with the SP in all 30 months, never the model alone, and the edge it wanted
drifted from 10% to 30% and back to 20%. Two cautions before anyone reads +50% as the business. **The blend takes
the SP as an input, so these are bets struck at the SP** (the price at the jump), not at the TAB open we plan to bet
into; whether the open is better or worse than the SP for these dogs is exactly what the open recording (BetMatic
probe, waiting on $1 in the account) will say. And the latest months are thin and mixed: 36 bets in October at
-53%, and the SP itself has sharpened since August (the table above), so the edge against it is being measured on a
market that is changing under us.

### Bets at BSP, 8% commission on winnings, the rule chosen the same way

| month | rule chosen on the 6 months before (bets, ROI there) | bets | winners | A/E | flat ROI | cumulative units |
|---|---|---|---|---|---|---|
| 2024-06 | blend, one a race, $8-$13, 30% (624, +20%) | 79 | 11 | 1.451 | +28.9% | +23 |
| 2024-07 | blend, one a race, $8-$13, 30% (594, +16%) | 98 | 8 | 0.858 | -15.3% | +8 |
| 2024-08 | blend, all, $1.5-$21, 50% (642, +21%) | 109 | 7 | 0.799 | -15.1% | -9 |
| 2024-09 | blend, all, $13-$21, 50% (413, +20%) | 66 | 7 | 1.733 | +66.4% | +35 |
| 2024-10 | blend, all, $13-$21, 50% (418, +27%) | 71 | 4 | 0.934 | -12.8% | +26 |
| 2024-11 | blend, one a race, $13-$21, 50% (393, +42%) | 75 | 3 | 0.657 | -38.3% | -3 |
| 2024-12 | blend, one a race, $13-$21, 50% (400, +14%) | 49 | 2 | 0.692 | -38.6% | -21 |
| 2025-01 | blend, one a race, $1.5-$21, 50% (569, +9%) | 105 | 7 | 0.874 | -27.0% | -50 |
| 2025-02 | model, one a race, $3-$5, 30% (327, +9%) | 78 | 15 | 0.788 | -25.2% | -69 |
| 2025-03 | blend, all, $5-$8, 20% (500, +7%) | 90 | 13 | 0.917 | -12.4% | -81 |
| 2025-04 | blend, one a race, $8-$13, 10% (1,509, +6%) | 261 | 19 | 0.739 | -32.7% | -166 |
| 2025-05 | blend, one a race, $8-$13, 10% (1,479, +1%) | 236 | 30 | 1.291 | +23.7% | -110 |
| 2025-06 | blend, one a race, $8-$13, 10% (1,448, +3%) | 244 | 18 | 0.752 | -30.5% | -185 |
| 2025-07 | ensemble, one a race, $1.5-$3, 2% (461, +4%) | 61 | 26 | 1.030 | -1.5% | -185 |
| 2025-08 | blend, all, $1.5-$21, 50% (719, +11%) | 91 | 8 | 1.151 | +13.0% | -174 |
| 2025-09 | blend, one a race, $1.5-$21, 50% (652, +19%) | 90 | 0 | 0.000 | -100.0% | -264 |
| 2025-10 | ensemble, one a race, $1.5-$3, 10% (319, +6%) | 60 | 25 | 0.975 | -2.8% | -265 |
| 2025-11 | ensemble, one a race, $1.5-$3, 10% (324, +7%) | 45 | 19 | 1.016 | -4.3% | -267 |
| 2025-12 | blend, one a race, $13-$21, 50% (396, +5%) | 60 | 4 | 1.116 | +0.3% | -267 |
| 2026-01 | blend, one a race, $8-$13, 20% (949, +7%) | 160 | 18 | 1.157 | +8.1% | -254 |
| 2026-02 | ensemble, one a race, $8-$13, 5% (2,047, +4%) | 333 | 39 | 1.196 | +10.6% | -219 |
| 2026-03 | ensemble, one a race, $8-$13, 2% (2,148, +3%) | 399 | 39 | 1.002 | -5.6% | -241 |
| 2026-04 | ensemble, one a race, $8-$13, 2% (2,194, +2%) | 358 | 40 | 1.138 | +8.3% | -211 |
| 2026-05 | blend, all, $3-$5, 10% (585, +3%) | 88 | 20 | 0.897 | -16.5% | -226 |
| 2026-06 | blend, one a race, $8-$13, 2% (2,021, +5%) | 349 | 37 | 1.079 | -0.9% | -229 |
| 2026-07 | ensemble, one a race, $8-$13, 20% (1,840, +8%) | 353 | 34 | 0.982 | -11.3% | -269 |
| 2026-08 | model, one a race, $1.5-$3, 5% (344, +7%) | 66 | 27 | 0.987 | -5.1% | -272 |
| 2026-09 | model, one a race, $3-$5, 30% (430, +13%) | 72 | 20 | 1.117 | +12.8% | -263 |
| 2026-10 | model, one a race, $3-$5, 30% (408, +18%) | 72 | 18 | 1.032 | +3.1% | -261 |

- Sequential rule: 1st half 2,102 bets, A/E 0.948, **-11.6%**, worst drawdown 84%, longest losing run 99; 2nd half
  2,116 bets, A/E 1.049, **-0.7%**, drawdown 50%, losing run 62; all 4,218 bets, A/E 0.999, -6.2%; 10 of 29 months
  in profit; last six -16%, -1%, -11%, -5%, +13%, +3%.
- Test 12's rule: -1.6% and -6.9% (2,694 and 2,701 bets, A/E 1.048 and 1.000; all 5,395 bets -4.2%); 13 of 29 months.
- Test 13's rule: -7.9% and -20.4% (1,195 and 1,195 bets, A/E 0.992 and 0.846; all 2,390 bets -14.1%); 8 of 29 months.

**Nothing works at BSP**, with the model fresh every month and the rule chosen every month: the best rule on any six
months rarely cleared +10% there and never held. The whole edge of the SP rules is the SP's own 19% book and its
longshot overpricing (Test 8); against the sharpest price the model's A/E is 1.00, which is exactly what a +0.117 gap
says. What the walk-forward settles: **a fresh model holds the edge at the SP** (the frozen one was fading, Tests 12
and 13), and it is the SP that moved in August, not the model. The next walk-forward carries the preview, the
ratings upgrades and, when they exist, Isolynx and GRV's rating (Tests 15 and 16 took the frozen gap from 0.127 to
0.1085), and the open prices decide whether a bet at the open keeps what a bet at the SP shows here.

## Test 15: GRV's pre-race preview of THIS race (4 Nov 2026, runs 41813400075 and 41813404980)

The per-runner `comment` is GRV's form-guide preview (Test 13), filled on 100% of runners; `isBestBet` is true on
2.8%. Added to round 3's B2 as this race's features (the 60 commonest comment words, the comment's length, isBestBet):

| row | features | rounds | early-stopping log loss | scored log loss | gap to BSP | 1st half | 2nd half |
|---|---|---|---|---|---|---|---|
| P0 round 3's B2 | 107 | 2900 | 1.6269 | 1.6105 | +0.1266 | +0.1195 | +0.1329 |
| P1 + this race's preview | 169 | 2768 | 1.6067 | 1.6011 | **+0.1172** | +0.1106 | +0.1231 |

The preview is worth **0.009 against BSP**, in both halves and on the early-stopping months (0.020 there): the
largest single gain since the training window (Test 10). It takes 16.5% of the model's splits (isBestBet 7.1%, then
PLACE, DANGER, CLOSE, HARD, TESTED, LOOKS, PREFER, NEEDS). Against BSP alone it adds nothing (BSP-matched races,
trained on winners: BSP alone 1.4883, BSP plus the preview 1.4907): the market already holds what the analyst knows,
which is what a legitimate pre-race opinion looks like and not what a field written after the race would.

**The leak check** (greyhound/preview.py): at 21:19 Sydney on 4 Nov, 8 VIC races were still to run; their 56 runners
were snapshotted from `/race/upcoming` and `/race/{id}/runs/form` BEFORE they ran: comment filled on 56 of 56, rating
on 56, isBestBet true on 1, startPrice on 56 of 56 (a price exists before the race), race analystComment and tips on
8 of 8, results entered on none. The compare against the bulk feed runs the morning after (mode=preview-compare,
from=2026-11-04), and a fuller snapshot of a whole day's racing is scheduled for 10am on 5 Nov. If the comments come
back unchanged, the preview goes into the walk-forward model; the gain to BSP would then be 0.127 to 0.117.

**The timing check that matters** (founder, 4 Nov: "we want to bet before the preview and odds come out"): at 21:45
Sydney on 4 Nov, `/race/upcoming` for **5 Nov** already returned all 50 of the next day's VIC races and their 382
runners with the comment, rating and isBestBet filled on every one (isBestBet true on 13), the race analystComment
and tips on 50 of 50, and a `startPrice` on all 382 (run 41816219297). The preview is published the evening before,
about ten hours before the TAB opened the Geelong market (07:22 on race morning, 27 Oct), so it is available for an
open-price bet. The `startPrice` existing the night before is itself a finding: tomorrow's compare says whether the
bulk feed's `startPrice`, which Tests 12 and 13 bet against as the SP, is this early price or a price at the jump.

## Test 16: the ratings engine upgrades, and GRV's rating (4 Nov 2026, gh topaz run 41820195552, `topaz_round6.py`)

Three upgrades to `greyhound/ratings.py`, each as at the end of the previous day and hand-tested: **shrinkage** (a
dog's mean time rating over its last 5 runs pulled toward its grade's prior by 3 pseudo-runs, so a two-run dog is
rated mostly by its grade), **context ability** (its mean rating in this race's distance band, sprint / middle /
staying, and at this track, with the run counts), and an **Elo over margins** (a nose defeat costs almost nothing, a
ten-length one the lot). Added to round 3's B2 plus the preview (Test 15), on the same 22,841 scored races:

| row | features | rounds | early-stopping log loss | scored log loss | gap to BSP | 1st half | 2nd half |
|---|---|---|---|---|---|---|---|
| D0 B2 + preview, old ratings | 169 | 2901 | 1.6066 | 1.6012 | +0.1174 | +0.1108 | +0.1232 |
| D1 + ratings upgrades | 181 | 2997 | 1.6017 | 1.5923 | **+0.1085** | +0.1003 | +0.1158 |
| D3 + GRV's rating (valid only if the compare clears it) | 183 | 2997 | 1.6000 | 1.5834 | +0.0996 | +0.0912 | +0.1071 |

The upgrades are worth **0.009** against BSP, in both halves and on the early-stopping months, and take 30% of the
model's splits: ability in the distance band 14%, the margin Elo 9%, shrinkage 2.6%, ability at the track 2.4%.
GRV's own rating is worth another 0.009 on top, IF the 5 Nov compare shows the number unchanged after the race (it
failed Test 9's leak check, which may have been reading its revision history; the snapshot shows a rating on every
runner the evening before). The gap to BSP has gone 0.150 (Test 9) → 0.137 → 0.127 → 0.117 → **0.1085**, and would be
0.0996 with GRV's rating.

Staking D1 as Test 12 (rules chosen on the early-stopping months, scored once): **at GRV's SP**, one bet a race at
$8-$13 with an edge of 50% or more (748 bets there, +31.6%) scored **+34.9% and +23.7%** (2,056 and 2,215 bets, A/E
1.360 and 1.247, longest losing runs 34 and 58), against +24.7% / +14.0% for the Test 12 model. **At BSP** the chosen
rule ($5-$8, 50%) lost -11.2% / -17.9%. Not run with Isolynx yet (the pull was in progress); D2 waits for it.

**Isolynx, later the same day: the key is not allowed it.** The pull (run 41820190239) answered HTTP 401 on every one
of 14,129 dogs, and a one-race probe (run 41854102271, `greyhound.isolynx probe`) found all three shapes the API
offers refused with the same key: per race `/isolynx/{raceId}/splits` and `/positions` (the Topaz-api wrapper's
documented endpoints) and per dog `/isolynx/dog/{dogId}/splits`, while the bulk runs, the race records and the
pre-race form all answer. Isolynx tracking needs access GRV has not granted the VIC key; the question to Jason is
drafted in the founder's Gmail. D2 is off the table until it is. The pull itself now stops on the first 401 instead
of spending three hours collecting them (`TopazForbidden`).

## Test 17: the finishing order as the label (4 Nov 2026, gh topaz run 41843056879, `topaz_round7.py`)

The model learns from one dog a race: the market's chance of each dog (BSP chances, every row since Test 10) or the
winner. A race's finishing order holds more, in principle: second beat the six behind it. The exploded-logit
(Plackett-Luce) likelihood reads an n-dog race as successive choices, each a softmax over the dogs still standing;
truncated at K stages with stage weights, and a dog with no finish standing in every denominator and never chosen.
Gradient and hessian are checked against finite differences in `tests/test_pl_objective.py`. Round 6's D1 inputs
(B2 + preview + ratings upgrades), fitted on 73,290 races (fields 4 to 10, mean 7.1; a finish recorded on 98.2% of
runners), each row early stopped on the win log loss of the six months before the scored quarter, same 22,841 races:

| row | rounds | early-stopping log loss | scored log loss | gap to BSP | 1st half | 2nd half |
|---|---|---|---|---|---|---|
| E0 D1 on BSP chances | 2961 | 1.6044 | 1.5926 | **+0.1087** | +0.1007 | +0.1159 |
| E1 Plackett-Luce depth 1 (the winner) | 417 | 1.6200 | 1.6096 | +0.1257 | +0.1175 | +0.1330 |
| E2 depth 3, equal weights | 648 | 1.6345 | 1.6269 | +0.1430 | +0.1329 | +0.1521 |
| E3 depth 3, weights 1, 0.5, 0.25 | 461 | 1.6195 | 1.6135 | +0.1296 | +0.1200 | +0.1382 |
| E4 the whole order | 2979 | 1.6560 | 1.6448 | +0.1609 | +0.1505 | +0.1702 |

| blend with E0 (weights fitted on the early-stopping months) | weights | early-stopping log loss | scored log loss | gap to BSP | 1st half | 2nd half |
|---|---|---|---|---|---|---|
| E0 + E1 | 0.63, 0.43 | 1.6037 | 1.5931 | +0.1092 | +0.1010 | +0.1165 |
| E0 + E2 | 0.66, 0.51 | 1.6029 | 1.5929 | +0.1090 | +0.1001 | +0.1170 |
| E0 + E3 | 0.57, 0.56 | 1.6024 | 1.5937 | +0.1099 | +0.1012 | +0.1176 |
| E0 + E4 | 0.81, 0.33 | 1.6029 | 1.5915 | +0.1076 | +0.0987 | +0.1156 |

**The finishing order does not help, and the deeper it is read the worse it gets.** Second to fourth as labels
(E2) are 0.034 worse than the market's chances; the whole order (E4) 0.052 worse; even the winner alone (E1) is
0.017 behind BSP chances, which is the whole gain of the soft label measured on its own. Blending a finishing-order
model into E0 moves the gap by a thousandth either way (E0 + E4 at +0.1076 is within noise, and its early-stopping
score did not pick it: the months chose E0 + E3, which scores 0.001 WORSE than E0 alone). The reading is the same
as Test 10's: the learner is not where the gap is. Lower placings in a greyhound race are mostly interference and
luck from the draw, and a label that says "fifth beat sixth" teaches the model that noise. BSP chances stay the
label; the ensemble's winners twin stays as it is. Row C of MODELS_RESEARCH.md ("use the whole finishing order")
is answered: margins are already in the Elo, and the order beyond the winner is not information at this level.

Staking the chosen blend (E0 + E3) as Test 12 (rules chosen on the early-stopping months, scored once): **at GRV's
SP**, every qualifier at $8-$13 with an edge of 50% or more (820 bets there, +46.1%) scored **+40.0% and +21.2%**
(2,234 and 2,355 bets, A/E 1.406 and 1.227, longest losing runs 43 and 56); **at BSP** the chosen rule ($5-$8, 50%)
lost -11.3% / -18.5%. Same picture as Tests 12 to 16: the SP pays, BSP does not.

## Test 19: GRV's tips for this race, and the round cap (4 Nov 2026, gh topaz run 41854109531, `topaz_round8.py`)

GRV's analyst tips (tip1 to tip4) and the race's analyst comment live in the race record, not the bulk runs; the
Topaz-api wrapper's `get_races` is `GET /api/race?from&to&owningauthoritycode`, which lists race records for a date
range, and a month answers in one call: **199,205 VIC race records, 2013 to November 2026, pulled in five minutes**
(`mode=run races=yes`, cached beside the runs). Every scored runner has a tips record; 54% of runners are tipped
(up to four a race). Matched to runners by box number (what the compare of 5 Nov confirms; the loader also accepts
a dog id or a name). The leak check first, because a tip written after the race would show up here:

| year | races | with a tips record | runners tipped | tip 1 won | SP favourite won |
|---|---|---|---|---|---|
| 2013 | 3,507 | 100% | 51% | 34.2% (3,355) | 39.8% |
| 2014 | 3,320 | 100% | 50% | 34.7% (3,200) | 40.8% |
| 2015 | 5,733 | 100% | 49% | 33.6% (5,512) | 37.1% |
| 2016 | 4,136 | 100% | 50% | 33.4% (3,963) | 37.4% |
| 2017 | 4,536 | 100% | 52% | 35.8% (4,314) | 41.0% |
| 2018 | 5,212 | 100% | 52% | 36.2% (4,992) | 41.8% |
| 2019 | 8,250 | 100% | 55% | 37.1% (7,888) | 42.7% |
| 2020 | 8,866 | 100% | 54% | 35.8% (8,444) | 41.9% |
| 2021 | 10,742 | 100% | 56% | 36.6% (10,377) | 42.2% |
| 2022 | 10,292 | 100% | 56% | 35.8% (9,991) | 41.8% |
| 2023 | 9,478 | 100% | 56% | 34.7% (9,414) | 39.9% |
| 2024 | 10,082 | 100% | 52% | 32.7% (10,001) | 38.0% |
| 2025 | 10,502 | 100% | 54% | 33.7% (10,423) | 38.7% |
| 2026 | 9,143 | 100% | 56% | 33.2% (9,076) | 40.4% |

The first tip wins 33% to 37% of its races in every year, four to six points BELOW the SP favourite, with no year
out of line: an honest pre-race opinion, weaker than the market, which is what a legitimate tip looks like. Then
the model (round 6's D1 inputs, same fit and scoring as Tests 15 and 16, same 22,841 races):

| row | features | rounds | early-stopping log loss | scored log loss | gap to BSP | 1st half | 2nd half |
|---|---|---|---|---|---|---|---|
| F0 D1 (B2 + preview + ratings upgrades) | 181 | 2883 | 1.6027 | 1.5911 | +0.1072 | +0.0989 | +0.1147 |
| F1 + GRV's tips for this race | 186 | 2971 | 1.5991 | 1.5900 | +0.1062 | +0.0988 | +0.1128 |
| F2 F1, round cap 6,000 | 186 | 4139 | 1.5985 | 1.5892 | **+0.1053** | +0.0981 | +0.1117 |

**The tips are worth 0.001, and the cap another 0.001**, each within the run-to-run noise of this split (D1 has
scored +0.1085, +0.1087 and +0.1072 on three fits today). The model takes to the tips hard, 45% of its splits
(tip_rank 25%, tip_top 20%), and gains almost nothing from them, which says the analyst's view was already in the
model through the preview's isBestBet and comment words (Test 15); the tips are the same opinion in another
column. The cap was binding in Test 16 (2,997 of 3,000) and is not at 6,000 (4,139 chosen), so the walk-forward
keeps its 3,000 for time and the standard split may use 6,000. Item 5 of MODELS_RESEARCH.md ("expert prices as
inputs ... small on top of the preview, since they overlap it") is confirmed, small. Both go into the final
walk-forward (`RACES_DIR` and the cap are switches on `topaz_walk.py`) because they are legitimate the evening
before and cost nothing; the 5 Nov compare says whether the tips are unchanged after the race.

Staking F2 as Test 12 (rules chosen on the early-stopping months, scored once): **at GRV's SP**, one bet a race at
$8-$13 with an edge of 50% or more (705 bets there, +36.8%) scored **+36.1% and +21.4%** (1,941 and 2,096 bets, A/E
1.376 and 1.229, longest losing runs 42 and 39). **At BSP** the chosen rule ($5-$8, 50%, every qualifier) lost
-7.6% / -18.4%.

## Test 18: the walk-forward with the preview and the ratings upgrades (4 Nov 2026, gh topaz run 41842337691, `topaz_walk.py`)

Test 14's walk-forward on round 3's B2, now with this race's GRV preview (Test 15) and the ratings upgrades (Test 16):
149 inputs plus 29 within-race relatives. The 181-input model does not fit 36 monthly refits inside the job, so it
refits **every second month** (`WALK_REFIT_EVERY=2`), 18 refits from December 2023, 73,238 to 102,838 training races,
about 8.5 minutes each, 155 minutes; a month between refits is priced by the previous refit, which still saw nothing
at or after its own month. Everything else as Test 14: 3,000 rounds on BSP chances and 400 on winners, recent years
weighted more, the rule each month chosen on the six months before it with at least 300 bets there.

### Log loss by month

| month | races | model | ensemble | GRV SP | BSP (races matched) | model gap to SP | gap to BSP |
|---|---|---|---|---|---|---|---|
| 2023-12 | 834 | 1.6300 | 1.6234 | 1.5940 | 1.5184 (754) | +0.0361 | +0.0903 |
| 2024-01 | 835 | 1.6246 | 1.6111 | 1.6075 | 1.4931 (723) | +0.0171 | +0.1091 |
| 2024-02 | 715 | 1.6432 | 1.6431 | 1.5765 | 1.5269 (664) | +0.0666 | +0.1088 |
| 2024-03 | 810 | 1.6304 | 1.6152 | 1.6308 | 1.4925 (683) | -0.0004 | +0.1027 |
| 2024-04 | 809 | 1.6289 | 1.6145 | 1.6111 | 1.4883 (705) | +0.0178 | +0.1051 |
| 2024-05 | 882 | 1.6264 | 1.6144 | 1.6492 | 1.5002 (718) | -0.0229 | +0.0765 |
| 2024-06 | 822 | 1.6760 | 1.6491 | 1.6596 | 1.5126 (640) | +0.0164 | +0.1009 |
| 2024-07 | 881 | 1.6672 | 1.6503 | 1.6876 | 1.5288 (723) | -0.0204 | +0.0922 |
| 2024-08 | 900 | 1.6619 | 1.6361 | 1.6499 | 1.4912 (705) | +0.0120 | +0.1044 |
| 2024-09 | 817 | 1.6524 | 1.6319 | 1.6379 | 1.4997 (697) | +0.0145 | +0.1177 |
| 2024-10 | 950 | 1.6152 | 1.6031 | 1.6172 | 1.4742 (835) | -0.0020 | +0.0984 |
| 2024-11 | 876 | 1.6217 | 1.6034 | 1.6091 | 1.5103 (744) | +0.0127 | +0.0742 |
| 2024-12 | 785 | 1.6758 | 1.6536 | 1.6790 | 1.5480 (616) | -0.0032 | +0.0700 |
| 2025-01 | 928 | 1.6233 | 1.6096 | 1.6159 | 1.4845 (831) | +0.0074 | +0.0996 |
| 2025-02 | 791 | 1.6255 | 1.6192 | 1.5999 | 1.5258 (749) | +0.0255 | +0.0851 |
| 2025-03 | 907 | 1.6355 | 1.6336 | 1.5737 | 1.4971 (842) | +0.0619 | +0.1134 |
| 2025-04 | 872 | 1.6239 | 1.6186 | 1.6231 | 1.4916 (774) | +0.0008 | +0.0995 |
| 2025-05 | 942 | 1.6645 | 1.6506 | 1.6700 | 1.5526 (787) | -0.0054 | +0.0645 |
| 2025-06 | 862 | 1.5971 | 1.5732 | 1.6204 | 1.4665 (747) | -0.0233 | +0.0869 |
| 2025-07 | 922 | 1.6254 | 1.6187 | 1.6292 | 1.5074 (815) | -0.0038 | +0.0818 |
| 2025-08 | 818 | 1.5389 | 1.5235 | 1.5227 | 1.4028 (723) | +0.0162 | +0.0973 |
| 2025-09 | 834 | 1.6078 | 1.5973 | 1.5933 | 1.4865 (721) | +0.0145 | +0.0824 |
| 2025-10 | 960 | 1.6286 | 1.6131 | 1.6347 | 1.4952 (821) | -0.0062 | +0.1006 |
| 2025-11 | 753 | 1.6015 | 1.5859 | 1.5705 | 1.4634 (666) | +0.0310 | +0.1060 |
| 2025-12 | 913 | 1.5881 | 1.5644 | 1.6146 | 1.4557 (786) | -0.0265 | +0.0895 |
| 2026-01 | 913 | 1.6305 | 1.6175 | 1.6056 | 1.4824 (824) | +0.0250 | +0.1190 |
| 2026-02 | 879 | 1.6148 | 1.6112 | 1.5675 | 1.4830 (828) | +0.0473 | +0.1078 |
| 2026-03 | 990 | 1.5813 | 1.5875 | 1.5360 | 1.4493 (963) | +0.0453 | +0.1219 |
| 2026-04 | 871 | 1.5526 | 1.5545 | 1.5089 | 1.4717 (860) | +0.0437 | +0.0813 |
| 2026-05 | 908 | 1.6421 | 1.6360 | 1.6255 | 1.5155 (821) | +0.0166 | +0.0954 |
| 2026-06 | 897 | 1.6263 | 1.6182 | 1.6411 | 1.4978 (814) | -0.0148 | +0.1028 |
| 2026-07 | 957 | 1.6051 | 1.6000 | 1.5671 | 1.4622 (886) | +0.0380 | +0.1284 |
| 2026-08 | 866 | 1.5784 | 1.5793 | 1.5156 | 1.4872 (856) | +0.0627 | +0.0880 |
| 2026-09 | 901 | 1.5394 | 1.5452 | 1.4641 | 1.4283 (900) | +0.0753 | +0.1106 |
| 2026-10 | 892 | 1.5252 | 1.5289 | 1.4322 | 1.4030 (892) | +0.0931 | +0.1222 |
| 2026-11 | 69 | 1.6248 | 1.6439 | 1.5317 | none matched | +0.0931 | |

Scored quarter as a whole (25,676 races): model 1.6145, ensemble 1.6040, SP 1.5952; on the 22,866 BSP-matched races
model 1.5824, BSP 1.4838, **gap +0.0987**, against Test 14's +0.1171 on B2 and the frozen +0.1267. The preview and
the ratings upgrades are worth 0.018 walk-forward, the same as their two 0.009s on the standard split, so those
gains are real and not an artefact of one split. **The model beat the SP outright in eleven of the 36 months**
(every negative gap above) and sits 0.019 behind it over the whole quarter; the August 2026 sharpening of the SP is
still there (+0.06 to +0.09 in the last three months) and the gap to BSP in those months is where it always was.

### Bets at GRV's SP, no commission, the rule chosen each month on the six months before it

| month | rule chosen on the 6 months before (bets, ROI there) | bets | winners | A/E | flat ROI | cumulative units |
|---|---|---|---|---|---|---|
| 2024-06 | blend, one a race, $8-$13, 10% (319, +67%) | 60 | 7 | 1.135 | +7.3% | +4 |
| 2024-07 | blend, one a race, $8-$13, 10% (365, +66%) | 65 | 12 | 1.771 | +84.9% | +60 |
| 2024-08 | blend, all, $8-$13, 10% (476, +50%) | 81 | 8 | 0.964 | -2.7% | +57 |
| 2024-09 | blend, one a race, $13-$21, 5% (412, +74%) | 68 | 6 | 1.377 | +28.1% | +76 |
| 2024-10 | blend, one a race, $13-$21, 5% (417, +71%) | 82 | 2 | 0.387 | -60.7% | +27 |
| 2024-11 | blend, all, $8-$13, 20% (329, +62%) | 54 | 6 | 1.096 | +22.2% | +39 |
| 2024-12 | ensemble, all, $5-$8, 50% (567, +45%) | 77 | 18 | 1.464 | +45.1% | +73 |
| 2025-01 | blend, all, $1.5-$21, 30% (638, +50%) | 142 | 40 | 1.523 | +45.4% | +138 |
| 2025-02 | ensemble, one a race, $5-$8, 50% (544, +48%) | 84 | 19 | 1.439 | +45.0% | +176 |
| 2025-03 | ensemble, all, $5-$8, 50% (535, +48%) | 98 | 13 | 0.852 | -14.2% | +162 |
| 2025-04 | blend, one a race, $8-$13, 10% (439, +63%) | 81 | 13 | 1.562 | +57.0% | +208 |
| 2025-05 | blend, one a race, $8-$13, 10% (440, +54%) | 77 | 19 | 2.418 | +147.4% | +321 |
| 2025-06 | blend, one a race, $8-$13, 10% (526, +76%) | 81 | 12 | 1.397 | +37.9% | +352 |
| 2025-07 | blend, one a race, $8-$13, 10% (541, +72%) | 84 | 14 | 1.648 | +61.0% | +403 |
| 2025-08 | blend, all, $8-$13, 20% (309, +100%) | 38 | 9 | 2.324 | +134.2% | +454 |
| 2025-09 | blend, all, $8-$13, 10% (546, +86%) | 84 | 10 | 1.153 | +11.0% | +464 |
| 2025-10 | blend, all, $8-$13, 20% (355, +101%) | 62 | 10 | 1.572 | +54.4% | +497 |
| 2025-11 | blend, all, $8-$13, 20% (354, +97%) | 55 | 13 | 2.331 | +127.5% | +567 |
| 2025-12 | blend, one a race, $1.5-$21, 30% (535, +84%) | 104 | 41 | 2.119 | +115.9% | +688 |
| 2026-01 | blend, one a race, $1.5-$21, 30% (566, +83%) | 104 | 21 | 1.191 | +19.6% | +708 |
| 2026-02 | blend, one a race, $1.5-$21, 30% (466, +74%) | 67 | 15 | 1.462 | +26.7% | +726 |
| 2026-03 | blend, one a race, $1.5-$21, 30% (355, +70%) | 93 | 19 | 1.171 | +14.1% | +739 |
| 2026-04 | blend, one a race, $1.5-$21, 30% (306, +63%) | 35 | 5 | 1.047 | +40.9% | +753 |
| 2026-05 | blend, all, $5-$8, 10% (310, +51%) | 60 | 10 | 1.043 | -0.3% | +753 |
| 2026-06 | blend, one a race, $1.5-$21, 20% (560, +50%) | 111 | 36 | 1.759 | +99.2% | +863 |
| 2026-07 | blend, one a race, $1.5-$21, 20% (508, +46%) | 78 | 18 | 1.294 | +26.4% | +884 |
| 2026-08 | blend, one a race, $8-$13, 2% (624, +46%) | 94 | 10 | 1.042 | +7.1% | +891 |
| 2026-09 | blend, one a race, $1.5-$21, 20% (400, +42%) | 56 | 7 | 0.830 | +1.8% | +892 |
| 2026-10 | blend, one a race, $1.5-$21, 10% (933, +34%) | 123 | 22 | 1.096 | +15.0% | +910 |
| 2026-11 | blend, one a race, $8-$13, 2% (364, +34%) | 4 | 1 | 2.380 | +150.0% | +916 |

- **Sequential rule**, 1st half: 1,150 bets, A/E 1.383, flat ROI **+35.7%**, bank x6.69 at 0.5% a bet, worst
  drawdown 32%, longest losing run 57. 2nd half: 1,152 bets, A/E 1.411, **+43.9%**, bank x10.80, worst drawdown
  14%, longest losing run 29. All: 2,302 bets, A/E 1.398, +39.8%, bank x72.24. **Months in profit 26 of 30**, and
  the last six all positive: Jun 2026 +99% (111 bets), Jul +26% (78), Aug +7% (94), Sep +2% (56), Oct +15% (123),
  Nov +150% (4). Test 14's B2 model had 23 of 30, and lost 53% in October.
- **Test 12's fixed rule** (all qualifiers, $8-$13, 50%): **+40.8% and +23.6%** (2,132 and 2,137 bets, A/E 1.425 and
  1.257, worst drawdown 26% and 34%, longest losing runs 38 and 47; all 4,269 bets +32.2%); 25 of 30 months; last
  six +60%, +54%, -14%, +12%, -29%, -29% (14 bets). Test 14's B2 walk scored the same rule +29.7% / +19.0%.
- **Test 13's fixed rule** (one a race, $5-$8, 50%): +29.3% and +19.5% (1,052 and 1,053 bets, A/E 1.292 and 1.205,
  drawdown 17% and 30%, losing runs 24 and 26; all 2,105 bets +24.4%); 24 of 30 months; last six +57%, -26%, -2%,
  -18%, -12%, -100% (6 bets). Test 14: +20.7% / +14.3%.

The better model bets less and more evenly: the sequential rule's halves are closer together than Test 14's (+35.7
and +43.9 against +53.7 and +48.0) on about the same number of bets, its worst drawdowns are smaller, and both fixed
rules gained about ten points of ROI in each half. The chooser took the blend with the SP in 27 of 30 months and
the ensemble in three (the first time a non-blend signal has been picked at the SP). The two cautions of Test 14
stand unchanged: the blend bets at the SP, not at the open, and the SP has sharpened since August.

### Bets at BSP, 8% commission on winnings

| month | rule chosen on the 6 months before (bets, ROI there) | bets | winners | A/E | flat ROI | cumulative units |
|---|---|---|---|---|---|---|
| 2024-06 | ensemble, one a race, $5-$8, 50% (420, +14%) | 62 | 6 | 0.621 | -42.5% | -26 |
| 2024-07 | blend, one a race, $13-$21, 30% (700, +8%) | 125 | 8 | 1.052 | -4.2% | -32 |
| 2024-08 | blend, all, $13-$21, 30% (773, +6%) | 109 | 7 | 1.047 | -3.3% | -35 |
| 2024-09 | blend, all, $13-$21, 30% (750, +13%) | 118 | 8 | 1.114 | +10.1% | -23 |
| 2024-10 | blend, one a race, $13-$21, 30% (693, +16%) | 131 | 10 | 1.259 | +15.5% | -3 |
| 2024-11 | blend, one a race, $1.5-$21, 50% (388, +27%) | 92 | 9 | 1.241 | +29.9% | +25 |
| 2024-12 | blend, all, $1.5-$21, 50% (431, +22%) | 62 | 3 | 0.662 | -43.3% | -2 |
| 2025-01 | blend, one a race, $1.5-$21, 50% (410, +8%) | 71 | 3 | 0.566 | -42.7% | -33 |
| 2025-02 | model, one a race, $3-$5, 30% (338, +9%) | 73 | 15 | 0.830 | -22.5% | -49 |
| 2025-03 | ensemble, one a race, $3-$5, 30% (471, +7%) | 91 | 22 | 0.955 | -10.2% | -58 |
| 2025-04 | blend, one a race, $1.5-$21, 50% (431, +5%) | 71 | 4 | 0.703 | -47.6% | -92 |
| 2025-05 | blend, all, $8-$13, 30% (507, +3%) | 75 | 13 | 1.813 | +72.6% | -38 |
| 2025-06 | blend, all, $8-$13, 30% (479, +7%) | 84 | 3 | 0.372 | -66.3% | -93 |
| 2025-07 | ensemble, one a race, $8-$13, 2% (2,231, +0%) | 400 | 41 | 1.057 | -1.6% | -99 |
| 2025-08 | blend, one a race, $1.5-$21, 50% (434, +18%) | 55 | 4 | 0.975 | +11.0% | -93 |
| 2025-09 | blend, one a race, $1.5-$21, 50% (434, +19%) | 60 | 3 | 0.632 | -35.0% | -114 |
| 2025-10 | ensemble, one a race, $3-$5, 30% (466, +6%) | 88 | 18 | 0.829 | -20.2% | -132 |
| 2025-11 | blend, all, $1.5-$21, 50% (426, +16%) | 59 | 6 | 1.397 | +33.7% | -112 |
| 2025-12 | blend, all, $1.5-$21, 50% (403, +23%) | 73 | 5 | 0.862 | -27.9% | -133 |
| 2026-01 | blend, all, $1.5-$21, 50% (418, +14%) | 97 | 4 | 0.546 | -52.3% | -183 |
| 2026-02 | model, one a race, $1.5-$3, 2% (434, +3%) | 82 | 32 | 0.901 | -12.0% | -193 |
| 2026-03 | ensemble, one a race, $8-$13, 10% (1,840, +2%) | 356 | 35 | 1.000 | -6.3% | -216 |
| 2026-04 | blend, one a race, $8-$13, 20% (855, +4%) | 166 | 19 | 1.191 | +11.1% | -197 |
| 2026-05 | blend, one a race, $8-$13, 20% (893, +6%) | 164 | 16 | 1.005 | -8.4% | -211 |
| 2026-06 | ensemble, one a race, $8-$13, 5% (2,122, +3%) | 350 | 39 | 1.134 | +3.1% | -200 |
| 2026-07 | blend, one a race, $8-$13, 20% (955, +11%) | 198 | 14 | 0.736 | -33.4% | -266 |
| 2026-08 | blend, one a race, $8-$13, 10% (1,518, +3%) | 258 | 28 | 1.114 | +6.5% | -250 |
| 2026-09 | model, one a race, $3-$5, 30% (444, +9%) | 72 | 16 | 0.899 | -9.1% | -256 |
| 2026-10 | model, one a race, $3-$5, 30% (415, +7%) | 67 | 15 | 0.919 | -12.0% | -264 |

- Sequential rule: 1st half 1,854 bets, A/E 0.953, **-6.9%**, worst drawdown 64%, longest losing run 51; 2nd half
  1,855 bets, A/E 0.978, **-7.4%**, drawdown 65%, losing run 74; all 3,709 bets, A/E 0.967, -7.1%; 9 of 29 months
  in profit; last six -8%, +3%, -33%, +6%, -9%, -12%.
- Test 12's rule: -2.0% and -4.1% (2,275 and 2,279 bets, A/E 1.058 and 1.034; all 4,554 bets -3.0%); 14 of 29 months.
- Test 13's rule: -13.7% and -16.3% (981 and 988 bets, A/E 0.923 and 0.890; all 1,969 bets -15.0%); 7 of 29 months.

**Still nothing at BSP** with a model 0.018 closer to it. The best rule on any six months there sits at +3% to +27%
and does not hold the next month; the A/E against the sharpest price is 0.97. The next walk-forward adds GRV's tips
(Test 19, legitimate and worth 0.001) and lifts the BSP-chance rounds to 4,000 (`WALK_ROUNDS_A`, after Test 19's
early stopping chose 4,139 with the cap lifted), and GRV's rating goes in the one after if the 5 Nov compare clears
it. The open prices decide what any of this is worth at the price we can actually take.

## Test 20: the walk-forward with GRV's tips and 4,000 rounds (4 Nov 2026, gh topaz run 41875722363, `topaz_walk.py`)

Test 18's walk-forward (preview, ratings upgrades, refit every second month) plus GRV's tips for this race (Test 19,
154 inputs plus 29 relatives) and the BSP-chance model at 4,000 rounds instead of 3,000 (`WALK_ROUNDS_A`). 18 refits,
139 minutes (7.7 a refit, the same as Test 18's 3,000-round refits because the tips make the trees shallower).

| month | races | model | ensemble | GRV SP | BSP (races matched) | model gap to SP | gap to BSP |
|---|---|---|---|---|---|---|---|
| 2023-12 | 834 | 1.6310 | 1.6259 | 1.5940 | 1.5184 (754) | +0.0371 | +0.0912 |
| 2024-01 | 835 | 1.6283 | 1.6176 | 1.6075 | 1.4931 (723) | +0.0208 | +0.1109 |
| 2024-02 | 715 | 1.6412 | 1.6436 | 1.5765 | 1.5269 (664) | +0.0646 | +0.1068 |
| 2024-03 | 810 | 1.6251 | 1.6134 | 1.6308 | 1.4925 (683) | -0.0057 | +0.0977 |
| 2024-04 | 809 | 1.6197 | 1.6027 | 1.6111 | 1.4883 (705) | +0.0086 | +0.0936 |
| 2024-05 | 882 | 1.6287 | 1.6155 | 1.6492 | 1.5002 (718) | -0.0205 | +0.0814 |
| 2024-06 | 822 | 1.6759 | 1.6509 | 1.6596 | 1.5126 (640) | +0.0163 | +0.0993 |
| 2024-07 | 881 | 1.6645 | 1.6471 | 1.6876 | 1.5288 (723) | -0.0231 | +0.0866 |
| 2024-08 | 900 | 1.6542 | 1.6264 | 1.6499 | 1.4912 (705) | +0.0043 | +0.0935 |
| 2024-09 | 817 | 1.6468 | 1.6295 | 1.6379 | 1.4997 (697) | +0.0090 | +0.1090 |
| 2024-10 | 950 | 1.6215 | 1.6066 | 1.6172 | 1.4742 (835) | +0.0043 | +0.1041 |
| 2024-11 | 876 | 1.6234 | 1.6042 | 1.6091 | 1.5103 (744) | +0.0144 | +0.0733 |
| 2024-12 | 785 | 1.6781 | 1.6536 | 1.6790 | 1.5480 (616) | -0.0009 | +0.0736 |
| 2025-01 | 928 | 1.6212 | 1.6144 | 1.6159 | 1.4845 (831) | +0.0053 | +0.0961 |
| 2025-02 | 791 | 1.6264 | 1.6172 | 1.5999 | 1.5258 (749) | +0.0265 | +0.0849 |
| 2025-03 | 907 | 1.6333 | 1.6247 | 1.5737 | 1.4971 (842) | +0.0596 | +0.1126 |
| 2025-04 | 872 | 1.6201 | 1.6117 | 1.6231 | 1.4916 (774) | -0.0030 | +0.0961 |
| 2025-05 | 942 | 1.6656 | 1.6517 | 1.6700 | 1.5526 (787) | -0.0044 | +0.0669 |
| 2025-06 | 862 | 1.5908 | 1.5658 | 1.6204 | 1.4665 (747) | -0.0296 | +0.0791 |
| 2025-07 | 922 | 1.6193 | 1.6108 | 1.6292 | 1.5074 (815) | -0.0099 | +0.0790 |
| 2025-08 | 818 | 1.5442 | 1.5251 | 1.5227 | 1.4028 (723) | +0.0215 | +0.1010 |
| 2025-09 | 834 | 1.6001 | 1.5882 | 1.5933 | 1.4865 (721) | +0.0068 | +0.0785 |
| 2025-10 | 960 | 1.6264 | 1.6080 | 1.6347 | 1.4952 (821) | -0.0083 | +0.0974 |
| 2025-11 | 753 | 1.6011 | 1.5844 | 1.5705 | 1.4634 (666) | +0.0306 | +0.1050 |
| 2025-12 | 913 | 1.5839 | 1.5588 | 1.6146 | 1.4557 (786) | -0.0307 | +0.0865 |
| 2026-01 | 913 | 1.6241 | 1.6093 | 1.6056 | 1.4824 (824) | +0.0185 | +0.1113 |
| 2026-02 | 879 | 1.6051 | 1.6003 | 1.5675 | 1.4830 (828) | +0.0376 | +0.0988 |
| 2026-03 | 990 | 1.5806 | 1.5820 | 1.5360 | 1.4493 (963) | +0.0447 | +0.1214 |
| 2026-04 | 871 | 1.5509 | 1.5506 | 1.5089 | 1.4717 (860) | +0.0420 | +0.0799 |
| 2026-05 | 908 | 1.6371 | 1.6292 | 1.6255 | 1.5155 (821) | +0.0116 | +0.0905 |
| 2026-06 | 897 | 1.6267 | 1.6208 | 1.6411 | 1.4978 (814) | -0.0145 | +0.1035 |
| 2026-07 | 957 | 1.6085 | 1.6035 | 1.5671 | 1.4622 (886) | +0.0414 | +0.1299 |
| 2026-08 | 866 | 1.5808 | 1.5830 | 1.5156 | 1.4872 (856) | +0.0652 | +0.0905 |
| 2026-09 | 901 | 1.5323 | 1.5381 | 1.4641 | 1.4283 (900) | +0.0682 | +0.1031 |
| 2026-10 | 892 | 1.5147 | 1.5185 | 1.4322 | 1.4030 (892) | +0.0826 | +0.1117 |
| 2026-11 | 69 | 1.6178 | 1.6386 | 1.5317 | none matched | +0.0861 | |

Scored quarter as a whole (25,676 races): model 1.6122, ensemble 1.6006, SP 1.5952; on the 22,866 BSP-matched races
model 1.5797, BSP 1.4838, **gap +0.0959** against Test 18's +0.0987 and Test 14's +0.1171. The model beat the SP in
twelve of 36 months and sits 0.017 behind it on the quarter. The tips and the extra rounds are worth 0.003
walk-forward, the two 0.001s of Test 19 and a little more: real, small, and kept.

### Bets at GRV's SP, no commission

| month | rule chosen on the 6 months before (bets, ROI there) | bets | winners | A/E | flat ROI | cumulative units |
|---|---|---|---|---|---|---|
| 2024-06 | blend, all, $8-$13, 10% (309, +58%) | 61 | 5 | 0.808 | -27.0% | -16 |
| 2024-07 | blend, one a race, $8-$13, 5% (485, +60%) | 84 | 16 | 1.801 | +92.0% | +61 |
| 2024-08 | blend, one a race, $13-$21, 5% (356, +61%) | 75 | 8 | 1.712 | +58.3% | +104 |
| 2024-09 | blend, one a race, $13-$21, 10% (314, +80%) | 58 | 5 | 1.334 | +28.1% | +121 |
| 2024-10 | blend, one a race, $13-$21, 10% (315, +78%) | 68 | 1 | 0.233 | -77.9% | +68 |
| 2024-11 | blend, all, $8-$13, 20% (307, +56%) | 49 | 4 | 0.798 | -15.1% | +60 |
| 2024-12 | ensemble, all, $5-$8, 50% (540, +43%) | 83 | 20 | 1.501 | +47.8% | +100 |
| 2025-01 | ensemble, one a race, $5-$8, 50% (528, +46%) | 97 | 18 | 1.163 | +17.1% | +117 |
| 2025-02 | blend, one a race, $1.5-$21, 30% (454, +45%) | 63 | 16 | 1.493 | +55.2% | +152 |
| 2025-03 | blend, one a race, $8-$13, 10% (467, +56%) | 75 | 15 | 1.958 | +106.9% | +232 |
| 2025-04 | blend, one a race, $8-$13, 5% (561, +64%) | 94 | 15 | 1.572 | +57.3% | +286 |
| 2025-05 | blend, one a race, $8-$13, 10% (414, +68%) | 63 | 12 | 1.899 | +91.9% | +344 |
| 2025-06 | blend, one a race, $8-$13, 10% (482, +83%) | 76 | 12 | 1.502 | +45.7% | +378 |
| 2025-07 | blend, one a race, $8-$13, 10% (501, +76%) | 84 | 20 | 2.390 | +140.2% | +496 |
| 2025-08 | blend, one a race, $8-$13, 10% (524, +95%) | 83 | 15 | 1.781 | +72.3% | +556 |
| 2025-09 | blend, all, $8-$13, 10% (519, +91%) | 69 | 9 | 1.288 | +25.2% | +573 |
| 2025-10 | blend, all, $8-$13, 20% (333, +103%) | 53 | 10 | 1.850 | +76.4% | +614 |
| 2025-11 | blend, all, $8-$13, 20% (323, +104%) | 47 | 15 | 3.111 | +207.9% | +712 |
| 2025-12 | blend, one a race, $8-$13, 10% (458, +82%) | 87 | 14 | 1.553 | +52.3% | +757 |
| 2026-01 | blend, one a race, $8-$13, 10% (475, +77%) | 101 | 16 | 1.535 | +48.1% | +806 |
| 2026-02 | blend, one a race, $8-$13, 10% (407, +71%) | 74 | 12 | 1.566 | +48.9% | +842 |
| 2026-03 | blend, one a race, $8-$13, 10% (422, +65%) | 94 | 7 | 0.734 | -26.3% | +817 |
| 2026-04 | blend, one a race, $1.5-$21, 30% (302, +76%) | 41 | 6 | 1.043 | +57.8% | +841 |
| 2026-05 | blend, one a race, $1.5-$21, 20% (449, +55%) | 90 | 20 | 1.295 | +36.8% | +874 |
| 2026-06 | blend, one a race, $1.5-$21, 20% (584, +44%) | 111 | 33 | 1.575 | +61.0% | +942 |
| 2026-07 | blend, one a race, $1.5-$21, 20% (500, +44%) | 82 | 15 | 1.073 | +1.1% | +943 |
| 2026-08 | blend, all, $1.5-$21, 20% (452, +54%) | 54 | 10 | 1.258 | +16.3% | +951 |
| 2026-09 | blend, all, $1.5-$21, 20% (341, +65%) | 45 | 5 | 0.835 | -24.7% | +940 |
| 2026-10 | model, one a race, $8-$13, 50% (842, +28%) | 138 | 10 | 0.740 | -28.1% | +902 |
| 2026-11 | blend, all, $1.5-$21, 10% (598, +28%) | 7 | 1 | 0.931 | +42.9% | +904 |

- **Sequential rule**: 1st half 1,102 bets, A/E 1.507, **+49.7%**, bank x13.02 at 0.5% a bet, worst drawdown 36%,
  longest losing run 48; 2nd half 1,104 bets, A/E 1.324, **+32.3%**, bank x5.13, drawdown 31%, losing run 33; all
  2,206 bets, A/E 1.409, +41.0%, bank x66.78. Months in profit 24 of 30; last six +61% (111), +1% (82), +16% (54),
  -25% (45), -28% (138), +43% (7).
- **Test 12's rule**: +44.0% and +22.0% (2,004 and 2,007 bets, A/E 1.453 and 1.232, drawdown 24% and 43%, losing runs
  42 and 45; all 4,011 bets +33.0%); 23 of 30 months; last six +56%, +61%, -10%, +15%, -31%, -23% (13).
- **Test 13's rule**: +23.3% and +16.3% (1,034 and 1,034 bets, A/E 1.225 and 1.175, drawdown 15% and 32%, losing runs
  17 and 28; all 2,068 bets +19.8%); 23 of 30 months; last six +23%, -52%, +2%, -2%, -17%, +23% (6).

The same money as Test 18 (+41.0% against +39.8% over all bets, Test 12's rule +33.0% against +32.2%) arranged less
evenly: 24 months in profit against 26, and September and October 2026 lost where Test 18's model made +2% and +15%.
October is the month the chooser picked the model alone for the first time at the SP (the blend's six months before
it had fallen to +28%), on 138 bets, and lost 28%. A gap 0.003 smaller did not buy a steadier bet.

### Bets at BSP, 8% commission on winnings

| month | rule chosen on the 6 months before (bets, ROI there) | bets | winners | A/E | flat ROI | cumulative units |
|---|---|---|---|---|---|---|
| 2024-06 | blend, one a race, $5-$8, 20% (380, +19%) | 45 | 7 | 0.962 | -14.5% | -7 |
| 2024-07 | blend, one a race, $8-$13, 20% (762, +11%) | 141 | 13 | 0.962 | -5.7% | -14 |
| 2024-08 | model, one a race, $5-$8, 50% (361, +8%) | 48 | 4 | 0.517 | -52.3% | -40 |
| 2024-09 | blend, all, $1.5-$21, 50% (380, +19%) | 59 | 4 | 0.877 | -10.5% | -46 |
| 2024-10 | blend, one a race, $1.5-$21, 50% (346, +29%) | 62 | 3 | 0.678 | -41.7% | -72 |
| 2024-11 | blend, one a race, $1.5-$21, 50% (348, +35%) | 83 | 7 | 1.127 | +13.3% | -61 |
| 2024-12 | blend, one a race, $8-$13, 30% (451, +22%) | 49 | 5 | 1.060 | -7.5% | -64 |
| 2025-01 | blend, one a race, $8-$13, 30% (436, +18%) | 69 | 3 | 0.433 | -57.2% | -104 |
| 2025-02 | blend, one a race, $8-$13, 30% (422, +7%) | 74 | 11 | 1.574 | +51.7% | -65 |
| 2025-03 | blend, one a race, $8-$13, 30% (428, +12%) | 64 | 8 | 1.283 | +25.1% | -49 |
| 2025-04 | blend, one a race, $8-$13, 30% (430, +12%) | 94 | 9 | 0.987 | -5.3% | -54 |
| 2025-05 | blend, one a race, $8-$13, 30% (450, +14%) | 73 | 13 | 1.834 | +67.4% | -5 |
| 2025-06 | blend, one a race, $8-$13, 30% (423, +13%) | 75 | 5 | 0.687 | -35.0% | -31 |
| 2025-07 | blend, one a race, $8-$13, 30% (449, +7%) | 91 | 9 | 1.020 | -0.2% | -32 |
| 2025-08 | blend, one a race, $8-$13, 30% (471, +15%) | 68 | 9 | 1.359 | +22.7% | -16 |
| 2025-09 | blend, one a race, $1.5-$21, 50% (394, +19%) | 48 | 0 | 0.000 | -100.0% | -64 |
| 2025-10 | blend, one a race, $1.5-$3, 2% (348, +10%) | 68 | 31 | 1.074 | +3.2% | -62 |
| 2025-11 | blend, one a race, $1.5-$21, 50% (364, +16%) | 52 | 6 | 1.506 | +50.9% | -35 |
| 2025-12 | blend, all, $1.5-$21, 50% (366, +29%) | 69 | 5 | 0.928 | -30.5% | -56 |
| 2026-01 | blend, one a race, $1.5-$21, 50% (359, +17%) | 76 | 3 | 0.571 | -53.0% | -97 |
| 2026-02 | model, one a race, $8-$13, 5% (2,001, +4%) | 326 | 37 | 1.159 | +7.9% | -71 |
| 2026-03 | model, one a race, $8-$13, 5% (2,010, +3%) | 376 | 35 | 0.947 | -11.0% | -112 |
| 2026-04 | blend, one a race, $8-$13, 2% (1,769, +3%) | 327 | 33 | 1.029 | -3.4% | -124 |
| 2026-05 | blend, one a race, $8-$13, 2% (1,832, +1%) | 306 | 42 | 1.407 | +30.2% | -31 |
| 2026-06 | blend, one a race, $8-$13, 30% (539, +5%) | 90 | 13 | 1.481 | +31.9% | -2 |
| 2026-07 | blend, one a race, $8-$13, 30% (547, +15%) | 108 | 9 | 0.872 | -21.9% | -26 |
| 2026-08 | blend, one a race, $8-$13, 30% (582, +11%) | 104 | 13 | 1.301 | +27.0% | +2 |
| 2026-09 | blend, one a race, $8-$13, 30% (605, +16%) | 99 | 7 | 0.710 | -31.4% | -29 |
| 2026-10 | blend, one a race, $8-$13, 30% (600, +14%) | 102 | 9 | 0.887 | -12.6% | -42 |

- Sequential rule: 1st half 1,619 bets, A/E 1.042, **-2.7%**, worst drawdown 51%, longest losing run 73; 2nd half
  1,627 bets, A/E 1.068, **+0.1%**, drawdown 53%, losing run 35; all 3,246 bets, A/E 1.054, -1.3%; 11 of 29 months;
  last six +30% (306), +32% (90), -22% (108), +27% (104), -31% (99), -13% (102).
- Test 12's rule: +4.2% and -7.6% (2,217 and 2,232 bets, A/E 1.116 and 0.993; all 4,449 bets -1.7%); 12 of 29 months.
- Test 13's rule: -7.8% and -10.2% (1,006 and 1,006 bets, A/E 0.985 and 0.955; all 2,012 bets -9.0%); 9 of 29 months.

At BSP this is the first walk-forward that does not lose outright: the sequential rule's A/E is 1.05 and its second
half is level, and Test 12's rule shows a profit in its first half. It is still not a bet (a 51% drawdown for
nothing), but the direction is the direction. Both switches stay on for the production model.

## TAB's own racing feed (5 Nov 2026, run 41911907844)

The TAB app shows an "Open" price beside the current price for every greyhound runner (the founder's screenshots of
Sandown R1 at 7:47am: Kiwi Evoca open $1.95, $1.45 half an hour later; TAB opened the market between 6:45 and
7:16am, as it opened Geelong at 7:22 on 27 Oct, and in the founder's experience TAB goes up first and Sportsbet
copies). So TAB keeps the open and serves it to its app, and `greyhound/tab_api.py` reads the same public
tab-info-service with an honest client identity (field names first, the open per runner if it is there). From a
GitHub runner the service answers a plain script with an HTML page, not JSON (api.beta.tab.com.au; api.tab.com.au
does not resolve), and we do not dress a script up as a browser to get past that. It is TAB's feed to serve or not.
What this leaves: the recorder runs from Australia, where the founder is, as a one-line scheduled command on his
machine each morning after 7:30am (TAB keeps the open all day, so one read catches every race's open), or the
BetMatic routes in the sections above. The CSV it writes is the input `greyhound/opens_join.py` expects.

## Tonight's card is sealed in the public log (5 Nov 2026)

`topaz_price_upcoming.py` prices the day's VIC card before it runs. Its first run (41911162992) printed GRV's rating,
pre-race price and tip for two races' runners into the Actions log and the report artifact, and both are public on
this repository: the founder's rule is that Topaz data never sits anywhere public. The script now prints only counts,
field names and ciphertext: the card is gzip'd, encrypted with a fresh AES-256 key, and that key is encrypted to
`greyhound/keys/card_pub.pem` (`greyhound/sealed.py`, RSA-OAEP). The private key lives only where the card is read,
never in the repository. Each base64 line carries a CRC32 so a copied line can be checked on its own. The unsealed
card becomes the race page through `research/greyhound/card_page.py`, which is never committed and goes to a private
artifact. The first run's log and its report artifact still hold those two races' GRV values; deleting them is the
founder's call.

## Test 21: the gallops value rule on the dogs, and early speed (5 Nov 2026, gh topaz run 41923647913, `topaz_round9.py`)

Round 8's F2 model (D1 + preview + tips; early stopping chose 4,559 rounds), fitted once on the standard split and
scored once on the races from 3 June 2024 (25,639 with GRV's SP, 22,841 with BSP on every runner).

### Early speed (founder, on Sandown R1: "box 1, he just leads and the race is over, so the early split should matter")

From each race's own in-running record, every race since 2013: **the dog first at the first point wins 52.7%**
(103,716 runs), 52.3% from box 1 and 53.8% from boxes 7-8. Leading early decides half of all races. Knowing who will
lead is the hard part: the fastest dog on the pre-race early-speed rating leads only 30.3% of the time (39.0% from
box 1). Does the model price the early-speed dogs right? Actual wins against each price's expected wins:

| dogs | runners | wins | win % | our model expected | A/E vs our model | A/E vs BSP | A/E vs GRV's SP |
|---|---|---|---|---|---|---|---|
| fastest early, clear of the next, box 1 | 1,545 | 399 | 25.8% | 412 | 0.969 | 0.999 | 1.040 |
| fastest early, clear of the next, boxes 2-3 | 2,906 | 613 | 21.1% | 661 | 0.927 | 0.940 | 0.991 |
| fastest early, box 1 | 3,065 | 727 | 23.7% | 767 | 0.948 | 0.975 | 1.008 |
| fastest early, boxes 2-3 | 5,861 | 1,218 | 20.8% | 1,255 | 0.971 | 0.979 | 1.027 |
| fastest early, boxes 4-6 | 7,753 | 1,504 | 19.4% | 1,528 | 0.984 | 0.979 | 1.024 |
| fastest early, boxes 7-8 | 6,137 | 1,236 | 20.1% | 1,252 | 0.987 | 0.978 | 1.027 |
| second fastest early, box 1-3 | 8,845 | 1,772 | 20.0% | 1,715 | 1.033 | 1.039 | 1.073 |
| second fastest early, box 4-8 | 13,916 | 2,339 | 16.8% | 2,296 | 1.019 | 1.001 | 1.027 |
| third or slower early, box 1 | 15,132 | 2,487 | 16.4% | 2,433 | 1.022 | 1.020 | 1.032 |
| third or slower early, boxes 2-8 | 95,720 | 10,984 | 11.5% | 10,958 | 1.002 | 1.002 | 0.972 |

**The model does not under-price the early-speed dogs; it slightly over-prices them** (A/E 0.93-0.99 against our
model for every "fastest early" group, against BSP's 0.94-1.00), and the second-fastest early dogs drawn inside win a
little more often than both our model and BSP expect (1.03-1.04). The fastest early dog on a past-splits rating wins
20-26%, not the 52.7% a leader wins, because a third of the time it does not lead. The gain is in predicting the lead
better, not in weighting it more: the held-out-last-start inputs (Test 22) are the first try at that.

### The gallops value rule

As research/form_gbm/README.md writes it: a logit blend of our chance with the market's (Benter's stage 2, weights
fitted on the early-stopping months), a value bet when the market price is at least RATIO x the blended price, our
price $2-$15 (and any), staked Kelly x75 units on the chance halfway between the blend and the market, capped at 4.
1.3x is the founder's and the headline, decided before the run.

At **GRV's SP**, no commission (blend weights: ours 0.49, the SP 0.69, against about 0.2 for the model in Test 9):

| ratio | our price | half | bets | winners | A/E | flat ROI | Kelly x75 units staked | Kelly ROI | units won | worst drawdown (units) | longest losing run |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **1.3x** | **$2-$15** | **1st** | **710** | **173** | **1.522** | **+55.3%** | **1,413 (avg 1.99)** | **+56.4%** | **+797** | **58** | **21** |
| **1.3x** | **$2-$15** | **2nd** | **708** | **153** | **1.461** | **+47.6%** | **1,203 (avg 1.70)** | **+59.2%** | **+712** | **43** | **23** |
| 1.3x | any | 1st | 884 | 197 | 1.484 | +35.8% | 1,600 (avg 1.81) | +54.0% | +864 | 59 | 25 |
| 1.3x | any | 2nd | 903 | 187 | 1.532 | +65.4% | 1,378 (avg 1.53) | +62.5% | +861 | 41 | 25 |
| 1.2x | $2-$15 | 1st | 1,676 | 405 | 1.375 | +36.7% | 2,333 (avg 1.39) | +46.2% | +1,077 | 66 | 22 |
| 1.2x | $2-$15 | 2nd | 1,721 | 374 | 1.325 | +35.1% | 2,011 (avg 1.17) | +45.0% | +904 | 67 | 24 |
| 1.2x | any | 1st | 2,045 | 463 | 1.353 | +25.9% | 2,671 (avg 1.31) | +44.0% | +1,177 | 72 | 28 |
| 1.2x | any | 2nd | 2,162 | 433 | 1.336 | +36.1% | 2,300 (avg 1.06) | +46.1% | +1,060 | 65 | 23 |
| 1.1x | $2-$15 | 1st | 2,574 | 611 | 1.277 | +31.6% | 2,719 (avg 1.06) | +41.3% | +1,122 | 67 | 26 |
| 1.1x | $2-$15 | 2nd | 2,598 | 539 | 1.192 | +21.8% | 2,317 (avg 0.89) | +38.6% | +894 | 72 | 30 |
| 1.1x | any | 1st | 3,100 | 696 | 1.255 | +22.2% | 3,144 (avg 1.01) | +39.5% | +1,242 | 70 | 29 |
| 1.1x | any | 2nd | 3,232 | 630 | 1.213 | +28.2% | 2,655 (avg 0.82) | +40.2% | +1,067 | 69 | 32 |

At **BSP**, 8% commission on winnings, the blend fitted on the early-stopping months puts **no weight on our model**
(ours -0.04, BSP 1.03), so the rule finds almost nothing: 5 bets in the first half at 1.3x, none in the second; at 1.1x
29 and 22 bets at -17.1% and -14.2% flat.

**The founder's rule is the best staking rule found on the dogs.** At GRV's SP the 1.3x line on $2-$15 dogs makes
+55.3% and +47.6% flat (A/E 1.52 and 1.46) on about 700 bets a half, and +56% to +59% on turnover with Kelly x75,
with worst drawdowns of 58 and 43 units. Test 12's fixed rule made +36% / +21% on the same kind of split. The wider
ratios make more units on more bets at a lower rate. At BSP there is nothing to bet, because Betfair's price already
holds everything our model knows. Both caveats from the gallops hold: these bets are struck at the SP, a 119% book that
overprices longshots, and not at the TAB open; and the gallops found a back-filled open much softer than a live one
(+41.9% against -11.6%). This is the rule the TAB opens will be scored on the day they exist.
