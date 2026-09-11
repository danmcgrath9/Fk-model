# How punters analyse and price a race, and how it is presented

Research note, 11 Sep 2026. Most Australian racing sites are blocked from the
environment this was written in, so the specifics below come from search extracts of
the sources named; the conventions are consistent across all of them.

## 1. Pricing a race

- Serious punters frame their own market to 100% (some to 80 or 90%) and back only a
  runner whose market price is longer than their assessed price: an overlay.
  (Horse Racing Info, "Framing your own market"; Turf Talk, "Pricing up a market".)
- Bookmaker markets open around 132% and settle around 118%; the market's implied
  chances must be normalised to 100% before comparison. (Champion Bets, "Market
  percentage".)
- Betfair Hub's predictions model presents, per runner: rated chance, rated price,
  market price and VALUE %, defined as (1 / rated price) minus (1 / market price), so
  a 20% rated chance against a 12.5% market chance is +7.5%. Highest positive value is
  the model's back, lowest negative its lay. (Betfair Hub predictions model; Betfair
  Automation Hub, "Value and odds".)
- Ratings providers (RB Ratings, Champion Bets, TopRate) show rating, rated price and
  market price side by side, sorted by rating.

**What the report does now:** rated price framed to 100% from the model probability,
market price, value % in probability points (the Betfair definition), the race's
market percentage (overround) stated once in the race header, rows sorted by rating,
and a value ladder chart with positive value up and negative down. The 5-point flag
becomes a threshold on the same value % column, so the number and the flag are one
figure.

## 2. Speed maps

- The Australian convention (Racing NSW "Punting Pointers", Racing and Sports, TAB,
  Champion Ratings, brissyraces): runners are placed in settling-position groups,
  Leader, On pace, Midfield, Off pace, Backmarker (abbreviations L, P, OP, M, OM, BM),
  with the predicted leader in advance of the field and the rest staggered.
- Barrier is always shown beside the runner because it drives the map.
- The map is read for TEMPO: several runners mapping as leaders means pressure on the
  speed and favours the closers; one leader with no pressure favours the on-pace
  runners. The widely quoted statistic is that the first four settling positions win
  about 60% of races (Racing Life).

**What the report does now:** the speedmap is drawn as a field map: x is predicted
early position with the leader at the front, runners in five lanes by settling group,
each marker labelled with the barrier, colour by early speed. A tempo line under the
title counts the runners mapping Leader or On pace and states the reading rule.

## 3. Sectionals

- Punting Form's segments: to the 600m marker, last 600, last 400, last 200 (and last
  100), plus overall; benchmarks per track, distance and section; variation from the
  benchmark in lengths. The read is the 600 to 400 sprint against the 600 to finish:
  a horse doing excess work at the 600 to 400 is being penalised late. (Punting Form
  docs; Racing NSW "Punting Pointers: Sectionals".)
- Timeform's finishing speed percentage compares the closing sectional to the overall
  race speed against a course-and-distance PAR; the difference from par is what
  matters, not the raw figure. (Timeform, "The Timeform knowledge: sectional
  analysis"; RaceiQ.)
- Form King's vs-Class benchmark is already the "difference from par" number, per
  section, so the worm plots exactly that.

**What the report does now:** the sectional worm stays (it is the Punting Form shape),
and a ranked LAST 600M table sits beside it: recency-weighted vs-Class over the last
600m sections and over the sections before them, best first, so the late-speed read
does not depend on tracing eight lines.

## 4. The market's movement

- Opening to current price, firm (steamer) or drift, ranked; late moves carry sharper
  information than morning ones. (At The Races and Sportsbet market movers;
  Equianalytix.)

**What the report does now:** a firm/drift chart of the % change from opening to
current price, firmers up, drifters down, ranked.

## 5. Position in running

- The position worm is how in-running data is shown (Punting Form, Racing Post
  in-running); the lanes in section 2 are the same information stated as a category.

**What the report does now:** unchanged, with each runner's colour shared between its
latest and older runs.

## Sources

- https://www.championbets.com.au/betting-academy-article/market-percentage-price-punt
- https://www.championbets.com.au/betting-academy-article/race-ratings
- https://www.horseracinginfo.com.au/betting-guide/framing-your-own-market.htm
- https://www.turftalk.co.za/pricing-up-a-market-an-essential-skill-punters-really-should-learn/
- https://www.betfair.com.au/hub/racing/horse-racing/predictions-model/
- https://betfair-datascientists.github.io/wagering/valueAndOdds/
- https://www.racingnsw.com.au/news/feature-articles/punting-pointers-speed-maps/
- https://www.racingnsw.com.au/news/feature-articles/punting-pointers-sectionals/
- https://www.racinglife.com.au/news/how-to-read-a-speed-map
- https://championratings.com.au/understanding-speed-maps-a-beginners-guide-to-australian-racing/
- https://docs.puntingform.com.au/docs/sectional-data
- https://www.timeform.com/horse-racing/features/rowley/the-timeform-knowledge-sectional-analysis-872015
- https://raceiq.com/par-sectionals-fsp/
- https://www.attheraces.com/market-movers
- https://www.equianalytix.com/hubs/odds-movements-market-movers
