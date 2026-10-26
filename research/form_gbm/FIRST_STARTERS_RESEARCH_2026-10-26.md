# What other models do with first starters, against what ours does (26 Oct 2026)

Founder: "do some research on what other models do with first starters". Web search summaries only (full texts are
egress-blocked); trade sources, no peer-reviewed study of debutant pricing was found.

## What the field does
- Ratings vendors give a debutant a rating from pre-debut information: sire record, trainer, jockey booking, trip,
  going, race shape (GTX, RatingTheRaces). The rating is a prior, not form.
- Sire debut strike rates, and better, sire "wins above expectation" on debut (actual winners v the market's expected
  winners; the Irish Field's sire analysis). Kingman / Dubawi ~20% debut strike rates; some sires' debutants win far
  less than the market expects. Sire effects vary by distance and by age at debut (3yo debutants by some sires win
  more than 2yo).
- Trainer debut records: first-out strike rate over the last 18 months (DRF debut reports), and patterns (a trainer's
  debutants that start in the top three of the betting; month and distance splits; Geegeez).
- Pre-race work: US models rate published workouts 1-100 (Horse Racing Nation's First Time Power Ratings, 50,000+
  debutants). The Australian equivalent is barrier trials, with times and sectionals where published.
- Benter's frame: blend the model with the public odds. The market carries what the model cannot see (trial
  impressions, stable confidence), and the blend weight can differ by race type.

## What ours already has
first_starter flag; trial count, wins, placings, last-trial finish and margin, days since trial (stage2.trials, 13
inputs, in stage 1 since v5); sire_fs_* (sire's first-starter A/E and win rate); sire and dam-sire A/E; gear changes;
the general jockey and trainer stats.

## What ours is missing, against that list
1. TRIAL TIMES AND SECTIONALS. Our trial records carry finish and margin only (40,964 trial cells, 0 rated, 30 Sep).
   Every outside approach treats pre-race work quality as the main debut signal. Ask Form King whether trials are
   timed or benchmarked anywhere in the API.
2. TRAINER FIRST-STARTER RECORD. We have trainer first-UP (trainer_fu_*), not trainer first-STARTER. A trainer's
   debut strike rate and A/E is the most-cited input in the debut literature and is cheap to build from our own data.
3. JOCKEY BOOKING ON A DEBUTANT relative to the jockey's usual (a top jockey on a first starter is stable intent).
4. AGE AT DEBUT and sire-by-age / sire-by-distance debut splits.
5. A MARKET BLEND WEIGHTED FOR FIRST STARTERS. Our own numbers say the market knows more about them than we do: backed
   first starters win 24.4% against the 18.6% we give them (market 21.9%); KL to BSP 0.138 in races with 2+ first
   starters against 0.075 with none. Benter's approach is a heavier market weight where the model is blind. The live
   blend is one weight (0.82 ours / 0.22 open) for every runner; a first-starter weight fitted on the holdout is a
   cheap test.

## Tried before and did not help
A stage 2 fitted only on first-starter races (worse, 0.1077 v 0.1046); second-stage trainer/sire first-starter gaps
(no gain). So the gain is in NEW inputs (trial quality, trainer debut record) and the market weight, not a separate
model.

## Order
(5) market weight for first starters: an hour, testable now. (2) trainer first-starter A/E and (3) jockey booking:
a day, testable on the current data. (1) trial times: depends on Form King. Until then the race rule stands (no bets
in a race where a first starter opens $6 or shorter, no bets on first starters), which is where the money already is.
