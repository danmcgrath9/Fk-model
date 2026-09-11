# fk-model: Form King pricing model, Phase 0 and 0.5

A credit-aware data layer for the Form King Modellers API (Single State Pro, Victoria,
20,000 credits a month) and a form report built from what it stores.

## What is built

| Piece | Where | Status |
|---|---|---|
| Spec reader (server, auth header, operations, parameters) | `fk/spec.py` | tested on a stand-in spec |
| Credit cost table (spec prose, `x-credits`, `credits.yaml` override) | `fk/credits.py` | tested |
| SQLite credit ledger with derived running balance | `fk/ledger.py`, `scripts/ledger.py` | tested |
| HTTP client: prices before calling, ledgers every call, refuses live without a yes | `fk/client.py` | tested with a fake session |
| Supabase schema, 9 tables, `fetched_at` on every row, `track_speed_verified` NOT NULL | `sql/001_schema.sql` | applied twice on Postgres 16, idempotent, RLS on, browser roles revoked |
| Horse profile cache policy (first sight 10, known 5 after a new start, else no call) | `fk/cache.py` | tested |
| Daily VIC pull with estimate-then-confirm | `scripts/daily_pull.py` | written; cannot run until the spec is present |
| Next-morning results and final odds | `scripts/fetch_results.py` | written; same |
| Form report: tempo line, market %, rated price and value per runner, lane speedmap, value ladder, market moves, position worm, sectional worm, late-speed table | `fk/report/`, `scripts/build_report.py` | charts and maths tested; `--demo` renders |

## What is NOT done, and why

1. **The spec was not available to the session that wrote this.** `b2c-openapi.yaml`
   was in a claude.ai project's knowledge, which a cloud session cannot read, and
   formking.com.au is blocked from that environment. So:
   - the operation names in `fk/ops.py` are the names from your brief, not the spec's;
   - the credit costs are read from the spec at runtime by a parser that has only been
     tested on a stand-in, so `credits.yaml` is the safe path;
   - every response field is a candidate list in `fk/fields.py` that raises with the
     real keys when it misses. Nothing is guessed silently.
2. **No call has been made against FK-TEST-API-KEY.** The API host is unreachable from the
   session. The first test-key run happens on your machine.
3. **Neural rating to probability** is a softmax stand-in, stated on the report page.
   If the spec exposes a rated price or probability, map it in `fk/fields.py` and
   use that instead.

## Running it from your phone (no computer needed)

Two GitHub Actions workflows do the work on GitHub's servers: `fk daily pull` every
evening (18:30 Melbourne standard time) and `fk results` every morning (07:00). Reports
are uploaded to a private Supabase bucket and a link appears on each run's page, which the
GitHub mobile app shows. Everything below is a website form.

1. **A new Supabase project** for the horse model (supabase.com, New project, Sydney).
   Not the cafe project: these keys go into GitHub, and the cafe's never do.
2. In that project's SQL editor, paste and run `sql/001_schema.sql`, then
   `sql/002_credit_ledger_and_reports.sql`.
3. On GitHub, repo **Settings > Secrets and variables > Actions**, add two secrets:
   - `FK_API_KEY`: your Form King key
   - `FK_DATABASE_URL`: Supabase Settings > Database > Connection string (URI), with the
     password filled in
   Optional, for a tap-to-open report link instead of a zip download:
   - `FK_SUPABASE_URL`: Supabase Settings > API > Project URL
   - `FK_SUPABASE_SERVICE_ROLE_KEY`: Supabase Settings > API > service_role key
4. Upload the spec: open the repository on GitHub, **Add file > Upload files**,
   choose `b2c-openapi.yaml`.
5. **Actions > fk daily pull > Run workflow** with key `test`. Read the run page. Field-name
   errors here are expected the first time; paste them to Claude to fix.
6. When a test run is clean: **Settings > Secrets and variables > Actions > Variables**,
   add `FK_LIVE` = `true`. From then on the schedule uses your key.

Guards while nobody is watching: `FK_MAX_CREDITS_PER_RUN` (600) and `FK_MIN_BALANCE`
(1000) are repository variables; a run whose estimate breaks either stops before its
first paid call and says so on the run page.

## Setup (on a computer)

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp env.example .env          # then put your key in FK_API_KEY
cp credits.example.yaml credits.yaml
# put b2c-openapi.yaml (1.0.8) in this folder
```

`.gitignore` keeps `.env`, `credits.sqlite`, `reports/*.html` and the spec out of git.

## First run, in order

1. `python scripts/spec_report.py`
   Prints every operation the spec declares, which of `fk/ops.py`'s six names resolve,
   which are priced, and the spec's top-level description. Fix `fk/ops.py` names and
   write `credits.yaml` from what it prints.
2. `python -m pytest -q`
3. Paste `sql/001_schema.sql` into the Supabase SQL editor. Put the connection string in
   `.env` as `DATABASE_URL`.
4. `python scripts/daily_pull.py --key test --dry-run`
   No network. Prints unit prices and the cost of one nine-race meeting.
5. `python scripts/daily_pull.py --key test`
   Against FK-TEST-API-KEY. The first time a response arrives, expect `FieldUnmapped`
   errors naming the real keys; put them first in `fk/fields.py` and re-run. Test-key
   calls are ledgered under `test` and never charged.
6. Only when you say so: `python scripts/daily_pull.py --key live`. It prints the
   estimate and asks. A nine-race Saturday meeting should be about 300 credits. If it
   says 3,000, stop.
7. Next morning: `python scripts/fetch_results.py --key live`.
8. `python scripts/build_report.py --date YYYY-MM-DD` writes `reports/YYYY-MM-DD-<track>.html`
   and opens it. `--demo` renders synthetic data to check the layout.

## After the first live pull

```
python scripts/ledger.py show
python scripts/ledger.py reconcile --site-used <credits used per the Form King usage tab> --note "usage tab, 12 Sep"
```

If the site and the ledger disagree, the ledger is wrong: a cost in `credits.yaml`, or
whether a failed call is charged (`FK_CHARGE_FAILED=0` if the spec says failures are
free; the default assumes they cost). Fix the cause; the adjustment row records the gap.

## How the report is laid out, and why

Per race, in the order a punter reads it (sources in `docs/PUNTER_PRESENTATION_RESEARCH.md`):

1. Tempo line and the market percentage on current prices.
2. Summary table sorted by Neural: barrier, weight, jockey, days, Neural, EXP, rated price
   (1 / Neural %, a market framed to 100%), price, opening, firm/drift, market %, Neural %,
   value in probability points (Neural % minus market %, the Betfair Hub definition), flag
   at more than 5 points either way.
3. Speedmap as a lane map: Leader, On pace, Midfield, Off pace, Backmarker by predicted
   early position, leader at the front, barrier in the marker, colour by early speed.
4. Value ladder (best value at the top) and market moves since opening (firmers first).
5. Position worm (last 5 runs, newest solid) and sectional worm (recency-weighted vs-Class,
   last 600m shaded), with a ranked late-speed table: to the 600m against the last 600m.

## Design notes

- The ledger balance is derived from rows, never stored as a counter.
- The client validates every parameter name against the spec, so a typo is refused,
  not sent.
- `daily_pull.py` prices the meetings call alone, makes it, then prices everything
  that depends on the answer and asks again. Profiles are priced a third time, after
  the race forms say which horses are new.
- Reports read only the database. No API call, ever, from `build_report.py`.
