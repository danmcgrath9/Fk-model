# NBA player props: step 1, the projection

Separate from the racing code. Nothing here touches `research/form_gbm`, `data/live_bets`,
the `fk-*` workflows, the Form King key or BetMatic. No bets, paper or real.

## What it does

Projection for each player-game = **minutes x per-minute rate**, for points, rebounds,
assists and threes made. Two LightGBM models per stat (minutes; rate weighted by minutes).

| File | Job |
|---|---|
| `fetch_data.py` | Downloads cdn.nba.com play-by-play, 2020/21 to 2025/26, from github.com/shufinskiy/nba_data (free). |
| `boxscores.py` | Rebuilds every box score from play-by-play: counting stats from events, minutes from substitutions. |
| `features.py` | Pre-game features. Every one is computed from earlier games only. |
| `project.py` | Trains on 2020/21 to 2023/24, scores 2024/25 and 2025/26, prints the scorecard. |
| `tests/test_nba.py` | Hand-checked minutes on a made-up game; a test that changing a game's result moves none of that game's features. |

```
python nba/fetch_data.py && python nba/boxscores.py && python nba/features.py && python nba/project.py
python -m pytest nba/tests -q
```
Data lands in `nba/data/` (git-ignored, ~1.3 GB).

## The box scores can be trusted

nba_data ships play-by-play, not box scores, so they are rebuilt and checked:

| Check | Result |
|---|---|
| Games | 7,230 regular-season games, 154,330 player-games |
| Team points = final score | 100.00% of games |
| Points, rebounds, assists = cdn.nba.com's own running totals | 100.00% of player-games |
| Team minutes add to 5 x game length | 99.96% of games (the 3 that fail are dropped) |

## Results, out of sample (run 21 Oct 2026)

Scored on players averaging 20+ minutes coming in and 5+ games into the season, about
who books post lines for. Mean absolute error, lower is better.

| Season | Stat | Model | Season avg | Last-10 avg | Model's gain on the better average, 95% CI |
|---|---|---|---|---|---|
| 2024/25 | Minutes | **4.12** | 4.85 | 4.49 (ewm) | |
| 2024/25 | Points | **5.11** | 5.32 | 5.35 | 0.18 to 0.25 |
| 2024/25 | Rebounds | **2.00** | 2.06 | 2.08 | 0.05 to 0.08 |
| 2024/25 | Assists | **1.54** | 1.57 | 1.60 | 0.02 to 0.04 |
| 2024/25 | Threes | **1.05** | 1.06 | 1.08 | 0.00 to 0.01 |
| 2025/26 | Minutes | **4.11** | 4.85 | 4.46 (ewm) | |
| 2025/26 | Points | **5.05** | 5.28 | 5.27 | 0.18 to 0.25 |
| 2025/26 | Rebounds | **1.98** | 2.03 | 2.06 | 0.04 to 0.06 |
| 2025/26 | Assists | **1.54** | 1.57 | 1.58 | 0.02 to 0.04 |
| 2025/26 | Threes | **1.03** | 1.04 | 1.05 | 0.00 to 0.01 |

About 14,600 to 14,900 player-games per season. The bootstrap resamples whole games.

**What this does and does not show.** The model beats the two averages a punter would
use, in both test seasons, by the same amount each time. That is the bar for step 1. It
says **nothing yet about beating a bookmaker**: a prop line is far sharper than a season
average. Step 3 (against DunkAPI's opening and closing lines) is the real test. Threes
barely beat the averages, so treat threes as the weakest market until step 3 says otherwise.

## Known limits, stated loudly

1. **Who's playing tonight is taken as known.** The model is told which rotation players
   (10+ minutes a game) play. In real life that comes off the injury report and the
   inactive list ~30 minutes before tip, but coach's-decision DNPs and first-minute
   injuries are visible here and would not be. Removing these inputs costs 0.09 points
   and 0.22 minutes of MAE; the model still beats both averages without them. So
   roughly 40% of the points gain depends on knowing the lineup, which means **bets
   must go on after the inactive list, not at an open posted the day before**. That
   cuts against the racing edge (get on at the open) and needs step 3 to settle.
2. **Spread and total are stand-ins.** `exp_margin` / `exp_total` come from each team's
   prior points scored and allowed. The real game spread and total (The Odds API,
   paid) should replace them; blowout risk drives starters' minutes.
3. **Regular season only.** Playoff rotations shorten; not modelled.
4. **A player is only projected for games he played.** Props are void if he does not
   play, so that is the right conditioning, but a projection made before the
   inactive list has to be thrown away if he is ruled out.
5. A starter who plays a whole first quarter without touching the ball or being
   subbed is invisible to the events; those few games fail the minutes check and are
   dropped.

## What costs money (nothing yet)

| Source | Cost | Needed for |
|---|---|---|
| nba_data play-by-play | Free | Done |
| DunkAPI historical prop lines | From US$19/month (their figure, not yet checked) | Step 3 |
| The Odds API historical spreads/totals | Paid plan | Replacing the stand-ins |
| nba_api (stats.nba.com) | Free, but blocked from the cloud box | Live injury/inactive lists |

Next: step 2, turning each projection into an over/under probability.
