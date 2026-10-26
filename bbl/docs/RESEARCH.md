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

All choices on the choose seasons (2022/23, 2023/24); 2024/25 confirms; 2025/26 still held back.

**League-strength adjustment: adopted.** Each player-game's figures are divided by its league's factor
(estimated on matches before July 2022) before they enter his form, and the model is told the league of
the game being priced. On the choose seasons, against the leak-free unadjusted build, per player-game
log-likelihood of runs (when he bats): BBL +0.0004 (90% interval -0.0003 to +0.0011, 82% likely positive),
WBBL +0.0038 (+0.0013 to +0.0064, 99%). Chance to bat: BBL +0.004, WBBL -0.006 (worse). Team win chance
unchanged; WBBL first-innings runs 0.15 runs worse (noise at ~100 games). A small, principled gain on the
market we would bet; on by default (`LEAGUE_ADJUST=0` builds the unadjusted frame).

**Ball-by-ball simulator (v2): not adopted, kept as the research direction.** Two rounds:

| choose seasons | v1 (current) | v2, first build | v2, with home ground, ratings, varied batting order |
|---|---|---|---|
| BBL head-to-head, bits | 0.062 | 0.005 | 0.038 |
| WBBL head-to-head, bits | 0.036 | 0.019 | 0.025 |
| BBL first-innings runs, CRPS | 16.37 | 16.63 | 16.74 |
| WBBL first-innings runs, CRPS | 16.33 | 16.66 | **16.34** (miss 23.06 against v1's 23.28) |
| BBL player runs, log-lik | -3.772 | -3.856 | -3.803 |
| WBBL player runs, log-lik | -3.705 | -3.759 | -3.750 |
| WBBL chance to bat, log-lik | -0.466 | -0.469 | **-0.456** |

A 50/50 or 25/75 blend of v1 and the first v2 did not beat v1 on runs, and only WBBL win chance edged up.
The first build's diagnosis found the gaps that the second closed half of: a fixed batting order credited
openers with 26.8 runs a game against an actual 24.2 (BBL) and 27.1 against 23.1 (WBBL), and the ball model
had no home advantage. What remains, in order of likely value:
1. **Match-level conditions.** WBBL simulated first innings spread 24.6 runs against 29.2 in reality; nothing
   in a ball model makes a whole match high or low scoring (the "thin tails" critique of WASP-style models).
   A shared per-match draw (pitch, weather) would add it.
2. **Phase-specific player skill.** A batter's power-play and death-over rates differ; the ball model sees
   one blended rate per player (the batting-order paper's point).
3. **Bowling plans.** Workload-weighted random overs ignore who bowls at the death.
4. **More simulations and a bigger ball model** once the structure is right (600 simulations, 150 trees now).
The simulator's value is that it prices every market from one match, so same-game combinations, top batter
and player props agree with the team price; that is worth building toward, not worth betting on yet.

**Corrected stand-in results (v1, leak-free, league-adjusted, current build):**

| runs vs stand-in line, 1.87 both ways | bets | hit | ROI | 90% interval |
|---|---|---|---|---|
| BBL choose 2022/23-2023/24 | 178 | 64.0% | +19.8% | +7.1% to +32.4% |
| **BBL confirm 2024/25** | 88 | 60.2% | **+12.6%** | **-1.8% to +21.8%** |
| WBBL choose | 392 | 62.8% | +17.4% | +10.9% to +23.7% |
| **WBBL confirm 2024/25** | 116 | 58.6% | **+9.6%** | **-1.8% to +25.3%** |

Both confirm intervals now include zero. Still an upper bound against a stand-in, as before.

## 6. What "best in the world" needs that we do not have

- **Real prices.** The literature's test is closing line value against a sharp close (Betfair). Without
  recorded prices every return above is a proxy. The single most valuable next step is the odds key.
- **Ball-tracking data** (line, length, speed, shot type) is what CricViz and the broadcasters' models run on;
  not public. Cricsheet's ball outcome is the ceiling of what we can know about each delivery.
- **Start times and weather** for dew and rain: Cricsheet has dates only. Open-Meteo history needs a paid
  plan for this use; a fixture list with start times would let BOM daily data in for free.
- **Announced squads and late changes** for the team-news test (no archive exists; record them ourselves).

## 7. Collected 22 Oct: start times, home sides, weather, squads (bbl/docs/DATA_INVENTORY.md)

- **Day against night (BBL):** the chasing side won 34% of 47 day games and 55% of 500 night games.
- **Dew (BBL):** the closer the air to its dew point at the end of the game, the more often the chase wins:
  57.6% under a 3C gap, 52.6% at 3 to 6C, 50.8% over 6C (611 games; logistic slope -0.043 per 1C, permutation
  p = 0.02). Several weather effects were looked at, so this is promising, not proven. It is only usable once the
  toss says who chases, with a forecast for the night, and it is to be confirmed on seasons not yet looked at.
- **Home side (BBL):** won 52.6% of 435 games where the page marks it; venue_share (our home proxy) averages
  0.38 for those sides against 0.19 for all, so the proxy tracks it.
- **Weather and scoring:** no link between weather and first-innings runs above the ground's average (all |r| < 0.1).

## 8. Improvements while waiting for odds (26 Oct)

Each judged on 2022/23-2023/24 and then checked on 2024/25; anything that worked in only one of the two was dropped.

| change | choose seasons | 2024/25 | decision |
|---|---|---|---|
| **After-the-toss win price, BBL** (who chases, chasing at night) | 0.062 -> 0.069 bits | -0.020 -> +0.009 bits | **adopted** for the after-toss price only; the pre-toss price never sees it |
| same for WBBL | 0.036 -> 0.024 | | not adopted |
| dew-point gap in the win price | no gain beyond night | | not adopted (only BBL/WBBL games have weather to train on) |
| night and dew as prop inputs | runs WBBL -0.003 (interval excludes 0) | | not adopted (`PROPS_CONTEXT=1` to compare) |
| **phase skills, chance to bat** (powerplay and death shares, strike rates, dot rate) | WBBL +0.0063 per player-game (97% likely positive), BBL -0.0004 | WBBL +0.0021, BBL +0.0010 | **adopted** for the chance-to-bat model only |
| phase skills, wickets (death and powerplay economy, death share) | BBL +0.0035, WBBL +0.0024 | BBL -0.0011, WBBL -0.0063 | dropped: one period only |
| phase skills, runs and sixes | no gain | | not adopted |
| spread recalibration for sixes and wickets | WBBL sixes -0.640 -> -0.672 on the real run | | rejected: the prototype's gain came from where its grid stopped (overfitting); sixes stays flagged |

**Benter's second stage, built and tested, waiting on prices** (`bbl/model/benter.py`): our chance and the market's
(margin removed by the power method) blended as p proportional to exp(alpha log p_model + beta log p_market), alpha and beta fitted
walk-forward by season. On made-up markets it gives equal sources equal weight and beats both, and gives a model
that adds nothing no weight at all, which is the property that keeps us off bets the market already prices. The
paper comparer labels every edge UNBLENDED until real weights exist.

**Paper record started** (`bbl-price` workflow): every game in the next three days priced and logged before it is
played, with time and code version, and scored once Cricsheet has the result. The first log holds WBBL|12's two
openers (29 Oct). The daily schedule needs the workflow file on `main` (GitHub runs schedules only from the
default branch); until then it runs on a push.
