-- The paper book, third pass: which model priced each bet, and scratchings.
--
-- Every bet from the book's first eight race days was priced by a FORM-ONLY model (no
-- market input), which back-tests well behind the morning market; the first model that
-- reads the market went live at 2026-09-23 00:13 UTC. A plan's record means nothing
-- unless it is read per model, so each bet now carries the model that priced it.
--
-- Paste into the Supabase SQL editor of the fk-model project, or let the scripts apply it
-- (they run this file when the column is missing). Guarded; re-run is a no-op.

alter table fk.paper_bets add column if not exists model text;

-- Scratchings. A bet on a runner scratched after the race was priced is VOID (stake back),
-- not a loser and not left open; the field the race was priced against is kept, so a
-- runner scratched after the bet can be named, and the bookmaker DEDUCTION it causes (a
-- share of a winning fixed-odds bet's winnings) is stored with the bet it applies to.
alter table fk.paper_bets add column if not exists void      boolean not null default false;
alter table fk.paper_bets add column if not exists field_ids jsonb;
alter table fk.paper_bets add column if not exists deduction numeric;

update fk.paper_bets set model = 'form_only (before the market model)'
 where model is null and placed_at < timestamptz '2026-09-23 00:13:24+00';
