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
