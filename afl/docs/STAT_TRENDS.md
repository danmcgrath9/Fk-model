# How the game has changed, in our own data

Per game, both sides together, home-and-away and finals, from the AFL Tables / Footywire stats we hold. 2020 had 16-minute quarters, so its counts are about a fifth lower and are not comparable. Rule changes and what was said about them are in docs/RULES_AND_NEWS.md.

| season | disposals | kicks | handballs | marks | tackles | goals | contested poss. | uncontested poss. | contested marks | clearances | hitouts | kicks per handball | uncontested share % | top 3 per side, disposals | player-games with 30+ % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2012 | 714.0 | 412.0 | 302.0 | 176.0 | 127.0 | 27.0 | 283.0 | 427.0 | 23.0 | 75.0 | 79.0 | 1.36 | 60.1 | 27.9 | 4.3 |
| 2013 | 717.0 | 414.0 | 303.0 | 177.0 | 126.0 | 27.0 | 280.0 | 432.0 | 21.0 | 75.0 | 79.0 | 1.37 | 60.7 | 27.7 | 4.3 |
| 2014 | 725.0 | 411.0 | 315.0 | 176.0 | 133.0 | 25.0 | 275.0 | 445.0 | 19.0 | 76.0 | 82.0 | 1.3 | 61.8 | 28.5 | 5.2 |
| 2015 | 727.0 | 408.0 | 319.0 | 181.0 | 131.0 | 25.0 | 273.0 | 453.0 | 21.0 | 78.0 | 86.0 | 1.28 | 62.4 | 28.5 | 5.3 |
| 2016 | 751.0 | 411.0 | 340.0 | 177.0 | 140.0 | 26.0 | 285.0 | 466.0 | 23.0 | 73.0 | 79.0 | 1.21 | 62.0 | 29.1 | 6.1 |
| 2017 | 764.0 | 422.0 | 342.0 | 187.0 | 137.0 | 26.0 | 285.0 | 478.0 | 22.0 | 74.0 | 80.0 | 1.23 | 62.6 | 29.3 | 6.5 |
| 2018 | 747.0 | 425.0 | 323.0 | 180.0 | 130.0 | 24.0 | 291.0 | 458.0 | 22.0 | 73.0 | 78.0 | 1.32 | 61.1 | 28.8 | 5.5 |
| 2019 | 742.0 | 438.0 | 303.0 | 183.0 | 125.0 | 23.0 | 289.0 | 442.0 | 23.0 | 76.0 | 77.0 | 1.45 | 60.5 | 29.2 | 6.2 |
| 2020 | 592.0 | 349.0 | 242.0 | 140.0 | 101.0 | 18.0 | 236.0 | 347.0 | 18.0 | 60.0 | 59.0 | 1.44 | 59.6 | 23.8 | 1.2 |
| 2021 | 731.0 | 436.0 | 295.0 | 189.0 | 115.0 | 23.0 | 272.0 | 448.0 | 23.0 | 71.0 | 69.0 | 1.48 | 62.2 | 29.1 | 5.8 |
| 2022 | 718.0 | 432.0 | 286.0 | 183.0 | 117.0 | 24.0 | 274.0 | 433.0 | 21.0 | 74.0 | 72.0 | 1.51 | 61.2 | 28.5 | 5.1 |
| 2023 | 725.0 | 429.0 | 296.0 | 181.0 | 122.0 | 24.0 | 272.0 | 438.0 | 21.0 | 74.0 | 76.0 | 1.45 | 61.7 | 28.3 | 5.0 |
| 2024 | 710.0 | 425.0 | 285.0 | 185.0 | 120.0 | 25.0 | 262.0 | 432.0 | 19.0 | 74.0 | 75.0 | 1.49 | 62.2 | 27.8 | 4.4 |
| 2025 | 704.0 | 414.0 | 291.0 | 176.0 | 119.0 | 24.0 | 259.0 | 429.0 | 19.0 | 74.0 | 78.0 | 1.42 | 62.4 | 27.9 | 4.3 |
| 2026 | 728.0 | 421.0 | 307.0 | 182.0 | 114.0 | 26.0 | 256.0 | 449.0 | 18.0 | 72.0 | 71.0 | 1.37 | 63.7 | 28.2 | 4.6 |

## What moved in 2026, against 2025

- Disposals up 24 a game (704 to 728), nearly all of it handballs (+16) and uncontested possessions (+20).
- Contested possessions (256) and tackles (114) the lowest in the 15 seasons we hold; hitouts down from 78 to 71.
- Goals up from 24 to 26 a game.
- The best players did not take a bigger share: the top three per side averaged 28.2, about where they have sat since 2022.

For the model: the league level moves every summer, which is why it carries the league average of recent games, and why rounds 1-3 are its weakest stretch (docs/RESEARCH_TESTS.md). A rule change shows up in the inputs within a few rounds; it cannot be seen before round 1.
