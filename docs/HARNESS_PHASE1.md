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
