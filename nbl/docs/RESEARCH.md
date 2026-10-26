# NBL model research log

What the strongest public basketball models do, what was tried here, and what the numbers said. Every
choice is made on 2016-17 to 2022-23 (rolling: each season predicted from the seasons before it, or the
2022-23 tuning season) and confirmed on 2023-24 and 2024-25. 2025-26 has been looked at before, so the
clean test from here on is the games played from 22 Oct 2026 (the paper season, `model/grade.py`).

## What the best models do (sources at the foot)

| Idea | Who | Status here |
|---|---|---|
| Each stat has its own memory, decay chosen by fit, exponential in time | DARKO (per-stat decay by days, Kalman filter, boosted trees on top) | **adopted** (per stat, by games) |
| Plus/minus anchored on a box-score prior, then moved by lineup data | EPM, RAPTOR, LEBRON | on-court ratings built (`model/onoff.py`); a box prior did no better than a zero prior |
| Team rating = player ratings x expected minutes | FiveThirtyEight (RAPTOR), EPM team ratings | **in use** (squad on-court rating, open and named) |
| Opponent-adjusted offence and defence, recency-weighted, additive | KenPom | tried, no gain |
| Minutes first: every prop is minutes x rate | every practitioner guide | **in use** (minutes model, 4.25 min miss against 4.63 for the plain average) |
| Points simulated as two-point, three-point and free-throw makes | practitioner prop models | tried: best at the line for points; not adopted yet (needs simulation in pricing) |
| Usage redistribution when a teammate is out | practitioner guides (with/without splits) | tried, no gain |
| Markets: main markets near efficient; lines react to absences by the close; props get less attention | academic studies (spreads, totals); practitioner claims (props) | the reason props are the target, and why recorded lines are the real test |

## Experiments

Props are scored by log score (mean log chance of what happened; higher is better) and by binary log loss at
three .5 lines around the projection (lower is better), on 2022-23 and on 2023-24 to 2024-25.

### 1. Per-stat memory: adopted
`research/rate_memory.py`. One decay (0.92 a game) and one prior (60 minutes) for every stat, against a decay
and prior per stat chosen on 2016-22 by how well rate x actual minutes predicted the next game.

| stat | decay | prior minutes | confirm-season error change |
|---|---|---|---|
| points | 0.95 | 60 | -0.05% |
| rebounds | 0.95 | 15 | -1.3% |
| assists | 0.95 | 30 | -0.7% |
| threes | 0.97 | 60 | -0.8% |
| threes attempted | 0.92 | 15 | -2.0% |
| steals | 0.985 | 240 | -1.2% |
| free throws attempted | 0.95 | 60 | +0.07% |

Decaying by days instead of games (so the off-season counts): no consistent change (`research/rate_memory_days.py`).
Through the full props model, log score improved in four markets of five on both seasons; PRA was level.

### 2. Spread that changes with the projection: adopted
`research/distributions.py`. Negative binomial with a(mu) = a0 mu^k instead of one a per market. The spread
falls as the projection rises (k from -0.9 to -1.4). Line log loss, confirm seasons: points 0.6724 to 0.6678,
PRA 0.6795 to 0.6775, threes 0.3944 to 0.3931, assists 0.4729 to 0.4720, rebounds level. Calibration of the
points over: where we said 60-70% it came in 69% (was 62%).

### 3. Points as shots: promising, not adopted yet
Same experiment. Two-point, three-point and free-throw attempts drawn from the player's rates and minutes,
makes from his shrunk percentages, rescaled to the projection's mean. Best line log loss for points (0.6649
against 0.6678, confirm), worse log score on the confirm seasons. Needs simulation inside the pricing.

### 4. Usage redistribution: rejected
`frame.redistribution`, structural model term `log_boost`. A teammate who usually plays and is absent frees
his usual points, rebounds, assists and shots, shared in proportion to each player's own usual output.
Looking back 1, 3 and 6 games: no change beyond the fourth decimal in any market. Likely reason: recent
minutes already carry it (when a teammate is out, the others' minutes go up, and the minutes model sees it).

### 5. Knowing the starters: the biggest gain found (with knowing the squad, experiment 7)
Adding who starts (announced shortly before the tip, after books post props) to the minutes and prop
models: minutes miss 4.25 to 4.18; log score better in every market but threes (PRA -3.390 to -3.377,
rebounds -2.161 to -2.154 on the confirm seasons). **An angle: re-price after starting fives are announced.**
Not built: no source for starting fives before the tip has been found; the NBL app shows them.

### 6. Kalman filter for each rate (DARKO): rejected
`research/kalman_rates.py`. A drifting true rate per player and stat, game weight growing with minutes, extra
drift over the off-season. Against the adopted per-stat decay, error on the confirm seasons changed by 0.02% to
0.36%, with the best settings at the edge of the search. Not worth the complexity: rate estimation is
saturated with this data.

### 7. What the backtest assumes about team news
The prop models use who dressed for the game (the named squad: teammates out, the squad's usual minutes).
Taking that away (only last game's squad known): minutes miss 4.25 to 4.34, log score worse in every market
(points -3.107 to -3.113, assists -1.630 to -1.631, confirm seasons). Against the naive stand-in book the
returns barely move (points +13.9% to +11.7%, PRA +12.9% to +14.3%), because that book ignores team news too;
a real book does not. **So: bet props after the squads are named, and re-run the price sheet then.** Starting
fives (experiment 5) are worth about as much again.

### 8. Team model: nothing beat the current one
`research/team_experiments.py` (rolling 2018-19 to 2022-23, then 2023-24 and 2024-25, log loss):

| features | rolling | confirm |
|---|---|---|
| Elo only | 0.6550 | 0.6654 |
| current (named squad) | 0.6564 | **0.6600** |
| + opponent-adjusted efficiency | 0.6575 | 0.6602 |
| adjusted instead of raw efficiency | 0.6570 | 0.6604 |
| + early-season weights | 0.6582 | 0.6619 |
| lean: Elo, squad rating, adjusted efficiency, rest | **0.6538** | 0.6616 |

Differences under 0.003. With these inputs the margin is mostly noise; more needs information (injuries,
starting fives, the market itself).

### 9. Voulgaris's angles: second halves, tendencies, half time
`research/voulgaris.py`, 1,503 regulation games whose quarters add up to the final (2015-16 to now).
Voulgaris made his name on NBA second-half totals (books split the full-game total about 50/50 while second
halves scored more, late fouling in close games being the usual explanation), on coaches' game-management
habits, and later on "Ewing", a lineup-level game simulator. Sources: the ESPN profile and secondary write-ups
below; the details are second-hand.

- **NBL halves are the other way round.** First halves outscore second halves in every one of 12 seasons:
  3.7 points a game on average (the first half carries 50.4% to 51.5% of a season's points; 50.8% of our
  pre-game total, 2016-22). The third quarter is the lowest-scoring quarter in 9 of 12 seasons. A book that
  splits a total evenly gives value on first-half overs and second-half unders: the reverse of his NBA bet.
- **Late fouling does not show up as more second-half points** in close NBL games (final margin 0-5: second
  half 4.2 below the first; 6-10: 1.2 below, with the 4th quarter 1.0 above the other quarters' average).
- **Team tendencies do not last.** A team's games' second-half lean, odd games against even games in the same
  season: r = -0.08; one season to the next: r = 0.14; a team's share of its points in the 4th quarter,
  odd against even: r = 0.11. Coaches are not in the data, so his coach angle cannot be tested directly.
- **At half time, the first half says almost nothing about the second.** Predicting second-half points on
  2023-24: "same as the first half" misses by 12.3; our pre-game total x the second-half share misses by 9.6;
  adding the first half and the half-time margin to the pre-game total does no better (9.6). If a book's live
  second-half line follows first-half pace, the edge is to trust the pre-game number instead.
- Built from this: the price sheet now prices first- and second-half totals; the grader scores them; the line
  recorder takes pre-game half totals with the props and one live snapshot of the second-half lines at half time
  (40-80 minutes after the tip); the probe checks whether Australian books post NBL half markets at all.
- "Ewing" (simulate a game lineup by lineup from projected minutes and on-court ratings): the ingredients exist
  (`model/onoff.py`, the minutes model); not built.

### 10. Session of 26 Oct 2026
- **Points priced shot by shot: adopted.** Attempts and makes simulated from the player's rates (`props.shot_draws`),
  rescaled to the projection. Line log loss for points: 2022-23 0.6709 to 0.6678 (where it is chosen, automatically,
  inside `props.project`), 2023-24 to 2024-25 0.6678 to 0.6643. The price sheet uses it.
- **Threes as attempts x makes: rejected.** 0.4539 to 0.4544 (2022-23), 0.4520 to 0.4527 (confirm).
- **Each player's own minutes spread in the simulation: rejected.** 2022-23 0.6678 to 0.6675, confirm 0.6643 to 0.6646.
- **Offence and defence on-court ratings (O/D-RAPM): inconclusive, not adopted.** `research/od_ratings.py`. Totals:
  rolling 14.45 to 14.79 points miss (worse), confirm 14.92 to 14.61 (better); margin log loss 0.6564 to 0.6562
  rolling, 0.6600 to 0.6586 confirm. Choices are made on the rolling seasons, which said no.
- **How prop bets move together** (standardised misses, 2023-24 and 2024-25): same player points-PRA 0.915,
  points-threes 0.648, rebounds-PRA 0.575; teammates slightly negative (points -0.059: they share the ball);
  opponents about zero. Used by the staking.
- **Benter's second stage, built** (`betting/market.py`, `betting/staking.py`): margin stripped from book prices,
  our chance combined with the market's in a logit (the racing rule, half each, until 400 recorded results; then
  fitted by maximum likelihood), quarter Kelly on the combined chance, shrunk for correlated bets, capped at 2% a bet
  and 15% a round. Benter's own finding is the reason: his model alone did not beat the public, the combination did.

### 11. Session of 26 Oct 2026, second round
- **Team memory (TEAM_DECAY): kept at 0.90.** `research/team_memory.py`, 0.80 to 0.97: 0.90 is best on the rolling
  seasons for totals (14.45 points miss) and level for margins; longer memory looked better on 2023-25 totals only.
- **Minutes features: rejected.** Foul rate, rotation size and rank, recent role change: minutes miss 4.246 to
  4.249-4.256, log scores unchanged in the fourth decimal. With pre-game information minutes look saturated; only
  knowing the starters moved them (experiment 5).
- **Recalibrating the over chance** (a logistic layer fitted on 2022-23): helped PRA a lot (line log loss 0.6775 to
  0.6725 on 2023-25), points a little, nothing else; its PRA coefficients said the distribution's shape was wrong,
  so the cause was fixed instead:
- **PRA simulated from its parts: adopted.** Shot-by-shot points plus rebounds and assists, Poisson at the player's
  rates over the same simulated minutes, rescaled to the projection. Line log loss 2022-23 0.6791 to 0.6775,
  2023-25 0.6775 to 0.6740. Rebound and assist spread inside the simulation chosen on 2022-23 (Poisson beat
  gamma-mixed shapes 3, 8, 20). A spread fitted to the lines instead did less (0.6760 on 2023-25).

- **Bottom-up team total (Ewing-lite): adopted.** `research/bottom_up.py`. Each squad's expected points from its
  players (per-minute scoring rate x share of the team's 200 minutes x expected pace), used RELATIVE to the league's
  recent level: the absolute version won 5 of 7 rolling seasons but missed 2020-21 (the hub season) by 18.1 points,
  carrying the previous season's scoring over. Relative version: total miss rolling 14.45 to 14.24, 2023-25 14.92
  to 14.61, better in 6 of 7 rolling seasons. In the team report: 2024-25 15.6 to 15.2, 2025-26 15.1 to 14.8, this
  season 15.9 to 15.3 (a fourth look at those seasons; the choice was made on 2016-22). Margin: no gain.

## Next, in order
1. Recorded lines, half lines included: the only test that matters. Then blend our number with the market's and measure closing line value.
2. Starting fives at tip, if a source exists: the largest measured gain.
3. Fit Benter's combination on recorded lines (400+ results), then paper bets with the staking.
4. Tried and set aside: Kalman rates, usage redistribution, adjusted efficiency, early-season weights.

## Sources
- DARKO, What is DARKO: https://www.darko.app/about
- Dunks & Threes, About EPM: https://dunksandthrees.com/about/epm
- FiveThirtyEight, How our NBA predictions work: https://fivethirtyeight.com/methodology/how-our-nba-predictions-work/
- KenPom, Ratings methodology: https://kenpom.com/blog/ratings-methodology/
- Points as shots (practitioner): https://www.excelladz.com/post/how-i-built-an-nba-player-prop-model-part-3
- Usage after an absence (practitioner): https://unabated.com/post/fine-tune-your-nba-prop-betting-strategy-using-unabated-nba
- Voulgaris, ESPN profile: https://www.espn.com/blog/playbook/dollars/post/_/id/2935/meet-the-worlds-top-nba-gambler ; secondary accounts: https://sportshistorynetwork.com/gambling/inside-the-mind-of-haralabos-voulgaris/ , https://www.sportsboom.us/betting/nba-betting-strategies
- Market efficiency survey: https://www2.gwu.edu/~forcpgm/Sports_paper_GW1.pdf ; NBA inefficiencies: https://thesportjournal.org/article/nba-gambling-inefficiencies-a-second-look/ ; early-season totals: https://www.ubplj.org/index.php/jpm/article/view/601
