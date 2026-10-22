# AFL team model, step 2: does the 22 matter? (21 Oct 2026)

Lineup strength rebuilt on AFL Player Ratings (afl/model/strength.py): each player's value is his rating points
(Fryzigg, 2012-2025), recency-weighted (half-life 8 games) and pulled toward a replacement level when he has few games.
2026 has no published ratings, so a stand-in predicted from the same game's box score is used; checked on 2025, where
the real ratings are known, it correlates 0.92 with them (R² 0.84, average miss 1.7 points, 9,703 player-games).

Two lineup measures per team per game: **named** (the 22 that played, valued before the game) and **open** (last week's
side less anyone subbed off injured, empty spots at replacement level: what was knowable before team news). Their
difference is the team news.

## Result: no lineup measure improves the team model on unseen games

650 games, 2024-2026, fitted on 2013-2022, paired against the same model with no lineup measure at all
(results-only rating, recent form, rest, travel):

| lineup measure | margin miss (pts) | change | bits per game | change |
|---|---|---|---|---|
| none | 26.29 | | 0.198 | |
| SuperCoach, side at the open (the old one) | 26.24 | -0.05 ± 0.10 | 0.201 | +0.004 ± 0.003 |
| Player Ratings, named 22 | 26.41 | +0.12 ± 0.23 | 0.197 | -0.000 ± 0.007 |
| Player Ratings at the open + team news | 26.49 | +0.20 ± 0.24 | 0.197 | -0.001 ± 0.007 |

All within noise. In fitting, team news carries 0.65 points of margin per rating point the named side gains over the side
expected at the open, so it is real, but at about 4.5 points of margin for a typical week's news it is small against
the ~34-point spread of one result, and it does not show up out of sample.

## What it means
- Results and recent form already hold most of what the 22 tells you; week-to-week changes are small.
- Team news cannot be shown to sharpen our margin predictions. Whether BOOKS price team news correctly is a separate
  question, answerable only with recorded line moves (the Odds API pull, or BetMatic's odds watch from round 1 2027).
- The team model stays as it is (results-only rating + form + rest + travel); lineup measures stay in the table for the
  odds test.
