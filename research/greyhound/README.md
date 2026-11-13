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

**Betwatch's answer (Jamie Watts, founder, 13 Nov 2026), and the key is on.** Price history for thoroughbreds,
greyhounds and harness goes back to November 2022 on the current API. Each bookmaker's flucs come with timestamps up
to the jump, TAB included. The first price held is the first one Betwatch picked up that day, "usually close to the
open but can miss sharp early moves", so it is not a guaranteed opening price. $99 a month after a free trial, one key
for all three codes. Rate limits are dynamic, so big pulls need pacing. "Using the data for your own models, not
shared or resold, is fine." A beta platform (free, better opening prices) has no history yet.

The founder added the key as the Actions secret `BETWATCH_API_KEY`. `greyhound/betwatch.py` with the `gh betwatch`
workflow:
- **probe** prints counts only for sample days: races, runners, TAB coverage, flucs per runner, and how long before
  the jump TAB's first price lands.
- **pull** writes month files of every Victorian greyhound race with TAB, Sportsbet and Ladbrokes flucs (the last
  price only for other bookmakers) into the repository's Actions cache, paced at a call a second. It is resumable.

Nothing is printed but counts, and nothing is stored anywhere public.

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

**The 4 Nov compare** (run 41931171614, the next morning): the 56 runners snapshotted at 21:19 Sydney on 4 Nov, before
their 8 races ran, against the bulk feed for that day:

| field | the same after the race |
|---|---|
| comment | 56 of 56 (none changed, none filled late) |
| GRV's rating | 56 of 56 |
| isBestBet | 56 of 56 |
| race analystComment | 8 of 8 |
| tips (tip1-4) | 8 of 8; all 32 tip values are box numbers |
| the pre-race `startPrice` against the bulk `startPrice` | **1 of 56**; correlation of log prices +0.775, median change 72%; the pre-race prices make a 123% book (8 races) |

Two things settled. **GRV's preview, tips and rating are written before the race and not touched after**, so the
preview (Test 15), the tips (Test 19) and **GRV's rating are legitimate inputs**: the rating is the D3 row of Test 16,
worth another 0.009 against BSP, and it goes into the next walk-forward (`WALK_GRV_RATING=yes`). Test 9's leak check
on the rating was reading something else (most likely the rating being set from the previous run's result, which is
allowed). **The `startPrice` GRV shows before the race is not the SP**: it is a separate price, a 122-123% book, that
moves to the bulk `startPrice` by a median 72%. Every staking test (12, 14, 16, 18, 20, 21) bet at the bulk
`startPrice`, the SP at the jump, so none of them is a test of the evening price; tonight's paper bets, picked against
it, are names to check at TAB's open, not bets the backtest stands behind. The 5 Nov snapshot (10:08 Sydney, run
41931175896: 50 races, 382 runners, comment, rating and price on all 382, isBestBet on 13, a 122% book, tips on 50 of
50, no results in) is compared tomorrow morning.

**The 5 Nov compare** (run 42127040392, 6 Nov): the snapshot of all 50 races and 382 runners, taken at 10:08 Sydney on
race day, against the bulk feed for that day. One snapshot file is kept per day, and the 10:08 read replaced the 21:45
read of the evening before.

| field | the same after the race |
|---|---|
| comment | 380 of 382 (2 changed, none filled late) |
| GRV's rating | 382 of 382 |
| isBestBet | 382 of 382 |
| race analystComment | 47 of 50 |
| tips (tip1-4) | filled before on 50 of 50, the same after on 46 of 50; 197 of the 200 tip values are box numbers |
| the pre-race `startPrice` against the bulk `startPrice` | **1 of 382**; correlation of log prices +0.685 on 347 runners, median change 76%; the pre-race prices make a 122% book (median of 50 races) |

The second day confirms the first on the two things that matter:
- **GRV's rating and isBestBet are never touched after the race** (382 of 382 each), so the rating in the weekly model
  stands
- **the bulk `startPrice` is the SP at the jump, not the price GRV shows beforehand** (1 of 382 equal), so every
  staking test bet at the real SP

The comments and tips are not quite frozen on a full day. Two runner comments, 3 race comments and the tips of 4 races
in 50 changed between 10:08 and the bulk feed. The likeliest cause is late scratchings, after which GRV re-tips a race
before it runs; nothing here can tell that from a post-race edit. At 4 races in 50 it cannot be most of what the tips
are worth, but the tips' value (Test 19, 0.001) is small enough that this does not matter either way.

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

## Test 22: held out last start by a quicker leader, fastest early today (5 Nov 2026, gh topaz run 41928002206, `topaz_round10.py`)

The founder's idea, on Sandown R1: "if it didn't lead or get held out because there was a faster leader in that race,
but this race now he's the fastest". Eight new inputs, all built from the dog's previous start only:

- whether it led at the first point
- its split rank in that race
- its gap to the leader's split
- its pre-race speed rank there and here
- whether its speed rank has gone up
- a flag for "held out": it did not lead, a quicker beginner did, and today it is the fastest early dog in the field

The flag is on for 4.4% of runners (32,715). The previous-start inputs are filled on 92%.

The setup was the same standard split as Test 21:
- trained before 3 June 2024
- scored on the 22,841 races after it with BSP on every runner
- BSP's log loss on those races is 1.4839

G0 is round 8's F2 again; G1 adds the eight inputs.

| row | inputs | rounds | early-stopping log loss | scored log loss | gap to BSP | 1st half | 2nd half |
|---|---|---|---|---|---|---|---|
| G0 F2 (D1 + preview + tips) | 186 | 4,205 | 1.5985 | 1.5893 | +0.1054 | +0.0979 | +0.1121 |
| G1 + held out last start | 194 | 3,744 | 1.6000 | 1.5891 | +0.1052 | +0.0970 | +0.1126 |

The new inputs take 0.5% of the model's splits. The largest is speed_rank_up relative to the race, at 0.2%. The
held-out flag itself takes 0.0%.

Are the held-out dogs under-priced? This compares actual wins against expected wins on the scored races with BSP:

| dogs | runners | wins | win % | G0 expected | A/E vs G0 | A/E vs G1 | A/E vs BSP | A/E vs GRV's SP |
|---|---|---|---|---|---|---|---|---|
| held out last start, fastest early today | 7,378 | 1,510 | 20.5% | 1,519 | 0.994 | 0.990 | 0.987 | 1.031 |
| ... and drawn box 1-2 | 2,025 | 454 | 22.4% | 480 | 0.945 | 0.940 | 0.964 | 1.002 |
| fastest early today, led last start | 6,839 | 1,535 | 22.4% | 1,619 | 0.948 | 0.954 | 0.980 | 1.021 |
| fastest early today, did not lead last start | 15,237 | 2,993 | 19.6% | 3,021 | 0.991 | 0.989 | 0.978 | 1.025 |
| all other runners | 137,895 | 18,156 | 13.2% | 18,039 | 1.007 | 1.006 | 1.006 | 0.994 |

**No gain.** The gap to BSP moves by 0.0002 (+0.1054 to +0.1052), which is noise; the first half got slightly worse
and the second slightly better.

The held-out dogs are not a hidden edge. They win 20.5%, against 20.6% expected by our model and 20.7% by BSP. The ones
drawn inside win less than both expect (A/E 0.945 and 0.964).

The model and Betfair already treat a dog that was beaten to the lead as a dog that may be beaten to it again. Only
GRV's SP under-rates the fastest early dogs, by 2-3%, and that is the overround on the favourites rather than a fact
about speed.

The one group the model over-prices is the fastest early dog that led last start (A/E 0.948). This is the same
over-pricing of early speed that Test 21 found. It suggests the model leans on the last lead a little too hard. It does
not suggest an input that is missing.

These inputs stay out of the model.

## Test 23: reliable beginners and box preference (5 Nov 2026, gh topaz run 41929274182, `topaz_round11.py`)

The founder: "What about reliable beginners versus not? Because they won't do the same every time as they miss it
sometimes ... and then what about like speed from certain boxes etc? Some dogs like being inside versus outside and vice
versa". Eight new inputs, every one from runs on earlier days only. Box groups: inside = boxes 1-3, middle = 4-5,
outside = 6-8.

Reliable beginners:

| input | what it measures | filled |
|---|---|---|
| split_sd10 | spread of its first-split rating over its last 10 runs (high = erratic) | 82% |
| split_worst5 | its worst first-split rating in its last 5 | 87% |
| missed_rate10 | share of its last 10 where it was 3+ places worse at the first point than its early-speed rank | 85% |
| early_sd10 | spread of its position at the first point over its last 10 | 82% |

Box preference:

| input | what it measures | filled |
|---|---|---|
| box_pref_time | its time rating from today's kind of box minus its overall rating, shrunk to 0 by 3 runs | 92% |
| box_pref_split | the same for its first-split rating | 92% |
| box_runs_here | how many runs it has had from today's kind of box | 99% |
| inside_vs_out | its shrunk inside rating minus its shrunk outside rating, signed by today's draw | 92% |

The setup was the same standard split as Tests 21 and 22:
- trained before 3 June 2024
- scored on the 22,841 races after it with BSP on every runner
- BSP's log loss on those races is 1.4839

H0 is round 8's F2 again.

| row | inputs | rounds | early-stopping log loss | scored log loss | gap to BSP | 1st half | 2nd half |
|---|---|---|---|---|---|---|---|
| H0 F2 (D1 + preview + tips) | 186 | 4,205 | 1.5985 | 1.5893 | +0.1054 | +0.0979 | +0.1121 |
| H1 + reliable beginners | 192 | 5,173 | 1.5979 | 1.5883 | **+0.1044** | +0.0964 | +0.1116 |
| H2 + box preference | 192 | 2,848 | 1.6004 | 1.5889 | +0.1050 | +0.0971 | +0.1121 |
| H3 + both | 198 | 1,824 | 1.5991 | 1.5902 | +0.1063 | +0.0977 | +0.1140 |

Share of the model's splits taken by the new inputs:

| row | new inputs' share | largest |
|---|---|---|
| H1 | 1.0% | split_sd10, split_worst5, early_sd10, missed_rate10 relative to the race: 0.2% each |
| H2 | 0.7% | box_runs_here 0.2% |
| H3 | 1.2% | box_runs_here 0.2% |

Actual wins against expected wins, on the scored races with BSP:

| dogs | runners | wins | win % | H0 expected | A/E vs H0 | A/E vs H3 | A/E vs BSP | A/E vs GRV's SP |
|---|---|---|---|---|---|---|---|---|
| fastest early, reliable beginner (steadiest quarter on split_sd10) | 4,579 | 874 | 19.1% | 931 | 0.939 | 0.935 | 0.944 | 0.984 |
| fastest early, erratic beginner (most erratic quarter) | 5,451 | 1,107 | 20.3% | 1,099 | 1.007 | 1.000 | 0.993 | 1.035 |
| missed the start in 30%+ of its last 10 | 24,868 | 3,407 | 13.7% | 3,370 | 1.011 | 1.017 | 1.017 | 1.008 |
| drawn in the kind of box it races best from (top quarter of box_pref_time) | 40,183 | 6,005 | 14.9% | 5,795 | 1.036 | 1.010 | 0.994 | 1.008 |
| drawn in the kind of box it races worst from (bottom quarter) | 40,183 | 5,394 | 13.4% | 5,481 | 0.984 | 0.997 | 1.011 | 0.996 |
| drawn on the side it races best from (top tenth of inside_vs_out) | 15,449 | 2,567 | 16.6% | 2,369 | 1.084 | 1.036 | 1.006 | 1.040 |
| drawn on the side it races worst from (bottom tenth) | 15,449 | 2,178 | 14.1% | 2,192 | 0.994 | 1.009 | 1.016 | 1.006 |

The test of whether an A/E is real is how far it sits from 1.000 in standard errors. One standard error is about
1/sqrt(wins): 0.034 on 874 wins, 0.020 on 2,567, 0.013 on 6,005.

**Reliable beginners: a 0.001 gain, at the edge of the noise.** H1 moves the gap from +0.1054 to +0.1044, and both
halves improve (by 0.0015 and 0.0005). The size matches the run-to-run noise of this split: D1 scored +0.1085, +0.1087
and +0.1072 on three fits.

The founder's guess on direction was half right. The steadiest fast beginners win LESS than expected:
- 19.1% from 4,579 runs
- A/E 0.939 against our model and 0.944 against BSP, about 1.7 standard errors below 1

So both the model and Betfair over-price them a little. The erratic fast beginners are priced right (1.007 and 0.993).
The over-pricing of early speed in Tests 21 and 22 sits in the steady dogs, not the erratic ones. One reading: the
market and the model both bank on a reliable dog leading, and when it does not, it has nothing else. At 1.7 standard
errors this is a lead, not a finding. It is worth watching in the walk-forward as a lay angle at BSP, not betting on.

**Box preference: our model was missing it, and Betfair was not.** A dog drawn on the side it races best from wins
16.6%:
- **A/E 1.084 against H0**, which is 4 standard errors and real
- 1.006 against BSP, so Betfair prices it right
- 1.040 against GRV's SP

Adding the inputs (H3) takes the model to 1.036, and the box-preference top quarter from 1.036 to 1.010. But it does not
move the log loss (H2 +0.1050). Those dogs are a tenth of the field, and the correction is a few per cent of their
chance, so the gain is under a thousandth.

H3 (both) is worse than either alone, +0.1063, with early stopping choosing only 1,824 rounds. That is the noise of
this split showing itself, not a reason to believe the two cancel.

**What goes forward.** The reliable-beginner inputs (H1) join the final walk-forward as a candidate. The walk-forward's
30 months judge a 0.001 better than one split can. The box-preference inputs stay out: they fix a pricing error Betfair
does not make and add nothing measurable.

The gap to BSP is still about 0.104, which is where Tests 19 to 22 left it. Form inputs built from the dog's own
history have stopped moving it. What remains is mostly:
- the lead, which needs tracking data (Isolynx, still 401)
- the market's own money, which needs the TAB opens

## Test 24: the old greyhound tales against Betfair, and where we are closest to BSP (5 Nov 2026, gh topaz run 41937604493, `topaz_round12.py`)

The founder: "Keep testing things like I said, the ole greyhound tales on how to back them and how we can get the model
closer, look for data things". Thirty tales a punter can apply before the race, each with:
- A/E (actual wins against expected) at BSP and at GRV's SP, both renormalised to a 100% book
- flat 1-unit ROI at BSP after 8% commission on winnings, and at GRV's SP as paid

The tales are scored on every race since 2020 where Betfair priced every runner: 65,285 races, in halves split at
9 May 2023. The favourite tales use GRV's SP favourite.

### Part 1: the tales, no model

| tale | runners | win % | A/E at BSP (1st / 2nd) | flat ROI at BSP, 8% comm (1st / 2nd) | A/E at GRV's SP (1st / 2nd) | flat ROI at GRV's SP (1st / 2nd) |
|---|---|---|---|---|---|---|
| box 1 | 62,326 | 18.4% | 1.006 / 1.003 | -6.8% / -9.5% | 0.992 / 1.021 | -22.6% / -19.8% |
| box 2 | 61,869 | 16.0% | 1.006 / 1.006 | -5.9% / -6.1% | 1.022 / 1.024 | -18.9% / -17.4% |
| box 8 | 61,397 | 14.5% | 0.971 / 0.982 | -10.8% / -8.9% | 0.968 / 0.996 | -25.7% / -22.6% |
| SP favourite | 66,868 | 40.6% | 0.996 / 0.998 | -5.2% / -5.9% | 1.012 / 1.035 | -14.9% / -13.6% |
| SP favourite in box 1 | 13,839 | 42.8% | 1.011 / 1.001 | -2.9% / -6.1% | 1.016 / 1.042 | -14.6% / -12.9% |
| SP favourite in box 7-8 | 16,857 | 40.3% | 1.002 / 0.998 | -4.7% / -6.3% | 1.017 / 1.039 | -14.5% / -13.4% |
| SP favourite, 6 or fewer runners | 19,117 | 45.0% | 0.980 / 0.977 | -7.1% / -7.6% | 1.000 / 1.015 | -16.7% / -14.4% |
| won last start | 62,978 | 19.7% | 0.987 / 1.012 | -11.7% / -8.1% | 0.998 / 1.026 | -22.8% / -20.0% |
| won its last two | 12,072 | 25.2% | 0.972 / 1.024 | -11.2% / -7.3% | 0.997 / 1.059 | -21.4% / -18.6% |
| beaten favourite last start | 37,700 | 22.0% | 0.991 / 0.985 | -10.0% / -6.9% | 1.018 / 1.030 | -17.9% / -15.2% |
| first up after 28+ days | 31,603 | 14.0% | 0.992 / 0.997 | -8.9% / -11.6% | 0.982 / 0.989 | -25.0% / -26.6% |
| second up after a 28+ day spell | 25,413 | 15.1% | 0.990 / 0.986 | -7.9% / -0.2% | 1.000 / 0.990 | -24.0% / -21.6% |
| **backing up within 4 days** | **77,416** | **13.7%** | **1.025 / 1.028** | **-6.6% / -5.9%** | **1.020 / 1.026** | **-22.2% / -20.6%** |
| dropping in grade | 69,264 | 15.4% | 1.015 / 0.994 | -5.9% / -9.1% | 1.023 / 1.014 | -19.8% / -21.0% |
| rising in grade | 92,872 | 14.2% | 0.986 / 1.016 | -12.6% / -6.0% | 0.981 / 1.003 | -26.5% / -24.3% |
| up 50m+ in trip | 76,499 | 13.2% | 1.009 / 1.005 | -10.9% / -9.2% | 0.997 / 0.993 | -25.7% / -25.0% |
| down 50m+ in trip | 63,989 | 14.8% | 1.015 / 1.001 | -4.6% / -9.0% | 1.021 / 1.017 | -20.3% / -22.7% |
| debut | 12,728 | 15.1% | 0.961 / 0.981 | -14.9% / -11.2% | 0.959 / 0.965 | -26.1% / -24.7% |
| first time at the track (not debut) | 85,410 | 16.7% | 1.014 / 1.009 | -4.9% / -5.5% | 1.023 / 1.030 | -19.1% / -19.2% |
| vacant box beside it | 108,507 | 15.9% | 1.000 / 1.001 | -8.4% / -9.2% | 1.003 / 0.998 | -22.0% / -22.6% |
| box 1, box 2 vacant | 3,253 | 20.8% | 0.995 / 0.991 | +2.7% / -14.2% | 0.965 / 0.975 | -19.8% / -24.8% |
| weight up 1kg+ since last start | 3,407 | 12.5% | 1.015 / 0.936 | +0.7% / +3.4% | 1.001 / 0.931 | -24.7% / -25.5% |
| weight down 1kg+ since last start | 2,684 | 11.3% | 0.948 / 0.962 | -5.1% / -9.8% | 0.931 / 0.920 | -22.5% / -25.9% |
| trainer has 2+ in the race | 50,378 | 12.9% | 1.009 / 0.995 | -11.3% / -11.6% | 1.004 / 0.974 | -23.6% / -24.3% |
| under 2 years old | 72,964 | 19.2% | 1.009 / 1.012 | -5.5% / -5.5% | 1.029 / 1.052 | -17.0% / -15.2% |
| over 4 years old | 36,227 | 8.7% | 0.976 / 1.019 | -15.8% / -19.1% | 0.915 / 0.912 | -33.8% / -36.9% |
| hot trainer (top tenth, 28-day strike rate) | 50,408 | 20.9% | 0.995 / 1.010 | -10.8% / -8.3% | 1.016 / 1.048 | -21.1% / -17.9% |
| sex recorded as Dog | 260,066 | 15.3% | 1.000 / 1.000 | -7.6% / -9.4% | 1.007 / 1.010 | -21.0% / -22.5% |
| sex recorded as Bitch | 195,932 | 13.0% | 1.000 / 0.999 | -8.1% / -9.4% | 0.989 / 0.986 | -24.0% / -24.0% |
| maiden race | 69,295 | 14.3% | 1.000 / 0.997 | -3.6% / -6.4% | 0.998 / 0.996 | -21.7% / -23.4% |
| night race (6pm on) | 84,824 | 14.2% | 1.000 / 1.000 | -8.1% / -9.4% | 1.000 / 1.000 | -24.3% / -23.9% |
| day race (before 6pm) | 371,174 | 14.3% | 1.000 / 1.000 | -7.8% / -9.4% | 1.000 / 1.000 | -21.7% / -22.9% |
| GRV's first tip | 63,948 | 34.9% | 0.980 / 0.974 | -8.0% / -9.8% | 1.019 / 1.037 | -14.6% / -14.3% |
| GRV's best bet | 16,201 | 46.5% | 0.996 / 1.001 | -4.6% / -5.2% | 1.053 / 1.092 | -11.0% / -8.4% |

The favourite-longshot question at BSP:

| BSP | runners | win % | A/E at BSP (1st / 2nd) | flat ROI at BSP, 8% comm (1st / 2nd) |
|---|---|---|---|---|
| $1-$2 | 17,459 | 60.7% | 0.995 / 1.000 | -4.5% / -3.8% |
| $2-$3 | 32,814 | 40.1% | 0.988 / 1.012 | -6.0% / -4.2% |
| $3-$5 | 67,382 | 25.7% | 1.004 / 0.985 | -5.7% / -7.8% |
| $5-$8 | 67,154 | 15.9% | 0.999 / 0.993 | -7.0% / -7.7% |
| $8-$13 | 66,334 | 10.0% | 0.996 / 1.033 | -7.9% / -4.8% |
| $13-$21 | 57,551 | 6.4% | 1.050 / 1.016 | -3.0% / -6.6% |
| $21-$51 | 78,352 | 3.3% | 1.009 / 0.985 | -7.8% / -10.5% |
| $51+ | 68,951 | 0.9% | 0.957 / 0.943 | -16.5% / -21.6% |

**No tale beats BSP after commission in both halves.** Betfair's price is within 3% of the truth on all thirty, in both
halves. Only two tales show a positive ROI at BSP, and neither holds up:
- box 1 with box 2 vacant: +2.7% in the first half, then -14.2%
- weight up 1kg+: +0.7% / +3.4% on 3,407 runners, from a few long-priced winners. Its second-half A/E is 0.936.

The steadiest tale is **backing up within 4 days**. BSP under-rates those dogs by 2.5% and 2.8%, the same in both halves,
on 77,416 runners. That is still -6% after the 8% commission. A market bias of 2-3% is smaller than the commission.
The same holds the other way: GRV's first tip is over-bet at BSP (A/E 0.980 / 0.974), but laying it at BSP still loses
after commission.

BSP's favourite-longshot bias is small next to a bookmaker's:
- $1 to $51 dogs are priced within 1-5%, and A/E is never consistently above 1
- $51+ dogs win 4-6% less than BSP says

**GRV's SP is where the tales live**, and it is a bookmaker price with a 19% margin:
- it under-rates GRV's own best bets (A/E 1.053 / 1.092), young dogs (1.029 / 1.052), hot trainers (1.016 / 1.048) and
  favourites (1.012 / 1.035)
- it over-rates dogs over 4 (0.915 / 0.912), debutants and big weight changes

Flat backing at the SP still loses 8-37% on every tale. The 1.3x rule earns at the SP (Test 21) because it bets only
where our price and the SP disagree by 30% or more.

### Part 2: our model (round 8's F2, 4,205 rounds), the 22,841 scored races with BSP from 3 June 2024

Our log loss on these races is 1.5893, against BSP's 1.4839.

| tale | runners | wins | A/E vs our model | A/E vs BSP | A/E vs GRV's SP |
|---|---|---|---|---|---|
| box 1 | 21,856 | 4,006 | 1.003 | 1.009 | 1.029 |
| box 2 | 21,710 | 3,413 | 0.994 | 0.998 | 1.014 |
| box 8 | 21,563 | 3,187 | 1.002 | 0.987 | 1.006 |
| SP favourite | 23,466 | 9,302 | **1.159** | 0.998 | 1.036 |
| SP favourite in box 1 | 4,727 | 2,007 | 1.146 | 1.009 | 1.055 |
| SP favourite in box 7-8 | 5,956 | 2,382 | 1.207 | 1.005 | 1.053 |
| SP favourite, 6 or fewer runners | 6,325 | 2,793 | 1.129 | 0.982 | 1.021 |
| won last start | 21,669 | 4,204 | 0.981 | 1.011 | 1.025 |
| won its last two | 4,046 | 1,006 | 0.995 | 1.035 | 1.069 |
| beaten favourite last start | 13,404 | 2,874 | 1.006 | 0.993 | 1.041 |
| first up after 28+ days | 10,504 | 1,394 | 0.999 | 0.963 | 0.955 |
| second up after a 28+ day spell | 8,516 | 1,211 | 0.971 | 0.971 | 0.971 |
| backing up within 4 days | 25,743 | 3,522 | 1.025 | 1.022 | 1.020 |
| dropping in grade | 23,076 | 3,567 | 1.008 | 0.992 | 1.015 |
| rising in grade | 31,000 | 4,352 | 1.003 | 1.011 | 0.998 |
| up 50m+ in trip | 25,991 | 3,450 | 1.010 | 1.004 | 0.991 |
| down 50m+ in trip | 20,475 | 2,978 | 1.012 | 0.990 | 1.006 |
| **debut** | 3,796 | 562 | **0.929** | 0.969 | 0.955 |
| first time at the track (not debut) | 25,940 | 4,283 | 1.011 | 1.007 | 1.030 |
| vacant box beside it | 36,857 | 5,776 | 0.996 | 0.992 | 0.988 |
| box 1, box 2 vacant | 1,082 | 218 | 0.964 | 0.968 | 0.956 |
| weight up 1kg+ since last start | 1,156 | 127 | 0.934 | 0.881 | 0.879 |
| weight down 1kg+ since last start | 848 | 90 | 0.928 | 0.928 | 0.882 |
| **trainer has 2+ in the race** | 19,255 | 2,457 | **0.966** | 0.997 | 0.975 |
| under 2 years old | 23,025 | 4,498 | 1.034 | 1.018 | 1.064 |
| over 4 years old | 16,044 | 1,417 | 0.977 | 1.037 | 0.919 |
| hot trainer (top tenth, 28-day strike rate) | 15,855 | 3,326 | 1.024 | 1.017 | 1.057 |
| sex recorded as Dog | 90,684 | 13,628 | 1.000 | 0.997 | 1.006 |
| sex recorded as Bitch | 70,047 | 9,213 | 1.000 | 1.005 | 0.991 |
| maiden race | 22,148 | 3,129 | 0.995 | 0.996 | 0.994 |
| night race (6pm on) | 27,542 | 3,834 | 1.000 | 1.000 | 1.000 |
| day race (before 6pm) | 133,189 | 19,007 | 1.000 | 1.000 | 1.000 |
| **GRV's first tip** | 22,668 | 7,609 | **0.964** | 0.970 | 1.035 |
| GRV's best bet | 6,245 | 2,826 | 0.999 | 0.996 | 1.092 |

The gap to BSP by kind of race (winner log loss, ours less BSP's):

| Betfair BSP volume on the race (fifth boundaries 2,467 / 3,468 / 4,603 / 6,300) | races | our log loss | BSP | gap to BSP |
|---|---|---|---|---|
| thinnest fifth | 4,569 | 1.6243 | 1.5144 | +0.1100 |
| second fifth | 4,568 | 1.5961 | 1.4866 | +0.1095 |
| middle fifth | 4,568 | 1.6159 | 1.5027 | +0.1132 |
| fourth fifth | 4,568 | 1.5800 | 1.4800 | +0.1000 |
| deepest fifth | 4,568 | 1.5301 | 1.4357 | +0.0944 |

| track | races | our log loss | BSP | gap to BSP |
|---|---|---|---|---|
| BAL | 2,293 | 1.5945 | 1.4849 | +0.1096 |
| BEN | 2,159 | 1.6025 | 1.4869 | +0.1156 |
| GEL | 2,366 | 1.5693 | 1.4680 | +0.1013 |
| HOR | 1,321 | 1.5037 | 1.3991 | +0.1046 |
| HVL | 1,818 | 1.5819 | 1.4431 | +0.1388 |
| MEA | 844 | 1.6321 | 1.5686 | +0.0635 |
| MEP | 1,216 | 1.5499 | 1.4506 | +0.0993 |
| SAN | 1,041 | 1.5860 | 1.5135 | +0.0725 |
| SAP | 1,101 | 1.4689 | 1.3887 | +0.0802 |
| SHP | 1,962 | 1.6039 | 1.4992 | +0.1046 |
| SLE | 1,755 | 1.6529 | 1.5486 | +0.1043 |
| TRA | 426 | 1.6744 | 1.5625 | +0.1119 |
| WBL | 2,185 | 1.6386 | 1.5150 | +0.1235 |
| WGL | 2,354 | 1.5879 | 1.4889 | +0.0990 |

| race | races | our log loss | BSP | gap to BSP |
|---|---|---|---|---|
| day | 19,007 | 1.5844 | 1.4824 | +0.1020 |
| night (6pm on) | 3,834 | 1.6136 | 1.4910 | +0.1226 |
| maiden | 3,397 | 1.5872 | 1.4668 | +0.1203 |
| not maiden | 19,834 | 1.5896 | 1.4866 | +0.1031 |
| 6 or fewer runners | 6,163 | 1.4125 | 1.3182 | +0.0943 |
| 7 runners | 8,294 | 1.6008 | 1.4918 | +0.1091 |
| 8+ runners | 8,384 | 1.7078 | 1.5978 | +0.1100 |

The 1.3x rule (our price $2-$15, Kelly x75, cap 4, 8% commission) at three Betfair prices, each with its own Benter
blend fitted on the early-stopping months:

| price | blend weights (ours / market) | half | bets | winners | flat ROI |
|---|---|---|---|---|---|
| BSP | -0.04 / 1.03 | 1st / 2nd | 5 / 0 | 1 / 0 | +88.0% / none |
| best back price at the scheduled off | -0.03 / 1.04 | 1st / 2nd | 5 / 1 | 1 / 1 | +260.4% / +515.2% |
| pre-play weighted average price | -0.05 / 1.05 | 1st / 2nd | 0 / 0 | | |
| BSP, thinnest fifth of markets | -0.04 / 1.03 | 1st / 2nd | 5 / 0 | 1 / 0 | +88.0% / none |

### What it says

**Betfair already knows the old tales.** At any Betfair price (BSP, the best back price at the scheduled off, or the
pre-play average) the blend puts no weight on our model, so there is nothing to bet. The six bets above are
noise.

Our gap to BSP is not smaller in thin markets: the thinnest fifth is +0.1100 and the deepest +0.0944. It is smallest at
MEA and SAN (+0.06 to +0.07) and in small fields, and largest at HVL (Healesville's straight, +0.139), at WBL, at night
and in maidens.

*Correction (6 Nov 2026, Test 41): the day and night rows in this test are wrong. The start time was read as UTC, and a
Melbourne time with no zone came out 10 or 11 hours late, so "night (6pm on)" here is mostly late-morning races. The
parse is fixed; the day/night split will be rerun.*

**The tales our model misses are fixes for the model, not bets:**

| what the model gets wrong | A/E vs our model | A/E vs BSP |
|---|---|---|
| over-prices debutants | 0.929 | 0.969 |
| over-prices a trainer's second runner in the race | 0.966 | 0.997 |
| over-prices GRV's first tip | 0.964 | 0.970 |
| under-prices dogs under 2 | 1.034 | 1.018 |
| under-prices dogs backing up within 4 days | 1.025 | 1.022 |

The trainer one is the cleanest. BSP prices it right while our model is 3.4% out, which says Betfair reads which of a
trainer's dogs is the stable's elect and our model does not.

**The SP favourite wins 16% more often than our model says** (A/E 1.159), against BSP's 0.998. That is not a tale but the
size of what the market knows and we do not, concentrated where the money goes: on the dog it makes favourite. Only
market information (the TAB opens, Betfair's early prices) or information the market uses (the lead, Isolynx) can close
it.

The Betfair files carry more columns than we use: the highest, lowest and last price matched before the off, pre-play
volume, the best lay at the scheduled off, and the back and lay market percentages. The highest pre-play price matched
is the nearest thing in free history to an early price, and is the next test of the founder's "TAB opens first" idea on
Betfair's side.

## Test 25: the drift (5 Nov 2026, gh topaz run 41941247168, `topaz_round13.py`)

The founder, on Shepparton R2: "So Hot So Swifty $3.20 to $19 and runs last by 100 lengths ... our model is fkn no
where". A dog whose price blows out before the off is the market saying something no form guide holds. Betfair's free
files give, for every runner, the shortest and longest price matched before the off, so with BSP:
- **drift** = BSP over the shortest price matched before the off (So Hot Swifty: $19 / $3.20 = 5.9x)
- **firm** = the longest price matched over BSP

The drift is measured to the off, so it is known only as the jump approaches. A guard built on it is a rule for bets
struck late, or for a live price checked against its shortest; it is not available at the TAB open.

### Part 1: no model, 65,060 races from 2020 with BSP and a pre-play price on every dog, halves split at 13 May 2023

| BSP over the shortest price matched (drifted) | runners | win % | A/E at BSP (1st / 2nd) | flat ROI at BSP, 8% comm (1st / 2nd) | A/E at GRV's SP (1st / 2nd) |
|---|---|---|---|---|---|
| under 1.1x | 119,862 | 24.0% | 0.992 / 0.989 | -7.5% / -8.5% | 1.074 / 1.102 |
| 1.1-1.3x | 144,643 | 16.1% | 1.008 / 1.013 | -5.8% / -7.0% | 1.017 / 1.020 |
| 1.3-1.6x | 92,718 | 9.7% | 1.005 / 0.999 | -7.7% / -10.0% | 0.925 / 0.878 |
| 1.6-2.2x | 59,024 | 5.4% | 0.999 / 1.011 | -13.2% / -7.2% | 0.805 / 0.715 |
| 2.2-3.5x | 27,569 | 2.5% | 0.949 / 0.996 | -10.0% / -17.6% | 0.590 / 0.504 |
| 3.5x+ | 10,574 | 1.2% | 1.355 / 0.872 | -2.9% / -39.5% | 0.544 / 0.257 |

| the longest price matched over BSP (firmed) | runners | win % | A/E at BSP (1st / 2nd) | flat ROI at BSP, 8% comm (1st / 2nd) | A/E at GRV's SP (1st / 2nd) |
|---|---|---|---|---|---|
| under 1.1x | 121,549 | 14.8% | 1.004 / 1.013 | -6.3% / -7.3% | 0.941 / 0.975 |
| 1.1-1.3x | 162,880 | 16.6% | 1.000 / 1.005 | -5.7% / -8.1% | 1.014 / 1.030 |
| 1.3-1.6x | 102,216 | 13.8% | 0.996 / 0.978 | -9.1% / -10.4% | 1.032 / 1.001 |
| 1.6-2.2x | 48,112 | 10.1% | 0.998 / 0.986 | -9.2% / -14.2% | 1.030 / 0.979 |
| 2.2-3.5x | 15,333 | 6.0% | 1.018 / 0.978 | -19.3% / -14.7% | 1.008 / 0.873 |
| 3.5x+ | 4,301 | 3.1% | 0.988 / 0.803 | -39.2% / -30.7% | 0.918 / 0.608 |

### Part 2: our model (F2, 2,626 rounds), the 22,769 scored races with BSP from 5 June 2024

One more day of results was in the cache than for Test 24, so the split and the fit moved slightly.

| drift | runners | wins | A/E vs our model | A/E vs BSP | A/E vs GRV's SP |
|---|---|---|---|---|---|
| under 1.1x | 42,834 | 9,986 | **1.179** | 0.986 | 1.106 |
| 1.1-1.3x | 52,447 | 8,463 | 1.024 | 1.016 | 1.026 |
| 1.3-1.6x | 32,208 | 3,075 | 0.810 | 1.010 | 0.884 |
| 1.6-2.2x | 19,527 | 986 | 0.613 | 1.001 | 0.697 |
| 2.2-3.5x | 9,176 | 207 | **0.426** | 0.955 | 0.469 |
| 3.5x+ | 3,913 | 33 | **0.264** | 0.848 | 0.242 |

The 1.3x rule at GRV's SP (our price $2-$15, Kelly x75 cap 4; blend ours 0.49 / SP 0.70), split by the dog's drift on
Betfair:

| drift | half | bets | winners | A/E | flat ROI | Kelly ROI | units won |
|---|---|---|---|---|---|---|---|
| under 1.1x | 1st | 221 | 75 | 1.776 | +95.7% | +81.5% | +439 |
| under 1.1x | 2nd | 150 | 57 | 2.134 | +168.8% | +156.3% | +505 |
| 1.1-1.3x | 1st | 222 | 54 | 1.480 | +43.7% | +53.1% | +237 |
| 1.1-1.3x | 2nd | 181 | 47 | 1.660 | +54.1% | +68.5% | +225 |
| 1.3-1.6x | 1st | 114 | 12 | 0.742 | -17.0% | -21.1% | -39 |
| 1.3-1.6x | 2nd | 153 | 19 | 0.883 | -13.9% | -6.5% | -15 |
| 1.6-2.2x | 1st | 57 | 5 | 0.795 | -21.2% | -33.3% | -21 |
| 1.6-2.2x | 2nd | 104 | 7 | 0.613 | -27.2% | -22.1% | -29 |
| 2.2-3.5x | 1st | 18 | 2 | 1.098 | +23.3% | +26.6% | +7 |
| 2.2-3.5x | 2nd | 40 | 3 | 0.748 | -26.8% | -40.6% | -20 |
| 3.5x+ | 2nd | 6 | 1 | 1.830 | +70.0% | +70.1% | +4 |
| no Betfair pre-play price | 1st | 6 | 1 | 1.355 | +66.7% | +186.1% | +26 |
| no Betfair pre-play price | 2nd | 11 | 1 | 0.661 | -9.1% | -57.7% | -11 |
| all bets | 1st | 638 | 149 | 1.437 | +44.7% | +50.9% | +649 |
| all bets | 2nd | 645 | 135 | 1.436 | +45.6% | +60.3% | +659 |

| guard: no bet when drift is at least | half | bets | winners | A/E | flat ROI | Kelly ROI | units won |
|---|---|---|---|---|---|---|---|
| **1.3x** | **1st** | **449** | **130** | **1.636** | **+69.6%** | **+70.3%** | **+702** |
| **1.3x** | **2nd** | **342** | **105** | **1.857** | **+102.4%** | **+107.1%** | **+719** |
| 1.6x | 1st | 563 | 142 | 1.485 | +52.1% | +55.9% | +663 |
| 1.6x | 2nd | 495 | 124 | 1.589 | +66.4% | +77.7% | +704 |
| 2.2x | 1st | 620 | 147 | 1.443 | +45.3% | +51.4% | +642 |
| 2.2x | 2nd | 599 | 131 | 1.464 | +50.2% | +65.1% | +675 |
| 3.5x | 1st | 638 | 149 | 1.437 | +44.7% | +50.9% | +649 |
| 3.5x | 2nd | 639 | 134 | 1.433 | +45.4% | +60.3% | +655 |
| no guard | 1st | 638 | 149 | 1.437 | +44.7% | +50.9% | +649 |
| no guard | 2nd | 645 | 135 | 1.436 | +45.6% | +60.3% | +659 |

### What it says

**The drift is the biggest thing our model cannot see.** A dog that drifts to 2.2-3.5x its shortest price wins 43% of
what our model expects (A/E 0.426), and 3.5x+ drifters win 26%. Dogs that never drift win 18% more than we expect
(1.179). This is the SP-favourite gap of Test 24 (1.159) seen from the other side. The market's late money is most of
the 0.10 between us and BSP.

**BSP prices the drift:**
- A/E is 0.95-1.01 in every band with real numbers
- 3.5x+ in the first half is 1.355, on about 60 wins

**GRV's SP does not price the drift.** GRV's SP is a bookmaker price that lags the money:
- dogs that drift 2.2-3.5x on Betfair win half what GRV's SP says (0.590 / 0.504)
- 3.5x+ drifters win a quarter to a half of it (0.544 / 0.257)
- dogs that never drift win 7-10% more than it says (1.074 / 1.102)

**The 1.3x rule's profit is all in dogs that did not drift.** Every drift band under 1.3x makes +44% to +169% in both
halves. Every band from 1.3x to 2.2x loses in both halves (-14% to -27%). The rule was backing drifters: GRV's SP
leaves them looking long against our price, and they are long for a reason.

A guard of **no bet once the dog has drifted 1.3x from its shortest price**:
- cuts the bets from about 640 to 450 and 340 a half
- lifts flat ROI from +45% / +46% to **+70% / +102%**, and Kelly ROI from +51% / +60% to +70% / +107%
- makes more units in both halves (+702 and +719, against +649 and +659)

It is the best rule found on the dogs. It is chosen after seeing these numbers, so it needs the walk-forward before
anything is staked on it.

Two cautions:
- The drift here runs to the off, which flatters it. A live guard sees the drift up to the moment of the bet, a minute
  or two before the jump.
- These are still GRV's SP prices, and a live bet takes TAB's or Betfair's price.

The practical rule for the founder's TAB idea follows: take the open per the 1.3x rule, then **do not add to, or
re-take, a dog that drifts 30% from its shortest price before the jump**. The opens history will say what a bet at the
open does on dogs that later drift.

## Test 26: the lead model (5 Nov 2026, gh topaz run 41957830188, `topaz_round14.py`)

The founder, on Lemonade Lass: "Was it always going to lead". Test 21 found the dog that leads at the first point wins
52.7%, while the fastest early dog on our past splits leads only 30.3%.

The lead model:
- uses the same LightGBM race softmax and the same pre-race inputs as the win model
- uses the label "led at the first point", from GRV's in-running, on races with exactly one leader (93% of races)
- was fitted on 73,338 races to 5 Dec 2023, early-stopped to 5 June 2024 (300 rounds), and scored after

On the scored quarter's 22,443 one-leader races its log loss is **1.5404**, against 1.9362 for an equal chance each.

| rule | its pick leads | its pick wins |
|---|---|---|
| **the lead model's top pick** | **39.8%** of 22,443 races | **28.3%** |
| fastest early on past splits | 31.2% of 22,436 races | 20.5% |
| led most often (last 10) | 32.3% of 18,155 races | 20.8% |

It is calibrated (actual leads against its expected, by its own chance):

| lead chance | runners | led | lead model expected | won | win % |
|---|---|---|---|---|---|
| 0%-10% | 80,749 | 3,624 | 3,663 | 6,569 | 8.1% |
| 10%-20% | 36,982 | 5,646 | 5,317 | 5,907 | 16.0% |
| 20%-35% | 24,766 | 6,453 | 6,544 | 5,335 | 21.5% |
| 35%-50% | 9,913 | 4,037 | 4,102 | 2,922 | 29.5% |
| 50%-70% | 4,179 | 2,284 | 2,404 | 1,438 | 34.4% |
| 70%-100% | 546 | 399 | 412 | 272 | 49.8% |

Then the win model with the lead chance as an input. The training rows get it out of fold, from lead models fitted on
the other two date blocks (409, 296 and 186 rounds); the early-stopping and scored rows get it from the full fit. That
is the same standard split, the 22,769 scored races with BSP, where BSP's log loss is 1.4838.

| row | inputs | rounds | early-stopping log loss | scored log loss | gap to BSP | 1st half | 2nd half |
|---|---|---|---|---|---|---|---|
| G0 F2 (D1 + preview + tips) | 186 | 2,626 | 1.5996 | 1.5901 | +0.1063 | +0.0992 | +0.1127 |
| **G1 + the lead chance** | 189 | 4,716 | 1.5978 | 1.5882 | **+0.1044** | **+0.0969** | **+0.1110** |
| G2 G1 + the trainer's runners | 192 | 3,707 | 1.5986 | 1.5889 | +0.1051 | +0.0980 | +0.1115 |

The new inputs' share of the model's splits:
- G1: 6.6% (p_lead relative to the race 4.9%, p_lead 1.3%, lead_rank 0.4%)
- G2: 6.9% (p_lead 3.0%, p_lead relative 3.0%, lead_rank 0.9%; trainer_runners, trainer_rank and stable_elect 0.0% each)

| dogs (scored quarter, races with BSP) | runners | wins | win % | A/E vs G0 | A/E vs G1 | A/E vs G2 | A/E vs BSP | A/E vs GRV's SP |
|---|---|---|---|---|---|---|---|---|
| lead chance 50%+ | 4,727 | 1,715 | 36.3% | 0.988 | 0.987 | 0.987 | 0.979 | 1.073 |
| lead chance 35-50% | 10,029 | 2,951 | 29.4% | 1.036 | 1.032 | 1.031 | 1.017 | 1.101 |
| lead chance 20-35% | 25,090 | 5,400 | 21.5% | 0.998 | 0.996 | 0.996 | 0.979 | 1.035 |
| lead chance under 20% | 120,385 | 12,703 | 10.6% | 0.995 | 0.996 | 0.996 | 1.008 | 0.957 |
| lead model's top pick, box 1 | 5,352 | 1,618 | 30.2% | 1.002 | 1.002 | 1.003 | 0.998 | 1.068 |
| lead model's top pick, boxes 2-8 | 17,381 | 4,812 | 27.7% | 1.023 | 1.020 | 1.019 | 1.001 | 1.085 |
| trainer's second runner or lower | 9,695 | 957 | 9.9% | 0.955 | 0.958 | 0.972 | 0.996 | 0.940 |
| the stable's elect | 8,799 | 1,412 | 16.0% | 0.979 | 0.982 | 0.992 | 1.001 | 1.009 |

**The lead model picks the leader 39.8% of the time**, against 31.2% for the fastest early dog: right 28% more often,
in 8.6 more races in every hundred. Its top pick wins 28.3% against 20.5%. Its chances are honest: a dog it gives
50-70% leads 55%, one it gives 70%+ leads 73%.

**Feeding it in moves the win model 0.0019 closer to BSP** (+0.1063 to +0.1044), and **both halves improve**
(by 0.0023 and 0.0017). This is the largest single gain since the ratings upgrades of Test 16; the last five ideas were
worth 0.001 or less. The model leans on it, with 6.6% of its splits, the most any new input has taken since GRV's tips.
Run-to-run noise on this split is about 0.0015, so the walk-forward decides.

The trainer's runners add nothing (0.0% of splits; G2 is +0.1051, worse than G1). They do narrow the second runner's
over-pricing from A/E 0.955 to 0.972.

The market already prices the likely leader:
- BSP's A/E is 0.979-1.017 in every lead band
- our models' A/E is 0.987-1.036 in every lead band
- GRV's SP under-rates the likely leaders by 7-10% (1.073 and 1.101), which is part of why the 1.3x rule earns
  against it

**What goes forward:** the lead chance (G1) joins the reliable-beginner inputs (Test 23) for the final walk-forward. If
it holds there, the weekly train fits a lead model beside the win model, and the card prints each dog's chance of
leading.

## Test 27: the final walk-forward, everything that cleared (5 Nov 2026, gh topaz run 41967576028, `topaz_walk.py`)

The founder: "Run the final walk-forward with everything that cleared". The run, against Test 20's set-up:
- carried over: the preview, the ratings upgrades, GRV's tips and 4,000 rounds, refitted every second month on every
  race before that month
- added, three things at once: GRV's own rating (cleared by the 4 Nov compare; worth 0.009 on Test 16's one split, and
  in no walk-forward before this one), the reliable-beginner inputs (Test 23) and the lead chance (Test 26)
- the lead chance is forward-chained: 27 lead fits of 300 rounds, each half-year priced by a lead model that saw only
  earlier races
- the drift guard (Test 25) on the bets, with the drift filled on 100% of BSP runners
- 161 inputs plus 33 within-race relatives
- 18 refits, 221 minutes in all

| month | races | model | ensemble | GRV SP | BSP (races matched) | model gap to SP | gap to BSP |
|---|---|---|---|---|---|---|---|
| 2023-12 | 834 | 1.6251 | 1.6171 | 1.5940 | 1.5184 (754) | +0.0312 | +0.0858 |
| 2024-01 | 835 | 1.6253 | 1.6109 | 1.6075 | 1.4931 (723) | +0.0177 | +0.1077 |
| 2024-02 | 715 | 1.6394 | 1.6353 | 1.5765 | 1.5269 (664) | +0.0629 | +0.1042 |
| 2024-03 | 810 | 1.6235 | 1.6066 | 1.6308 | 1.4925 (683) | -0.0073 | +0.0939 |
| 2024-04 | 809 | 1.6168 | 1.5974 | 1.6111 | 1.4883 (705) | +0.0057 | +0.0898 |
| 2024-05 | 882 | 1.6230 | 1.6080 | 1.6492 | 1.5002 (718) | -0.0263 | +0.0742 |
| 2024-06 | 822 | 1.6664 | 1.6322 | 1.6596 | 1.5126 (640) | +0.0068 | +0.0886 |
| 2024-07 | 881 | 1.6565 | 1.6363 | 1.6876 | 1.5288 (723) | -0.0311 | +0.0771 |
| 2024-08 | 900 | 1.6465 | 1.6120 | 1.6499 | 1.4912 (705) | -0.0034 | +0.0863 |
| 2024-09 | 817 | 1.6448 | 1.6210 | 1.6379 | 1.4997 (697) | +0.0069 | +0.1063 |
| 2024-10 | 950 | 1.6176 | 1.6031 | 1.6172 | 1.4742 (835) | +0.0003 | +0.0999 |
| 2024-11 | 876 | 1.6150 | 1.5971 | 1.6091 | 1.5103 (744) | +0.0059 | +0.0668 |
| 2024-12 | 785 | 1.6669 | 1.6408 | 1.6790 | 1.5480 (616) | -0.0121 | +0.0642 |
| 2025-01 | 928 | 1.6160 | 1.6104 | 1.6159 | 1.4845 (831) | +0.0001 | +0.0928 |
| 2025-02 | 791 | 1.6289 | 1.6167 | 1.5999 | 1.5258 (749) | +0.0289 | +0.0873 |
| 2025-03 | 907 | 1.6267 | 1.6189 | 1.5737 | 1.4971 (842) | +0.0530 | +0.1049 |
| 2025-04 | 872 | 1.6063 | 1.5973 | 1.6231 | 1.4916 (774) | -0.0169 | +0.0794 |
| 2025-05 | 942 | 1.6623 | 1.6480 | 1.6700 | 1.5526 (787) | -0.0077 | +0.0616 |
| 2025-06 | 862 | 1.5797 | 1.5519 | 1.6204 | 1.4665 (747) | -0.0407 | +0.0664 |
| 2025-07 | 922 | 1.6179 | 1.6126 | 1.6292 | 1.5074 (815) | -0.0113 | +0.0770 |
| 2025-08 | 818 | 1.5297 | 1.5103 | 1.5227 | 1.4028 (723) | +0.0069 | +0.0871 |
| 2025-09 | 834 | 1.5931 | 1.5804 | 1.5933 | 1.4865 (721) | -0.0002 | +0.0719 |
| 2025-10 | 960 | 1.6156 | 1.6010 | 1.6347 | 1.4952 (821) | -0.0191 | +0.0852 |
| 2025-11 | 753 | 1.5926 | 1.5722 | 1.5705 | 1.4634 (666) | +0.0222 | +0.0976 |
| 2025-12 | 913 | 1.5789 | 1.5556 | 1.6146 | 1.4557 (786) | -0.0357 | +0.0788 |
| 2026-01 | 913 | 1.6209 | 1.6044 | 1.6056 | 1.4824 (824) | +0.0154 | +0.1088 |
| 2026-02 | 879 | 1.5956 | 1.5886 | 1.5675 | 1.4830 (828) | +0.0280 | +0.0893 |
| 2026-03 | 990 | 1.5736 | 1.5748 | 1.5360 | 1.4493 (963) | +0.0376 | +0.1150 |
| 2026-04 | 871 | 1.5469 | 1.5466 | 1.5089 | 1.4717 (860) | +0.0381 | +0.0752 |
| 2026-05 | 908 | 1.6377 | 1.6261 | 1.6255 | 1.5155 (821) | +0.0122 | +0.0920 |
| 2026-06 | 897 | 1.6204 | 1.6117 | 1.6411 | 1.4978 (814) | -0.0207 | +0.0955 |
| 2026-07 | 957 | 1.5930 | 1.5892 | 1.5671 | 1.4622 (886) | +0.0259 | +0.1125 |
| 2026-08 | 866 | 1.5717 | 1.5731 | 1.5156 | 1.4872 (856) | +0.0561 | +0.0821 |
| 2026-09 | 901 | 1.5289 | 1.5394 | 1.4641 | 1.4283 (900) | +0.0648 | +0.1001 |
| 2026-10 | 892 | 1.5070 | 1.5079 | 1.4322 | 1.4030 (892) | +0.0748 | +0.1040 |
| 2026-11 | 113 | 1.6212 | 1.6397 | 1.5436 | nan (0) | +0.0776 | +nan |

The scored quarter as a whole (25,720 races):
- model 1.6053, ensemble 1.5927, GRV's SP 1.5952
- on the 22,866 BSP-matched races, model 1.5725 against BSP's 1.4838

| walk-forward | gap to BSP |
|---|---|
| Test 14 (frozen inputs, fresh model monthly) | +0.1171 |
| Test 18 (+ preview, ratings upgrades) | +0.0987 |
| Test 20 (+ tips, 4,000 rounds) | +0.0959 |
| **Test 27 (+ GRV's rating, reliable beginners, the lead chance)** | **+0.0888** |

**Closer to BSP than Test 20 in 33 of the same 35 months.** The two exceptions are 2025-02 (+0.0873 against +0.0849)
and 2026-05 (+0.0920 against +0.0905). The 0.0071 gain is the largest of any walk-forward step since the preview and
ratings upgrades.

It belongs to three inputs added together, and this run cannot split it between them. On one split, GRV's rating was
worth 0.009 (Test 16), the lead chance 0.0019 (Test 26) and the reliable beginners 0.001 (Test 23), so GRV's rating
is probably most of it. A walk-forward with GRV's rating alone (`WALK_GRV_RATING=yes` and nothing else new) says how
much the other two add. The ensemble with the winners twin beats GRV's SP over the quarter (1.5927 against 1.5952).

### Bets at GRV's SP, no commission

| month | rule chosen on the 6 months before (bets, ROI there) | bets | winners | A/E | flat ROI | cumulative units |
|---|---|---|---|---|---|---|
| 2024-06 | blend, all, $8-$13, 10% (341, +56%) | 56 | 6 | 1.033 | -8.0% | -4 |
| 2024-07 | blend, one a race, $8-$13, 10% (371, +51%) | 61 | 11 | 1.712 | +81.8% | +45 |
| 2024-08 | blend, one a race, $13-$21, 5% (355, +77%) | 72 | 7 | 1.558 | +44.3% | +77 |
| 2024-09 | blend, one a race, $13-$21, 10% (327, +87%) | 61 | 6 | 1.535 | +44.8% | +105 |
| 2024-10 | blend, one a race, $13-$21, 10% (336, +85%) | 65 | 1 | 0.248 | -76.9% | +55 |
| 2024-11 | blend, one a race, $13-$21, 10% (353, +61%) | 64 | 4 | 0.981 | -7.3% | +50 |
| 2024-12 | blend, one a race, $13-$21, 10% (305, +50%) | 35 | 0 | 0.000 | -100.0% | +15 |
| 2025-01 | blend, all, $8-$13, 20% (327, +51%) | 72 | 11 | 1.459 | +38.2% | +42 |
| 2025-02 | ensemble, one a race, $8-$13, 50% (798, +48%) | 118 | 17 | 1.452 | +43.6% | +94 |
| 2025-03 | blend, all, $1.5-$21, 30% (486, +63%) | 64 | 13 | 1.152 | +33.0% | +115 |
| 2025-04 | blend, all, $1.5-$21, 30% (331, +69%) | 66 | 24 | 2.077 | +112.0% | +189 |
| 2025-05 | blend, all, $1.5-$21, 30% (374, +91%) | 58 | 15 | 1.512 | +95.7% | +244 |
| 2025-06 | blend, all, $1.5-$21, 30% (421, +82%) | 85 | 27 | 1.959 | +101.4% | +331 |
| 2025-07 | blend, all, $1.5-$21, 30% (534, +81%) | 77 | 24 | 1.826 | +65.6% | +381 |
| 2025-08 | blend, all, $8-$13, 20% (315, +99%) | 40 | 10 | 2.431 | +146.5% | +440 |
| 2025-09 | blend, all, $8-$13, 20% (306, +104%) | 40 | 5 | 1.229 | +12.5% | +445 |
| 2025-10 | blend, one a race, $8-$13, 20% (366, +91%) | 66 | 10 | 1.465 | +43.8% | +474 |
| 2025-11 | blend, one a race, $8-$13, 20% (367, +85%) | 43 | 10 | 2.300 | +126.7% | +528 |
| 2025-12 | blend, one a race, $8-$13, 20% (301, +95%) | 71 | 14 | 1.899 | +86.6% | +590 |
| 2026-01 | blend, one a race, $8-$13, 20% (314, +96%) | 67 | 8 | 1.170 | +16.9% | +601 |
| 2026-02 | blend, one a race, $1.5-$21, 30% (522, +80%) | 95 | 26 | 1.795 | +95.4% | +691 |
| 2026-03 | blend, one a race, $1.5-$21, 30% (493, +86%) | 98 | 26 | 1.489 | +40.4% | +731 |
| 2026-04 | blend, one a race, $1.5-$21, 30% (381, +89%) | 57 | 7 | 0.944 | -1.6% | +730 |
| 2026-05 | blend, one a race, $1.5-$21, 20% (551, +67%) | 104 | 26 | 1.582 | +58.7% | +791 |
| 2026-06 | blend, one a race, $1.5-$21, 20% (652, +60%) | 128 | 41 | 1.649 | +98.2% | +917 |
| 2026-07 | blend, one a race, $1.5-$21, 20% (581, +68%) | 99 | 14 | 0.847 | -33.3% | +884 |
| 2026-08 | blend, one a race, $1.5-$21, 20% (547, +52%) | 77 | 11 | 1.009 | -27.0% | +863 |
| 2026-09 | blend, one a race, $1.5-$21, 20% (416, +44%) | 54 | 11 | 1.410 | +58.1% | +894 |
| 2026-10 | blend, all, $1.5-$21, 20% (329, +47%) | 29 | 5 | 1.204 | +1.7% | +895 |
| 2026-11 | blend, one a race, $8-$13, 2% (402, +32%) | 8 | 1 | 1.172 | +25.0% | +897 |

**Sequential rule**
- 1st half: 1,014 bets, A/E 1.536, flat ROI +43.2%, bank x7.65 at 0.5% a bet, worst drawdown 41%, longest losing run 58
- 2nd half: 1,016 bets, A/E 1.435, flat ROI +45.2%, bank x8.65 at 0.5% a bet, worst drawdown 27%, longest losing run 25
- all: 2,030 bets, A/E 1.480, flat ROI +44.2%, bank x66.13 at 0.5% a bet, worst drawdown 41%, longest losing run 58
- months in profit 23 of 30; last 6: 2026-06 +98% (128), 2026-07 -33% (99), 2026-08 -27% (77), 2026-09 +58% (54), 2026-10 +2% (29), 2026-11 +25% (8)

**Test 12 rule: all, $8-$13, 50%**
- 1st half: 1,927 bets, A/E 1.454, flat ROI +43.9%, bank x51.03 at 0.5% a bet, worst drawdown 22%, longest losing run 41
- 2nd half: 1,933 bets, A/E 1.246, flat ROI +23.7%, bank x7.59 at 0.5% a bet, worst drawdown 42%, longest losing run 51
- all: 3,860 bets, A/E 1.351, flat ROI +33.8%, bank x387.15 at 0.5% a bet, worst drawdown 42%, longest losing run 51
- months in profit 27 of 30; last 6: 2026-06 +63% (129), 2026-07 +65% (155), 2026-08 +8% (123), 2026-09 -17% (136), 2026-10 -33% (146), 2026-11 +12% (18)

**Test 13 rule: one a race, $5-$8, 50%**
- 1st half: 1,002 bets, A/E 1.351, flat ROI +34.6%, bank x5.20 at 0.5% a bet, worst drawdown 14%, longest losing run 23
- 2nd half: 1,004 bets, A/E 1.162, flat ROI +14.3%, bank x1.91 at 0.5% a bet, worst drawdown 27%, longest losing run 25
- all: 2,006 bets, A/E 1.256, flat ROI +24.5%, bank x9.92 at 0.5% a bet, worst drawdown 27%, longest losing run 25
- months in profit 25 of 30; last 6: 2026-06 +40% (81), 2026-07 -25% (61), 2026-08 -5% (71), 2026-09 -11% (84), 2026-10 -35% (79), 2026-11 +28% (12)

### Bets at BSP, 8% commission on winnings

| month | rule chosen on the 6 months before (bets, ROI there) | bets | winners | A/E | flat ROI | cumulative units |
|---|---|---|---|---|---|---|
| 2024-06 | blend, one a race, $5-$8, 20% (386, +9%) | 53 | 9 | 1.073 | -0.4% | -0 |
| 2024-07 | ensemble, all, $8-$13, 50% (876, +9%) | 168 | 19 | 1.173 | +12.6% | +21 |
| 2024-08 | ensemble, all, $8-$13, 50% (913, +10%) | 161 | 18 | 1.154 | +7.1% | +32 |
| 2024-09 | blend, all, $1.5-$21, 50% (333, +27%) | 45 | 5 | 1.558 | +53.2% | +56 |
| 2024-10 | blend, one a race, $1.5-$21, 50% (306, +45%) | 57 | 3 | 0.737 | -42.3% | +32 |
| 2024-11 | blend, all, $1.5-$21, 50% (330, +40%) | 80 | 6 | 1.008 | -4.8% | +28 |
| 2024-12 | blend, one a race, $8-$13, 30% (400, +31%) | 48 | 3 | 0.665 | -41.1% | +9 |
| 2025-01 | blend, one a race, $8-$13, 30% (398, +21%) | 57 | 5 | 0.883 | -17.0% | -1 |
| 2025-02 | blend, one a race, $3-$5, 10% (439, +11%) | 98 | 16 | 0.654 | -37.8% | -38 |
| 2025-03 | blend, one a race, $8-$13, 30% (383, +10%) | 71 | 10 | 1.452 | +41.9% | -8 |
| 2025-04 | blend, one a race, $8-$13, 30% (397, +20%) | 79 | 6 | 0.784 | -29.3% | -32 |
| 2025-05 | blend, one a race, $8-$13, 30% (407, +16%) | 67 | 12 | 1.855 | +70.7% | +16 |
| 2025-06 | blend, one a race, $8-$13, 30% (379, +13%) | 57 | 4 | 0.723 | -33.2% | -3 |
| 2025-07 | blend, one a race, $8-$13, 30% (388, +13%) | 76 | 9 | 1.240 | +17.0% | +10 |
| 2025-08 | blend, one a race, $8-$13, 30% (407, +18%) | 63 | 11 | 1.759 | +66.5% | +52 |
| 2025-09 | blend, one a race, $8-$13, 30% (413, +22%) | 50 | 1 | 0.208 | -80.5% | +11 |
| 2025-10 | blend, all, $1.5-$3, 2% (347, +12%) | 70 | 28 | 0.951 | -7.8% | +6 |
| 2025-11 | blend, all, $1.5-$21, 50% (323, +15%) | 34 | 5 | 1.888 | +69.9% | +30 |
| 2025-12 | blend, all, $1.5-$21, 50% (301, +22%) | 51 | 5 | 1.257 | +15.4% | +38 |
| 2026-01 | ensemble, all, $1.5-$3, 5% (549, +4%) | 105 | 39 | 0.858 | -19.4% | +17 |
| 2026-02 | model, one a race, $8-$13, 10% (1,866, +2%) | 296 | 28 | 0.969 | -9.1% | -10 |
| 2026-03 | blend, one a race, $1.5-$21, 50% (311, +4%) | 80 | 3 | 0.454 | -52.4% | -52 |
| 2026-04 | ensemble, one a race, $8-$13, 10% (1,903, +1%) | 307 | 35 | 1.158 | +9.4% | -23 |
| 2026-05 | ensemble, all, $3-$5, 20% (788, +2%) | 134 | 31 | 0.916 | -15.1% | -43 |
| 2026-06 | blend, one a race, $8-$13, 30% (486, +6%) | 81 | 14 | 1.777 | +58.2% | +4 |
| 2026-07 | blend, one a race, $8-$13, 30% (492, +20%) | 108 | 8 | 0.768 | -33.1% | -32 |
| 2026-08 | blend, one a race, $8-$13, 30% (531, +15%) | 94 | 8 | 0.894 | -14.2% | -45 |
| 2026-09 | blend, one a race, $8-$13, 30% (558, +8%) | 101 | 5 | 0.500 | -57.7% | -103 |
| 2026-10 | model, all, $8-$13, 50% (1,017, +9%) | 178 | 16 | 0.896 | -14.2% | -128 |

**Sequential rule**
- 1st half: 1,432 bets, A/E 1.013, flat ROI +1.9%, bank x0.99 at 0.5% a bet, worst drawdown 43%, longest losing run 49
- 2nd half: 1,437 bets, A/E 0.947, flat ROI -10.9%, bank x0.40 at 0.5% a bet, worst drawdown 63%, longest losing run 60
- all: 2,869 bets, A/E 0.981, flat ROI -4.5%, bank x0.40 at 0.5% a bet, worst drawdown 69%, longest losing run 60
- months in profit 11 of 29; last 6: 2026-05 -15% (134), 2026-06 +58% (81), 2026-07 -33% (108), 2026-08 -14% (94), 2026-09 -58% (101), 2026-10 -14% (178)

**Test 12 rule: all, $8-$13, 50%**
- 1st half: 2,118 bets, A/E 1.126, flat ROI +4.5%, bank x1.27 at 0.5% a bet, worst drawdown 42%, longest losing run 49
- 2nd half: 2,132 bets, A/E 1.029, flat ROI -3.8%, bank x0.54 at 0.5% a bet, worst drawdown 62%, longest losing run 53
- all: 4,250 bets, A/E 1.077, flat ROI +0.4%, bank x0.68 at 0.5% a bet, worst drawdown 70%, longest losing run 53
- months in profit 14 of 29; last 6: 2026-05 +49% (179), 2026-06 +29% (160), 2026-07 -44% (183), 2026-08 +36% (163), 2026-09 -14% (174), 2026-10 -14% (178)

**Test 13 rule: one a race, $5-$8, 50%**
- 1st half: 941 bets, A/E 0.919, flat ROI -13.4%, bank x0.50 at 0.5% a bet, worst drawdown 57%, longest losing run 50
- 2nd half: 941 bets, A/E 0.934, flat ROI -13.1%, bank x0.51 at 0.5% a bet, worst drawdown 57%, longest losing run 26
- all: 1,882 bets, A/E 0.926, flat ROI -13.3%, bank x0.26 at 0.5% a bet, worst drawdown 77%, longest losing run 50
- months in profit 10 of 29; last 6: 2026-05 -0% (81), 2026-06 +8% (74), 2026-07 +9% (66), 2026-08 -51% (75), 2026-09 +9% (80), 2026-10 -53% (95)

### The 1.3x rule, month by month (our price $2-$15, Kelly x75 cap 4, the blend refitted each month on the six before)

At GRV's SP, no commission. Blend weights refitted each month: ours 0.38 to 0.64, the SP 0.55 to 0.77.

| rule | half | bets | winners | A/E | flat ROI | units staked | Kelly ROI | units won | worst drawdown (units) | months in profit |
|---|---|---|---|---|---|---|---|---|---|---|
| no guard | 1st | 1,147 | 262 | 1.454 | +50.5% | 2,317 | +59.1% | +1,368 | 51 | 13 of 13 |
| no guard | 2nd | 1,149 | 281 | 1.629 | +66.3% | 2,096 | +81.7% | +1,712 | 49 | 14 of 16 |
| no guard | all | 2,296 | 543 | 1.539 | +58.4% | 4,413 | +69.8% | +3,080 | 51 | 27 of 29 |
| **drift guard 1.3x** | **1st** | **760** | **201** | **1.554** | **+64.5%** | **1,695** | **+71.0%** | **+1,204** | **43** | **13 of 13** |
| **drift guard 1.3x** | **2nd** | **769** | **237** | **1.882** | **+103.5%** | **1,549** | **+112.3%** | **+1,739** | **29** | **14 of 17** |
| drift guard 1.3x | all | 1,529 | 438 | 1.716 | +84.1% | 3,244 | +90.7% | +2,943 | 43 | 26 of 29 |

(A month split by the halves' dividing date counts in both halves.)

At BSP, 8% commission: the blend weights refitted each month are ours -0.10 to 0.08 and BSP 0.94 to 1.08. The rule
finds 5 bets in 29 months, and none with the guard.

### What it says

**Everything together moved the model 0.0071 closer to BSP**, to +0.0888, and it was closer than Test 20 in 33 of 35
months. GRV's rating is probably most of that; the ablation run will say.

**The 1.3x rule holds when every month's model and blend are fitted only on the past.** Without the guard:
- +50.5% and +66.3% flat, and +59.1% and +81.7% on Kelly
- 2,296 bets, +3,080 units
- 27 of 29 months in profit

**The drift guard holds up out of sample** and is the best rule on the dogs:
- +64.5% and +103.5% flat, and +71.0% and +112.3% on Kelly
- 1,529 bets, +2,943 units
- a worst drawdown of 43 and 29 units
- 26 of 29 months in profit
- a third fewer bets for nearly the same units, so each unit staked works harder and the drawdowns are smaller

Both caveats stand:
- **The prices are GRV's SP**, a bookmaker price with a 19% margin, not TAB's open.
- **The drift runs to the off.** A live bet sees the drift only up to the moment it is struck.

At Betfair's price the model still adds nothing: the sequential rule and Tests 12 and 13 all lose or break even at
BSP after commission, and the 1.3x rule finds no bets there. The gap to BSP is smaller, but there is still a gap.

**What goes into production:** the reliable-beginner inputs and the lead chance join the weekly train (the lead model
fitted and saved beside the win model), and the card prints each dog's chance of leading. The TAB opens are the test
that remains.

## Test 28: the ablation, GRV's rating alone (5 Nov 2026, gh topaz run 41992943091, `topaz_walk.py`)

Test 27 added three inputs to the walk-forward at once. This run takes the same set-up, with the same months and the
same refits, and adds only GRV's rating, without the reliable beginners or the lead chance: 155 inputs plus 30
relatives. The drift guard is still on for the bets.

| month | races | model | ensemble | GRV SP | BSP (races matched) | model gap to SP | gap to BSP |
|---|---|---|---|---|---|---|---|
| 2023-12 | 834 | 1.6260 | 1.6193 | 1.5940 | 1.5184 (754) | +0.0320 | +0.0866 |
| 2024-01 | 835 | 1.6233 | 1.6133 | 1.6075 | 1.4931 (723) | +0.0158 | +0.1059 |
| 2024-02 | 715 | 1.6408 | 1.6403 | 1.5765 | 1.5269 (664) | +0.0643 | +0.1061 |
| 2024-03 | 810 | 1.6242 | 1.6078 | 1.6308 | 1.4925 (683) | -0.0067 | +0.0957 |
| 2024-04 | 809 | 1.6154 | 1.5966 | 1.6111 | 1.4883 (705) | +0.0042 | +0.0889 |
| 2024-05 | 882 | 1.6222 | 1.6092 | 1.6492 | 1.5002 (718) | -0.0270 | +0.0773 |
| 2024-06 | 822 | 1.6653 | 1.6364 | 1.6596 | 1.5126 (640) | +0.0057 | +0.0861 |
| 2024-07 | 881 | 1.6581 | 1.6359 | 1.6876 | 1.5288 (723) | -0.0295 | +0.0790 |
| 2024-08 | 900 | 1.6477 | 1.6153 | 1.6499 | 1.4912 (705) | -0.0022 | +0.0883 |
| 2024-09 | 817 | 1.6400 | 1.6223 | 1.6379 | 1.4997 (697) | +0.0022 | +0.1018 |
| 2024-10 | 950 | 1.6152 | 1.5983 | 1.6172 | 1.4742 (835) | -0.0020 | +0.0985 |
| 2024-11 | 876 | 1.6156 | 1.5962 | 1.6091 | 1.5103 (744) | +0.0066 | +0.0683 |
| 2024-12 | 785 | 1.6689 | 1.6473 | 1.6790 | 1.5480 (616) | -0.0101 | +0.0658 |
| 2025-01 | 928 | 1.6155 | 1.6083 | 1.6159 | 1.4845 (831) | -0.0004 | +0.0935 |
| 2025-02 | 791 | 1.6273 | 1.6159 | 1.5999 | 1.5258 (749) | +0.0274 | +0.0853 |
| 2025-03 | 907 | 1.6284 | 1.6204 | 1.5737 | 1.4971 (842) | +0.0547 | +0.1079 |
| 2025-04 | 872 | 1.6058 | 1.5981 | 1.6231 | 1.4916 (774) | -0.0173 | +0.0814 |
| 2025-05 | 942 | 1.6614 | 1.6445 | 1.6700 | 1.5526 (787) | -0.0086 | +0.0620 |
| 2025-06 | 862 | 1.5840 | 1.5573 | 1.6204 | 1.4665 (747) | -0.0364 | +0.0715 |
| 2025-07 | 922 | 1.6174 | 1.6130 | 1.6292 | 1.5074 (815) | -0.0118 | +0.0756 |
| 2025-08 | 818 | 1.5345 | 1.5146 | 1.5227 | 1.4028 (723) | +0.0117 | +0.0919 |
| 2025-09 | 834 | 1.5928 | 1.5829 | 1.5933 | 1.4865 (721) | -0.0005 | +0.0712 |
| 2025-10 | 960 | 1.6162 | 1.5997 | 1.6347 | 1.4952 (821) | -0.0185 | +0.0855 |
| 2025-11 | 753 | 1.5905 | 1.5688 | 1.5705 | 1.4634 (666) | +0.0200 | +0.0947 |
| 2025-12 | 913 | 1.5805 | 1.5535 | 1.6146 | 1.4557 (786) | -0.0341 | +0.0806 |
| 2026-01 | 913 | 1.6203 | 1.6031 | 1.6056 | 1.4824 (824) | +0.0148 | +0.1080 |
| 2026-02 | 879 | 1.5996 | 1.5935 | 1.5675 | 1.4830 (828) | +0.0321 | +0.0932 |
| 2026-03 | 990 | 1.5758 | 1.5749 | 1.5360 | 1.4493 (963) | +0.0398 | +0.1166 |
| 2026-04 | 871 | 1.5454 | 1.5446 | 1.5089 | 1.4717 (860) | +0.0365 | +0.0743 |
| 2026-05 | 908 | 1.6343 | 1.6231 | 1.6255 | 1.5155 (821) | +0.0088 | +0.0869 |
| 2026-06 | 897 | 1.6182 | 1.6056 | 1.6411 | 1.4978 (814) | -0.0229 | +0.0941 |
| 2026-07 | 957 | 1.5954 | 1.5874 | 1.5671 | 1.4622 (886) | +0.0283 | +0.1137 |
| 2026-08 | 866 | 1.5752 | 1.5739 | 1.5156 | 1.4872 (856) | +0.0595 | +0.0857 |
| 2026-09 | 901 | 1.5276 | 1.5331 | 1.4641 | 1.4283 (900) | +0.0635 | +0.0986 |
| 2026-10 | 892 | 1.5066 | 1.5042 | 1.4322 | 1.4030 (892) | +0.0745 | +0.1036 |
| 2026-11 | 113 | 1.6230 | 1.6378 | 1.5436 | nan (0) | +0.0793 | +nan |

| walk-forward | gap to BSP |
|---|---|
| Test 20 (no GRV rating) | +0.0959 |
| **Test 28 (+ GRV's rating)** | **+0.0891** |
| Test 27 (+ GRV's rating, reliable beginners, the lead chance) | +0.0888 |

The scored quarter as a whole (25,720 races): model 1.6056, ensemble 1.5924, GRV's SP 1.5952. On the 22,866
BSP-matched races, model 1.5729 against BSP's 1.4838.

**GRV's rating is 0.0068 of Test 27's 0.0071.** The reliable beginners and the lead chance add 0.0003 on top:
- Test 27 is closer to BSP than Test 28 in 20 of the 35 months
- by 0.0004 a month on average

That is noise-sized. The lead model's 0.0019 on one split (Test 26) mostly does not survive the walk-forward, where GRV's
rating already carries much of what it knew. GRV's rating is GRV's own pre-race view of the dog, and a dog that leads is
part of what it rates.

The bets, the same rules on both runs:

| rule | Test 28 (GRV's rating) | Test 27 (+ reliable + lead) |
|---|---|---|
| 1.3x rule at GRV's SP, no guard | 2,257 bets, +59.0% flat, Kelly +63.3%, **+2,764** units, 25 of 29 months | 2,296 bets, +58.4% flat, Kelly +69.8%, **+3,080** units, 27 of 29 months |
| 1.3x rule at GRV's SP, drift guard | 1,494 bets, +82.3% flat, Kelly +82.2%, **+2,639** units, 25 of 29 months | 1,529 bets, +84.1% flat, Kelly +90.7%, **+2,943** units, 26 of 29 months |
| Sequential rule at GRV's SP | 2,126 bets, +41.9% flat, 24 of 30 months | 2,030 bets, +44.2% flat, 23 of 30 months |
| Test 12 rule at GRV's SP | 3,826 bets, +32.8% flat, 23 of 30 months | 3,860 bets, +33.8% flat, 27 of 30 months |
| Test 13 rule at GRV's SP | 1,998 bets, +20.4% flat, 25 of 30 months | 2,006 bets, +24.5% flat, 25 of 30 months |
| Sequential rule at BSP | 3,517 bets, -3.2% flat | 2,869 bets, -4.5% flat |
| 1.3x rule at BSP | 5 bets | 5 bets |

The 1.3x rule at GRV's SP in Test 28, by half (blend weights ours 0.38 to 0.64, SP 0.55 to 0.77):

| rule | half | bets | winners | A/E | flat ROI | units staked | Kelly ROI | units won | worst drawdown (units) | months in profit |
|---|---|---|---|---|---|---|---|---|---|---|
| no guard | 1st | 1,125 | 253 | 1.437 | +50.7% | 2,272 | +51.8% | +1,178 | 58 | 12 of 13 |
| no guard | 2nd | 1,132 | 278 | 1.615 | +67.2% | 2,096 | +75.7% | +1,587 | 44 | 14 of 17 |
| no guard | all | 2,257 | 531 | 1.525 | +59.0% | 4,368 | +63.3% | +2,764 | 58 | 25 of 29 |
| drift guard 1.3x | 1st | 747 | 194 | 1.534 | +63.3% | 1,677 | +64.0% | +1,074 | 53 | 12 of 13 |
| drift guard 1.3x | 2nd | 747 | 228 | 1.830 | +101.4% | 1,535 | +102.0% | +1,565 | 32 | 14 of 17 |
| drift guard 1.3x | all | 1,494 | 422 | 1.681 | +82.3% | 3,212 | +82.2% | +2,639 | 53 | 25 of 29 |

The other Test 28 summaries:

| rule | 1st half | 2nd half | all |
|---|---|---|---|
| Sequential, GRV's SP | 1,062 bets, A/E 1.392, +39.4% | 1,064, 1.435, +44.4% | 2,126, 1.417, +41.9% (worst drawdown 36%) |
| Test 12 rule, GRV's SP | 1,911, 1.384, +37.5% | 1,915, 1.292, +28.0% | 3,826, 1.338, +32.8% |
| Test 13 rule, GRV's SP | 998, 1.284, +28.0% | 1,000, 1.144, +12.8% | 1,998, 1.214, +20.4% |
| Sequential, BSP | 1,756, 0.967, -9.2% | 1,761, 1.122, +2.9% | 3,517, 1.034, -3.2% |
| Test 12 rule, BSP | 2,098, 1.183, +10.4% | 2,103, 1.041, -2.8% | 4,201, 1.112, +3.8% |
| Test 13 rule, BSP | 921, 0.952, -10.2% | 928, 0.938, -11.6% | 1,849, 0.945, -10.9% |

**The log loss barely moves, but the betting does.** With the lead chance and the reliable beginners:
- the 1.3x rule's Kelly ROI rises by 6.5 points (no guard) and 8.5 points (drift guard)
- it makes about 300 more units either way
- it has two more months in profit without the guard (27 against 25)
- the Test 12 and 13 rules and the sequential rule also earn a little more at GRV's SP

The gain lands where the rule bets, among dogs the blend and the SP disagree on. One walk-forward on one set of months
cannot prove that, but every rule at GRV's SP points the same way, and none points the other.

**Decision:** GRV's rating is already in the weekly train (`WALK_GRV_RATING=yes`). The reliable beginners and the lead
chance go in too, on the betting evidence. The lead model is fitted in the weekly train and saved beside the win model,
so the nightly price run loads it rather than fitting 27 lead models a night.

## Test 29: sharpen the price, and the place market (6 Nov 2026, gh topaz run 42139071416, `topaz_round15.py`)

**Set-up.**
- The production inputs, the weekly train's:
  - 161 inputs with GRV's rating, the reliable beginners and the lead chance
  - the lead chance forward-chained by half-year, 27 lead fits
- The standard split: early stopping took 2,878 rounds, and the last quarter is scored.
- Scored: 22,747 races with BSP; BSP's log loss on them is 1.4839.

### Part A: is the model too flat?

Test 24 found the SP favourite wins 16% more than our model says. If the whole price were too flat (favourites too
long, outsiders too short), a power on the race softmax would fix it: p ~ p_model ^ a, with a > 1 sharpening. The
power was chosen on the early-stopping months, from 0.80 to 1.60 in steps of 0.02.

The early-stopping months chose a = **1.02**. Their log loss was 1.5955 at 1.00 and 1.5953 at 1.02.

| price | log loss | gap to BSP | 1st half | 2nd half | SP favourite A/E |
|---|---|---|---|---|---|
| the model as fitted | 1.5816 | +0.0977 | +0.0907 | +0.1039 | 1.149 |
| sharpened, power 1.02 | 1.5814 | +0.0975 | +0.0905 | +0.1037 | 1.136 |

**The model is not too flat.** Sharpening gains 0.0002 and brings the favourite's A/E from 1.149 to 1.136. A power big
enough to close the favourite's gap would cost more on every other dog than it gains on the favourite, which is why the
early-stopping months stopped at 1.02. The favourite is a bias of its own, not a scale on the whole price.
**Decision:** no change to production.

### Part B: the place market

Betfair's place result sets each race's places: 2 in 61% of the 22,492 scored races with a place BSP on every runner,
3 in the rest. The three place chances compared:
- **ours**: Harville's, from our win chances
- **the market's**: 1 / place BSP, rescaled so the race adds to the places paid
- **the blend**: a logit blend of the two, fitted on the early-stopping months

The fitted blend is logit(blend) = **-0.02** x ours + **1.03** x market + 0.01.

| place chance | binary log loss | 1st half | 2nd half | A/E |
|---|---|---|---|---|
| ours (Harville from our win chances) | 0.5608 | 0.5618 | 0.5598 | 1.000 |
| place BSP | 0.5290 | 0.5304 | 0.5276 | 1.000 |
| the blend | 0.5288 | 0.5303 | 0.5274 | 1.000 |

| our place price | runners | placed | A/E vs ours | A/E vs place BSP |
|---|---|---|---|---|
| $1-$1.5 | 18,367 | 12,584 | 0.869 | 0.994 |
| $1.5-$2 | 20,974 | 11,093 | 0.916 | 0.999 |
| $2-$3 | 30,071 | 12,446 | 1.005 | 1.003 |
| $3-$5 | 33,215 | 9,790 | 1.117 | 1.003 |
| $5-$10 | 30,689 | 5,871 | 1.282 | 1.009 |
| $10-$1000 | 25,174 | 2,029 | 1.357 | 0.984 |

**Our place price adds nothing to place BSP.**
- Place BSP beats ours in both halves.
- The blend's weight on ours is nil (-0.02).
- Ours shows Harville's known bias:
  - our shortest dogs placed 13% less often than ours said
  - dogs over $10 placed 36% more often
- Place BSP is within 2% of the truth in every band.

Harville gives a favourite too much chance of filling second and third. Changing that would be a better place
formula, not a better model, and against place BSP there is no room for it.

The value rule at place BSP (8% commission, our place price $1.20-$10, Kelly x75 on halfway between the blend and the
market, cap 4):

| rule | half | bets | placed | flat ROI | units staked | Kelly ROI | units won |
|---|---|---|---|---|---|---|---|
| 1.1x | 1st | 163 | 64 | +41.7% | 530 | +40.6% | +215 |
| 1.1x | 2nd | 327 | 131 | +30.5% | 1,021 | +38.4% | +392 |
| 1.2x | 1st | 102 | 40 | +49.9% | 382 | +50.5% | +193 |
| 1.2x | 2nd | 137 | 59 | +75.5% | 512 | +75.6% | +387 |
| 1.3x | 1st | 83 | 34 | +65.0% | 315 | +64.0% | +202 |
| 1.3x | 2nd | 96 | 43 | +92.0% | 374 | +90.4% | +338 |

**These profits are not a bet anyone can make, and they are not our model's.**
- The blend is the market (weights -0.02 / 1.03 / +0.01), so "place BSP at least 1.3 times the blended price" reads,
  near enough, as "place BSP at least 1.3 times the market's own rescaled price". That happens only in races whose
  place BSPs add up to well under the places paid: the places divided by the sum of 1 / place BSP is at least 1.3, so
  the place book is under about 77% of fair.
- This is inferred from the blend's weights. The run did not print each bet's place book; round 16 measures it.
- The condition reads every runner's final place BSP, which nobody knows until the off.

What it does say is that some Victorian place markets settle under-round at BSP, by enough to have paid +30% to +92% in
both halves. Whether that is any use depends on two things round 16 checks:
- Can it be seen before the off, from the last place price traded?
- Does the money in those markets carry a stake? In a thin market, a backer's own BSP stake pulls the BSP in.

The run logged a divide warning on the Kelly stake. Runners whose stake came out undefined fail the stake test, so they
are in no count above; the cause has not been checked.

**Decision:** nothing from Part B goes to the card. Our model does not price the place market better than place BSP.

## Test 30: the place book (6 Nov 2026, gh topaz runs 42144999948 and 42146524811, `topaz_round16.py`)

Test 29's place rule made its money in races whose place BSPs added up to well under the places paid. This test needs
no model, only Betfair's free files. It takes every race since 2020 with a place BSP on every runner that ran and 2 or
3 places paid:
  place book = (sum over the runners of 1 / place BSP) / places paid      (1 = fair; under 1 = under-round)

### How often the place book settles under-round at BSP

VIC: 95,811 races from 2 Jan 2020, with halves split at 19 Jul 2023 and 2 places paid in 41% of races. The place book
at BSP has a median of 1.007, a 10th percentile of 0.987 and a 90th of 1.030. The win book in the same races has a
median of 1.003.

The table backs every runner at place BSP, with 8% commission:

| place book at BSP | races | share | runners | placed | flat ROI (1st / 2nd) | median place BSP money per race | median win book |
|---|---|---|---|---|---|---|---|
| under 0.77 | 114 | 0.1% | 749 | 337 | +143.2% / +inf | $1,190 | 1.011 |
| 0.77-0.85 | 28 | 0.0% | 197 | 74 | +30.0% / +307.2% | $134 | 0.999 |
| 0.85-0.95 | 537 | 0.6% | 3,846 | 1,349 | +3.4% / +7.8% | $733 | 1.001 |
| 0.95-1.05 | 92,714 | 96.8% | 678,818 | 240,273 | -7.7% / -6.6% | $2,350 | 1.003 |
| 1.05 and over | 2,418 | 2.5% | 17,384 | 6,009 | -15.3% / -10.7% | $694 | 1.006 |

All of Australia gives the same picture: 290,926 races, a median place book of 1.006, and under 0.77 in 362 races
(0.1%).

**Under-round place markets are rare:**
- 0.7% of Victorian races settle under 0.95, and 0.1% under 0.77.
- In 96.8% of races the book is within 5% of fair, and backing the whole field loses 7%.
- The "+inf" means a runner that placed carries an infinite place BSP in Betfair's files, a glitch in the file. A
  glitch like that also drops a race into the under-0.77 band, because 1 / infinity adds nothing to the book. So part
  of that band is bad data, not a real price.

### Do the prices traded before the off know the result?

| place chance from (VIC) | races where every runner traded | binary log loss | the same runners at place BSP | A/E |
|---|---|---|---|---|
| last price traded | 82,948 | 0.5464 | 0.5458 | 1.000 |
| weighted average traded | 82,948 | 0.5471 | 0.5458 | 1.000 |

No. Both score just behind place BSP, which is how a price traded before the jump behaves. A price traded after the
jump would score far below BSP. Greyhound place markets are not turned in-play, so the last price traded is a pre-off
price. All of Australia agrees: 0.5441 and 0.5447 against 0.5435.

The book from the last price traded tracks the book at BSP only loosely (correlation 0.58 in VIC, 0.53 for the
weighted average). But 94% of the VIC races that settled under 0.77 at BSP were already under 0.85 on the last price
traded (91% across Australia).

### The bet anyone could make: back every runner at place BSP when the book before the off is under a cap

The selection reads only prices traded before the off. The bet is struck at BSP, which nobody needs to know in
advance. Commission is 8%.

VIC, book on the last price traded:

| under | half | races | bets | placed | flat ROI | median place BSP money per race |
|---|---|---|---|---|---|---|
| 0.80 | 1st | 44 | 280 | 131 | +51.5% | $3,897 |
| 0.80 | 2nd | 39 | 258 | 115 | +50.3% | $897 |
| 0.85 | 1st | 49 | 316 | 145 | +46.9% | $3,924 |
| 0.85 | 2nd | 49 | 332 | 141 | +45.2% | $758 |
| 0.90 | 1st | 82 | 540 | 225 | +21.9% | $3,412 |
| 0.90 | 2nd | 87 | 615 | 244 | +22.6% | $461 |
| 0.95 | 1st | 555 | 3,901 | 1,390 | -1.5% | $1,161 |
| 0.95 | 2nd | 431 | 3,093 | 1,107 | +1.6% | $503 |

VIC, book on the weighted average traded:

| under | half | races | bets | placed | flat ROI | median place BSP money per race |
|---|---|---|---|---|---|---|
| 0.80 | 1st | 51 | 328 | 148 | +42.1% | $3,623 |
| 0.80 | 2nd | 33 | 212 | 99 | +62.3% | $1,098 |
| 0.85 | 1st | 54 | 346 | 156 | +39.2% | $3,616 |
| 0.85 | 2nd | 38 | 249 | 112 | +54.7% | $947 |
| 0.90 | 1st | 68 | 451 | 194 | +33.2% | $3,706 |
| 0.90 | 2nd | 51 | 345 | 146 | +39.0% | $866 |
| 0.95 | 1st | 293 | 2,078 | 763 | +1.4% | $4,607 |
| 0.95 | 2nd | 316 | 2,281 | 837 | +0.8% | $1,308 |

All of Australia, book on the last price traded:

| under | half | races | bets | placed | flat ROI | median place BSP money per race |
|---|---|---|---|---|---|---|
| 0.80 | 1st | 120 | 762 | 358 | +58.2% | $3,795 |
| 0.80 | 2nd | 150 | 1,007 | 428 | +43.1% | $541 |
| 0.85 | 1st | 139 | 901 | 410 | +50.2% | $3,777 |
| 0.85 | 2nd | 206 | 1,407 | 572 | +69.7% | $404 |
| 0.90 | 1st | 247 | 1,657 | 679 | +26.0% | $3,074 |
| 0.90 | 2nd | 364 | 2,544 | 977 | +37.4% | $336 |
| 0.95 | 1st | 1,875 | 13,227 | 4,777 | +2.1% | $1,180 |
| 0.95 | 2nd | 1,714 | 12,013 | 4,303 | +7.9% | $463 |

(All of Australia, weighted average: under 0.85 made +48.5% on 136 races and +107.9% on 137; under 0.90, +32.8% on
195 and +63.1% on 226.)

### Is the rule carried by a few big prices? (run 42146524811)

Book on the last price traded:

| under | scope | bets | flat ROI | place BSP capped at $20 | without the 5 biggest returns | biggest place BSP that placed |
|---|---|---|---|---|---|---|
| 0.85 | VIC | 648 | +46.0% | +45.6% | +35.4% | $23.00 |
| 0.90 | VIC | 1,155 | +22.3% | +22.0% | +16.2% | $23.00 |
| 0.85 | all of Australia | 2,308 | +62.1% | +37.9% | +34.4% | $593.68 |
| 0.90 | all of Australia | 4,201 | +32.9% | +19.4% | +17.6% | $593.68 |

Year by year, book on the last price traded under 0.90:

| year | VIC races | VIC bets | VIC flat ROI | VIC median place BSP money per race | Australia races | Australia flat ROI | Australia median money |
|---|---|---|---|---|---|---|---|
| 2020 | 35 | 232 | +5.0% | $553 | 115 | +13.7% | $650 |
| 2021 | 24 | 155 | +19.0% | $3,986 | 64 | +19.5% | $3,934 |
| 2022 | 15 | 97 | +44.2% | $4,325 | 48 | +45.7% | $4,097 |
| 2023 | 13 | 86 | +59.0% | $4,967 | 40 | +45.8% | $5,320 |
| 2024 | 13 | 86 | +44.6% | $1,198 | 42 | +74.5% | $1,043 |
| 2025 | 49 | 359 | +3.6% | $305 | 217 | +39.5% | $223 |
| 2026 (to October) | 20 | 140 | +51.1% | $588 | 85 | +19.0% | $348 |

**The edge is real, small and thin.**
- **Big prices do not carry it in Victoria.** Capping place BSP at $20 changes nothing, the biggest place BSP that
  placed was $23, and taking out the five biggest returns still leaves +35% (under 0.85) and +16% (under 0.90). Across
  Australia a few long prices do more of the work: +62% falls to +38% capped.
- **It makes money in both halves and in every year**, in Victoria and across Australia.
- **It is rare.** Victoria had 98 races under 0.85 in nearly seven years (about 14 a year), and 13 to 49 a year under
  0.90. Across Australia: 345 races under 0.85, about 50 a year.
- **The money is thin.** In 2025-26 the median place BSP money in these races was $223 to $588 a race, across the
  whole field. A backer's own BSP stake is matched against the lay money at BSP, so in a market that size a stake of
  $10 a runner moves the price it is paid at. These ROIs are what a bet too small to move the BSP would have made.
- **"The last price traded" is the last trade before the market closed.** Anyone betting acts a little before that,
  on a book that can still move.

Rough size, before the stake moves the price: $10 a runner on about 7 runners is $70 a race. About 14 Victorian races
a year at +46% is about $450 a year. About 50 Australian races a year at +60% is about $2,000 a year, at most.

**Decision:** nothing goes to the card; the card is TAB win bets. A Betfair place sideline would need four things,
and none of it happens without the founder's OK:
- a Betfair API key to read the place books live
- a watch a few minutes before each jump
- a paper run first: record the live book, then compare it with the BSP and the result
- a measure of how far our own stake moves the BSP in a market this thin

The win market shows nothing like this: its book at BSP sits at 1.003 in the same races, and Test 28's 1.3x rule at
BSP found 5 bets.

**Parked** (founder, 6 Nov 2026: "park the Betfair place thing"). Nothing is built for it. If it is picked up, the
first step is still a paper run on live place books.

## Test 31: the winners twin against BSP (6 Nov 2026, gh topaz run 42155433985, `topaz_round17.py`)

Every walk-forward since Test 14 has scored an "ensemble" beside the card's model. In Test 28, for example, the model
scored 1.6056, the ensemble 1.5924 and GRV's SP 1.5952. The two models:
- **A**: fitted on the BSP's chances. This is the model the card prices with.
- **B**: a twin fitted on the winners.

The gap to BSP had only ever been measured on A. This run uses the production inputs (161, with the drift on for the
guard) and the standard split:
- A: early stopping took 2,878 rounds.
- B: the same inputs and recency weights; early stopping took 319 rounds.
- The ensemble: 0.50 x A plus 0.56 x B, fitted on the early-stopping months.

Scored: 22,747 races with BSP (BSP 1.4839; 1st half 1.5010, 2nd 1.4686) and 25,630 races with GRV's SP (SP 1.5951).

| price | log loss, BSP races | gap to BSP | 1st half | 2nd half | log loss, SP races | gap to GRV's SP |
|---|---|---|---|---|---|---|
| A, the BSP-chance model (the card) | 1.5816 | +0.0977 | +0.0907 | +0.1039 | 1.6095 | +0.0144 |
| B, the winners twin | 1.5946 | +0.1107 | +0.1012 | +0.1192 | 1.6109 | +0.0157 |
| the ensemble of A and B | 1.5831 | +0.0992 | +0.0908 | +0.1068 | 1.6017 | +0.0066 |

| runners (scored races with BSP) | runners | wins | A/E vs A | A/E vs B | A/E vs the ensemble | A/E vs BSP |
|---|---|---|---|---|---|---|
| SP favourite | 23,368 | 9,255 | 1.149 | 1.156 | 1.115 | 0.997 |
| A's price $1-$2 | 3,665 | 2,165 | 1.003 | 1.018 | 0.969 | 0.984 |
| A's price $2-$3 | 10,789 | 4,339 | 1.006 | 1.018 | 0.974 | 1.001 |
| A's price $3-$5 | 24,304 | 6,254 | 1.005 | 1.011 | 0.989 | 0.992 |
| A's price $5-$10 | 42,889 | 6,314 | 1.024 | 1.022 | 1.039 | 1.009 |
| A's price $10-$20 | 37,205 | 2,685 | 0.981 | 0.964 | 1.030 | 1.008 |
| A's price $20-$1000 | 41,226 | 990 | 0.864 | 0.818 | 0.942 | 1.006 |

The 1.3x rule at GRV's SP (our price $2-$15, Kelly x75 cap 4, no commission):

| ours | blend weights (ours / SP) | guard | half | bets | winners | A/E | flat ROI | units staked | Kelly ROI | units won |
|---|---|---|---|---|---|---|---|---|---|---|
| A | 0.50 / 0.69 | none | 1st | 699 | 188 | 1.666 | +71.7% | 1,413 | +71.1% | +1,004 |
| A | 0.50 / 0.69 | none | 2nd | 703 | 173 | 1.603 | +72.6% | 1,232 | +74.9% | +922 |
| A | 0.50 / 0.69 | none | all | 1,402 | 361 | 1.635 | +72.1% | 2,645 | +72.8% | +1,927 |
| A | 0.50 / 0.69 | drift under 1.3x | 1st | 481 | 152 | 1.808 | +91.1% | 1,084 | +87.5% | +949 |
| A | 0.50 / 0.69 | drift under 1.3x | 2nd | 407 | 133 | 1.904 | +116.1% | 812 | +109.3% | +888 |
| A | 0.50 / 0.69 | drift under 1.3x | all | 888 | 285 | 1.852 | +102.6% | 1,897 | +96.8% | +1,837 |
| the ensemble | 0.52 / 0.63 | none | 1st | 1,305 | 337 | 1.598 | +66.8% | 2,575 | +62.3% | +1,604 |
| the ensemble | 0.52 / 0.63 | none | 2nd | 1,310 | 260 | 1.342 | +36.1% | 2,274 | +51.0% | +1,159 |
| the ensemble | 0.52 / 0.63 | none | all | 2,615 | 597 | 1.476 | +51.4% | 4,849 | +57.0% | +2,763 |
| the ensemble | 0.52 / 0.63 | drift under 1.3x | 1st | 874 | 268 | 1.746 | +87.3% | 1,908 | +78.2% | +1,491 |
| the ensemble | 0.52 / 0.63 | drift under 1.3x | 2nd | 746 | 199 | 1.615 | +72.1% | 1,431 | +86.5% | +1,237 |
| the ensemble | 0.52 / 0.63 | drift under 1.3x | all | 1,620 | 467 | 1.688 | +80.3% | 3,338 | +81.7% | +2,728 |

**The ensemble does not close the gap to BSP.**
- On the races with BSP it is 0.0015 behind A (+0.0992 against +0.0977), level in the first half and behind in the
  second.
- It beats GRV's SP by more (+0.0066 against +0.0144), but the whole of that gain is in the races Betfair does not
  cover, so it is not a race the card can check against BSP. On the 2,883 SP races without a BSP winner, A scores about
  1.83 and the ensemble about 1.75 (worked from the totals above). A is trained on the BSP's chances where they exist
  and GRV's SP where they do not, and B learns those races from the result.
- The ensemble is the better-calibrated price on long dogs: A/E 0.942 over $20, against A's 0.864. But it gives some
  of that back in the middle: the ensemble undercounts its $2-$3 dogs (0.974) where A is at 1.006.

**In the 1.3x rule the ensemble bets more and earns less per bet.**
- It finds about 80-90% more bets.
- With the drift guard it wins more units in both halves: +1,491 against +949, and +1,237 against +888.
- Its ROI is lower: Kelly +81.7% against +96.8% with the guard, and +57.0% against +72.8% without.
- Without the guard its second half falls to +36.1% flat, against A's +72.6%.

This is a trade between turnover and edge, not a better price. More bets at a lower edge also means more TAB
accounts watched sooner.

**Decision:** A stays on the card. Whether the extra units are worth the extra bets is the founder's call, and a
walk-forward of the rule on the ensemble should come before any switch. The walk-forward's `horse_rule` uses A only
today.

## Test 32: the label (6 Nov 2026, gh topaz run 42164443982, `topaz_round19.py`)

The card's model learns the market's chances. It uses BSP's chance where Betfair's files have the dog (2020 on) and
GRV's SP where they do not: every race before 2020, plus the runners Betfair's files miss since. GRV's SP is a
bookmaker's price with a 19% margin and its own tilts (Test 24). The training rows were tried four ways, on the
production inputs and the standard split:
- 73,369 training races, 38,303 of them with a BSP on every runner (from 1 Jan 2020).
- GRV's SP corrected to BSP takes a power of 1.065: on the races with both, BSP is a little sharper than the SP.
- Scored: 22,747 races with BSP (BSP 1.4839) and 25,630 with GRV's SP (SP 1.5951).

| training label | races | rounds | log loss | gap to BSP | 1st half | 2nd half | gap to GRV's SP | SP favourite A/E |
|---|---|---|---|---|---|---|---|---|
| L0 BSP's chance, else GRV's SP's (the weekly train) | 73,369 | 2185 | 1.5823 | +0.0984 | +0.0915 | +0.1046 | +0.0149 | 1.151 |
| L1 only races with a BSP on every runner | 38,303 | 4529 | 1.5805 | +0.0966 | +0.0904 | +0.1021 | +0.0126 | 1.131 |
| **L2 the rest at half weight** | 73,369 | 4750 | **1.5797** | **+0.0958** | **+0.0890** | **+0.1019** | **+0.0121** | 1.142 |
| L3 the rest on GRV's SP corrected to BSP (power 1.06) | 73,369 | 4930 | 1.5809 | +0.0970 | +0.0901 | +0.1032 | +0.0134 | 1.139 |

**How big is the noise?** L0 is the same model as rounds 15 and 17. There it scored 1.5816 on 2,878 rounds; here it
scored 1.5823 on 2,185. The early stopping landed differently, and the run-to-run noise is about 0.0007.

**Every change to the label beats L0, and L2 beats it most.** Against this run's L0, L2 is 0.0026 better. Against the
same model in round 17 (+0.0977, halves +0.0907 / +0.1039), it is 0.0019 better, and better in both halves. Even L1,
on half the races, beats L0. So the SP-labelled races are not doing much for the model at full weight. Correcting the
SP to BSP (L3) helps less than simply weighting those races down. The SP favourite's A/E moves only a little (1.151 to
1.131-1.142). The favourite gap is not the label's doing either.

**Decision:** not yet in production. The gain is about three times the noise and in both halves, but it is one split.
`WALK_SP_WEIGHT=0.5` now sets the weight in the walk-forward (`topaz_walk.py`) and in the weekly train
(`topaz_price_upcoming.py`); the default of 1 leaves both as they were. A walk-forward with the weight at 0.5 goes
next, against Test 27's +0.0888. The weekly train takes it only if the walk-forward agrees.

## Test 33: track character (6 Nov 2026, gh topaz run 42177269716, `topaz_round20.py`)

The founder asked about track dimensions, then settled on measuring each track from its own results ("1 is fine now,
would just be a small amount of cases, a dog transferring for the first time"). Topaz carries no dimensions. Each
track and distance is measured from its races on earlier days (at least 30):
- the leader's win share
- wins from 4th or worse at the first point
- the mean winning margin
- boxes 1-2 against boxes 7-8

A **speed track** is one where the leader wins 51.2% or more (the training rows' median). Each dog then gets its
average beat-the-market (won less its market chance) at today's kind of track and at the other kind.

The leader's win share by track, latest distance: HVL 43%, BAL 44%, TRA 46%, SAP 46%, CRN 47%, HOR 47%, SAN 47%,
MEP 47%, BEN 48%, WGL 48%, MEA 48%, GEL 51%, SHP 52%, SLE 56%, WBL 62%.

The production inputs and the standard split. Scored: 22,747 races with BSP (BSP 1.4839). 22,794 runners were at the
track for the first time (not debut), in 11,271 of those races.

| row | inputs | rounds | log loss | gap to BSP | 1st half | 2nd half | gap, races with a first-timer |
|---|---|---|---|---|---|---|---|
| F0 the production model | 161 | 2185 | 1.5823 | +0.0984 | +0.0915 | +0.1046 | +0.0969 |
| F1 + track character and form by kind of track | 168 | 5955 | 1.5794 | +0.0955 | +0.0888 | +0.1014 | +0.0948 |

| runners (races with BSP) | runners | wins | A/E vs F0 | A/E vs F1 | A/E vs BSP | A/E vs GRV's SP |
|---|---|---|---|---|---|---|
| first time at the track | 19,524 | 3,182 | 1.010 | 1.011 | 1.013 | 1.031 |
| first time, a speed track, form there good | 3,530 | 616 | 0.985 | 0.984 | 0.998 | 1.012 |
| first time, form at this kind of track poor | 9,574 | 1,423 | 1.000 | 1.002 | 1.003 | 1.015 |
| raced here before | 136,811 | 19,014 | 1.001 | 1.000 | 0.999 | 0.996 |

The 1.3x rule at GRV's SP (our price $2-$15, Kelly x75 cap 4):

| row | guard | half | bets | winners | A/E | flat ROI | units staked | Kelly ROI | units won |
|---|---|---|---|---|---|---|---|---|---|
| F0 | none | 1st | 693 | 188 | 1.649 | +70.2% | 1,418 | +69.1% | +980 |
| F0 | none | 2nd | 691 | 162 | 1.538 | +63.8% | 1,202 | +72.5% | +871 |
| F0 | none | all | 1,384 | 350 | 1.596 | +67.0% | 2,620 | +70.6% | +1,851 |
| F0 | drift under 1.3x | 1st | 484 | 152 | 1.765 | +88.8% | 1,099 | +83.9% | +922 |
| F0 | drift under 1.3x | 2nd | 401 | 126 | 1.818 | +106.4% | 800 | +105.1% | +842 |
| F0 | drift under 1.3x | all | 885 | 278 | 1.789 | +96.8% | 1,899 | +92.9% | +1,764 |
| F1 | none | 1st | 796 | 206 | 1.581 | +62.4% | 1,648 | +68.7% | +1,133 |
| F1 | none | 2nd | 794 | 195 | 1.614 | +68.6% | 1,406 | +78.4% | +1,103 |
| F1 | none | all | 1,590 | 401 | 1.597 | +65.5% | 3,054 | +73.2% | +2,236 |
| F1 | drift under 1.3x | 1st | 561 | 170 | 1.716 | +80.9% | 1,282 | +82.6% | +1,059 |
| F1 | drift under 1.3x | 2nd | 471 | 152 | 1.908 | +111.6% | 934 | +113.2% | +1,057 |
| F1 | drift under 1.3x | all | 1,032 | 322 | 1.802 | +94.9% | 2,216 | +95.5% | +2,116 |

**Dogs at a new track are not where the gap is.**
- Our model already prices them about right: they win 1.0% more than F0 says and 1.3% more than BSP says.
- GRV's SP is the price that under-rates them, by 3.1%.
- Dogs with good form at today's kind of track win slightly less than F0 says (0.985).

**Track character helps a little everywhere.**
- 0.0029 closer to BSP overall, and closer in both halves (0.0027 and 0.0032).
- With the drift guard, about 350 more units, more in both halves (+1,059 against +922, +1,057 against +842), at the
  same Kelly ROI.
- The gain is smaller on the races with a first-timer (0.0021), so it is not the first-timers that carry it.

One caution: F0 stopped early at 2,185 rounds here. The same model at 2,878 rounds scored 1.5816 in rounds 15 and 17,
and against that F1's gain is 0.0022. That is still about three times the noise (Test 32).

**Decision:** a walk-forward before production. `WALK_TRACK=yes` puts the inputs into `build_full`, with a speed track
fixed at the leader winning 50%, near the median, so no cut is fitted on the scored months.

## Test 34: the horse book's rules on the dogs (6 Nov 2026, gh topaz run 42180541333, `topaz_round21.py`)

The founder's brief for the horse book ("build a model and betting system like the Fk-model horse book"), tried rule
by rule on the dogs. Set-up: the production model (2,878 rounds) and the standard split, scored on the last quarter.
The dogs have no history of TAB's opens, so GRV's SP stands in for the open, which is the price the horse book bets.

### 1. Distance from BSP (KL divergence; 22,747 races with BSP and GRV's SP on every runner)

| price | KL from BSP | 1st half | 2nd half |
|---|---|---|---|
| our model | 0.0944 | 0.0900 | 0.0987 |
| GRV's SP | 0.0690 | 0.0744 | 0.0637 |

GRV's SP sits closer to BSP than our model does, and has moved closer in the second half (Test 14's August 2026
sharpening). Our model never sees a price, so this is the expected order.

### 2. The lay book at BSP (lay 1 unit; a loser +0.92, a winner -(BSP - 1); no first starters)

| rule | half | lays | winners | A/E vs BSP | return per lay | units laid | units won |
|---|---|---|---|---|---|---|---|
| BSP $15-$40, BSP 1.6x our price (the horse rule) | 1st | 7,965 | 306 | 0.923 | -1.1% | 7,965 | -88.8 |
| BSP $15-$40, BSP 1.6x our price (the horse rule) | 2nd | 8,513 | 331 | 0.936 | -3.8% | 8,513 | -321.0 |
| BSP $15-$40, BSP 1.6x our price (the horse rule) | all | 16,478 | 637 | 0.930 | -2.5% | 16,478 | -409.8 |
| BSP $15-$40, BSP 1.3x our price | 1st | 11,481 | 473 | 0.970 | -4.3% | 11,481 | -498.5 |
| BSP $15-$40, BSP 1.3x our price | 2nd | 11,779 | 475 | 0.953 | -4.6% | 11,779 | -543.6 |
| BSP $15-$40, BSP 1.3x our price | all | 23,260 | 948 | 0.961 | -4.5% | 23,260 | -1,042.1 |
| BSP $15-$40, BSP 2x our price | 1st | 4,530 | 161 | 0.882 | +2.6% | 4,530 | +115.8 |
| BSP $15-$40, BSP 2x our price | 2nd | 5,174 | 189 | 0.912 | -0.7% | 5,174 | -37.9 |
| BSP $15-$40, BSP 2x our price | all | 9,704 | 350 | 0.898 | +0.8% | 9,704 | +77.9 |
| BSP $8-$15, BSP 1.6x our price | 1st | 3,108 | 308 | 1.120 | -19.4% | 3,108 | -603.9 |
| BSP $8-$15, BSP 1.6x our price | 2nd | 3,519 | 319 | 1.019 | -9.4% | 3,519 | -331.6 |
| BSP $8-$15, BSP 1.6x our price | all | 6,627 | 627 | 1.066 | -14.1% | 6,627 | -935.6 |
| BSP $8-$15, BSP 1.3x our price | 1st | 5,948 | 582 | 1.088 | -17.0% | 5,948 | -1,009.8 |
| BSP $8-$15, BSP 1.3x our price | 2nd | 6,230 | 581 | 1.035 | -11.0% | 6,230 | -682.7 |
| BSP $8-$15, BSP 1.3x our price | all | 12,178 | 1,163 | 1.061 | -13.9% | 12,178 | -1,692.5 |

**The lay book does not carry over.**
- The long dogs we rate 1.6x longer than BSP do win less than BSP says (A/E 0.930), but not by enough to pay the
  commission: -2.5%, and a loss in both halves.
- At 2x it is break-even (+0.8%, and the second half loses).
- At $8-$15 the dogs we dislike win MORE than BSP says (1.066), so laying them loses 14%.
- BSP's favourite-longshot bias is small on the dogs (Test 24), and the horse lay book lives on that bias.

### 3. The back book at BSP (1 unit on the BSP favourite, 8% commission)

| rule | half | bets | winners | A/E vs BSP | flat ROI | units staked | units won |
|---|---|---|---|---|---|---|---|
| BSP favourite $4-$7, our price 1.6x BSP (the horse rule) | 1st | 193 | 52 | 1.183 | +11.2% | 193 | +21.6 |
| BSP favourite $4-$7, our price 1.6x BSP (the horse rule) | 2nd | 190 | 36 | 0.827 | -21.1% | 190 | -40.2 |
| BSP favourite $4-$7, our price 1.6x BSP (the horse rule) | all | 383 | 88 | 1.006 | -4.9% | 383 | -18.6 |
| BSP favourite $4-$7, our price 1.3x BSP | 1st | 334 | 87 | 1.140 | +7.4% | 334 | +24.6 |
| BSP favourite $4-$7, our price 1.3x BSP | 2nd | 317 | 64 | 0.882 | -16.1% | 317 | -50.9 |
| BSP favourite $4-$7, our price 1.3x BSP | all | 651 | 151 | 1.014 | -4.0% | 651 | -26.3 |
| BSP favourite $2-$4, our price 1.6x BSP | 1st | 2,163 | 803 | 1.016 | -4.4% | 2,163 | -96.1 |
| BSP favourite $2-$4, our price 1.6x BSP | 2nd | 2,108 | 816 | 1.053 | -0.5% | 2,108 | -11.5 |
| BSP favourite $2-$4, our price 1.6x BSP | all | 4,271 | 1,619 | 1.034 | -2.5% | 4,271 | -107.6 |
| BSP favourite $2-$4, our price 1.3x BSP | 1st | 4,009 | 1,479 | 1.003 | -5.4% | 4,009 | -215.5 |
| BSP favourite $2-$4, our price 1.3x BSP | 2nd | 3,942 | 1,541 | 1.055 | +0.0% | 3,942 | +1.5 |
| BSP favourite $2-$4, our price 1.3x BSP | all | 7,951 | 3,020 | 1.029 | -2.7% | 7,951 | -214.0 |
| BSP favourite $1-$2, our price 1.3x BSP | 1st | 1,376 | 808 | 0.992 | -3.8% | 1,376 | -52.9 |
| BSP favourite $1-$2, our price 1.3x BSP | 2nd | 1,614 | 950 | 0.970 | -6.1% | 1,614 | -98.1 |
| BSP favourite $1-$2, our price 1.3x BSP | all | 2,990 | 1,758 | 0.980 | -5.1% | 2,990 | -151.0 |

**The back book does not carry over either.**
- The $4-$7 favourites are rare on the dogs (383 in 20 months), and the rule's +11.2% first half turns into -21.1%.
- The $2-$4 favourites we rate 1.6x longer than BSP do win 3.4% more than BSP says. That is the same favourite
  under-rating Test 24 found (A/E 1.15 against our model). But 3% is smaller than the commission.

### 4. The order sheet at GRV's SP (blend 0.50 x ours, 0.69 x GRV's, fitted on the early-stopping months)

| rule | half | bets | winners | A/E vs the price | flat ROI | units staked | units won |
|---|---|---|---|---|---|---|---|
| the horse book's order sheet and stake | 1st | 1,889 | 547 | 1.357 | +45.6% | 12,572 | +6,158.3 |
| the horse book's order sheet and stake | 2nd | 1,857 | 460 | 1.227 | +19.1% | 12,791 | +3,359.5 |
| the horse book's order sheet and stake | all | 3,746 | 1,007 | 1.295 | +32.5% | 25,363 | +9,517.7 |
| Test 27's 1.3x rule (x75 Kelly, cap 4) | 1st | 699 | 188 | 1.666 | +71.7% | 1,413 | +1,004.4 |
| Test 27's 1.3x rule (x75 Kelly, cap 4) | 2nd | 703 | 173 | 1.603 | +72.6% | 1,232 | +922.3 |
| Test 27's 1.3x rule (x75 Kelly, cap 4) | all | 1,402 | 361 | 1.635 | +72.1% | 2,645 | +1,926.7 |
| the order sheet, Test 27's stake | 1st | 1,889 | 547 | 1.357 | +45.6% | 2,436 | +1,273.5 |
| the order sheet, Test 27's stake | 2nd | 1,857 | 460 | 1.227 | +19.1% | 1,915 | +834.0 |
| the order sheet, Test 27's stake | all | 3,746 | 1,007 | 1.295 | +32.5% | 4,351 | +2,107.5 |
| Test 27's bets, the horse book's stake | 1st | 699 | 188 | 1.666 | +71.7% | 5,804 | +4,196.9 |
| Test 27's bets, the horse book's stake | 2nd | 703 | 173 | 1.603 | +72.6% | 6,095 | +4,581.2 |
| Test 27's bets, the horse book's stake | all | 1,402 | 361 | 1.635 | +72.1% | 11,898 | +8,778.0 |
| the order sheet, drift guard 1.3x | 1st | 1,393 | 449 | 1.421 | +51.5% | 9,252 | +5,246.6 |
| the order sheet, drift guard 1.3x | 2nd | 1,170 | 368 | 1.397 | +46.0% | 8,064 | +4,461.2 |
| the order sheet, drift guard 1.3x | all | 2,563 | 817 | 1.410 | +49.0% | 17,316 | +9,707.9 |

**The order sheet's selection is looser than the dogs' rule.**
- The horse sheet bets when the blended chance x the price is at least 1.2 (1.15 under $4). The dogs' rule needs 1.3.
- So the sheet finds 2.7x the bets at half the edge: +32.5% flat, against +72.1%.
- Its second half drops to +19.1%; the 1.3x rule holds at +72.6%.
- With the drift guard the sheet holds better (+51.5% and +46.0%).

**The horse stake is the dogs' Kelly at a bigger size.**
- On the 1.3x rule's own bets it returns 73.8% on units staked, against 72.8% for the dogs' x75 Kelly.
- It stakes 4.5x as much (up to 10 units a bet against 4), and wins 4.5x as many units, +4,197 and +4,581 in the two
  halves.
- So the formula is not better or worse, only bigger. How big to bet is a bankroll decision, and it is the founder's.

### 5. Calibration by track (the brief's metro fix)

Our model's A/E over all runners at a track is 1.000 at every track. That is true by construction: each race's chances
add to 1 and each race has one winner, so it tells nothing. The order sheet's bets, track by track, do tell something:

| track | runners | order-sheet bets | their winners | their A/E vs GRV's SP |
|---|---|---|---|---|
| BAL | 19,953 | 422 | 127 | 1.477 |
| BEN | 17,935 | 374 | 107 | 1.451 |
| GEL | 19,055 | 399 | 119 | 1.412 |
| HOR | 9,934 | 241 | 84 | 1.484 |
| HVL | 16,513 | 408 | 90 | 1.171 |
| MEA | 6,697 | 65 | 16 | 1.028 |
| MEP | 8,602 | 144 | 39 | 1.175 |
| SAN | 7,546 | 102 | 20 | 0.836 |
| SAP | 7,624 | 125 | 39 | 1.409 |
| SHP | 18,135 | 324 | 85 | 1.236 |
| SLE | 14,303 | 289 | 70 | 1.198 |
| TRA | 3,438 | 73 | 21 | 1.602 |
| WBL | 17,250 | 399 | 109 | 1.309 |
| WGL | 19,912 | 381 | 81 | 1.061 |

**The metro fix may carry over, but less than it first looked.** Corrected after the track codes were read (run
42189617014): Sandown and The Meadows each race under two codes.
- Sandown is SAN (Sandown Park, since 2013) and SAP (Sandown, since Aug 2014).
- The Meadows is MEA (The Meadows) and MEP (Meadows).
- Cranbourne (CRN) last raced in Jan 2022.

The order sheet's bets by venue:
- **Sandown:** SAN 0.836 on 102 bets, but SAP 1.409 on 125. Together that is about 1.14 (59 winners against about
  52 expected).
- **The Meadows:** MEA 1.028 on 65, MEP 1.175 on 144. Together about 1.13 (55 against about 49).
- **The country tracks:** mostly 1.2 to 1.6, but Warragul is 1.061 and Healesville 1.171.

So the two metro venues sit at the low end, not in a class of their own, and the samples are small. The next step is
the 1.3x rule track by track over the walk-forward's 29 months, before any track gets the lean to the market.

**Decision:** the card keeps the 1.3x rule and its x75 Kelly stake.
- Not taken: the lay book, the back book and the 1.2 edge do not hold on the dogs.
- Still to test: the metro lean at Sandown and The Meadows (all four codes).
- The founder's call: the stake size.

## Test 35: Isolynx tracking, and the checks (6 Nov 2026, gh topaz run 42181292510, `topaz_round18.py`)

GRV switched the key on for Isolynx at 2:25pm on 6 Nov. The pull (run 42158318067) asked for 14,140 dogs and got
96,877 tracked runs of 9,787 dogs, from 20 Oct 2022 to 6 Nov 2026, with no failures. The tracked tracks are The
Meadows, Sandown, Healesville, Traralgon and Cranbourne.

The inputs come from each dog's earlier tracked runs, par-relative by track and distance (`topaz_round6.isolynx_features`,
15 inputs):
- the jump, 50 m, 100 m and last 100 m times
- rail distance, speed at 100 m and top speed

A tracked run before the race exists for 23% of all runners since 2013, and for 68% in the scored quarter.

**A check** (`greyhound.isolynx.trouble`) is a 50 m section 1 m/s slower than the two either side, or 2+ places lost
in one section, between the first and the last 100 m. The check inputs: checked in its last tracked run, the dip,
places lost, and the share checked in its last 5. 53% of tracked runs count as checked, so the threshold is loose
(see below).

The production inputs and the standard split; 22,747 scored races with BSP (BSP 1.4839).

| lead model | one-leader races | its top pick led | 1st half | 2nd half |
|---|---|---|---|---|
| without Isolynx | 22,463 | 40.4% | 40.1% | 40.7% |
| with Isolynx | 22,463 | 40.3% | 39.9% | 40.5% |

| row | inputs | rounds | log loss | gap to BSP | 1st half | 2nd half |
|---|---|---|---|---|---|---|
| F0 the production model, no Isolynx | 161 | 2878 | 1.5816 | +0.0977 | +0.0907 | +0.1039 |
| **F1 + Isolynx in the win model** | 176 | 5499 | **1.5777** | **+0.0938** | **+0.0860** | **+0.1007** |
| F2 + Isolynx in the lead model too | 176 | 4040 | 1.5788 | +0.0949 | +0.0874 | +0.1016 |
| **F3 F2 + the checks** | 180 | 5984 | **1.5775** | **+0.0936** | **+0.0865** | **+0.1000** |

(The split by tracked and other tracks failed: the script matched track names against track codes. It is fixed for
the next run.)

| last tracked run | runners | wins | A/E vs F2 | A/E vs F3 | A/E vs BSP | A/E vs GRV's SP |
|---|---|---|---|---|---|---|
| checked | 50,749 | 7,363 | 1.027 | 1.023 | 1.008 | 1.016 |
| not checked | 58,963 | 8,262 | 0.959 | 0.961 | 1.000 | 0.997 |
| checked, 3+ places lost | 3,303 | 492 | 1.009 | 1.004 | 0.992 | 1.016 |
| no tracked run before | 50,366 | 7,122 | 1.023 | 1.025 | 0.993 | 0.988 |

The 1.3x rule at GRV's SP (our price $2-$15, Kelly x75 cap 4):

| row | guard | half | bets | winners | A/E | flat ROI | units staked | Kelly ROI | units won |
|---|---|---|---|---|---|---|---|---|---|
| F0 | none | 1st | 699 | 188 | 1.666 | +71.7% | 1,413 | +71.1% | +1,004 |
| F0 | none | 2nd | 703 | 173 | 1.603 | +72.6% | 1,232 | +74.9% | +922 |
| F0 | none | all | 1,402 | 361 | 1.635 | +72.1% | 2,645 | +72.8% | +1,927 |
| F0 | drift under 1.3x | 1st | 481 | 152 | 1.808 | +91.1% | 1,084 | +87.5% | +949 |
| F0 | drift under 1.3x | 2nd | 407 | 133 | 1.904 | +116.1% | 812 | +109.3% | +888 |
| F0 | drift under 1.3x | all | 888 | 285 | 1.852 | +102.6% | 1,897 | +96.8% | +1,837 |
| F1 | none | 1st | 984 | 247 | 1.573 | +63.3% | 1,963 | +66.6% | +1,307 |
| F1 | none | 2nd | 1,040 | 225 | 1.440 | +51.2% | 1,801 | +59.7% | +1,074 |
| F1 | none | all | 2,024 | 472 | 1.507 | +57.1% | 3,764 | +63.3% | +2,381 |
| F1 | drift under 1.3x | 1st | 680 | 205 | 1.760 | +88.4% | 1,489 | +84.6% | +1,259 |
| F1 | drift under 1.3x | 2nd | 620 | 172 | 1.656 | +88.1% | 1,195 | +85.3% | +1,019 |
| F1 | drift under 1.3x | all | 1,300 | 377 | 1.711 | +88.3% | 2,684 | +84.9% | +2,278 |
| F2 | none | 1st | 976 | 239 | 1.527 | +59.8% | 1,934 | +60.9% | +1,178 |
| F2 | none | 2nd | 1,027 | 216 | 1.411 | +48.6% | 1,769 | +59.3% | +1,049 |
| F2 | none | all | 2,003 | 455 | 1.469 | +54.0% | 3,703 | +60.1% | +2,227 |
| F2 | drift under 1.3x | 1st | 680 | 200 | 1.717 | +86.5% | 1,479 | +81.5% | +1,205 |
| F2 | drift under 1.3x | 2nd | 600 | 168 | 1.689 | +92.9% | 1,164 | +89.4% | +1,040 |
| F2 | drift under 1.3x | all | 1,280 | 368 | 1.704 | +89.5% | 2,643 | +85.0% | +2,246 |
| F3 | none | 1st | 1,028 | 261 | 1.597 | +66.6% | 2,013 | +68.0% | +1,368 |
| F3 | none | 2nd | 1,048 | 227 | 1.443 | +51.2% | 1,834 | +62.4% | +1,144 |
| F3 | none | all | 2,076 | 488 | 1.521 | +58.8% | 3,847 | +65.3% | +2,512 |
| F3 | drift under 1.3x | 1st | 717 | 216 | 1.751 | +90.2% | 1,542 | +84.5% | +1,304 |
| F3 | drift under 1.3x | 2nd | 626 | 175 | 1.681 | +88.1% | 1,219 | +90.9% | +1,108 |
| F3 | drift under 1.3x | all | 1,343 | 391 | 1.719 | +89.2% | 2,762 | +87.3% | +2,412 |

**Isolynx in the win model is the biggest single step since GRV's rating.**
- F1 is 0.0039 closer to BSP (+0.0938 against +0.0977), and closer in both halves (0.0047 and 0.0032). The F0 here
  is the same 2,878-round fit as rounds 15 and 17, so the comparison is clean, and the gain is about five times the
  noise.
- For scale, GRV's rating was worth 0.0068 in the walk-forward (Test 28).
- This is with tracking for only 23% of the training rows: tracking starts in Oct 2022 and the fit runs from 2013.

**Isolynx does not help the lead model.** Its top pick led 40.3% of the time, against 40.4% without, and putting
tracking into the lead model (F2) is worse than leaving it out (F1). The lead model already has the first-split
ratings, and the tracking's jump and 50 m times add nothing to who leads.

**The checks add a little more** (F3, 0.0013 on F2). They also show something the market prices and we did not:
- Dogs checked in their last tracked run win 2.7% more than our model says, and dogs with a clean last run win 4.1%
  less.
- BSP has both right (1.008 and 1.000).
- So the market knows a dog had trouble last start, and our model did not.
- F3 barely moves the A/E (1.023 / 0.961), most likely because the checks exist only from Oct 2022 and most of the fit
  is older.
- The threshold is too loose to be a "check" in the founder's sense: 53% of runs pass it, and the tighter "3+ places
  lost" group is close to right already (1.009). The A/E split is real either way.

**In the 1.3x rule, Isolynx brings more bets at a lower edge, and more units in both halves.**
- With the drift guard: F1 +1,259 and +1,019 against F0's +949 and +888, at a Kelly ROI of 84.9% against 96.8%.
- F3 makes the most: +2,412 units at 87.3%.
- This is the Test 31 pattern again: every gain in the price brings more disagreements with the SP, each a little
  smaller.

**Decision:** Isolynx goes into the win model and the checks with it (F3), not into the lead model. That needs:
1. a walk-forward with it, against Test 27's +0.0888
2. the nightly price run pulling each card dog's tracking first. That is a day's runners, about 600 calls at 72 a
   minute, about 9 minutes, and the weekly train re-pulling the dogs that ran that week.

Until both are built and the walk-forward agrees, the card runs as it is. Next for the checks: a stricter threshold,
and fitting only on 2022 on, where the checks exist.

## Test 36: five seeds, and the 1.3x rule track by track (6 Nov 2026, gh topaz run 42184462496, `topaz_round22.py`)

Two items from the founder's horse brief ("LightGBM, 5 seeds averaged"; "Metro fix"), on the production inputs and the
standard split, scored on 22,747 races with BSP (BSP 1.4839).

### 1. Five seeds (each early-stopped: 2,878, 3,396, 4,819, 4,804 and 5,058 rounds)

| model | log loss | gap to BSP | 1st half | 2nd half |
|---|---|---|---|---|
| seed 1 alone (the weekly train's seed) | 1.5816 | +0.0977 | +0.0907 | +0.1039 |
| seed 2 alone | 1.5803 | +0.0964 | +0.0902 | +0.1020 |
| seed 3 alone | 1.5802 | +0.0963 | +0.0898 | +0.1022 |
| seed 4 alone | 1.5800 | +0.0961 | +0.0889 | +0.1025 |
| seed 5 alone | 1.5799 | +0.0960 | +0.0890 | +0.1023 |
| **the five averaged** | **1.5791** | **+0.0952** | **+0.0884** | **+0.1013** |

**Five seeds help, and the spread of single seeds measures the noise.**
- The five averaged are 0.0013 better than a typical single seed (1.5804), and better in both halves.
- Seed 1, the one every test so far has used, is the worst of the five: it stopped earliest, at 2,878 rounds.
- So a single seed moves the score by up to 0.0017. That is the noise to hold every one-split result against.
- The tests that cleared it:
  - Isolynx's F1 (1.5777) beats the best single seed by 0.0022.
  - Track character's F1 (1.5794, Test 33) and the half-weight label's L2 (1.5797, Test 32) sit within the seed
    spread of the other seeds. Their gains over seed 1 may be partly seed luck.
  - The walk-forwards running now decide those two.

### 2. The 1.3x rule at GRV's SP (our price $2-$15, Kelly x75 cap 4)

| rule | half | bets | winners | A/E | flat ROI | units staked | Kelly ROI | units won |
|---|---|---|---|---|---|---|---|---|
| one seed, every track (0.50 / 0.69) | 1st | 699 | 188 | 1.666 | +71.7% | 1,413 | +71.1% | +1,004 |
| one seed, every track (0.50 / 0.69) | 2nd | 703 | 173 | 1.603 | +72.6% | 1,232 | +74.9% | +922 |
| one seed, every track (0.50 / 0.69) | all | 1,402 | 361 | 1.635 | +72.1% | 2,645 | +72.8% | +1,927 |
| five seeds, every track (0.51 / 0.68) | 1st | 754 | 197 | 1.597 | +64.6% | 1,558 | +69.0% | +1,075 |
| five seeds, every track (0.51 / 0.68) | 2nd | 748 | 181 | 1.582 | +66.3% | 1,316 | +75.8% | +998 |
| five seeds, every track (0.51 / 0.68) | all | 1,502 | 378 | 1.590 | +65.5% | 2,873 | +72.1% | +2,072 |
| five seeds, SAN and MEA | 1st | 18 | 2 | 0.668 | -38.9% | 38 | -37.9% | -14 |
| five seeds, SAN and MEA | 2nd | 22 | 7 | 1.753 | +93.6% | 40 | +69.2% | +27 |
| five seeds, SAN and MEA | all | 40 | 9 | 1.288 | +34.0% | 77 | +16.8% | +13 |
| five seeds, every other track | 1st | 736 | 195 | 1.620 | +67.2% | 1,520 | +71.6% | +1,089 |
| five seeds, every other track | 2nd | 726 | 174 | 1.575 | +65.5% | 1,276 | +76.0% | +970 |
| five seeds, every other track | all | 1,462 | 369 | 1.599 | +66.3% | 2,796 | +73.7% | +2,059 |

This run's "metro" was SAN and MEA alone. It ran before the track codes showed that Sandown and The Meadows each race
under two codes, so SAP and MEP sit in "every other track"; the table below has all four.

| track (five seeds) | bets | winners | A/E | flat ROI | Kelly ROI | units won |
|---|---|---|---|---|---|---|
| GEL Geelong | 158 | 55 | 2.082 | +123.5% | +123.1% | +401 |
| HOR Horsham | 95 | 28 | 1.831 | +90.1% | +123.4% | +238 |
| BAL Ballarat | 194 | 53 | 1.736 | +84.2% | +94.2% | +367 |
| SLE Sale | 130 | 36 | 1.709 | +71.8% | +72.6% | +189 |
| BEN Bendigo | 144 | 36 | 1.704 | +91.0% | +74.0% | +187 |
| SAP Sandown | 49 | 13 | 1.770 | +73.1% | +101.5% | +86 |
| SHP Shepparton | 100 | 26 | 1.610 | +53.0% | +76.7% | +140 |
| MEP Meadows | 53 | 13 | 1.567 | +36.2% | +74.7% | +68 |
| WBL Warrnambool | 168 | 41 | 1.441 | +46.8% | +43.0% | +145 |
| WGL Warragul | 162 | 32 | 1.307 | +61.7% | +48.2% | +151 |
| TRA Traralgon | 35 | 6 | 1.291 | +37.7% | +14.3% | +8 |
| **HVL Healesville** | **174** | **30** | **1.111** | **+1.0%** | **+25.2%** | **+77** |
| SAN Sandown Park | 22 | 3 | 0.723 | -48.2% | -38.5% | -18 |
| MEA The Meadows | 18 | 6 | (fewer than 20 bets, not listed) | | | |

The metro lean (five seeds):

| rule | half | bets | winners | A/E | flat ROI | units staked | Kelly ROI | units won |
|---|---|---|---|---|---|---|---|---|
| the blend refitted on SAN and MEA races (0.40 / 0.81) | 1st | 740 | 195 | 1.610 | +66.3% | 1,530 | +70.5% | +1,079 |
| the blend refitted on SAN and MEA races (0.40 / 0.81) | 2nd | 729 | 175 | 1.575 | +65.3% | 1,281 | +75.9% | +973 |
| the blend refitted on SAN and MEA races (0.40 / 0.81) | all | 1,469 | 370 | 1.593 | +65.8% | 2,811 | +73.0% | +2,052 |
| SAN and MEA left out | 1st | 736 | 195 | 1.620 | +67.2% | 1,520 | +71.6% | +1,089 |
| SAN and MEA left out | 2nd | 726 | 174 | 1.575 | +65.5% | 1,276 | +76.0% | +970 |
| SAN and MEA left out | all | 1,462 | 369 | 1.599 | +66.3% | 2,796 | +73.7% | +2,059 |

**The metro lean is not needed.**
- The rule bets rarely at the metro tracks: 142 of 1,502 bets across all four codes.
- The blend refitted on metro races does lean to the market (0.40 / 0.81 against 0.51 / 0.68), but it changes the
  units by 20 either way.
- Taken whole, Sandown (SAN and SAP: 71 bets, 16 winners) and The Meadows (MEA and MEP: 71 bets, 19 winners) both make
  money. Only SAN on its own (22 bets) loses, and 22 bets is too few to call.

**Healesville is the weak track.**
- It carries the second-most bets (174), with the lowest A/E of any track with real numbers (1.111). Flat ROI is
  +1.0% and Kelly ROI +25%, against 43-123% at the country tracks.
- It is the one Victorian track Test 33 found the leader wins least at (43%), and the order sheet's bets were lower
  there too (Test 34: 1.171).
- The founder asked about straight tracks: Healesville is where the dogs' racing shape is most different, and where our
  edge is thinnest.
- One split is not a rule. The walk-forward's 29 months by track decide whether Healesville gets a lean or is left off.

**Decision:**
- Five seeds go into the weekly train once the code saves and loads five boosters. Not tonight: tonight's card stays
  on the saved single model.
- No metro lean.
- Healesville goes to the walk-forward check.

## Test 37: the walk-forward, the 1.3x rule on the ensemble (6 Nov 2026, gh topaz run 42164447871, `topaz_walk.py`, `WALK_RULE_ENSEMBLE=yes`)

Test 31's open item: on the standard split, the ensemble (the BSP-chance model and its winners twin) made the 1.3x
rule bet 80-90% more often at a lower ROI. This is the same question month by month, with the rule's blend refitted on
the six months before each month, and the production inputs as Test 27.

**The run is short.** Five jobs shared the runners, and the walk-forward's time guard stopped refitting after June
2026. So it covers 25 months (June 2024 to June 2026), not Test 27's 29, and the four months the SP sharpened most
(July to October 2026) are not in it. Over those 25 months, on the 19,332 BSP-matched races, the gap to BSP is
+0.0862. That is not comparable with Test 27's +0.0888 over a different span. The model and the ensemble below are
scored over the same 25 months, so the comparison between them is fair.

The 1.3x rule at GRV's SP (our price $2-$15, Kelly x75 cap 4, no commission):

| ours | rule | half | bets | winners | A/E | flat ROI | units staked | Kelly ROI | units won | worst drawdown | months in profit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| the model (the card) | no guard | 1st | 1,100 | 244 | 1.404 | +46.8% | 2,229 | +54.6% | +1,216 | 59 | 12 of 13 |
| the model (the card) | no guard | 2nd | 1,103 | 286 | 1.695 | +72.7% | 2,052 | +83.8% | +1,720 | 38 | 13 of 13 |
| the model (the card) | no guard | all | 2,203 | 530 | 1.547 | +59.8% | 4,281 | +68.6% | +2,936 | 59 | 24 of 25 |
| the model (the card) | drift guard 1.3x | 1st | 738 | 194 | 1.528 | +64.2% | 1,649 | +70.4% | +1,161 | 42 | 13 of 13 |
| the model (the card) | drift guard 1.3x | 2nd | 738 | 235 | 1.921 | +106.6% | 1,499 | +113.1% | +1,695 | 26 | 13 of 13 |
| the model (the card) | drift guard 1.3x | all | 1,476 | 429 | 1.721 | +85.4% | 3,148 | +90.7% | +2,856 | 42 | 25 of 25 |
| the ensemble | no guard | 1st | 1,867 | 392 | 1.428 | +49.0% | 3,481 | +54.4% | +1,894 | 65 | 12 of 12 |
| the ensemble | no guard | 2nd | 1,874 | 419 | 1.525 | +54.9% | 3,406 | +66.2% | +2,254 | 63 | 13 of 14 |
| the ensemble | no guard | all | 3,741 | 811 | 1.476 | +51.9% | 6,887 | +60.2% | +4,148 | 65 | 25 of 25 |
| the ensemble | drift guard 1.3x | 1st | 1,215 | 307 | 1.573 | +69.7% | 2,474 | +69.5% | +1,720 | 51 | 12 of 12 |
| the ensemble | drift guard 1.3x | 2nd | 1,217 | 343 | 1.766 | +86.8% | 2,396 | +95.2% | +2,281 | 42 | 13 of 14 |
| the ensemble | drift guard 1.3x | all | 2,432 | 650 | 1.669 | +78.2% | 4,871 | +82.2% | +4,001 | 51 | 25 of 25 |

Blend weights refitted each month: the model 0.48-0.64 with the SP 0.55-0.68; the ensemble 0.50-0.67 with the SP
0.49-0.64. On the whole scored span, the model scored 1.6138, the ensemble 1.5981 and GRV's SP 1.6118.

**The walk-forward confirms Test 31, month by month.** With the drift guard, the ensemble:
- bets 65% more often (2,432 against 1,476)
- wins 40% more units (+4,001 against +2,856)
- wins more in both halves (+1,720 against +1,161, and +2,281 against +1,695)
- is in profit in all 25 months
- does it at a lower Kelly ROI (82.2% against 90.7%) and a deeper worst drawdown (51 units against 42)

It is the same trade as before, more money at a slightly thinner edge, now holding in every month and both halves.
Over the whole span the ensemble also scores better than GRV's SP (1.5981 against 1.6118); the model alone does not
(1.6138).

**Decision:** the founder's call.
- The case for switching the card's rule to the ensemble is now as strong as the case for the drift guard was.
- What it needs: the weekly train fits and saves the winners twin beside the model, the nightly price run prices both,
  and the card's rule blends the ensemble with GRV's price.
- The cost: about 65% more bets a night at TAB, so more account attention.

## Test 38: the walk-forward, the half-weight label (6 Nov 2026, gh topaz run 42171022820, `topaz_walk.py`, `WALK_SP_WEIGHT=0.5`)

Test 32's open item: on one split, training the BSP-chance model with the races that lack a BSP on every runner (whose
label is GRV's SP chance in whole or part) at half weight beat the full label by 0.0026, in both halves. This is the
same question month by month, with everything else as Test 37 (the production inputs, the ensemble rule switched on).

The run stopped at the same place as Test 37 (the time guard, June 2026), so the two cover the same 25 months and
compare like for like.

| scored quarter | Test 37 (full weight) | half weight |
|---|---|---|
| all 21,991 races: the model | 1.6138 | **1.6111** |
| all 21,991 races: the ensemble | 1.5981 | **1.5970** |
| all 21,991 races: GRV's SP | 1.6118 | 1.6118 |
| the 19,332 BSP-matched races: the model | 1.5771 | **1.5755** |
| the 19,332 BSP-matched races: BSP | 1.4909 | 1.4909 |
| **gap to BSP** | +0.0862 | **+0.0846** |

Month by month, the half-weight gap is smaller in 21 of the 31 scored months. It is larger in 2023-12, 2024-05,
2024-08, 2024-11, 2025-03, 2025-04, 2025-09, 2026-03, 2026-04 and 2026-05.

With the half weight the model alone now scores better than GRV's SP on the whole span (1.6111 against 1.6118), which
at full weight it did not.

The 1.3x rule at GRV's SP (our price $2-$15, Kelly x75 cap 4, no commission), the model as the card uses it. Blend
weights refitted each month: ours 0.49-0.65, the SP 0.53-0.67.

| label | rule | half | bets | winners | A/E | flat ROI | units staked | Kelly ROI | units won | worst drawdown | months in profit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| full (Test 37) | no guard | 1st | 1,100 | 244 | 1.404 | +46.8% | 2,229 | +54.6% | +1,216 | 59 | 12 of 13 |
| full (Test 37) | no guard | 2nd | 1,103 | 286 | 1.695 | +72.7% | 2,052 | +83.8% | +1,720 | 38 | 13 of 13 |
| full (Test 37) | no guard | all | 2,203 | 530 | 1.547 | +59.8% | 4,281 | +68.6% | +2,936 | 59 | 24 of 25 |
| **half** | no guard | 1st | 1,208 | 272 | 1.445 | +50.7% | 2,401 | +55.4% | +1,329 | 64 | 13 of 13 |
| **half** | no guard | 2nd | 1,211 | 310 | 1.675 | +72.9% | 2,290 | +86.6% | +1,982 | 45 | 13 of 13 |
| **half** | no guard | all | 2,419 | 582 | 1.559 | +61.8% | 4,690 | +70.6% | +3,311 | 64 | 25 of 25 |
| full (Test 37) | drift guard 1.3x | 1st | 738 | 194 | 1.528 | +64.2% | 1,649 | +70.4% | +1,161 | 42 | 13 of 13 |
| full (Test 37) | drift guard 1.3x | 2nd | 738 | 235 | 1.921 | +106.6% | 1,499 | +113.1% | +1,695 | 26 | 13 of 13 |
| full (Test 37) | drift guard 1.3x | all | 1,476 | 429 | 1.721 | +85.4% | 3,148 | +90.7% | +2,856 | 42 | 25 of 25 |
| **half** | drift guard 1.3x | 1st | 816 | 216 | 1.551 | +66.2% | 1,798 | +68.1% | +1,224 | 60 | 12 of 13 |
| **half** | drift guard 1.3x | 2nd | 818 | 255 | 1.885 | +107.6% | 1,675 | +113.7% | +1,905 | 51 | 13 of 13 |
| **half** | drift guard 1.3x | all | 1,634 | 471 | 1.716 | +87.0% | 3,473 | +90.1% | +3,130 | 60 | 24 of 25 |

With the drift guard (the card's rule), the half weight:
- bets 11% more often (1,634 against 1,476)
- wins 10% more units (+3,130 against +2,856), and more in both halves (+1,224 against +1,161, +1,905 against +1,695)
- at the same edge: flat ROI +87.0% against +85.4%, Kelly ROI 90.1% against 90.7%, A/E 1.716 against 1.721
- with a deeper worst drawdown (60 units against 42) and one losing month (24 of 25 in profit against 25 of 25)

Without the guard it is better on every line except the drawdown (64 against 59).

The sequential rule at GRV's SP (each month's rule chosen on the six months before) did +63.9% flat on 1,713 bets, A/E
1.630, 24 of 25 months in profit (1st half +53.3%, 2nd +74.3%), against +49.0% at full weight.

At BSP with 8% commission there is still nothing. The blend gives our model a weight of -0.09 to 0.08 against BSP's
0.93 to 1.07, so the 1.3x rule at BSP made 5 bets in 25 months. The sequential rule at BSP lost 3.1% flat on 3,178 bets
(A/E 1.016, 12 of 25 months in profit; 1st half -9.0%, 2nd +2.6%). Beating BSP is the job of rounds 23, 24 and 25
(`topaz_round23.py` to `topaz_round25.py`), written up as they finish.

**The walk-forward confirms Test 32.** The half weight is closer to BSP over the whole span and in two months out of
three, and the card's rule bets a little more at the same edge. The deeper drawdown is the cost of the extra bets, and
18 extra units of drawdown against 274 extra units won is a fair trade.

**Decision:** in production. `WALK_SP_WEIGHT=0.5` goes into the weekly train (gh-topaz-nightly.yml). It takes effect at
Sunday's train; the nightly cards until then use the model saved last Sunday. The price run exports it too, so its
fallback fit (when no saved model is found) trains the same way.

## Test 39: can we beat BSP? The blend, with Isolynx and the checks (6 Nov 2026, gh topaz run 42200167984, `topaz_round23.py`)

The founder asked: "It would be nice to beat BSP, do we have any edges with that?" In every blend of our price with BSP
so far, ours has got a weight near zero, so once BSP is known the model adds nothing. Isolynx and the checks (Test 35)
are the first inputs BSP might not fully hold, so this blends both models with BSP. The blend is fitted on the
early-stopping months and scored on the last quarter's 22,747 races with a BSP on every runner. BSP alone scores 1.4839
(1st half 1.4981, 2nd 1.4699).

| model | rounds | weights (ours / BSP) | ours alone | blend with BSP | blend less BSP | 1st half | 2nd half |
|---|---|---|---|---|---|---|---|
| P the production model | 4,040 | -0.065 / 1.055 | 1.5809 | 1.4840 | +0.0001 | +0.0002 | -0.0001 |
| I + Isolynx and the checks | 2,352 | -0.050 / 1.044 | 1.5795 | 1.4840 | +0.0001 | +0.0003 | -0.0001 |

The rule at BSP (8% commission on winnings, our price $2-$15, Kelly x75 cap 4), back when BSP is at least r times the
blended price:

| model | r | half | bets | winners | A/E | flat ROI | units staked | Kelly ROI | units won |
|---|---|---|---|---|---|---|---|---|---|
| P | 1.1x | 1st | 42 | 9 | 1.349 | +16.4% | 47 | +70.1% | +33 |
| P | 1.1x | 2nd | 77 | 14 | 1.040 | -9.7% | 26 | -7.2% | -2 |
| P | 1.1x | all | 119 | 23 | 1.143 | -0.5% | 73 | +42.8% | +31 |
| P | 1.2x | 1st | 8 | 2 | 2.197 | +70.7% | 21 | +145.5% | +30 |
| P | 1.2x | 2nd | 1 | 0 | 0.000 | -100.0% | 1 | -100.0% | -1 |
| P | 1.2x | all | 9 | 2 | 1.938 | +51.7% | 21 | +136.2% | +29 |
| P | 1.3x | 1st | 4 | 1 | 3.041 | +135.0% | 12 | +189.8% | +22 |
| P | 1.3x | 2nd | 0 | | | | | | |
| P | 1.3x | all | 4 | 1 | 3.041 | +135.0% | 12 | +189.8% | +22 |
| I | 1.1x | 1st | 33 | 6 | 1.138 | -17.1% | 48 | +61.3% | +29 |
| I | 1.1x | 2nd | 35 | 6 | 1.141 | +1.4% | 12 | -8.3% | -1 |
| I | 1.1x | all | 68 | 12 | 1.139 | -7.6% | 60 | +47.1% | +28 |
| I | 1.2x | 1st | 9 | 2 | 1.648 | +51.7% | 25 | +109.0% | +27 |
| I | 1.2x | 2nd | 0 | | | | | | |
| I | 1.2x | all | 9 | 2 | 1.648 | +51.7% | 25 | +109.0% | +27 |
| I | 1.3x | 1st | 5 | 1 | 1.583 | +88.0% | 16 | +119.0% | +19 |
| I | 1.3x | 2nd | 0 | | | | | | |
| I | 1.3x | all | 5 | 1 | 1.583 | +88.0% | 16 | +119.0% | +19 |

**No.** Once BSP is in the blend, both models get a slightly negative weight, so BSP already holds everything they know,
the tracking and the checks included. The blend is 0.0001 worse than BSP alone. The rule finds almost nothing to bet:
119 bets in the quarter at 1.1x, and four at 1.3x, too few to read anything into.

On its own, I is 0.0014 better than P (1.5795 against 1.5809). That is in Test 35's direction but smaller than its
0.0039, and within one seed's noise (Test 36: 0.0017). On these races the gap to BSP is +0.0970 for P and +0.0956 for I.

**Decision:** nothing to bet at BSP. The win model's job is still the TAB prices before the off, where Tests 27 and 38
show the edge.

## Test 40: a rule search at BSP, chosen on old months (6 Nov 2026, gh topaz run 42200450285, `topaz_round24.py`)

The founder asked: "Surely we could find rules with our markets to beat BSP." Test 39 blended our price with BSP and
found nothing. This test asks the narrower question: is there a kind of runner where BSP is reliably wrong, in the
direction our model points?

A rule is three choices:
- a segment: all runners, backing up within 4 days, first time at the track, checked in the last tracked run, clean in
  the last tracked run, boxes 1-2, boxes 7-8, or first starters
- a BSP band: $1.50-$3, $3-$5, $5-$8, $8-$15 or $15-$30
- a side and an edge: back at BSP when BSP is at least r times our price, or lay at BSP when BSP is at most our price
  divided by r, with r = 1.1, 1.3 or 1.6

Stakes are flat, 1 unit, with 8% commission on winnings. The model is I from Test 39 (2,352 rounds, 180 inputs). Its
prices on the early-stopping months (6 Dec 2023 to 5 Jun 2024, never trained on) choose the rules. A rule is chosen
when it had at least 200 bets and a profit there. The scored quarter then tests each chosen rule once, in both halves.

137 rules had 200 or more bets on the early-stopping months, and 30 of them made a profit there. Those 30 on the scored
quarter:

| rule | early-stopping months: bets, ROI | 1st half: bets, ROI | 2nd half: bets, ROI | all: bets, winners, A/E vs BSP, ROI, units |
|---|---|---|---|---|
| back backing up within 4 days, BSP $15-$30, BSP >= 1.6x ours | 339, +41.7% | 850, +18.2% | 1,013, +4.5% | 1,863, 102, 1.145, +10.7%, +200 **both halves** |
| back backing up within 4 days, BSP $15-$30, BSP >= 1.3x ours | 485, +36.2% | 1,282, +13.6% | 1,410, +1.0% | 2,692, 143, 1.102, +7.0%, +188 **both halves** |
| back backing up within 4 days, BSP $15-$30, BSP >= 1.1x ours | 614, +26.0% | 1,634, +9.0% | 1,745, -4.6% | 3,379, 174, 1.059, +1.9%, +65 |
| back boxes 1-2, BSP $15-$30, BSP >= 1.6x ours | 534, +20.5% | 1,488, -20.9% | 1,643, -5.6% | 3,131, 142, 0.940, -12.8%, -402 |
| back checked last tracked run, BSP $5-$8, BSP >= 1.3x ours | 425, +17.9% | 758, -8.2% | 775, +4.6% | 1,533, 254, 1.054, -1.7%, -27 |
| lay clean last tracked run, BSP $5-$8, BSP <= ours / 1.3 | 344, +16.6% | 1,236, -13.7% | 1,452, -1.3% | 2,688, 435, 1.002, -7.0%, -188 |
| back boxes 1-2, BSP $15-$30, BSP >= 1.3x ours | 808, +16.4% | 2,158, -18.2% | 2,259, -11.4% | 4,417, 197, 0.916, -14.7%, -651 |
| lay all runners, BSP $15-$30, BSP <= ours / 1.6 | 300, +15.0% | 834, -3.7% | 743, -16.2% | 1,577, 85, 1.045, -9.6%, -151 |
| lay clean last tracked run, BSP $5-$8, BSP <= ours / 1.1 | 532, +14.6% | 1,934, -7.4% | 2,215, -5.4% | 4,149, 667, 0.995, -6.3%, -263 |
| back all runners, BSP $5-$8, BSP >= 1.6x ours | 367, +12.7% | 921, +0.9% | 1,180, -17.5% | 2,101, 318, 0.969, -9.4%, -198 |
| back boxes 7-8, BSP $15-$30, BSP >= 1.6x ours | 589, +10.7% | 1,376, +4.5% | 1,555, +3.6% | 2,931, 152, 1.092, +4.0%, +117 **both halves** |
| back boxes 1-2, BSP $15-$30, BSP >= 1.1x ours | 995, +10.2% | 2,645, -18.7% | 2,667, -10.3% | 5,312, 240, 0.924, -14.5%, -769 |
| back clean last tracked run, BSP $8-$15, BSP >= 1.6x ours | 274, +9.6% | 1,307, -10.8% | 1,589, -4.2% | 2,896, 257, 0.987, -7.2%, -208 |
| back backing up within 4 days, BSP $8-$15, BSP >= 1.6x ours | 211, +8.5% | 467, +16.9% | 570, -5.3% | 1,037, 104, 1.116, +4.7%, +49 |
| lay backing up within 4 days, BSP $1.5-$3, BSP <= ours / 1.1 | 347, +8.1% | 867, -4.2% | 925, -1.7% | 1,792, 803, 0.986, -2.9%, -52 |
| back boxes 7-8, BSP $5-$8, BSP >= 1.3x ours | 240, +7.8% | 543, -18.2% | 705, -16.1% | 1,248, 176, 0.891, -17.1%, -213 |
| back boxes 1-2, BSP $8-$15, BSP >= 1.6x ours | 386, +7.4% | 995, +5.6% | 1,095, +16.9% | 2,090, 225, 1.182, +11.5%, +241 **both halves** |
| back clean last tracked run, BSP $5-$8, BSP >= 1.3x ours | 228, +6.8% | 1,063, -4.1% | 1,222, -13.2% | 2,285, 346, 0.963, -9.0%, -205 |
| back boxes 7-8, BSP $15-$30, BSP >= 1.3x ours | 895, +6.1% | 2,091, +1.8% | 2,225, -2.1% | 4,316, 218, 1.051, -0.2%, -8 |
| lay backing up within 4 days, BSP $1.5-$3, BSP <= ours / 1.3 | 230, +6.1% | 586, +0.1% | 635, +1.5% | 1,221, 526, 0.951, +0.8%, +10 **both halves** |
| back checked last tracked run, BSP $5-$8, BSP >= 1.1x ours | 719, +5.9% | 1,337, -5.4% | 1,385, -3.2% | 2,722, 442, 1.023, -4.3%, -118 |
| back boxes 1-2, BSP $5-$8, BSP >= 1.3x ours | 348, +5.8% | 921, -8.0% | 973, -3.3% | 1,894, 301, 1.008, -5.6%, -105 |
| lay first time at the track, BSP $5-$8, BSP <= ours / 1.1 | 351, +5.7% | 732, -7.5% | 684, +4.6% | 1,416, 222, 0.969, -1.7%, -24 |
| back all runners, BSP $5-$8, BSP >= 1.3x ours | 1,012, +4.2% | 2,595, -4.7% | 2,791, -8.2% | 5,386, 847, 0.999, -6.5%, -350 |
| lay first time at the track, BSP $5-$8, BSP <= ours / 1.3 | 241, +3.1% | 503, -9.9% | 466, -1.2% | 969, 158, 1.007, -5.7%, -56 |
| lay boxes 1-2, BSP $5-$8, BSP <= ours / 1.3 | 416, +1.8% | 1,036, -24.5% | 1,007, +14.3% | 2,043, 329, 0.993, -5.4%, -110 |
| lay checked last tracked run, BSP $8-$15, BSP <= ours / 1.1 | 822, +1.5% | 1,942, -0.6% | 1,734, -22.3% | 3,676, 363, 1.039, -10.8%, -398 |
| back boxes 7-8, BSP $5-$8, BSP >= 1.1x ours | 412, +0.8% | 1,006, -19.4% | 1,218, -18.1% | 2,224, 311, 0.880, -18.7%, -416 |
| back backing up within 4 days, BSP $5-$8, BSP >= 1.1x ours | 261, +0.2% | 656, +1.7% | 765, -12.6% | 1,421, 227, 1.010, -6.0%, -85 |
| back boxes 7-8, BSP $15-$30, BSP >= 1.1x ours | 1,120, +0.2% | 2,638, +2.4% | 2,748, -5.3% | 5,386, 272, 1.043, -1.5%, -83 |

**5 of the 30 chosen rules made a profit in both halves of the scored quarter.** That is a little more than luck,
not enough to call an edge:
- Two of the five are the same rule at two edges (backing up within 4 days, $15-$30, at 1.6x and 1.3x), so there are
  four distinct results, and one of them (the favourite lay) made +0.8%.
- A rule with no edge before commission loses about 7% at BSP once commission is taken. At $15-$30, with about a
  thousand bets a half, a half's ROI moves by about 14% either way by chance alone. So a zero-edge longshot rule is in
  profit in both halves about one time in ten, and a $5-$8 rule about one time in 25. Ten of the 30 are $15-$30
  rules, four are $8-$15 and 16 are $5-$8 or shorter, so luck alone gives about two.
- The 30 as a whole lost: 23 of them lost over the quarter, some heavily. Back boxes 1-2 at $15-$30 lost 13% to 15%
  at all three edges, after making 10% to 20% on the early-stopping months.

Two rules are worth watching:
- **Back boxes 1-2 at BSP $8-$15 when BSP is at least 1.6x our price:** 2,090 bets, 225 winners against 190 BSP
  expected (A/E 1.182), +11.5% after commission, +241 units. The 1st half made +5.6% and the 2nd +16.9%. The winners
  excess is about 2.5 standard errors. It is the strongest out-of-sample result in the table, but it was one of 30
  scored, and its neighbour at $15-$30 lost in both halves.
- **Back a dog backing up within 4 days at BSP $15-$30 when BSP is at least 1.6x our price:** 1,863 bets, 102 winners
  against 89 expected (A/E 1.145), +10.7%, +200 units, but the 2nd half made only +4.5% (about 1.4 standard errors).

**Decision:** nothing proven at BSP. Neither rule goes on the card. The next step is a walk-forward of this search
(rules re-chosen each month on the months before, bet the month after), so the two rules have to survive being chosen
fresh every month. Until then they are paper only.

## Test 41: where is the gap to BSP? (6 Nov 2026, gh topaz run 42205482534, `topaz_round25.py`)

The founder asked: "Can we find all the ways to use the data to get closer to BSP, see where we differ most." The
model is Test 39's I: the production inputs plus Isolynx and the checks, 2,352 rounds, 180 inputs, on the standard
split. It is scored on 22,747 races from 6 Jun 2024 with a BSP on every runner. Our log loss is 1.5795 and BSP's
1.4839, a **gap of +0.0956** (1st half +0.0881, 2nd +0.1031).

For each race the gap is measured on its winner: the log of BSP's chance for the winner, less the log of ours. The
mean over races is the gap above. Each slice reports its races, its mean gap, and its share of the whole gap. A slice
whose share of the gap is bigger than its share of races is where we lose most to BSP.

**How to read the price slices.** Slices cut by the winner's BSP, by our price or by the two together are cut on
what BSP said, and BSP is the better forecaster. So they show where the gap lands, not what causes it. Test 29 found
the model is not too flat (sharpening gained 0.0002). The slices cut on the race or the dog are the ones that point at
something to fix.

### The race

| track | races | share of races | mean gap | share of the whole gap |
|---|---|---|---|---|
| HVL | 1,818 | 8.0% | +0.1370 | 11.5% |
| WBL | 2,170 | 9.5% | +0.1145 | 11.4% |
| WGL | 2,350 | 10.3% | +0.0961 | 10.4% |
| BAL | 2,293 | 10.1% | +0.0982 | 10.4% |
| GEL | 2,354 | 10.3% | +0.0910 | 9.9% |
| BEN | 2,154 | 9.5% | +0.0967 | 9.6% |
| SHP | 1,951 | 8.6% | +0.0995 | 8.9% |
| SLE | 1,751 | 7.7% | +0.0926 | 7.5% |
| HOR | 1,310 | 5.8% | +0.0924 | 5.6% |
| MEP | 1,206 | 5.3% | +0.0858 | 4.8% |
| SAP | 1,091 | 4.8% | +0.0632 | 3.2% |
| SAN | 1,041 | 4.6% | +0.0645 | 3.1% |
| MEA | 844 | 3.7% | +0.0549 | 2.1% |
| TRA | 414 | 1.8% | +0.0964 | 1.8% |

| distance | races | share of races | mean gap | share of the whole gap |
|---|---|---|---|---|
| 420-519 m | 9,604 | 42.2% | +0.0906 | 40.0% |
| 350-419 m | 8,068 | 35.5% | +0.1010 | 37.5% |
| under 350 m | 2,057 | 9.0% | +0.1331 | 12.6% |
| 520-619 m | 2,646 | 11.6% | +0.0721 | 8.8% |
| 620 m+ | 372 | 1.6% | +0.0659 | 1.1% |

| grade | races | share of races | mean gap | share of the whole gap |
|---|---|---|---|---|
| 5 | 11,635 | 51.1% | +0.1038 | 55.5% |
| Maiden | 3,110 | 13.7% | +0.1121 | 16.0% |
| 7 | 2,934 | 12.9% | +0.0866 | 11.7% |
| 6 | 2,478 | 10.9% | +0.0874 | 10.0% |
| 4 | 1,780 | 7.8% | +0.0560 | 4.6% |
| 3 | 450 | 2.0% | +0.0467 | 1.0% |
| 1 | 208 | 0.9% | +0.0767 | 0.7% |
| 2 | 152 | 0.7% | +0.0696 | 0.5% |

| field size | races | share of races | mean gap | share of the whole gap |
|---|---|---|---|---|
| 7 | 8,251 | 36.3% | +0.1004 | 38.1% |
| 8 | 8,075 | 35.5% | +0.1007 | 37.4% |
| 6 | 4,600 | 20.2% | +0.0834 | 17.6% |
| 5 | 1,355 | 6.0% | +0.0909 | 5.7% |
| 9 | 216 | 0.9% | +0.1021 | 1.0% |
| 4 | 183 | 0.8% | +0.0122 | 0.1% |

**The start-time slice is wrong and is left out.** The run printed 18,924 races before 3pm, 408 from 6 to 9pm, 3,415
from 9pm on, and none from 3 to 6pm. A Victorian racing day does not look like that. The code read every start time as
UTC (`topaz_round12.tale_columns`). If Topaz writes Melbourne's clock with no zone, that puts each race 10 or 11 hours
late, and the printed shape is what you would see. Test 24's day/night split used the same column and is wrong for the
same reason (see the note there). The parse is fixed: a time without a zone is now read as Melbourne's clock. The next
run prints how many start times carry a zone and the races by hour, so the fix can be checked before the slice is used.

### The winner

| the winner's BSP | races | share of races | mean gap | share of the whole gap |
|---|---|---|---|---|
| $1-$2 | 3,644 | 16.0% | +0.2427 | 40.7% |
| $2-$3 | 4,610 | 20.3% | +0.2339 | 49.6% |
| $3-$5 | 6,051 | 26.6% | +0.1673 | 46.6% |
| $5-$8 | 3,716 | 16.3% | +0.0660 | 11.3% |
| $8-$15 | 2,860 | 12.6% | -0.1058 | -13.9% |
| $15+ | 1,866 | 8.2% | -0.3984 | -34.2% |

| the winner's price from us | races | share of races | mean gap | share of the whole gap |
|---|---|---|---|---|
| $1-$2 | 2,185 | 9.6% | +0.0337 | 3.4% |
| $2-$3 | 4,333 | 19.0% | +0.0464 | 9.2% |
| $3-$5 | 6,286 | 27.6% | +0.0881 | 25.5% |
| $5-$8 | 4,657 | 20.5% | +0.1153 | 24.7% |
| $8-$15 | 3,518 | 15.5% | +0.1585 | 25.6% |
| $15+ | 1,768 | 7.8% | +0.1422 | 11.6% |

| the winner: BSP over our price | races | share of races | mean gap | share of the whole gap |
|---|---|---|---|---|
| BSP under half our price | 1,544 | 6.8% | +0.9234 | 65.6% |
| BSP 0.5-0.8x ours | 6,777 | 29.8% | +0.4102 | 127.9% |
| within 25% | 10,027 | 44.1% | +0.0223 | 10.3% |
| BSP 1.25-2x ours | 3,542 | 15.6% | -0.4024 | -65.6% |
| BSP over 2x ours | 857 | 3.8% | -0.9682 | -38.2% |

| the winner's starts before | races | share of races | mean gap | share of the whole gap |
|---|---|---|---|---|
| debut | 551 | 2.4% | +0.1625 | 4.1% |
| 1-3 starts | 1,850 | 8.1% | +0.1052 | 9.0% |
| 4-10 | 4,155 | 18.3% | +0.0979 | 18.7% |
| 11-30 | 7,536 | 33.1% | +0.0933 | 32.3% |
| 31+ | 8,655 | 38.0% | +0.0901 | 35.9% |

| days since the winner's last start | races | share of races | mean gap | share of the whole gap |
|---|---|---|---|---|
| up to 4 days | 3,508 | 15.4% | +0.0980 | 15.8% |
| 5-8 | 12,088 | 53.1% | +0.0906 | 50.4% |
| 9-15 | 3,924 | 17.3% | +0.0885 | 16.0% |
| 16-29 | 1,442 | 6.3% | +0.1044 | 6.9% |
| 30-60 | 742 | 3.3% | +0.0975 | 3.3% |
| 61+ | 492 | 2.2% | +0.1529 | 3.5% |

| the winner's box | races | share of races | mean gap | share of the whole gap |
|---|---|---|---|---|
| 8 | 3,173 | 13.9% | +0.1215 | 17.7% |
| 7 | 2,732 | 12.0% | +0.1370 | 17.2% |
| 1 | 3,992 | 17.5% | +0.0857 | 15.7% |
| 6 | 2,297 | 10.1% | +0.1149 | 12.1% |
| 4 | 2,850 | 12.5% | +0.0797 | 10.5% |
| 2 | 3,394 | 14.9% | +0.0663 | 10.3% |
| 3 | 2,462 | 10.8% | +0.0817 | 9.3% |
| 5 | 1,847 | 8.1% | +0.0839 | 7.1% |

| GRV's tip for the winner | races | share of races | mean gap | share of the whole gap |
|---|---|---|---|---|
| not tipped | 4,581 | 20.1% | +0.1642 | 34.6% |
| 4 | 2,582 | 11.4% | +0.1538 | 18.3% |
| 1 | 7,576 | 33.3% | +0.0483 | 16.8% |
| 3 | 3,448 | 15.2% | +0.1038 | 16.5% |
| 2 | 4,560 | 20.0% | +0.0658 | 13.8% |

| tracking | races | share of races | mean gap | share of the whole gap |
|---|---|---|---|---|
| a tracked run before | 15,625 | 68.7% | +0.0787 | 56.5% |
| no tracked run | 7,122 | 31.3% | +0.1326 | 43.5% |

| the winner's last tracked run | races | share of races | mean gap | share of the whole gap |
|---|---|---|---|---|
| no tracked run | 7,122 | 31.3% | +0.1326 | 43.5% |
| checked last time | 7,363 | 32.4% | +0.0996 | 33.7% |
| clean last time | 8,262 | 36.3% | +0.0600 | 22.8% |

| the winner at this track | races | share of races | mean gap | share of the whole gap |
|---|---|---|---|---|
| raced here before | 18,480 | 81.2% | +0.0973 | 82.7% |
| first time here | 4,267 | 18.8% | +0.0881 | 17.3% |

| how far the winner firmed before the off (longest price traded over BSP) | races | share of races | mean gap | share of the whole gap |
|---|---|---|---|---|
| firmed under 1.1x | 6,837 | 30.1% | -0.0065 | -2.1% |
| 1.1-1.3x | 9,412 | 41.4% | +0.1116 | 48.3% |
| 1.3-1.6x | 4,534 | 19.9% | +0.1724 | 36.0% |
| 1.6-2.2x | 1,577 | 6.9% | +0.2038 | 14.8% |
| firmed 2.2x+ | 368 | 1.6% | +0.1677 | 2.8% |

### Runner by runner: when we differ from BSP, who is right?

| runner: BSP over our price | runners | wins | A/E vs ours | A/E vs BSP |
|---|---|---|---|---|
| BSP under half our price | 7,017 | 1,544 | 2.513 | 1.020 |
| BSP 0.5-0.8x ours | 29,743 | 6,777 | 1.490 | 0.999 |
| within 25% | 52,910 | 10,027 | 1.008 | 0.994 |
| BSP 1.25-2x ours | 39,805 | 3,542 | 0.673 | 1.014 |
| BSP over 2x ours | 30,602 | 857 | 0.362 | 0.991 |

When we differ from BSP, BSP is right every time. Its A/E is 0.991 to 1.020 in every band, while ours runs from 0.36
to 2.51. This is Tests 39 and 40 again from the other side: there is no kind of runner where our price beats BSP's.

### What the map says, biggest first

Ranked by how far each slice's share of the gap runs above its share of races:

1. **The late money.** The winners that firmed by 10% or more before the off are 69.8% of races and carry all of the
   gap (101.9%). Where the winner did not firm (30.1% of races), we are level with BSP: -0.0065. The gap is not form
   we read wrongly. It is information that reaches the market in the last part of the betting, and none of our inputs
   carries it.
2. **Winners GRV did not tip:** 34.6% of the gap on 20.1% of races (+0.1642, against +0.0483 when GRV tipped the
   winner first). The market knows which untipped dogs are live, and we do not.
3. **No tracked run:** 43.5% of the gap on 31.3% of races (+0.1326 against +0.0787 with one). The gap is about 40% smaller
   where the winner had a tracked run (partly because tracking is at the bigger tracks).
4. **Wide boxes 6 to 8:** 47.0% of the gap on 36.0% of races (+0.1149 to +0.1370, against +0.0663 to +0.0857 in boxes
   1 to 5). The market knows more than we do about which wide dogs can win from there.
5. **Grade 5 and maidens:** 71.5% of the gap on 64.8% of races. The metro tracks (SAN, SAP, MEA, MEP) are the
   reverse: 13.2% of the gap on 18.4% of races.
6. **Healesville and the sprints:** HVL alone is 11.5% of the gap on 8.0% of races (+0.1370), and races under 350 m are
   12.6% on 9.0% (+0.1331). Healesville is a straight track. WBL is next (+0.1145).
7. **Checked last time** (+0.0996) against clean (+0.0600) among winners with a tracked run: our check inputs (Test 35)
   still under-credit a dog that was checked.
8. **Small slices:** debutants (+0.1625, 4.1% of the gap on 2.4% of races), and a return after 61+ days (+0.1529, 3.5%
   on 2.2%). First time at the track makes no difference (+0.0881 against +0.0973).

### The plan, in the order the gap is

1. **The late money is the gap, so the only cure is data that sees it before we bet.** Three sources:
   - a market price at bet time as an input: the TAB open, or an early Betfair price. The history is waiting on
     BetMatic, Betwatch or our own nightly snapshots.
   - trial results, which is where kennels show what they know. The email to Jason is drafted.
   - Isolynx in production (item 3).
   This is the biggest lever, and the one we cannot pull from the data we hold.
2. **The tip slice:** test whether the model leans on GRV's tips too hard. Refit without the tip inputs and compare the
   gap on untipped winners.
3. **Tracking:** Isolynx into the weekly train and the nightly card (already on the build list), and a count of which
   tracks and months it misses.
4. **Wide boxes, Healesville and the sprints:** box bias by track and distance from earlier days. Test 33's
   `trk_inside` is in the walk-forward still running (WALK_TRACK, run 42182824738). A per-box win rate by track and
   distance, and a straight-track input, come next.
5. **Checks:** a time-lost-to-the-check input (the Isolynx dip and positions lost, as a size, not a yes/no).

## Test 42: the rule search at BSP, re-chosen every month (6 Nov 2026, gh topaz run 42206655423, `topaz_round26.py`)

Test 40's next step: re-choose the rule search every month, so the two paper rules only count if the search keeps
finding them.
- One model (I, 2,352 rounds, 180 inputs) is fitted on races before 6 Dec 2023 and never refitted.
- For each month from June 2024 to October 2026 (29 months), the rules are chosen on the six months before it: Test
  40's segments x BSP bands x back or lay x 1.1, 1.3 or 1.6, with 200+ bets and a profit there.
- The month is then bet two ways. "Every chosen rule" bets each runner once per side, however many rules pick it.
  "The best rule alone" bets only the rule with the highest ROI in the window.
- Flat 1 unit at BSP, 8% commission on winnings (the founder's rate, confirmed 6 Nov).

| month | rules chosen | best rule (bets, ROI on the 6 months) | every rule: bets, ROI | best rule: bets, ROI | cumulative units, every / best |
|---|---|---|---|---|---|
| 2024-06 | 30 | back backing up within 4 days, $15-$30, 1.6x (336, +38%) | 1,277, +11.6% | 39, +52.4% | +149 / +20 |
| 2024-07 | 36 | back backing up within 4 days, $15-$30, 1.6x (337, +55%) | 1,762, -8.6% | 74, -42.4% | -4 / -11 |
| 2024-08 | 40 | back backing up within 4 days, $8-$15, 1.6x (211, +50%) | 2,171, -4.7% | 32, +16.8% | -106 / -6 |
| 2024-09 | 46 | back backing up within 4 days, $8-$15, 1.6x (200, +55%) | 2,205, -12.2% | 27, +11.3% | -374 / -2 |
| 2024-10 | 46 | back backing up within 4 days, $8-$15, 1.6x (200, +65%) | 2,397, -2.9% | 32, -100.0% | -443 / -34 |
| 2024-11 | 52 | back first time at the track, $15-$30, 1.6x (307, +31%) | 2,243, +13.4% | 59, -54.5% | -143 / -67 |
| 2024-12 | 45 | back checked last tracked run, $8-$15, 1.6x (403, +34%) | 1,839, +5.1% | 56, -16.2% | -50 / -76 |
| 2025-01 | 47 | lay checked last tracked run, $15-$30, 1.3x (269, +59%) | 2,233, +3.6% | 56, -10.1% | +31 / -81 |
| 2025-02 | 51 | back backing up within 4 days, $15-$30, 1.6x (325, +49%) | 1,732, -1.8% | 62, +109.6% | +0 / -13 |
| 2025-03 | 61 | back backing up within 4 days, $15-$30, 1.6x (322, +49%) | 2,618, -5.7% | 67, -7.0% | -150 / -18 |
| 2025-04 | 57 | back checked last tracked run, $15-$30, 1.6x (619, +68%) | 2,386, -11.3% | 91, -57.8% | -419 / -71 |
| 2025-05 | 56 | back checked last tracked run, $15-$30, 1.6x (615, +56%) | 2,496, -4.9% | 115, -70.3% | -541 / -152 |
| 2025-06 | 50 | back backing up within 4 days, $15-$30, 1.6x (352, +41%) | 1,971, -6.0% | 68, -76.9% | -659 / -204 |
| 2025-07 | 51 | lay clean last tracked run, $15-$30, 1.3x (250, +33%) | 2,331, -11.8% | 35, +42.1% | -936 / -189 |
| 2025-08 | 46 | lay clean last tracked run, $15-$30, 1.3x (247, +32%) | 1,864, -11.8% | 24, +12.8% | -1,156 / -186 |
| 2025-09 | 37 | back checked last tracked run, $8-$15, 1.6x (356, +35%) | 1,614, -10.5% | 50, +40.8% | -1,325 / -166 |
| 2025-10 | 43 | back checked last tracked run, $8-$15, 1.6x (349, +49%) | 1,953, -7.9% | 59, -18.5% | -1,480 / -177 |
| 2025-11 | 38 | back checked last tracked run, $8-$15, 1.6x (339, +39%) | 1,434, -10.1% | 35, -100.0% | -1,625 / -212 |
| 2025-12 | 32 | lay checked last tracked run, $8-$15, 1.6x (239, +24%) | 1,454, -3.8% | 43, +8.9% | -1,680 / -208 |
| 2026-01 | 32 | back backing up within 4 days, $15-$30, 1.6x (391, +46%) | 1,796, -17.1% | 62, +23.2% | -1,988 / -193 |
| 2026-02 | 24 | back backing up within 4 days, $15-$30, 1.6x (385, +50%) | 1,027, -27.8% | 67, -62.9% | -2,273 / -236 |
| 2026-03 | 21 | back backing up within 4 days, $15-$30, 1.6x (392, +38%) | 1,040, -10.9% | 66, -60.8% | -2,386 / -276 |
| 2026-04 | 20 | back first time at the track, $15-$30, 1.6x (266, +38%) | 890, -3.0% | 37, -62.5% | -2,413 / -299 |
| 2026-05 | 31 | lay boxes 7-8, $8-$15, 1.6x (201, +39%) | 1,477, -9.4% | 29, +29.0% | -2,551 / -290 |
| 2026-06 | 36 | back first time at the track, $15-$30, 1.6x (292, +25%) | 1,685, +4.4% | 64, -20.6% | -2,476 / -304 |
| 2026-07 | 39 | back boxes 1-2, $8-$15, 1.6x (471, +32%) | 2,025, -5.8% | 96, -5.0% | -2,594 / -308 |
| 2026-08 | 42 | back boxes 1-2, $8-$15, 1.6x (493, +36%) | 1,912, -9.4% | 71, +47.4% | -2,774 / -275 |
| 2026-09 | 44 | back boxes 1-2, $8-$15, 1.6x (489, +43%) | 2,100, -15.6% | 91, -12.6% | -3,101 / -286 |
| 2026-10 | 44 | back checked last tracked run, $8-$15, 1.6x (420, +45%) | 2,067, -7.8% | 80, +18.9% | -3,262 / -271 |

| bets | half | bets | back winners | A/E vs BSP (backs) | flat ROI | units | months in profit |
|---|---|---|---|---|---|---|---|
| every chosen rule | 1st | 26,905 (16,134 backs) | 1,596 | 1.043 | -2.2% | -601 | 4 of 13 |
| every chosen rule | 2nd | 27,094 (13,512 backs) | 1,566 | 0.988 | -9.8% | -2,661 | 1 of 17 |
| every chosen rule | all | 53,999 (29,646 backs) | 3,162 | 1.015 | -6.0% | -3,262 | 5 of 29 |
| the best rule alone | 1st | 843 (728 backs) | 30 | 0.731 | -22.8% | -192 | 6 of 16 |
| the best rule alone | 2nd | 844 (772 backs) | 56 | 0.967 | -9.4% | -79 | 6 of 14 |
| the best rule alone | all | 1,687 (1,500 backs) | 86 | 0.869 | -16.1% | -271 | 12 of 29 |

Test 40's two paper rules were among those chosen in most months: back boxes 1-2 at $8-$15 at 1.6x in 23 of 29, and
back a dog backing up within 4 days at $15-$30 at 1.6x in 22 of 29.

**The search loses when it is re-run every month.** Betting every rule it chooses lost 6.0% on 53,999 bets. It lost in
both halves (-2.2% and -9.8%), and 24 of 29 months lost. Betting only the best rule lost 16.1%. The backs it chooses
win about as often as BSP says (A/E 1.015), and commission takes the rest. In most months the best rule had made
+24% to +68% on the six months before, and it lost in 17 of the 29 months after.

**The two paper rules do not survive as an edge.** The search keeps finding them, but each month it chooses 20 to 61
rules, and most of the others that look as good lose. So "it made money on the months before" does not pick a winner. When the
backing-up rule was the single best rule (8 months), it lost in 5 of them. When boxes 1-2 at $8-$15 was (3 months), it
lost in 2.

This run gives the two rules no fresh evidence for or against. Over these 29 months they made Test 40's +11.5% and
+10.7%, on the same model and the same months, so the only fresh test left is months that have not happened yet.

**Decision:** stop searching for rules at BSP. Rounds 23, 24 and 26 (Tests 39, 40 and 42) all say the same thing: at
BSP, after 8% commission, the model has nothing to add. The two rules can be logged on paper from tonight at no cost
(about 70 bets a month each), and a year of that is about 800 bets each, enough to see a +10% edge only roughly. The
model's edge is at TAB before the late money arrives, and Test 41 says that late money is exactly where BSP beats us.

## Test 43: the walk-forward, track character (6 Nov 2026, gh topaz run 42182824738, `topaz_walk.py`, `WALK_TRACK=yes`)

Test 33's open item. On one split, track character and each dog's form at the same kind of track scored 1.5794, inside
one seed's noise. This is the same question month by month, with the production inputs as Test 37.

The added inputs:
- the track and distance's leader-win, closer-win, winning-margin and inside-box shares, from earlier days
- each dog's record against the market at speed tracks and at the rest, with a speed track fixed at the leader winning
  50% or more

The extra inputs slowed the refits, so the time guard stopped them after April 2026. The run scores 29 months (December
2023 to April 2026) and bets 23 (June 2024 to April 2026), against Test 37's 31 and 25. The log-loss comparison below
is over the months both runs have, which hold the same races and the same BSP-matched races month by month.

| months both runs score | months | races | BSP-matched | model, Test 37 | model, track character | gap to BSP, Test 37 | gap to BSP, track character |
|---|---|---|---|---|---|---|---|
| all, Dec 2023 to Apr 2026 | 29 | 25,071 | 21,944 | 1.6150 | **1.6131** | +0.0869 | **+0.0853** |
| 1st half, Dec 2023 to Jan 2025 | 14 | 11,844 | 10,038 | 1.6338 | **1.6326** | +0.0886 | **+0.0878** |
| 2nd half, Feb 2025 to Apr 2026 | 15 | 13,227 | 11,906 | 1.5982 | **1.5956** | +0.0855 | **+0.0833** |
| the bet months, Jun 2024 to Apr 2026 | 23 | 20,186 | 17,697 | 1.6126 | **1.6103** | +0.0856 | **+0.0836** |

The gap is smaller in 21 of the 29 months, larger in 7 and equal in one:
- larger: 2024-02, 2024-03, 2024-04, 2024-05, 2024-08, 2025-06 and 2026-04, each by 0.0002 to 0.0020
- the biggest gains: 2025-02 (-0.0088), 2024-12 (-0.0076), 2025-11 and 2026-01 (-0.0054 each)

Over its own scored span (20,186 races), the run scored model 1.6103, ensemble 1.5965 and GRV's SP 1.6099. On the 17,697
BSP-matched races: model 1.5730, BSP 1.4894, gap +0.0836.

The 1.3x rule at GRV's SP (our price $2-$15, Kelly x75 cap 4, no commission). Blend weights refitted each month: ours
0.50-0.64, the SP 0.54-0.68. The comparison with Test 37 is not like for like: this run's 23 months against Test 37's
25, which include May and June 2026.

| run | rule | half | bets | winners | A/E | flat ROI | units staked | Kelly ROI | units won | worst drawdown | months in profit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| track character (23 months) | no guard | 1st | 1,143 | 252 | 1.410 | +47.9% | 2,272 | +52.3% | +1,188 | 59 | 11 of 13 |
| track character (23 months) | no guard | 2nd | 1,151 | 284 | 1.614 | +64.4% | 2,155 | +75.4% | +1,626 | 48 | 11 of 11 |
| track character (23 months) | no guard | all | 2,294 | 536 | 1.511 | +56.2% | 4,427 | +63.6% | +2,813 | 59 | 22 of 23 |
| track character (23 months) | drift guard 1.3x | 1st | 763 | 200 | 1.547 | +65.9% | 1,667 | +69.6% | +1,161 | 53 | 11 of 12 |
| track character (23 months) | drift guard 1.3x | 2nd | 770 | 241 | 1.866 | +101.0% | 1,599 | +105.5% | +1,686 | 46 | 12 of 12 |
| track character (23 months) | drift guard 1.3x | all | 1,533 | 441 | 1.707 | +83.6% | 3,266 | +87.2% | +2,847 | 53 | 22 of 23 |
| Test 37 (25 months) | no guard | all | 2,203 | 530 | 1.547 | +59.8% | 4,281 | +68.6% | +2,936 | 59 | 24 of 25 |
| Test 37 (25 months) | drift guard 1.3x | all | 1,476 | 429 | 1.721 | +85.4% | 3,148 | +90.7% | +2,856 | 42 | 25 of 25 |

With the drift guard, track character made 67 bets a month (1,533 in 23 months) against Test 37's 59, and 124 units a
month against 114. Its flat ROI is +83.6% against +85.4% and its Kelly ROI 87.2% against 90.7%. It is the same edge,
bet a little more often.

The other rules over the 23 months:
- **sequential at GRV's SP:** +50.0% flat on 1,486 bets, A/E 1.480, 20 of 23 months in profit (1st half +35.3%, 2nd
  +64.6%)
- **Test 12's rule at the SP:** +41.1% on 2,948
- **Test 13's rule at the SP:** +35.2% on 1,524
- **at BSP with 8% commission:** still nothing. Our weight in the blend is -0.08 to 0.08, the 1.3x rule made 5 bets,
  and the sequential rule lost 9.5% on 2,129 bets (7 of 23 months in profit)

**The walk-forward confirms Test 33.** Track character is closer to BSP in both halves and in 21 of 29 months. The gain
(0.0016 to 0.0020) is the same size as the half-weight label's (Test 38: 0.0016). Over its own span the model alone
all but matches GRV's SP (1.6103 against 1.6099).

**Decision:** in production. `WALK_TRACK=yes` goes into the weekly train and the nightly price run.
- **Saturday's card is safe.** The price run's `align` drops any input the saved model never saw, so the old model
  prices exactly as before until Sunday's train fits the new one.
- **The price path is checked.** A smoke test built the inputs on a day with no results (synthetic data, the price
  run's `keep_unresulted` path): every track column filled, with no errors.
- **Not yet tested together.** The half weight (Test 38) and track character are separate changes, each walked forward
  on its own. A walk-forward with both is running, to read before Sunday's train.

## Test 44: the walk-forward, the half weight and track character together (7 Nov 2026, gh topaz run 42220952771, `topaz_walk.py`, `WALK_SP_WEIGHT=0.5 WALK_TRACK=yes`)

Tests 38 and 43 each walked one change forward on its own, and each moved the gap to BSP by about 0.0016. Both went
into production on 6 Nov, for Sunday's train. This run checks the two together, with everything else as Test 37.

It is the slowest run yet. The time guard stopped the refits after December 2025, so it scores 25 months (December 2023
to December 2025) and bets 19 (June 2024 to December 2025). All four runs below score those 25 months, on the same
races and the same BSP-matched races month by month. The comparison is over those months only.

| window | months | races | BSP-matched | gap, Test 37 | gap, half weight | gap, track | gap, both | both less Test 37 | both less half weight | both less track |
|---|---|---|---|---|---|---|---|---|---|---|
| all | 25 | 21,418 | 18,469 | +0.0855 | +0.0841 | +0.0841 | **+0.0836** | -0.0019 | -0.0005 | -0.0005 |
| 1st half, Dec 2023 to Dec 2024 | 13 | 10,916 | 9,207 | +0.0882 | +0.0874 | +0.0876 | **+0.0866** | -0.0016 | -0.0008 | -0.0010 |
| 2nd half, Jan to Dec 2025 | 12 | 10,502 | 9,262 | +0.0829 | +0.0808 | +0.0806 | **+0.0806** | -0.0023 | -0.0002 | -0.0000 |
| the bet months, Jun 2024 to Dec 2025 | 19 | 16,533 | 14,222 | +0.0835 | +0.0818 | +0.0816 | **+0.0809** | -0.0026 | -0.0010 | -0.0007 |

| window | model, Test 37 | model, half weight | model, track | model, both | ensemble, Test 37 | ensemble, half weight | ensemble, track | ensemble, both |
|---|---|---|---|---|---|---|---|---|
| all 25 months | 1.6207 | 1.6183 | 1.6190 | **1.6176** | 1.6037 | **1.6027** | 1.6036 | 1.6032 |
| 1st half | 1.6354 | 1.6336 | 1.6342 | **1.6323** | 1.6172 | **1.6166** | 1.6174 | 1.6167 |
| 2nd half | 1.6055 | **1.6023** | 1.6032 | 1.6024 | 1.5897 | **1.5882** | 1.5893 | 1.5892 |
| the bet months | 1.6195 | 1.6166 | 1.6174 | **1.6157** | 1.6009 | **1.5997** | 1.6007 | 1.6002 |

Month by month, with both changes the gap is smaller than Test 37's in 18 of 25 months, than the half weight's in 16
(one tie), and than track character's in 12:

| month | Test 37 | half weight | track | both |
|---|---|---|---|---|
| 2023-12 | +0.0864 | +0.0873 | +0.0859 | +0.0870 |
| 2024-01 | +0.1086 | +0.1055 | +0.1061 | +0.1050 |
| 2024-02 | +0.1044 | +0.1038 | +0.1064 | +0.1068 |
| 2024-03 | +0.0912 | +0.0907 | +0.0920 | +0.0931 |
| 2024-04 | +0.0911 | +0.0883 | +0.0913 | +0.0919 |
| 2024-05 | +0.0731 | +0.0755 | +0.0750 | +0.0740 |
| 2024-06 | +0.0893 | +0.0874 | +0.0889 | +0.0874 |
| 2024-07 | +0.0788 | +0.0779 | +0.0774 | +0.0741 |
| 2024-08 | +0.0855 | +0.0879 | +0.0866 | +0.0798 |
| 2024-09 | +0.1030 | +0.1023 | +0.1012 | +0.1018 |
| 2024-10 | +0.1019 | +0.0988 | +0.1016 | +0.0984 |
| 2024-11 | +0.0630 | +0.0653 | +0.0630 | +0.0636 |
| 2024-12 | +0.0681 | +0.0632 | +0.0605 | +0.0609 |
| 2025-01 | +0.0924 | +0.0898 | +0.0899 | +0.0913 |
| 2025-02 | +0.0873 | +0.0852 | +0.0785 | +0.0813 |
| 2025-03 | +0.1060 | +0.1072 | +0.1052 | +0.1054 |
| 2025-04 | +0.0791 | +0.0793 | +0.0789 | +0.0763 |
| 2025-05 | +0.0619 | +0.0577 | +0.0616 | +0.0580 |
| 2025-06 | +0.0696 | +0.0690 | +0.0705 | +0.0684 |
| 2025-07 | +0.0743 | +0.0682 | +0.0700 | +0.0752 |
| 2025-08 | +0.0865 | +0.0841 | +0.0832 | +0.0851 |
| 2025-09 | +0.0712 | +0.0717 | +0.0708 | +0.0693 |
| 2025-10 | +0.0855 | +0.0831 | +0.0843 | +0.0828 |
| 2025-11 | +0.0978 | +0.0926 | +0.0924 | +0.0934 |
| 2025-12 | +0.0821 | +0.0805 | +0.0807 | +0.0793 |

Over its own scored span (16,533 races, June 2024 to December 2025), the run scored model 1.6157, ensemble 1.6002 and
GRV's SP 1.6221. On the 14,222 BSP-matched races: model 1.5749, BSP 1.4940, gap +0.0809.

The 1.3x rule at GRV's SP over its 19 bet months (our price $2-$15, Kelly x75 cap 4, no commission). The other runs bet
23 or 25 months that run into 2026, so this is not a like-for-like comparison of the rule.

| ours | rule | half | bets | winners | A/E | flat ROI | units staked | Kelly ROI | units won | worst drawdown | months in profit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| the model (0.50-0.65 / SP 0.54-0.67) | no guard | 1st | 978 | 200 | 1.325 | +36.8% | 1,954 | +47.0% | +919 | 62 | 9 of 9 |
| the model | no guard | 2nd | 981 | 254 | 1.674 | +71.3% | 1,892 | +77.8% | +1,472 | 68 | 10 of 11 |
| the model | no guard | all | 1,959 | 454 | 1.500 | +54.1% | 3,846 | +62.2% | +2,391 | 68 | 18 of 19 |
| the model | drift guard 1.3x | 1st | 665 | 158 | 1.430 | +55.1% | 1,455 | +60.5% | +880 | 34 | 9 of 9 |
| the model | drift guard 1.3x | 2nd | 670 | 207 | 1.857 | +102.0% | 1,407 | +99.5% | +1,400 | 52 | 10 of 11 |
| the model | drift guard 1.3x | all | 1,335 | 365 | 1.645 | +78.6% | 2,862 | +79.7% | +2,280 | 52 | 18 of 19 |
| the ensemble (0.52-0.67 / SP 0.49-0.63) | no guard | 1st | 1,504 | 302 | 1.360 | +41.8% | 2,888 | +45.5% | +1,313 | 63 | 9 of 9 |
| the ensemble | no guard | 2nd | 1,507 | 357 | 1.610 | +67.5% | 2,744 | +74.5% | +2,043 | 40 | 11 of 11 |
| the ensemble | no guard | all | 3,011 | 659 | 1.485 | +54.7% | 5,632 | +59.6% | +3,356 | 63 | 19 of 19 |
| the ensemble | drift guard 1.3x | 1st | 1,008 | 235 | 1.447 | +56.4% | 2,117 | +55.9% | +1,183 | 45 | 9 of 9 |
| the ensemble | drift guard 1.3x | 2nd | 1,009 | 286 | 1.799 | +98.7% | 1,953 | +99.1% | +1,935 | 41 | 11 of 11 |
| the ensemble | drift guard 1.3x | all | 2,017 | 521 | 1.621 | +77.5% | 4,070 | +76.6% | +3,118 | 45 | 19 of 19 |

The other rules over the 19 months:
- **sequential at GRV's SP:** +50.1% flat on 1,397 bets, A/E 1.479, 18 of 19 months in profit (1st half +19.7%, 2nd
  +80.4%)
- **sequential at BSP with 8% commission:** +3.5% on 1,321 bets, A/E 1.090, 11 of 19 months (1st half -5.9%, 2nd
  +12.8%). Tests 38, 42 and 43 all lost at BSP, so this is not an edge.
- **the 1.3x rule at BSP:** 5 bets, with our weight in the blend at -0.07 to 0.08

**Together is better than either alone, but only just.**
- With both changes the gap is the smallest in every window: -0.0019 against Test 37 over the 25 months, -0.0026 over
  the bet months.
- Against each change alone, the pair gains only 0.0005. Two changes worth about 0.0014 each are worth 0.0019 together,
  so they overlap.
- Month by month the pair beats track character alone in only 12 of 25. Most of what it adds over track character
  comes from four months: 2024-07, 2024-08, 2024-10 and 2025-05, worth 0.0026 to 0.0068 each.
- Neither change hurts the other. On the gap to BSP, the pair is at least as good as each alone in every window, and it
  ties track character in the 2nd half. On log loss, the half weight alone edges it in the 2nd half (1.6023 against
  1.6024) and on the ensemble (1.6027 against 1.6032 over the 25 months), by less than one seed's noise.

**Decision:** both stay in production as they are. Sunday's train fits the model with the half-weight label and track
character. Nothing in `gh-topaz-nightly.yml` changes.

**The next walk-forwards need fewer refits.** Each new input slows the monthly refits, and this run reached only
December 2025. Refitting every second month (`WALK_REFIT_EVERY=2`, as Test 27 did) would cover the whole of 2026.

## Test 45: lay the dogs the market dislikes, at BSP (7 Nov 2026, gh topaz run 42287437174, `topaz_round27.py`)

The founder: "when we rate a horse between $7-$15 and it starts $15-$40 with a 1.5x bigger price than us. The market
knows something we don't, it's right not us. So if we lay those horses we make money at bsp." Test 34 tried that rule
on the dogs at BSP $15-$40, with BSP at least 1.6x our price: A/E 0.930, -2.5% after commission, a loss in both halves.
This round looks for where the market's dislike is strongest:
- **BSP bands:** $8-$15, $15-$40, $40-$100.
- **How far BSP is above our price:** 1.6x, 2x, 2.5x, 3x.
- **Groups:**
  - all runners
  - no tracked run, and a tracked run before
  - not tipped by GRV
  - boxes 7-8
  - drifted 1.3x or more from its shortest pre-play price, and did not drift. Both are known only near the off.
- **The lay:** 1 unit at BSP, 8% commission. A loser keeps 0.92 and a winner costs BSP - 1. No first starters.

The model is the one from Tests 39 to 42, on the standard split: it prices the early-stopping months and the scored
quarter from 6 Jun 2024. A rule is "chosen" if it made 200+ lays and a profit on the early-stopping months. A lay pays
only when its A/E against BSP is under the break-even A/E, shown in brackets. Returns are per lay, per unit of the
backer's stake. A $40-$100 lay risks $39 to $99 to win 92c.

| lay at BSP | early-stopping: lays, A/E, return | 1st half: lays, A/E, return | 2nd half: lays, A/E, return | all: lays, winners, A/E (break-even), return, units |
|---|---|---|---|---|
| all runners, BSP $8-$15, BSP >= 1.6x ours | 1,155, 1.061, -13.8% | 2,999, 1.128, -20.4% | 3,372, 1.055, -14.8% | 6,371, 622, 1.089 (0.927), -17.5%, -1,112 |
| all runners, BSP $8-$15, BSP >= 2x ours | 433, 0.944, -2.6% | 1,138, 1.178, -25.6% | 1,403, 0.986, -9.2% | 2,541, 239, 1.072 (0.927), -16.5%, -420 |
| all runners, BSP $8-$15, BSP >= 2.5x ours | 129, 1.182, -24.5% | 317, 1.109, -18.7% | 467, 0.822, +10.6% | 784, 63, 0.937 (0.927), -1.3%, -10 |
| all runners, BSP $8-$15, BSP >= 3x ours | 22, 1.645, -77.5% | 87, 0.831, +15.8% | 148, 0.869, +5.7% | 235, 17, 0.855 (0.926), +9.5%, +22 **both halves** |
| all runners, BSP $15-$40, BSP >= 1.6x ours | 2,926, 0.952, -3.6% | 7,572, 0.949, -2.3% | 8,160, 0.973, -5.9% | 15,732, 635, 0.961 (0.923), -4.2%, -655 |
| all runners, BSP $15-$40, BSP >= 2x ours | 1,610, 0.904, -1.9% | 4,299, 0.972, -3.3% | 4,919, 0.856, +4.7% | 9,218, 343, 0.910 (0.923), +0.9%, +87 |
| all runners, BSP $15-$40, BSP >= 2.5x ours | 707, 0.925, -5.2% | 2,039, 1.037, -9.8% | 2,578, 1.025, -11.5% | 4,617, 187, 1.030 (0.923), -10.7%, -496 |
| all runners, BSP $15-$40, BSP >= 3x ours | 303, 0.603, +32.7% | 908, 1.175, -28.1% | 1,319, 1.139, -25.1% | 2,227, 97, 1.154 (0.923), -26.4%, -587 **chosen** |
| all runners, BSP $40-$100, BSP >= 1.6x ours | 2,046, 1.046, -11.1% | 5,692, 0.960, -4.8% | 6,715, 0.982, -7.6% | 12,407, 204, 0.972 (0.921), -6.3%, -784 |
| all runners, BSP $40-$100, BSP >= 2x ours | 1,460, 1.288, -33.1% | 4,147, 0.880, +5.5% | 5,163, 0.965, -5.7% | 9,310, 144, 0.927 (0.921), -0.7%, -64 |
| all runners, BSP $40-$100, BSP >= 2.5x ours | 903, 1.376, -40.8% | 2,719, 0.853, +8.9% | 3,516, 0.970, -4.9% | 6,235, 94, 0.919 (0.921), +1.2%, +72 |
| all runners, BSP $40-$100, BSP >= 3x ours | 554, 1.496, -51.0% | 1,734, 0.791, +11.8% | 2,301, 0.803, +13.3% | 4,035, 52, 0.798 (0.921), +12.6%, +510 **both halves** |
| no tracked run, BSP $8-$15, BSP >= 1.6x ours | 404, 1.004, -13.0% | 813, 1.159, -23.7% | 859, 1.003, -9.6% | 1,672, 161, 1.079 (0.927), -16.5%, -275 |
| no tracked run, BSP $8-$15, BSP >= 2x ours | 138, 0.827, +10.6% | 258, 1.289, -37.9% | 335, 0.993, -10.1% | 593, 58, 1.122 (0.927), -22.2%, -131 |
| no tracked run, BSP $8-$15, BSP >= 2.5x ours | 43, 1.644, -65.5% | 55, 1.477, -61.9% | 97, 1.098, -12.8% | 152, 16, 1.237 (0.927), -30.6%, -46 |
| no tracked run, BSP $15-$40, BSP >= 1.6x ours | 1,137, 1.122, -20.4% | 2,253, 0.995, -7.5% | 2,190, 1.106, -24.7% | 4,443, 195, 1.049 (0.923), -15.9%, -708 |
| no tracked run, BSP $15-$40, BSP >= 2x ours | 626, 1.203, -34.8% | 1,208, 0.908, +2.1% | 1,256, 0.973, -11.1% | 2,464, 94, 0.941 (0.923), -4.6%, -114 |
| no tracked run, BSP $15-$40, BSP >= 2.5x ours | 269, 1.022, -11.1% | 553, 1.160, -26.3% | 647, 1.237, -30.4% | 1,200, 56, 1.201 (0.923), -28.5%, -342 |
| no tracked run, BSP $15-$40, BSP >= 3x ours | 124, 0.630, +28.0% | 225, 1.317, -49.3% | 340, 1.587, -64.1% | 565, 31, 1.480 (0.923), -58.2%, -329 |
| no tracked run, BSP $40-$100, BSP >= 1.6x ours | 849, 0.983, -10.4% | 1,771, 0.765, +14.1% | 1,809, 1.393, -54.7% | 3,580, 65, 1.080 (0.921), -20.7%, -740 |
| no tracked run, BSP $40-$100, BSP >= 2x ours | 603, 1.111, -21.9% | 1,241, 0.679, +26.7% | 1,339, 1.497, -68.4% | 2,580, 47, 1.101 (0.921), -22.7%, -585 |
| no tracked run, BSP $40-$100, BSP >= 2.5x ours | 360, 1.216, -34.2% | 749, 0.660, +31.6% | 905, 1.502, -63.1% | 1,654, 30, 1.121 (0.921), -20.2%, -335 |
| no tracked run, BSP $40-$100, BSP >= 3x ours | 208, 1.547, -75.5% | 451, 0.425, +54.9% | 564, 1.114, -18.5% | 1,015, 13, 0.810 (0.921), +14.1%, +143 |
| a tracked run before, BSP $8-$15, BSP >= 1.6x ours | 751, 1.091, -14.3% | 2,186, 1.116, -19.2% | 2,513, 1.072, -16.6% | 4,699, 461, 1.092 (0.927), -17.8%, -837 |
| a tracked run before, BSP $8-$15, BSP >= 2x ours | 295, 0.999, -8.7% | 880, 1.146, -22.0% | 1,068, 0.983, -8.9% | 1,948, 181, 1.056 (0.927), -14.8%, -289 |
| a tracked run before, BSP $8-$15, BSP >= 2.5x ours | 86, 0.952, -4.0% | 262, 1.031, -9.6% | 370, 0.751, +16.7% | 632, 47, 0.866 (0.927), +5.8%, +36 |
| a tracked run before, BSP $8-$15, BSP >= 3x ours | 14, 0.851, +3.0% | 71, 0.683, +32.0% | 117, 0.789, +14.0% | 188, 12, 0.750 (0.926), +20.8%, +39 **both halves** |
| a tracked run before, BSP $15-$40, BSP >= 1.6x ours | 1,789, 0.844, +7.0% | 5,319, 0.929, -0.1% | 5,970, 0.925, +1.0% | 11,289, 440, 0.927 (0.923), +0.5%, +53 **chosen** |
| a tracked run before, BSP $15-$40, BSP >= 2x ours | 984, 0.714, +19.1% | 3,091, 0.997, -5.4% | 3,663, 0.816, +10.1% | 6,754, 249, 0.899 (0.923), +3.0%, +202 **chosen** |
| a tracked run before, BSP $15-$40, BSP >= 2.5x ours | 438, 0.865, -1.6% | 1,486, 0.991, -3.6% | 1,931, 0.955, -5.2% | 3,417, 131, 0.971 (0.923), -4.5%, -154 |
| a tracked run before, BSP $15-$40, BSP >= 3x ours | 179, 0.585, +36.0% | 683, 1.129, -21.2% | 979, 0.989, -11.6% | 1,662, 66, 1.046 (0.923), -15.5%, -258 |
| a tracked run before, BSP $40-$100, BSP >= 1.6x ours | 1,197, 1.090, -11.6% | 3,921, 1.048, -13.3% | 4,906, 0.832, +9.7% | 8,827, 139, 0.929 (0.921), -0.5%, -45 |
| a tracked run before, BSP $40-$100, BSP >= 2x ours | 857, 1.412, -41.0% | 2,906, 0.965, -3.5% | 3,824, 0.782, +16.3% | 6,730, 97, 0.861 (0.921), +7.7%, +521 |
| a tracked run before, BSP $40-$100, BSP >= 2.5x ours | 543, 1.482, -45.2% | 1,970, 0.925, +0.3% | 2,611, 0.789, +15.3% | 4,581, 64, 0.847 (0.921), +8.9%, +407 **both halves** |
| a tracked run before, BSP $40-$100, BSP >= 3x ours | 346, 1.466, -36.3% | 1,283, 0.915, -3.3% | 1,737, 0.705, +23.6% | 3,020, 39, 0.794 (0.921), +12.1%, +366 |
| GRV did not tip it, BSP $8-$15, BSP >= 1.6x ours | 181, 0.663, +25.5% | 517, 1.366, -43.6% | 541, 1.055, -14.9% | 1,058, 109, 1.206 (0.927), -28.9%, -306 |
| GRV did not tip it, BSP $8-$15, BSP >= 2x ours | 47, 0.256, +63.4% | 147, 1.476, -52.3% | 146, 0.896, -2.3% | 293, 29, 1.185 (0.926), -27.4%, -80 |
| GRV did not tip it, BSP $15-$40, BSP >= 1.6x ours | 1,371, 0.961, -7.2% | 3,402, 0.991, -4.3% | 3,415, 1.142, -22.1% | 6,817, 285, 1.066 (0.923), -13.2%, -901 |
| GRV did not tip it, BSP $15-$40, BSP >= 2x ours | 637, 0.950, -12.0% | 1,688, 1.001, -3.7% | 1,717, 1.114, -18.3% | 3,405, 136, 1.058 (0.923), -11.1%, -377 |
| GRV did not tip it, BSP $15-$40, BSP >= 2.5x ours | 251, 1.089, -23.9% | 664, 1.129, -10.1% | 725, 1.458, -51.7% | 1,389, 65, 1.300 (0.923), -31.8%, -442 |
| GRV did not tip it, BSP $15-$40, BSP >= 3x ours | 84, 1.065, -16.4% | 256, 1.377, -35.2% | 314, 1.577, -72.0% | 570, 29, 1.487 (0.923), -55.5%, -316 |
| GRV did not tip it, BSP $40-$100, BSP >= 1.6x ours | 1,582, 1.035, -8.6% | 4,261, 0.972, -7.0% | 4,664, 0.956, -5.7% | 8,925, 142, 0.964 (0.921), -6.3%, -562 |
| GRV did not tip it, BSP $40-$100, BSP >= 2x ours | 1,077, 1.326, -34.7% | 2,956, 0.832, +9.6% | 3,374, 0.922, -2.7% | 6,330, 90, 0.880 (0.921), +3.0%, +190 |
| GRV did not tip it, BSP $40-$100, BSP >= 2.5x ours | 616, 1.452, -40.9% | 1,788, 0.779, +17.3% | 2,105, 0.877, +3.6% | 3,893, 51, 0.832 (0.921), +9.8%, +383 **both halves** |
| GRV did not tip it, BSP $40-$100, BSP >= 3x ours | 348, 1.522, -51.9% | 1,063, 0.850, +7.4% | 1,262, 0.771, +22.0% | 2,325, 29, 0.807 (0.921), +15.3%, +357 **both halves** |
| boxes 7-8, BSP $8-$15, BSP >= 1.6x ours | 299, 0.943, -6.9% | 687, 1.132, -22.3% | 878, 0.907, +1.3% | 1,565, 140, 1.006 (0.927), -9.0%, -141 |
| boxes 7-8, BSP $8-$15, BSP >= 2x ours | 102, 0.682, +22.3% | 264, 1.311, -41.4% | 367, 0.900, -2.5% | 631, 59, 1.071 (0.927), -18.8%, -119 |
| boxes 7-8, BSP $8-$15, BSP >= 2.5x ours | 26, 1.823, -99.7% | 63, 1.781, -91.9% | 120, 0.580, +29.1% | 183, 16, 1.003 (0.927), -12.6%, -23 |
| boxes 7-8, BSP $15-$40, BSP >= 1.6x ours | 787, 1.062, -19.6% | 1,897, 1.018, -10.6% | 2,183, 1.060, -14.5% | 4,080, 177, 1.041 (0.923), -12.7%, -519 |
| boxes 7-8, BSP $15-$40, BSP >= 2x ours | 422, 0.803, +1.1% | 1,044, 0.970, -4.9% | 1,303, 0.992, -11.7% | 2,347, 94, 0.982 (0.923), -8.7%, -204 **chosen** |
| boxes 7-8, BSP $15-$40, BSP >= 2.5x ours | 190, 0.794, -1.3% | 500, 0.977, -4.1% | 677, 1.187, -30.7% | 1,177, 51, 1.099 (0.923), -19.4%, -228 |
| boxes 7-8, BSP $15-$40, BSP >= 3x ours | 84, 0.642, +21.6% | 228, 1.288, -38.3% | 335, 1.532, -70.4% | 563, 31, 1.435 (0.923), -57.4%, -323 |
| boxes 7-8, BSP $40-$100, BSP >= 1.6x ours | 485, 0.880, +4.9% | 1,444, 1.023, -5.1% | 1,841, 1.058, -13.1% | 3,285, 58, 1.043 (0.921), -9.6%, -316 **chosen** |
| boxes 7-8, BSP $40-$100, BSP >= 2x ours | 341, 0.923, -3.8% | 1,034, 0.868, +10.9% | 1,400, 0.892, +5.0% | 2,434, 36, 0.882 (0.921), +7.5%, +183 **both halves** |
| boxes 7-8, BSP $40-$100, BSP >= 2.5x ours | 210, 1.222, -32.8% | 676, 0.815, +19.8% | 956, 0.817, +5.2% | 1,632, 22, 0.816 (0.921), +11.3%, +184 **both halves** |
| boxes 7-8, BSP $40-$100, BSP >= 3x ours | 134, 1.900, -103.5% | 437, 0.428, +49.1% | 606, 0.604, +31.2% | 1,043, 9, 0.532 (0.921), +38.7%, +404 **both halves** |
| drifted 1.3x+ (near the off), BSP $8-$15, BSP >= 1.6x ours | 623, 1.023, -9.6% | 1,562, 1.147, -22.5% | 1,862, 1.127, -21.9% | 3,424, 348, 1.136 (0.927), -22.2%, -760 |
| drifted 1.3x+ (near the off), BSP $8-$15, BSP >= 2x ours | 267, 1.025, -11.1% | 668, 1.322, -39.9% | 877, 1.010, -11.4% | 1,545, 155, 1.144 (0.927), -23.7%, -366 |
| drifted 1.3x+ (near the off), BSP $8-$15, BSP >= 2.5x ours | 92, 1.157, -24.1% | 200, 1.182, -23.1% | 336, 0.903, +3.1% | 536, 46, 1.006 (0.927), -6.7%, -36 |
| drifted 1.3x+ (near the off), BSP $8-$15, BSP >= 3x ours | 16, 2.277, -141.1% | 65, 1.109, -9.9% | 114, 1.044, -8.4% | 179, 16, 1.068 (0.926), -9.0%, -16 |
| drifted 1.3x+ (near the off), BSP $15-$40, BSP >= 1.6x ours | 1,598, 0.845, +6.5% | 4,522, 0.992, -7.5% | 5,237, 0.916, -1.5% | 9,759, 382, 0.951 (0.923), -4.3%, -417 **chosen** |
| drifted 1.3x+ (near the off), BSP $15-$40, BSP >= 2x ours | 944, 0.771, +12.6% | 2,751, 0.970, -4.4% | 3,406, 0.772, +13.5% | 6,157, 213, 0.860 (0.923), +5.5%, +338 **chosen** |
| drifted 1.3x+ (near the off), BSP $15-$40, BSP >= 2.5x ours | 453, 0.826, +8.9% | 1,395, 1.022, -12.3% | 1,901, 0.930, -1.7% | 3,296, 124, 0.969 (0.923), -6.2%, -205 **chosen** |
| drifted 1.3x+ (near the off), BSP $15-$40, BSP >= 3x ours | 204, 0.762, +19.6% | 660, 1.307, -42.9% | 1,010, 1.017, -13.1% | 1,670, 71, 1.130 (0.923), -24.9%, -416 **chosen** |
| drifted 1.3x+ (near the off), BSP $40-$100, BSP >= 1.6x ours | 1,343, 1.253, -31.3% | 4,348, 1.011, -11.2% | 5,143, 0.986, -9.1% | 9,491, 159, 0.997 (0.921), -10.1%, -955 |
| drifted 1.3x+ (near the off), BSP $40-$100, BSP >= 2x ours | 978, 1.440, -48.4% | 3,248, 0.893, +3.2% | 4,051, 0.968, -6.5% | 7,299, 113, 0.934 (0.921), -2.2%, -159 |
| drifted 1.3x+ (near the off), BSP $40-$100, BSP >= 2.5x ours | 618, 1.627, -61.9% | 2,203, 0.866, +8.1% | 2,839, 1.075, -15.8% | 5,042, 81, 0.984 (0.921), -5.4%, -272 |
| drifted 1.3x+ (near the off), BSP $40-$100, BSP >= 3x ours | 408, 1.566, -51.9% | 1,428, 0.748, +15.8% | 1,907, 0.907, +2.5% | 3,335, 45, 0.839 (0.921), +8.2%, +273 **both halves** |
| did not drift 1.3x, BSP $8-$15, BSP >= 1.6x ours | 532, 1.105, -18.8% | 1,436, 1.107, -18.2% | 1,504, 0.970, -6.5% | 2,940, 274, 1.036 (0.927), -12.2%, -359 |
| did not drift 1.3x, BSP $8-$15, BSP >= 2x ours | 166, 0.816, +11.2% | 469, 0.976, -5.5% | 523, 0.952, -6.1% | 992, 84, 0.963 (0.927), -5.9%, -58 |
| did not drift 1.3x, BSP $8-$15, BSP >= 2.5x ours | 37, 1.241, -25.7% | 117, 0.988, -11.1% | 130, 0.622, +29.2% | 247, 17, 0.795 (0.927), +10.1%, +25 |
| did not drift 1.3x, BSP $15-$40, BSP >= 1.6x ours | 1,328, 1.079, -15.8% | 3,043, 0.891, +5.2% | 2,920, 1.072, -13.9% | 5,963, 253, 0.979 (0.923), -4.2%, -248 |
| did not drift 1.3x, BSP $15-$40, BSP >= 2x ours | 666, 1.092, -22.3% | 1,546, 0.977, -1.6% | 1,511, 1.038, -15.2% | 3,057, 130, 1.007 (0.923), -8.3%, -255 |
| did not drift 1.3x, BSP $15-$40, BSP >= 2.5x ours | 254, 1.104, -30.4% | 644, 1.066, -4.3% | 676, 1.282, -39.1% | 1,320, 63, 1.176 (0.923), -22.1%, -292 |
| did not drift 1.3x, BSP $15-$40, BSP >= 3x ours | 99, 0.268, +59.8% | 248, 0.838, +11.1% | 308, 1.543, -64.8% | 556, 26, 1.226 (0.923), -30.9%, -172 |
| did not drift 1.3x, BSP $40-$100, BSP >= 1.6x ours | 702, 0.663, +27.4% | 1,341, 0.764, +20.3% | 1,572, 0.968, -2.9% | 2,913, 44, 0.873 (0.921), +7.8%, +226 **chosen** |
| did not drift 1.3x, BSP $40-$100, BSP >= 2x ours | 481, 0.991, -2.2% | 897, 0.838, +13.6% | 1,112, 0.956, -2.6% | 2,009, 31, 0.902 (0.921), +4.6%, +93 |
| did not drift 1.3x, BSP $40-$100, BSP >= 2.5x ours | 284, 0.856, +4.6% | 515, 0.804, +12.5% | 677, 0.533, +41.2% | 1,192, 13, 0.651 (0.921), +28.8%, +344 **chosen** **both halves** |
| did not drift 1.3x, BSP $40-$100, BSP >= 3x ours | 145, 1.315, -49.6% | 305, 0.987, -7.3% | 394, 0.309, +65.4% | 699, 7, 0.607 (0.921), +33.7%, +235 |

79 rules had 100+ lays in the scored quarter. 11 were chosen on the early-stopping months, and 1 of those made a profit
in both scored halves: the did-not-drift lays at $40-$100, 2.5x our price, 1,192 lays, 13 winners. That is no better
than luck. A $40-$100 lay rule turns on a handful of winners, so a zero-edge rule is in profit in both halves of a
quarter about one time in five, and two of the 11 would get there by chance.

**The horse rule does not pay on the dogs.**
- **$15-$40 at 1.6x our price, the founder's rule:** A/E 0.961 against a break-even of 0.923. It loses -4.2% on
  15,732 lays, in both halves (-2.3% and -5.9%). This is Test 34's answer again: these dogs do win less than BSP says,
  just not enough to pay 8%.
- **At 2x:** +0.9% on 9,218 lays. The 1st half lost (-3.3%) and the 2nd half won (+4.7%).
- **Where the market's dislike should be strongest, the lays get no better:**
  - **No tracked run or not tipped:** worse. At $15-$40 these dogs mostly win more than BSP says (A/E 0.94 to 1.49).
  - **Drifted late:** +5.5% at 2x on 6,157 lays, but the 1st half lost.
- **At $8-$15 it is the other way round.** The dogs BSP rates 1.6x or more longer than we do win more than BSP says,
  at A/E 1.06-1.14. Laying them loses 12-22%.

**The only lays that won are the very long ones, and they cannot be trusted:**
- At $40-$100 with BSP 2x to 3x our price, nine rules made a profit in both scored halves, at A/E 0.53 to 0.88. All
  runners at 3x made +12.6% on 4,035 lays: 52 winners against 65 BSP expected, about 1.6 standard errors.
- **On the early-stopping months seven of the same nine lost heavily:** -33% to -104%, at A/E 1.22 to 1.90. Over both
  periods together, the all-runners 3x lay has 65 winners against about 74 expected (A/E about 0.88), one standard
  error.
- **The risk is lopsided.** Each lay risks $39 to $99 to win 92c, so "+12.6% per lay" is about +0.2% on the money put
  at risk. Test 1 found the same: BSP's longshot bias on the dogs is real but small, and "laying a $200 shot risks $199
  to win 92c".

**Decision:** no lay book at BSP for the dogs. The very long lays ($40-$100, BSP 3x our price) can be logged on paper
at no cost. They would need a year of fresh months before they meant anything.


## Test 46: does the market over-rate box 8? Lay it at BSP (7 Nov 2026, gh topaz run 42294768850, `topaz_round28.py`)

The founder: "Maybe it's the other way that the market over rates from box 8 or something". The earlier evidence said
yes, a little:
- Test 2 (every Australian race) found box 8 the one box BSP over-rates: A/E 0.970, in both halves.
- Test 24 found the same in Victoria from 2020: 0.971 / 0.982.

A lay at BSP needs about 0.92 to 0.95 to pay 8% commission. This test is Victoria only, on the standard split, with
the model from Tests 39 to 45 (2,352 rounds, 180 inputs), scored from 6 Jun 2024 to 31 Oct 2026 and split into halves
at 16 Aug 2025.

Each rule lays 1 unit at BSP and never a first starter. The rules cover:
- box 8, with box 1 as the control
- where that box is weak at this track and distance (`box_ratio`, its win rate over its field-size share from earlier
  days, 0.8 or under), middling, or strong (1.1 or over), or anywhere
- BSP $1.50-$4, $4-$8, $8-$15, $15-$40, $40-$100
- our view: any, the market likes the dog more than we do (BSP at or under our price / 1.2), or less (BSP 1.3x ours or
  more)

A rule is "chosen" with 200+ lays and a profit on the early-stopping months. The break-even A/E is in brackets.

| lay at BSP | early-stopping: lays, A/E, return | 1st half: lays, A/E, return | 2nd half: lays, A/E, return | all: lays, winners, A/E (break-even), return, units |
|---|---|---|---|---|
| box 8, anywhere, any view, BSP $1.5-$4 | 868, 0.960, -3.4% | 2,350, 0.946, +0.3% | 2,268, 0.988, -2.5% | 4,618, 1,703, 0.967 (0.951), -1.1%, -50 |
| box 8, anywhere, any view, BSP $4-$8 | 978, 0.885, +5.3% | 2,512, 0.862, +7.6% | 2,568, 1.000, -6.4% | 5,080, 860, 0.932 (0.934), +0.6%, +28 **chosen** |
| box 8, anywhere, any view, BSP $8-$15 | 857, 1.038, -11.0% | 2,115, 1.037, -10.5% | 2,117, 1.061, -12.5% | 4,232, 414, 1.049 (0.927), -11.5%, -486 |
| box 8, anywhere, any view, BSP $15-$40 | 956, 1.323, -43.8% | 2,497, 0.932, -1.5% | 2,500, 1.004, -10.3% | 4,997, 215, 0.968 (0.924), -5.9%, -295 |
| box 8, anywhere, any view, BSP $40-$100 | 396, 1.186, -12.1% | 1,115, 1.079, -9.1% | 1,334, 1.249, -33.7% | 2,449, 50, 1.171 (0.921), -22.5%, -552 |
| box 8, anywhere, market likes it more (BSP <= ours / 1.2), BSP $1.5-$4 | 477, 1.029, -11.8% | 1,361, 0.946, +0.5% | 1,239, 0.986, -2.5% | 2,600, 981, 0.966 (0.952), -0.9%, -23 |
| box 8, anywhere, market likes it more (BSP <= ours / 1.2), BSP $4-$8 | 422, 0.927, +1.7% | 1,073, 0.908, +3.6% | 991, 1.084, -15.7% | 2,064, 381, 0.993 (0.934), -5.7%, -117 **chosen** |
| box 8, anywhere, market likes it more (BSP <= ours / 1.2), BSP $8-$15 | 201, 1.445, -45.3% | 587, 1.016, -5.6% | 522, 1.235, -28.4% | 1,109, 119, 1.119 (0.927), -16.3%, -181 |
| box 8, anywhere, market likes it more (BSP <= ours / 1.2), BSP $15-$40 | 130, 1.651, -57.7% | 364, 0.943, +1.5% | 295, 1.124, -21.9% | 659, 32, 1.026 (0.924), -9.0%, -59 |
| box 8, anywhere, market likes it more (BSP <= ours / 1.2), BSP $40-$100 | 28, 0.000, +92.0% | 74, 1.414, -63.2% | 74, 2.228, -139.1% | 148, 5, 1.811 (0.921), -101.1%, -150 |
| box 8, anywhere, market likes it less (BSP >= 1.3x ours), BSP $1.5-$4 | 31, 0.749, +20.0% | 94, 0.755, +17.6% | 122, 1.086, -12.2% | 216, 63, 0.942 (0.944), +0.8%, +2 |
| box 8, anywhere, market likes it less (BSP >= 1.3x ours), BSP $4-$8 | 153, 0.843, +3.4% | 397, 0.895, +5.3% | 507, 0.966, -1.4% | 904, 146, 0.935 (0.933), +1.5%, +14 |
| box 8, anywhere, market likes it less (BSP >= 1.3x ours), BSP $8-$15 | 302, 0.990, -13.6% | 704, 1.004, -7.5% | 846, 1.065, -15.0% | 1,550, 146, 1.038 (0.927), -11.6%, -180 |
| box 8, anywhere, market likes it less (BSP >= 1.3x ours), BSP $15-$40 | 551, 1.354, -53.7% | 1,365, 1.075, -19.0% | 1,535, 0.928, -3.0% | 2,900, 124, 0.997 (0.923), -10.5%, -306 |
| box 8, anywhere, market likes it less (BSP >= 1.3x ours), BSP $40-$100 | 285, 1.254, -23.3% | 820, 0.927, +9.2% | 1,073, 1.301, -39.8% | 1,893, 37, 1.140 (0.921), -18.6%, -352 |
| box 8, weak here (0.8 or under), any view, BSP $1.5-$4 | 36, 1.116, -15.5% | 115, 0.935, +7.7% | 84, 0.968, -8.0% | 199, 68, 0.949 (0.950), +1.1%, +2 |
| box 8, weak here (0.8 or under), any view, BSP $4-$8 | 60, 1.026, -3.1% | 169, 1.066, -15.4% | 156, 1.047, -16.2% | 325, 61, 1.057 (0.934), -15.8%, -51 |
| box 8, weak here (0.8 or under), any view, BSP $8-$15 | 63, 0.507, +35.8% | 181, 0.844, +12.0% | 142, 1.216, -30.4% | 323, 30, 1.008 (0.927), -6.6%, -21 |
| box 8, weak here (0.8 or under), any view, BSP $15-$40 | 79, 2.198, -122.6% | 249, 0.632, +31.1% | 213, 1.262, -30.2% | 462, 19, 0.923 (0.924), +2.8%, +13 |
| box 8, weak here (0.8 or under), any view, BSP $40-$100 | 47, 0.000, +92.0% | 105, 1.059, +8.4% | 139, 2.823, -219.2% | 244, 9, 2.061 (0.921), -121.2%, -296 |
| box 8, weak here (0.8 or under), market likes it more (BSP <= ours / 1.2), BSP $4-$8 | 23, 1.198, -12.2% | 73, 0.766, +7.7% | 64, 0.931, -3.6% | 137, 21, 0.845 (0.934), +2.4%, +3 |
| box 8, weak here (0.8 or under), market likes it less (BSP >= 1.3x ours), BSP $15-$40 | 34, 2.420, -176.3% | 115, 0.619, +25.3% | 123, 0.951, -3.7% | 238, 8, 0.792 (0.923), +10.3%, +24 |
| box 8, weak here (0.8 or under), market likes it less (BSP >= 1.3x ours), BSP $40-$100 | 34, 0.000, +92.0% | 79, 1.400, -19.1% | 108, 3.172, -271.5% | 187, 8, 2.409 (0.921), -164.9%, -308 |
| box 8, middling here, any view, BSP $1.5-$4 | 287, 1.053, -13.9% | 420, 0.896, +2.8% | 426, 0.982, -1.8% | 846, 302, 0.940 (0.951), +0.5%, +4 |
| box 8, middling here, any view, BSP $4-$8 | 367, 0.978, -6.2% | 514, 0.932, -0.7% | 494, 1.127, -18.4% | 1,008, 187, 1.028 (0.934), -9.4%, -94 |
| box 8, middling here, any view, BSP $8-$15 | 297, 1.013, -4.9% | 445, 1.186, -27.0% | 471, 1.048, -13.0% | 916, 96, 1.115 (0.927), -19.8%, -182 |
| box 8, middling here, any view, BSP $15-$40 | 332, 1.425, -60.2% | 592, 0.834, +3.4% | 641, 1.163, -27.7% | 1,233, 55, 1.004 (0.924), -12.7%, -157 |
| box 8, middling here, any view, BSP $40-$100 | 147, 0.794, +26.8% | 308, 0.758, +17.9% | 335, 0.852, +12.4% | 643, 9, 0.807 (0.921), +15.0%, +97 **both halves** |
| box 8, middling here, market likes it more (BSP <= ours / 1.2), BSP $1.5-$4 | 163, 1.153, -24.0% | 221, 0.858, +7.4% | 217, 0.981, -1.3% | 438, 154, 0.919 (0.952), +3.1%, +14 |
| box 8, middling here, market likes it more (BSP <= ours / 1.2), BSP $4-$8 | 163, 1.055, -16.5% | 230, 0.954, -1.1% | 185, 1.139, -20.2% | 415, 80, 1.039 (0.934), -9.6%, -40 |
| box 8, middling here, market likes it more (BSP <= ours / 1.2), BSP $8-$15 | 79, 1.574, -53.0% | 130, 1.250, -25.0% | 108, 1.069, -18.6% | 238, 27, 1.170 (0.927), -22.1%, -53 |
| box 8, middling here, market likes it more (BSP <= ours / 1.2), BSP $15-$40 | 43, 1.929, -94.8% | 101, 0.853, +22.4% | 86, 1.187, -28.2% | 187, 9, 1.011 (0.924), -0.9%, -2 |
| box 8, middling here, market likes it less (BSP >= 1.3x ours), BSP $4-$8 | 54, 0.880, -2.6% | 81, 0.938, +0.5% | 87, 1.243, -24.5% | 168, 32, 1.098 (0.933), -12.5%, -21 |
| box 8, middling here, market likes it less (BSP >= 1.3x ours), BSP $8-$15 | 93, 0.830, +8.0% | 128, 0.945, -6.4% | 190, 0.864, +2.8% | 318, 26, 0.897 (0.927), -0.9%, -3 |
| box 8, middling here, market likes it less (BSP >= 1.3x ours), BSP $15-$40 | 201, 1.404, -66.8% | 307, 1.223, -40.4% | 378, 1.108, -27.9% | 685, 34, 1.160 (0.923), -33.5%, -230 |
| box 8, middling here, market likes it less (BSP >= 1.3x ours), BSP $40-$100 | 102, 1.147, -1.9% | 209, 0.857, +13.5% | 269, 0.430, +60.1% | 478, 5, 0.613 (0.921), +39.7%, +190 **both halves** |
| box 8, strong here (1.1 or over), any view, BSP $1.5-$4 | 543, 0.902, +3.1% | 1,812, 0.957, -0.6% | 1,751, 0.987, -2.0% | 3,563, 1,326, 0.972 (0.951), -1.3%, -46 **chosen** |
| box 8, strong here (1.1 or over), any view, BSP $4-$8 | 549, 0.812, +13.6% | 1,829, 0.824, +12.1% | 1,908, 0.959, -2.1% | 3,737, 609, 0.893 (0.934), +4.9%, +182 **chosen** |
| box 8, strong here (1.1 or over), any view, BSP $8-$15 | 495, 1.104, -18.8% | 1,487, 1.008, -7.5% | 1,493, 1.059, -11.4% | 2,980, 287, 1.033 (0.927), -9.5%, -283 |
| box 8, strong here (1.1 or over), any view, BSP $15-$40 | 541, 1.154, -23.2% | 1,646, 1.005, -7.9% | 1,633, 0.887, +0.7% | 3,279, 138, 0.947 (0.924), -3.6%, -119 |
| box 8, strong here (1.1 or over), any view, BSP $40-$100 | 200, 1.758, -66.3% | 702, 1.220, -23.6% | 854, 1.150, -22.5% | 1,556, 32, 1.182 (0.921), -23.0%, -358 |
| box 8, strong here (1.1 or over), market likes it more (BSP <= ours / 1.2), BSP $1.5-$4 | 296, 0.952, -3.6% | 1,081, 0.969, -1.6% | 982, 0.986, -2.3% | 2,063, 794, 0.977 (0.952), -1.9%, -39 |
| box 8, strong here (1.1 or over), market likes it more (BSP <= ours / 1.2), BSP $4-$8 | 235, 0.817, +15.3% | 770, 0.907, +4.6% | 738, 1.072, -14.5% | 1,508, 278, 0.988 (0.934), -4.7%, -71 **chosen** |
| box 8, strong here (1.1 or over), market likes it more (BSP <= ours / 1.2), BSP $8-$15 | 99, 1.462, -47.3% | 393, 0.990, -2.4% | 378, 1.287, -31.2% | 771, 84, 1.137 (0.927), -16.5%, -127 |
| box 8, strong here (1.1 or over), market likes it more (BSP <= ours / 1.2), BSP $15-$40 | 72, 1.210, -14.7% | 222, 0.964, -6.4% | 188, 1.109, -21.1% | 410, 20, 1.031 (0.924), -13.1%, -54 |
| box 8, strong here (1.1 or over), market likes it less (BSP >= 1.3x ours), BSP $1.5-$4 | 19, 0.710, +26.4% | 69, 0.785, +14.8% | 97, 1.040, -7.3% | 166, 48, 0.933 (0.944), +1.9%, +3 |
| box 8, strong here (1.1 or over), market likes it less (BSP >= 1.3x ours), BSP $4-$8 | 89, 0.852, +5.4% | 285, 0.921, +2.5% | 381, 0.860, +8.1% | 666, 102, 0.887 (0.933), +5.7%, +38 **both halves** |
| box 8, strong here (1.1 or over), market likes it less (BSP >= 1.3x ours), BSP $8-$15 | 189, 1.116, -29.7% | 527, 0.965, -4.7% | 604, 1.057, -13.8% | 1,131, 104, 1.014 (0.927), -9.6%, -108 |
| box 8, strong here (1.1 or over), market likes it less (BSP >= 1.3x ours), BSP $15-$40 | 314, 1.233, -33.0% | 940, 1.060, -16.1% | 1,025, 0.822, +9.1% | 1,965, 79, 0.936 (0.923), -3.0%, -58 |
| box 8, strong here (1.1 or over), market likes it less (BSP >= 1.3x ours), BSP $40-$100 | 148, 1.618, -65.2% | 532, 0.880, +11.7% | 692, 1.352, -43.3% | 1,224, 24, 1.147 (0.921), -19.4%, -237 |
| box 1, anywhere, any view, BSP $1.5-$4 | 1,122, 1.003, -5.2% | 2,869, 0.993, -3.9% | 2,980, 1.020, -6.8% | 5,849, 2,305, 1.007 (0.952), -5.4%, -316 |
| box 1, anywhere, any view, BSP $4-$8 | 1,177, 1.025, -9.5% | 2,896, 0.989, -6.8% | 2,800, 1.026, -10.4% | 5,696, 1,046, 1.007 (0.934), -8.6%, -489 |
| box 1, anywhere, any view, BSP $8-$15 | 783, 0.975, -4.1% | 2,048, 1.092, -16.3% | 2,076, 1.054, -14.4% | 4,124, 417, 1.073 (0.927), -15.3%, -632 |
| box 1, anywhere, any view, BSP $15-$40 | 823, 1.091, -9.3% | 2,195, 0.909, +0.9% | 2,138, 0.945, -2.1% | 4,333, 179, 0.927 (0.924), -0.6%, -25 |
| box 1, anywhere, any view, BSP $40-$100 | 306, 0.944, -5.9% | 840, 0.956, -0.1% | 1,056, 1.041, -10.8% | 1,896, 33, 1.003 (0.921), -6.1%, -115 |
| box 1, anywhere, market likes it more (BSP <= ours / 1.2), BSP $1.5-$4 | 541, 0.988, -2.1% | 1,416, 0.994, -2.6% | 1,411, 1.024, -7.8% | 2,827, 1,147, 1.009 (0.953), -5.2%, -146 |
| box 1, anywhere, market likes it more (BSP <= ours / 1.2), BSP $4-$8 | 405, 1.068, -13.7% | 987, 1.108, -18.9% | 964, 0.975, -4.1% | 1,951, 380, 1.042 (0.935), -11.6%, -226 |
| box 1, anywhere, market likes it more (BSP <= ours / 1.2), BSP $8-$15 | 156, 1.145, -27.8% | 403, 1.040, -8.7% | 390, 1.357, -44.1% | 793, 91, 1.196 (0.927), -26.1%, -207 |
| box 1, anywhere, market likes it more (BSP <= ours / 1.2), BSP $15-$40 | 94, 0.908, -14.7% | 242, 1.466, -63.1% | 199, 1.129, -20.5% | 441, 28, 1.312 (0.924), -43.9%, -193 |
| box 1, anywhere, market likes it less (BSP >= 1.3x ours), BSP $1.5-$4 | 57, 0.944, -3.2% | 189, 0.967, -1.0% | 192, 1.045, -9.7% | 381, 121, 1.007 (0.945), -5.4%, -20 |
| box 1, anywhere, market likes it less (BSP >= 1.3x ours), BSP $4-$8 | 266, 1.055, -18.4% | 647, 0.932, +0.8% | 695, 1.024, -9.4% | 1,342, 228, 0.979 (0.933), -4.5%, -60 |
| box 1, anywhere, market likes it less (BSP >= 1.3x ours), BSP $8-$15 | 335, 0.805, +14.8% | 880, 1.141, -23.6% | 958, 0.993, -11.2% | 1,838, 180, 1.064 (0.927), -17.1%, -315 **chosen** |
| box 1, anywhere, market likes it less (BSP >= 1.3x ours), BSP $15-$40 | 496, 1.301, -23.2% | 1,442, 0.829, +8.6% | 1,487, 0.903, +3.2% | 2,929, 110, 0.866 (0.923), +5.9%, +173 **both halves** |
| box 1, anywhere, market likes it less (BSP >= 1.3x ours), BSP $40-$100 | 238, 0.747, +27.0% | 688, 0.683, +21.3% | 906, 1.035, -14.3% | 1,594, 24, 0.883 (0.921), +1.0%, +16 **chosen** |
| box 1, strong here (1.1 or over), any view, BSP $1.5-$4 | 1,099, 1.000, -5.0% | 2,849, 0.992, -3.8% | 2,957, 1.020, -6.8% | 5,806, 2,285, 1.006 (0.952), -5.3%, -308 |
| box 1, strong here (1.1 or over), any view, BSP $4-$8 | 1,156, 1.022, -8.8% | 2,880, 0.985, -6.3% | 2,781, 1.019, -9.7% | 5,661, 1,034, 1.002 (0.934), -8.0%, -451 |
| box 1, strong here (1.1 or over), any view, BSP $8-$15 | 765, 0.971, -3.5% | 2,034, 1.089, -15.8% | 2,062, 1.056, -14.7% | 4,096, 414, 1.073 (0.927), -15.3%, -625 |
| box 1, strong here (1.1 or over), any view, BSP $15-$40 | 793, 1.105, -11.1% | 2,185, 0.913, +0.5% | 2,128, 0.949, -2.5% | 4,313, 179, 0.931 (0.924), -1.0%, -43 |
| box 1, strong here (1.1 or over), any view, BSP $40-$100 | 292, 0.996, -10.6% | 834, 0.962, -0.8% | 1,053, 1.044, -11.1% | 1,887, 33, 1.008 (0.921), -6.5%, -123 |
| box 1, strong here (1.1 or over), market likes it more (BSP <= ours / 1.2), BSP $1.5-$4 | 524, 0.985, -1.9% | 1,409, 0.994, -2.5% | 1,395, 1.025, -7.9% | 2,804, 1,137, 1.009 (0.953), -5.2%, -146 |
| box 1, strong here (1.1 or over), market likes it more (BSP <= ours / 1.2), BSP $4-$8 | 400, 1.083, -15.0% | 981, 1.103, -18.1% | 954, 0.969, -3.4% | 1,935, 375, 1.037 (0.935), -10.9%, -210 |
| box 1, strong here (1.1 or over), market likes it more (BSP <= ours / 1.2), BSP $8-$15 | 149, 1.129, -24.1% | 397, 1.028, -6.7% | 386, 1.344, -43.4% | 783, 89, 1.184 (0.927), -24.8%, -194 |
| box 1, strong here (1.1 or over), market likes it more (BSP <= ours / 1.2), BSP $15-$40 | 89, 0.953, -20.7% | 239, 1.484, -65.0% | 199, 1.129, -20.5% | 438, 28, 1.321 (0.924), -44.8%, -196 |
| box 1, strong here (1.1 or over), market likes it less (BSP >= 1.3x ours), BSP $1.5-$4 | 55, 0.922, -1.5% | 186, 0.965, -0.8% | 192, 1.045, -9.7% | 378, 120, 1.006 (0.945), -5.3%, -20 |
| box 1, strong here (1.1 or over), market likes it less (BSP >= 1.3x ours), BSP $4-$8 | 262, 1.050, -17.2% | 645, 0.935, +0.5% | 694, 1.017, -8.6% | 1,339, 227, 0.977 (0.933), -4.2%, -57 |
| box 1, strong here (1.1 or over), market likes it less (BSP >= 1.3x ours), BSP $8-$15 | 333, 0.809, +14.4% | 874, 1.149, -24.4% | 953, 0.998, -11.8% | 1,827, 180, 1.070 (0.927), -17.8%, -325 **chosen** |
| box 1, strong here (1.1 or over), market likes it less (BSP >= 1.3x ours), BSP $15-$40 | 480, 1.298, -23.7% | 1,439, 0.830, +8.5% | 1,482, 0.906, +2.9% | 2,921, 110, 0.869 (0.923), +5.7%, +166 **both halves** |
| box 1, strong here (1.1 or over), market likes it less (BSP >= 1.3x ours), BSP $40-$100 | 233, 0.762, +25.6% | 683, 0.688, +20.7% | 905, 1.035, -14.4% | 1,588, 24, 0.886 (0.921), +0.7%, +11 **chosen** |

78 rules had 100+ lays in the scored quarter. 9 were chosen on the early-stopping months, and none of the 9 made a
profit in both scored halves. Luck alone would give about one: most of the 9 are short-priced lays, which a
zero-edge rule makes a profit on in both halves only a few times in a hundred.

**Box 8 is no longer over-rated.** Over the five "anywhere, any view" bands, laid box 8 runners won at a lay-weighted
A/E of 0.999 against BSP, and box 1's at 1.003 (21,376 and 21,898 lays). By band, box 8 ran:

| BSP band | A/E | break-even | return per lay |
|---|---|---|---|
| $1.50-$4 | 0.967 | 0.951 | -1.1% |
| $4-$8 | 0.932 | 0.934 | +0.6% |
| $8-$15 | 1.049 | 0.927 | -11.5% |
| $15-$40 | 0.968 | 0.924 | -5.9% |
| $40-$100 | 1.171 | 0.921 | -22.5% |

The 2020-2023 lean against box 8 (Tests 2 and 24) is gone or nearly gone in the scored years.

**Where box 8 is strong at the track, at $4-$8, it came closest:** A/E 0.893, +4.9% on 3,737 lays, chosen.
- It made +12.1% in the 1st half and lost 2.1% in the 2nd.
- The market-likes-it-less slice of the same cell made +5.7% in both halves, but on only 666 lays, and it had too few
  lays on the early-stopping months (89) to be chosen.

The other "both halves" rows are longshots with 5 to 9 winners, or box 1 rules that lost 23% on the early-stopping
months.

**Decision:** no box 8 lay at BSP. The box is priced right now, and every cell that looks good either failed a half or
rests on a handful of winners.


## Test 47: the bench, market angles one at a time (7 Nov 2026, gh topaz run 42299569375, `topaz_round29.py`)

The founder: "There would be lots of different things you could test". The bench uses no model: the market against
itself, on every Victorian race since 2020 that has a BSP on every runner. A rule is one segment, in one price band
($1.50-$3, $3-$5, $5-$8, $8-$15, $15-$40, $40-$100), with one bet: back at BSP, lay at BSP (8% commission), or back at
GRV's SP. The segments are:
- the race: box (each of 1 to 8), track, distance, grade, field size, Betfair's scheduled start (before or after 6pm)
- the dog's form: starts before, days since the last start, won last start, SP favourite last start, first time at
  the track
- outside information: GRV's tip, tracking and checks, the trainer's second runner in the race
- the market: the late move (Betfair's last pre-play price against its pre-play average) and how much money traded

The price band for a BSP bet is set by Betfair's last pre-play price, which is known before the off, unlike BSP itself.
For an SP bet it is set by GRV's SP. A rule is:
- chosen on the first 60% of race days (300+ bets and a profit)
- scored once on the last 40%, split into halves, with z = return over its standard error. With no edge, about 2.3%
  of chosen rules reach z >= 2 by luck.
- re-chosen every month on the 12 months before, then bet (a runner once per bet, however many rules pick it), as
  Test 42 did

65,285 races, 455,998 runners with a BSP on every runner and GRV's SP: choosing on 2020-01-01 to 2024-02-05 (39,749 races), scored once on 2024-02-06 to 2026-10-31 (25,536 races), halves split at 2025-07-11. Betfair's pre-play prices on 100% of runners.

Races by Betfair's scheduled hour (a check that it is Melbourne's clock): 8h 90, 9h 315, 10h 481, 11h 1,733, 12h 2,208, 13h 2,195, 14h 2,730, 15h 3,010, 16h 2,975, 17h 3,294, 18h 3,409, 19h 3,826, 20h 3,748, 21h 3,110, 22h 1,999, 23h 19

| bet | rules with 300+ bets on the choosing years | chosen (a profit there) | chosen, profit in the scored years | chosen, profit in both halves | chosen, z >= 2 on the scored years | z >= 2 expected by luck |
|---|---|---|---|---|---|---|
| back at BSP | 393 | 20 | 4 | 1 | 0 | 0.5 |
| lay at BSP | 393 | 39 | 9 | 4 | 0 | 0.9 |
| back at GRV's SP | 389 | 0 | 0 | 0 | 0 | 0.0 |

All bets: 1,175 rules tried, 59 chosen.

Every chosen rule with z >= 1.5 on the scored years, best first:

| rule | choosing years: bets, return, z | scored 1st half: bets, return | 2nd half: bets, return | scored: bets, A/E vs the price paid, return, z |
|---|---|---|---|---|
| lay at BSP: grade 4, $40-$100 | 2,503, +19.8%, +1.5 | 750, +17.3% | 927, +36.7% | 1,677, 0.617, +28.0%, +1.7 **both halves** |

### Re-chosen every month on the 12 months before (150+ bets and a profit there), then bet

| bet | rules chosen a month | half | bets | winners | A/E vs the price paid | return | units | months in profit |
|---|---|---|---|---|---|---|---|---|
| back at BSP | 50-89 | 1st | 51,466 | 6,043 | 1.000 | -7.1% | -3,664 | 2 of 18 |
| back at BSP | 50-89 | 2nd | 50,352 | 5,617 | 1.015 | -7.3% | -3,657 | 4 of 16 |
| back at BSP | 50-89 | all | 101,818 | 11,660 | 1.007 | -7.2% | -7,321 | 5 of 33 |
| lay at BSP | 57-96 | 1st | 57,911 | 7,615 | 0.991 | -6.5% | -3,752 | 2 of 18 |
| lay at BSP | 57-96 | 2nd | 54,833 | 7,100 | 0.989 | -5.3% | -2,912 | 4 of 16 |
| lay at BSP | 57-96 | all | 112,744 | 14,715 | 0.990 | -5.9% | -6,664 | 6 of 33 |
| back at GRV's SP | 2-10 | 1st | 3,060 | 314 | 0.892 | -16.0% | -489 | 4 of 18 |
| back at GRV's SP | 2-10 | 2nd | 3,399 | 318 | 0.808 | -25.1% | -852 | 3 of 16 |
| back at GRV's SP | 2-10 | all | 6,459 | 632 | 0.847 | -20.8% | -1,341 | 7 of 33 |

**Nothing beats luck.**
- 1,175 rules were tried and 59 chosen. None reached z >= 2 on the scored years, where luck alone would give 1.4. The
  best was a lay of grade 4 runners at $40-$100: +28.0% on 1,677 lays, z 1.7.
- Re-chosen every month, every bet loses:
  - **back at BSP:** -7.2% on 101,818 bets, A/E 1.007
  - **lay at BSP:** -5.9% on 112,744, A/E 0.990
  - **back at GRV's SP:** -20.8% on 6,459, A/E 0.847
- What the market's prices say on their own: at BSP every slice of the market is priced to within a percent or two,
  and commission takes the rest. GRV's SP is a much worse price, at A/E about 0.85.

**Betfair's own start times read as Melbourne's clock.** Races run from 8am to 11pm and peak at 7-8pm. That confirms
Test 41's finding that the Topaz start times had been read 10 or 11 hours late.

## Test 48: the bench, box x early speed and the draw (7 Nov 2026, gh topaz run 42301552708, `topaz_round29.py`, `BENCH_PAIRS=yes`)

The founder: "we know there are more boxes than 1 and 8 and then there's dogs that are fast and not fast". Test 47's
bench, plus:
- early speed on its own (fastest, 2nd-3rd or 4th+ in the field on past splits, and led early in half its runs)
- every box x early-speed rank
- every box x whether a quicker beginner is drawn inside it
- every early-speed rank x track

65,285 races, 455,998 runners with a BSP on every runner and GRV's SP: choosing on 2020-01-01 to 2024-02-05 (39,749 races), scored once on 2024-02-06 to 2026-10-31 (25,536 races), halves split at 2025-07-11. Betfair's pre-play prices on 100% of runners.

Races by Betfair's scheduled hour (a check that it is Melbourne's clock): 8h 90, 9h 315, 10h 481, 11h 1,733, 12h 2,208, 13h 2,195, 14h 2,730, 15h 3,010, 16h 2,975, 17h 3,294, 18h 3,409, 19h 3,826, 20h 3,748, 21h 3,110, 22h 1,999, 23h 19

Segments: 155 (with box x early speed, box x a quicker beginner inside, early speed x track)

| bet | rules with 300+ bets on the choosing years | chosen (a profit there) | chosen, profit in the scored years | chosen, profit in both halves | chosen, z >= 2 on the scored years | z >= 2 expected by luck |
|---|---|---|---|---|---|---|
| back at BSP | 877 | 108 | 28 | 9 | 0 | 2.5 |
| lay at BSP | 877 | 137 | 38 | 16 | 1 | 3.2 |
| back at GRV's SP | 867 | 10 | 2 | 0 | 0 | 0.2 |

All bets: 2,621 rules tried, 255 chosen.

Every chosen rule with z >= 1.5 on the scored years, best first:

| rule | choosing years: bets, return, z | scored 1st half: bets, return | 2nd half: bets, return | scored: bets, A/E vs the price paid, return, z |
|---|---|---|---|---|
| lay at BSP: box 4, no quicker beginner inside it, $40-$100 | 714, +1.9%, +0.1 | 231, +53.9% | 234, +75.8% | 465, 0.357, +64.9%, +4.1 **both halves** |
| back at BSP: box 5, a quicker beginner drawn inside it, $8-$15 | 3,478, +0.8%, +0.2 | 1,202, +16.5% | 1,096, +8.4% | 2,298, 1.227, +12.7%, +1.9 **both halves** |
| lay at BSP: grade 4, $40-$100 | 2,503, +19.8%, +1.5 | 750, +17.3% | 927, +36.7% | 1,677, 0.617, +28.0%, +1.7 **both halves** |
| lay at BSP: track GEL, fastest early, $8-$15 | 678, +11.1%, +1.0 | 195, +23.1% | 212, +20.0% | 407, 0.756, +21.5%, +1.7 **both halves** |
| back at BSP: box 2, 4th+ fastest early, $8-$15 | 3,743, +2.0%, +0.4 | 1,248, +6.9% | 1,249, +13.5% | 2,497, 1.184, +10.2%, +1.6 **both halves** |

### Re-chosen every month on the 12 months before (150+ bets and a profit there), then bet

| bet | rules chosen a month | half | bets | winners | A/E vs the price paid | return | units | months in profit |
|---|---|---|---|---|---|---|---|---|
| back at BSP | 151-199 | 1st | 61,758 | 8,010 | 1.001 | -7.0% | -4,310 | 2 of 18 |
| back at BSP | 151-199 | 2nd | 60,725 | 7,892 | 1.008 | -7.5% | -4,553 | 3 of 16 |
| back at BSP | 151-199 | all | 122,483 | 15,902 | 1.004 | -7.2% | -8,863 | 4 of 33 |
| lay at BSP | 190-223 | 1st | 66,621 | 9,347 | 0.995 | -6.5% | -4,355 | 1 of 18 |
| lay at BSP | 190-223 | 2nd | 64,479 | 8,958 | 0.991 | -5.8% | -3,760 | 3 of 16 |
| lay at BSP | 190-223 | all | 131,100 | 18,305 | 0.993 | -6.2% | -8,116 | 4 of 33 |
| back at GRV's SP | 22-43 | 1st | 12,108 | 1,504 | 0.840 | -19.2% | -2,322 | 0 of 18 |
| back at GRV's SP | 22-43 | 2nd | 10,499 | 1,262 | 0.815 | -25.6% | -2,687 | 1 of 16 |
| back at GRV's SP | 22-43 | all | 22,607 | 2,766 | 0.828 | -22.2% | -5,009 | 1 of 33 |

**Nothing beats luck here either.**
- 2,621 rules were tried and 255 chosen. One reached z >= 2, where luck alone would give 5.9.
  - The one is a lay of box 4 runners with no quicker beginner inside them, at $40-$100: 465 lays, +64.9%, z 4.1.
  - On the choosing years the same lay made +1.9% (z 0.1), and with about three winners in the scored years its z is
    far less than it looks. A lay that rarely loses has a small spread until the loss comes.
- The five rules with z >= 1.5 all made a profit in both halves. Two of them are backs at BSP $8-$15 about the draw
  and early speed, the kind of thing a price might miss:
  - **box 5 with a quicker beginner drawn inside it:** 2,298 bets, A/E 1.227, +12.7%. That is +16.5% in the 1st half
    and +8.4% in the 2nd, after +0.8% on the choosing years.
  - **box 2 and 4th+ fastest early:** 2,497 bets, A/E 1.184, +10.2%. That is +6.9% and +13.5%, after +2.0%.
- Luck alone would put about 17 of the 255 at z >= 1.5 (6.7%), and here there are 5, so even these two are inside what
  luck makes.
- Re-chosen every month, every bet loses:
  - **back at BSP:** -7.2% on 122,483 bets
  - **lay at BSP:** -6.2% on 131,100
  - **back at GRV's SP:** -22.2% on 22,607

**Decision:** no market-only rule at BSP or GRV's SP. The two $8-$15 backs (box 5 with a quicker beginner inside it,
box 2 when slow away) can be logged on paper at no cost.

Across Tests 39 to 48, everything at BSP gives the same answer. The market alone does not pay: BSP is priced right in
every slice we can cut, and GRV's SP is far worse. The edge the card has, the 1.3x rule at GRV's SP (Tests 27, 37, 38,
43, 44), comes from the model's price, and the price it is bet at matters as much as the model. Hence the TAB opens.

## Test 49: the 1.3x rule at TAB's own prices, from Betwatch (13 Nov 2026, gh topaz run 43396526317, `topaz_round30.py`)

Founder, 13 Nov 2026: "we will win long term on opening ... Just have to get that data and then get a strategy".

> **Correction, the same night (Test 50).** The +44.7% below is not an edge at the open. 88% of the bets (930 of
> 1,051) were in races where a dog was scratched after TAB's market opened, against 27.5% of all races. Our model
> priced the field that ran, so it saw value in every dog left in once a strong one came out. TAB takes that back as
> a deduction, and after the deduction the rule LOST 10.5% flat (-335 Kelly units, 13 of 30 months in profit). The
> 78% of bets that shortened by BSP is mostly the same thing: a scratching shortens every dog left in.

**The data.** The `gh betwatch` pull (run 43380037426, 132 minutes) fetched every Victorian greyhound race from November
2022 to 12 November 2026. It holds 49 month files, all complete. A month is about 1,200-1,300 races and 8,500-9,600
runners, and TAB has price changes on 99-100% of runners in every month. Joined by date and dog name, round 30 reads
437,489 runners from 7 Nov 2022 to 12 Nov 2026.

**The test.** This is the production model (the weekly train's inputs, the half-weight label, 3,784 rounds by early
stopping, 168 inputs) on the standard split, scored on the last quarter. The 1.3x rule runs at three prices:
- GRV's SP, as before;
- TAB's first recorded price of the day;
- TAB's last recorded price before the jump.

For each price:
- **Blend:** ours is blended with that price's own book (normalised per race), fitted on the early-stopping months.
- **When it bets:** when the price is at least 1.3 times the blended price, with our blended price $2-$15.
- **Staking:** Kelly x75 on the chance halfway between the blend and that price's chance, cap 4, no commission.

| scored quarter | runners | races | TAB's first price on | races with it on every runner | hours from TAB's first price to the jump (median) | TAB's first book (median) | GRV's SP book (median) |
|---|---|---|---|---|---|---|---|
| 10 Jun 2024 to 12 Nov 2026 | 187,531 | 25,731 | 97.6% | 23,072 | 10.0 | 133% | 119% |

The first TAB price is a morning price: about 10 hours before a typical race. The book at that hour is loose, at 133%.

| price (blend: ours / that book) | half | bets | winners | A/E vs that price | flat ROI | units staked | Kelly ROI | units won | worst drawdown | months in profit |
|---|---|---|---|---|---|---|---|---|---|---|
| GRV's SP (0.50 / 0.68) | 1st | 785 | 205 | 1.575 | +63.4% | 1,617 | +63.6% | +1,029 | 49 | 15 of 15 |
| GRV's SP (0.50 / 0.68) | 2nd | 774 | 189 | 1.646 | +72.8% | 1,326 | +80.9% | +1,072 | 37 | 14 of 16 |
| GRV's SP (0.50 / 0.68) | all | 1,559 | 394 | 1.608 | +68.1% | 2,944 | +71.4% | **+2,101** | 49 | 28 of 30 |
| TAB's first price (0.55 / 0.67) | 1st | 386 | 103 | 1.498 | +53.2% | 1,142 | +71.5% | +816 | 53 | 13 of 15 |
| TAB's first price (0.55 / 0.67) | 2nd | 665 | 166 | 1.420 | +39.7% | 2,143 | +45.1% | +967 | 54 | 15 of 16 |
| TAB's first price (0.55 / 0.67) | all | 1,051 | 269 | 1.449 | **+44.7%** | 3,285 | +54.3% | **+1,784** | 54 | 28 of 30 |
| TAB's last price before the jump (0.01 / 1.12) | all | 0 | | | | | | | | |

With the drift guard (no dog that drifted 1.3x or more from its shortest Betfair price before the off):
- **GRV's SP:** 1,001 bets, A/E 1.811, +99.6% flat, +2,005 units.
- **TAB's first price:** 808 bets, A/E 1.568, +59.3% flat, +1,731 units, 26 of 30 months in profit.

**The guard cannot be used at the open.** It reads the dog's drift up to the off, which is many hours after a bet at
TAB's first price.

At TAB's last price the blend gives ours a weight of 0.01 against TAB's 1.12, so the rule never bets. By the jump TAB's
price is as sharp as BSP, where our weight was -0.10 to 0.08 (Test 27) and -0.07 to 0.08 (Test 44).

**Closing-line value.** For the rule's bets, BSP is compared with the price taken:

| bets at | half | bets with a BSP | BSP shorter than the price taken | mean log(price taken / BSP) | A/E vs BSP |
|---|---|---|---|---|---|
| GRV's SP | 1st | 782 | 73.3% | +0.390 | 0.963 |
| GRV's SP | 2nd | 745 | 58.8% | +0.242 | 1.113 |
| GRV's SP | all | 1,527 | 66.2% | +0.318 | 1.029 |
| TAB's first price | 1st | 386 | 78.2% | +0.325 | 1.030 |
| TAB's first price | 2nd | 640 | 78.0% | +0.290 | 1.004 |
| TAB's first price | all | 1,026 | 78.1% | +0.304 | 1.014 |

**What it means.**
- **The rule pays at TAB's first price in both halves, on a price that could be bet.** The return is +44.7% flat on
  1,051 bets and +1,784 Kelly units over 30 months, 28 of them in profit.
- **The market comes to us.** Four bets in five shorten by the jump, and the price taken is on average about 35% above
  BSP (exp 0.304). At BSP the same dogs are about fair (A/E 1.014).
- **This fits Test 41.** The gap between our price and BSP is the late money, and at the open we are ahead of it.

**Not yet known, and each could shrink it:**
1. **Scratchings after the bet.** At 10 hours out the field is not final. A dog scratched later brings a fixed-odds
   deduction. Our model also priced the race knowing who actually ran and which boxes were vacant.
2. **Whether the first price stood.** Betwatch's first price is the first it saw, and TAB may have corrected it within
   minutes.
3. **TAB's limits.** Early fixed-odds markets carry small limits, and winning accounts are restricted. No data here
   can test that.

Round 32 tests the first two.

## Test 50: can TAB's first price be had? Scratchings and deductions (13 Nov 2026, gh topaz runs 43405429255 and 43414156636, `topaz_round32.py`)

Founder, the same night: "Did you apply 6c to every bet?" Test 49 had taken nothing off.

This uses Test 49's model and rule. The rule's 1,051 bets at TAB's first price were checked three ways.

**Scratchings.** In 27.5% of the scored races a runner was scratched after TAB's market opened. Every one of those
scratched dogs had a TAB price to deduct by.

**1. How long the first price stood**, for the 1,051 bets (minutes to TAB's next change of price):

| under 1 | under 5 | under 30 | under 60 | median | next change shorter |
|---|---|---|---|---|---|
| 4.9% | 21.8% | 43.7% | 50.3% | 59 min | 76.7% |

**2. Scratchings after the bet, and the deductions.** All bets are at TAB's first price, with Kelly stakes as struck.

TAB's deduction is read off the founder's own TAB records (data/live_bets). It is 100c over the scratched dog's price
at the scratching, rounded down, and at most 75c a race. That rule matches five of the six records ($12 8c, $14 7c,
$16 6c, $26 3c, $34 2c). It gives $17 5c where the record says 6c.

| bets | half | bets | winners | A/E vs the price | flat ROI | units staked | Kelly ROI | units won | months in profit |
|---|---|---|---|---|---|---|---|---|---|
| Test 49 as it was, nothing off | all | 1,051 | 269 | 1.449 | +44.7% | 3,285 | +54.3% | +1,784 | 28 of 30 |
| races with no runner scratched after the open | 1st | 65 | 15 | 1.266 | +5.8% | 70 | +47.5% | +33 | 7 of 15 |
| races with no runner scratched after the open | 2nd | 56 | 17 | 1.777 | +63.8% | 67 | +51.4% | +35 | 9 of 15 |
| races with no runner scratched after the open | all | 121 | 32 | 1.494 | +32.6% | 138 | +49.4% | +68 | 16 of 30 |
| races with one or more scratched after the open | all | 930 | 237 | 1.443 | +46.2% | 3,148 | +54.5% | +1,716 | 27 of 30 |
| 6c in the dollar off every bet's winnings | 1st | 386 | 103 | 1.498 | +45.6% | 1,142 | +63.0% | +720 | 13 of 15 |
| 6c in the dollar off every bet's winnings | 2nd | 665 | 166 | 1.420 | +32.8% | 2,143 | +38.0% | +815 | 13 of 16 |
| 6c in the dollar off every bet's winnings | all | 1,051 | 269 | 1.449 | +37.5% | 3,285 | +46.7% | +1,535 | 26 of 30 |
| the scratched dogs' share of TAB's opening book off the winnings | all | 1,051 | 269 | 1.449 | +1.8% | 3,285 | +4.0% | +131 | 17 of 30 |
| **TAB's deduction (100c over the scratched dog's price)** | 1st | 386 | 103 | 1.498 | -3.6% | 1,142 | +1.6% | +18 | 11 of 15 |
| **TAB's deduction** | 2nd | 665 | 166 | 1.420 | -14.5% | 2,143 | -16.5% | -353 | 3 of 16 |
| **TAB's deduction** | all | 1,051 | 269 | 1.449 | **-10.5%** | 3,285 | **-10.2%** | **-335** | 13 of 30 |

**3. Did BSP come in under the price?** BSP is compared with the price taken and with the price paid after TAB's
deduction:

| races | half | bets with a BSP | BSP under the price taken | BSP under the price paid | mean log(price taken / BSP) | mean log(price paid / BSP) | A/E vs BSP |
|---|---|---|---|---|---|---|---|
| every race | all | 1,026 | 801 (78.1%) | 339 (33.0%) | +0.304 | -0.181 | 1.014 |
| no scratching after the open | 1st | 65 | 42 (64.6%) | 42 (64.6%) | +0.220 | +0.220 | 0.927 |
| no scratching after the open | 2nd | 55 | 31 (56.4%) | 31 (56.4%) | +0.100 | +0.100 | 1.385 |
| no scratching after the open | all | 120 | 73 (60.8%) | 73 (60.8%) | +0.165 | +0.165 | 1.117 |
| a scratching after the open | all | 906 | 728 (80.4%) | 266 (29.4%) | +0.322 | -0.227 | 1.001 |

**What it means.**
- **The bets cluster where TAB's market changed.** The rule put 88% of its bets into races where a dog was scratched
  after the open, against 27.5% of races overall. Our model prices the field that ran. When a strong dog is scratched,
  every dog left in looks overpriced at TAB's opening price.
- **TAB's deduction takes it back, and more.** Paid as TAB pays, the rule lost 10.5% flat and 335 Kelly units, with
  the second half at -14.5%. A flat 6c on every bet (+37.5%) understates the deductions badly. These bets sit in races
  where a favourite came out, and that is where the deductions are biggest.
- **Most of the 78% is the scratching too.** Against the price paid, BSP came in under it on only 33% of bets.
- **What is left is too small to call.** In races with no scratching after the open, 121 bets made +32.6% flat, with
  A/E vs BSP 1.117 and BSP under the price on 61% of them. But only 16 of 30 months were in profit, and the first half
  was +5.8%.
- **About the first price itself.** It stood a median of 59 minutes. On 22% of bets it changed within 5 minutes, and
  when it changed it shortened three times in four.

**What next.** Round 33 rebuilds each race as it stood at the bet:
- each dog scratched later goes back in at TAB's chance for it;
- our chances for the rest are scaled to make room;
- every bet is paid after TAB's deduction.

That is what the live card already does, because it prices the declared field the night before. Round 31 (every
rule at TAB's prices) was re-run with TAB's deduction on every return.

## Test 51: the rule on the field as it stood when the bet was struck (13 Nov 2026, gh topaz run 43416687768, `topaz_round33.py`)

Founder: "Well keep testing and get better".

The model prices the field that ran. A bettor at TAB's open bets into the field in the market then, which includes dogs
scratched later. That bettor is paid after TAB's deduction for them. Three versions of the 1.3x rule run side by side,
on Test 49's model and split:
- **A:** the field that ran, nothing deducted (Test 49 as it was).
- **B:** the field that ran, paid after TAB's deduction (Test 50's table).
- **C:** the field at the bet, paid after TAB's deduction:
  - each dog scratched later goes back in at TAB's chance for it;
  - ours for the dogs that ran is scaled by (1 - that chance);
  - the blend is fitted on early-stopping races with no scratching after the bet, then applied over the whole field at
    the bet.

C assumes we would have rated a scratched dog as TAB did, since we have no price of our own for a dog that did not run.

| bet time | version | half | bets | winners | A/E vs the price | flat ROI | units staked | Kelly ROI | units won | months in profit |
|---|---|---|---|---|---|---|---|---|---|---|
| TAB's first price | A (0.54 / 0.66) | all | 1,047 | 266 | 1.454 | +44.4% | 3,263 | +53.9% | +1,760 | 28 of 30 |
| TAB's first price | B | all | 1,047 | 266 | 1.454 | -10.7% | 3,263 | -10.4% | -340 | 13 of 30 |
| TAB's first price | **C (0.54 / 0.67)** | 1st | 65 | 16 | 1.356 | +9.6% | 72 | +49.8% | +36 | 6 of 14 |
| TAB's first price | **C** | 2nd | 66 | 17 | 1.560 | +36.1% | 74 | +43.6% | +32 | 9 of 15 |
| TAB's first price | **C** | all | 131 | 33 | 1.454 | **+23.0%** | 146 | +46.6% | **+68** | 15 of 29 |
| TAB's first price | C, no scratching after the bet | all | 110 | 29 | 1.529 | +33.6% | 123 | +49.7% | +61 | 15 of 29 |
| TAB's first price | C, a scratching after the bet | all | 21 | 4 | 1.074 | -33.0% | 23 | +30.3% | +7 | 4 of 11 |
| TAB's first price | C at 1.1x | all | 241 | 62 | 1.326 | +21.7% | 186 | +44.0% | +82 | 17 of 30 |
| TAB's first price | C at 1.2x | all | 239 | 62 | 1.333 | +22.8% | 183 | +45.9% | +84 | 17 of 30 |
| TAB's first price | C at 1.5x | all | 14 | 3 | 1.442 | +42.9% | 33 | +38.5% | +13 | 3 of 10 |
| 30 minutes after the open | A (0.29 / 0.97) | all | 493 | 149 | 1.599 | +71.4% | 1,891 | +68.1% | +1,288 | 23 of 28 |
| 30 minutes after the open | B | all | 493 | 149 | 1.599 | -12.9% | 1,891 | -14.3% | -271 | 8 of 28 |
| 30 minutes after the open | C (0.28 / 0.99) | all | 4 | 3 | 3.166 | +175.0% | 15 | +185.7% | +29 | 3 of 3 |
| 60 minutes after the open | A (0.27 / 1.00) | all | 445 | 137 | 1.625 | +76.8% | 1,712 | +73.3% | +1,254 | 23 of 28 |
| 60 minutes after the open | B | all | 445 | 137 | 1.625 | -5.2% | 1,712 | -6.3% | -109 | 11 of 28 |
| 60 minutes after the open | C (0.25 / 1.02) | all | 30 | 11 | 1.980 | +95.7% | 118 | +99.7% | +117 | 10 of 10 |

In version C at 1.3x, BSP is compared with the price paid after TAB's deduction:

| bet time | half | bets with a BSP | BSP under the price paid | mean log(price paid / BSP) | A/E vs BSP |
|---|---|---|---|---|---|
| TAB's first price | 1st | 65 | 43 (66.2%) | +0.272 | 0.915 |
| TAB's first price | 2nd | 65 | 37 (56.9%) | +0.092 | 1.163 |
| TAB's first price | all | 130 | 80 (61.5%) | +0.182 | 1.024 |
| 60 minutes after the open | all | 28 | 24 (85.7%) | +0.321 | 1.286 |

**What it means.**
- **Priced as a bettor at the open would have priced it, the rule still profits, but on few bets.** It made 131 bets in
  30 months (about four a month), at +23.0% flat. The Kelly stakes are small, so +46.6% Kelly is only +68 units. Only
  15 of 29 months were in profit, and the first half was +9.6%. At about one standard error from zero, that is not
  enough to call an edge.
- **Nearly all of Test 49 came from the field changing after the open.** A made 1,047 bets and C made 131. TAB's
  opening book runs at about 133%. Once the field is priced as it stood, TAB rarely opens a dog at 1.3x our price.
- **The bets C makes do beat BSP.** BSP was under the price paid on 61.5% of them, and the price paid averaged about
  20% above BSP (exp 0.182).
- **Waiting does not help.** By 30 to 60 minutes after the open, ours has a blend weight of only 0.25-0.28, and C makes
  4 and 30 bets. That is too few to read.
- **Next.**
  - **The live card** already prices the declared field the night before, so its bets at TAB's open are the honest
    test going forward.
  - **More prices at the open.** One bookmaker at a 133% book rarely leaves 1.3x. Round 31 (every rule at TAB's,
    Sportsbet's and Ladbrokes' first prices, after deductions) prices the field that ran. Its market-only rules are
    fair as they stand, and its model rules need the field at the bet (round 34).

## Test 52: every rule at TAB's prices, paid after TAB's deduction (13 Nov 2026, gh topaz run 43414576249, `topaz_round31.py`)

Founder: "Well try all rules", then "Did you apply 6c to every bet?"

**The test.**
- **The model:** the production model, refitted every 6 months from November 2022 on every race before. Every price is
  out of sample: nine refits, the last fitted on 103,730 races.
- **The bench:** 32,981 races with TAB's first and last price on every runner.
  - Rules are chosen on 1 May 2023 to 12 Jun 2025 (18,979 races).
  - They are scored once on 13 Jun 2025 to 12 Nov 2026 (14,002 races), with the halves split at 11 Mar 2026.
- **The prices:** three, all paid after TAB's deduction for the dogs scratched after the price was struck (Test 50's
  table):
  - TAB's first price;
  - TAB's last price before the jump;
  - the best first price of TAB, Sportsbet and Ladbrokes.
- **The rules:** 143 segments x price bands x bets, 24,024 rules in all.
  - The bets are every runner, our top pick, and the price at 1.0, 1.1, 1.2, 1.3, 1.5 or 2.0 times our blended price.
  - Our blended price is ours blended each month with that price's own book, fitted on the 6 months before.

**What is fair here and what is not.**
- **The every-runner rules are fair.** They use no model, so the field does not matter.
- **The rules that use ours are not fair.** Ours priced the field that ran, not the field at the bet. Test 51 shows how
  far that moves the 1.3x rule: 1,047 bets at -10.7% on the field that ran, against 131 bets at +23.0% on the field at
  the bet. Round 34 re-runs every rule on the field at the bet.

In 22.1% of bench races a runner was scratched after TAB's open. TAB's deduction in those races was a median 13c in the
dollar.

**Log loss on the 32,452 bench races where every book prices every runner** (lower is better; ours knew the final field,
which flatters it):

| book | log loss | less TAB's first book |
|---|---|---|
| ours | 1.5761 | -0.0037 |
| ours blended with TAB's first book | 1.5496 | -0.0302 |
| ours blended with TAB's last book | 1.4973 | -0.0824 |
| TAB's first book | 1.5797 | 0 |
| TAB's last book | 1.5014 | -0.0784 |
| GRV's SP | 1.5493 | -0.0304 |
| BSP | 1.4868 | -0.0930 |

**Every runner, $1.50-$100, by bet** (returns after TAB's deduction):

| price | bet | choosing: bets, return | scored 1st half: bets, return | 2nd half: bets, return | scored: bets, A/E vs the price paid, return, z |
|---|---|---|---|---|---|
| TAB's first price | every runner | 132,886, -34.0% | 48,076, -36.8% | 48,229, -37.4% | 96,305, 0.770, -37.1%, -54.2 |
| TAB's first price | our top pick | 17,908, -9.4% | 6,563, -12.2% | 6,665, -12.4% | 13,228, 0.916, -12.3%, -12.3 |
| TAB's first price | price 1x ours or more | 11,332, +6.3% | 2,603, -12.4% | 2,213, -8.7% | 4,816, 1.109, -10.7%, -5.0 |
| TAB's first price | price 1.1x ours or more | 5,398, +18.0% | 1,171, -17.8% | 948, -11.9% | 2,119, 1.217, -15.1%, -4.8 |
| TAB's first price | price 1.2x ours or more | 2,710, +26.9% | 606, -14.1% | 513, -16.7% | 1,119, 1.337, -15.3%, -3.5 |
| TAB's first price | price 1.3x ours or more | 1,459, +36.5% | 350, -16.9% | 295, -18.5% | 645, 1.479, -17.6%, -3.3 |
| TAB's first price | price 1.5x ours or more | 519, +62.6% | 138, -8.5% | 114, -38.8% | 252, 1.584, -22.2%, -2.8 |
| TAB's first price | price 2x ours or more | 69, +149.6% | 22, -16.9% | 14, +22.5% | 36, 2.469, -1.6%, -0.1 |
| TAB's last price before the jump | every runner | 130,153, -27.3% | 47,159, -28.0% | 47,377, -29.4% | 94,536, 0.802, -28.7%, -31.3 |
| TAB's last price before the jump | our top pick | 16,970, -14.3% | 6,097, -13.7% | 6,186, -13.3% | 12,283, 0.870, -13.5%, -13.4 |
| TAB's last price before the jump | price 1x ours or more | 3, +76.2% | 0 | 0 | 0 |
| best first price of the three | every runner | 132,941, -30.3% | 48,025, -34.2% | 48,185, -34.7% | 96,210, 0.801, -34.5%, -47.4 |
| best first price of the three | our top pick | 18,147, -5.2% | 6,625, -9.7% | 6,723, -10.0% | 13,348, 0.944, -9.8%, -9.6 |
| best first price of the three | price 1x ours or more | 16,990, +0.8% | 3,660, -11.6% | 3,262, -11.4% | 6,922, 1.052, -11.6%, -4.2 |
| best first price of the three | price 1.1x ours or more | 8,643, +10.7% | 1,606, -12.9% | 1,356, -8.0% | 2,962, 1.155, -10.7%, -2.0 |
| best first price of the three | price 1.2x ours or more | 4,454, +22.2% | 816, -19.3% | 711, -8.4% | 1,527, 1.263, -14.2%, -2.3 |
| best first price of the three | price 1.3x ours or more | 2,454, +34.6% | 460, -16.7% | 411, -5.2% | 871, 1.402, -11.3%, -1.2 |
| best first price of the three | price 1.5x ours or more | 924, +53.1% | 182, +6.5% | 154, -22.1% | 336, 1.646, -6.6%, -0.5 |
| best first price of the three | price 2x ours or more | 159, +155.6% | 34, +5.7% | 23, +57.2% | 57, 2.528, +26.5%, +0.6 |

At TAB's last price the 1.1x to 2x rules made no bets at all, in any year. By the jump our blend is TAB's book, so
TAB's price is never above our price.

**Chosen on the first years, scored once on the rest.** A rule is chosen when it had 300 or more bets and a profit in
the choosing years:

| price | rules with 300+ bets | chosen | chosen, profit in the scored years | chosen, profit in both halves | chosen, z >= 2 in the scored years | z >= 2 expected by luck |
|---|---|---|---|---|---|---|
| TAB's first price | 1,579 | 353 | 36 | 11 | 0 | 8.1 |
| TAB's last price before the jump | 1,162 | 1 | 0 | 0 | 0 | 0.0 |
| best first price of the three | 1,810 | 496 | 64 | 19 | 0 | 11.4 |

**Re-chosen every month** on the 12 months before (150 or more bets and a profit there), then bet:

| price | rules chosen a month | half | bets | winners | A/E vs the price paid | return | units | months in profit |
|---|---|---|---|---|---|---|---|---|
| TAB's first price | 22-69 | 1st | 3,214 | 1,055 | 0.999 | -15.7% | -505 | 1 of 10 |
| TAB's first price | 22-69 | 2nd | 2,698 | 979 | 1.022 | -6.7% | -181 | 2 of 9 |
| TAB's first price | 22-69 | all | 5,912 | 2,034 | 1.010 | -11.6% | -686 | 3 of 18 |
| TAB's last price before the jump | 10-22 | all | 4,531 | 884 | 0.855 | -27.1% | -1,227 | 1 of 18 |
| best first price of the three | 62-206 | 1st | 6,444 | 1,999 | 0.969 | -13.5% | -871 | 1 of 10 |
| best first price of the three | 62-206 | 2nd | 5,161 | 1,605 | 0.944 | -15.2% | -786 | 0 of 9 |
| best first price of the three | 62-206 | all | 11,605 | 3,604 | 0.958 | -14.3% | -1,657 | 1 of 18 |

**What it means.**
- **Backing at the open costs about 35c in the dollar.** Every runner at TAB's first price returned -37.1% after the
  deduction, and the best of three bookmakers -34.5%. TAB's last price costs less, at -28.7%. That is the price of
  betting blind at the open, and every rule has to beat it.
- **No rule survives choosing and scoring.** Of the 849 rules chosen at the open (353 at TAB's first price, 496 at the
  best of three), none reached z 2 in the scored years. Luck alone would give about 19, so the profits in the choosing
  years were noise.
- **Re-choosing every month loses too.** It lost 11.6% at TAB's first price and 14.3% at the best of three, with 3 and
  1 of 18 months in profit.
- **The model rules here lose, but they are not the honest test.** At 1.3x the choosing years made +36.5% and the
  scored years -17.6%. These bets sit in races where a dog came out later (Test 50). Round 34 prices the field as it
  stood at the bet.
- **A/E above 1 with a loss is the deduction.** The 1.3x rule's winners came in 48% more often than TAB's first price
  said (A/E 1.479). TAB's deduction then took more than that edge back.
- **On log loss ours beat TAB's opening book, but only just.** Ours scored 1.5761 against 1.5797, and that is with ours
  knowing the final field. Blended, the two scored 1.5496, about level with GRV's SP (1.5493). BSP (1.4868) and TAB's
  last book (1.5014) are well ahead of both. The market learns a lot between the morning and the jump.
