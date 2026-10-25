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
