# How to build the best cricket model: research, tested on our data (21 Oct 2026)

What the published work and the betting literature say makes a T20 model good, each claim with the
strength of its source, then measured on our 14,686 Cricsheet matches where it can be. Every measured
figure comes from `python -m bbl.research.measure` (MEASURE.md on the release). What was built from it,
and whether it helped, is at the end.

**Source strength.** Several primary sources (arXiv, SFU, Columbia) could not be opened from this
environment; where a claim rests on a search summary of a paper rather than the paper, it says
"(summary)". Claims from betting blogs and vendor pages are marked "(weak)".

## 1. What the best cricket models do

| idea | source | strength | measured here |
|---|---|---|---|
| Simulate ball by ball: each ball a multinomial outcome by batter, bowler, overs used and wickets down, with empirical-Bayes shrinkage for thin samples | Davis, Perera and Swartz, *A Simulator for Twenty20 Cricket*, ANZ J. Stat. 2015 ([PDF](https://www.sfu.ca/~tswartz/papers/t20sim.pdf), [Wiley](https://onlinelibrary.wiley.com/doi/full/10.1111/anzs.12109)) | peer-reviewed (summary) | built as v2, see section 5 |
| Win probability and projected total from balls and wickets left, by dynamic programming (WASP); criticised for thin tails because a Markov state forgets who is batting | [WASP](https://en.wikipedia.org/wiki/WASP_(cricket_calculation_tool)), [noenthuda critique](https://www.noenthuda.com/2014/03/13/wasps-have-thin-tails-or-why-cricket-prediction-algorithms-fail) | encyclopaedia, blog | v2 keeps the players in the state |
| Phase-specific player profiles with James-Stein shrinkage, Monte Carlo over batting orders and bowling plans | arXiv 2604.13861 ([PDF](https://arxiv.org/pdf/2604.13861)) | preprint (summary) | v2 uses over number and shrinks through the ewm form |
| A batter's chance of getting out RISES once he is set (per-ball hazard roughly doubles by 30-34 balls); a set batter is higher-variance, not safer | Misra, IPL study ([PDF](https://www.cs.columbia.edu/%7Emisra/set-batter-2026.pdf)); Auckland COMPASS ([slides](https://cdn.auckland.ac.nz/assets/arts/research-centres/compass/documents/COMPASS_Presentation.pdf)) | preprint and slides (summary) | **confirmed, weaker in BBL**: see 3 |
| Compare players across leagues through the players who play in several (transfer fixed effects); CricViz does the same | CricViz ([article](https://cricviz.com/evaluating-different-standards-of-t20-cricket/)); football method ([blog](https://tonyelhabr.rbind.io/posts/soccer-league-strength/)); arXiv 2608.18020 flags competition-strength bias as unsolved | industry, blog | **confirmed and large**: see 4 |
| Context-adjusted player value: charge a batter only for dismissals above the league hazard | arXiv 2608.18020 ([HTML](https://arxiv.org/html/2608.18020v2)) | preprint (summary) | the per-ball model does this by construction |

## 2. What the betting literature says matters

| idea | source | strength | what we do |
|---|---|---|---|
| Choose models on calibration, not accuracy: calibration-chosen +34.7% ROI against -35.2% accuracy-chosen on an NBA season | Walsh and Joshi, *Machine Learning with Applications* 2024 ([Bath](https://researchportal.bath.ac.uk/en/publications/machine-learning-for-sports-betting-should-model-selection-be-bas/)) | peer-reviewed, one season | every choice here is made on log-likelihood / log loss (calibration-sensitive), never hit rate |
| Props carry wider margins than main markets (7.9% against 4.8% average) | Mendeley margin panel ([data](https://data.mendeley.com/datasets/yt3xsvk7zn)) | single-contributor dataset | consistent with props being where the effort goes |
| Whether props are mispriced (not just dearer) is unproven | same, and [iGaming Business](https://igamingbusiness.com/sports-betting/how-global-bookmakers-offer-us-sports/) | industry | only recorded prices answer it |
| Closing line value is the test that survives variance; a sharp book's close is the benchmark, a soft book's is not | [overview](https://simplefunctions.dev/concepts/from-sports-betting-clv-to-pm-trade-quality), [operator guide](https://track360.io/blog/sportsbook-bet-limiting-sharp-player-liability-operator-guide-2026) | weak | CLV against the close, Betfair where it exists, is the paper-season test |
| Books limit winners by quietly cutting stake factors | [operator guide](https://track360.io/blog/sportsbook-bet-limiting-sharp-player-liability-operator-guide-2026) | weak (vendor) | an edge is worth only what can be staked (the brief's risk 1) |
| Fractional Kelly (a quarter to a half) because the edge estimate is itself an estimate | [summary](https://www.topendsports.com/sports-betting/tools/kelly-criterion-calculator/) | weak | staking is decided with the founder after the paper season |
| No study found of favourite-longshot bias in IPL or BBL odds | search, [Springer](https://link.springer.com/article/10.1007/s10479-022-04722-3) for other sports | absence | measurable from our own recorded prices |

## 3. Measured on our data

**Toss and chasing** (decided games, no rain rule):

| | games | chasing side won | toss winner won | chose to field |
|---|---|---|---|---|
| BBL | 615 | 53.0% (±3.9%) | 53.2% (±3.9%) | 60.8% |
| WBBL | 466 | 53.0% (±4.5%) | 48.5% (±4.5%) | 64.2% |
| other club T20 | 6,908 | 53.3% (±1.2%) | 50.6% (±1.2%) | 64.9% |

Chasing is worth about three points everywhere and the toss almost nothing, which is why the toss did not
help the win model. By ground the BBL chase rate runs from 44% (Adelaide, 81 games) to 62% (MCG, 73), but
the ±11% that many games carry makes most of that noise. Dew could not be tested: Cricsheet has no start
times, and nearly every BBL game is at night.

**Power Surge** (BBL 2020/21 on, overs 11 to 18 only): 10.9 runs and 0.44 wickets an over inside the
surge against 8.2 and 0.34 in the same overs outside it. It usually starts in over 15 (middle half 13 to 16).

**Getting out by balls already faced** (not run out), per 100 balls:

| balls faced | 0-4 | 5-9 | 10-19 | 20-29 | 30-39 | 40+ |
|---|---|---|---|---|---|---|
| BBL: outs per 100 balls | 4.7 | 5.4 | 5.1 | 5.0 | 6.0 | 6.6 |
| BBL: runs per ball | 1.01 | 1.30 | 1.39 | 1.46 | 1.55 | 1.71 |
| WBBL: outs per 100 balls | 4.4 | 4.9 | 4.9 | 5.0 | 5.3 | 5.4 |
| WBBL: runs per ball | 0.87 | 1.11 | 1.19 | 1.30 | 1.36 | 1.57 |

A set batter scores 70% faster and gets out 40% more often (BBL), the research's point exactly, though
smaller than its IPL "doubling". A single negative binomial for runs cannot carry this shape; a model that
tracks balls faced can.

**League strength** (men, club T20 since 2018, batters with 120+ balls in a league; the same batter's
runs per dismissal against his IPL figure): India's domestic T20 +20%, BPL +20%, Blast +14 to +16%, Super
Smash +15%, PSL +11%, BBL +1%, CPL 0%, SA20 -7%, The Hundred -11%. Our v1 form treated a run in all of them
the same.

## 4. A leak found during this work (fixed)

Cricsheet lists each XI in the order it batted in that game: the list position equals the actual
batting position for 98.4% of batters, and players who did not bat sit at the bottom 99.5% of the time.
The v1 prop model used that list position as a feature, so it knew in-game who batted and where. The
stand-in returns first reported (BBL +13%, WBBL +17% on 2024/25) were inflated by it. Replaced by
`exp_pos`, his usual position ranked within the XI from past games only, with ties broken on the player
id (a first fix broke ties by row order, which let the order back in; the new test caught that). A test
now shuffles the list order and checks no feature moves. Corrected figures are in section 5.

## 5. What was built, and whether it helped

(In progress: the league adjustment and the ball-by-ball simulator are being compared with v1 on the choose seasons. This section is filled when those runs finish.)
