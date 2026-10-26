# Player props, step 1: anytime scorer and player carded, out of sample

45,266 player-matches with minutes on the pitch, seasons 2017-2027; a named player who never came on is left out (a void bet at most books). Every rate from earlier matches only. Log loss, lower is better; differences with 90% intervals resampling weeks.

## anytime scorer, teams named (happened in 9.1% of player-matches)

| season | rows | model | raw rate | flat rate |
|---|---|---|---|---|
| 2016-17 | 3,817 | 0.2645 | 0.2688 | 0.3081 |
| 2017-18 | 3,773 | 0.2632 | 0.2654 | 0.3040 |
| 2018-19 | 3,812 | 0.2805 | 0.2854 | 0.3228 |
| 2019-20 | 4,101 | 0.2567 | 0.2606 | 0.2908 |
| 2020-21 | 4,683 | 0.2576 | 0.2607 | 0.2939 |
| 2021-22 | 4,796 | 0.2577 | 0.2617 | 0.2855 |
| 2022-23 | 4,891 | 0.2640 | 0.2689 | 0.2967 |
| 2023-24 | 5,032 | 0.2747 | 0.2772 | 0.3041 |
| 2024-25 | 5,330 | 0.2761 | 0.2805 | 0.3001 |
| 2025-26 | 4,878 | 0.2730 | 0.2767 | 0.2892 |
| 2026-27 | 153 | 0.2506 | 0.2562 | 0.2657 |

settings chosen on, 2016-17 to 2020-21: model minus raw rate -0.0037 (-0.0047 to -0.0026); model better.

settings chosen on, 2016-17 to 2020-21: model minus flat rate -0.0392 (-0.0426 to -0.0359); model better.

untouched test, 2021-22 on: model minus raw rate -0.0039 (-0.0048 to -0.0029); model better.

untouched test, 2021-22 on: model minus flat rate -0.0260 (-0.0288 to -0.0234); model better.

Calibration, test seasons:

| predicted band | rows | average predicted | happened |
|---|---|---|---|
| (0.0, 0.05] | 10,461 | 0.027 | 0.033 |
| (0.05, 0.1] | 7,595 | 0.072 | 0.076 |
| (0.1, 0.15] | 3,148 | 0.121 | 0.116 |
| (0.15, 0.2] | 1,592 | 0.173 | 0.181 |
| (0.2, 0.3] | 1,607 | 0.242 | 0.273 |
| (0.3, 0.4] | 523 | 0.338 | 0.312 |
| (0.4, 0.6] | 154 | 0.460 | 0.455 |

## anytime scorer, at the open (before teams are named) (happened in 9.1% of player-matches)

| season | rows | model | raw rate | flat rate |
|---|---|---|---|---|
| 2016-17 | 3,817 | 0.2672 | 0.2688 | 0.3081 |
| 2017-18 | 3,773 | 0.2647 | 0.2654 | 0.3040 |
| 2018-19 | 3,812 | 0.2840 | 0.2854 | 0.3228 |
| 2019-20 | 4,101 | 0.2591 | 0.2606 | 0.2908 |
| 2020-21 | 4,683 | 0.2595 | 0.2607 | 0.2939 |
| 2021-22 | 4,796 | 0.2608 | 0.2617 | 0.2855 |
| 2022-23 | 4,891 | 0.2672 | 0.2689 | 0.2967 |
| 2023-24 | 5,032 | 0.2754 | 0.2772 | 0.3041 |
| 2024-25 | 5,330 | 0.2791 | 0.2805 | 0.3001 |
| 2025-26 | 4,878 | 0.2755 | 0.2767 | 0.2892 |
| 2026-27 | 153 | 0.2492 | 0.2562 | 0.2657 |

settings chosen on, 2016-17 to 2020-21: model minus raw rate -0.0013 (-0.0019 to -0.0007); model better.

settings chosen on, 2016-17 to 2020-21: model minus flat rate -0.0369 (-0.0404 to -0.0333); model better.

untouched test, 2021-22 on: model minus raw rate -0.0015 (-0.0019 to -0.0010); model better.

untouched test, 2021-22 on: model minus flat rate -0.0235 (-0.0267 to -0.0207); model better.

Calibration, test seasons:

| predicted band | rows | average predicted | happened |
|---|---|---|---|
| (0.0, 0.05] | 9,651 | 0.028 | 0.033 |
| (0.05, 0.1] | 8,220 | 0.072 | 0.075 |
| (0.1, 0.15] | 3,279 | 0.122 | 0.116 |
| (0.15, 0.2] | 1,762 | 0.172 | 0.192 |
| (0.2, 0.3] | 1,595 | 0.240 | 0.246 |
| (0.3, 0.4] | 443 | 0.338 | 0.330 |
| (0.4, 0.6] | 130 | 0.458 | 0.423 |

## player carded (yellow or red) (happened in 13.8% of player-matches)

| season | rows | model | raw rate | flat rate |
|---|---|---|---|---|
| 2016-17 | 3,817 | 0.4281 | 0.4399 | 0.4397 |
| 2017-18 | 3,773 | 0.4102 | 0.4194 | 0.4247 |
| 2018-19 | 3,812 | 0.4113 | 0.4197 | 0.4227 |
| 2019-20 | 4,101 | 0.3813 | 0.3924 | 0.3890 |
| 2020-21 | 4,683 | 0.3851 | 0.3943 | 0.4023 |
| 2021-22 | 4,796 | 0.3880 | 0.3997 | 0.3952 |
| 2022-23 | 4,891 | 0.4093 | 0.4206 | 0.4216 |
| 2023-24 | 5,032 | 0.3728 | 0.3803 | 0.3841 |
| 2024-25 | 5,330 | 0.3430 | 0.3452 | 0.3518 |
| 2025-26 | 4,878 | 0.3597 | 0.3671 | 0.3657 |
| 2026-27 | 153 | 0.4152 | 0.4443 | 0.4343 |

settings chosen on, 2016-17 to 2020-21: model minus raw rate -0.0099 (-0.0117 to -0.0082); model better.

settings chosen on, 2016-17 to 2020-21: model minus flat rate -0.0126 (-0.0143 to -0.0108); model better.

untouched test, 2021-22 on: model minus raw rate -0.0080 (-0.0096 to -0.0064); model better.

untouched test, 2021-22 on: model minus flat rate -0.0092 (-0.0107 to -0.0076); model better.

Calibration, test seasons:

| predicted band | rows | average predicted | happened |
|---|---|---|---|
| (0.0, 0.05] | 1,857 | 0.041 | 0.054 |
| (0.05, 0.1] | 6,573 | 0.075 | 0.082 |
| (0.1, 0.15] | 6,840 | 0.124 | 0.111 |
| (0.15, 0.2] | 6,069 | 0.174 | 0.175 |
| (0.2, 0.3] | 3,688 | 0.228 | 0.210 |
| (0.3, 0.4] | 53 | 0.312 | 0.245 |

## Verdict

Settings were chosen on 2016-17 to 2020-21 and scored on 2021-22 onwards.

- **Anytime scorer, teams named:** beats a player's raw goals-per-appearance rate in every test season
  (-0.0039 log loss, interval clear of zero) and is well calibrated across the range.
- **Anytime scorer, at the open** (before teams are named, minutes from the player's recent role): still
  better than the raw rate (-0.0015) but keeps only about a third of the edge. **When to bet scorer props:
  after teams are named** (about an hour before kick-off in the A-League), which is also when books have
  the least time to react.
- **Player carded (yellow or red):** the first version beat the raw rate (-0.0043) but was too spread
  (low-risk players 3.3% predicted, 6.2% happened). A Platt rescaling fitted on the selection seasons only
  (a -0.30, b 0.75) took the test-season gain to -0.0080 and fixed most of the calibration. It was found
  after the test seasons had been looked at once, so its clean check is 2026-27 as it is played.
- No referee factor: it did not help at any shrinkage on the selection seasons.
- These are probabilities, not profit: whether they beat a book's prices needs recorded odds.
