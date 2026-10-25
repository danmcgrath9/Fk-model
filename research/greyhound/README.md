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
