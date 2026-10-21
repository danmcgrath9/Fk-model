# What the best NBA models do, and what that means for ours (21 Oct 2026)

Sources are rated for trust. Our own numbers come from code in this folder.

## What the best do

| Who | What | Trust |
|---|---|---|
| **DARKO** (Kostya Medvedovsky; "Daily Adjusted and Regressed Kalman Optimized") | Uses EVERY game a player has played, older games decayed (e.g. 0.99 a game, so a year-old game counts ~40x less than yesterday's), with a different decay per stat; Bayesian updating ("Kalman filter") so each new game moves the estimate by how surprising it was; refreshed daily for every player and box stat. The best-known public projection system. | Medium: public descriptions only, internals not published |
| **Haralabos Voulgaris** (widely called the best NBA bettor; later Mavericks quant director) | Started by watching games for COACHING patterns: rotations at the same minute marks each quarter, predictable late-game strategies; books were slow to adjust (halftime totals). Then built "Ewing" with a mathematician: a simulator that plays out a game between two teams and projects the score. | Low-medium: profiles and interviews, no technical detail |
| **Impact metrics** (RAPM, RPM by Jeremias Engelmann, EPM, LEBRON, DPM) | Team-strength building blocks: regularised plus-minus with a box-score prior. No public head-to-head says which predicts best; practitioners blend them. | Medium |
| **Prop-model practitioners** | Every stat = minutes x rate; minutes is "the hardest input"; per-possession rates scaled by pace; shrink small samples; Monte Carlo for the spread of outcomes; anchor to team totals so a rested star's usage goes somewhere. | Low: blogs, but consistent |
| **League rule** | Starting lineups must now be set 30 minutes before tip (was 10). Lines can be caught by late news; earlier info could help either side. | Medium (Action Network) |

## What we tested against that, on our data

| Idea | Result |
|---|---|
| DARKO-style very slow decay (half-life ~70 games) on rates | No gain (`decay_test.py`) |
| Coach rotation tendencies (blowouts, close games), player boost when teammates out | No gain (`tendencies.py`) |
| Defence vs position, pace, form, new team, hot shooting | Points miss -0.01 a game; real but tiny (`model_v2.py`) |
| **Where our error comes from** | If our MINUTES were perfect, the points miss would fall 13% (5.08 to 4.40), rebounds 9%, assists and threes 5-6%. Minutes is the biggest lever we control; the rest is game-to-game luck no model removes. At 7pm our minutes miss is 4.41. |
| Our miss vs the line (12 stars) | Line 5.86 points, ours 6.09: the line is ~4% better, about a third of what perfect minutes would buy, which is consistent with the books having better minutes information than the 7pm injury report. |

**Bottom line:** the model is at the level a box-score model can reach; more inputs from the
same box scores stop paying. The best in the world are better because of MINUTES
INFORMATION and SPEED (lineups, minutes limits, rotations) and because they price the whole
game together, not because of a cleverer formula on the same data.

## Plan to become as good as it gets, in order

1. **Re-project at the last report before each tip-off.** The official injury report comes
   every 15 minutes and starting lineups are set 30 minutes before tip. A run 45 and 20 minutes
   before each game's tip uses the freshest outs. Free (daily pipeline + more schedule times).
2. **Real spreads and totals** in place of our stand-ins (The Odds API month): blowout risk is
   the main driver of starters' minutes that we cannot see today.
3. **Lineup-level minutes from play-by-play.** We already rebuild who is on court from
   substitutions; next is each coach's actual rotation (who comes in for whom, at what minute)
   and how it changes when a named player sits. This is Voulgaris's edge in data form.
4. **Simulate the game** (Ewing-style) so points, rebounds, assists and PRA come out
   correlated and consistent with the team total; needed for combos and multis.
5. **Always price against the market**: the line holds information we lack, so the bet
   decision blends both (done in `probability.py` / `backtest_odds.py`).
6. **Judge only on out-of-sample profit at the time you could have bet**, never on fit.

## Sources

- DARKO: [DARKO site](https://apanalytics.shinyapps.io/DARKO/_w_66db5831/), [Wharton paper citing it](https://wsb.wharton.upenn.edu/wp-content/uploads/2023/12/Brill_2023_Q.pdf), [Bright Side of the Sun](https://www.brightsideofthesun.com/suns-analysis/99966/suns-darko-dpm-analytics-oso-ighodaro-defense-devin-booker-impact-advanced-stats-roster-projections)
- Voulgaris: [The Power Rank](https://thepowerrank.com/the-craft-of-sports-betting-professionals-2/), [Sports History Network](https://sportshistorynetwork.com/gambling/inside-the-mind-of-haralabos-voulgaris/), [Trademate](https://tradematesports.medium.com/nbas-greatest-ever-bettor-haralabos-voulgaris-from-pro-bettor-to-maverick-s-director-10-people-7f142bbf95dd), [Casino.org](https://www.casino.org/blog/wild-life-worlds-best-nba-bettor/)
- Impact metrics: [APM (Wikipedia)](https://en.wikipedia.org/wiki/Adjusted_Plus_Minus), [arXiv 1604.03186](https://arxiv.org/pdf/1604.03186), [The F5 on RAPM](https://thef5.substack.com/p/rapm-eye-test), [Royce Webb / Engelmann](https://www.roycewebb.com/p/final-nba-draft-big-board-why-ace)
- Prop practice: [Engelmann newsletter](https://jeremiasengelmann.substack.com/p/how-to-accurately-predict-nba-player), [Building an NBA prop model](https://lordwinrow.medium.com/building-an-nba-prop-model-a-lockdown-project-part-4-ec00c1c3de6e), [pace and props](https://nbaplayerbets.com/articles/nba-pace-of-play-prop-betting/), [arXiv 2406.09895](https://arxiv.org/pdf/2406.09895)
- Lineups: [Action Network, 30-minute rule](https://www.actionnetwork.com/nba/nba-rule-change-starting-lineups-sports-betting), [Legal Sports Report](https://www.legalsportsreport.com/35137/nba-lineups-sports-betting-dfs/)
- Free live data: [SportsDataVerse data releases](https://github.com/sportsdataverse/sportsdataverse-data), [hoopR](https://rdrr.io/cran/hoopR/f/README.md); paid alternatives checked: [balldontlie](https://highlightly.net/blogs/best-nba-apis-in-2026), [API-NBA free 100/day](https://www.api-football.com/news/post/how-to-get-started-with-api-nba-the-complete-beginners-guide)
