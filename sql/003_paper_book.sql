-- The paper book: every selection the page would have backed, logged at the morning price
-- when the page is built and settled at Betfair SP when the results come in. No money
-- moves; this is how "would we be ahead" gets a sample behind it.
-- Paste into the Supabase SQL editor of the fk-model project, or let the scripts apply it
-- (they run this file when the table is missing). Guarded; re-run is a no-op.

create table if not exists fk.paper_bets (
    bet_id        text primary key,               -- race|horse|plan
    race_id       text not null references fk.races (race_id),
    horse_id      text not null references fk.horses (horse_id),
    plan          text not null,
    meeting_date  date not null,
    track         text,
    race_number   integer,
    horse_name    text,
    placed_at     timestamptz not null default now(),
    price         numeric,                        -- market price when placed
    rated_price   numeric,
    model_prob    numeric,
    market_prob   numeric,
    stake         numeric not null,               -- units
    settled_at    timestamptz,
    settle_price  numeric,                        -- Betfair SP, else starting price
    finish        integer,
    won           boolean,
    returned      numeric                         -- units back, 0 on a loser
);
create index if not exists paper_bets_open on fk.paper_bets (settled_at) where settled_at is null;
create index if not exists paper_bets_plan_date on fk.paper_bets (plan, meeting_date);
alter table fk.paper_bets enable row level security;
revoke all on fk.paper_bets from anon, authenticated;
grant all on fk.paper_bets to service_role;
