# Teams named: does the starting XI improve the head-to-head prices?

1,696 matches with both line-ups. Plus-minus ratings from segments before each match week; the XI's rating against the side's usual XI shifts the team model's expected goals. b chosen on the tune seasons only.

|    b |   tune |   confirm |   final |
|-----:|-------:|----------:|--------:|
| 0    | 1.0082 |    1.0583 |  1.0691 |
| 0.25 | 1.0048 |    1.0577 |  1.0719 |
| 0.5  | 1.0043 |    1.0598 |  1.0787 |
| 0.75 | 1.0069 |    1.0647 |  1.0893 |
| 1    | 1.0125 |    1.0723 |  1.1038 |
| 1.5  | 1.0329 |    1.0962 |  1.1449 |
| 2    | 1.0657 |    1.1317 |  1.2026 |

Chosen b = 0.5.

| seasons | games | at the open | teams named | difference (90% interval, by week) | verdict |
|---|---|---|---|---|---|
| tune 2015-16 to 2019-20 | 707 | 1.0082 | 1.0043 | -0.0039 (-0.0102 to +0.0026) | no difference |
| confirm 2020-21 to 2022-23 | 485 | 1.0583 | 1.0598 | +0.0015 (-0.0064 to +0.0095) | no difference |
| final 2023-24 to 2025-26 | 504 | 1.0691 | 1.0787 | +0.0096 (+0.0008 to +0.0185) | teams named worse |

In the tenth of matches where the line-ups moved most (170), mean |XI difference| 0.64 goals per 90.

## Verdict

Not adopted. Rating a confirmed XI with regularised plus-minus and shifting the team model by its
difference from the side's usual XI is no better on the tune and confirm seasons and slightly worse on
the newest three (interval clear of zero). With about 160 matches a season and heavy squad turnover,
plus-minus ratings are too noisy to say how much a missing player matters. The literature's gain
(Arntzen & Hvattum 2021) came from much bigger leagues. Ideas left for this: ratings built from
minutes share and goal involvement rather than plus-minus, and a simpler "how many of last week's XI
are missing" count.
