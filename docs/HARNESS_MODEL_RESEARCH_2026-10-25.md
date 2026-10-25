# How the best racing models work, and a harness model for Australia (25 Oct 2026)

Founder: "We don't have to be exactly like Form King. Do some research on the best models, horse models and harness
models and how we can recreate it for Australian racing." The gallops literature (Benter, Bolton and Chapman, Lessmann
et al) was read on 4 Oct and is in research/form_gbm/README.md; this note adds the rating methods underneath those
models, the harness-specific work, and the data that exists in Australia. Strength of each source is stated: most
racing "research" is vendor marketing or one author's backtest.

## 1. The models: what the evidence says

| approach | evidence | strength | what it means for us |
|---|---|---|---|
| Two stages: a fundamental model, then a blend with the market's price (Benter 1994) | Benter's paper; a German-racing re-analysis; an HKJC hobby project finds every fundamentals-only model (logit, LightGBM, MLP, transformer) about 8% worse in log loss than the de-vigged market, and the blend puts 88% of its weight on the market | strong for the method; the HKJC numbers are one author's | Already how the gallops model works. In harness the blend has to be with the OPEN, the price we bet, never BSP |
| Conditional / multinomial logit per race (Bolton and Chapman 1986; McFadden) | the standard in the literature; Silverman and Suchard (Hong Kong, 3,681 races) add a frailty term and a LASSO fitted to profit, and report 36.7% simulated ROI | strong as a method; the ROI is one unreplicated study | Our second learner. Worth trying the profit-targeted fit once there is an open price to fit against |
| Gradient-boosted trees, and learning-to-rank (LambdaRank) | Korean study: CatBoost ranks best (NDCG 0.89), LightGBM and XGBoost bet best | moderate, one study | Our stage 1 already. Ranking objectives are a cheap test, not a rebuild |
| Predict finishing position or margin, then turn it into probabilities | Armerin, Hallgren and Koski (KTH), harness, Applied Artificial Intelligence 2019; Chalmers V75 thesis (2023) predicts distance behind the winner with a neural net: on par with its baseline, did not beat the odds | moderate (peer-reviewed harness paper); the thesis is honest that it lost | A margin target uses more of each race than win/lose. Test it as a second target |
| Support vector regression on harness (Schumaker, Northfield Park, 15 months) | beat betting favourites in 5 of 7 pari-mutuel bet types; four races of history was the best depth | weak (small, US tote, old) | Only the "how many past runs" finding is useful: test 4 v 6 v 10 |
| French Trot forecasting competition (CANSSI Ontario, 2023, 190 teams) | winners named, methods not published | none yet | Nothing to copy until a write-up appears |

The pattern across all of it: the model family matters less than the inputs, every honest study finds the market hard to
beat on fundamentals alone, and the money is in combining a good fundamental price with a market price that is still
soft. That is the gallops finding too (the edge is at the open, not at BSP; harness Test 2 found BSP as sharp as
gallops BSP).

## 2. The ratings underneath: what a "Form King for harness" is

Form King's value is not the neural net; it is turning each run into comparable numbers. The methods are public:

- **Speed figures (Beyer; TrackMaster's harness chain).** Raw time over the distance, then an inter-track variant
  (the same time is worth more at one track than another), then a daily track variant (how fast the whole meeting ran
  against par: TrackMaster computes it from the day's winning times against par times), then a post-position
  adjustment. TrackMaster also adjusts pace figures by track. Strong: decades of use; the exact formulas are proprietary.
- **Sectional ratings (Timeform, Simon Rowlands).** Finishing speed % = (overall time x sectional distance x 100) /
  (overall distance x sectional time). Each course and distance has an "optimum"; the gap from it is the pace the horse
  was set and becomes an upgrade or downgrade to its time rating. Australian versions (Punting Form, TopRate,
  Ratings2Win) express each section in lengths against a standard. Strong method; the claimed accuracy is vendors'.
- **Class.** Harness Racing Australia's National Rating (NR) is points by finishing position and stake level, and races
  are split by it. It measures what a horse has won, not how fast it went, which is exactly the gap a time rating fills.
- **Harness-specific adjustments** (handicapping press, no peer-reviewed numbers found): the draw matters more on small
  tracks; a horse parked or three wide covers more ground; modern sulkies are said to favour on-pace horses. Our own
  Test 4 found the market OVERRATES TAB 1 in pacers (A/E 0.93-0.96), so the draw is priced, if anything too much.

What none of the services publish, and we would build: a daily track variant per meeting, par times per track,
distance and start type, ground covered from position and width, and a pace adjustment from the race's lead time and
quarters.

## 3. Australia: who rates harness, and what data exists

- **Ratings:** Betfair's own harness model (rated prices for selected meetings) is built on RISE data, so RISE does
  license its data for modelling. Giddy-Up sells top-four harness ratings and "early speed". No Form King equivalent for
  harness was found; Punting Form, TopRate and Ratings2Win are thoroughbred-first.
- **Sectionals, the important finding of this pass:**
  - Victoria: HRV's Sectionals Hub (thetrots.com.au) has per-horse sectional data for every Victorian meeting from
    1 Jan 2023, downloadable per meeting. Exact fields not seen (thetrots.com.au refuses automated reading, 403).
  - Queensland: Racing Queensland publishes harness sectionals for every TAB meeting as PDF, CSV and ZIP, including
    individual horse times, top speed and mile rate. The page lists files from Aug 2017 to at least Feb 2026 (Albion
    Park, Redcliffe and others). Terms for the harness files not found; RQ's thoroughbred sectionals page says
    "educational purposes only" and disclaims accuracy.
  - NSW: HRNSW posts sectional PDFs per meeting (race quarters, lead time, mile rate, each horse's position and width at
    the 800m and 400m).
  Together these three states ran 69,862 of the 96,209 Australian races since 2020 (Test 1: NSW 26,834, VIC 24,950,
  QLD 18,078). If their terms allow personal use, the sectional side of the model may not depend on RISE
  at all; RISE would still be needed for results, drivers and trainers across every state.

## 4. The recipe for Australian harness (built in layers, each scored against BSP before the next)

**Layer 1, data.** Results, fields, drivers, trainers, gait, start type, handicap, stewards (breaks): RISE. Sectionals:
RISE, or HRV/RQ/HRNSW directly. BSP and place BSP: Betfair's free files (have). Timestamped opens: the recorder (running).

**Layer 2, ratings per run (our own figures):**
1. Pars: median adjusted mile rate per track x distance x start type x class band, from our own history.
2. Daily variant: each meeting's race residuals against par, class-adjusted, robust median, iterated with the pars.
3. Time rating: the run's time against par after the variant, with margin turned into time at that race's speed,
   standing-start handicap metres added back, and breaks flagged and left out of the horse's figures.
4. Sectional rating: last half and last quarter against the track's par, and finishing speed against the race's pace
   (lead time and middle quarters), Rowlands-style, so a quick finish off a slow pace is not over-rated.
5. Trip: extra ground from position and width at the 800m and 400m (death seat, three wide), where published.

**Layer 3, the horse and the race:** best, recent and trend of each rating; distance, track and start-type form;
driver and trainer strike rates and the driver change (point in time); empirical draw tables by track, distance and
start type; a pace map (who leads, who sits outside the leader) from each horse's lead times and early positions.

**Layer 4, the model:** LightGBM plus a conditional logit, renormalised per race (the gallops recipe); then the
Benter blend with the OPEN price. Optional tests: a margin target, a ranking objective, a profit-targeted logit.

**Layer 5, scoring and bets:** KL to BSP and winner log loss by month, two date halves (the yardstick: market history
alone is at 0.49-0.52; gallops with Form King data at 0.08-0.09); value-at-open and the BSP lay rule as in the brief;
paper before live.

Order of testing by expected value: time ratings and daily variants first (the core of every speed-figure system),
then draw and pace map (harness's distinguishing factors), then sectionals, then drivers and trainers.

## 5. What we will not copy

Form King checks track speeds by hand (trackSpeedVerified); ours will be statistical. Per-horse sectionals exist only
where a state publishes them, so the ratings will be fuller in VIC and QLD than elsewhere. And none of this replaces the
data: every method above starts from a time for every run.

## Sources

Benter 1994 (gwern.net/doc/statistics/decision/1994-benter.pdf); Bolton and Chapman 1986
(gwern.net/doc/statistics/decision/1986-bolton.pdf); Silverman and Suchard, Journal of Prediction Markets 7(1)
(ideas.repec.org/a/buc/jpredm/v7y2013i1p43-52.html); Armerin, Hallgren and Koski, "Forecasting Ranking in Harness Racing
Using Probabilities Induced by Expected Positions" (tandfonline.com/doi/full/10.1080/08839514.2018.1536105); Chalmers
V75 thesis (odr.chalmers.se); Schumaker, harness SVR papers (robschumaker.com/publications); KCI learning-to-rank study
(journal.kci.go.kr ART003266151); HKJC project (github.com/aaron4415/NN-based-Horse-Racing-Prediction-HKJC); German
Benter analysis (github.com/chris-alex-p/german-horse-racing); TrackMaster harness ratings
(trackmaster.com/articles/har/ratings) and HarnessPro help (info.trackmaster.com/harness/prohelp.htm); Rowlands
sectional timing (johnston.racing PDF; timeform.com sectional features); HRA ratings-based handicapping
(harness.org.au/hra/Ratings-Based-Handicapping-System.pdf); Betfair harness predictions
(betfair.com.au/hub/racing/harness/harness-racing-predictions); Racing Queensland harness sectionals
(racingqueensland.com.au/industry/harness/harness-sectionals, read through `fk read terms`); HRV sectionals
(thetrots.com.au news, via search only); CANSSI Ontario French Trot competition (canssiontario.utoronto.ca).
