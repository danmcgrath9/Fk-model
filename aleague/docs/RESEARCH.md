# How to be the best soccer model: what the literature says (21 Oct 2026)

A literature survey for this project, done from search-engine abstracts and snippets: arXiv and most
journals could not be opened from the research environment, so no primary paper was read in full.
Figures marked "(secondary)" come from a later paper or blog quoting the original. Nothing here is a
result of ours.

## The ten improvements, ranked for this project

| # | Improvement | Needs | Effort | Evidence |
|---|---|---|---|---|
| 1 | **Blend with the market and measure against it.** De-vig closing odds (Shin or power method), then a second-stage logit of the result on [our log-odds, market log-odds] on held-out seasons. The weight on our model is the edge, if any | odds | low | Benter 1994 (racing, R² .1237 public alone, .1327 with model, secondary); a 2026 Serie A preprint (arXiv 2608.11505, not peer reviewed) gives a well-specified Dixon-Coles weight 0.000 against Pinnacle's close over 19 seasons |
| 2 | **Home advantage that moves over time** (its own faster decay or a random walk), team-specific home effects shrunk hard to the league | goals | low | COVID-era fall well documented; time-varying team-specific home advantage improves goal prediction (Qi et al. 2025 preprint). No A-League study found |
| 3 | **Player ratings from line-up minutes** (regularised plus-minus over segments between substitutions), combined with team ratings; also a better new-season prior (share of last season's rated minutes that returns) | line-ups | medium | Arntzen & Hvattum 2021: Elo and plus-minus about equal alone, combined significantly better (size not found) |
| 4 | **Tune or model the dynamics** (state-space strengths: Rue & Salvesen 2000, Koopman & Lit 2015; footBayes, Macrì-Demartino et al. 2026) | goals | medium | dynamic models beat static; differences modest |
| 5 | **Calibrate, then ensemble** (ordered logit on expected goal difference; pi-ratings, goal-difference Elo, boosted trees on rating features) | goals | low-medium | Goddard 2005 hybrid best; 2017 Soccer Prediction Challenge won by boosted trees on pi-rating features; 40-year review (Hubáček et al. 2022): top score-based models "nearly indistinguishable" |
| 6 | **Totals and BTTS need more than goals** (shots, corners); at least a time-varying league scoring level, and test negative binomial / Weibull-count / diagonal-inflated scores | shots for the big gain | high / low | Wheatcroft 2020: shots-and-corners ratings about +0.8% a bet over 12 years in 10 European over/under markets; Boshnakov et al. 2017 Weibull count |
| 7 | Market value as a strength prior | Transfermarkt (terms forbid scraping) | medium | Peeters 2018 (internationals); about level with Elo domestically |
| 8 | **Evaluate properly**: log loss first (Wheatcroft 2021), paired tests, closing line value on every hypothetical bet; 1,000 bets at evens give an ROI standard error of about 3.2%, so one A-League season cannot prove an edge | - | low | |
| 9 | **Staking**: shrunken / fractional Kelly when probabilities are estimated (Baker & McHale 2013); expect limits (Kaunitz et al. 2017 were restricted within months) | - | low | |
| 10 | **Props**: P(scores) = 1 - exp(-team λ x player share x expected minutes / 90), shares shrunk hierarchically (McHale & Szczepański), minutes from a start/sub model, goal timing weighted late; cards = player rate x referee x match state (Dawson et al. 2007: referees differ, away sides carded more). "Props are softer" is a hypothesis, not a finding | line-ups | medium-high | no peer-reviewed prop-pricing method found |

## Facts worth keeping

- Market efficiency: average closing odds are precise probabilities (Kaunitz et al., 479,440 games); their
  outlier strategy made 8.5% with real money on 256 bets before restriction. 1X2 shows a favourite-longshot
  bias; Asian handicap prices do not (Whelan & Hegarty, 80,000+ matches), so the Asian line is the cleaner
  benchmark. Inefficiencies appear in single seasons and do not persist (14-season study, J. Sports Econ.).
- 2017 Soccer Prediction Challenge: winner Hubáček, Šourek, Železný (boosted trees, relational and pi-rating
  features), Constantinou's Dolores second, 0.94% behind. Pi-ratings beat two Elo variants (Constantinou &
  Fenton 2013).
- A-League market efficiency: one Macquarie thesis (Dodig, 2010-15 AFL/NRL/A-League); findings not read.

## What this means for us

The goals-only model already sits where the literature says goals-only models sit (level with Elo). The
gains left are, in order: the market blend and closing line value (needs the key), line-ups (being pulled
from Ultimate A-League), a home advantage that moves, calibration, and shots data for totals (no free
permitted source). See docs/TEAM_STEP2.md for what was tested.

Full reference list with links: in the session report of 21 Oct 2026, reproduced below.

- Hubáček et al. 2019: https://ida.fel.cvut.cz/papers/hubacek2019learning.html
- Berrar, Lopes & Dubitzky 2019: https://mlanthology.org/mlj/2019/berrar2019mlj-incorporating
- Hubáček et al. 2022 review: https://ieeexplore.ieee.org/iel7/8016797/9623699/09623700.pdf
- Constantinou & Fenton 2013 (pi-ratings): https://qmro.qmul.ac.uk/xmlui/bitstream/123456789/10776/5/CONSTANTINOU%20Determing%20the%20Level%20of%20Ability%202012%20Accepted.pdf
- Koopman & Lit 2015: https://econpapers.repec.org/RePEc:tin:wpaper:20120099
- Ley et al. 2019: https://arxiv.org/pdf/1705.09575
- Macrì-Demartino et al.: https://arxiv.org/abs/2508.05891v1
- Goddard 2005: https://www.stat.berkeley.edu/~aldous/157/Papers/goddard.pdf
- Boshnakov et al. 2017: https://ideas.repec.org/a/eee/intfor/v33y2017i2p458-466.html
- Karlis & Ntzoufras: https://jstatsoft.org/article/view/v014i10
- Arntzen & Hvattum 2021: https://statmod.org/smij/Vol21/Iss5/Arntzen/Abstract.html
- Kharrat, McHale & Peña 2020: https://ar5iv.arxiv.org/html/1706.04943
- Wheatcroft 2020 (over/under): https://researchonline.lse.ac.uk/id/eprint/103712 ; RPS critique: https://arxiv.org/pdf/1908.08980
- Kaunitz et al.: https://arxiv.org/pdf/1710.02824
- Angelini & De Angelis 2019: https://ideas.repec.org:443/a/eee/intfor/v35y2019i2p712-721.html
- Whelan & Hegarty: https://mpra.ub.uni-muenchen.de/116925/
- Serie A closing-price preprint: https://arxiv.org/pdf/2608.11505
- Benter 1994: https://www.Gwern.net/doc/statistics/decision/1994-benter.pdf
- Baker & McHale 2013: https://pubsonline.informs.org/doi/fpi/10.1287/deca.2013.0271
- Time-varying home advantage: https://arxiv.org/abs/2506.11399v1 ; Bundesliga post-COVID: https://arxiv.org/pdf/2411.12509
- McHale & Szczepański: https://salford-repository.worktribe.com/output/1428599/a-mixed-effects-model-for-identifying-goal-scoring-ability-of-footballers
- A-League efficiency thesis: https://figshare.mq.edu.au/articles/thesis/Betting_market_efficiency_an_examination_of_Australian_sport/19431953
