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

Researched 21 Oct 2026. No free archive of NBA prop OPENING and CLOSING odds was found.

| Source | Cost | What it really holds |
|---|---|---|
| nba_data play-by-play | Free | Done |
| DunkAPI | Free key: 500 credits/month. Paid tiers not confirmed | Prop lines from May 2023 (DraftKings, FanDuel, BetMGM, ESPN BET, Pinnacle and others). **Its own client docs say the NBA archive "mostly holds one pre-game capture per line, so the opening and closing lines are usually the same"**; true opens only from its live capture, October 2026 on. `get_prop_history` = 10 credits for one player, one market, up to 200 games. Game spread/total with open and close per book from July 2020, 10 credits a day. |
| The Odds API | Historical is paid plans only. Third-party listings: US$30 (20K credits), $59 (100K), $119 (5M), $249 (15M); not confirmed on their site | Player props from 3 May 2023 in snapshots every 5 minutes, so real opens and closes. 10 credits per market per region per game per snapshot: 4 markets x 1 region x open + close = 80 credits a game, about 300K for 2023/24 to 2025/26. |
| nba_api (stats.nba.com) | Free | Live injury/inactive lists |

Neither odds host nor stats.nba.com is reachable from the cloud box, so any pull runs from
a new `nba-*` GitHub workflow with the key as a GitHub secret.

## Pulling prop lines (DunkAPI, free key)

`pull_dunkapi.py` reads a request file in `nba/requests/` and saves one JSON per
player-stat to `nba/lines/dunkapi/`, with every call's credits in `ledger.csv`. It runs in
the **nba props pull** workflow (`.github/workflows/nba-props-pull.yml`, its own
concurrency group), which fires when a request file changes on this branch and commits
what came back. The key is the `DUNKAPI_API_KEY` GitHub secret; without it the run
skips and spends nothing. Hard cap per run (`max_credits`), a 20-credit floor on the
account, exact-name matching only, and nothing already saved is bought twice.

First request: 11 players x 4 stats over 2024/25 and 2025/26, about 451 of the free 500
credits.

## First line test (21 Oct 2026, `line_test.py`)

10 players (Durant, Maxey, Brunson, Banchero, Harden, Sengun, Bane, Randle, DeRozan,
Ingram), 5,436 regular-season lines, 2024/25 and 2025/26. Line = DunkAPI's median across
~6-7 books from one pre-game capture (opening = closing in 100% of rows). Every line's
result matched our box score in 99.9% of cases.

| | Our miss | Line's miss |
|---|---|---|
| Points | 6.21 | **6.08** |
| Rebounds | **2.03** | 2.04 |
| Assists | 2.05 | **2.02** |
| Threes | 1.16 | 1.16 |

The line is as good as our projection or better on every stat. Betting our side every
time at the recorded prices: -4.3% (95% CI -7.1% to -1.6%). Only when we disagree with
the line by 2+ is it positive: 426 bets, +4.0% (CI -4.6% to +12.8%), almost all points,
positive in all three calendar years; 3+: 229 bets, +7.3% (CI -4.8% to +19.5%). Not proven.
Not the under bias: backing every under loses 2.9%.

Two cautions. Our projection knows who played; the line was captured at an unknown time
before tip, so some "edge" may be late scratches the capture missed. And the first-cut
probabilities are overconfident (says 73%, wins 55%), so step 2 has to calibrate them.

## Step 2 and the role players (21 Oct 2026, `probability.py`)

**Probabilities.** Each stat is a negative binomial around the projection, with its
spread fitted to the model's out-of-sample misses in 2023/24. The textbook spread (grows
with the projection squared) was wrong for points, whose spread grows in a straight line,
so each stat gets its own curve. Checked on 2024/25: rebounds, assists and threes within
2 to 4 points of honest in every bin (60% said, ~60% happened); points within 5. The
model is now re-trained before each season (walk-forward); freezing it at 2023/24 had
2025/26 points running half a point low.

**Against the bookie.** Blend `logit p = a + b x model + c x market` fitted on 2024/25
lines (3,071), scored on 2025/26 lines it never saw (3,554), 12 players:

| Log loss on 2025/26 (lower is better) | |
|---|---|
| Market alone | **0.6885** |
| Blend | 0.6892 |
| Coin flip | 0.6931 |
| Model alone | 0.6981 |

The line alone is best: on these players, at roughly the close, **it already holds
everything our model knows.** Betting the blend: +2.3% at any edge (CI -4.1% to +9.1%),
falling as the demanded edge rises, which is what no edge looks like.

**Role players are no softer.** Naz Reid and Josh Hart, 1,189 lines: our miss 2.54, the
line's 2.54. Our side every time: -4.6%.

## Injury reports, and the line test without hindsight (21 Oct 2026)

**Data.** The NBA's official injury report (free, no key): `pull_injuries.py` in the
`nba injuries pull` workflow reads the league's archived PDFs with the `nbainjuries`
package. Six snapshots per game day (5pm the day before, then 11am, 1pm, 3pm, 5pm, 7pm US
Eastern), 2023/24 to 2025/26: **2,471 of 2,475 reports read**, saved in
`nba/injuries/raw/` (about 30 MB of CSV). `injuries_check.py` joins them to our players
by team, last name and first initial (92.6% one match, 7.0% none, nearly all players out
for the whole season who never appear in a box score).

**Check.** Last report before tip-off against what happened: Out 29,338 rows, 0.1%
played; Doubtful 237, 0.4%; Questionable 1,507, 52%; Probable 663, 91%; Available 6,204, 85%.

**Projections without hindsight.** `at_report.py` rebuilds the "who plays tonight" inputs
from the report filed by each hour (Out or Doubtful = missing, Questionable = half), with
the same walk-forward models. Minutes miss in January 2025: 4.63 at 5pm the day before,
4.28 at 7pm, 4.01 if you knew who played.

**The line test again** (`line_test_at_report.py`, 12 players, 6,625 lines):

| Projection made at | Our miss | Line's miss | Our side every time | 2+ apart: bets, ROI | Model weight in blend |
|---|---|---|---|---|---|
| 5pm day before | 2.854 | 2.779 | -5.1% | 708, -4.6% | 0.12 |
| 11am | 2.849 | 2.779 | -6.0% | 606, -5.4% | 0.11 |
| 3pm | 2.843 | 2.779 | -6.4% | 579, -6.3% | 0.15 |
| 7pm | 2.840 | 2.779 | -5.7% | 575, -4.3% | 0.19 |
| Knew who played | 2.804 | 2.779 | -3.9% | 472, +4.9% | 0.39 |

The earlier "+4% when we disagree by 2+" came entirely from knowing who played. With
only what the injury report said, every hour loses, and the line alone still scores best
on 2025/26 (log loss 0.688). Against these lines, at roughly the close, there is no edge.
What is left: the OPENING line (before injury news is priced in) and Australian books.

**What is left to test.** (1) The opening line, before the market sharpens: needs The
Odds API's timed snapshots. (2) Australian books against the US close (step 4): needs
no model at all. (3) A better model: real spread/total, injury-news timing.


## Betting angles (21 Oct 2026, `angles.py`)

Angles tested: defence against role (guard/wing/big from per-minute rates; the data has no
positions), stand-in game total, pace, blowout risk, rest, home/away, last game against
average, line against average. All built from earlier games only.

**In real games (29,596 prop-able player-games, 2024/25-2025/26)** they are real. Points
against season average, worst to best bucket: defence vs role 1.17, last game 1.94, total
0.72, rest 0.52, pace 0.41. Our model already absorbs most of it; what it misses, worst to
best bucket: defence vs role 0.32 points (and 0.28 rebounds, 0.25 assists), total 0.14.
So defence vs role is worth adding as a model feature.

**Against the line (12 players, 6,625 lines):** none survives. 9 of 92 buckets were
profitable on the same side in both seasons, no more than luck. The bookies price these
public angles already. One hint to keep: threes unders won 54-56% against a market price
of 52% in both seasons, but the under is priced short (median 1.77-1.81), so backing every
under made -2.5% and +1.6% (both 95% ranges span zero). Low lines (0.5, 1.5) did +3% on
1,022 bets. Not proven; check on more players and best-of-books prices.

## Our own angles (21 Oct 2026, `angles2.py`), directions fixed before testing

| Angle (side) | Test A: actual minus model when on, 95% range | Test B: lines, 24/25 / 25/26 |
|---|---|---|
| Whistle-happy referee crew (pts over) | -0.04 [-0.17, +0.07] | -11.0% (248) / -10.3% (317) |
| Tight referee crew (pts under) | +0.10 [-0.02, +0.21] | -7.1% (264) / -6.5% (307) |
| Star teammate back (pts under) | -0.07 [-0.25, +0.11] | +9.5% (66) / -3.3% (96) |
| Minutes jump (reb over) | **+0.09 [+0.01, +0.17]** | +3.3% (40) / -3.0% (28) |
| **Hot threes last game (threes under)** | **+0.10 [+0.03, +0.18]** (they make MORE than the model expects) | **+8.3% (53) / +16.3% (52)** |
| Tired: 3 in 4 nights or 4th+ road game (pts under) | -0.08 [-0.21, +0.05] | +0.3% (214) / +2.8% (256) |
| New team, first 10 games (no side set) | **-0.57 [-1.11, -0.02]** (score less than the model expects) | too few lines |
| Big favourite's star (pts under) | +0.15 [-0.32, +0.66] | -9.1% (43) / +19.5% (61) |

Dead: referee crews, star back, tired, tanking (too few lines). Leads:
1. **Threes under after a hot shooting night.** Shooters do keep some of it (they beat the
   model by 0.10 threes), but the line jumps by more, so unders won in BOTH seasons. Only 105
   lines, so not proven; fits the wider threes-under lean above.
2. **New team, early season:** our model overrates these players by about half a point a
   game. A model fix first; the market may share the bias (season under way now).
3. **Minutes jump:** our model is slightly slow on rebounds after a role change. Model fix.

## Model v2: the angles as inputs (21 Oct 2026, `model_v2.py`)

Added defence vs role, pace, minutes jump, games with current team, new-team flag and last
game's excess threes. On all prop-able player-games the gain is real but tiny: points miss
5.107 -> 5.096 (2024/25) and 5.053 -> 5.043 (2025/26), both 95% ranges above zero;
rebounds and threes a few thousandths; minutes and assists no change. Against the lines at
7pm: our miss 2.840 -> 2.831, the line 2.779; our side every time -5.7% -> -6.3%. The
angles were mostly already in the model, and the line stays ahead. More features on the
same data have stopped paying; the next answers need more lines.
