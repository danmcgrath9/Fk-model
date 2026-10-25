# Brief: build a harness (trots) pricing model alongside the Fk-model thoroughbred model

Written 25 Oct 2026 for a fresh session. It is the sister of docs/GREYHOUND_MODEL_BRIEF.md and shares its rules,
reading list and phases; this file carries only what is different about harness. Read both.

## 0. Rules (unchanged from the greyhound brief)
Secrets only in GitHub secrets; never pasted. Provider terms read before any download; no scraping past what is
allowed. No racing data or code in any other repo. No bet without the founder's OK in chat on the exact list, dry run
first; paper before live. Settle after scratching deductions. Every backtest: train before a cut-off, score after,
two date halves, a rule counts only if it holds in both, A/E beside ROI. Write every test up, including the failures.

## 1. What is different about harness
- Pace and gait matter: a pacer or trotter that breaks (gallops) is beaten, so a runner's break history is a feature
  in its own right, and a race's expected tempo (who leads, who sits in the death seat outside the leader) is as
  important as the box draw in dogs. Record in-run position every run.
- Draw and standing/mobile starts: front-row v second-row draws in mobile starts, and the handicap (metres) in
  standing starts, move the price a lot. The draw is known at fields; model it per track and distance.
- Driver and trainer: a small pool of drivers wins a large share; a driver change is information.
- Sectional data: mile rate, lead time, quarters. Some bodies publish them; some do not. Find out which.
- Fields are smaller than gallops, markets thinner, opening prices later and from fewer bookmakers: the open-price edge
  may be smaller than for gallops and the exchange matters more. Measure before assuming.

## 2. Phase 1: data (do this first; report back before any model code)
Sources to check, terms first: Harness Racing Victoria and Harness Racing Australia (fields, form, results, driver and
trainer stats), the other state bodies, Betfair (BSP, place BSP, the historical data product), the bookmakers that open
harness markets and when. For each: what it holds, how far back, access, terms, cost. Hard requirement, as for dogs: a
TIMESTAMPED OPENING PRICE per runner, or there is no open-price edge to measure.
Canonical tables: meeting, race (track, distance, start type, handicap, class, gait), runner (horse id, draw, driver,
trainer), past runs (date, track, distance, draw, start type, finish, margin, mile rate, lead time, quarters where
published, in-run position, broke or not, SP/BSP), results. Point-in-time only.

## 3. Phases 2-4
As the greyhound brief: stage-1 trees plus a second learner, renormalised per race; stage 2 on the market's history of
the horse; score by winner log loss and KL to BSP against the open and BSP, by month; value-at-open rule with the price
band found from the data; staking from research/form_gbm/stake_rule.py; the BSP lay where ours/BSP chance >= 1.6 by
price band; place on the exchange; paper book two weeks minimum before live; BetMatic for the plumbing if it carries
harness (check).

## 4. The first report back
Data sources and costs; races and months in the set; log loss v open v BSP by month; the open rule's ROI by month in
both halves; the lay by band; and a recommendation (paper or not) with reasons. Tables, every number from code.

## 5. Order of work across the three codes
Thoroughbreds national first (the archive retrain). Then greyhounds. Harness only if greyhounds work, because the
data is thinner and the time is better spent scaling the code that pays.
