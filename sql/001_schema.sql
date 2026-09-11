-- Form King model: data layer. Target: Supabase Postgres.
-- Paste into the Supabase SQL editor. Guarded, so re-running is a no-op.
--
-- Conventions
--   * Every table keeps the raw API payload (raw jsonb) beside the columns we
--     read, so a field mapped later can be backfilled without another credit.
--   * Every row stores fetched_at: the instant we received it from the API.
--   * Ids are text because the spec's id types were not confirmed when this
--     was written; text loses nothing and never truncates.
--   * RLS is on with no policies: these tables are read and written by the
--     scripts through the service role only. Browser roles are revoked
--     explicitly because Supabase grants them on every new public table by
--     default regardless of what the migration says.

create schema if not exists fk;

create table if not exists fk.meetings (
    meeting_id    text primary key,
    meeting_date  date not null,
    track         text not null,
    state         text not null,
    raw           jsonb not null,
    fetched_at    timestamptz not null default now()
);
create index if not exists meetings_date_state on fk.meetings (meeting_date, state);

create table if not exists fk.races (
    race_id       text primary key,
    meeting_id    text not null references fk.meetings (meeting_id),
    race_number   integer,
    race_name     text,
    distance_m    integer,
    scheduled_at  timestamptz,
    raw           jsonb not null,
    fetched_at    timestamptz not null default now()
);
create index if not exists races_meeting on fk.races (meeting_id, race_number);

create table if not exists fk.horses (
    horse_id          text primary key,
    name              text not null,
    -- numBenchmarks we last asked for on this horse's profile; the cache reads it
    profile_depth     integer,
    profile_fetched_at timestamptz,
    raw               jsonb,
    fetched_at        timestamptz not null default now()
);

create table if not exists fk.entries (
    race_id       text not null references fk.races (race_id),
    horse_id      text not null references fk.horses (horse_id),
    barrier       integer,
    weight_kg     numeric(5,2),
    jockey        text,
    trainer       text,
    scratched     boolean not null default false,
    neural_rating numeric,
    exp_rating    numeric,
    days_since_last_run integer,
    raw           jsonb not null,
    fetched_at    timestamptz not null default now(),
    primary key (race_id, horse_id)
);

-- A past start, as the API reports it on a profile or a race-form entry.
create table if not exists fk.past_events (
    past_event_id text primary key,
    horse_id      text not null references fk.horses (horse_id),
    event_date    date,
    track         text,
    distance_m    integer,
    finish_position integer,
    margin        numeric,
    raw           jsonb not null,
    fetched_at    timestamptz not null default now()
);
create index if not exists past_events_horse on fk.past_events (horse_id, event_date desc);

-- The sectional benchmarks for a past start. One row per (horse, run).
create table if not exists fk.benchmarked_runs (
    run_id               text primary key,
    horse_id             text not null references fk.horses (horse_id),
    past_event_id        text references fk.past_events (past_event_id),
    event_date           date,
    track_speed_verified boolean not null,   -- required: every row states it
    sections             jsonb,              -- section labels in running order
    positions            jsonb,              -- position in running per section
    vs_class             jsonb,              -- vs-Class benchmark per section
    raw                  jsonb not null,
    fetched_at           timestamptz not null default now()
);
create index if not exists benchmarked_runs_horse on fk.benchmarked_runs (horse_id, event_date desc);

create table if not exists fk.speedmaps (
    race_id       text primary key references fk.races (race_id),
    runners       jsonb not null,   -- [{horse_id, predicted_position, early_speed, raw}]
    raw           jsonb not null,
    fetched_at    timestamptz not null default now()
);

-- One row per price observation. 'source' names where the price came from
-- (e.g. the odds endpoint's bookmaker field); 'kind' is opening|current|starting.
create table if not exists fk.odds_snapshots (
    id            bigserial primary key,
    race_id       text not null references fk.races (race_id),
    horse_id      text not null references fk.horses (horse_id),
    source        text not null default 'formking',
    kind          text not null check (kind in ('opening','current','starting')),
    price         numeric not null,
    observed_at   timestamptz not null,
    raw           jsonb,
    fetched_at    timestamptz not null default now(),
    unique (race_id, horse_id, source, kind, observed_at)
);
create index if not exists odds_race on fk.odds_snapshots (race_id, horse_id, observed_at desc);

create table if not exists fk.results (
    race_id         text not null references fk.races (race_id),
    horse_id        text not null references fk.horses (horse_id),
    finish_position integer,
    margin          numeric,
    starting_price  numeric,
    raw             jsonb not null,
    fetched_at      timestamptz not null default now(),
    primary key (race_id, horse_id)
);

-- Service-role only. Supabase's default privileges hand anon/authenticated
-- access to every new table; take it back and switch RLS on with no policies.
do $$
declare t text;
begin
  for t in select tablename from pg_tables where schemaname = 'fk' loop
    execute format('alter table fk.%I enable row level security', t);
    execute format('revoke all on fk.%I from anon, authenticated', t);
  end loop;
end $$;
revoke usage on schema fk from anon, authenticated;
grant usage on schema fk to service_role;
grant all on all tables in schema fk to service_role;
grant all on all sequences in schema fk to service_role;
