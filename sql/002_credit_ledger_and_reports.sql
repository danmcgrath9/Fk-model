-- Credit ledger in Postgres (for unattended runs) and the private reports bucket.
-- Paste into the Supabase SQL editor of the fk-model project. Guarded; re-run is a no-op.

create table if not exists fk.credit_ledger (
    id            bigserial primary key,
    ts            timestamptz not null,
    month         text not null,                 -- YYYY-MM (UTC), the allowance window
    key_kind      text not null check (key_kind in ('live','test','adjust')),
    operation     text not null,
    method        text,
    path          text,
    params        jsonb,
    http_status   integer,
    credits       integer not null,              -- charged; negative allowed on 'adjust'
    note          text
);
create index if not exists credit_ledger_month on fk.credit_ledger (month, key_kind);
alter table fk.credit_ledger enable row level security;
revoke all on fk.credit_ledger from anon, authenticated;
grant all on fk.credit_ledger to service_role;
grant usage, select on sequence fk.credit_ledger_id_seq to service_role;

-- Private bucket for the HTML reports. The workflow uploads with the service role and
-- prints a signed link (7 days) in the run summary; nobody can list or read it without one.
insert into storage.buckets (id, name, public)
values ('fk-reports', 'fk-reports', false)
on conflict (id) do nothing;
