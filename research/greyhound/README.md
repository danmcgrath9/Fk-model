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
