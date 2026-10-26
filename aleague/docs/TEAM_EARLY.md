# Early-season shrinkage of team strengths

Head-to-head log loss, lower is better. alpha 0 is the current model. Chosen on the tune seasons.

## plain

|   alpha |   tau |   tune |   confirm |   seen |
|--------:|------:|-------:|----------:|-------:|
|    0.5  |     3 | 1.0075 |    1.0565 | 1.0688 |
|    0.25 |     3 | 1.0075 |    1.0577 | 1.0688 |
|    0.75 |     3 | 1.0078 |    1.0555 | 1.069  |
|    0    |     6 | 1.0078 |    1.0591 | 1.069  |
|    0    |    12 | 1.0078 |    1.0591 | 1.069  |
|    0    |     3 | 1.0078 |    1.0591 | 1.069  |
|    0.25 |     6 | 1.008  |    1.0569 | 1.0685 |
|    0.5  |     6 | 1.0087 |    1.055  | 1.0684 |
|    0.25 |    12 | 1.009  |    1.0564 | 1.0681 |
|    0.75 |     6 | 1.0099 |    1.0534 | 1.0688 |
|    0.5  |    12 | 1.0112 |    1.0543 | 1.0681 |
|    0.75 |    12 | 1.0144 |    1.0527 | 1.0691 |

Chosen: alpha 0.5, tau 3.0.

| seasons | first 10 club matches: current | chosen | all matches: difference (90% interval) |
|---|---|---|---|
| confirm | 1.0960 | 1.0893 | -0.0026 (-0.0044 to -0.0010) |
| seen | 1.0581 | 1.0574 | -0.0003 (-0.0028 to +0.0022) |

## continuity

|   alpha |   tau |   tune |   confirm |   seen |
|--------:|------:|-------:|----------:|-------:|
|    0.75 |     3 | 1.0072 |    1.0571 | 1.069  |
|    0.5  |     3 | 1.0073 |    1.0577 | 1.069  |
|    0.25 |     3 | 1.0075 |    1.0584 | 1.0689 |
|    0.5  |     6 | 1.0076 |    1.0569 | 1.0688 |
|    0.25 |     6 | 1.0077 |    1.058  | 1.0688 |
|    0.75 |     6 | 1.0078 |    1.0559 | 1.0689 |
|    0    |    12 | 1.0078 |    1.0591 | 1.069  |
|    0    |     6 | 1.0078 |    1.0591 | 1.069  |
|    0    |     3 | 1.0078 |    1.0591 | 1.069  |
|    0.25 |    12 | 1.008  |    1.0577 | 1.0687 |
|    0.5  |    12 | 1.0084 |    1.0563 | 1.0686 |
|    0.75 |    12 | 1.0091 |    1.0551 | 1.0688 |

Chosen: alpha 0.75, tau 3.0.

| seasons | first 10 club matches: current | chosen | all matches: difference (90% interval) |
|---|---|---|---|
| confirm | 1.0960 | 1.0907 | -0.0020 (-0.0035 to -0.0007) |
| seen | 1.0581 | 1.0582 | +0.0000 (-0.0024 to +0.0023) |

## Verdict

Adopted the plain version (settings.json `early_alpha` 0.5, `early_tau` 3): each club's strength is used at
half weight in its first match of a season, rising towards full weight over its first several matches.
Chosen on 2015-16 to 2019-20; on 2020-21 to 2022-23 it improves head-to-head log loss by 0.0026 a match
(interval clear of zero), and it is neutral on the newest seasons. Squad continuity (how much of last
season's minutes are back) did no better than the plain version, so the simpler one is kept.
