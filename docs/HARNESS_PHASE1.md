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

## Test 2: how sharp is BSP for harness? (25 Oct 2026, research/harness/t_bsp_sharp.py, `fk harness betfair`)

Founder's question. Betfair's free files, Jan 2020 to Sep 2026, duplicates removed. A race counts when at least four
runners carry a BSP above $1, there is exactly one winner, and the winner has a BSP: 96,209 Australian harness races,
863,818 runners. Thoroughbreds (Betfair's ANZ files, Jan 2024 to Sep 2026, 46,596 Australian races) run the same way as
the yardstick. NZ harness is left out: only 48 NZ races carry a usable BSP.

Calibration: wins against what BSP says (expected = sum of 1/BSP), back ROI flat 1 unit at BSP, BEFORE commission.

| BSP band | harness runners | harness A/E | harness back ROI | gallops A/E | gallops back ROI |
|---|---|---|---|---|---|
| $1-$2 | 27,081 | 1.000 | -0.0% | 1.001 | -0.0% |
| $2-$3 | 39,738 | 1.005 | +0.7% | 0.998 | -0.1% |
| $3-$4 | 43,293 | 1.003 | +0.3% | 1.011 | +1.1% |
| $4-$6 | 76,276 | 1.000 | +0.1% | 1.003 | +0.3% |
| $6-$8 | 61,634 | 0.996 | -0.5% | 0.984 | -1.5% |
| $8-$11 | 75,864 | 1.007 | +0.5% | 0.988 | -1.0% |
| $11-$16 | 88,498 | 0.996 | -0.5% | 0.991 | -1.0% |
| $16-$21 | 60,093 | 0.993 | -0.6% | 0.990 | -0.9% |
| $21-$31 | 80,667 | 0.966 | -3.5% | 1.005 | +0.5% |
| $31-$51 | 87,888 | 0.974 | -2.5% | 0.931 | -6.5% |
| $51+ | 222,751 | 0.985 | -0.0% | 0.980 | -7.3% |
| all | 863,818 | 0.999 | -0.6% | 0.996 | -2.5% |

Winner log loss, each price renormalised per race (lower = sharper), on the races where all three exist:

| | harness (96,052 races) | gallops (46,575 races) |
|---|---|---|
| BSP | 1.5716 | 1.7651 |
| pre-play weighted average price | 1.5762 | 1.7700 |
| best back at the scheduled off | 1.5813 | 1.7698 |
| BSP's gain over the pre-play WAP | 0.0046 | 0.0049 |

The two codes' log losses are not comparable with each other (harness fields are smaller and more favourite-heavy:
27,081 harness runners went off under $2 against 5,936 gallopers); the gain from pre-play to BSP is, and it is the same.

Stability, harness: A/E overall 0.993 to 1.004 in every year 2020-2026; 0.995 to 1.006 in every state; 0.997 and 1.001
in the two date halves; BSP's log loss beats the pre-play WAP's in every year, state, volume tercile and half. The only
leans: runners from $21 to $51 win 3% fewer than BSP says in both halves combined (A/E 0.966 and 0.974), and in the
lowest-volume third of races runners under $4 win 2.4% more than BSP says (A/E 1.024).

What it says:
1. Harness BSP is as sharp as gallops BSP: within half a percent of fair in every band up to $21, overall 0.6% under
   fair before commission. Backing at BSP is a zero-edge bet before commission and a loser after it, as it is in gallops.
2. The $21-$51 lean is worth +2.5% to +3.5% to a BSP layer per $1 of the backer's stake before commission. Commission is
   charged on net winnings and a typical exchange rate (5% or more) is larger than that, so it is not an edge by itself;
   it is a place for the model-disagreement lay rule (ours/BSP >= 1.6) to start looking, nothing more.
3. BSP is the sharpest price Betfair records, better than anything pre-play, so it is the right yardstick for Phase 2:
   a harness model is good when it gets close to BSP, and useful only where it is close AND a softer price exists
   earlier, which brings it back to the opening price the recorder is collecting.
4. Calibration on average is not the same as unbeatable runner by runner: these tables say the market has no bias by
   price band, not that a model cannot find the runners it has wrong. That needs form data (RISE).

## Test 3: a price from the market's own history of each horse, scored against BSP (25 Oct 2026, hx_model.py)

Founder: build on what we have while RISE is asked. Inputs, all from races that started BEFORE this one in Betfair's
files: the horse's last three BSP chances and its five-run mean, runs, days since, wins and places, wins against what
BSP expected, last start's BSP rank and in-running low, changes of distance, track and gait; plus the field (track,
state, distance, gait, TAB number, field size, the market name's last word). No current-race price. Scratchings excluded
from history. Trees (LightGBM, 289 rounds by early stopping) and a logistic regression; the validation months chose
the trees alone. Train 64,799 races to 30 Jun 2024; validation 7,299 (Jul-Dec 2024); holdout 24,111 (Jan 2025 to Sep
2026), split at 15 Nov 2025.

| price | winner log loss, 1st half | 2nd half | KL to BSP, 1st half | 2nd half |
|---|---|---|---|---|
| equal chances | 2.1901 | 2.1832 | 0.5826 | 0.6089 |
| market-history model | 2.1017 | 2.1026 | 0.4934 | 0.5185 |
| pre-play WAP | 1.5942 | 1.5794 | 0.0084 | 0.0107 |
| BSP | 1.5897 | 1.5692 | 0 | 0 |

By month the model closes 10% to 16% of the distance from equal chances to BSP (every month, no trend). Biggest inputs
by gain: track 18.9%, mean of the last five BSP chances 13.5%, last start's BSP rank 10.9%, field 7.9%, last BSP chance
7.7%, days since 5.9%, TAB number 3.7%.

Verdict: market history alone is nowhere near BSP. For scale, the gallops model with full Form King form sat at KL
0.08-0.09 against an opening market at 0.14; this sits at 0.49-0.52. A horse's past prices say who the market rated,
not why, and in harness the why (driver, draw, how the race will be run, the horse's actual times) is the price. The
pipeline (point-in-time history, cut-off, halves, KL by month) is built and is where RISE's form drops in.

## Test 4: betting angles at BSP, both halves, 8% commission (25 Oct 2026, hx_angles.py)

82,587 Australian races, Jan 2021 to Sep 2026 (2020 builds the history), split at 15 Nov 2023. Every angle is a back or
a lay at BSP because BSP is the only price the files carry. Each table also shows the back ROI without the group's ten
biggest wins. Full tables are in the run's step summary (`fk harness betfair`, run 40177753707).

Held in both halves after commission: one.

| angle | half | bets | wins | A/E | lay ROI after 8% |
|---|---|---|---|---|---|
| TAB 1 pacers under $4 (lay) | 2021-Nov 2023 | 7,232 | 2,991 | 0.932 | +3.2% |
| | Nov 2023-Sep 2026 | 6,353 | 2,569 | 0.950 | +0.4% |

The lean behind it is the clearest in the set: TAB 1 pacers as a whole win 4.4% and 7.1% less than BSP says (A/E 0.956
and 0.929 on 35,654 and 34,164 runners), and TAB 2 and TAB 1-2 in fields of 10+ lean the same way (A/E 0.92-0.97). The
market overrates the inside draw in pacers. After an 8% commission the lay is close to break-even (+1.8% across both
halves), so whether it pays depends on the commission actually charged; at 5% it would be about +3.5% (the 3 points saved apply only to the 59% of lays that win). Not a bet yet: one
lean that survives about thirty angles tried is what chance alone would also produce now and then, so it needs a
forward test on races after September 2026 before it is believed.

Did not hold (selected): favourites (A/E 0.998/1.008, lose 3-5% after commission either side); favourites in
low-volume races (A/E 1.009/1.033, still -1.3% to -4.1% backed); $21-$51 lay (-7.1%, -2.5%); first up, backed up,
beaten favourite, unlucky last start (traded $1.50 or less and lost), surprise last-start winners, gait switchers, horses
that beat BSP before: all within commission of zero in at least one half.

Model-disagreement angles (Test 3's model on its holdout): the only group positive in both halves, runners the model
rates at 0.625x BSP or less at $15-$30 BACKED, is 86 and 61 bets with 8 and 6 winners, and minus its ten biggest wins it
is -100%: noise. Runners the model rates at 2x BSP or more win less than BSP says (A/E 0.933, 0.921): BSP is right about
them and the model is wrong, as expected of a model this far from BSP.

Place market (63,333 races after cleaning; 1,764 dropped for infinite or absurd place BSPs or a placed count that does
not match the places paid): every band from $1 to $50 is within commission of zero. Place BSPs of $50 and up show A/E
2.59 and 1.16 and +444%/+41% backed, but minus the ten biggest wins the second half is -1.9%, and a place BSP above $50
is set by almost no money: a real bet there moves the price it is settled at. Read as illiquid prices, not an edge. The
first run of this test reported two place "edges" before the cleaning; both came from infinite place BSPs in Betfair's
files.

## Test 5: the opening-price recorder's first run (25 Oct 2026, `fk harness opens` run 40176208641)

Ran 7:20pm to 12:51am Sydney time on Sunday 25 Oct, every race in BetMatic's "Harness" schedule starting within 36
hours: 124 races at 13 venues. BetMatic's harness schedule is not only Australian: it carried French (Enghien, Salon de
Provence, Le Croise Laroche), North American (Woodbine, Flamboro Downs, Northfield Park, Yonkers) and New Zealand
(Ashburton) meetings beside Redcliffe, Dubbo, Globe Derby, Pinjarra and Hamilton.

| | |
|---|---|
| Requests answered | 12,926 (each race asked about 106 times) |
| Requests unanswered within 20 s | 162 (1.2%); the WebSocket reconnected on its own |
| Races already open at our first look | 17 (Redcliffe's evening card, Ashburton's next-day card) |
| Races that opened while watched | 8, all French (Salon de Provence, Enghien) |
| Races still not open when the run ended | 99, including every Australian Monday meeting (Dubbo, Globe Derby, Pinjarra) |
| Bracket on the 8 opens (opened_at minus last_empty_at) | median 3.2 min, range 2.3 to 5.9 min |
| When those 8 opened | 20 to 40 minutes before the start |
| Bookmakers seen | TAB and Sportsbet (the bot's two sessions); on Salon R4 Sportsbet priced 2 min before TAB, otherwise together |

What it says:
1. The recorder works: answers come back, are paired to the right race, and an open is timed to about three minutes.
   The bracket is the length of one pass over every watched race, so watching fewer races narrows it.
2. No Australian open was caught. Tonight's Redcliffe card was already up at 7:20pm, and Monday's Australian meetings
   were still not up at 12:51am, so Australian harness markets open some time between 1am and the evening of race day
   at the latest; the next run has to cover the morning.
3. Overseas races are a third of the schedule and slow every pass: filter to Australian venues.
4. Proposed (founder to OK): an Australian-venue filter, and the workflow scheduled four times a day (about 5am, 10:30am,
   4pm and 9:30pm Sydney, 5.5 hours each), which covers about 22 hours a day with half-hour gaps. Free while the
   repository is public.
