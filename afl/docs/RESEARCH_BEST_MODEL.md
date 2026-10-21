# What the best prop and match modellers do that we are not doing yet

Research date: 21 October 2026. Reading only: no data was bought, no account was opened, nothing was scraped.

## How to read this document

- **How the research was done.** This session's network blocked direct page loads for almost every site that mattered (squiggle.com.au, matterofstats.com, wheeloratings.com, arxiv.org, pinnacle.com and others all refused the connection). So every source below was read through search-engine summaries, not by opening the page. Where a fact comes from a summary, the URL is given so it can be read in full in a browser. Where I am relying on my own background knowledge rather than a source found today, the text says **(background, not re-verified today)**.
- **Source strength labels:**
  - **Peer-reviewed**: journal or refereed conference paper.
  - **Practitioner**: a named modeller or bettor writing about their own method (Matter of Stats, Wheelo, Squiggle, DARKO, Rufus Peabody interviews, Buchdahl, Whelan's blog).
  - **Blog**: anonymous or semi-anonymous writing with no track record attached.
  - **Marketing**: tipster, affiliate or vendor pages. Treated as hypotheses only.
- **"Unknown" means unknown.** Very little of what sharp prop bettors do has been measured in public. Most expected-gain figures below are "unknown" and I have not invented them.

## Where we start from

| Piece | Current state | Honest read |
|---|---|---|
| Player props | LightGBM Poisson on leak-free pre-game features; NB spread (dispersion per position for disposals); walk-forward by season | Sound design. Disposals MAE 3.71 vs 3.85 for a last-10 average is a 3.6% improvement over a naive baseline. A bookmaker line is probably also better than last-10, so this number does not yet say anything about an edge |
| Team model | Ridge on Elo and form differences | Competitive with public Squiggle models, behind "Punters" (the bookmaker average). That is normal: the market is the hardest benchmark in AFL |
| Lineup strength | AFL Player Ratings tried, did not help out of sample | Consistent with what others report (see section B) |
| Odds | None yet; Odds API historical props (from mid-2023) to be bought | This is the biggest gap. Nothing about edge can be measured until it exists |

## The ranked list (short version)

Ranked by expected value for us: likely size of gain, multiplied by how sure we are it applies, divided by effort. Detail for each is in the numbered sections that follow.

| Rank | Idea | Why it ranks here | Effort | Needs paid data? |
|---|---|---|---|---|
| 1 | Build the market-comparison harness before any more modelling: de-vig every ladder rung, score model vs market with log loss, CLV against a cross-book consensus close | Every other idea is unmeasurable without it; the only test that matters is "better than the price" | Medium | Yes, The Odds API (already planned) |
| 2 | Use the market's own game expectations (line and total) as features instead of, or beside, our Elo margin | Free or cheap; the market margin beats our team model by construction, and game environment drives team disposal volume | Low | Squiggle "Punters" (free API); AusSportsBetting history (free download, check terms) |
| 3 | A separate time-on-ground and sub-risk stage (expected TOG, P(named sub), P(subbed off)) feeding the rate model | The minutes stage is the first thing every serious NBA/NFL prop modeller separates out; the AFL sub rule makes low-TOG outcomes a real mass in the distribution | Medium | No |
| 4 | Role features and role-change detection: centre bounce attendance share, kick-ins, ruck share, forward/back time, with the latest game weighted heavily | Prop edges cluster where a role has changed and the line has not caught up | Medium | Partly: CBA data availability needs checking (see 4) |
| 5 | Teammate-out redistribution modelled explicitly (team pool times player share) | Our "teammates in/out" features are probably too coarse to say who inherits the outgoing player's CBAs | Medium | No |
| 6 | Shrinkage and per-stat decay: empirical Bayes priors for small samples, and a separately tuned half-life for each stat | Peer-reviewed evidence that shrinkage roughly halves error on small samples; noisy stats (tackles, marks) need longer memory than disposals | Low to medium | No |
| 7 | Better distribution, checked at the ladder rungs: dispersion that depends on features, randomised PIT checks, per-threshold recalibration | Australian books sell ladders (15+, 20+, 25+, 30+), so the tail must be right, not just the mean | Medium | No |
| 8 | Joint simulation of a game for same-game multis and correlated staking | SGMs are the dominant Australian prop product and correlation pricing is reported to be inconsistent across books; also protects the bankroll | High | No for building; yes to test |
| 9 | Timing: measure where lines are softest (open, after Thursday teams, after final teams) and target that window | Practitioners consistently say props are softest early; we can measure it the day odds arrive | Low once odds exist | Yes (odds with timestamps) |
| 10 | Staking and evaluation discipline: shrunk fractional Kelly, simultaneous-bet sizing, caps on correlated exposure, sample-size targets set in advance | Protects against the most common way a small real edge is lost or a fake edge is believed | Low | No |
| 11 | Team model: score games on scoring shots or xScore, not only points; long-memory venue effects; blend with market | Matter of Stats' best system does this; but the team market is hard to beat, so its main value is as an input to props | Medium | No (xScore history is the question) |
| 12 | Market structure edges to test once odds exist: favourite-longshot bias on high ladder rungs, softer stats (tackles, marks) vs disposals, over/under bias | Plausible and cheap to test with bought odds, but public evidence is weak | Low | Yes |
| 13 | Scorer and venue effects on subjective stats (tackles, marks, contested possessions) | Peer-reviewed evidence of scorekeeper bias exists in the NBA; untested for AFL | Low | No |

---

## Section A. Player-prop modelling (any sport)

### A1. Minutes / time-on-ground as its own stage (Rank 3)

**What it is.** Predict how long the player will be on the ground first, then predict the per-minute rate, then combine. Every public description of serious NBA and NFL prop work separates opportunity (minutes, snaps, routes) from efficiency (output per unit of opportunity), because opportunity is the largest single source of variance and it reacts to news (injuries, rotations, blowouts) differently from rate.

**Evidence.**
- NFL: opportunity vs efficiency decomposition (routes run, targets per route run, yards per target) is described in detail by a named fantasy analyst ([Ben Gretch, "Stealing Signals"](https://bengretch.substack.com/i/187529180/miami-dolphins), practitioner) and PFF built an XGBoost "expected target share" model on route data because share metrics are more stable than raw outcomes ([PFF](https://www.pff.com/news/fantasy-football-advice-maybe-its-time-to-look-at-targets-differently), practitioner). No published validation of a full multiplicative model was found.
- NBA: DARKO, the best-known public NBA projection system, is a daily-updated, decay-weighted, Kalman-filter system focused on box-score stats ([Power Rank podcast with Kostya Medvedovsky](https://thepowerrank.libsyn.com/kostya-medvedovsky-on-the-darko-nba-player-projections), practitioner). That it models minutes as a separate projection is **(background, not re-verified today)**.
- Rufus Peabody, one of the best-known US prop bettors, builds a separate projection for each prop and bets the differences from the book ([The Ringer profile](https://www.theringer.com/2022/9/21/23363621/gamblers-super-bowl-props-rufus-peabody-nfl), [VSiN](https://vsin.com/the-vsin-daily/inside-the-mind-of-sharpest-of-the-super-bowl-prop-sharps/), practitioner interviews). These describe the habit, not the maths.

**Why it matters more in AFL than it looks.** Since 2021 each team has a substitute. A player named as the sub, or subbed out early, posts a disposal count far below his normal distribution. A single-stage model that predicts disposals directly learns a blurred mixture of "plays the whole game" and "plays 25%". A two-stage model can put explicit probability on the low-TOG branch and widen the lower tail correctly. Whether a disposals bet on a player who is subbed off stands or is voided varies and looks inconsistent in punters' reports ([r/AFLbetting thread](https://reddit.sudovanilla.org/r/AFLbetting), blog-grade); **the actual settlement rules of each bookmaker must be read before this is modelled**, because they decide whether the low-TOG branch is a loss or a refund.

**How to test with our data.** Per-game TOG% is in the Fryzigg/AFL data. Fit (a) a TOG model (features: recent TOG, age, role, injury return, named-sub flag where available, rest, expected margin for blowout risk), (b) a rate model on disposals per full game, and (c) combine as a mixture: P(sub or early exit) times low-TOG distribution plus the rest. Compare walk-forward against the current one-stage model on log loss at each ladder threshold (15+, 20+, 25+, 30+), not just MAE.

**Expected gain.** Unknown for AFL. Most of the gain should show up in the lower tail and in calibration of "over" probabilities, which MAE barely sees.

**Effort.** Medium. No paid data.

### A2. Usage and role models (Ranks 4 and 5)

**What it is.** The share of the team's volume a player gets, modelled directly, with explicit rules for redistribution when a teammate is out. In the NBA this is "usage"; in the NFL it is target share and snap share; the AFL analogue is centre bounce attendance share, stoppage presence, kick-in duty, ruck share and the time spent in each zone.

**Evidence.**
- AFL fantasy analysts treat centre bounce attendances (CBAs) as the main signal of midfield role, but also show the link to output varies a lot by player: one elite midfielder took only 16% of disposals from centre bounces despite about 19 CBAs a game, and centre-bounce disposals per CBA ranged roughly 0.21 to 0.36 across midfielders ([Keeper League Podcast CBA analysis](https://keeperleaguepod.com.au/?p=5896), practitioner/blog). So CBA is a role flag, not a disposal multiplier.
- AFL.com.au publishes round-by-round CBAs credited to Champion Data, and Footyinfo says the stat has been recorded since 2019 (2019 and 2020 incomplete) ([AFL.com.au](https://www.afl.com.au/news/449735/fantasy-centre-bounce-attendances-round-two), [Footyinfo](https://www.footyinfo.com/stats/player/career/fantasy/most-cbas)). **I could not confirm whether the Fryzigg file carries CBAs.** The AFL.com.au match stats that fitzRoy's `fetch_player_stats_afl` pulls include extended stats, and I believe CBAs are among them **(background, not re-verified today)**. Check the columns before planning around it.
- NBA usage redistribution: a figure of about 60% of a missing player's usage being redistributed circulates, but the only source found is an anonymous page ([blog-grade](https://edge-assist.duckdns.org/data-status/docs/nba-player-props/ruling/NBA%20Player%20Props%20Data%20Audit%20Council%20Ruling)). Treat the number as a hypothesis.

**How to test.**
1. Role features: last-game and last-3 CBA share, kick-ins, ruck contests share, inside-50 and rebound-50 share, plus a "role changed" flag when last-game CBA share differs from the 10-game share by more than some threshold. Measure the improvement only on games where the role changed, because that is where an edge would be.
2. Top-down redistribution: project team total disposals for the game (from expected margin, expected total, weather, opponent pace), then each player's share. When a regular midfielder is out, his historical CBA share has to go somewhere; estimate where from past games when he was out (with-or-without-you splits), shrunk towards the team's general pattern.

**Expected gain.** Unknown. Practitioners consistently say the edge in props is concentrated in role changes and late news, which this targets.

**Effort.** Medium. No paid data if CBAs are in the AFL.com.au feed; from 2019 only.

### A3. Bayesian / empirical Bayes shrinkage and per-stat memory (Rank 6)

**What it is.** A player's observed rate is a noisy estimate of his true rate. Shrink it towards a sensible group average (position, role, age), by an amount that depends on how many games we have and how noisy the stat is. Separately, choose how fast old games are forgotten for each stat, rather than one decay for all.

**Evidence.**
- Efron and Morris (1975, JASA) showed that shrinking early-season batting averages towards the group mean gave less than half the mean squared error of the raw averages ([paper PDF](https://www.medicine.mcgill.ca/epidemiology/hanley/bios602/MultilevelData/EfronMorrisJASA1975.pdf), peer-reviewed). Brown (2008, Annals of Applied Statistics) repeated the field test on a larger set ([arXiv 0803.3697](https://arxiv.org/pdf/0803.3697), peer-reviewed).
- Baseball's "stabilisation" work (Carleton, Tango) estimates, per stat, the sample size at which signal and noise are half and half; at that point you weight the player 50/50 with the league mean ([FanGraphs](https://blogs.fangraphs.com/randomness-stabilization-regression), [Baseball Prospectus](https://www.baseballprospectus.com/?p=14293), practitioner). Carleton later warned that stabilisation within a sample is not the same as predicting the next sample ([Rotowire](https://www.rotowire.com/baseball/article/the-z-files-the-fallacy-of-stabilization-and-an-early-look-at-home-runs-56442)).
- DARKO's design uses exponential decay and a Kalman filter ([podcast](https://thepowerrank.libsyn.com/kostya-medvedovsky-on-the-darko-nba-player-projections), practitioner); per-stat decay rates were not found in public.

**How to test.** (a) Split-half reliability per stat per position in our 2012-2026 data: how many games until disposals, marks, tackles, goals per full game reach a split-half correlation of 0.5. Expect tackles and marks to need many more games than disposals. (b) Replace the single exponentially weighted form with a per-stat half-life tuned in walk-forward. (c) Add a shrunk prior (position-and-role mean, weighted by games played) as a feature, or fit the rate as a mixed model and feed the posterior mean to LightGBM. Gains should be largest for debutants, players returning from injury and players who just changed club.

**Expected gain.** Large on small samples (the 1975 result), small on established players. Overall for us: unknown, probably modest, but cheap.

**Effort.** Low to medium. No paid data.

### A4. Distribution choice, checked where the money is (Rank 7)

**What it is.** The mean is not enough because Australian books mostly sell thresholds and ladders, not a single 50/50 line ([2021 TAB ladder 20+/25+/30+/35+](https://www.sportsnews.com.au/afl/afl-round-19-odds-and-betting-preview-2021/570087/amp); [tipster examples of 15+ and 20+ prices](https://www.gambling.com/au/news/afl-betting-tips-2025-round-14-best-bets-and-betting-trends), marketing-grade but show the product). A model that is right on average but too narrow in the tail will look like it has edge on every 30+ and 35+ rung, and that "edge" is the classic way a prop model loses money.

**Options, and evidence.**
- Negative binomial with a dispersion that depends on features (role, TOG certainty, weather) rather than per position only. LightGBMLSS fits full conditional distributions, including discrete and zero-inflated families, with gradient boosting ([GitHub](https://github.com/StatMixedML/LightGBMLSS), software, v0.6.1 released Dec 2025). Whether it ships a negative binomial family was not confirmed; plain LightGBM accepts a custom NB objective, worked through in a retail forecasting paper ([arXiv 2311.00993](https://arxiv.org/pdf/2311.00993), preprint). A simpler route is a second model on squared Pearson residuals.
- Zero-inflated for goals: test ZINB vs NB on log score; for most forwards NB may already be enough. Unknown which wins.
- Conformal or isotonic recalibration of each threshold probability on held-out seasons: no sports-prop application was found, only the general methods ([Self-calibrating conformal prediction, NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/hash/c1c49aba08e6c90f2b1f85751f497a2f-Abstract.html), peer-reviewed).
- Calibration matters more than accuracy for betting: choosing NBA models by calibration rather than accuracy gave ROI of +34.69% vs -35.17% in a one-season betting test (Walsh and Joshi 2024, Machine Learning with Applications, [record](https://researchportal.bath.ac.uk/en/publications/machine-learning-for-sports-betting-should-model-selection-be-bas/), peer-reviewed, single season so treat the size with caution).
- Checking a count forecast: randomised PIT histograms and proper scoring rules for counts (Czado, Gneiting and Held 2009, Biometrics) **(background, not re-verified today)**.

**How to test.** For each stat, compute reliability at each rung (predicted P(20+) in bins vs observed rate), the randomised PIT histogram, and log score of the full count distribution, by position and by TOG band. Then compare: per-position NB dispersion (current) vs feature-dependent dispersion vs isotonic-recalibrated thresholds.

**Expected gain.** Unknown in accuracy terms; in betting terms, mis-calibrated tails are where a model's apparent edge is most often fake, so this mainly prevents losses.

**Effort.** Medium. No paid data.

### A5. Correlation between props and same-game multis (Rank 8)

**What it is.** Two bets on one game are not independent: a blowout lifts the winners' disposals and cuts the losers'; rain cuts marks for everyone; two midfielders on one team share a pool of possessions. The best approach is a joint simulation: draw a game state (margin, team disposal totals, weather effect), then draw each player's stats conditional on it.

**Evidence.** Sportsbooks adjust SGM prices for correlation and reportedly disagree with each other on the sign of some correlations, which is where shopping helps ([OpticOdds](https://opticodds.com/blog/correlation-in-same-game-parlays), [Establish The Run](https://establishtherun.com/should-you-bet-same-game-parlays/), vendor/practitioner). The same sources say SGM hold is several times a single bet's ([Juice Reel](https://juicereel.beehiiv.com/p/the-dangers-of-same-game-parlays), blog). No peer-reviewed study of SGM mispricing was found. Australian SGM pricing examples exist only in affiliate content ([BettingPro](https://www.bettingpro.com.au/afl/afl-same-game-multi-tips/), marketing).

**How to test.** From historical games, measure residual correlations (actual minus projected) between teammates, between opponents, and between a player's stats. If the residual correlation of two teammates' disposals is materially negative (shared pool) or positive (game pace), a joint simulator will price their combination differently from the product of singles. Testing whether books misprice it needs SGM prices, which The Odds API is unlikely to carry **(unknown, check)**.

**Expected gain.** Unknown. Even if we never bet an SGM, the correlation matrix is needed for staking (A10).

**Effort.** High.

### A6. Injury and news repricing (part of Ranks 5 and 9)

**What it is.** Reprice instantly when news lands: Thursday team announcements, and final teams 90 minutes before the bounce (60 minutes in 2020), with clubs allowed to bring in any of four emergencies without explanation, which the AFL expected would produce more late changes ([AFL.com.au](https://www.afl.com.au/news/441560/the-late-change-just-got-later-afl-cuts-time-for-final-teams-release), [AFL.com.au](https://www.afl.com.au/news/922861/more-late-changes-incoming-afl-clarifies-team-selection-rules/amp), official).

**How to test.** Once timestamped odds exist: for each late out, compare prop lines on his teammates before and after the change. If lines on the likely beneficiaries do not move, or move late, that is the clearest soft spot in the market. Our model already handles teammates in/out; the work is a fast "rerun after final teams" path. HPN's PERT model, which needs announced teams, publishes later in the week for exactly this reason ([Squiggle](https://squiggle.com.au/?p=465), practitioner).

**Expected gain.** Unknown. Practically limited by how fast we can act and how much the books let us bet.

### A7. How sharp prop bettors describe the work

- They "make their own number" for every prop and bet the difference ([Sharper, True Pokerjoe 2016](https://www.hpb.com/sharper-a-guide-to-modern-sports-betting/M-7897912-T.html), practitioner book; content on props not confirmed).
- They bet openers, because the market's job is to close the gap between the opener and the sharp view ([Rufus Peabody, VSiN](https://vsin.com/the-vsin-daily/inside-the-mind-of-sharpest-of-the-super-bowl-prop-sharps/), practitioner).
- Most books copy a small number of market-making books rather than setting lines themselves; the useful skill is knowing which books lead and which follow ([The Logic of Sports Betting, Miller and Davidow 2019, review](https://www.geegeez.co.uk/the-logic-of-sports-betting-book-review), [LSR excerpt](https://www.legalsportsreport.com/33079/the-logic-of-sports-betting-market-agreement-and-resistance/), practitioner book).
- Prop limits are lower and props bettors get flagged: "If you exclusively play props, you could come in the crosshairs for books" ([Betting Life newsletter](https://betting-life-newsletter.beehiiv.com/p/rufus-dawgs-name), blog).
- Two views on whether props are still soft: "props went from one of the easiest markets to beat to efficient" ([BetSmart](https://betsmart.beehiiv.com/p/efficient-prop-markets), blog) vs "inefficiencies still slip through every day" ([WagerLens](https://wagerlens.beehiiv.com/p/sportsbooks-still-miss-on-these-player-props-here-s-how-to-spot-them-cd5b4a319e0a5ddc), blog). Both are US-centric opinion. Nothing comparable exists for AFL.

### A8. Academic evidence on prop market efficiency

No peer-reviewed study of sportsbook player-prop efficiency was found in this search. The peer-reviewed betting-market literature covers sides, totals and moneylines: early-season NBA totals biased ([Journal of Prediction Markets 2013](https://www.ubplj.org/index.php/jpm/article/view/601)), early-season NFL totals ([Journal of Sports Economics 2014](https://ideas.repec.org/a/sae/jospec/v15y2014i2p201-211.html)), NFL biases and crowd wisdom ([Shank 2019](https://journals.sagepub.com/doi/10.32731/IJSF.141.022019.01)). One 2026 preprint finds Polymarket NBA prop markets thin (about 13 trades per market on average) ([arXiv 2605.00864](https://arxiv.org/pdf/2605.00864), preprint, prediction market not a sportsbook). **Conclusion: prop-market softness is widely asserted and not well measured in public. We will have to measure it ourselves.**

---

## Section B. AFL specifically

### B1. What the public AFL modellers do

| Model | Method (as far as public sources show) | Source and strength |
|---|---|---|
| **MoSHBODS** (Matter of Stats, Tony Corke) | Elo-style offence and defence ratings. Performance is a 50/50 blend of standardised points and standardised scoring shots (tuned). Venue Performance Values from a team's past over/under-performance at a ground, with a very long 65-game look-back and about 60% of the excess carried in; season carryover about 0.65 | [MoS tuning post](https://matterofstats.com/mafl-stats-journal/2020/2/12/bringing-the-mos-twins-into-the-2020s), [MoSSBODS 2.0](https://matterofstats.com/mafl-stats-journal/2015/11/1/an-improved-vflafl-team-rating-system-mossbods-20?format=amp), [2024 review](https://matterofstats.com/mafl-stats-journal/2024/11/30/we-need-to-talk-about-moshbods-), practitioner. MoS finished 22nd on Squiggle in 2024 and was left out of s10 in 2025 |
| **Wheelo Ratings** | Team model: expected score = league average plus own attack and opponent defence ratings; attack ratings update on adjusted vs expected score. Player side: "Equity", their implementation of the AFL Player Ratings, split into pre/post-clearance, ball-winning and ball-use; a shot model giving expected score per shot (xSc) and shooting over/under expectation. Brownlow model uses coaches' votes, margin, polling history and stats, 20,000 simulations | [Wheelo methodology](https://www.wheeloratings.com/afl_methodology.html), [Wheelo stats page](https://www.wheeloratings.com/afl_stats.html), [Brownlow guide PDF](https://wheeloratings.com/src/docs/wheelo-brownlow-guide-2024.pdf), practitioner. **No player-stat projection model from Wheelo was found** |
| **HPN (PERT)** | Tipping model built on player-level PAV (Player Approximate Value) of the named 22; publishes after teams are announced | [Squiggle](https://squiggle.com.au/?p=465), practitioner. PAV is available via the Squiggle API ([fitzRoy vignette](https://jimmyday12.r-universe.dev/fitzRoy/doc/using-squiggle-api.html)) |
| **Squiggle** | Ratings from final scores and venues only; home advantage from ground familiarity (Squiggle 2.0). s10 = average of last year's top 10 models by MAE | [Squiggle](https://squiggle.com.au/introducing-s10/), practitioner |
| **The Arc, Graft, Massey, AFLalytics, Footy Maths Institute** | **Unknown.** No methodology page was retrievable. Massey ratings in general are least-squares rating systems **(background, not re-verified today)** | Squiggle listings only |
| **Academic** | Bayesian dynamic Skellam model (Manderson, Murray, Turlach 2018), slightly worse than betting markets; time-varying Bradley-Terry with team features up to 71.5% correct ([arXiv 2405.12588](https://arxiv.org/pdf/2405.12588)); ML on 2013-2018 performance indicators at about 73%, roughly matching bookmakers ([IJCSS 2019](https://reference-global.com/article/10.2478/ijcss-2019-0020)) | Peer-reviewed / preprint |

**The market benchmark.** Squiggle's "Punters" (average of many bookmakers' lines) narrowly topped the 2018 bits table over the best computer model (39.76 vs 39.27) ([Squiggle 2018](https://squiggle.com.au/models-leaderboard-winners-2018/)); a 2025 extraction showed Punters with the highest bits figure but the row attribution could not be verified ([Squiggle 2025](https://squiggle.com.au/leaderboard/?y=2025)). Matter of Stats uses the aggregate bookmaker closing line from the AusSportsBetting AFL data file as its "truth" in skill-vs-luck simulations ([MoS](https://matterofstats.com/mafl-stats-journal/2024/10/7/reviewing-moshplays-2024-squiggle-performance)). Older peer-reviewed tests found no general favourite-longshot bias in AFL head-to-head and line markets for 2001-2004 but a bias favouring home teams in games outside Victoria, with only modest simulated profits ([Schnytzer and Weinberg](https://econ.biu.ac.il/en/node/1162), peer-reviewed working paper).

**So for our team model:** being behind Punters is the expected result, and the public evidence says the head-to-head market is close to efficient. The team model's main value to us is as an input to props.

### B2. Ideas for the team model (Rank 11, and Rank 2)

1. **Use the market itself as the game-environment input to props (Rank 2).** For prop modelling we do not need our own expected margin to be the best possible; we need the best available one. The market's margin (Squiggle "Punters", already in our Squiggle tips) and the market total (AusSportsBetting historical file, which carries lines and totals **(background, not re-verified today; check its terms of use)**) should beat our Elo margin as features. Test: swap the feature, rerun walk-forward, compare disposals log loss. Effort low. Expected gain unknown but likely positive, because the market margin beats our team model by construction and the expected total is a direct proxy for game pace.
2. **Score games on scoring shots or xScore, not only points.** MoSHBODS blends points and scoring shots 50/50. Matter of Stats found that using xScore margins as the measure of truth cut every forecaster's mean absolute error by about 6% to 15% each season, meaning a lot of actual-margin variation is goal-kicking luck ([MoS, What if Squiggle used xScore](https://www.matterofstats.com/mafl-stats-journal/2024/10/12/what-if-squiggle-used-xscore), practitioner). The implied idea: update Elo on scoring shots or xScore and you remove some noise from the ratings. Test: rebuild Elo with scoring-shot margins (we have scoring shots in the per-game data); compare out-of-sample margin MAE and log loss against the points-only Elo. xScore history: AFLxScore 2017-2020 and Wheelo 2021-2024 per that post; scraping either needs their terms checked.
3. **Long-memory venue effects.** MoS's tuned look-back for venue performance is 65 games with about 60% of the excess counted. Test as a feature in the ridge.
4. **Lineup strength, again, differently.** AFL Player Ratings did not help. Matter of Stats reviewed which player rating data predicts team results best ([MoS review](https://www.matterofstats.com/mafl-stats-journal/2020/4/28/a-review-of-afl-player-rating-data), practitioner; conclusions not retrievable today). HPN's PERT is the public model built on lineups. A narrower version may work where the broad one did not: only count changes from the team's typical 22 (who is in and out this week, weighted by their shrunk value), rather than the absolute strength of the 22. Unknown gain.
5. **Blend with the market rather than compete with it.** For any team bet, the honest default is market probability, moved only by what our model sees that the market cannot (late changes). See C4.

### B3. AFL player-stat projection work in public

- No public AFL disposals projection with a stated method and accuracy was found. Commercial pages advertising disposal predictions had no method ([example](https://footyworld.duckdns.org/predictions), unverifiable).
- A Towards Data Science series models AFL fantasy points per minute and TOG from age, draft pick and position, and finds the share of time in midfield and defence is the strongest driver of points per minute ([TDS](https://towardsdatascience.com/lifecycle-of-an-afl-players-career-part-2-a4bf9bdb01a8/), blog). This supports idea A1/A2: role (where on the ground) drives rate.
- Karl Jackson's Swinburne PhD values player involvements by the expected value of the next score ([thesis](https://figshare.swinburne.edu.au/articles/thesis/Assessing_player_performance_in_Australian_football_using_spatial_data/26294677), peer-reviewed thesis). Relevant to player value, not directly to disposal counts.
- An open AFL player-match dataset 2000-2023 includes per-match weather from 2010 and advanced stats from 2012 ([b2find record](https://b2find.eudat.eu/dataset/bd7e05fb-7dd9-5e5e-9e8e-a3aca011cc97)); useful as a cross-check on our own weather join.
- **Our 3.71 MAE is therefore not comparable to any published figure.** The benchmark that will mean something is the book line's own MAE on the same games.

### B4. Centre bounce attendances and role (Rank 4)

How much CBA matters is **unknown in measured terms**. The fantasy evidence (B3, A2) says: CBA share flags a midfield role, the disposal yield per CBA varies a lot by player, and a CBA rise after a teammate's injury is a common precursor to a scoring jump. Test plan in A2. The measured question for us is: on games where last-game CBA share moved by more than 15 percentage points from the 10-game average, does including it reduce error, and does the book line lag?

### B5. Weather and ground (part of Rank 7)

No systematic wet-vs-dry study of AFL stats was found; only match anecdotes (high tackle counts in the wet). Tipster content claims small grounds produce more tackles, without data ([BettingPro](https://www.bettingpro.com.au/afl/afl-same-game-multi-tips/), marketing). We already have weather; the test is interaction terms (rain x position, rain x stat) and stat-specific dispersion in the wet. Cheap.

---

## Section C. Beating the market

### C1. When to bet (Rank 9)

- Practitioners consistently say props open soft and move quickly once sharp money arrives, so value is at or soon after the open ([Covers](https://www.covers.com/guides/what-line-moves-can-tell-us), [Action Network](https://www.actionnetwork.com/education/sports-betting-market-terms-and-strategies), practitioner/marketing; [Peabody](https://vsin.com/the-vsin-daily/inside-the-mind-of-sharpest-of-the-super-bowl-prop-sharps/)). Limits at the open are lower, which is the trade-off.
- For AFL the natural windows are: market open (often after Thursday teams for Friday/Saturday games), and final teams (90 minutes before). Online in-play betting is not legal in Australia under the Interactive Gambling Act **(background, not re-verified today)**, so everything here is pre-game.
- **Test once odds arrive:** for every prop, record price at first sighting, at Thursday-teams-plus-1-hour, at 90 minutes before, and at close. Compute our model's edge at each and the average subsequent move towards our number. If our number is right, early prices should show positive CLV and late prices little. The Odds API's historical snapshots are at fixed intervals, so "open" means "first snapshot" **(check the snapshot interval for AFL props)**.

### C2. How books set prop lines

- Most books copy a few market makers ([Logic of Sports Betting](https://www.legalsportsreport.com/33079/the-logic-of-sports-betting-market-agreement-and-resistance/)). Props are often compiled from feeds: Altenar says it builds its player specials from five providers ([Altenar](https://altenar.com/en-us/blog/sportsbook-features-guide-player-props/), vendor). Whether Australian books take AFL prop prices from a shared supplier is **unknown**. Champion Data is the AFL's official data provider, 49% owned by the AFL, and says it works with wagering organisations, without naming clients ([Wikipedia](https://en.wikipedia.org/wiki/Champion_Data), [Champion Data](https://www.championdata.com/about-us/)).
- **Testable once odds exist:** if several Australian books post identical or near-identical disposal lines at the same moment, they share a source, and "line shopping" across them buys little. Where they differ, the outlier is the bet (the Kaunitz method below). Compare our MAE to the consensus line's MAE; if the consensus line is close to a recent average, our features (role, TOG, teammates) are exactly what it is missing.

### C3. Where prop markets are thought to be soft (Rank 12)

| Claim | Evidence | Strength | Our test |
|---|---|---|---|
| Lower-volume stats (tackles, marks) are softer than disposals | Tipster guides say "most punters stick to goals and disposals; the value is often elsewhere" ([BettingPro](https://www.bettingpro.com.au/afl/afl-same-game-multi-tips/)) | Marketing | Compare model-vs-market log loss gap by stat |
| High ladder rungs (30+, 35+, 3+ goals) are overpriced longshots | Whelan's peer-reviewed work: bookmakers set higher margins on longshots, so loss rates on longshots exceed the standard calculation ([Whelan MPRA list](https://mpra.ub.uni-muenchen.de/view/people/Whelan=3AKarl=3A=3A.html)) | Peer-reviewed for other markets; untested on AFL props | Overround and our edge by rung |
| Public prefers overs, so unders are better value | Supported for NBA game totals in older studies; for props, evidence is anecdotal and one cricket prop modeller found overs paid better ([Tyche Sports](https://tychesports.substack.com/p/a-year-of-modelling-cricket-player)) | Weak | Over vs under hit rate against de-vigged price |
| Large pricing errors happen | Sportsbet voided "any player 40+ disposals" bets as obvious errors in 2019; the NT regulator ordered payment ([NT decision PDF](https://dth.nt.gov.au/__data/assets/pdf_file/0011/749855/Reasons-for-Decision-Sportsbet-AFL-40-Disposal-Gambling-Disputes.pdf), [iGaming Business](https://igamingbusiness.com/legal-compliance/sportsbet-ordered-to-pay-up-after-afl-odds-errors/)) | Primary (regulator) | Not a strategy; shows errors exist and that the regulator limits "obvious error" voids |

### C4. Line shopping and "beating the bookies with their own numbers"

Kaunitz, Zhong and Kreiner averaged odds across many bookmakers as the probability estimate and bet the outlier prices on soccer; they report roughly 8.5% to 9.9% returns over five months of real-money betting, then were severely limited by bookmakers ([MIT Technology Review](https://www.technologyreview.com/2017/10/19/67760/the-secret-betting-strategy-that-beats-online-bookmakers/), reporting on a preprint). This is the cleanest public illustration of two facts at once: consensus is a strong probability estimate, and soft books restrict winners fast. For us the practical version is: bet only where our model AND the cross-book consensus both disagree with the chosen book's price, and treat our model as moving the consensus, not replacing it. Hubáček, Šourek and Železný (2019, International Journal of Forecasting) went further: they trained models to be accurate AND decorrelated from the bookmaker's implied probabilities, and that made more money than accuracy alone on NBA 2007-2014 ([IJF record](https://ideas.repec.org/a/eee/intfor/v35y2019i2p783-796.html), peer-reviewed). Test: once odds exist, add a penalty on correlation with the market's de-vigged probability, or bet only where the model and market disagree for a reason we can name (role change, late out).

### C5. Limits and account restriction in Australia

- Northern Territory-licensed bookmakers (Sportsbet, Ladbrokes, bet365 and most others hold NT licences) are not obliged to accept bets from anyone; winning punters report closures, severe limits or being moved to tote-only ([The Straight](https://thestraight.com.au/australian-bookies-warned-about-third-party-accounts), [InvestSmart](https://www.investsmart.com.au/investment-news/lose-or-be-locked-out-you-bet/41484), journalism, partly advocacy). Using another person's account can breach rules and draw a fine up to $18,900 under NT provisions, reportedly untested.
- I found no current Australian minimum-bet-limit rule for sports props. Racing minimum-bet rules exist in some states **(background, not re-verified today)**; they do not cover AFL props.
- Pinnacle withdrew from Australia in 2018 **(background, not re-verified today)**, so there is no legal high-limit sharp book for AFL props here. Betfair Australia is the exchange; AFL player markets there are limited **(unknown, check)**.
- **Implication:** a real AFL prop edge will be capped by limits within months. Plan the paper season and the first real-money season around measuring edge per bet and CLV, not bankroll growth.

### C6. Kelly with correlated bets (Rank 10)

- Plug-in Kelly overbets because our probabilities are estimates. Baker and McHale (2013, Decision Analysis) derive a shrinkage factor for Kelly under parameter uncertainty and show shrunk Kelly beats raw Kelly in simulation and on tennis data ([INFORMS](https://pubsonline.informs.org/doi/fpi/10.1287/deca.2013.0271), peer-reviewed).
- Simultaneous bets: the joint Kelly problem grows exponentially with the number of bets ([arXiv 2604.24723](https://www.emergentmind.com/papers/2604.24723), preprint); Whitrow (2007, JRSS C) gives algorithms for many simultaneous events **(background, not re-verified today)**; several bets on one game are treated in Andersen, Hassel, Hvattum and Stålhane (2020) ([record](https://dspace.vut.cz/handle/11012/200389), peer-reviewed). Penaltyblog's Python library has a multiple-outcome Kelly ([docs](https://penaltyblog.readthedocs.io/en/latest/betting/bet_size.html), software).
- **Practical rule to test in the paper season:** fractional Kelly (quarter to half), shrunk further by the model's own calibration error; a cap on total stake per game; and treat two props on one game as one position when their residual correlation (from A5) is high.

---

## Section D. Evaluation

### D1. Proper scoring rules and the right comparison (Rank 1)

- Score the full predicted distribution (log score of the count; ranked probability score across the ladder) and each threshold probability (log loss), not MAE alone. MAE rewards the median and is blind to the tails we will actually bet. Proper scoring rules for this purpose: Gneiting and Raftery (2007, JASA) **(background, not re-verified today)**.
- Compare against the market on the same props: de-vig each book's ladder (Shin, power or additive methods; Shin's method has been reported more accurate than simple normalisation ([shin package](https://pypi.org/project/shin), citing Štrumbelj 2014); Clarke, Kovalchik and Ingram 2017 on adjusting for overround ([implied package docs](https://rdrr.io/cran/implied/f/vignettes/introduction.Rmd))). For ladders, the de-vig must respect that P(20+) >= P(25+) >= P(30+).
- A Kelly-style or flat-stake backtest return is a noisy accuracy measure; there is an IJF paper on whether betting returns are a useful measure of forecast accuracy ([IJF 2020](https://ideas.repec.org/a/eee/intfor/v36y2020i2p713-722.html), peer-reviewed; conclusions not read). Use returns as a check, log loss vs market as the test.

### D2. CLV as the main metric, with caveats

- CLV is the industry's main skill signal: bettors who beat the close tend to be profitable, and books flag accounts that do it ([deucescracked explainer](https://www.deucescracked.com/blog/closing-line-value-explained-sports-betting-sharp-test-2026), practitioner). The idea is traced to Bellini's *Conquering Risk* ([SBR forum](https://www.sportsbookreview.com/forum/handicapper-think-tank/475316-the-misunderstanding-of-beating-the-closing-line), forum).
- Karl Whelan (UCD economist) argues that positive average CLV does not guarantee long-run winnings ([Whelan blog](https://www.karlwhelan.com/?p=2595), practitioner with peer-reviewed record).
- **Caveat specific to us:** CLV only works if the close is efficient. A single Australian soft book's prop close may be a copied number. Measure CLV against a cross-book consensus close, de-vigged, and check that the consensus close itself beats the open on log loss. If it does not, CLV against it means little.

### D3. How many bets to tell skill from luck

My arithmetic, not a source (assumptions stated):

| Measure | Assumption | Bets for a 2-standard-error signal |
|---|---|---|
| Profit, odds about 1.90 | Per-bet return SD about 0.95 units; true ROI 3% | (2 x 0.95 / 0.03)^2 = about 4,000 |
| Profit, odds about 1.90 | True ROI 5% | about 1,450 |
| Profit, ladder rung at about 4.00 | Per-bet SD about 1.7; true ROI 5% | about 4,600 |
| CLV (percent, vs consensus close) | Per-bet CLV SD 5%; true mean CLV 2% | (2 x 5 / 2)^2 = about 25 |
| CLV | Per-bet CLV SD 8%; true mean CLV 1% | about 260 |

The CLV per-bet SD is a guess and must be measured from the bought data. The message stands regardless: a season of profit cannot separate a 3% edge from luck, while CLV can in a few hundred bets, provided D2's caveat holds. Buchdahl's books (*Squares and Sharps, Suckers and Sharks* 2016; *Monte Carlo or Bust* 2021 ([listing](https://abbeys.com.au/book/monte-carlo-or-bust-9780857304858.do))) and his Pinnacle articles cover the same ground with a t-test on yield adjusted for odds **(background, not re-verified today)**.

### D4. Backtest pitfalls specific to our plan

| Pitfall | Where it would bite us | Guard |
|---|---|---|
| Look-ahead in features | Season-level aggregates, opponent concessions computed with the target game, TOG of the target game leaking into "rate per full game" | Already walk-forward; add a test that recomputes features from data strictly before each game's start time and asserts equality |
| Line availability | Backtesting against a line that was only up for minutes, or only at one book, or posted after final teams | Use the snapshot the bet could have been placed on, at a stated time; record which books carried it |
| Survivorship / selection | Books only post props for regular players; injured or dropped players vanish from the market but not from our data; players subbed off may be voided | Evaluate only on props that existed; apply each book's settlement rules for subs and late withdrawals |
| Multiple testing | Many stats x rungs x books x timings; some will look profitable by chance | Fix the strategy (stat, rungs, timing, edge threshold) on 2023-2024 odds, test on 2025, then paper 2027 |
| Market data starts mid-2023 | The Odds API historical non-featured markets start mid-2023 ([The Odds API AFL](https://the-odds-api.com/sports/afl-odds.html)) | Only three seasons; keep at least one fully untouched |
| Model tuned on MAE | Optimises the median, not the rung probabilities | Tune on ladder log loss |

---

## Paid data, terms of use and scraping flags

| Source | Status | Flag |
|---|---|---|
| The Odds API historical props | Paid plan; AFL props from mid-2023, AU bookmakers; props via the event-odds endpoint | Market keys for disposals/marks/tackles **not confirmed**; check the market list and snapshot interval before buying |
| Squiggle API (tips incl. Punters, PAV) | Free | Squiggle asks API users to identify themselves with a User-Agent **(background)**; follow its usage notes |
| AusSportsBetting historical AFL odds | Free download used by Matter of Stats | Check terms of use |
| Wheelo Ratings, AFLxScore | Public pages | No API found; terms not checked; do not scrape without permission |
| AFL.com.au match stats (via fitzRoy) | Free | AFL site terms not checked; fitzRoy is widely used but that is not permission |
| Champion Data | Commercial | Official source of CBAs and advanced stats; licensing needed for anything beyond what AFL.com.au publishes |
| Bookmaker websites | Terms generally forbid automated access **(background)** | Do not scrape; use the API |
| SGM prices | Probably not in The Odds API | Unknown |

---

## Suggested order of work

1. Before the odds arrive: Rank 2 (market margin and total as features), Rank 3 (TOG and sub stage), Rank 6 (shrinkage and per-stat decay), Rank 7 (ladder calibration). All testable today with our data, all cheap, all improve the thing we will bet.
2. When the odds arrive: Rank 1 harness first (de-vig ladders, model vs market log loss by stat and rung, CLV vs consensus close), then Rank 12 market-structure tests and Rank 9 timing.
3. Then Ranks 4 and 5 (role and redistribution), focused on the games where role changed, because that is where the market is most likely to lag.
4. Ranks 8, 10, 11, 13 as the paper season approaches.

## Idea 13 detail (scorer and venue effects)

Scorekeeper bias in NBA box scores (home scorers credit more assists) has been documented and adjusted for (van Bommel and Bornn, Journal of Quantitative Analysis in Sports, 2017) **(background, not re-verified today)**. AFL stats are coded centrally by Champion Data, which should reduce this, but subjective stats (tackles, contested possessions, pressure acts) may still vary by venue or coding team. Test: venue fixed effects on residuals for each stat, after controlling for teams and weather. Cheap; probably small.
