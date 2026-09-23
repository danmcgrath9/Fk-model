-- The paper book, third pass: which model priced each bet.
--
-- Every bet from the book's first eight race days was priced by a FORM-ONLY model (no
-- market input), which back-tests well behind the morning market; the first model that
-- reads the market went live at 2026-09-23 00:13 UTC. A plan's record means nothing
-- unless it is read per model, so each bet now carries the model that priced it.
--
-- Paste into the Supabase SQL editor of the fk-model project, or let the scripts apply it
-- (they run this file when the column is missing). Guarded; re-run is a no-op.

alter table fk.paper_bets add column if not exists model text;

update fk.paper_bets set model = 'form_only (before the market model)'
 where model is null and placed_at < timestamptz '2026-09-23 00:13:24+00';
