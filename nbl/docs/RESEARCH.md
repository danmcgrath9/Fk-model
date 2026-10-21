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

### 5. Knowing the starters: the biggest gain found
Adding who starts (announced shortly before the tip, after books post props) to the minutes and prop
models: minutes miss 4.25 to 4.18; log score better in every market but threes (PRA -3.390 to -3.377,
rebounds -2.161 to -2.154 on the confirm seasons). **An angle: re-price after starting fives are announced.**
Not built: no source for starting fives before the tip has been found; the NBL app shows them.

### 6. Team model: nothing beat the current one
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

## Next, in order
1. Recorded lines: the only test that matters. Then blend our number with the market's and measure closing line value.
2. Starting fives at tip, if a source exists: the largest measured gain.
3. Points by simulation of shots, in the pricing.
4. A Kalman-style projection of each rate (DARKO) to replace the plain decay, and a boosted model on top.

## Sources
- DARKO, What is DARKO: https://www.darko.app/about
- Dunks & Threes, About EPM: https://dunksandthrees.com/about/epm
- FiveThirtyEight, How our NBA predictions work: https://fivethirtyeight.com/methodology/how-our-nba-predictions-work/
- KenPom, Ratings methodology: https://kenpom.com/blog/ratings-methodology/
- Points as shots (practitioner): https://www.excelladz.com/post/how-i-built-an-nba-player-prop-model-part-3
- Usage after an absence (practitioner): https://unabated.com/post/fine-tune-your-nba-prop-betting-strategy-using-unabated-nba
- Market efficiency survey: https://www2.gwu.edu/~forcpgm/Sports_paper_GW1.pdf ; NBA inefficiencies: https://thesportjournal.org/article/nba-gambling-inefficiencies-a-second-look/ ; early-season totals: https://www.ubplj.org/index.php/jpm/article/view/601
