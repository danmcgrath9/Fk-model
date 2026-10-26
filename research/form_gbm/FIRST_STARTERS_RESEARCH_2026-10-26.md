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

## Tested the same day (t_fs_weight.py, t_fs_feats.py): neither helps, the race rule stands
- (5) A FIRST-STARTER MARKET WEIGHT. Own (ours, open) blend weights for first starters, fitted on one half of the v10
  holdout, scored on the other. Worse out of sample in both halves: winner log loss in first-starter races 1.8480 v
  1.8349 live (early), 1.7465 v 1.7410 (late); KL to BSP 0.1111 v 0.1018 (early). The fitted weights swing (ours 0.30 /
  0.65, open 1.05 / 0.30), so the half they are fitted on does not describe the other. The plan inside first-starter
  races is also worse with them (early, race rule applied: open +15.6% against +41.1% live).
- (2) and (3) TRAINER AND JOCKEY DEBUT RECORDS. trainer_fs (runs, A/E, win rate), jockey_fs, and for first starters
  the booked jockey's 12-month win rate and its rank in the race, point in time. Same LightGBM as t_5v10.py, 3 seeds,
  trained before 3 Jun. The trees barely use them (0.4% of gain across all seven) and nothing improves in both halves:
  first-starter-race log loss 1.9047 v 1.9169 early (better), 1.7976 v 1.7757 late (worse); KL to BSP worse in both
  (0.1660 v 0.1610, 0.1876 v 0.1865); the plan's ROI at the open falls in both (+11.3% to 0.0%, +10.3% to +8.2%).
  15 months of data is a median of 11 debutants per trainer, too thin for the record to say anything the market has not.
- What did not move: backed first starters (open $6 or under) won 29.5% / 27.4% of the time; the model gives them
  15.4% / 18.0%, BSP 24.1% / 24.5%. The blind spot is real and none of the cheap inputs closes it. Trial quality
  (item 1, a Form King question) and the national archive's depth for the trainer record (item 2 again, retest on it)
  are what is left. Until then: no bets on first starters, no bets in a race where one opens $6 or shorter.
- Side note: f_careerForm_s == 0 marks 3,305 runners as unraced; the first_starter column marks 1,739. Not chased
  here; the two definitions should be reconciled before the trainer record is retested on the archive.
