# Brief: build a greyhound (then harness) pricing model alongside the Fk-model thoroughbred model

Written 25 Oct 2026 for a fresh session. Everything the thoroughbred model learned in five weeks is in this repo;
read it before writing code. The goal is the same product on a second code: a price for every runner before the
market opens, bets at the opening price where our price says the open is soft, settled honestly, and a BSP lay rule.

## 0. Rules that carry over unchanged
- Secrets only in this repo's GitHub secrets / environment secrets. Never paste a key, token or password into a chat,
  a file or a commit. Data-provider terms are read before any bulk download; no scraping past what a provider allows.
- No racing data or code in any other repo.
- No bet goes on without the founder's OK in chat on the exact list, dry run first. Paper book before live, always.
- Settle at the price taken after scratching deductions; quote prices after deductions; a taken bet is never dropped.
- Every backtest: train before a cut-off, score after it, split the holdout into two date halves, and only believe a
  rule that holds in both. Report A/E (wins / expected) beside ROI. Flat 1u and the staking plan both.
- Write up every test in a README in the research folder, numbers and all, including the ones that failed.

## 1. Read first (in this repo)
- research/form_gbm/README.md: the whole thoroughbred story, test by test. The method to copy is in there.
- data/live_bets/TIPPING_RULES.md and BETMATIC_PLAN.md: how bets are built, sent and recorded.
- scripts/export_dataset.py (how a day file is built), research/form_gbm/stake_rule.py (staking), betmatic_orders.py
  (order sheets with price steps), market_sheet.py (the page), t_lay_halves.py and t_bsp_angles.py (the BSP lay test).
- The findings that matter most: the edge is at the OPENING price, not at BSP (73% of our bets shorten by the jump,
  BSP is close to fair); a model's job is to know which runners the open has wrong; laying at BSP works only where the
  model rates a runner far better than BSP does; late bookmaker prices are 30% shorter than the exchange.

## 2. Greyhounds first, harness second
Greyhounds: more races than gallops in Victoria, fields of 8, box draw and sectional (first-split) times carry most of
the signal, markets thinner and open later. Harness: fewer public data sources; do it only if greyhounds work.

## 3. Phase 1: data (expect this to be most of the work; there is no Form King for dogs)
1. Find the sources and READ THEIR TERMS before downloading anything: GRV (Victoria) and the other state bodies'
   published form, fields and results; Betfair for prices (BSP, place BSP) and the Betfair historical data product;
   bookmaker opening prices (which bookmaker opens first for dogs, and when). Record for each source: what it holds,
   how far back, how it is accessed, what the terms allow, cost.
2. Build the canonical tables: meeting, race (track, distance, grade, box count, time), runner (dog id, box, trainer,
   weight), past runs per dog (date, track, distance, box, finish, margin, time, first split, in-run position, grade,
   SP/BSP), results (finish, time, BSP, place BSP). Point-in-time only: a feature may use nothing dated on or after the
   race day.
3. Prices: opening price per runner from the first bookmaker to open, timestamped; BSP and place BSP. Without a
   timestamped open there is no open-price edge to measure, so this is a hard requirement before modelling.
4. Target: 12+ months of history across the Victorian tracks, then other states.

## 4. Phase 2: model
- Stage 1: gradient-boosted trees (LightGBM) on per-runner features, normalised to a race probability (same recipe as
  research/form_gbm: trees + a second learner, blended, renormalised per race). Features: recent times at the
  distance/track adjusted for track speed on the day, first-split times, box, box win rate at the track/distance,
  grade moves, days since last run, trainer rate, age, weight change, in-run position habits.
- Stage 2 (as in the gallops model): the market's history on the dog (what the market thought last time v what
  happened), blended with the opening price where it exists.
- Score: winner log loss and KL to BSP against the opening market and against BSP, by month. The model is useful when
  it is closer to BSP than the open is.

## 5. Phase 3: betting rules and backtest
- Value at the open: back where our price x open >= 1.2 (test 1.15-1.3), price band to be found (gallops: $1.60-$15),
  open under 3x ours, no first starters (test), deductions modelled (dogs scratch less; measure it).
- Staking: research/form_gbm/stake_rule.py as the starting point; test flat v the plan.
- BSP: back at BSP (expect ~zero), lay at BSP where ours/BSP chance >= 1.6 by price band, place on the exchange from
  our win probabilities. Same two-halves discipline.
- Deliverable: a README with monthly tables (bets, won, staked, ROI at open after deductions, ROI at BSP, beat-BSP
  share, worst month, drawdown) and a one-page summary for the founder with the honest caveats.

## 6. Phase 4: live plumbing (only after Phase 3 is positive in both halves)
- Daily: pull fields -> price -> order sheet (price steps, min/max odds, stake) -> BetMatic (reuse betmatic/ tools;
  check which bookmakers BetMatic supports for greyhounds) -> fills recorded at the open -> settle nightly from results.
- Paper book for at least two weeks before a dollar goes on. Tweet cards reuse branding/mercer-tipping/tipcard.py.

## 7. What "done" looks like for the first report back
A written answer to: where does the data come from and what did it cost; how many races and months are in the set;
model log loss v open v BSP by month; the value-at-open rule's ROI by month in both halves; the BSP lay by band; and a
recommendation (go to paper, or not) with the reasons. Numbers in tables, every number from code in the repo.
