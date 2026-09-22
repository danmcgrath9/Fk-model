-- The paper book, second pass: the market a bet was struck into, and one snapshot per race.
--
-- A race priced twice (the night before and again on race morning) could only ever GAIN
-- bets: a horse already backed was left alone, but a horse whose price had drifted far
-- enough to raise a flag was backed on the second pass. The book therefore took the union
-- of every flag that appeared at any observation, which is not a rule anyone could follow.
-- `first_priced_at` marks the pricing that decides a race; later runs add nothing.
--
-- `opening_price` is the market open, so a settled bet carries open -> struck -> Betfair SP
-- and the movement is readable rather than inferred.
--
-- Paste into the Supabase SQL editor of the fk-model project, or let the scripts apply it
-- (they run this file when the columns are missing). Guarded; re-run is a no-op.

alter table fk.paper_bets add column if not exists opening_price   numeric;
alter table fk.paper_bets add column if not exists first_priced_at timestamptz;

-- Bets already in the book were struck at the first pricing of their own race, so the
-- earliest placed_at per race is that race's snapshot.
update fk.paper_bets b
   set first_priced_at = f.first_at
  from (select race_id, min(placed_at) as first_at from fk.paper_bets group by race_id) f
 where b.race_id = f.race_id and b.first_priced_at is null;

create index if not exists paper_bets_race on fk.paper_bets (race_id);
