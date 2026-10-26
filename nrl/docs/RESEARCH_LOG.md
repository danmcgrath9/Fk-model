# Research log: what we tried to make the NRL model better, and what happened

Every idea is judged the same way: settings tuned on FIT (2003-2018) only, scored on DEV (2019-2022) and
CONFIRM (2023-2024), **adopted only if it helps on both**. The final seasons (2025-2026) were scored once on
21 Oct 2026 and cannot vote on later changes. Numbers are bits per game (higher is better) or log loss / Brier /
miss (lower is better), from the runs named.

## What the outside world does (21 Oct 2026 reading)

| Who / what | What it does | What we took from it |
|---|---|---|
| [Rugby Club Ranks](https://rugbyclubranks.github.io/accuracy_page.html) | Glicko-style rating per player, summed for the named side, separate winner and margin regressions | the same structure as ours (player ratings plus team ratings); its page could not be read from here, so no figures compared yet |
| [Stats Chat (David Scott)](https://www.statschat.org.nz/author/david-scott/page/167/) | team ratings shrunk between seasons; published NRL tipping rates of about 54% to 66% a season | our teams-named model tips 67% (confirm) and 63% (final): the same band |
| [Alphr](https://alphr.com.au/nrl/accuracy), [TippingEdge](https://tippingedge.com.au/how-it-works/) | XGBoost ensembles on 100-160 features | they publish 61-64% held-out strike rates and Alphr a -3.2% margin ROI in 2026: accuracy is not profit |
| [UTS travel study](https://opus.lib.uts.edu.au/handle/10453/151653) | 2,352 NRL games 2007-2019: about 1.1 points of margin lost per 1,000 km travelled | to test (needs venue coordinates from the weather pull) |
| [Net Wins Added (RQES)](https://lida.sport-iat.de/ta/Record/4092548?lng=en) | player value from Stats Perform match data, "predicts 80.9% of winners" | uses each match's own stats, so it explains games after the fact; not a forecast. Warning, not a method |
| Plus-minus in soccer ([Sæbø & Hvattum](https://arxiv.org/pdf/1706.04943)) | player ratings and team ratings combined beat either alone | that is our design |
| Try-scorer sellers ([Hard Yards Edge](https://www.hardyardsedge.com.au/), betting guides) | split the market's implied try total across players; books lean on a player's own record | market-implied team totals are the next try-model input once odds exist |
| Sharp benchmarks | closing line value against a sharp closing price (Pinnacle, Betfair) is how professionals judge a model | the real test of this model; needs the odds pull |

No peer-reviewed NRL betting-market efficiency study turned up; the favourite-longshot literature is soccer and racing.

## Experiments on our data

| Idea | Result | Decision |
|---|---|---|
| Damp blowouts in rating updates (tanh cap), with the update rate re-tuned | FIT miss 13.447 -> 13.444 at best | rejected: noise |
| Club-specific home advantage | FIT miss 13.447 -> 13.457 and worse | rejected |
| Faster rating updates in a team's first 6 games of a season | FIT 13.447 -> 13.456 and worse | rejected |
| Spread that varies by game (expected total, mismatch) | DEV line Brier 0.18321 -> 0.18356, CONFIRM 0.19645 -> 0.19657 | rejected |
| Gradient-boosted margin model | DEV 0.160 -> 0.118 bits; blend 50/50 DEV 0.144, CONFIRM 0.0945 v 0.0925 | rejected: fails on DEV |
| Line-up box-score strength (named 17's recent run metres, line breaks, try assists, tackle breaks, missed tackles), ridge | DEV 0.1590 -> 0.1618 bits, CONFIRM 0.0928 -> 0.0886 | rejected: helps one set only. Plain least squares on 11 stats broke outright (collinear stats whose relationship changed with the 2020 six-again rule) |
| **Key-number margin distribution** (t curve re-weighted by how often each exact margin happens) | exact-margin log loss DEV 4.25 -> 3.87, CONFIRM 4.29 -> 3.91; win bits DEV 0.1581 -> 0.1591, CONFIRM 0.0913 -> 0.0924; half-point lines unchanged | **adopted**: h2h and margin bands in the price card |
| Champion Data form in the try model (line breaks, tackle breaks, run metres, try assists, possessions) | log loss DEV 0.4238 -> 0.4229, CONFIRM 0.4376 -> 0.4373 | **adopted** (small) |
| Referee tendency (the referee's recent totals against expectation, from RLP appointments) | totals miss DEV 10.060 -> 10.055, CONFIRM 10.755 -> 10.756 | rejected: no effect |
| **Travel distance** (away km - home km, per 1,000 km; club base = town of most home games) | teams named DEV 0.1589 -> 0.1597 bits, CONFIRM 0.0913 -> 0.0926; at the open 0.1498 -> 0.1502 and 0.0876 -> 0.0890; 0.7 points per 1,000 km (UTS study: 1.1) | **adopted** in the team model |
| Weather, actual (Open-Meteo archive; roofs dry) | totals miss DEV 10.061 -> 9.911, CONFIRM 10.747 -> 10.613 (rain in the game -1.4 points per mm; 31 games with 2mm+ averaged 35.3 against 43.9); anytime try log loss DEV 0.42294 -> 0.42284, CONFIRM 0.43725 -> 0.43658; run metres mixed, tackles flat | helps in hindsight only, see the forecast test |
| Weather, as a bettor knows it (day-ahead forecasts, Previous Runs archive, 2024: the only confirm season it covers, 213 games) | day-ahead rain in the game correlates 0.58 with what fell (temperature 0.97, dew point 0.96). Totals miss 10.901 with no weather, 10.929 with actual weather, 10.977 with the forecast; using only the well-forecast variables (24h rain, temperature, dew point) 10.952. Open-Meteo's "historical forecast" archive was IDENTICAL to actual weather (rain correlation 1.00) and tests nothing | **not adopted** for live prices: the gain exists only in hindsight and came from a few very wet games, which are what forecasts miss. Re-test in 2027 with every game's day-ahead forecast recorded beside the totals line |
| Team scoring style (each side's recent totals against expectation) | totals miss DEV 10.060 -> 10.055, CONFIRM 10.755 -> 10.778 | rejected: fails CONFIRM |
| Rain and humidity shrinking the margin (expected margin x rain, x dew point) | DEV 0.1573 -> 0.1539 bits, CONFIRM 0.0893 -> 0.0798 | rejected: rain lowers totals, not margins |
| **One name per club** (bug fix): RLP records each season's name, and every rename restarted a club at average (Bulldogs 2000 and 2010, Sharks 2000 and 2003, Warriors 2001 and 2002, Roosters 2000) | the Warriors' 2002 restart: +13.5 actual against +3.3 predicted over 8 games. DEV/CONFIRM barely move (last rename 2010): teams named 0.1597 -> 0.1595, 0.0926 -> 0.0927 | **fixed** |
| **Expansion clubs start 4 points below average** (Titans 2007 tuned, Dolphins 2023 checked; mergers excluded) | Titans miss 12.31 -> 11.87; Dolphins miss 12.96 -> 12.96, bias -3.5 -> -0.9 | **adopted**: the Perth Bears start there in 2027 |
| State of Origin back-ups (players who played Origin in the last 3 or 7 days, home minus away; RLP Origin ids match NRL ids) | teams named DEV 0.1589 -> 0.1582, CONFIRM 0.0930 -> 0.0928; open likewise | rejected: no fatigue effect (back-up players are stars the ratings already count) |
| Two-stage try model (players rescaled to a team-level try model) | the players' own sum is the better team total (Poisson deviance DEV -1.2576 v -1.2384); full rescale DEV 0.42286 -> 0.42401 | rejected |
| **Refit before each season on every completed season** (live policy; backtests keep the frozen 2003-2018 fit) | on 2023-24 with a fit through 2022: try model 0.4372 -> 0.43635 (tries per team-game predicted 3.78 -> 3.90, actual 4.00), team model 0.0930 -> 0.0979 bits | **adopted** for the price card |
| Running league-level try correction | DEV unchanged, CONFIRM 0.4372 -> 0.43697 | not needed once the models are refitted each season |
| Attack and defence ratings per player (each side's score from its 17's attack and the other 17's defence; ridge tuned on 2006-2018 to 5,000) | margin unchanged; totals miss DEV 10.060 -> 10.088, CONFIRM 10.755 -> 10.769 (a lighter ridge: DEV worse, CONFIRM better) | rejected: the 2006-2018 gain does not carry into the post-2020 game |
| Try calibration by position (diagnostic) | both DEV and CONFIRM: centres over-predicted 6-9%, forwards under-predicted (second row 13%, props 13-20%, hookers 12%): tries have shifted from centres to forwards in the modern game | led to the two tests below |
| Running per-position try correction | frozen fit: DEV 0.42286 -> 0.42267, CONFIRM 0.43720 -> 0.43658; on top of the refit-before-season model: 0.43635 -> 0.43627 at best (chosen on the same seasons) | rejected: the refit already does this job |
| Season as a try-model feature | DEV 0.42286 -> 0.42310, CONFIRM 0.43720 -> 0.43716; refit 0.43635 -> 0.43646 | rejected |
| Team try style (share of the attacking team's recent tries by this player's position group) | DEV 0.42286 -> 0.42298, CONFIRM 0.43720 -> 0.43697 | rejected: fails DEV |
| Line-up experience (summed log career games) and age (named 17, home minus away) | DEV 0.1589 -> 0.1532 / 0.1515 bits, CONFIRM 0.0930 -> 0.0946 / 0.0963 (older sides worse, -0.6 points per year of average age) | rejected: fails DEV |
| Edge defence for try scorers (tries the opponent concedes to each jersey number) | DEV 0.42294 -> 0.42293, CONFIRM 0.43725 -> 0.43729 | rejected: the position-group feature already holds it |

## What the evidence says about where "best in the world" comes from

1. **Not from more rating tweaks.** Every rating change since tuning moved the miss by under 0.03 points against
   a typical miss of 13.5: an NRL margin is mostly noise around a well-estimated mean.
2. **From the market and timing.** The public models tip in the same 60-67% band; the only scoreboard that
   separates them is closing line value. Real odds (open, after teams, close) are the single biggest unknown.
3. **From props, where books are said to price on a player's own record.** Our try model already beats a
   competent stand-in; the next inputs are the market's implied team totals and, for run metres and tackles,
   whether books even post those lines in Australia.
4. **From information speed.** Tuesday's list carries nearly all the line-up value (0.050 v 0.051 bits for who
   played), so the window between lists dropping and books repricing is where a fast model earns, if it exists.

## Still to test

- Weather against day-ahead forecasts over a full season (record them through 2027).
- Market-implied totals for the try model, and CLV, once odds exist.
