# Research ideas, tested without bookmaker lines

From docs/RESEARCH_BEST_MODEL.md. Fitted 2013-2023, tuned 2024, scored 2025-2026 (never seen), paired per player-game, ± one standard error. Kept where more than two standard errors better. The market view of the game exists from 2017 (Squiggle "Punters"); earlier rows carry none and the model treats them as unknown.

## New inputs

### Disposals

Current model: average miss 3.721.

| tried | log-lik change | average miss change | kept |
|---|---|---|---|
| market view of the game | +0.0001 ± 0.0003 | -0.001 ± 0.001 | no |
| market margin in place of ours | +0.0005 ± 0.0003 | -0.002 ± 0.001 | no |
| shorter and longer memory | +0.0012 ± 0.0004 | -0.007 ± 0.002 | yes |
| substitute risk | +0.0003 ± 0.0003 | -0.001 ± 0.001 | no |

### Marks

Current model: average miss 1.776.

| tried | log-lik change | average miss change | kept |
|---|---|---|---|
| market view of the game | +0.0000 ± 0.0002 | -0.001 ± 0.001 | no |
| market margin in place of ours | +0.0008 ± 0.0003 | -0.003 ± 0.001 | yes |
| shorter and longer memory | +0.0012 ± 0.0005 | -0.003 ± 0.001 | yes |
| substitute risk | +0.0001 ± 0.0002 | -0.001 ± 0.001 | no |

### Tackles

Current model: average miss 1.419.

| tried | log-lik change | average miss change | kept |
|---|---|---|---|
| market view of the game | -0.0002 ± 0.0002 | -0.002 ± 0.000 | no |
| market margin in place of ours | -0.0001 ± 0.0002 | -0.000 ± 0.000 | no |
| shorter and longer memory | +0.0023 ± 0.0004 | -0.006 ± 0.001 | yes |
| substitute risk | -0.0001 ± 0.0002 | +0.000 ± 0.000 | no |

### Goals

Current model: average miss 0.531.

| tried | log-lik change | average miss change | kept |
|---|---|---|---|
| market view of the game | +0.0003 ± 0.0002 | -0.002 ± 0.000 | no |
| market margin in place of ours | +0.0001 ± 0.0002 | -0.000 ± 0.000 | no |
| shorter and longer memory | +0.0011 ± 0.0004 | -0.002 ± 0.000 | yes |
| substitute risk | +0.0001 ± 0.0002 | -0.000 ± 0.000 | no |

## A spread that depends on the player

Spread = exp(c0 + c1 x log projection + c2 x the player's own recent volatility (sd / mean of his last 10)), fitted on 2024's out-of-sample projections, scored on 2025-2026 against the spread the walk-forward uses now (per position for disposals, one spread for the rest).

| stat | c1 (projection) | c2 (volatility) | log-lik change | kept |
|---|---|---|---|---|
| disposals | -0.802 | +1.678 | +0.0008 ± 0.0007 | no |
| marks | -0.380 | +0.158 | +0.0003 ± 0.0001 | yes |
| tackles | -0.390 | +0.327 | +0.0004 ± 0.0002 | no |
| goals | -1.686 | +0.613 | -0.0002 ± 0.0009 | no |

## The position on the team sheet

Named position (centre square, ruck, wing, back, forward, bench, sub) and how often he has lately been named in the centre square. Fryzigg ends at 2025, so fitted 2013-2022, tuned 2023, scored 2024-2025.

| stat | matched | log-lik change | average miss change | kept |
|---|---|---|---|---|
| disposals | 99% | +0.0013 ± 0.0005 | -0.004 ± 0.002 | yes |
| marks | 99% | -0.0000 ± 0.0003 | -0.000 ± 0.001 | no |
| tackles | 99% | +0.0009 ± 0.0003 | -0.001 ± 0.001 | yes |
| goals | 99% | +0.0022 ± 0.0005 | -0.001 ± 0.000 | yes |

## What was adopted

| idea | adopted for | how |
|---|---|---|
| shorter and longer memory (half-lives 2, 12 and 30 games beside 5) | all four stats | `afl/model/props.py` stat_features |
| position on the team sheet | disposals, tackles, goals | `afl/model/named_position.py`; live from the pasted team sheet (`afl/live/team_sheet.py`) |
| market margin in place of ours | marks only passed, and only just | not adopted yet: live it needs the market's margin each week, which arrives with the odds feed; revisit then |
| spread depending on the player's volatility | marks only passed (+0.0003) | not adopted: too small to be worth another moving part |
| market view of the game beside ours, substitute risk | none | dropped |

After the rebuild, the walk-forward average miss for disposals is 3.72 (2025) and 3.71 (2026), from 3.74 and 3.72.
The 2026 figure gains nothing from positions, because Fryzigg has not published 2026; live 2027 rows carry them from the
team sheet.
