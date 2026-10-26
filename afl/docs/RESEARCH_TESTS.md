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
## Who inherits the ball when a teammate is out

Per stat: the usual output of players missing from last week's side, each player's share-weighted slice of it, the same for centre clearances, and his own record in past games when a key midfielder was out. Fitted 2013-2023, tuned 2024, scored 2025-2026.

| stat | log-lik change | average miss change | kept |
|---|---|---|---|
| disposals | -0.0002 ± 0.0003 | +0.001 ± 0.001 | no |
| marks | -0.0000 ± 0.0002 | -0.000 ± 0.000 | no |
| tackles | +0.0010 ± 0.0003 | -0.001 ± 0.000 | yes |
| goals | +0.0001 ± 0.0002 | -0.000 ± 0.000 | no |


Adopted from the test above: who inherits the ball, for tackles only (`REDIST_STATS` in afl/model/walkforward.py).
## One model or an average of several

The current model against the average of 5 fitted with different random seeds. Fitted 2013-2023, tuned 2024, scored 2025-2026.

| stat | log-lik change | average miss change | kept |
|---|---|---|---|
| disposals | +0.0003 ± 0.0001 | -0.002 ± 0.001 | yes |
| marks | +0.0001 ± 0.0001 | +0.000 ± 0.000 | no |
| tackles | -0.0004 ± 0.0001 | +0.000 ± 0.000 | no |
| goals | +0.0001 ± 0.0001 | +0.000 ± 0.000 | no |

Not adopted from the test above: averaging five seeds. It passes for disposals (+0.0003) and hurts tackles, and five
times the training for a sixth of what the team-sheet position bought is not worth another moving part.
## Players who changed clubs

Games at his current club, a new-club flag (first 16 games after 20+ elsewhere), playing his former club, and how far his output at the new club has moved from what he brought. Fitted 2013-2023, tuned 2024, scored 2025-2026; also scored on the mover rows alone, where any effect would show.

| stat | log-lik change (all) | on new-club rows | on former-club games | kept |
|---|---|---|---|---|
| disposals | -0.0002 ± 0.0003 | +0.0005 ± 0.0016 (933) | +0.0037 ± 0.0038 (274) | no |
| marks | +0.0002 ± 0.0002 | -0.0004 ± 0.0010 (933) | +0.0022 ± 0.0021 (274) | no |
| tackles | -0.0005 ± 0.0002 | -0.0006 ± 0.0011 (933) | -0.0017 ± 0.0017 (274) | no |
| goals | +0.0002 ± 0.0002 | +0.0002 ± 0.0010 (933) | +0.0003 ± 0.0017 (274) | no |

Not adopted from the test above: nothing about a club move earns a place. Recent movers are projected about as well as
everyone else, because their form inputs follow them across clubs, and the "lifts against his old club" effect is
not there in 274 such games in 2025-2026 (all four stats within their noise).
## Ground shape and size

What each ground has done lately to each stat, overall and for each position group, and how often the player has played there. Fitted 2013-2023, tuned 2024, scored 2025-2026; also scored at the grounds most unlike the MCG (Kardinia Park, the SCG, the Gabba, Docklands).

| stat | log-lik change (all) | at those four grounds | kept |
|---|---|---|---|
| disposals | +0.0002 ± 0.0003 | +0.0002 ± 0.0005 (6,709) | no |
| marks | +0.0010 ± 0.0005 | +0.0014 ± 0.0009 (6,709) | yes |
| tackles | -0.0008 ± 0.0003 | +0.0005 ± 0.0004 (6,709) | no |
| goals | +0.0001 ± 0.0002 | +0.0003 ± 0.0004 (6,709) | no |

Adopted from the test above: ground shape and size for marks only (`GROUND_STATS` in afl/model/walkforward.py), on
the line (+0.0010 ± 0.0005). The overall disposal level of each ground was already in the model (venue_rel).
## The league level of each stat

Average per game of the stat over the league's last 36 games (before this one), and the same over the last 9. Fitted 2013-2023, tuned 2024, scored 2025-2026, and on 2026 alone (the year the game changed most).

| stat | log-lik change (2025-26) | on 2026 | kept |
|---|---|---|---|
| disposals | -0.0000 ± 0.0003 | +0.0008 ± 0.0004 | no |
| marks | +0.0010 ± 0.0003 | +0.0022 ± 0.0004 | yes |
| tackles | +0.0006 ± 0.0003 | +0.0009 ± 0.0004 | yes |
| goals | -0.0000 ± 0.0002 | -0.0000 ± 0.0003 | no |

Adopted from the test above: the league level for marks and tackles (`LEAGUE_STATS` in afl/model/walkforward.py).
Disposals already had it (league_game_D); goals gained nothing.
