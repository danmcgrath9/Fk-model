# The best greyhound models, and how we rebuild them with our data (25 Oct 2026)

Founder: "We don't have to make it exactly like Form King, but research the best greyhound models in the world and
how we can recreate them, with the data."

## What can and cannot be known

Nobody profitable publishes a working greyhound model. What is public: Benter's 1994 paper (the template every
serious racing model follows), Timeform's own description of its greyhound ratings, Betfair's Iggy model and its
tutorials, a few academic papers (mostly 1990s-2000s US tracks), and recent hobby projects. Everything below is from
search extracts of those sources; the pages themselves are blocked from this session. Where a figure is second-hand
it says so.

## The models, one by one

### 1. Benter's two-stage model (the professional template)
- Stage 1: a "fundamental" multinomial (conditional) logit on runner features (Bolton and Chapman, 1986), giving each
  runner a win probability. Stage 2: a small logit combining that probability with the public's odds.
- Reported (second-hand, from a blog summary of the paper): on 2,313 Hong Kong races, the fundamental model alone
  explained less than the odds (pseudo-R2 .1016 against .1237), but the two together beat the odds (.1327). The
  market carries information the model lacks; the model carries information the market misprices.
- **Ours already**: the gallops model is exactly this shape (trees + second learner, then the stage-2 market blend).
  Nothing new to build, only to apply.

### 2. Timeform greyhound ratings (the UK reference for time figures)
Per Timeform's own guide:
- each dog has an **expected time** from its previous 8 races at the same number of bends (races mixed with trials
  if it has fewer);
- each meeting gets a **going allowance** from expected against calculated times, race by race;
- **trouble in running** is allowed for, so a dog that was checked can be rated above the winner;
- **sectional ratings** use the same logic, sectional times adjusted in proportion to the going allowance.
- What we cannot copy: the trouble allowance is set by Timeform's analysts by hand. Stewards' comments ("checked",
  "crowded", "galloped on") are the substitute, if Topaz carries them.

### 3. Betfair's Iggy (the best free Australian model)
- Built by Betfair's data scientists from GRV, QLD, WA and NSW data; publishes daily rated prices. Inputs named:
  "sectional time data, box number, market prices and many other variables". Version 2 is current.
- No profit record is published. **But its results files are on the same free data listing** as the BSP files, so
  its log loss against BSP can be measured on the same races. That is a free benchmark: the best public Australian
  greyhound model, scored the way ours will be.
- Betfair's own tutorial models (median winner time per track and distance as the reference time, box, features over
  the last 365 days, logistic regression) concluded they "have poor performances compared to market starting prices".
  The plain feature set is not enough; the market is hard to beat.

### 4. Betfair's 2026 greyhound datathon
- Scored on average log loss per race, with a probability for every runner. Winners were due about 26 March 2026; no
  write-up found from here.

### 5. Academic work
- Chen et al. (IEEE Expert, 1994): a neural network on 10 variables the experts said they used, trained on 200
  Tucson races, beat three professional handicappers over 100 races (+$124.80 against about -$70 each, $2 bets). Its
  edge was weighting **race grade** more than the experts did: grade moves matter.
- Schumaker (SVR on 1,953 US races): accuracy and payout pull against each other; a model tuned for longshots hit
  20% but paid more than one hitting 34%. Pick the target by money, not by strike rate.
- Finishing-order models: Harville (each place as a fresh win race among those left) is biased at the extremes;
  Henery's model predicts ordering probabilities better. Matters for place betting from win chances.

### 6. Recent practice (hobby and open projects, not proof of profit)
- An open greyhound project builds Elo and Kalman ratings, "form lines" (who beat whom, through common opponents),
  speed ratings, trap bias, trainer and sire statistics, and trains LightGBM with the race's conditional logit as the
  loss, walk-forward, scored against SP and Betfair. That is the current shape of a serious amateur build.

## Rebuilding it with our data

| Layer | Best practice it copies | Our data | Notes |
|---|---|---|---|
| A. Time ratings | Timeform: pars, meeting going allowance, expected time, run and sectional ratings | Topaz run times, first splits, track, distance, grade, date | Point-in-time only; pars reset at track changes |
| B. Trouble | Timeform's trouble allowance | Stewards' comments and in-run positions, if Topaz has them | The one piece we approximate, not copy |
| C. Strength | Elo / Kalman / form lines over finishing orders | Topaz placings and margins | Use the whole finishing order and margins, not only the winner: 8 dogs a race give far more signal than one winner |
| D. Early speed and the box | Iggy's sectional + box; first-bend theory | First-split ratings, box, track box bias (Betfair files have box and result for 339,000 races, free) | Greyhound-specific: a dog's chance depends on its neighbours' early speed (crowding at the first bend), so model the field, not the dog alone |
| E. Class | Chen's grade weighting | Grade and grade moves (145 spellings to map) | |
| F. First starters | Timeform uses trials | Topaz trial results | |
| G. Stage 1 | Conditional logit / LightGBM with the race-softmax loss | All of the above | Our gallops recipe |
| H. Stage 2 | Benter's market blend | Opening price (BetMatic probe), the dog's past BSPs against its results | Our gallops recipe |
| I. Place and exotics | Henery over Harville | Win chances from G/H | For the brief's place-at-BSP test |

**Yardsticks, in order**: BSP (winner log loss 1.5044 on 305,093 Australian races, Test 1), Iggy on the same races
(free, measurable now), and the recorded opening price. A model is worth betting only where it beats the price it
bets into; Benter's own result says it will not beat the market alone, only add to it.

## What can be done before the Topaz key

1. **Score Iggy against BSP** from the free files: the best free Australian greyhound model's log loss and A/E by
   band, both halves. Tells us how high the bar really is.
2. **Box bias by track and distance** from the Betfair files (box, distance, result, 339,000 races): the first
   real feature, point-in-time.
Neither needs Topaz, and neither is the model; both are measurements.

## Greyhound-specific methods, read 4 Nov 2026 (founder: "look at the best racing models in the world and anything you can find on greyhounds")

**Betfair's Data Scientists, "Greyhound Modelling in Python using the Topaz API"** (betfair-datascientists.github.io/
modelling/topazTutorial, read through fk read terms, run 41771247854). The closest published work to ours, on the same
data. Pipeline: Topaz bulk runs; drop fields added after the race; set the winner's resultMargin to 0 (it holds the
margin over second, as our probe found). Features:
- dog age, weight min-max scaled within the race, last5 split into win and place rates;
- `finishingPlaceMovement` = second-last in-running position less the place (finishes strong or fades);
- run time against the rolling 365-day median winning time at that track and distance (their speed index);
- `hasAtLeast1VacantBox` (an empty box beside the dog), and the box's rolling 365-day win rate at that track and
  distance GIVEN the vacancy;
- rolling 28/91/365-day aggregates (min, max, mean, median, std) of normalised time, place, prize money, margin and
  finishing movement, for the **dog, trainer, dam and sire**.
Models: twelve sklearn-style classifiers on one year held out, probabilities normalised to 1 per race. Log loss 0.745
to 0.756 for every competent learner (CatBoost, logistic regression, MLP, LightGBM, XGBoost within 0.004 of each
other): the features decide it, not the learner. **They never compare against the starting price or the BSP**, which
is the question that decides whether a model can bet. Topaz keys through Betfair go only to active Betfair Australia
customers who have deposited, bet into at least 100 Betfair markets and intend to bet; access is for 3 months and
continues only with ongoing wagering.

**Timeform** ("Ratings and sectionals explained"): times adjusted by a going allowance for the meeting, a rating
equivalent per track and distance, and sectional ratings, all feeding an expected sectional and final time for the
next race. That is the design of `greyhound/ratings.py` (pars, meeting variant, time and split ratings in lengths).

**Academic work** (from search, not read in full): Johansson and Sonstrod's neural networks at Gulf Greyhound Park
(win accuracy and payout, no log loss), Schumaker's SVM regression for longshots. Neither measures against the market
price.

**What this changes for us**: four feature groups from Betfair's tutorial we did not have (rolling windows,
sire/dam/trainer form, vacant boxes, finishing movement), now in `topaz_theories.py` as T3 and T4 beside our own
engine (T1), run style and the map (T2), GRV's own fields behind leak checks (T5) and the market's past view (T6).

## Where the last 0.117 to BSP can come from (4 Nov 2026, founder: "research to get us closer")

What fifteen tests on the full Victorian history have established, before any new idea:

- **Features decide it, the learner does not.** A bigger model, ranks within the field and a mixed target gave
  nothing (Test 10); Betfair's own tutorial found every competent learner within 0.004 of the others.
- **Every gain so far was new information or more of it.** The training window 0.013; class, recent form, prize and
  interactions 0.011; GRV's pre-race preview 0.009. Round style and the map 0.004 on the free files' map; comments
  as last-run text, trials (thin feed) and 60-day box bias nothing.
- **The ratings are the ceiling of the fundamentals.** The best pre-race time rating predicts the dog's own run at
  r = 0.41 (Test 11). Greyhound runs are noisy: a dog's time varies run to run by more than the field spread, so
  no rating built from past runs alone will get much past that, and the model's top inputs (Elo, past SPs, trainer
  rate, time ratings) are already the ones that carry it.
- **What BSP has that a morning model cannot**: money and news from the day (late scratchings, kennel knowledge,
  the track running fast or slow in the early races, the public's read of the field at 3pm). Part of the 0.117 is
  that, and it is unreachable before the open by construction. The right yardstick for a bet at the open is the
  open; BSP is the sharpest reference, not the target to equal.

Ranked by expected gain per unit of work, with the evidence for each:

1. **The open price itself, as Benter's stage 2.** Blending our model with GRV's SP beat the SP by 0.022 (Test 9)
   with the model's weight near 0.2: a price plus a model is sharper than either. The same blend with the TAB open,
   fitted on recorded opens, is the one input certain to help AND legitimate for a bet placed at the open: the open
   is known the moment it exists. Nothing in the repo can do this until opens are recorded (the BetMatic probe, $1
   in the TAB account). This is the largest expected gain on the list and it costs no modelling.
2. **GRV's own rating, if tomorrow's compare shows it unchanged after the race.** The `rating` field failed Test 9's
   leak check (its movement INTO a run tracked that run's result), but the 4 Nov snapshot shows a rating on every
   runner the evening before. If the compare finds the number the same before and after, it is a pre-race figure
   and the leak check was reading its revision history, not a leak; GRV's rating is then the richest expert input
   we have (the best-bet flag alone, a one-bit version of it, moved the gap 0.009). Expected gain 0.005-0.02.
3. **Isolynx sectionals at The Meadows, Sandown, Healesville and Traralgon**: time to 50m and 300m, the last 100m,
   speed at each point, average distance to the rail, for every runner (the bulk feed has only the first split, and
   second splits on 9%). The run-home split is the measure punters say separates dogs that "run hot to the turn and
   fade"; rail distance is run style measured rather than coded. One request per race, about 3 years at four tracks:
   roughly 18,000 calls, four hours at our cap. GRV's own notes warn that jump/20m times differ by track and the
   first-split par at The Meadows was 0.03s fast, so each measure needs a par per track and distance like our time
   rating. Expected gain 0.005-0.015 at those tracks (about 40% of VIC races), nothing elsewhere.
4. **Ratings methodology**, three upgrades the engine does not have: (a) shrinkage: a dog with two runs is rated as
   if its two times were the truth, where a Bayesian rating pulls it toward the track-and-grade prior by run count
   (the model partly corrects for this through `runs`, but the rating itself should); (b) ability by distance band
   and by track (sprinters at 300m, stayers at 600m+, and the dog's record at THIS track: `bestTimeTrackDistance`
   exists in the bulk feed and `same_track` is a flag, not a rating); (c) an Elo that uses margins, not just
   finishing order (a dog beaten by half a length and one beaten by ten lengths lose the same today). Each is a
   day's work and testable on the standard split; together perhaps 0.005-0.01.
5. **Expert prices as inputs**: GRV's analyst tips (tip1-4, in the pre-race race record, not the bulk feed) and
   Betfair's Iggy rated price (published on the hub the morning of the race, 2024 on). Both are opinions the open
   may under-use; both are only usable if they exist before the open, which the tips do (snapshotted the evening
   before) and Iggy's timing has to be checked. Expected gain small on top of the preview, since they overlap it.
6. **The day's going, from the meeting's earlier races.** The going variant is the largest single adjustment in the
   time rating, and for race 8 the day's first seven races measure it exactly; the model today sees only earlier
   days. Legitimate for a bet placed after race 1, not at the open. Worth having for the second channel (bets near
   the jump at TAB's price), not for open slips.

Not worth pursuing, on the evidence: more learner capacity; the comment as last-run text; the 60-day box bias
(the long-run rate already carries it); trials through `/trialresult` until GRV explains the thin feed; sire and dam
windows beyond what T3 has (1-2% of splits).

The order of work this implies: record opens (the founder's $1), then items 2 and 4 on the standard split while the
opens accumulate, then Isolynx; and stage 2 with the open the moment a month of opens exists.

### Where the list stands (4 Nov 2026, evening)

- Item 4 (ratings methodology) is BUILT and worth 0.009 (Test 16: 0.117 to 0.1085). Item 2 (GRV's rating) is worth
  another 0.009 if the 5 Nov compare clears it (the number on every runner the evening before; whether it is the
  same after the race is what the compare says). Item 3 (Isolynx): the pull ran all afternoon (run 41820190239),
  the D2 row runs when it is in. Item 5 (expert prices): the race records carry GRV's tip1-4 and the analyst
  comment, and `/api/race?from&to` lists them for any date range, so a pull exists (`mode=run races=yes`) and round 8
  tests the tips with a strike-rate-by-year leak check. Item 1 (the open) still waits on $1 in the TAB account.
- Beyond the list: the walk-forward (Test 14) says a FRESH model holds the edge at the SP that the frozen one was
  losing (+53.7% / +48.0% with the rule chosen out of sample; nothing at BSP), and that the SP itself sharpened from
  August 2026. The finishing order as the label (round 7, truncated Plackett-Luce, row C of the table above) is the
  one learner-side idea with information behind it rather than capacity; it is running. The 3,000-round cap was the
  binding stop in Test 16 (2,997), so round 8 lifts it to 6,000 as a row.
- The next walk-forward carries everything that cleared: the preview, the ratings upgrades, Isolynx, the tips and,
  if cleared, GRV's rating (`topaz_walk.py` has the switches; `WALK_REFIT_EVERY=2` because the 181-input model does
  not fit 36 refits in a job).
