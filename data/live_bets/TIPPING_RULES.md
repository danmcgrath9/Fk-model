# Mercer Tipping: rules for public tips

**From Thu 15 Oct 2026: tips are posted at their OPENING price** (founder, 14 Oct: "make sure we post opening prices").
The tips are the BetMatic book's fills (orders made before the market, filled at Form King's opening price), posted once
the market is up and quoted at the price each opened at, never a later price. The record is public-record.md, settled at
the opening price less the race's scratching deduction. The earlier Twitter record (evening/9am prices) was deleted.

1. **A tip is locked once it is tweeted.** Price, stake and our quoted price stay exactly as posted, and it is settled at
   that price. A later refresh, reprice or model change never edits a tip already out. (Founder, 10 Oct 2026, after
   Caulfield's Campaldino and Grand Larceny were restaked and repriced in a reissue.)
2. **New bets after a refresh are added, not swapped in.** Anything the sheet adds later (e.g. after scratchings) is a
   new tip at its own price and time, tweeted on its own.
3. **Scratched tips are refunded at 0**, noted once in a short update tweet, and nothing else changes.
4. **A bet taken is never dropped.** A reprice, model change or new price can add bets, but every bet already taken
   stays on the sheet (the "Bets taken" box) and in the records until it is settled, even if the model no longer rates it.
   (Founder, 11 Oct 2026.)
5. Stakes follow the live rule (stake_rule.py: from 18 Oct 2026 plain Kelly x125, x5/8, max 5u, no only-ride or
   small-field multipliers) at the price tweeted, and are fixed from then on.

## Messages on the founder's behalf (13 Oct 2026, founder: "Never send a message again without drafting it to me")
Every message sent for the founder (Slack, email, anything) is shown to him as a final draft first, word for word, and is
sent only after he approves that exact text. Changing the wording after his approval means showing it again. No
exceptions for "small" edits, for messages he described in outline, or for ones he said to send before seeing them.

## The BetMatic standard (13 Oct 2026, founder: "treating like BetMatic, and then that's how we document everything from now on")
Every meeting is now run and recorded as if the bets went through BetMatic at the open:
1. **Before the market opens** (straight after the 11am fields pull: one pull per meeting bet, no retries, founder 14 Oct "make all pulls at 11:30am now so we dont waste credits", then "do both at 11am"): `research/form_gbm/betmatic_orders.py DAYPREFIX GTAG OUT.csv`
   writes the order file, `data/live_bets/DAYPREFIX-betmatic-preopen.csv`: every runner the rules could bet, a minimum odds
   from our model alone shaded 5% (`0.95 x (1.2 / p_model^0.82)^(1/0.78)`, tested in t_betmatic.py) and the stake in up to
   three price tiers so it grows with the opening price. This is the file BetMatic would be sent.
2. **After the open**: `betmatic_fills.py ORDERS.csv DAYPREFIX` records which orders fill at Form King's opening price.
   Those fills are the BetMatic bets, logged in `data/live_bets/betmatic-book.md`.
3. **After the races**: the same script with `--results` settles them (scratching deductions applied); the book carries
   each meeting's P/L beside the open book and the tips.
4. (Scrapped 1 Nov 2026, see below.) The race-level first-starter rule needed the market, so it is checked once the market is up; a filled order in such a
   race is marked, not deleted (taken is taken).
Until BetMatic is live these are paper bets; what the founder actually takes stays in live-record.md.
5. **9:30am top-up check (from 14 Oct 2026, paper):** on race day at 9:30am, after scratchings, refresh prices, re-price
   on the final field and run `research/form_gbm/topup.py DAYPREFIX GTAG`; log any top-ups in the top-up section of
   betmatic-book.md and settle them with the results. Tracked to see whether a top-up earns; the backtests say it does not.
   Kept on (founder, 15 Oct 2026: "5c is nothing for something that I would want to sell to clients"): paper only, every
   race day, 5 credits a meeting, until the live sample settles the question.

## The forward test is the BetMatic method only (14 Oct 2026)
Founder: "Forward test I only want the model that we would be using with betmatic". data/live_bets/forward-test-betmatic.md,
from research/form_gbm/fwd_betmatic.py: every meeting the founder bets, the pre-open order file built from the model's
FIRST price for the meeting (git history, never re-made after the race), filled at the opening price, 8 steps,
first-starter race rule, scratched runners void, deductions. Add each meeting to MEETINGS and re-run it when its results
are in. The old sheet forward test (forward-test.md) is retired.
Order files now carry max_odds (3x our price, $8 for EARLY runners): a minimum-odds order alone also fills at an open
far past our price, which the rules would not bet. Whether BetMatic can carry a maximum price is a question for them;
the forward test reports the result both ways.

## Metro: no bets at $12+, full stakes (1 Nov 2026)
Founder, 1 Nov 2026: "we go back to normal stakes but we cap at $12". Flemington, Caulfield, Moonee Valley and Sandown,
every day of the week. The metro fix (20% lean to the market) stays; orders carry a $12 maximum and full stakes (the 31 Oct
half stakes are off). research/form_gbm/t_price_bands.py, v10 holdout from 3 Jun: metro fix bets at $12+ won 4 where 9
were expected (-24u); under $12 they won 23 against 24.5, as calibrated as provincial (196 v 197). Capped, full stakes:
+86u at +35.6% (halves +32% / +42%), worst drawdown 31u; uncapped: +62u at +19.6%. Country/provincial are NOT capped:
$8-12 made +77% and $20+ +74% there. Twitter units are half, so metro on Twitter tops out at 5u like everywhere else.

## Big overlays: double the stake at 2.2x our price (2 Nov 2026)
Founder, 2 Nov 2026: "NIce fucking love it". When TAB opens a horse at 2.2x our price or more and we rate it under $8,
the stake is doubled; the 10u cap stays. On the order sheet it is one extra order per horse, from 2.2x our price
(rounded up to the cent) to the usual ceiling, carrying the stake again, and every step already above that line carries
double its total (betmatic_orders.py BIG_OVERLAY; the order's note says "stake doubled"). Pre-open sheets only.
research/form_gbm/t_stake_edge.py, v10 holdout from 3 Jun, every live rule, at the open less 7%: the live stake is about
2u in every overlay band, yet bets opening at 2.2x+ our price made +99% (170 bets, both halves). Doubling those rated
under $8 (113 bets, about 6 a week): +1,556u (+59.4%) against +1,236u (+52.6%), worst drawdown 58u against 52u, profit
per unit of drawdown 26.8 against 23.8, both halves up. $8+ made only +22% there, so it stays at one stake. The 2.2x
line and the $8 cut were chosen on that holdout, so expect less than the test. Twitter units stay half the model stake.

## First starters: the race rule is scrapped (1 Nov 2026)
Founder, 1 Nov 2026: "Yeah switch it, lets go". First starters themselves are never bet (betmatic_orders.py filters them),
but a race holding one is bet like any other: no race is dropped from an order sheet for a first starter, at any price.
The test (research/form_gbm/t_fs_half.py, v10 holdout from 3 Jun, at the open less 7%): bets on raced horses in races
with first starters made +232u on 597u (+38.9%) against +53.8% in races without; skipping them (the 30 Oct rule) gave up
314u against no rule. By count of first starters (1 / 2 / 3 / 4+: +19% / +60% / +18% / +58%) there is no pattern. At BSP
those bets are -16% against -0.3%: the edge is in getting the open. Supersedes the 20 Oct "flag every first-starter race"
check (BETMATIC_PLAN.md), the 26 Oct $6 race rule and the 30 Oct "skip first starters" rule. The weekly calibration check
watches the group.

## Deductions: scrapped (1 Nov 2026)
Founder, 1 Nov 2026: "Just completely scrap the deduction pay". From Sun 1 Nov no deductions are ESTIMATED, printed on a card or applied to a paper or Twitter settlement by guess: a bet
settles at the price taken, unless the founder reports TAB's actual deduction for the race (as on 1 Nov: Mornington R3 23c,
R9 11c), which is then applied to the winnings, 1 + (price - 1) x (1 - d), paper and Twitter alike. Real bets settle at what TAB actually paid
(BetMatic reports the return), so any deduction shows up there and nowhere else. Settlements before 1 Nov keep the
deductions they were recorded with. The sections below on deductions are history.

## Deductions: TAB's actual figure wins (14 Oct 2026) (superseded 1 Nov 2026)
Founder: "This is deductions from TAB at opening". For every meeting bet, record the deductions TAB applied on the bets
struck at its opening price in data/live_bets/DAYPREFIX-deductions-actual.txt ("race, cents  # horse"); deductions.py
uses them in place of the estimate (betmatic_fills.py, betmatic_html.py, fwd_betmatic.py all read through it). The
estimate (0.95 / price of every runner scratched after the open, matching TAB's published schedule) ran 2.5x too high on
Caulfield 14 Oct (59c against 24c). The backtest KEEPS its 16c average deduction and the estimate stays as it is
(founder, 14 Oct: "I'm fine with high deductions"): conservative on purpose. At 6.5c the holdout would be +61% staked.

## Posting tips to X (14 Oct 2026)
Founder: "after we place the bet we send it out". Claude writes data/live_bets/tweets/DAYPREFIX.json (main post, card
image path, one reply per horse, all at the opening prices actually taken) and the card PNG beside it, commits, and
dispatches the fk-tweet workflow. The job runs in the GitHub environment "twitter", which needs the founder's approval
before it starts and holds the X keys (X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET) as environment
secrets. Approve = post. NAME.posted.json records the post IDs and blocks a second posting. Only after the bets are on.

## Three price steps, not eight (14 Oct 2026)
Each horse's order is now 3 steps (x1, x1.25, x1.5 of its minimum), each sized at the next step's price. Same holdout
profit as 8 steps (+801u; earlier races +1,584u against +1,564u), at most 3 bets a horse at the open instead of 8, so
fewer simultaneous bets for TAB to see. Turnover about 4% higher. Forward test 5-13 Oct: +24.66u (8 steps: +26.28u),
same 32 horses and 7 winners.

**Twitter units DOUBLED from Thu 12 Nov 2026 (founder, 10 Nov: "We are doubling Twitter units", "From Thursday onwards"): the posted stake is the full model stake (10u max), so a Mercer card shows the same units as the open bets. Cards and tweets up to Wed 11 Nov stay at half; the record shows the switch.** (Superseded:) **Twitter stakes are the model stake halved (founder, 20 Oct 2026).** The model cap went to 10u on 20 Oct; Twitter keeps a 5u max, so every posted stake is half the model stake (7.70u model posts as 3.85u). Tweets before 20 Oct were already on a 5u max, so the posted record stays on one scale. The book keeps the model stake and the posted stake side by side.

**Copied tips (founder, 21 Oct 2026, replacing "no follower-book orders" for tips he forwards).** When the founder forwards another tipster's bet and says to take it: units at $50, minimum odds always 20c under the tipster's quoted price, and the top bookie price at the time (BetMatic High Odds First across every running session, `when: best` in fk-betmatic). Placed straight away, dry run first, sent only on his OK on the exact order. Recorded in their own section of betmatic-book.md, never mixed into the model's results.

**Unit size (founder, 21 Oct 2026): $50 a unit moving forward.** Every BetMatic send uses unit 50 unless the founder says otherwise. The Fri 23 Oct (Cranbourne, Ballarat) and Sat 24 Oct (Flemington) orders sent on 21 Oct went at $25.
- **Cards (founder, 22 Oct 2026):** a card asked for with no Mercer, or "just a card", has no bottom notes line at all. The Twitter card footer is "Win bets." only (no "Placed early").

**No explanatory notes on sheets, pages or cards (founder, 24 Oct 2026: "get rid of all the fucking notes about betmatic and shit. Stop fucking doing that moving forward").**
Race pages and cards carry the prices, the bets and the tables, nothing else: no paragraphs explaining how BetMatic,
deductions, take-at prices, staking or the shadow book work, and no "BetMatic" labels on the page. market_sheet.py and
betmatic_html.py no longer write them. Explanations go in chat only if the founder asks.

**The Twitter record is the card the founder posted (27 Oct 2026, founder: "how'd you get that wrong?").** Bendigo Wed 28
had two cards on file: card_wed28.json (value at the Form King open, model stakes halved, with Imperial Award) and the one
he posted (the BetMatic open fills halved, six horses, no Imperial Award). Claude quoted the first as the tweeted card and
gave a race number from memory. From now on: the moment a card is posted, its horses, races, prices, rated prices and units
go into betmatic-book.md marked "Tweeted Twitter card"; anything quoted later as what we tipped comes from that entry
(or the posted image), never from a working card file, and race numbers come from the order file, never from memory.

**Metro (founder, 31 Oct 2026, after Derby Day 0 from 6: "Yes" to the fix at half stakes).** At Flemington, Caulfield, Moonee
Valley and Sandown the order sheet leans our chance 20% to the market and halves every stake (betmatic_orders.py METRO;
t_metro_fix.py). Cards for metro meetings carry the halved units. Back to full stakes only after about 50 live metro bets
show the fix holds; until then metro results are reported on their own line.

## Undeclared riders (1 Nov 2026, found from St Gotthard "jockey -41%", Flemington 31 Oct)
Priced before riders are declared, Form King gives an empty jockey and every jockey input came through as 0, which the model
(never trained on a missing rider) read as a jockey who never wins: 5-25 runners a meeting for weeks (Flemington 31 Oct 22 of 138,
Mildura 3 Nov 13 of 46). From 1 Nov drop_scr.py gives an undeclared rider the median of the meeting's declared riders, input
by input, and a meeting priced before riders are declared is re-priced once they are (riders declared: compare and replace
the orders, on the founder's word). Flemington 31 Oct with the fix: The Roaring Sun $50 -> $29 (won $6.50), Unhinged $13.60 ->
$8.34 (2nd, SP $2.90); the bets barely moved (9.79u v 11.88u, the same horses less Persian Spirit).

## Back-settler shade off (1 Nov 2026)
Founder, 1 Nov 2026: "Yep turn the shade off". shade_back.py now multiplies by 1.0. Under the 1 Nov rules the x0.85 shade
lost on the v10 holdout (+1,090u at +45.8% with it, +1,237u at +52.7% without, worse in both halves) and on the full
out-of-fold history (+4,604u v +4,720u). By distance (t_backmarkers.py, our bets, out of fold): sprint back-settlers around
a bend are the best group (+68%, wins/expected 0.96); beyond 1200m back-settlers run 0.83-0.88, the reason the shade
existed, but the opening-price edge still pays them (+41% to +49%). Note: the backtests quoted to the founder on 1 Nov
(+1,237u) were run without the shade while the live sheets carried it; switching it off makes the two match.
Flemington straight (t_straight_oof.py, 74 races): the model is calibrated there overall; our FORWARD bets on the straight
won 2 against 6.5 expected (-72%, 37 bets), too few for a rule: every straight-course bet is flagged and tracked.

## Flemington straight: forward runners' chance x0.7, not a ban (1 Nov 2026)
Founder, 1 Nov 2026: "only drop them if it makes sense, like a leader can win, but it has to make sense from an ROI point of
view" (replacing a same-day ban). At Flemington, 1200m or less, a runner that usually settles forward (settle share under
0.3) has its chance x0.7 in shade_back.py and the race is renormalised, so midfield and back-settlers pick it up; a leader
at a big enough price is still a bet. t_straight_mult.py, out of fold, 74 straight races: straight bets -9% as priced,
+2% at x0.9, +9% at x0.8, +16% at x0.7, +25% at x0.6, +36% with leaders at zero. x0.7 is the cautious pick on 74 races
chosen after seeing them; revisit as straight races build up. Applies from the next fresh pricing (shade_back runs once
per v6 file).

## Input audit (1 Nov 2026, founder: "Can we test all inputs and make sure they make sense?")
t_input_audit.py compares every model input on the live day files with the training data. Everything lines up except four
inputs that arrive EMPTY when a meeting is priced before declarations, and are read as zero:
- jockey stats (15-28% of runners early, 1% in training) and the jockey's riding weight (19-31% v 7%): drop_scr.py gives
  an undeclared rider the meeting's median jockey, riding weight included;
- gear changes (none at all early, 24% of runners carry one in training): cannot be filled; known once declared;
- barrier and speed map (20% missing on the first Flemington Tuesday export): gone on the re-export.
Re-exported after declarations, every meeting matches training (Mornington, Flemington Tue, Echuca s7, Wangaratta s6: 2-6%).
RULE: a meeting priced before riders are declared is re-priced once they are, and the orders are compared and replaced
(founder's word) before the market opens where it has not; the 9:30am race-day re-price is always on declared fields.

## EARLY tag cap $8 -> $15 (1 Nov 2026)
Founder, 1 Nov 2026: "Yep move it to $15" (after Azzacool, Ballarat R7 2 Nov: rated $9.43, opened $15, blocked by the $8
cap). Second-up after a good first-up (placed or within 2L first-up): bet at the open or not at all, no bet over $15.
t_secup_cap.py, full history out of fold, our bets on them by opening price: under $4 +59%, $4-8 +56%, $8-12 +89%
(+105% / +74% by half), $12-15 +42%, $15+ -24% (both halves negative). Plan: cap $8 +4,537u, $12 +4,729u, $15 +4,743u.

## Units: backs $100, lays $200 (3 Nov 2026)
Founder, 3 Nov 2026, after the lay book's month-by-month at $100 and $200: "Do the lays at $200 and backs at $100". A back
unit is $100 (betmatic_orders.py UNIT_DOLLARS, the send workflow's default, betmatic_html.py), so the 10u cap is $1,000
on one horse. A lay is 1u = $200 of backer's stake at Betfair SP (settle_lays.py), so the liability is $2,800 at $15 and
$7,800 at the $40 max, $5,100 on the average lay; a loser pays +$184. Twitter units stay half the model stake. Still paper:
the bot is off and TAB holds $0.65; the lay trial runs to its four weeks before a real lay goes on.
AMENDED the same evening (founder: "Do $50 a bet and $200 a lay"): a back unit is $50 (10u cap = $500 on one horse); a
lay stays $200. The $100 back unit lasted an hour and was never sent on.

## Paper back book at Betfair SP, from Thu 5 Nov 2026 (founder, 3 Nov: "a lay and back table down the bottom ... a game day tab")
Rule fixed before the first race (research/form_gbm/README.md 3 Nov; t_fav47_months.py, t_fav47_live.py): back 1u at Betfair
SP the horse that is the BSP FAVOURITE of its race when its BSP is $4 to $7 AND our price (the live shaded model) is at least
1.6x the BSP, which on the page reads as "back if fav: $4 to $X" with X = ours / 1.6 capped at $7. Nothing else is a back:
not the second favourite at the same price, not a favourite under $4, not a favourite we agree with. Backtest 3 Jun-13 Oct
61 bets, 24 winners, +79%; the live weeks 14 Oct-3 Nov 17 bets, 6 winners, +53%; the 1.3x line is tracked in the research
only (flat out of sample). Settled from Form King's results with research/form_gbm/settle_backs.py. Paper, four weeks, then
judged, like the lay book; the dollar size of a unit is not set until it goes real. Every meeting page carries the lay book,
the back book and a Game day section (race by race, that race's lays and backs) from lay_sheet.py.
GAME-DAY SEND (founder, 3 Nov: "follow Betfair but then can send out a betmatic note when we know it's going to land in there"):
every build writes DAYPREFIX-GTAG-backs-betmatic.csv, one BetMatic row per back candidate (min $4, max its cap, 1u). The
founder watches Betfair's projected SP; when the favourite is going to land in its range, the fk-betmatic workflow sends
THAT ONE ROW (action send, file = the -backs-betmatic.csv, race and number, when = best, unit = the dollars, dry_run = no):
a standard bet now, High Odds First at the top bookie price, so the bookies carry the back and Betfair only gives the
signal. Allow about a minute from dispatch to placement: fire it three or four minutes out, not one.

## Top-ups stopped (4 Nov 2026)
Founder, 4 Nov 2026: "I think we can stop doing top up". The 9:30am re-price no longer runs topup.py or keeps a top-up
table; it re-prices the final field, refreshes the lay book, back book and game day, and leaves the open book alone. The
tracked record stays in betmatic-book.md as it was. research/form_gbm/topup.py stays in the repo, unused.

## One page per race day (6 Nov 2026, founder: "lets do that for all days moving forward")
Every race day has one artifact for the whole day: bets taken at the open from every meeting, a Game day tab across
every meeting in jump order, then each meeting's sheet under its own tab (research/form_gbm/day_page.py). The day page
is rebuilt and republished to the same URL whenever a meeting page changes; its link leads every message about that day.
URLs are kept in data/live_bets/DAY-PAGES.md.

## Form adjustments (founder's calls, applied every time the horse is priced)
Kept in data/live_bets/form-adjustments.json and applied before pricing any meeting the horse is in, with the price shown
both ways on the first run so the effect is visible.
- Cavill Avenue (8 Nov 2026, founder: "remember when price Cavill, we have +4 lengths"): its 30 Sep Ballarat run (3rd,
  beaten 0.75L, Form King WFA 82.6) is rated 4 lengths better, +7.9 points (1.98 a length, Form King's own conversion in
  that race): WFA 90.5. Down for the G3 Thoroughbred Club Stakes, Sandown Sat 14 Nov.

## No locking in (8 Nov 2026, founder: "1 - never")
Backing at the open and laying the same horse at BSP to lock in the price move (t_greenup.py, backtest +46%, every week up)
is NOT to be used or proposed again. The open book stays unhedged.

## Paper lay book, second band $8-$12 (from Mon 9 Nov 2026; founder, 8 Nov: "Yes add it in")
Lay 1u ($200) at Betfair SP if BSP is $8 to $12 AND at least 1.6x our price, beside the $15-$40 band (unchanged). $12-$15
stays out: it lost in the backtest and live. Evidence: holdout +69% / +30% by half; live 14 Oct - 8 Nov 43 lays, 3 winners
against 4.4 expected, +27% (research/form_gbm/t_bsp_candidates_live.py). lay_sheet.py writes one CSV row per window with a
band column and shows a horse's windows stacked in one cell; settle_lays.py totals each band on its own line. Judge both
bands, and the favourite backs, at the end of November.

## $15-$40 lay trigger 1.6x -> 1.5x (from Mon 9 Nov 2026; founder, 8 Nov: "Yeah do that")
The $15-$40 band lays when BSP is at least 1.5x our price (was 1.6x); the $8-$12 band stays at 1.6x. Evidence
(research/form_gbm/t_lay_trigger.py and the live sweep): the 1.5-1.6x slice was 174 lays, 4 winners against 7.8 BSP
expected, +80u (backtest +45.7u, Jun-Jul -6.8u / Aug-Oct +52.4u; live 37 lays, no winner, +34u); since June the band at 1.5x
is +$88,800 against +$72,800 at 1.6x. Going lower is not worth it: 1.4-1.5x won exactly what BSP said (10 v 10.2) and
below 1.4x the extra lays lose. About 8 more lays a week, so a little more liability on the day.

## Going live on Betfair, Friday 13 Nov 2026 (founder, 8 Nov: "We are going live Friday with this all", "$50 a lay works")
- Lays live at $50 a lay (the backer's stake; liability = $50 x (BSP - 1)), both bands; favourite backs $50 until the
  founder sets otherwise. Open bets through BetMatic as before, which needs TAB funded and the bot running by Wednesday,
  because Friday's markets open Wednesday or Thursday.
- scripts/betfair_runner.py and .github/workflows/fk-betfair.yml: 90 s before each jump it reads Betfair's projected SP and
  fires the lay and back rules as SP (limit-on-close) orders; caps $3,000 liability a race, $40,000 a day; paper mode logs
  only. Betfair blocks API logins from the US, where GitHub's runners are, so it runs on a self-hosted runner in Australia
  (label betfair-au). The "betfair" environment holds the key and login and needs the founder's approval to start: that
  approval is the day's send. Each race day needs data/live_bets/DATE-betfair-manifest.txt (DAYPREFIX GTAG per meeting),
  written by the 9:30am re-price. The key arrives later in the week (Betfair needs the account funded first); the first
  paper run with it checks the login and API addresses.

## Betfair SP rules under watch (founder, 10 Nov 2026: "Track all of those")
The live weeks showed the $15-$40 lay at 1.5x ours winning as often as BSP said (317 lays, 14 won v 13.6; the backtest
had 19 v 38.9), so the rules were re-searched for ones that make money in the backtest's two halves AND live
(research/form_gbm/t_both_samples.py: 77 rules, 6 held; about 10 would by luck, so none is proven). All eight below
are tracked on paper by research/form_gbm/track_rules.py (rebuilt from every settled meeting since 9 Oct into
data/live_bets/rule-tracker.csv), reported in the 9:30am settle message, and judged again at the end of November:
1. Lay $8-$12 when BSP >= 1.6x ours (current).        5. Lay $12-$15 drifted 1.25x from the open.
2. Lay $25-$40 drifted 2x from Form King's open.        6. Back $3-$5 firmed 1.5x from the open.
3. Lay $25-$40 when BSP <= ours / 1.6.                 7. Lay $15-$40 when BSP >= 1.5x ours (current, failing live).
4. Lay $8-$12 firmed 1.5x from the open.                8. Back the BSP favourite $4-$7 when ours >= 1.6x BSP (current).
Added 10 Nov (research/form_gbm/t_back_rules.py: 49 back rules, 2 held, about 6 by luck): 9. Back $4-$7 firmed 1.5x from the
open. 10. Back any $4-$7 runner when ours >= 1.6x BSP (the favourite rule widened).
Which of these go live on Betfair from Fri 13 Nov is the founder's call.
