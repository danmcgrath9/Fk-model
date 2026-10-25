# Harness Phase 1: data sources (25 Oct 2026)

Follows docs/HARNESS_MODEL_BRIEF.md, Phase 1. Founder's call the same day: harness now, not after greyhounds.

## How this was checked, and what is not yet checked

The Claude cloud session's network refuses harness.org.au, thetrots.com.au, historicdata.betfair.com, betfair.com.au,
the Betfair data scientists site and betmatic.app. Everything below came from search results. **No provider's terms
have been read from the page itself yet.** The `fk read terms` workflow fetches a page as text into the run log from
GitHub's runners, which can reach those hosts; terms are read that way before anything is downloaded.

## Sources

| Source | Holds | Back to | Access | Terms (as found) | Cost |
|---|---|---|---|---|---|
| harness.org.au (the shared national site of HRA, the state bodies and the clubs; RISE runs it) | Fields, form, results, every state | Long-run | Web pages | Legacy terms: no copying or re-transmitting "except with express approval". Current terms unread. **Not downloadable without approval.** | Free to view |
| RISE Racing (harness industry data and systems company) | "Commercial API"; PJ Data refers bulk historic sectionals to RISE since Nov 2022 | Unknown (PJ Data sectionals from 2015) | Ask: siteadmin@riseracing.com | Not published | Not published |
| HRV | Victorian fields; its race-fields licence is for wagering service providers | - | Via RISE / harness.org.au | WSP business use only | WSP fees |
| HRNSW and other states | HRNSW sectional PDFs per meeting: gross time, mile rate, lead time, four quarters, position and width at 800m and 400m | Seen Apr 2024 to Feb 2026 | PDFs | Unread | Free |
| Betfair Hub CSVs | ANZ harness, per runner: BSP, win/place result, WAPs, LTP, pre-play and in-play max/min matched, best prices at the scheduled off; harness model-results files too | Yearly 2020-2025, monthly 2026 | Free, no login | Unread | Free |
| Betfair historic data (Advanced/Pro) | Full exchange stream, timestamped from market creation | AU from Oct 2016 | Paid download; Betfair asks ANZ customers to contact them first | Unread | Not confirmed |
| PuntersEdge | Per bookmaker: first price after the open, last pre-jump price, finish | 4 Aug 2026 only; price paths kept 45 days | API | Personal on Free/Hobby/Standard; commercial from Business | Business $99/mo, Platform $199/mo |
| BetMatic (ours) | TAB's price from our own bot; odds request accepts code "Harness" | From when we record | WebSocket (enabled 18 Oct) | Our account | Already paid |
| FormFav | Harness form and results (their analysis, not the official feed) | Unknown | API, Pro, 7-day trial | Not found | Not found |
| Form King, Punting Form | Thoroughbreds only (Form King raceType Flat/Hurdle; Punting Form per a competitor's page) | - | - | - | - |

## Findings

1. **No historical timestamped opening price per runner exists in any source found.** PuntersEdge has about 12 weeks
   from 4 Aug 2026. Betfair Pro has a timestamped exchange open from 2016, but harness exchange markets open thin, so
   that open needs measuring before it is trusted, and it is not the bookmaker open the gallops edge was found at.
2. So the open is recorded forward: `betmatic/harness_open_watch.py` (workflow `fk harness opens`). The gallops README
   already found back-filled opens differ from live ones (+41.9% back-filled, -11.6% live), so a recorded open is the
   honest quantity anyway.
3. Licensed form, results and sectionals mean RISE. Emailed 25 Oct 2026 (personal betting only; nothing published or
   shared). That promise covers anything derived from RISE data: no harness tips or cards while it stands.
4. BSP history is free (Betfair Hub, 2020 on), subject to the terms read.

## The recorder: what it stores and what it cannot say

Per race (data/harness_opens/YYYY-MM-DD.json): `last_empty_at` (last poll with no market) and `opened_at` (first poll
with prices), so the open happened between them; per runner per bookmaker, the first win and place price and when.
`open_seen_on_first_poll` true means the market was already up when we first looked: those prices may have moved, so
those races are left out of any open-price test. Gaps between runs widen the bracket, and the bracket says so.

## Open questions

- Does BetMatic's schedule carry harness under code "Harness", and is the bot's TAB session answering for it? The first
  run says (it stops with the codes it saw if not).
- When does TAB open harness markets? Measured by the recorder.
- Where it runs long-term: continuous recording is about 1,440 Actions minutes a day. That is free while this repository
  is public and roughly US$300+ a month if it is made private, so the founder's always-on machine may be the place.

## Test 1: Betfair's free ANZ harness files (25 Oct 2026, `fk harness betfair`, research/harness/profile_betfair.py)

Terms: read through `fk read terms` from the data listing page itself. Its only condition on downloading is a
disclaimer (no warranty as to accuracy or completeness; use at your own risk). Downloaded fresh on each run from
Betfair; nothing mirrored or committed. harness.org.au's terms page answered 403 to GitHub's runner too (it blocks
automated clients), and historicdata.betfair.com did the same; neither was pushed past.

What the files hold: 15 files (yearly zips 2020-2025, monthly CSVs Jan-Sep 2026), 41 columns, the same in every file.

| | |
|---|---|
| Runner rows | 1,043,222 as published; 1,025,126 after removing 18,096 duplicates |
| Win markets (races) | 112,242, Jan 2020 to Sep 2026, every month present (1,100 to 1,600 races a month) |
| By state | NSW 26,834, VIC 24,950, QLD 18,078, NZ 15,569, WA 14,406, SA 6,838, TAS 4,817, ACT 750 |
| By gait | Pace 96,332, Trot 15,870 (a few dozen races carry a class word in the gait field instead) |
| Win BSP present | 84.4% of rows overall; 77% to 98% by month, about 80% to 87% since 2022 |
| Place BSP present | 62.7% of rows |
| Tracks | 125; Albion Park, Redcliffe, Gloucester Park, Menangle and Melton carry the most |

Columns, all one row per runner per race: meeting date, scheduled and actual off time, track, state, race number,
distance, gait (RACE_TYPE), win and place market ids and the win market name (e.g. "R1 2138m Trot S"), selection id,
TAB number, name, win and place result, win and place BSP and BSP volume, pre-play max/min/last/weighted-average price
and volume, in-play the same, best back and lay at the scheduled off and the book percentages there.

What they do NOT hold: any timestamped early price (the earliest prices are pre-play extremes and averages over the
whole pre-play period, with no time on them), driver, trainer, barrier draw (TAB_NUMBER is the saddlecloth, which in
harness usually follows the draw but is not guaranteed to), start type stated as such (the trailing letter in the
market name may encode it: not yet checked), margins, mile rate, sectionals, or whether a horse broke.

Data quality: several 2021 and 2022 monthly files (Jan-Apr 2021, Jul-Sep 2021, Jan-Mar 2022, Jul-Aug 2022, Oct-Nov 2022)
carry exactly the row count of a neighbouring file and start days before their own month, i.e. they overlap. Removing
duplicate (market, selection) pairs leaves every month at a normal size, but a file with an identical row count to its
neighbour may also be missing rows of its own month; spot-check a few days against another source before trusting
2021-22 month by month. Two of the first profile's errors were mine and are fixed: the meeting date is written day
first (1/12/2020 is 1 December), and coverage was first counted on place BSP instead of win BSP.

Use: BSP history for the Phase 2 scoring (KL to BSP, winner log loss) and the BSP lay test, across about 96,700
Australian races. Not usable for the open-price edge, which still needs the recorder.
