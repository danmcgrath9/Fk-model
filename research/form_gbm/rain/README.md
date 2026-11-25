# Race-day rain against the official rating (25 Nov 2026)

Founder, 25 Nov 2026: "Use the official rating for results and then test rain on race day. I suspect it's the worst and
most predictable of the lot."

Inputs (no credits): the 28 Oct 2026 `scripts/track_weather.py` run on the experiments branch (each Victorian meeting's
official ratings from results, 2017 to Oct 2026, beside ERA5 rain at the course on race day and each of the 3 days before)
and the 25 Nov `scripts/t_rain_forecast.py` run (what Open-Meteo's forecast said 1 to 5 days ahead, 2024 on). The scripts
here read those two outputs from the session scratch folder; the tables are in the .out.txt files.

- `t_rain.py`: rain on each day against the last race's rating, 3,171 meetings. Race-day rain moves the rating most per mm
  (about 2.5x rain 3 days before); the day before is next; the 3-day total plus race day predicts best.
- `t_fc.py`: forecast skill. Race-day rain 1-3 days out correlates 0.68-0.71 with what fell, as well as any other day at the
  same lead; 4 days out 0.54, 5 days out 0.41. A 10mm+ forecast 3 days out came true 60% of the time; it flagged 44% of the
  10mm+ race days.
- `t_band.py`: calling the going band (good 1-4, soft 5-7, heavy 8+, the only thing the model reads) from the Wednesday
  forecast for a Saturday, on 2025-26 meetings, with a band table built on 2017-24 actual rain. Of the 97 meetings the
  standing rule priced Soft 5 (15mm+ in the 3 days before), 41 finished Heavy, 34 Soft, 22 Good; with 2mm+ forecast on race
  day, 21 of 32 finished Heavy and 1 Good.

Caveat: below 15mm the live rule takes the official rating at pricing time, which this history does not hold, so the
band test's "else Good" stands in for it there. The 97 meetings above are where the rule overrides the official rating,
so they are a fair test of the rule itself. Nothing live changes from this without the founder's word.
