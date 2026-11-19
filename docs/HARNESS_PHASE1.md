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
| Requests answered | 10,820 (median 106 per race; a race stops being asked once it starts or every runner is priced) |
| Requests unanswered within 20 s | 162 (1.5% of 10,982); the WebSocket reconnected on its own |
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
4. Done 26 Oct (founder OK): an Australian-venue filter (config/harness_au_tracks.txt), races more than 6 hours out asked every 10 minutes instead of 2, and the workflow scheduled four times a day (about 5am, 10:30am,
   4pm and 9:30pm Sydney, 5.5 hours each), which covers about 22 hours a day with half-hour gaps. Free while the
   repository is public.

## Test 5b: the recorder's second run, Monday morning (26 Oct 2026, run 40245645282, cancelled at 2:16pm)

Australian venues only, lighter polling. Cancelled at 2:16pm Sydney by us (founder: "don't get my TAB limited"); the
record was kept. Monday's four Australian meetings (Dubbo, Globe Derby, Hamilton, Pinjarra: 32 races) were already
priced at the run's first look at 10:38am, by TAB and Sportsbet together, and they had not been at 12:51am, so they
opened between 1am and 10:38am on race day (the bracket, about 9.9 hours, is honest and too wide to use). Tuesday's
42 races were not open by 2:16pm Monday. So Australian harness markets open on the MORNING OF RACE DAY: a recorder
only has to watch race-day mornings, which is a small fraction of the reads of round-the-clock watching. The schedule
is paused until the founder decides how far odds reads through his TAB session may go.

## Test 6: model v2 and v3, and a ranking model (26 Oct 2026, hx_model.py, runs 40262142697 and 40263348982)

Same splits as Test 3 (train to 30 Jun 2024, validation Jul-Dec 2024, holdout 24,111 races 2025-26 in two halves).
v2 adds each horse's market rating per run, log(BSP chance x field), smoothed, best and trend; how it ran against its
price and in running; its rating against today's rivals and its rank in the field; and point-in-time draw records by
track, gait and TAB number. v3 adds its record in the place market (placed minus place-BSP chance, smoothed), its
in-running high last start, the class move (today's rivals against last start's) and its rating at this track and
distance band. A test pins that every input uses earlier races only.

| inputs | LL 1st half | LL 2nd half | KL to BSP 1st half | KL 2nd half | gap to BSP closed |
|---|---|---|---|---|---|
| v1 (Test 3) | 2.1017 | 2.1026 | 0.4934 | 0.5185 | 13.9% |
| v2 | 2.0966 | 2.1017 | 0.4893 | 0.5159 | 14.4% |
| **v3** | **2.0844** | **2.0916** | **0.4776** | **0.5045** | **16.3%** |
| v3 as a ranking model (lambdarank, winner 2, placed 1) | 2.1029 | 2.1065 | 0.4966 | 0.5213 | 13.5% |

v3 is better than v2 in both halves on both measures, and closes 12% to 21% of the gap by month (every month). Its
biggest inputs by gain: rating against today's rivals 16.6%, track 16.0%, field 6.2%, class move 5.9%, rating at this
track 4.7%, draw win rate 4.0%. The ranking objective is worse than the win model on the same inputs; dropped.

## Test 7: Benter's second stage (26 Oct 2026, hx_stage2.py)

Founder: "Are we doing a Benter style model?" Yes in structure: stage 1 (the fundamental model), then stage 2,
log p = a x log(model) + b x log(market), fitted on validation. The market for live bets will be the open; until enough
opens are recorded the pre-play weighted average price (WAP) stands in for it.

| price | LL 1st half | LL 2nd half | KL to BSP 1st half | KL 2nd half |
|---|---|---|---|---|
| v3 model alone | 2.0845 | 2.0918 | 0.4777 | 0.5045 |
| pre-play WAP alone | 1.5942 | 1.5794 | 0.0084 | 0.0107 |
| stage 2: model + WAP (fitted: a = 0.00, b = 1.00) | 1.5942 | 1.5794 | 0.0084 | 0.0107 |
| BSP | 1.5899 | 1.5697 | 0 | 0 |

Same answer with v2 (a = 0.00). The fit gives the model NO weight: a model built from a horse's past Betfair prices
knows nothing the market does not, because those prices are the market's own opinion. Benter's edge came from form the
market had not fully priced; this is the measured case for waiting on RISE's form and sectionals. Stage 1 can still be
made closer to BSP on Betfair data, but no bet should be expected from it until stage 2 gives the model a weight.

## Test 8: Betwatch's driver, trainer, class and TAB prices joined to Betfair (18 Nov 2026, bw_model.py, run 44261848718)

Founder, 18 Nov: "Times and sectionals would be the most important but sure, Option 3": build now from Betwatch (driver,
trainer, class, track condition, TAB's timestamped prices from Nov 2022) joined to Betfair's free files, and add RISE's
times and sectionals when its reseller is available. Betwatch data is for our own use only: it lives in this
repository's Actions cache, the logs print counts and scores, and nothing per runner is committed or uploaded.

**The pull** (run 44209230835, 87 minutes): all 49 months from Nov 2022 to 17 Nov 2026, every month complete. 59,159
races and 533,999 runners not scratched, 1,000 to 1,400 races a month; TAB price changes on 99%+ of runners in every
month.

**The join**, by Betfair market id and selection id only: 99.1% of Betwatch races carry a Betfair win market id. Of the
57,342 Australian Betfair races inside Betwatch's dates, 51,168 joined (89.2%), 460,807 runners (88.9%). Betfair's winner
is also first in Betwatch's results in 50,636 of 50,668 races, and Betwatch's runner number equals Betfair's TAB number
on 100.0% of joined runners. Model races (every starter joined, all with a BSP, one winner, field 4+, from 2023): 48,630,
with a driver on 99.9% of runners, a trainer on 99.8%, a TAB first price on every runner in 99.8% of races.

**The first run is void (runs 44249952697 and 44258812960).** It closed 108% of the gap to BSP, i.e. beat BSP, and
showed +100% ROI at TAB prices, which cannot happen without the result leaking in. It did: driver, trainer and barrier
records were running sums taken row by row in start order, and a key that more than one runner in a race shares then
carried that race's winner into the rows sorted after it. Two keys did this. Betwatch's `barrier` field for harness is
not a barrier draw: it is 0 for most runners (99th percentile 20) and the same for every runner in 95.8% of races,
which reads as a handicap in metres; its record "at this barrier" was the leak's biggest carrier and was the top input.
And a trainer with two runners in one race. Records are now totals over races that STARTED EARLIER only
(bw_data.prior_totals), with a test for both cases; the leak check stays in the script. The draw itself is in the model
through the TAB number, which in Australian harness follows the barrier draw.

**Holdout** (9,804 races, 1 Jan to 31 Oct 2026, never seen in fitting; train 2023 to Jun 2025, validation Jul-Dec 2025):

| price | LL 1st half | LL 2nd half | KL to BSP 1st half | KL 2nd half | gap to BSP closed |
|---|---|---|---|---|---|
| equal chances | 2.1698 | 2.1773 | 0.6071 | 0.6182 | 0% |
| v3, market history only (Tests 3 and 6, refitted on these races) | 2.0794 | 2.0789 | 0.5066 | 0.5082 | 15.4% |
| **v3 + driver, trainer, class, condition (a form price, no price from the race)** | **1.9706** | **1.9739** | **0.4002** | **0.4078** | **32.9%** |
| the same without the barrier field | 1.9723 | 1.9778 | 0.4021 | 0.4088 | 32.4% |
| TAB's first price (median about 9 to 22 hours before the jump) | 1.7120 | 1.7027 | 0.1514 | 0.1475 | 76.2% |
| v3 + people + TAB's first price as an input | 1.6982 | 1.6898 | 0.1399 | 0.1360 | 78.3% |
| **stage 2: log p = 0.20 log(form price) + 1.10 log(TAB first price)** | **1.6963** | **1.6866** | **0.1343** | **0.1303** | **78.8%** |
| TAB's last price before the start | 1.5907 | 1.5892 | 0.0303 | 0.0305 | 95.3% |
| pre-play WAP (9,792 races) | 1.5719 | 1.5707 | 0.0104 | 0.0120 | 98.4% |
| BSP | 1.5609 | 1.5616 | 0 | 0 | 100% |

What this says:
- Driver and trainer are real form. They double what market history alone gets (15.4% to 32.9% of the gap), in both
  halves. The biggest inputs: track 13.6%, driver win rate 10.8%, class 9.6%, trainer win rate 9.4%, rating against
  today's rivals 5.1%. The barrier field adds nothing (32.4% without it).
- For the first time, stage 2 gives the form model a weight against a market price: 0.20 on the form price with 1.10
  on TAB's first price (Test 7 gave market history 0.00 against WAP). The combined price is closer to BSP than TAB's
  first price in both halves (KL 0.134 against 0.151; 0.130 against 0.148): the form sees some of how TAB's morning
  price will move. It is a small step: 76.2% to 78.8%, while TAB's own price moves from 76% to 95% between the morning
  and the jump.
- No price here is close to BSP yet. That needs what the market has and this does not: times, sectionals, gear,
  trials. RISE remains the gap.

**Paper bets on the holdout (no money).** Backing at TAB's first price where the stage-2 chance x that price was at
least 1.05: 307 bets in the first half +17.2%, 317 in the second +20.4%; at 1.10: +29.0% and +37.0%. Both halves are
positive at every cut and for both TAB-open models, BUT with each group's ten biggest wins removed every row is
-15% to -55%: a few long winners carry it, on a few hundred bets a half. That is not evidence of an edge, and TAB's
first price here is the first Betwatch recorded (not guaranteed to be the open) at a bookmaker that limits winners.
Backing at BSP on the form price alone loses 14% to 16% in both halves after commission. **No bet is suggested.** What
would change that: the TAB-open result holding on more bets once sectionals are in, then paper bets recorded forward at
real morning prices before any money.

## Test 9: a form price against TAB's first price, then TAB priced in (18 Nov 2026, bw_form.py, runs 44386590720 and 44389293619)

Founder, 18 Nov: "I want to create a model that beats tab without its prices and then if we price tab in can we win".
Same races and splits as Test 8, restricted to races where every runner has a TAB first price (holdout 9,804 races,
2026, two halves). Two new form prices, neither seeing any price from the race being priced:
- **form+** (110 inputs): Test 8's inputs plus each horse's Betwatch record (finishing positions in every Betwatch race,
  including those Betfair lacks; its rating at TAB's last price in earlier races and how those prices moved), stable and
  driver form over the last 60 days, class and handicap change, and every key rating against the race (minus the race
  mean, and rank). Tested on earlier races only;
- **pure form** (64 inputs): form+ with every input built from any price removed (past BSP, past TAB, in-running
  prices, records measured against a price). Positions, wins, places, driver, trainer, class, handicap, draw, days.

**Part 1: does a form price beat TAB's first price? No.**

| price | LL 1st half | LL 2nd half | KL to BSP 1st half | KL 2nd half | gap to BSP closed | beats TAB first? |
|---|---|---|---|---|---|---|
| people (Test 8) | 1.9731 | 1.9766 | 0.4012 | 0.4087 | 32.5% | no |
| form+ | 1.9576 | 1.9607 | 0.3852 | 0.3937 | 35.0% | no |
| pure form | 1.9740 | 1.9799 | 0.4061 | 0.4152 | 32.1% | no |
| TAB first price | 1.7120 | 1.7027 | 0.1514 | 0.1475 | 76.2% | |
| stage 2: form+ with TAB first (0.15 / 1.10) | 1.6967 | 1.6868 | 0.1348 | 0.1307 | 78.7% | yes, both halves |
| stage 2: pure form with TAB first (0.20 / 1.10) | 1.6963 | 1.6868 | 0.1348 | 0.1308 | 78.7% | yes, both halves |
| TAB last price | 1.5907 | 1.5892 | 0.0303 | 0.0305 | 95.3% | yes |

The new inputs add 2.5 points (32.5% to 35.0%); finishing positions and past TAB prices add little beyond what was
there. Biggest inputs: track 13%, trainer win rate against the race 11%, class 9%, driver win rate rank 8%. Pure form
is as good as people, so almost none of the form signal comes from past prices. What the form prices lack is how fast
a horse runs: times and sectionals (RISE).

**Part 2: with TAB priced in, can we win? On paper at TAB's first price, yes in both halves; but read Part 3.**
Backing at TAB's first price where the stage-2 chance x that price clears an edge (no commission):

| edge at least | form+ 1st half | form+ 2nd half | pure form 1st half | pure form 2nd half |
|---|---|---|---|---|
| 5% | 286 bets, +11.9% | 307, +20.1% | 312, +19.6% | 327, +22.8% |
| 10% | 198, +28.8% | 218, +42.6% | 230, +22.8% | 232, +33.1% |
| 20% | 117, +41.5% | 126, +63.7% | 124, +49.5% | 138, +41.3% |

Positive at every cut, both halves, both models; with each group's ten biggest wins removed, every row is -18% to
-52% (a harsh cut on 50 to 100 winners, but the profits do lean on long winners). The form price alone, backed at TAB's
first price, loses 43% to 47%: TAB's first prices carry a large margin (every runner backed at TAB's first price
returns -36.9%).

**Part 3: closing-line value: where the profit comes from.**

| stage-2 bets, edge at least | half | bets | TAB price shortened after the bet | drifted | mean log(first / last) | ROI at TAB first | at TAB last | at BSP, 8% comm. | A/E v BSP |
|---|---|---|---|---|---|---|---|---|---|
| form+, 5% | 1st | 286 | 74% | 22% | +0.294 | +11.9% | -34.4% | -30.4% | 0.82 |
| form+, 5% | 2nd | 307 | 74% | 22% | +0.317 | +20.1% | -26.5% | -17.0% | 0.99 |
| form+, 10% | 1st | 198 | 75% | 22% | +0.329 | +28.8% | -28.1% | -24.7% | 0.87 |
| form+, 10% | 2nd | 218 | 78% | 18% | +0.408 | +42.6% | -18.9% | -9.2% | 1.06 |
| pure form, 10% | 1st | 230 | 73% | 23% | +0.305 | +22.8% | -28.0% | -25.8% | 0.87 |
| pure form, 10% | 2nd | 232 | 77% | 20% | +0.378 | +33.1% | -12.4% | +4.3% | 1.04 |
| every runner (baseline) | both | 87,709 | 30% | 64% | -0.258 | -36.9% | -33.2% | -10.8% | 1.00 |

What this says, plainly:
- The model is good at spotting TAB first prices that are too big: 72% to 83% of its bets shorten afterwards, against
  30% of all runners, and on average TAB's last price is 25% to 40% shorter than the price taken (log 0.29 to 0.54).
  That holds in both halves and is not carried by a few winners.
- The same horses are NOT better than the market thinks. At BSP they win about as often as BSP says (A/E 0.82 to 1.06,
  around 0.95 overall) and lose after commission; at TAB's last price they lose 12% to 34%. The model has no edge on
  the horses; its edge is on TAB's early price.
- So the paper profit exists only if TAB's first price can actually be taken, in size, before TAB moves it. That is
  exactly the bet TAB limits accounts for, and the "first price" here is the first Betwatch recorded (not guaranteed
  to be bettable at that moment, or to be the open).

**Decision for the founder: no bet.** The honest answer to "can we win" is: on TAB's early prices, perhaps, while the
account lasts; on the horses themselves, not yet. To test the early-price edge properly it has to be recorded forward:
at the moment a TAB price first appears, log the model's chance and the price that could really be taken, and see if
the bet would have been accepted (paper; and Test 5's recorder reads TAB through the founder's session, which is why it
is paused). To get an edge on the horses themselves, the form needs times and sectionals.

## Test 10: Racing Queensland's sectionals in the form price (19 Nov 2026, bw_sect.py, run 44437276233)

Founder, 19 Nov: "Just plug in". Racing Queensland publishes a sectional CSV for every TAB harness meeting
(racingqueensland.com.au/industry/harness/harness-sectionals). Its Disclaimer and Copyright page, read first: the site's
information "is intended to be used for personal use only and may not be used for commercial purposes without the
prior written consent of Racing Queensland", and except as the Copyright Act permits nothing "may be reproduced,
re-used or redistributed for any purpose whatsoever, without the express prior written permission". Our use is
personal: the files are in this repository's Actions cache only, the logs print counts. (HRV's Sectionals Hub refuses
every request from GitHub's runners, robots.txt included; it was not worked around.)

**The data** (rq_sectionals.py, run 44433257303): 835 meeting files listed, Nov 2023 to 18 Nov 2026; all fetched; 773
read (62 unreadable or empty, to look at). 59,978 runner rows in 6,734 races. Per runner: lead time, first, middle and
last half, the four quarters (time, metres travelled, position), last mile, top speed, metres travelled.
rq_join.py turns each run into speeds (metres travelled over time: last half, last quarter, first half, lead time),
top speed, each against the race's mean, ground covered beyond the shortest route anyone took, and position at the
first and third quarter; then each horse's record from EARLIER runs only (last, EWMA, best of five). Tested.

**The join** (date, track, race number, horse name): 73.6% of Betwatch runners at RQ's tracks inside RQ's dates; on
joined runners RQ's winner is Betwatch's winner 100.0% of the time and the TAB numbers agree 100.0%. 82% of 2026
Queensland runners had at least one earlier sectional run.

**Holdout: Queensland 2026, 2,039 races** (train 2023 to Jun 2025, of which 3,699 Queensland races with sectionals;
validation Jul-Dec 2025; stage 2 fitted on Queensland validation for both prices, so they compare fairly):

| price | LL 1st half | LL 2nd half | beats TAB first? |
|---|---|---|---|
| equal chances | 2.1335 | 2.1637 | no |
| form (Betwatch-only pure form, the live model) | 1.9419 | 1.9638 | no |
| **form + sectionals** | **1.8218** | **1.8381** | no |
| TAB first price | 1.6520 | 1.6344 | |
| stage 2: form + TAB first (0.25 / 1.30) | 1.6130 | 1.5922 | yes, both halves |
| **stage 2: form + sectionals + TAB first (0.30 / 1.20)** | **1.6090** | **1.5889** | yes, both halves |
| TAB last price | 1.5053 | 1.4988 | yes |

Sectionals are the biggest single lift the form price has had: 0.12 off the log loss in both halves. Measured from
equal chances to TAB's first price, the form price goes from about 39% of the way there to about 63%. Inside stage 2
the gain is small (0.003 to 0.004), and the form's weight rises only from 0.25 to 0.30: TAB's price already knows most
of what the sectionals say. Sectional inputs carry 8% of the tree's gain; the largest is the horse's smoothed
last-half speed against the race, measured against today's field.

**Paper bets at TAB's first price, Queensland 2026** (no commission):

| edge | half | without sectionals: bets, ROI at TAB first, at TAB last | with sectionals: bets, ROI at TAB first, at TAB last |
|---|---|---|---|
| 5% | 1st | 201, +20.4%, -17.4% | 287, +32.7%, -2.2% |
| 5% | 2nd | 187, -7.6%, -32.7% | 285, +6.4%, -22.3% |
| 10% | 1st | 114, +31.3%, -22.1% | 164, +46.1%, -2.2% |
| 10% | 2nd | 109, -2.2%, -36.4% | 154, +9.3%, -31.6% |
| 20% | 1st | 55, +75.0%, -11.0% | 60, +79.4%, -7.3% |
| 20% | 2nd | 63, +4.1%, -46.1% | 74, +37.0%, -25.2% |

With sectionals the bets are better at every cut in both halves, at TAB's first price and at TAB's last. 71% to 84% of
them shorten after the bet, as in Test 9. At TAB's last price they still lose, but the first half comes close to break
even (-2.2% at 5% and 10%), which the form alone never did: a first sign of an edge on the horses rather than only on
TAB's opener. The second half is much weaker than the first in every row, and these are a few hundred bets in one
state, so this is direction, not proof. Next: the 62 unreadable files, whether the 26% of unjoined runners are a name
mismatch, and the live picks (bw_live.py) to carry sectionals for Queensland races.
